"""
Open-Meteo weather integration for Pune — no API key required.
"""

import requests
from datetime import datetime

PUNE_LAT = 18.5204
PUNE_LON = 73.8567

_weather_cache = {"data": None, "fetched_at": None}


def get_pune_weather() -> dict:
    """
    Fetch current Pune weather from Open-Meteo (free, no API key).
    Cached for 10 minutes.
    """
    now = datetime.utcnow()
    if (
        _weather_cache["data"] is not None
        and _weather_cache["fetched_at"] is not None
        and (now - _weather_cache["fetched_at"]).seconds < 600
    ):
        return _weather_cache["data"]

    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={PUNE_LAT}&longitude={PUNE_LON}"
            f"&current=temperature_2m,precipitation,weathercode,windspeed_10m,relative_humidity_2m"
            f"&hourly=precipitation_probability,temperature_2m"
            f"&forecast_days=1"
            f"&timezone=Asia/Kolkata"
        )
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        raw = resp.json()

        current = raw.get("current", {})
        hourly = raw.get("hourly", {})

        # Pick current hour rain probability
        current_hour = datetime.now().hour
        rain_prob = 0
        if "precipitation_probability" in hourly:
            probs = hourly["precipitation_probability"]
            if len(probs) > current_hour:
                rain_prob = probs[current_hour]

        # Decode weather code
        wcode = current.get("weathercode", 0)
        condition, icon = _decode_weather_code(wcode)

        weather = {
            "temperature_c": current.get("temperature_2m", 28),
            "precipitation_mm": current.get("precipitation", 0),
            "rain_probability": rain_prob,
            "wind_kmh": current.get("windspeed_10m", 10),
            "humidity_pct": current.get("relative_humidity_2m", 60),
            "condition": condition,
            "icon": icon,
            "is_raining": current.get("precipitation", 0) > 0.5,
            "high_rain_risk": rain_prob > 60,
            "demand_multiplier": _rain_demand_multiplier(rain_prob, current.get("precipitation", 0)),
            "source": "Open-Meteo (live)",
            "fetched_at": now.isoformat(),
        }

    except Exception as e:
        # Fallback to realistic Pune defaults
        weather = {
            "temperature_c": 28.5,
            "precipitation_mm": 0,
            "rain_probability": 15,
            "wind_kmh": 12,
            "humidity_pct": 65,
            "condition": "Partly Cloudy",
            "icon": "🌤️",
            "is_raining": False,
            "high_rain_risk": False,
            "demand_multiplier": 1.0,
            "source": "Fallback (Open-Meteo unavailable)",
            "fetched_at": now.isoformat(),
            "error": str(e),
        }

    _weather_cache["data"] = weather
    _weather_cache["fetched_at"] = now
    return weather


def _decode_weather_code(code: int):
    if code == 0:
        return "Clear Sky", "☀️"
    elif code in (1, 2, 3):
        return "Partly Cloudy", "⛅"
    elif code in (45, 48):
        return "Foggy", "🌫️"
    elif code in (51, 53, 55):
        return "Drizzle", "🌦️"
    elif code in (61, 63, 65):
        return "Rain", "🌧️"
    elif code in (71, 73, 75):
        return "Snow", "❄️"
    elif code in (80, 81, 82):
        return "Rain Showers", "🌧️"
    elif code in (95, 96, 99):
        return "Thunderstorm", "⛈️"
    else:
        return "Cloudy", "☁️"


def _rain_demand_multiplier(rain_prob: float, precip_mm: float) -> float:
    """
    Pune-specific: rain causes 2-wheeler → bus shift.
    Higher rain probability → higher bus demand.
    """
    if precip_mm > 5:
        return 1.65  # heavy rain: 65% demand surge
    elif precip_mm > 0.5:
        return 1.40  # moderate rain: 40% surge
    elif rain_prob > 75:
        return 1.30  # high rain risk: 30% surge (people pre-emptively switch)
    elif rain_prob > 50:
        return 1.15  # moderate risk: 15% surge
    elif rain_prob > 30:
        return 1.05  # slight risk: 5% surge
    else:
        return 1.0   # no rain: baseline


# ── Alias so both main.py v1 and v2 can import ────────────────────────────
get_weather = get_pune_weather

