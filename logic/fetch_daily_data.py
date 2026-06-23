import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# 1. Load Environment Configuration
base_dir = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=base_dir / '.env')

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials. Check your root level .env file!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_yesterdays_date():
    """Gets yesterday's date string."""
    yesterday = datetime.now() - timedelta(days=1)
    return yesterday.strftime("%Y-%m-%d")

def fetch_open_meteo_daily_record(date_str, lat, lon):
    """
    Queries both hourly and daily datasets from Open-Meteo Archive API,
    aggregates hourly points to daily averages, and returns a single record dictionary.
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": date_str,
        "end_date": date_str,
        "daily": ["precipitation_sum", "temperature_2m_mean"],
        "hourly": ["soil_moisture_0_to_7cm", "runoff"],
        "timezone": "Africa/Lagos"
    }
    
    try:
        response = requests.get(url, params=params, timeout=12)
        response.raise_for_status()
        data = response.json()
        
        daily = data["daily"]
        hourly = data["hourly"]
        
        # --- 1. Process Hourly Block ---
        hourly_frame = pd.DataFrame({
            "soil_moisture": hourly["soil_moisture_0_to_7cm"],
            "runoff_hr": hourly["runoff"],
        })
        
        # Compute exact daily aggregation logic
        swvl1 = float(hourly_frame["soil_moisture"].mean()) if not hourly_frame["soil_moisture"].isna().all() else 0.25
        runoff_mm = float(hourly_frame["runoff_hr"].sum()) if not hourly_frame["runoff_hr"].isna().all() else 0.0
        
        # --- 2. Extract Daily Basics ---
        tp_mm = daily["precipitation_sum"][0] if daily["precipitation_sum"][0] is not None else 0.0
        temp_c = daily["temperature_2m_mean"][0] if daily["temperature_2m_mean"][0] is not None else 25.0
        
        return {
            "time": f"{date_str}T00:00:00",
            "latitude": lat,
            "longitude": lon,
            "swvl1": swvl1,
            "tp_mm": tp_mm,
            "runoff_mm": runoff_mm,
            "temp_c": temp_c
        }
        
    except Exception as e:
        print(f"API extraction failure at coordinate ({lat}, {lon}): {e}")
        return None

def sync_pipeline():
    yesterday_str = get_yesterdays_date()
    print(f"Commencing precise weather data sync for: {yesterday_str}")
    
    # Grab unique geographic coordinates from static database
    try:
        geo_rows = supabase.table("locations").select("latitude", "longitude").execute()
        coordinates = geo_rows.data
    except Exception as e:
        print(f"Failed to reach static locations catalog: {e}")
        return

    payload_batch = []
    for coord in coordinates:
        lat, lon = coord["latitude"], coord["longitude"]
        data_point = fetch_open_meteo_daily_record(yesterday_str, lat, lon)
        if data_point:
            payload_batch.append(data_point)
            
    # Batch update everything at once
    if payload_batch:
        try:
            supabase.table("flood_features").insert(payload_batch).execute()
            print(f"Successfully synced {len(payload_batch)} records for {yesterday_str} with complete metrics!")
        except Exception as e:
            print(f"Failed pushing updates to database: {e}")

if __name__ == "__main__":
    sync_pipeline()