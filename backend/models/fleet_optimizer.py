"""
Fleet optimizer using Google OR-Tools.
Takes demand forecasts and outputs optimal bus frequency per route.
"""

import random
from typing import List, Dict
from data.synthetic_gtfs import ROUTES

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


def optimize_fleet(forecasts: Dict, current_buses: List[Dict]) -> List[Dict]:
    """
    Given demand forecasts and current bus positions,
    return a list of fleet rebalancing recommendations.
    """
    recommendations = []
    rec_id = 1

    # Count buses per route currently
    buses_per_route = {}
    for bus in current_buses:
        rid = bus.get("route_id", "")
        buses_per_route[rid] = buses_per_route.get(rid, 0) + 1

    for route in ROUTES:
        rid = route["route_id"]
        fc = forecasts.get(rid, [])
        if not fc:
            continue

        # Get next 2-hour slots (8 slots)
        near_term = fc[:8]
        peak_slot = max(near_term, key=lambda x: x["passengers"])
        peak_demand = peak_slot["passengers"]
        current_fleet = buses_per_route.get(rid, route["fleet_assigned"])
        capacity_per_bus = 80  # seats per bus
        current_capacity = current_fleet * capacity_per_bus * 0.85  # 85% efficiency
        demand_gap = peak_demand - current_capacity

        if ORTOOLS_AVAILABLE:
            buses_needed = _ortools_solve(peak_demand, current_fleet, capacity_per_bus)
        else:
            # Greedy fallback
            buses_needed = max(current_fleet, math.ceil(peak_demand / (capacity_per_bus * 0.85)))

        extra_buses = buses_needed - current_fleet

        if extra_buses >= 2:
            severity = "critical" if extra_buses >= 5 else "high" if extra_buses >= 3 else "medium"
            rec = _build_recommendation(rec_id, route, peak_slot, extra_buses, severity, fc)
            recommendations.append(rec)
            rec_id += 1
        elif extra_buses == 1:
            rec = _build_recommendation(rec_id, route, peak_slot, 1, "low", fc)
            recommendations.append(rec)
            rec_id += 1

        # Check for underutilized routes (might contribute buses)
        avg_demand = sum(s["passengers"] for s in near_term) / max(len(near_term), 1)
        if avg_demand < current_fleet * capacity_per_bus * 0.35 and current_fleet > 3:
            excess = current_fleet - max(2, int(avg_demand / (capacity_per_bus * 0.7)))
            if excess >= 1:
                rec = {
                    "id": f"REC{rec_id:03d}",
                    "type": "redeploy",
                    "route_id": rid,
                    "route_name": route["route_name"],
                    "route_color": route["color"],
                    "title": f"Redeploy {excess} bus{'es' if excess > 1 else ''} from {route['route_name']}",
                    "description": f"{route['route_name']} is running at only {int(avg_demand / (current_fleet * capacity_per_bus) * 100)}% capacity. Redeploy {excess} bus{'es' if excess > 1 else ''} to high-demand routes.",
                    "reason": f"Low utilization: {int(avg_demand)} passengers vs {current_fleet * capacity_per_bus} capacity.",
                    "impact": f"+{excess * capacity_per_bus} seats freed for reallocation",
                    "buses_delta": -excess,
                    "priority": "medium",
                    "status": "pending",
                    "time_window": peak_slot["time"],
                    "digital_twin": {
                        "before_wait_min": 12,
                        "after_wait_min": 12,
                        "fuel_saved_liters": excess * 3.2,
                    },
                    "tags": ["efficiency", "rebalancing"],
                }
                recommendations.append(rec)
                rec_id += 1

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    recommendations.sort(key=lambda r: priority_order.get(r.get("priority", "low"), 3))
    return recommendations


def _build_recommendation(rec_id, route, peak_slot, extra_buses, severity, fc):
    """Build a human-readable recommendation card."""
    near_wait_before = max(5, 40 - route["fleet_assigned"] * 2)
    near_wait_after = max(3, near_wait_before - extra_buses * 4)
    rain_flag = peak_slot.get("rain_flag", False)
    event_flag = peak_slot.get("event_flag", False)

    reasons = []
    if peak_slot["day"] == "Monday" and route.get("corridor") == "IT_corridor":
        reasons.append("Monday IT corridor rush")
    if rain_flag:
        reasons.append("Rain forecast — 2-wheeler → bus shift expected")
    if event_flag:
        reasons.append("Major Pune event detected")
    reasons.append(f"Demand forecast: {peak_slot['passengers']} passengers at {peak_slot['time']}")
    reason_str = " | ".join(reasons) if reasons else f"Demand spike predicted at {peak_slot['time']}"

    return {
        "id": f"REC{rec_id:03d}",
        "type": "add_buses",
        "route_id": route["route_id"],
        "route_name": route["route_name"],
        "route_color": route["color"],
        "title": f"Add {extra_buses} bus{'es' if extra_buses != 1 else ''} on {route['route_name']} at {peak_slot['time']}",
        "description": (
            f"Pre-position {extra_buses} additional bus{'es' if extra_buses != 1 else ''} "
            f"on {route['route_name']} ({route['description']}) by {peak_slot['time']}. "
            f"Expected demand: {peak_slot['passengers']} passengers."
        ),
        "reason": reason_str,
        "impact": f"Wait time: {near_wait_before} min → {near_wait_after} min | {extra_buses * 80} extra seats",
        "buses_delta": extra_buses,
        "priority": severity,
        "status": "pending",
        "time_window": peak_slot["time"],
        "forecast_data": fc[:8],
        "digital_twin": {
            "before_wait_min": near_wait_before,
            "after_wait_min": near_wait_after,
            "passengers_stranded_before": max(0, peak_slot["passengers"] - route["fleet_assigned"] * 68),
            "passengers_stranded_after": 0,
            "fuel_extra_liters": extra_buses * 4.5,
        },
        "tags": (
            ["rain_alert"] if rain_flag else []
            + ["event_spike"] if event_flag else []
            + ["IT_corridor"] if route.get("corridor") == "IT_corridor" else []
        ),
    }


def _ortools_solve(demand: int, current_buses: int, capacity: int) -> int:
    """
    Use OR-Tools CP-SAT to find minimum buses needed.
    """
    model = cp_model.CpModel()
    n_buses = model.NewIntVar(current_buses, current_buses + 20, "n_buses")
    model.Add(n_buses * int(capacity * 0.85) >= demand)
    model.Minimize(n_buses)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 1.0
    status = solver.Solve(model)
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return solver.Value(n_buses)
    return current_buses + max(0, int((demand - current_buses * capacity * 0.85) / (capacity * 0.85)) + 1)


# Missing math import
import math
