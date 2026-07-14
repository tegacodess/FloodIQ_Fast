import os
import time
from datetime import datetime, timedelta
import requests
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"

# Hardcoded 95th percentile storm thresholds derived from your 5-year training matrix
THRESHOLD_3DAY = 36.89  # Statistically engineered 3-day multi-storm constraint
THRESHOLD_1DAY = 16.72  # Statistically engineered 1-day heavy cloudburst constraint

def sync_yesterdays_weather():
    # Calculate target dates
    yesterday_dt = datetime.utcnow() - timedelta(days=1)
    yesterday = yesterday_dt.strftime("%Y-%m-%d")
    
    # Range tracker to pull the trailing 4-day history for accurate rolling feature engineering
    four_days_ago = (yesterday_dt - timedelta(days=4)).strftime("%Y-%m-%d")
    
    print(f"Starting dynamic leak-free sync for date: {yesterday}")
    
    response = supabase.table("locations").select("id, latitude, longitude").execute()
    locations = response.data
    
    if not locations:
        print("No locations found in the database. Exiting.")
        return

    print(f"Processing daily update for {len(locations)} locations.")

    for i, loc in enumerate(locations, 1):
        loc_id = loc["id"]
        lat = loc["latitude"]
        lon = loc["longitude"]
        
        time.sleep(1.5)  # Pace queries defensively to prevent API rate limiting
        
        params = {
            "latitude": lat, "longitude": lon,
            "start_date": yesterday, "end_date": yesterday,
            "hourly": ["temperature_2m", "precipitation", "soil_moisture_0_to_7cm", "runoff"],
            "timezone": "Africa/Lagos"
        }
        
        try:
            res = requests.get(ARCHIVE_API_URL, params=params, timeout=30).json()
            
            if "hourly" not in res:
                error_reason = res.get("reason", "Unknown API error or Throttling")
                print(f"Warning: Primary API issue: {error_reason}. Retrying in 2 seconds.")
                
                time.sleep(2)
                res = requests.get(ARCHIVE_API_URL, params=params, timeout=30).json()
                
                if "hourly" not in res:
                    final_reason = res.get("reason", "Rate limited / IP Blocked")
                    print(f"Complete API failure for ({lat}, {lon}): {final_reason}. Skipping.")
                    continue
            
            hourly = res["hourly"]
            
            hr_df = pd.DataFrame({
                "time": pd.to_datetime(hourly["time"]),
                "temp": hourly["temperature_2m"], 
                "tp": hourly["precipitation"],
                "swvl": hourly["soil_moisture_0_to_7cm"], 
                "runoff": hourly["runoff"]
            })
            
            # Aggregate raw 24-hour timeline metrics for yesterday
            yesterdays_tp = float(hr_df["tp"].sum())
            yesterdays_temp = float(hr_df["temp"].mean())
            yesterdays_swvl = float(hr_df["swvl"].mean())
            yesterdays_runoff = float(hr_df["runoff"].sum())
            
            # Query preceding database history to build rolling storm windows without data leaks
            history_res = supabase.table("flood_features").select("time, tp_mm")\
                .eq("location_id", loc_id)\
                .gte("time", four_days_ago)\
                .lte("time", yesterday)\
                .execute()
            
            # Construct local dataframe to compute historical multi-day accumulation tracks
            history_data = history_res.data or []
            
            # Append yesterday's live metrics into the context pool
            history_data.append({"time": yesterday, "tp_mm": yesterdays_tp})
            hist_df = pd.DataFrame(history_data).drop_duplicates(subset=['time'])
            hist_df['time'] = pd.to_datetime(hist_df['time'])
            hist_df = hist_df.sort_values(by='time').reset_index(drop=True)
            
            # Reconstruct the 3-day rolling check window
            hist_df['rolling_3day'] = hist_df['tp_mm'].rolling(window=3, min_periods=1).sum()
            
            # Isolate yesterday's targeted cumulative window sum
            current_row = hist_df[hist_df['time'].dt.strftime('%Y-%m-%d') == yesterday]
            rolling_3day_sum = float(current_row['rolling_3day'].values[0]) if not current_row.empty else yesterdays_tp
            
            # Determine operational flood label dynamically using explicit mathematical conditions
            is_flooded = 0
            if rolling_3day_sum > THRESHOLD_3DAY or yesterdays_tp > THRESHOLD_1DAY:
                is_flooded = 1
                
            # Compile structured production-ready row dictionary matching destination database schema
            daily_row = {
                "location_id": loc_id,
                "time": yesterday,
                "temp_c": yesterdays_temp,
                "tp_mm": yesterdays_tp,
                "swvl1": yesterdays_swvl,
                "runoff_mm": yesterdays_runoff,
                "flood_label": is_flooded
            }
            
            # Stream record straight up to database via high-speed upsert
            supabase.table("flood_features").upsert(daily_row, on_conflict="time,location_id").execute()
            
            if i % 100 == 0:
                print(f"Synced {i}/{len(locations)} locations successfully.")
                
        except Exception as e:
            print(f"Connection error at node {i} ({lat}, {lon}): {str(e)}")
            continue

    print("Weather sync completed successfully with integrated leak-free classification logic!")

if __name__ == "__main__":
    sync_yesterdays_weather()