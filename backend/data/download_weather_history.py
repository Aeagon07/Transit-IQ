"""
Download 3 years of real Pune historical weather from Open-Meteo (free, no API key).
Saves to data/pune_weather_history.csv for ML model training.

Run once: python data/download_weather_history.py
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime

PUNE_LAT = 18.5204
PUNE_LON = 73.8567

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "pune_weather_history.csv")

def download_historical_weather(start_date="2022-01-01", end_date="2024-12-31"):
    print(f"📡 Downloading Pune weather history {start_date} → {end_date} from Open-Meteo...")
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": PUNE_LAT,
        "longitude": PUNE_LON,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join([
            "temperature_2m",
            "precipitation",
            "weathercode",
            "windspeed_10m",
            "relative_humidity_2m",
            "rain",
        ]),
        "timezone": "Asia/Kolkata",
        "wind_speed_unit": "kmh",
    }

    try:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        raw = resp.json()
    except Exception as e:
        print(f"❌ Download failed: {e}")
        print("   Using cached fallback data if available...")
        return None

    hourly = raw.get("hourly", {})
    times = hourly.get("time", [])
    n = len(times)
    print(f"✅ Downloaded {n:,} hourly records ({n//24:,} days)")

    df = pd.DataFrame({
        "datetime": pd.to_datetime(times),
        "temperature_c":   hourly.get("temperature_2m", [None] * n),
        "precipitation_mm": hourly.get("precipitation", [None] * n),
        "rain_mm":         hourly.get("rain", [None] * n),
        "weathercode":     hourly.get("weathercode", [None] * n),
        "windspeed_kmh":   hourly.get("windspeed_10m", [None] * n),
        "humidity_pct":    hourly.get("relative_humidity_2m", [None] * n),
    })

    df["hour"]        = df["datetime"].dt.hour
    df["weekday"]     = df["datetime"].dt.weekday      # 0=Mon
    df["month"]       = df["datetime"].dt.month
    df["date"]        = df["datetime"].dt.date.astype(str)
    df["is_raining"]  = (df["precipitation_mm"] > 0.5).astype(int)
    df["heavy_rain"]  = (df["precipitation_mm"] > 5.0).astype(int)

    # Pune-specific rain-to-bus demand multiplier
    def rain_demand_mult(row):
        p = row["precipitation_mm"] or 0
        if p > 5:   return 1.65
        if p > 0.5: return 1.40
        return 1.0
    df["rain_demand_multiplier"] = df.apply(rain_demand_mult, axis=1)

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"💾 Saved to: {OUTPUT_PATH}")

    rain_days = df[df["is_raining"] == 1]["date"].nunique()
    heavy_days = df[df["heavy_rain"] == 1]["date"].nunique()
    total_days = df["date"].nunique()
    print(f"   Rain days:   {rain_days}/{total_days} ({100*rain_days/total_days:.1f}%)")
    print(f"   Heavy rain:  {heavy_days}/{total_days} ({100*heavy_days/total_days:.1f}%)")
    print(f"   Max rain:    {df['precipitation_mm'].max():.1f}mm/hour")
    print(f"   Avg temp:    {df['temperature_c'].mean():.1f}°C")
    return df


if __name__ == "__main__":
    df = download_historical_weather()
    if df is not None:
        print("\n📊 Sample rows:")
        print(df[df["is_raining"]==1][["datetime","temperature_c","precipitation_mm","rain_demand_multiplier"]].head(10).to_string())
