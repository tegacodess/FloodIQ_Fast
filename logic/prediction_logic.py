import numpy as np
import pandas as pd
import joblib
from .config import FEATURE_COLS, GRID_CELLS, FLOODIQ_MODEL

def load_model(model_path=FLOODIQ_MODEL):
    return joblib.load(model_path)

def nearest_grid(lat, lon):
    return min(GRID_CELLS, key=lambda c: (c[0]-lat)**2 + (c[1]-lon)**2)

def run_prediction(weather_df, topo, model, threshold=0.5):
    df = weather_df.copy()
    df["date"] = pd.to_datetime(df["date"])

    
    # Terrain features
    # Check if topo is a dictionary block or a direct float value
    # Handle elevation safe assignment
    if isinstance(topo, dict):
        df["elevation"] = topo.get("elevation", 0.0)
        df["slope"] = topo.get("slope", 0.0)
        df["flow_accum"] = topo.get("flow_accum", 0.0)
    else:
        # If topo is an array, list, or simple series of metrics, extract them directly
        # Adjust the indices below if your TOPO_DATA tuple sequence is ordered differently (e.g., [elevation, slope, flow_accum])
        df["elevation"] = float(topo[0]) if hasattr(topo, '__getitem__') else float(topo)
        df["slope"] = float(topo[1]) if hasattr(topo, '__getitem__') and len(topo) > 1 else 0.0
        df["flow_accum"] = float(topo[2]) if hasattr(topo, '__getitem__') and len(topo) > 2 else 0.0
    # Month
    df["month"] = df["date"].dt.month

    # Rolling features — fetch 5 prior days of archive tp_mm to seed the window
    # At inference time we only have 3 forecast days, so we approximate:
    # rolling_3day_feat = sum of previous 3 days tp_mm (all prior to today)
    # rolling_5day_feat = sum of previous 5 days tp_mm
    # Since we only have 3 forecast rows, shift(1) within the small window
    # and fill NaN with 0 (no prior rainfall info available)

    # Month
    df["month"] = df["date"].dt.month

    # Rolling features — fetch 5 prior days of archive tp_mm to seed the window
    # At inference time we only have 3 forecast days, so we approximate:
    # rolling_3day_feat = sum of previous 3 days tp_mm (all prior to today)
    # rolling_5day_feat = sum of previous 5 days tp_mm
    # Since we only have 3 forecast rows, shift(1) within the small window
    # and fill NaN with 0 (no prior rainfall info available)
    df["rolling_3day_feat"] = (
        df["tp_mm"].shift(1).rolling(3, min_periods=1).sum().fillna(0)
    )
    df["rolling_5day_feat"] = (
        df["tp_mm"].shift(1).rolling(5, min_periods=1).sum().fillna(0)
    )
    df["swvl1"] = df["swvl1"].fillna(0.25)
    df["runoff_mm"] = df["runoff_mm"].fillna(0.0)
    df["tp_mm"] = df["tp_mm"].fillna(0.0)
    df["temp_c"] = df["temp_c"].fillna(25.0)
    # Precipitation thresholding: if tp_mm < 1mm, reduce flood prob by 90%
    probs = model.predict_proba(df[FEATURE_COLS])[:, 1]
    probs = np.where(df["tp_mm"] < 1.0, probs * 0.1, probs)

    df["flood_prob"] = probs
    df["flood_predicted"] = (probs >= threshold).astype(int)
    

    def get_risk(p):
        if p >= 0.7: return "HIGH", "🔴"
        if p >= 0.4: return "MODERATE", "🟡"
        return "LOW", "🟢"

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%d %b %Y")      

    df[["risk_level", "risk_emoji"]] = df["flood_prob"].apply(
        lambda p: pd.Series(get_risk(p))
    )
    return df