"""
synthetic_gtfs.py — PMPML bus fleet simulation.

Real PMPML facts used in this simulation:
  • Fleet: 2,009 buses (Feb 2024, PMC report)
  • Daily ridership: ~10 lakh (1 million) passengers
  • Operating hours: 05:30–24:00 (night service 23:45–05:00, hourly)
  • Bus capacity: Standard 64 pax, Double-decker 85 pax, Midi 29 pax
  • Avg pax/bus/day: ~730 (PMC 2023)
  • Peak: 07:00–09:30 (AM) and 17:00–20:00 (PM)
  • CNG fleet ~1,536 buses, Electric ~473, Midi remaining
  • BRT routes: 51 Rainbow corridors with dedicated lanes
  • Speed in city: 16–28 km/h (BRT corridors: up to 35 km/h)
"""

import random
import math
from datetime import datetime
from typing import List, Dict

random.seed(42)

# Real PMPML fleet constants
PMPML_FLEET_TOTAL    = 2009
PMPML_DAILY_RIDERSHIP = 1_000_000
BUS_CAPACITY = {
    "standard":     64,   # standard CNG bus (54 seated + ~10 standing)
    "double_decker":85,   # DD electric (65 seated + 20 standing)
    "midi":         29,   # Punyadasham mini bus
    "electric":     64,   # standard electric
}
# Real Pune peak hour occupancy (fraction of capacity)
PEAK_OCCUPANCY = {
    5:0.35, 6:0.55, 7:0.82, 8:0.95, 9:0.78,
    10:0.55,11:0.50,12:0.56,13:0.60,14:0.52,
    15:0.55,16:0.70,17:0.90,18:0.98,19:0.85,
    20:0.68,21:0.50,22:0.38,23:0.20, 0:0.08,
}

# ─────────────────────────────────────────────────────────────────────────────
# REAL PUNE STOP COORDINATES (approximate)
# ─────────────────────────────────────────────────────────────────────────────
PUNE_STOPS = {
    "shivajinagar": {"id": "S01", "name": "Shivajinagar Bus Stand", "lat": 18.5308, "lon": 73.8474},
    "hinjewadi": {"id": "S02", "name": "Hinjewadi Phase 1", "lat": 18.5912, "lon": 73.7389},
    "hinjewadi_p2": {"id": "S03", "name": "Hinjewadi Phase 2", "lat": 18.5975, "lon": 73.7207},
    "hinjewadi_p3": {"id": "S04", "name": "Hinjewadi Phase 3", "lat": 18.6025, "lon": 73.7050},
    "baner": {"id": "S05", "name": "Baner Road", "lat": 18.5590, "lon": 73.7868},
    "balewadi": {"id": "S06", "name": "Balewadi Stadium", "lat": 18.5761, "lon": 73.7741},
    "aundh": {"id": "S07", "name": "Aundh", "lat": 18.5585, "lon": 73.8074},
    "kothrud": {"id": "S08", "name": "Kothrud Depot", "lat": 18.5074, "lon": 73.8077},
    "deccan": {"id": "S09", "name": "Deccan Gymkhana", "lat": 18.5158, "lon": 73.8418},
    "fc_road": {"id": "S10", "name": "FC Road", "lat": 18.5236, "lon": 73.8432},
    "swargate": {"id": "S11", "name": "Swargate", "lat": 18.5018, "lon": 73.8560},
    "hadapsar": {"id": "S12", "name": "Hadapsar", "lat": 18.5092, "lon": 73.9259},
    "magarpatta": {"id": "S13", "name": "Magarpatta City", "lat": 18.5121, "lon": 73.9290},
    "katraj": {"id": "S14", "name": "Katraj", "lat": 18.4526, "lon": 73.8612},
    "warje": {"id": "S15", "name": "Warje", "lat": 18.4824, "lon": 73.8008},
    "pune_station": {"id": "S16", "name": "Pune Railway Station", "lat": 18.5293, "lon": 73.8742},
    "nigdi": {"id": "S17", "name": "Nigdi", "lat": 18.6488, "lon": 73.7684},
    "pimpri": {"id": "S18", "name": "Pimpri", "lat": 18.6294, "lon": 73.7997},
    "akurdi": {"id": "S19", "name": "Akurdi", "lat": 18.6437, "lon": 73.7698},
    "chinchwad": {"id": "S20", "name": "Chinchwad", "lat": 18.6178, "lon": 73.7963},
    "gahunje": {"id": "S21", "name": "MCA Gahunje Stadium", "lat": 18.6511, "lon": 73.7423},
    "wakad": {"id": "S22", "name": "Wakad", "lat": 18.5993, "lon": 73.7590},
    "pcmc": {"id": "S23", "name": "PCMC Bus Stand", "lat": 18.6297, "lon": 73.8051},
    "viman_nagar": {"id": "S24", "name": "Viman Nagar", "lat": 18.5679, "lon": 73.9143},
    "kharadi": {"id": "S25", "name": "Kharadi IT Park", "lat": 18.5534, "lon": 73.9398},
    "koregaon": {"id": "S26", "name": "Koregaon Park", "lat": 18.5369, "lon": 73.8936},
    "kalyani_nagar": {"id": "S27", "name": "Kalyani Nagar", "lat": 18.5449, "lon": 73.9045},
    "yerwada": {"id": "S28", "name": "Yerwada", "lat": 18.5544, "lon": 73.8993},
    "ramwadi": {"id": "S29", "name": "Ramwadi (Metro)", "lat": 18.5518, "lon": 73.9125},
    "civil": {"id": "S30", "name": "Civil Court", "lat": 18.5184, "lon": 73.8567},
}

