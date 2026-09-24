# FloodIQ FastAPI Backend
# Serves predictions, weather, and AI chat via REST API

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime, date
from typing import Optional
import os
from dotenv import load_dotenv
import requests 
from fastapi.responses import RedirectResponse
from supabase import create_client
from logic.landmark_constants import LANDMARK_AREAS


load_dotenv() 

supabase = create_client(
    supabase_url=os.getenv("SUPABASE_URL"),
    supabase_key=os.getenv("SUPABASE_KEY")
)
 

# Import logic modules 

from logic.config import FLOODIQ_MODEL, DEFAULT_THRESHOLD
from logic.prediction_logic import load_model, run_prediction  
from logic.helpers import (build_context, groq_chat, fetch_weather, find_nearest_db_location, get_dynamic_topo)

# App setup 
app = FastAPI(title="FloodIQ API", version="1.0.0")

ALLOWED_ORIGINS = [
    "http://localhost:5173",          # local Vite development server
    "http://127.0.0.1:5173",          # Local fallback
    "https://floodiq.vercel.app",     # live production Vercel URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,    
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent

#  Load models + secrets once at startup 
rf_model, xgb_model = None, None
GROQ_API_KEY: str = ""

@app.on_event("startup")
def startup_load_models():
    global FLOODIQ_MODEL, GROQ_API_KEY
    FLOODIQ_MODEL = load_model()
    print("Model loaded")

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    if GROQ_API_KEY:
        print("Groq API key loaded from environment")
    else:
        print("GROQ_API_KEY not set — AI assistant will be disabled")


# REQUEST / RESPONSE MODELS

class PredictRequest(BaseModel):
    lat: float
    lon: float
    location_name: str
    target_date: Optional[str] = None   # "YYYY-MM-DD" or None = today

class ChatRequest(BaseModel):
    prediction_context: str
    chat_history: list
    user_message: str

class InitialExplanationRequest(BaseModel):
    prediction_context: str
    location_name: str

class AreaLookupRequest(BaseModel):
    query: str

class ReverseGeocodeRequest(BaseModel):
    lat: float
    lon: float

# ENDPOINTS

@app.get("/api/areas")
def get_areas():
    """Return list of known Lagos areas"""
    return {"areas": list(LANDMARK_AREAS.keys())}



@app.post("/api/area-lookup")
def area_lookup(req: AreaLookupRequest):
    query_str = req.query.lower().strip()

    # Step A: hardcoded high-level areas -- instant, no network, no DB
    if query_str in LANDMARK_AREAS:
        lm = LANDMARK_AREAS[query_str]
        return {"found": True, "lat": lm["lat"], "lon": lm["lon"], "display_name": lm["display_name"]}

    # Step B: granular neighborhood match (unchanged)
    try:
        res = supabase.table("locations").select("*").ilike("location_detail", f"%{query_str}%").execute()
        if res.data:
            exact = [r for r in res.data if r["location_detail"].lower() == query_str]
            loc = exact[0] if exact else res.data[0]
            return {"found": True, "lat": loc['latitude'], "lon": loc['longitude'], "display_name": loc['location_detail'].title()}
        return {"found": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reverse-geocode")
def reverse_geocode(req: ReverseGeocodeRequest):
    """
    Converts browser auto-detect coordinates to a human-readable name, 
    while snapping them to your closest granular database coordinate.
    """
    
    # Snap the user's coordinates to nearest database point
    nearest_loc = find_nearest_db_location(req.lat, req.lon)
    
    # Target coordinates to resolve (default to raw if database is empty)
    target_lat = nearest_loc['latitude'] if nearest_loc else req.lat
    target_lon = nearest_loc['longitude'] if nearest_loc else req.lon

    try:
        # Pass coordinates to Nominatim to get a friendly local name
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat": target_lat,
                "lon": target_lon,
                "format": "json",
                "zoom": 14,
                "addressdetails": 1,
            },
            headers={"User-Agent": "FloodIQ/1.0 (lagos-flood-prediction)"},
            timeout=8
        )
        response.raise_for_status()
        data = response.json()
        addr = data.get("address", {})

        name = (
            addr.get("neighbourhood") or
            addr.get("suburb") or
            addr.get("quarter") or
            addr.get("village") or
            addr.get("town") or
            "Lagos"
        )

        # If database already had a name for this point, use it
        display_name = nearest_loc['location_detail'].title() if (nearest_loc and nearest_loc.get('location_detail')) else name

        return {
            "found": True,
            "display_name": display_name,
            "lat": target_lat,  # Returns the snapped coordinate so map works 
            "lon": target_lon,
            "raw_address": addr,
        }

    except Exception as e:
        # If the API times out, fall back to snapped coordinates with a generic name
        return {
            "found": True,
            "display_name": nearest_loc['location_detail'].title() if nearest_loc else "Auto-Detected Location",
            "lat": target_lat,
            "lon": target_lon,
            "error": f"Nominatim API failed, used database fallback: {str(e)}"
        }


