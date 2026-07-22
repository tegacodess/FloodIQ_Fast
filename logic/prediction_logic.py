import numpy as np
import pandas as pd
import joblib
import os
from supabase import create_client
from .config import FEATURE_COLS, FLOODIQ_MODEL

# Initialize Supabase client
supabase = create_client(os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_KEY", ""))

def load_model(model_path=FLOODIQ_MODEL):
    return joblib.load(model_path)

def run_prediction(weather_df, topo_dict, model, threshold=0.75):
    df = weather_df.copy()

    spatial_features = [
        'elevation', 'slope', 'flow_accum', 'distance_to_canal_m', 'surface_impervious_pct'
    ]
    for col in spatial_features:
        val = topo_dict.get(col)
        df[col] = 0.0 if val is None else val

    swvl1_val = topo_dict.get("swvl1")
    swvl1_val = 0.0 if swvl1_val is None else swvl1_val

    df['swvl1_x_elevation'] = swvl1_val * df['elevation']
    df['tp_x_elevation'] = df['tp_mm'] * df['elevation']
    df['tp_x_distance_canal'] = df['tp_mm'] / (df['distance_to_canal_m'] + 1)
    df['swvl1_x_distance_canal'] = swvl1_val * df['distance_to_canal_m']

    low_elev_threshold = topo_dict.get("low_elev_threshold")
    low_elev_threshold = 0.0 if low_elev_threshold is None else low_elev_threshold
    df['is_low_lying'] = (df['elevation'] < low_elev_threshold).astype(int)
    df['rain_on_low_ground'] = df['tp_mm'] * df['is_low_lying']

    probs = model.predict_proba(df[FEATURE_COLS])[:, 1]
    df["flood_prob"] = probs
    df["flood_predicted"] = (probs >= threshold).astype(int)

    def get_risk(p):
        if p >= 0.7: return "HIGH"
        if p >= 0.4: return "MODERATE"
        return "LOW"
    df["risk_level"] = df["flood_prob"].apply(get_risk)
    return df