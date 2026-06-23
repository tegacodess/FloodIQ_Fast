from __future__ import annotations

from datetime import datetime, date, timedelta

import numpy as np
import pandas as pd
import requests
import openmeteo_requests
import requests_cache
from retry_requests import retry
from supabase import create_client


from .config import (
    ARCHIVE_API_URL,
    FORECAST_API_URL,
    FORECAST_DAYS,
)



def _normalize_start_date(start_date):
    if start_date is None:
        return date.today()
    if isinstance(start_date, date):
        return start_date
    return pd.to_datetime(start_date).date()


def _replace_year_safe(target_date: date, year: int):
    try:
        return target_date.replace(year=year)
    except ValueError:
        return None


def _build_open_meteo_frame(data: dict):
    daily = data["daily"]
    hourly = data["hourly"]

    hourly_frame = pd.DataFrame({
        "time": pd.to_datetime(hourly["time"]),
        "soil_moisture": hourly["soil_moisture_0_to_7cm"],
        "runoff_hr": hourly["runoff"],
    })
    hourly_frame["date"] = hourly_frame["time"].dt.date
    aggregated = hourly_frame.groupby("date").agg(
        swvl1=("soil_moisture", "mean"),
        runoff_mm=("runoff_hr", "sum"),
    ).reset_index()

    aggregated = hourly_frame.groupby("date").agg(
    swvl1=("soil_moisture", "mean"),
    runoff_mm=("runoff_hr", "sum"),
    ).reset_index()

    # fill any missing soil moisture with Lagos wet season climatological mean
    aggregated["swvl1"] = aggregated["swvl1"].fillna(0.25)
    aggregated["runoff_mm"] = aggregated["runoff_mm"].fillna(0.0)

    

    records = []
    for index, date_string in enumerate(daily["time"]):
        date_value = pd.to_datetime(date_string).date()
        day_rows = aggregated[aggregated["date"] == date_value]
        swvl1 = float(day_rows["swvl1"].values[0]) if len(day_rows) else 0.2
        runoff_mm = float(day_rows["runoff_mm"].values[0]) if len(day_rows) else 0.0

        records.append({
            "date": date_string,
            "tp_mm": daily["precipitation_sum"][index] or 0.0,
            "temp_c": daily["temperature_2m_mean"][index] or 25.0,
            "swvl1": swvl1,
            "runoff_mm": runoff_mm,
        })

    return pd.DataFrame(records)

# Set up the cache and retry channels safely
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

def _fetch_open_meteo_window(api_url: str, lat: float, lon: float, days: int = 3, start_date=None):
    """
    Uses the official SDK to request high-fidelity hourly forecasts 
    for specific date targets using modular URL targets.
    """
    # 1. Fallback to today if no date is supplied
    if start_date is None:
        start_date = date.today()
    elif isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        
    end_date = start_date + timedelta(days=days - 1)

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "hourly": ["temperature_2m", "precipitation", "soil_moisture_0_to_10cm"],
        "timezone": "UTC"
    }

    # Use the modular api_url passed from fetch_weather
    responses = openmeteo.weather_api(api_url, params=params)
    response = responses[0] 

    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(1).ValuesAsNumpy()
    hourly_soil_moisture_0_to_10cm = hourly.Variables(2).ValuesAsNumpy()

    start_time = pd.to_datetime(hourly.Time(), unit="s", utc=True)
    
    hourly_data = {
        "date": pd.date_range(
            start=start_time,
            periods=len(hourly_temperature_2m), # Tells pandas exactly how many hours to generate
            freq="1h"
        )
    }
    
    hourly_data["temp_c"] = hourly_temperature_2m
    hourly_data["tp_mm"] = hourly_precipitation
    hourly_data["swvl1"] = hourly_soil_moisture_0_to_10cm
    hourly_data["runoff_mm"] = [p * 0.15 for p in hourly_precipitation]

    hourly_df = pd.DataFrame(data=hourly_data)

    # Group cleanly by date to give your model exactly 3 clean rows
    daily_df = hourly_df.groupby(hourly_df["date"].dt.date).agg({
        "temp_c": "mean",
        "tp_mm": "sum",
        "swvl1": "mean",
        "runoff_mm": "sum"
    }).reset_index()

    return daily_df

    