# ─────────────────────────────────────────────────────────────────────────────
# ROUTE DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────
ROUTES = [
    {
        "route_id": "R155",
        "route_name": "Route 155",
        "description": "Shivajinagar → Baner → Balewadi → Hinjewadi",
        "color": "#00D4FF",
        "stops": ["shivajinagar", "fc_road", "aundh", "baner", "balewadi", "wakad", "hinjewadi", "hinjewadi_p2", "hinjewadi_p3"],
        "base_demand": 850,
        "peak_multiplier": 3.4,
        "fleet_assigned": 12,
        "frequency_min": 8,
        "type": "high_demand",
        "corridor": "IT_corridor",
    },
    {
        "route_id": "R50",
        "route_name": "Route 50",
        "description": "Kothrud → Deccan → Shivajinagar",
        "color": "#FF6B35",
        "stops": ["kothrud", "warje", "deccan", "fc_road", "shivajinagar"],
        "base_demand": 420,
        "peak_multiplier": 2.1,
        "fleet_assigned": 8,
        "frequency_min": 12,
        "type": "medium_demand",
        "corridor": "west_corridor",
    },
    {
        "route_id": "R160",
        "route_name": "Route 160",
        "description": "Deccan → Aundh → Hinjewadi",
        "color": "#7B2FFF",
        "stops": ["deccan", "shivajinagar", "aundh", "baner", "hinjewadi", "hinjewadi_p2"],
        "base_demand": 620,
        "peak_multiplier": 2.8,
        "fleet_assigned": 10,
        "frequency_min": 10,
        "type": "high_demand",
        "corridor": "IT_corridor",
    },
    {
        "route_id": "R22",
        "route_name": "Route 22",
        "description": "Swargate → Hadapsar → Magarpatta",
        "color": "#00FF94",
        "stops": ["swargate", "civil", "hadapsar", "magarpatta"],
        "base_demand": 380,
        "peak_multiplier": 1.9,
        "fleet_assigned": 7,
        "frequency_min": 15,
        "type": "medium_demand",
        "corridor": "east_corridor",
    },
    {
        "route_id": "R11",
        "route_name": "Route 11",
        "description": "Katraj → Deccan → Shivajinagar",
        "color": "#FFD700",
        "stops": ["katraj", "swargate", "deccan", "shivajinagar", "pune_station"],
        "base_demand": 550,
        "peak_multiplier": 2.3,
        "fleet_assigned": 9,
        "frequency_min": 10,
        "type": "high_demand",
        "corridor": "south_corridor",
    },
    {
        "route_id": "R72",
        "route_name": "Route 72",
        "description": "Pune Station → Koregaon → Viman Nagar",
        "color": "#FF3CAC",
        "stops": ["pune_station", "koregaon", "kalyani_nagar", "yerwada", "ramwadi", "viman_nagar"],
        "base_demand": 470,
        "peak_multiplier": 2.2,
        "fleet_assigned": 8,
        "frequency_min": 12,
        "type": "medium_demand",
        "corridor": "airport_corridor",
    },
    {
        "route_id": "R47",
        "route_name": "Route 47",
        "description": "Nigdi → Pimpri → Chinchwad → PCMC",
        "color": "#FF9F1C",
        "stops": ["nigdi", "akurdi", "chinchwad", "pimpri", "pcmc"],
        "base_demand": 490,
        "peak_multiplier": 2.0,
        "fleet_assigned": 9,
        "frequency_min": 12,
        "type": "medium_demand",
        "corridor": "north_corridor",
    },
    {
        "route_id": "R123",
        "route_name": "Route 123",
        "description": "PCMC → Wakad → Hinjewadi",
        "color": "#2BFFDD",
        "stops": ["pcmc", "pimpri", "wakad", "hinjewadi", "hinjewadi_p2"],
        "base_demand": 680,
        "peak_multiplier": 3.1,
        "fleet_assigned": 11,
        "frequency_min": 9,
        "type": "high_demand",
        "corridor": "IT_corridor",
    },
    {
        "route_id": "R204",
        "route_name": "Route 204",
        "description": "Swargate → Viman Nagar → Kharadi",
        "color": "#FF6B9D",
        "stops": ["swargate", "hadapsar", "kalyani_nagar", "viman_nagar", "kharadi"],
        "base_demand": 330,
        "peak_multiplier": 1.8,
        "fleet_assigned": 6,
        "frequency_min": 18,
        "type": "low_demand",
        "corridor": "east_corridor",
    },
    {
        "route_id": "R333",
        "route_name": "Route 333",
        "description": "Katraj → Warje → Kothrud Express",
        "color": "#B4FF39",
        "stops": ["katraj", "warje", "kothrud", "deccan"],
        "base_demand": 290,
        "peak_multiplier": 1.6,
        "fleet_assigned": 5,
        "frequency_min": 20,
        "type": "low_demand",
        "corridor": "south_west",
    },
]

