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
    """
    Runs prediction based on dynamic topo data and weather inputs, 
    matching the training notebook logic.
    """
    df = weather_df.copy()
    
    # 1. Map dynamic topographic features from topo_dict
    # topo_dict comes from Supabase/API and should contain these keys
    spatial_features = [
        'elevation', 'slope', 'flow_accum', 'distance_to_canal_m', 'surface_impervious_pct'
    ]
    for col in spatial_features:
        df[col] = topo_dict.get(col, 0.0)

    # 2. Engineering features (based on training notebook logic)
    # Note: Ensure topo_dict contains 'swvl1' if being used for interaction
    swvl1_val = topo_dict.get("swvl1", 0.0)
    
    df['swvl1_x_elevation'] = swvl1_val * df['elevation']
    df['tp_x_elevation'] = df['tp_mm'] * df['elevation']
    df['tp_x_distance_canal'] = df['tp_mm'] / (df['distance_to_canal_m'] + 1)
    df['swvl1_x_distance_canal'] = swvl1_val * df['distance_to_canal_m']
    
    # Low lying logic (using quantile threshold from training)
    low_elev_threshold = topo_dict.get("low_elev_threshold", 0.0) 
    df['is_low_lying'] = (df['elevation'] < low_elev_threshold).astype(int)
    df['rain_on_low_ground'] = df['tp_mm'] * df['is_low_lying']

    # 3. Model Inference
    # Ensure FEATURE_COLS matches the order used in training
    probs = model.predict_proba(df[FEATURE_COLS])[:, 1]
    
    df["flood_prob"] = probs
    df["flood_predicted"] = (probs >= threshold).astype(int)
    
    # 4. Risk Level classification
    def get_risk(p):
        if p >= 0.7: return "HIGH", 
        if p >= 0.4: return "MODERATE", 
        return "LOW", 
    df["risk_level"] = df["flood_prob"].apply(lambda p: pd.Series(get_risk(p)))
    return df