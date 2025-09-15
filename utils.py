import asyncio
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo


def get_now() -> datetime:
    return datetime.now(timezone.utc)


def get_next_hour() -> datetime:
    return get_now().replace(second=0, microsecond=0, minute=0)


def get_next_n_hours(n: float) -> datetime:
    hours = int(n)
    mins = (n - hours) * 60
    return get_now() + timedelta(hours=hours, minutes=mins)


def to_number(string: str) -> int:
    try:
        return int(string)
    except ValueError:
        return 0


def str_not_empty(string: str | None) -> bool:
    return string is not None and string != ""


def get_not_empty_string(*strings: str) -> str:
    for string in strings:
        if str_not_empty(string):
            return string
    return ""

def every_minute_at_0(f):
    async def wrapper():
        while True:
            now = datetime.now()
            next_minute = (now.replace(second=0, microsecond=0) + timedelta(minutes=1))
            await asyncio.sleep((next_minute - now).total_seconds())
            await f()
    return wrapper

TZ_ABBREV_MAP = {
    "UTC": "UTC",
    "GMT": "Etc/GMT",
    "CET": "Europe/Berlin",
    "EET": "Europe/Athens",
    "EST": "America/New_York",  # Eastern Standard Time
    "EDT": "America/New_York",  # Eastern Daylight Time
    "CST": "America/Chicago",   # ⚠ could also mean China
    "CDT": "America/Chicago",
    "MST": "America/Denver",
    "MDT": "America/Denver",
    "PST": "America/Los_Angeles",
    "PDT": "America/Los_Angeles",
}

def resolve_timezone(tz_name: str) -> ZoneInfo | None:
    tz_name = tz_name.strip().upper()
    if tz_name in TZ_ABBREV_MAP:
        return ZoneInfo(TZ_ABBREV_MAP[tz_name])
    try:
        return ZoneInfo(tz_name)  # fallback to full IANA string
    except Exception:
        return None
