import pandas as pd

def build_prediction_features(df_weather: pd.DataFrame, df_geo: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms raw dynamic weather lookbacks and merges static terrain vectors
    on-the-fly to build the exact feature space expected by XGBoost.
    """
    # 1. Enforce chronological sequence for window operations
    df_weather['time'] = pd.to_datetime(df_weather['time'])
    df_weather = df_weather.sort_values(by='time').reset_index(drop=True)
    
    # 2. Extract Temporal Climatology Context
    df_weather['month'] = df_weather['time'].dt.month
    df_weather['is_rainy_s'] = df_weather['month'].isin([4, 5, 6, 7, 9, 10, 11]).astype(int)
    
    # 3. Compute Rolling Backwards Cumulative Baselines
    df_weather['rolling_3d'] = df_weather['tp_mm'].rolling(window=3, min_periods=1).sum()
    df_weather['rolling_5d'] = df_weather['tp_mm'].rolling(window=5, min_periods=1).sum()
    
    # 4. Integrate Static Structural Terrain Features
    final_df = pd.merge(df_weather, df_geo, on=['latitude', 'longitude'], how='left')
    
    # 5. Extract strictly the most recent row representing the prediction horizon
    latest_horizon_vector = final_df.iloc[[-1]].copy()
    
    return latest_horizon_vector