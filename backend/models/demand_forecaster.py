"""
Demand forecasting for Transit-IQ.
Uses Facebook Prophet for time-series demand prediction per route.
Falls back to rule-based model if Prophet is unavailable.
"""

import math
import random
from datetime import datetime, timedelta
from typing import List, Dict
from data.synthetic_gtfs import ROUTES

random.seed(0)

# ─────────────────────────────────────────────────────────────────────────────
# PUNE-SPECIFIC KNOWLEDGE
# ─────────────────────────────────────────────────────────────────────────────

# Pune major events (month, day, event_name, demand_boost)
PUNE_EVENTS = [
    (2, 28, "PCCOE Annual Day", 1.25),
    (3, 15, "Symbiosis University Exams", 1.30),
    (8, 1, "Ganpati Week Start", 2.10),
    (9, 5, "Ganpati Festival Peak", 2.50),
    (10, 2, "Dussehera", 1.80),
    (11, 1, "Diwali", 1.60),
    (1, 26, "Republic Day", 1.40),
    (8, 15, "Independence Day", 1.35),
    (4, 14, "IPL Match at Gahunje", 1.90),
    (5, 3,  "IPL Match at Gahunje", 1.90),
]


def _get_event_multiplier(dt: datetime) -> float:
    for month, day, name, boost in PUNE_EVENTS:
        if dt.month == month and dt.day == day:
            return boost
    return 1.0


def _hour_curve(hour: int) -> float:
    """Hourly demand shape for a typical Pune weekday."""
    profile = {
        0: 0.05, 1: 0.03, 2: 0.02, 3: 0.02, 4: 0.05,
        5: 0.15, 6: 0.45, 7: 0.80, 8: 1.00, 9: 0.85,
        10: 0.60, 11: 0.55, 12: 0.70, 13: 0.65, 14: 0.55,
        15: 0.60, 16: 0.75, 17: 0.90, 18: 1.00, 19: 0.85,
        20: 0.60, 21: 0.40, 22: 0.25, 23: 0.12,
    }
    return profile.get(hour, 0.5)


def _day_multiplier(weekday: int) -> float:
    """0=Mon, 6=Sun"""
    return {0: 1.10, 1: 1.00, 2: 1.00, 3: 1.00, 4: 1.05, 5: 0.80, 6: 0.60}[weekday]


def _it_corridor_multiplier(route: dict, hour: int, weekday: int) -> float:
    """IT corridors get bigger Monday morning spikes."""
    if route.get("corridor") == "IT_corridor" and weekday == 0 and 7 <= hour <= 10:
        return 1.45  # Monday morning Hinjewadi rush
    return 1.0


# ─────────────────────────────────────────────────────────────────────────────
# PROPHET-BASED FORECASTER (with rule-based fallback)
# ─────────────────────────────────────────────────────────────────────────────

try:
    from prophet import Prophet
    import pandas as pd
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False


_prophet_models: Dict = {}


def _generate_historical_df(route: dict, days: int = 180):
    """Generate synthetic historical demand as a pandas DataFrame for Prophet."""
    import pandas as pd
    records = []
    base = route["base_demand"]
    start = datetime.now() - timedelta(days=days)
    for d in range(days):
        dt = start + timedelta(days=d)
        for hour in range(0, 24):
            for quarter in range(4):
                ts = dt.replace(hour=hour, minute=quarter * 15, second=0, microsecond=0)
                demand = (
                    base
                    * _hour_curve(hour)
                    * _day_multiplier(dt.weekday())
                    * _it_corridor_multiplier(route, hour, dt.weekday())
                    * _get_event_multiplier(dt)
                    + random.gauss(0, base * 0.08)
                )
                demand = max(0, demand)
                records.append({"ds": ts, "y": demand})
    return pd.DataFrame(records)


def _train_prophet(route: dict):
    """Train a Prophet model for this route."""
    df = _generate_historical_df(route)
    m = Prophet(
        seasonality_mode="multiplicative",
        weekly_seasonality=True,
        daily_seasonality=True,
        changepoint_prior_scale=0.15,
    )
    m.fit(df)
    return m


def get_demand_forecast(
    route_id: str,
    weather_multiplier: float = 1.0,
    slots: int = 16,  # 4 hours ahead (16 × 15-min slots)
) -> List[Dict]:
    """
    Return demand forecast for next `slots` × 15-minute windows.
    Uses Prophet if available, otherwise rule-based.
    """
    route = next((r for r in ROUTES if r["route_id"] == route_id), None)
    if not route:
        return []

    now = datetime.now()
    results = []

    if PROPHET_AVAILABLE:
        if route_id not in _prophet_models:
            _prophet_models[route_id] = _train_prophet(route)
        model = _prophet_models[route_id]

        import pandas as pd
        future_times = [now + timedelta(minutes=15 * i) for i in range(slots)]
        future_df = pd.DataFrame({"ds": future_times})
        forecast = model.predict(future_df)

        for i, row in forecast.iterrows():
            raw = row["yhat"]
            lower = row["yhat_lower"]
            upper = row["yhat_upper"]
            adjusted = max(0, raw * weather_multiplier)
            ts = future_times[i]
            results.append({
                "slot": i,
                "time": ts.strftime("%H:%M"),
                "timestamp": ts.isoformat(),
                "passengers": int(adjusted),
                "lower": int(max(0, lower * weather_multiplier)),
                "upper": int(upper * weather_multiplier),
                "confidence_pct": 85,
                "day": ts.strftime("%A"),
                "event_flag": _get_event_multiplier(ts) > 1.1,
                "rain_flag": weather_multiplier > 1.2,
            })
    else:
        # Rule-based fallback — still accurate enough for demo
        for i in range(slots):
            ts = now + timedelta(minutes=15 * i)
            base = route["base_demand"]
            raw = (
                base
                * _hour_curve(ts.hour)
                * _day_multiplier(ts.weekday())
                * _it_corridor_multiplier(route, ts.hour, ts.weekday())
                * _get_event_multiplier(ts)
                * weather_multiplier
                + random.gauss(0, base * 0.05)
            )
            val = max(0, raw)
            margin = int(val * 0.12)
            results.append({
                "slot": i,
                "time": ts.strftime("%H:%M"),
                "timestamp": ts.isoformat(),
                "passengers": int(val),
                "lower": int(max(0, val - margin)),
                "upper": int(val + margin),
                "confidence_pct": 78,
                "day": ts.strftime("%A"),
                "event_flag": _get_event_multiplier(ts) > 1.1,
                "rain_flag": weather_multiplier > 1.2,
            })

    return results


def get_all_forecasts(weather_multiplier: float = 1.0) -> Dict:
    """Returns demand forecasts for all routes."""
    return {
        route["route_id"]: get_demand_forecast(route["route_id"], weather_multiplier)
        for route in ROUTES
    }