def calculate_last_available_run_window():
    """
    Calculates the exact start datetime anchor pointing to the most 
    recently completed 6-hour simulation run cycle (UTC).
    """
    # 1. Get current time in UTC (always match against vendor clock)
    now_utc = datetime.now(timezone.utc)
    
    # 2. Subtract 2 hours to account for model processing lag time
    adjusted_time = now_utc - timedelta(hours=2)
    
    # 3. Find the last completed 6-hour boundary hour integer
    run_hour = (adjusted_time.hour // 6) * 6
    
    # 4. Construct the precise timestamp anchor
    anchor_datetime = adjusted_time.replace(
        hour=run_hour, 
        minute=0, 
        second=0, 
        microsecond=0
    )
    
    return anchor_datetime

def _fetch_archive_climatology(lat: float, lon: float, days: int, start_date=None, years: int = 5):
    start_day = _normalize_start_date(start_date)
    buckets = {offset: [] for offset in range(days)}

    for year_offset in range(1, years + 1):
        sample_start = _replace_year_safe(start_day, start_day.year - year_offset)
        if sample_start is None:
            continue
        try:
            # 💡 FIXED: Passing ARCHIVE_API_URL cleanly as the first positional argument
            sample_frame = _fetch_open_meteo_window(
                ARCHIVE_API_URL, lat, lon, days, start_date=sample_start
            )
        except Exception as e:
            print(f"Climatology year offset -{year_offset} skipped: {str(e)}")
            continue

        for offset, (_, row) in enumerate(sample_frame.head(days).iterrows()):
            buckets[offset].append(row)

    records = []
    for offset in range(days):
        samples = buckets[offset]
        if not samples:
            continue

        sample_frame = pd.DataFrame(samples)
        target_date = start_day + timedelta(days=offset)
        records.append({
            "date": target_date.strftime("%Y-%m-%d"),
            "tp_mm": float(sample_frame["tp_mm"].mean()),
            "temp_c": float(sample_frame["temp_c"].mean()),
            "swvl1": float(sample_frame["swvl1"].mean()),
            "runoff_mm": float(sample_frame["runoff_mm"].mean()),
        })

    if not records:
        raise ValueError("Climatology fallback did not produce daily forecast rows")

    return pd.DataFrame(records)


def get_climatology_baseline(lat: float, lon: float, target_date: date):
    """
    Queries Supabase for the historical median of swvl1 and runoff_mm
    for the specific calendar month of the requested date.
    """
    target_month = target_date.month
    
    # 1. Query rows matching the location and the calendar month
    # Optimizing by pulling from your historical training tables
    response = supabase.table("historical_meteo_data") \
        .select("swvl1", "runoff_mm") \
        .eq("month", target_month) \
        .execute()
        
    data = response.data
    if not data:
        return 0.25, 0.0  # Safe emergency default if table check misses
        
    # 2. Calculate the historical median vectors using pandas/numpy
    import numpy as np
    swvl1_median = np.median([row['swvl1'] for row in data])
    runoff_median = np.median([row['runoff_mm'] for row in data])
    
    return float(swvl1_median), float(runoff_median)

def fetch_weather(lat, lon, days=FORECAST_DAYS, start_date=None):
    start_day = _normalize_start_date(start_date)
    today = date.today()
    forecast_horizon = today + timedelta(days=16)

    try:
        if start_day < today:
            # Passes ARCHIVE_API_URL first
            return _fetch_open_meteo_window(ARCHIVE_API_URL, lat, lon, days, start_date=start_day), None, "archive"
        if start_day <= forecast_horizon:
            # Passes FORECAST_API_URL first
            return _fetch_open_meteo_window(FORECAST_API_URL, lat, lon, days, start_date=start_day), None, "forecast"
        
        return _fetch_archive_climatology(lat, lon, days, start_day), None, "climatology"

    except Exception as primary_error:
        try:
            return _fetch_archive_climatology(lat, lon, days, start_day), None, "climatology"
        except Exception as fallback_error:
            return None, f"Weather fetch failed: {primary_error}; climatology fallback failed: {fallback_error}", None            

def build_context(
    predictions: pd.DataFrame,
    location_name: str,
    lat: float,
    lon: float,
    grid_cell,
    weather_mode: str = "forecast",
):
    mode_descriptions = {
        "archive": "Historical analysis from archived weather data (selected date is in the past)",
        "forecast": "Forward-looking forecast from Open-Meteo",
        "climatology": "Climatology estimate built from historical archive samples",
    }
    mode_label = mode_descriptions.get(weather_mode, "Unknown weather data source")
    window_start = str(predictions["date"].min()) if not predictions.empty else "N/A"
    window_end = str(predictions["date"].max()) if not predictions.empty else "N/A"

    lines = [
        f"Location: {location_name} (Lat {lat:.4f}, Lon {lon:.4f})",
        f"Nearest ERA5 grid cell: {grid_cell}",
        f"Analysis generated on: {datetime.now().strftime('%Y-%m-%d')}",
        f"Weather source mode: {mode_label}",
        f"3-day analysis window: {window_start} to {window_end}",
        "",
        "3-Day Flood Risk Output:",
    ]
    for _, row in predictions.iterrows():
        lines.append(
            f"  • {row['date']}: {row['risk_level']} RISK (probability {row['flood_prob']*100:.1f}%, rainfall {row['tp_mm']:.1f}mm)"
        )
    return "\n".join(lines)

def groq_chat(api_key: str, history: list, context: str):
    system = f"""You are FloodIQ, a flood risk assistant for Lagos State, Nigeria.
    Help users understand flood predictions and give practical safety advice.
    CURRENT PREDICTION CONTEXT:
    {context}
    Guidelines:
    - Be concise, clear and practical
    - Give actionable advice specific to Lagos
    - Reference the prediction data when relevant
    - If weather source mode says archived/historical, explicitly say this is a retrospective analysis, not a future forecast
    - If weather source mode says climatology, explicitly say this is an estimate based on historical patterns
    - Prioritise safety
    - Keep responses under 200 words"""
    messages = [{"role": "system", "content": system}]
    for message in history:
        role = "assistant" if message["role"] in ("model", "assistant") else "user"
        messages.append({"role": role, "content": message["content"]})

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "max_tokens": 400,
                "temperature": 0.7,
            },
            timeout=12,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"], None
    except requests.exceptions.HTTPError as error:
        return None, f"Groq error {error.response.status_code}: {error.response.text}"
    except Exception as error:
        return None, str(error)