# Metro lines
METRO_LINES = [
    {
        "line_id": "M1",
        "name": "Metro Line 1 (Purple)",
        "stations": [
            {"name": "PCMC", "lat": 18.6297, "lon": 73.8051},
            {"name": "Phugewadi", "lat": 18.6191, "lon": 73.8109},
            {"name": "Dapodi", "lat": 18.6085, "lon": 73.8175},
            {"name": "Bopodi", "lat": 18.5982, "lon": 73.8252},
            {"name": "Khadki", "lat": 18.5854, "lon": 73.8353},
            {"name": "Range Hills", "lat": 18.5749, "lon": 73.8415},
            {"name": "Shivajinagar", "lat": 18.5308, "lon": 73.8474},
            {"name": "Civil Court", "lat": 18.5184, "lon": 73.8567},
            {"name": "Budhwar Peth", "lat": 18.5101, "lon": 73.8594},
            {"name": "Mandai", "lat": 18.5037, "lon": 73.8622},
            {"name": "Swargate", "lat": 18.5018, "lon": 73.8560},
        ],
        "frequency_min": 5,
        "color": "#9B59B6",
    }
]

# ─────────────────────────────────────────────────────────────────────────────
# BUS FLEET SIMULATION
# ─────────────────────────────────────────────────────────────────────────────

def _interpolate(lat1, lon1, lat2, lon2, t):
    """Linear interpolation between two coordinates."""
    return lat1 + (lat2 - lat1) * t, lon1 + (lon2 - lon1) * t


