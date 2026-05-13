"""Map a `zone_description` (City_State, e.g. `Houston_TX`) to an IANA timezone.

The operator's BQ query for outreach must include `zone_description` so we can
enforce per-partner quiet hours. State default = each state's majority-population
timezone; CITY_OVERRIDES handles the well-known split-zone cities. Unknown values
return None — the caller treats them as `unmapped_zone` and skips the partner.
"""

from datetime import datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

QUIET_HOURS_START = 8   # 08:00 local
QUIET_HOURS_END = 21    # 21:00 local (exclusive)

STATE_TO_TZ = {
    "AL": "America/Chicago", "AK": "America/Anchorage", "AZ": "America/Phoenix",
    "AR": "America/Chicago", "CA": "America/Los_Angeles", "CO": "America/Denver",
    "CT": "America/New_York", "DE": "America/New_York", "DC": "America/New_York",
    "FL": "America/New_York",
    "GA": "America/New_York", "HI": "Pacific/Honolulu", "ID": "America/Boise",
    "IL": "America/Chicago", "IN": "America/Indiana/Indianapolis",
    "IA": "America/Chicago", "KS": "America/Chicago",
    "KY": "America/New_York",
    "LA": "America/Chicago", "ME": "America/New_York", "MD": "America/New_York",
    "MA": "America/New_York", "MI": "America/Detroit",
    "MN": "America/Chicago", "MS": "America/Chicago", "MO": "America/Chicago",
    "MT": "America/Denver", "NE": "America/Chicago",
    "NV": "America/Los_Angeles",
    "NH": "America/New_York", "NJ": "America/New_York", "NM": "America/Denver",
    "NY": "America/New_York", "NC": "America/New_York",
    "ND": "America/Chicago",
    "OH": "America/New_York", "OK": "America/Chicago",
    "OR": "America/Los_Angeles",
    "PA": "America/New_York", "RI": "America/New_York", "SC": "America/New_York",
    "SD": "America/Chicago",
    "TN": "America/Chicago",
    "TX": "America/Chicago",
    "UT": "America/Denver", "VT": "America/New_York", "VA": "America/New_York",
    "WA": "America/Los_Angeles", "WV": "America/New_York",
    "WI": "America/Chicago", "WY": "America/Denver",
}

CITY_OVERRIDES = {
    "El Paso_TX": "America/Denver",

    "Pensacola_FL": "America/Chicago",
    "Panama City_FL": "America/Chicago",
    "Fort Walton Beach_FL": "America/Chicago",
    "Destin_FL": "America/Chicago",
    "Crestview_FL": "America/Chicago",
    "Niceville_FL": "America/Chicago",
    "Marianna_FL": "America/Chicago",
    "DeFuniak Springs_FL": "America/Chicago",

    "Knoxville_TN": "America/New_York",
    "Chattanooga_TN": "America/New_York",
    "Johnson City_TN": "America/New_York",
    "Kingsport_TN": "America/New_York",
    "Bristol_TN": "America/New_York",
    "Oak Ridge_TN": "America/New_York",

    "Paducah_KY": "America/Chicago",
    "Bowling Green_KY": "America/Chicago",
    "Owensboro_KY": "America/Chicago",
    "Hopkinsville_KY": "America/Chicago",
    "Henderson_KY": "America/Chicago",

    "Gary_IN": "America/Chicago",
    "Hammond_IN": "America/Chicago",
    "Evansville_IN": "America/Chicago",
    "Merrillville_IN": "America/Chicago",
    "Michigan City_IN": "America/Chicago",
    "Valparaiso_IN": "America/Chicago",

    "Rapid City_SD": "America/Denver",
    "Sturgis_SD": "America/Denver",

    "Scottsbluff_NE": "America/Denver",
    "Alliance_NE": "America/Denver",
    "Chadron_NE": "America/Denver",

    "Goodland_KS": "America/Denver",
}


def zone_to_timezone(zone_description: Optional[str]) -> Optional[str]:
    if not zone_description or "_" not in zone_description:
        return None
    if zone_description in CITY_OVERRIDES:
        return CITY_OVERRIDES[zone_description]
    return STATE_TO_TZ.get(zone_description.rsplit("_", 1)[-1].upper())


def evaluate_window(zone_description: Optional[str], now_utc: Optional[datetime] = None) -> dict:
    """Decide whether a partner is currently inside the 8AM-9PM local window.

    Returns a dict with: status (`ok` / `outside_quiet_hours` / `unmapped_zone`),
    timezone (IANA, or None), local_time (ISO, or None), opens_at (ISO of next
    8AM in their local time, or None).
    """
    tz_name = zone_to_timezone(zone_description)
    if not tz_name:
        return {"status": "unmapped_zone", "timezone": None, "local_time": None, "opens_at": None}

    if now_utc is None:
        now_utc = datetime.now(ZoneInfo("UTC"))
    elif now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=ZoneInfo("UTC"))

    local = now_utc.astimezone(ZoneInfo(tz_name))
    in_window = QUIET_HOURS_START <= local.hour < QUIET_HOURS_END

    if in_window:
        return {"status": "ok", "timezone": tz_name,
                "local_time": local.isoformat(), "opens_at": None}

    next_open_date = local.date() if local.hour < QUIET_HOURS_START else local.date() + timedelta(days=1)
    opens_at = datetime.combine(next_open_date, time(QUIET_HOURS_START, 0), tzinfo=ZoneInfo(tz_name))
    return {"status": "outside_quiet_hours", "timezone": tz_name,
            "local_time": local.isoformat(), "opens_at": opens_at.isoformat()}
