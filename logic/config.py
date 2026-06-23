from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
MODEL_DIR = BASE_DIR / "model"
LOGO = STATIC_DIR / "logo.png"
FLOODIQ_MODEL = MODEL_DIR / "floodiq_final_model.pkl"

APP_NAME = "FloodIQ"
APP_TAGLINE = "Lagos Flood Risk Prediction"
FORECAST_DAYS = 3
DEFAULT_THRESHOLD = 0.5

FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"

LAGOS_AREAS = {
    "ikeja": (6.601, 3.351),
    "lekki": (6.465, 3.569),
    "victoria island": (6.428, 3.421),
    "vi": (6.428, 3.421),
    "surulere": (6.500, 3.356),
    "yaba": (6.516, 3.376),
    "ajah": (6.468, 3.581),
    "ikorodu": (6.619, 3.506),
    "badagry": (6.417, 2.883),
    "apapa": (6.448, 3.361),
    "mainland": (6.550, 3.375),
    "island": (6.450, 3.400),
    "mushin": (6.524, 3.352),
    "oshodi": (6.556, 3.334),
    "agege": (6.621, 3.320),
    "epe": (6.585, 3.983),
    "festac": (6.468, 3.278),
    "maryland": (6.566, 3.359),
    "ojota": (6.577, 3.387),
    "sangotedo": (6.435, 3.568),
    "abraham adesanya": (6.435, 3.568),
    "magodo": (6.597, 3.393),
}

TOPO_DATA = {
    (6.80, 3.00): {"elevation": 0.0, "slope": 0.0, "flow_accum": 1.0},
    (6.80, 3.25): {"elevation": 0.0, "slope": 0.0, "flow_accum": 1.0},
    (6.80, 3.50): {"elevation": 0.0, "slope": 0.0, "flow_accum": 1.0},
    (6.55, 3.00): {"elevation": 21.4, "slope": 75.69, "flow_accum": 66.0},
    (6.55, 3.25): {"elevation": 8.3, "slope": 75.69, "flow_accum": 66.0},
    (6.55, 3.50): {"elevation": 5.2, "slope": 75.69, "flow_accum": 66.0},
    (6.30, 3.00): {"elevation": 26.8, "slope": 89.94, "flow_accum": 328.0},
    (6.30, 3.25): {"elevation": 25.4, "slope": 89.94, "flow_accum": 328.0},
    (6.30, 3.50): {"elevation": 14.5, "slope": 89.94, "flow_accum": 328.0},
}

GRID_CELLS = list(TOPO_DATA.keys())
FEATURE_COLS = [
    "swvl1",
    "tp_mm",
    "runoff_mm",
    "temp_c",
    "elevation",
    "slope",
    "flow_accum",
    "month",
    "rolling_3day_feat",
    "rolling_5day_feat",
]