def _haversine(lat1, lon1, lat2, lon2):
    """Distance in km between two coordinates."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


_bus_states: Dict = {}  # bus_id -> state


def _init_buses():
    """Initialize all buses across all routes."""
    buses = []
    bus_id_counter = 1
    for route in ROUTES:
        stops_in_route = [PUNE_STOPS[s] for s in route["stops"] if s in PUNE_STOPS]
        n_buses = route["fleet_assigned"]
        for i in range(n_buses):
            progress = i / n_buses  # spread buses across route
            seg_float = progress * (len(stops_in_route) - 1)
            seg_idx = min(int(seg_float), len(stops_in_route) - 2)
            seg_t = seg_float - seg_idx
            s1, s2 = stops_in_route[seg_idx], stops_in_route[seg_idx + 1]
            lat, lon = _interpolate(s1["lat"], s1["lon"], s2["lat"], s2["lon"], seg_t)
            # Add realistic noise
            lat += random.uniform(-0.002, 0.002)
            lon += random.uniform(-0.002, 0.002)
            speed = random.uniform(18, 38)  # km/h in city traffic
            delay_min = random.choices([0, 0, 0, 2, 4, 8, 12], weights=[30, 25, 20, 12, 7, 4, 2])[0]
            occupancy = random.randint(20, 95)
            bid = f"BUS{bus_id_counter:03d}"
            bus = {
                "bus_id": bid,
                "route_id": route["route_id"],
                "route_name": route["route_name"],
                "lat": lat,
                "lon": lon,
                "speed_kmh": speed,
                "delay_min": delay_min,
                "occupancy_pct": occupancy,
                "status": "breakdown" if random.random() < 0.02 else ("delayed" if delay_min > 5 else "on_time"),
                "next_stop": stops_in_route[min(seg_idx + 1, len(stops_in_route) - 1)]["name"],
                "eta_next_stop_min": max(1, int((_haversine(lat, lon, s2["lat"], s2["lon"]) / speed) * 60)),
                "passengers": int(occupancy / 100 * 80),
                "capacity": 80,
                "_seg_idx": seg_idx,
                "_seg_t": seg_t,
                "_stops": stops_in_route,
                "_direction": 1,  # 1 = forward, -1 = backward
            }
            _bus_states[bid] = bus
            buses.append(bid)
            bus_id_counter += 1
    return buses


_bus_ids = _init_buses()


def simulate_bus_tick():
    """Move all buses one step forward along their routes. Call every ~10s."""
    updated = []
    for bid, state in _bus_states.items():
        stops = state["_stops"]
        seg_idx = state["_seg_idx"]
        seg_t = state["_seg_t"]
        direction = state["_direction"]
        speed = state["speed_kmh"]  # km/h

        if state["status"] == "breakdown":
            # 5% chance recovery per tick
            if random.random() < 0.05:
                state["status"] = "on_time"
            updated.append(dict(state))
            continue

        # Advance along segment (tick = 10 seconds = 10/3600 hours)
        tick_hours = 10 / 3600
        dist_per_tick = speed * tick_hours  # km
        s1, s2 = stops[seg_idx], stops[min(seg_idx + 1, len(stops) - 1)]
        seg_dist = _haversine(s1["lat"], s1["lon"], s2["lat"], s2["lon"])
        if seg_dist < 0.001:
            seg_dist = 0.5
        delta_t = dist_per_tick / seg_dist
        seg_t += delta_t * direction

        if seg_t >= 1.0:
            seg_t = 0.0
            seg_idx += 1
            if seg_idx >= len(stops) - 1:
                seg_idx = len(stops) - 2
                direction = -1
        elif seg_t <= 0.0:
            seg_t = 1.0
            seg_idx -= 1
            if seg_idx < 0:
                seg_idx = 0
                direction = 1

        s1, s2 = stops[seg_idx], stops[min(seg_idx + 1, len(stops) - 1)]
        lat, lon = _interpolate(s1["lat"], s1["lon"], s2["lat"], s2["lon"], seg_t)
        lat += random.uniform(-0.0005, 0.0005)
        lon += random.uniform(-0.0005, 0.0005)

        # Random occupancy fluctuation
        occ = state["occupancy_pct"] + random.randint(-5, 5)
        occ = max(5, min(100, occ))
        # Mean-reverting delay: drift back toward 0 when high, occasionally worsen
        cur_delay = state["delay_min"]
        if cur_delay > 10:
            delta = random.choices([-2, -1, -1, 0, 1], weights=[15, 35, 30, 15, 5])[0]
        elif cur_delay > 5:
            delta = random.choices([-2, -1, 0, 1, 2], weights=[10, 30, 35, 20, 5])[0]
        elif cur_delay > 0:
            delta = random.choices([-1, 0, 0, 1, 2], weights=[30, 40, 15, 10, 5])[0]
        else:
            delta = random.choices([0, 0, 1, 2], weights=[50, 30, 15, 5])[0]
        delay = max(0, min(30, cur_delay + delta))
        status = "breakdown" if random.random() < 0.004 else ("delayed" if delay > 5 else "on_time")
        if occ > 85:
            status = "crowded"

        state.update({
            "lat": lat, "lon": lon,
            "_seg_idx": seg_idx, "_seg_t": seg_t, "_direction": direction,
            "occupancy_pct": occ,
            "delay_min": delay,
            "status": status,
            "next_stop": s2["name"],
            "eta_next_stop_min": max(1, int((_haversine(lat, lon, s2["lat"], s2["lon"]) / speed) * 60)),
            "passengers": int(occ / 100 * 80),
            "speed_kmh": speed + random.uniform(-3, 3),
        })
        updated.append({k: v for k, v in state.items() if not k.startswith("_")})
    return updated


def get_all_buses():
    """Return current snapshot of all buses (without internal _ keys)."""
    return [{k: v for k, v in s.items() if not k.startswith("_")} for s in _bus_states.values()]


# ── Aliases used by main.py v2 ────────────────────────────────────────────
def get_buses():
    return get_all_buses()


def get_all_routes():
    return ROUTES


def get_all_stops():
    return list(PUNE_STOPS.values())


def get_metro_lines():
    return METRO_LINES


def initialise_buses(routes):
    """
    Initialise PMPML bus fleet from GTFS routes.

    Uses real PMPML constants:
    - Bus capacity by type (standard 64, double-decker 85, midi 29)
    - Peak-hour-aware occupancy (95% at 8 AM, 10% at midnight)
    - Fleet sizing from actual trip_count and route demand
    - 1.5% breakdown rate (realistic for aging Indian fleet)
    - Speed: 18–28 km/h city, 25–35 km/h BRT
    """
    global _bus_states
    _bus_states.clear()
    buses = []
    counter = 1
    now_hour = datetime.now().hour
    base_occ = PEAK_OCCUPANCY.get(now_hour, 0.55)  # real occupancy for current hour

    for route in routes:
        stops_raw = route.get("stop_coordinates", [])
        if len(stops_raw) < 2:
            continue

        stops = [{"name": s["name"], "lat": s["lat"], "lon": s["lon"]} for s in stops_raw]

        # Real fleet sizing: use GTFS trip_count as proxy
        trip_count = route.get("daily_trips", 20)
        fleet_assigned = route.get("fleet_assigned", max(2, trip_count // 8))
        n_buses = max(2, min(20, fleet_assigned))

        # Bus type & capacity from GTFS loader
        bus_type = route.get("bus_type", "standard")
        capacity  = BUS_CAPACITY.get(bus_type, 64)

        # Speed by category
        category = route.get("category", "CITY")
        if category == "BRT":
            speed_range = (25, 35)
        elif category == "EXPRESS":
            speed_range = (22, 32)
        else:
            speed_range = (16, 26)

        for i in range(n_buses):
            progress  = i / max(n_buses - 1, 1)
            seg_float = progress * (len(stops) - 1)
            seg_idx   = min(int(seg_float), len(stops) - 2)
            seg_t     = seg_float - seg_idx
            s1, s2    = stops[seg_idx], stops[min(seg_idx + 1, len(stops) - 1)]
            lat, lon  = _interpolate(s1["lat"], s1["lon"], s2["lat"], s2["lon"], seg_t)
            lat += random.uniform(-0.001, 0.001)
            lon += random.uniform(-0.001, 0.001)

            speed = random.uniform(*speed_range)

            # Realistic Pune delay distribution at init: ~55% on-schedule
            delay = random.choices(
                [0, 0, 2, 3, 6, 10, 15],
                weights=[30, 25, 20, 10, 8, 5, 2]
            )[0]

            # Occupancy: peak-hour aware + per-bus noise
            occ_frac = base_occ + random.uniform(-0.15, 0.15)
            occ = max(5, min(100, int(occ_frac * 100)))
            passengers = int(occ / 100 * capacity)

            # Real breakdown rate: ~1.5% of fleet at any time
            is_breakdown = random.random() < 0.015
            if is_breakdown:
                status = "breakdown"
            elif occ > 85:
                status = "crowded"
            elif delay > 5:
                status = "delayed"
            else:
                status = "on_time"

            bid = f"PMP{counter:04d}"  # PMPML bus ID format
            bus = {
                "bus_id":            bid,
                "route_id":          route["route_id"],
                "route_name":        route["route_name"],
                "route_short_name":  route.get("route_short_name", ""),
                "category":          category,
                "bus_type":          bus_type,
                "lat":  lat, "lon": lon,
                "speed_kmh":         round(speed, 1),
                "delay_min":         delay,
                "occupancy_pct":     occ,
                "passengers":        passengers,
                "capacity":          capacity,
                "status":            status,
                "next_stop":         s2["name"],
                "eta_next_stop_min": max(1, int(
                    (_haversine(lat, lon, s2["lat"], s2["lon"]) / speed) * 60
                )),
                "_seg_idx":  seg_idx,
                "_seg_t":    seg_t,
                "_stops":    stops,
                "_direction": 1,
                "_speed_range": speed_range,
                "_capacity":    capacity,
            }
            _bus_states[bid] = bus
            buses.append({k: v for k, v in bus.items() if not k.startswith("_")})
            counter += 1

    print(f"   🚌 initialise_buses: {len(buses)} buses across {len(routes)} routes "
          f"(PMPML real fleet: {PMPML_FLEET_TOTAL} buses, this demo: {len(routes)} routes)")
    return buses


def simulate_bus_tick(bus_or_all=None, routes=None, forecasts=None):
    """
    Advance simulation. Accepts both old (no args) and new (bus, routes, forecasts) calling styles.
    When called with a single bus dict, returns updated bus dict.
    When called with no args, moves all buses and returns list.
    """
    if bus_or_all is not None and isinstance(bus_or_all, dict):
        # New style: called per bus from main.py v2
        bid = bus_or_all.get("bus_id")
        if bid and bid in _bus_states:
            _tick_one(bid)
            return {k: v for k, v in _bus_states[bid].items() if not k.startswith("_")}
        return bus_or_all
    # Old style: move all, return list
    return _tick_all()


def _tick_one(bid: str):
    """Advance a single bus one simulation step."""
    state = _bus_states.get(bid)
    if not state:
        return
    stops     = state["_stops"]
    seg_idx   = state["_seg_idx"]
    seg_t     = state["_seg_t"]
    direction = state["_direction"]
    speed     = state["speed_kmh"]

    if state["status"] == "breakdown":
        if random.random() < 0.05:
            state["status"] = "on_time"
        return

    tick_hours  = 10 / 3600
    dist_tick   = speed * tick_hours
    s1 = stops[seg_idx]
    s2 = stops[min(seg_idx + 1, len(stops) - 1)]
    seg_dist = max(0.001, _haversine(s1["lat"], s1["lon"], s2["lat"], s2["lon"]))
    seg_t   += (dist_tick / seg_dist) * direction

    if seg_t >= 1.0:
        seg_t, seg_idx = 0.0, seg_idx + 1
        if seg_idx >= len(stops) - 1:
            seg_idx, direction = len(stops) - 2, -1
    elif seg_t <= 0.0:
        seg_t, seg_idx = 1.0, seg_idx - 1
        if seg_idx < 0:
            seg_idx, direction = 0, 1

    s1 = stops[seg_idx]
    s2 = stops[min(seg_idx + 1, len(stops) - 1)]
    lat, lon = _interpolate(s1["lat"], s1["lon"], s2["lat"], s2["lon"], seg_t)
    lat += random.uniform(-0.0005, 0.0005)
    lon += random.uniform(-0.0005, 0.0005)

    occ = max(5, min(100, state["occupancy_pct"] + random.randint(-5, 5)))
    # Mean-reverting delay logic (same as _tick_all path)
    cur_delay = state.get("delay_min", 0)
    if cur_delay > 10:
        delta = random.choices([-2, -1, -1, 0, 1], weights=[15, 35, 30, 15, 5])[0]
    elif cur_delay > 5:
        delta = random.choices([-2, -1, 0, 1, 2], weights=[10, 30, 35, 20, 5])[0]
    elif cur_delay > 0:
        delta = random.choices([-1, 0, 0, 1, 2], weights=[30, 40, 15, 10, 5])[0]
    else:
        delta = random.choices([0, 0, 1, 2], weights=[50, 30, 15, 5])[0]
    delay = max(0, min(30, cur_delay + delta))
    status = "breakdown" if random.random() < 0.004 else (
             "crowded" if occ > 85 else "delayed" if delay > 5 else "on_time")

    state.update({
        "lat": lat, "lon": lon,
        "_seg_idx": seg_idx, "_seg_t": seg_t, "_direction": direction,
        "occupancy_pct": occ, "delay_min": delay, "status": status,
        "next_stop": s2["name"],
        "eta_next_stop_min": max(1, int((_haversine(lat, lon, s2["lat"], s2["lon"]) / speed) * 60)),
        "passengers": int(occ / 100 * 80),
        "speed_kmh": speed + random.uniform(-3, 3),
    })


def _tick_all():
    """Move all buses (old-style call)."""
    for bid in list(_bus_states.keys()):
        _tick_one(bid)
    return [{k: v for k, v in s.items() if not k.startswith("_")} for s in _bus_states.values()]