@app.post("/api/predict")
def predict(req: PredictRequest):
    """Main prediction endpoint"""
    if FLOODIQ_MODEL is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    # Force fallback to today's date if target_date is not provided or empty
    target_date = date.today() 
    if req.target_date and req.target_date.strip() != "":
        try:
            target_date = datetime.strptime(req.target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Fetch weather using the guaranteed active date instance
    weather_df, error, is_climatology = fetch_weather(
        req.lat, req.lon, start_date=target_date, days=3
    )
    if error:
        raise HTTPException(status_code=502, detail=f"Weather API error: {error}")



    # Get topo features & run prediction
    topo_data = get_dynamic_topo(req.lat, req.lon)    
    if not topo_data or topo_data.get("error") == "INSUFFICIENT_DATA":
        raise HTTPException(
            status_code=422, 
            detail="Could not resolve topography for this location")

    predictions = run_prediction(
        weather_df.copy(), 
        topo_data, 
        FLOODIQ_MODEL,
        threshold=DEFAULT_THRESHOLD
    )

    class PredictionRequest(BaseModel):
        location_name: str
        lat: float
        lon: float
    

    max_prob = float(predictions['flood_prob'].max()) # Extracts the highest probability (e.g., 1.0)
    flood_days = int((predictions['risk_level'] == 'HIGH').sum())


    grid_cell = [topo_data.get('latitude', req.lat), topo_data.get('longitude', req.lon)]

    # Build context string for AI
    context = build_context(
        predictions, req.location_name, req.lat, req.lon,
        grid_cell, is_climatology
    )


    # Serialise day cards
    days = []
    for _, row in predictions.iterrows():
        prob = float(row['flood_prob'])
        days.append({
            "date":             row['date'],
            "flood_prob": round(prob, 4),
            "flood_predicted":  int(row['flood_predicted']),
            "risk_level":       row['risk_level'],
            "tp_mm":               round(float(row['tp_mm']), 2),
            "temp_c":              round(float(row['temp_c']), 1),
            "swvl1":              round(float(row['swvl1']), 1),
        })

    return {
        "location_name":  req.location_name,
        "lat":            req.lat,
        "lon":            req.lon,
        "grid_cell":      [req.lat, req.lon], # Simplified
        "elevation":      float(topo_data.get('elevation', 0.0)),
        "is_climatology": is_climatology,
        "flood_days":     flood_days,
        "max_probability": round(max_prob, 4),
        "days":           days,
        "prediction_context": context,
    }
 


@app.post("/api/chat/init")
def chat_init(req: InitialExplanationRequest):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="AI assistant not configured on server")
    
    # Structure the initial prompt context directly for your existing groq_chat function
    initial_history = [{
        "role": "user", 
        "content": f"Provide an simple summary of the flood risk prediction context for {req.location_name} based on this data framework."
    }]
    
    response, error = groq_chat(
        GROQ_API_KEY, initial_history, req.prediction_context
    )
    if error:
        raise HTTPException(status_code=502, detail=error)
    return {"response": response}

@app.post("/api/chat/message")
def chat_message(req: ChatRequest):
    """Continue AI conversation"""
    if not GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="AI assistant not configured on server")
    history = req.chat_history + [{"role": "user", "content": req.user_message}]
    response, error = groq_chat(
        GROQ_API_KEY, history, req.prediction_context
    )
    if error:
        raise HTTPException(status_code=502, detail=error)
    return {"response": response}


# SERVE FRONTEND
frontend_dist = BASE_DIR / "frontend" / "dist"

# REDIRECT ROUTE 
@app.api_route("/{file_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all_and_redirect(file_path: str):
    # If it looks like an API call that missed a real endpoint, give a clean 404 instead of redirecting
    if file_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API Endpoint Not Found")
        
    # Redirect all browser traffic to your clean Vercel frontend
    return RedirectResponse(url="https://floodiq.vercel.app", status_code=307)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
