import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("F1 Assistant")

BASE_URL = "https://api.openf1.org/v1"


def f1_get(endpoint: str, params: dict) -> list:
    """Helper to call OpenF1 API and return JSON."""
    response = requests.get(f"{BASE_URL}/{endpoint}", params=params)
    response.raise_for_status()
    return response.json()


@mcp.tool()
def get_sessions(year: int, country_name: str = None, session_name: str = None) -> list:
    """
    Get F1 sessions for a given year. Optionally filter by country or session type.
    Session types: 'Race', 'Qualifying', 'Sprint', 'Practice 1', 'Practice 2', 'Practice 3'.
    Example: get_sessions(2024, country_name='Monaco', session_name='Race')
    """
    params = {"year": year}
    if country_name:
        params["country_name"] = country_name
    if session_name:
        params["session_name"] = session_name
    data = f1_get("sessions", params)
    return [
        {
            "session_key": s["session_key"],
            "session_name": s["session_name"],
            "country": s["country_name"],
            "circuit": s["circuit_short_name"],
            "date": s["date_start"],
        }
        for s in data
    ]


@mcp.tool()
def get_driver_laps(session_key: int, driver_number: int) -> list:
    """
    Get all lap times for a specific driver in a session.
    driver_number: e.g. 1 = Verstappen, 44 = Hamilton, 16 = Leclerc, 4 = Norris, 63 = Russell.
    Returns lap number, lap duration in seconds, and sector times.
    """
    data = f1_get("laps", {"session_key": session_key, "driver_number": driver_number})
    return [
        {
            "lap_number": lap["lap_number"],
            "lap_duration": lap.get("lap_duration"),
            "sector_1": lap.get("duration_sector_1"),
            "sector_2": lap.get("duration_sector_2"),
            "sector_3": lap.get("duration_sector_3"),
            "is_pit_out_lap": lap.get("is_pit_out_lap"),
        }
        for lap in data
    ]


@mcp.tool()
def get_fastest_lap(session_key: int) -> dict:
    """
    Get the fastest lap of the entire session across all drivers.
    Returns the driver number, lap number, and lap time.
    """
    data = f1_get("laps", {"session_key": session_key})
    valid = [lap for lap in data if lap.get("lap_duration")]
    if not valid:
        return {"error": "No lap data found for this session."}
    fastest = min(valid, key=lambda x: x["lap_duration"])
    return {
        "driver_number": fastest["driver_number"],
        "lap_number": fastest["lap_number"],
        "lap_duration": fastest["lap_duration"],
    }


@mcp.tool()
def get_pit_stops(session_key: int, driver_number: int = None) -> list:
    """
    Get pit stop data for a session. Optionally filter by driver.
    Returns driver number, lap number, and pit stop duration in seconds.
    """
    params = {"session_key": session_key}
    if driver_number:
        params["driver_number"] = driver_number
    data = f1_get("pit", params)
    return [
        {
            "driver_number": p["driver_number"],
            "lap_number": p["lap_number"],
            "pit_duration": p.get("pit_duration"),
        }
        for p in data
    ]


@mcp.tool()
def get_tyre_stints(session_key: int, driver_number: int = None) -> list:
    """
    Get tyre stint strategy for a session. Shows which compound was used and for how many laps.
    Compounds: SOFT, MEDIUM, HARD, INTERMEDIATE, WET.
    Optionally filter by driver number.
    """
    params = {"session_key": session_key}
    if driver_number:
        params["driver_number"] = driver_number
    data = f1_get("stints", params)
    return [
        {
            "driver_number": s["driver_number"],
            "stint_number": s["stint_number"],
            "compound": s.get("compound"),
            "lap_start": s.get("lap_start"),
            "lap_end": s.get("lap_end"),
            "tyre_age_at_start": s.get("tyre_age_at_start"),
        }
        for s in data
    ]


@mcp.tool()
def get_race_positions(session_key: int) -> list:
    """
    Get the final race positions for all drivers in a session.
    Returns each driver's number and their finishing position.
    """
    data = f1_get("position", {"session_key": session_key})
    # Get the last recorded position per driver
    latest = {}
    for entry in data:
        dn = entry["driver_number"]
        latest[dn] = entry["position"]
    return sorted(
        [{"driver_number": k, "position": v} for k, v in latest.items()],
        key=lambda x: x["position"],
    )


@mcp.tool()
def get_weather(session_key: int) -> list:
    """
    Get weather conditions during a session.
    Returns air temp, track temp, humidity, wind speed, and rainfall.
    """
    data = f1_get("weather", {"session_key": session_key})
    if not data:
        return []
    # Return a sample every 10 entries to avoid huge responses
    sampled = data[::10]
    return [
        {
            "time": w["date"],
            "air_temp": w.get("air_temperature"),
            "track_temp": w.get("track_temperature"),
            "humidity": w.get("humidity"),
            "wind_speed": w.get("wind_speed"),
            "rainfall": w.get("rainfall"),
        }
        for w in sampled
    ]


@mcp.tool()
def get_race_control(session_key: int) -> list:
    """
    Get race control messages for a session: safety cars, flags, penalties, incidents.
    Returns time, category, flag, and message.
    """
    data = f1_get("race_control", {"session_key": session_key})
    return [
        {
            "time": r["date"],
            "category": r.get("category"),
            "flag": r.get("flag"),
            "driver_number": r.get("driver_number"),
            "message": r.get("message"),
        }
        for r in data
    ]


@mcp.tool()
def get_drivers(session_key: int) -> list:
    """
    Get all drivers participating in a session with their number, name, team, and acronym.
    Useful to look up driver numbers before querying lap or pit data.
    """
    data = f1_get("drivers", {"session_key": session_key})
    return [
        {
            "driver_number": d["driver_number"],
            "full_name": d.get("full_name"),
            "acronym": d.get("name_acronym"),
            "team": d.get("team_name"),
        }
        for d in data
    ]


if __name__ == "__main__":
    mcp.run()