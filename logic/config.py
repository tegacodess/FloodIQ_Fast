import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_PUBLIC_DIR = BASE_DIR / "frontend" / "public"
MODEL_DIR = BASE_DIR / "model"
LOGO = FRONTEND_PUBLIC_DIR / "logo.png"
FLOODIQ_MODEL = MODEL_DIR / "floodiq_final_model.pkl"

APP_NAME = "FloodIQ"
APP_TAGLINE = "Lagos Flood Risk Prediction"
FORECAST_DAYS = 3
DEFAULT_THRESHOLD = 0.5

FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"
ELEVATION_API_URL = "https://api.open-meteo.com/v1/elevation"
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

# 
# Replace them with a clean master list of features for your model:
FEATURE_COLS = [
    'tp_mm', 
    'temp_c', 
    'elevation', 
    'slope', 
    'flow_accum', 
    'distance_to_canal_m', 
    'surface_impervious_pct', 
    'swvl1_x_elevation', 
    'tp_x_elevation', 
    'tp_x_distance_canal', 
    'is_low_lying', 
    'rain_on_low_ground', 
    'swvl1_x_distance_canal'
]