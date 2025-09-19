import asyncio
from datetime import time
from datetime import datetime, timezone, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

UTC = ZoneInfo("UTC")


def get_now() -> datetime:
    return datetime.now(timezone.utc)


def get_next_hour() -> datetime:
    return get_now().replace(second=0, microsecond=0, minute=0)


def get_next_n_hours(n: float, start_time: Optional[datetime] = None, floored: bool = False) -> datetime:
    hours = int(n)
    mins = (n - hours) * 60
    result = nvl(get_now(), start_time) + timedelta(hours=hours, minutes=mins)
    if floored:
        result = result.replace(second=0, microsecond=0, minute=0)
    return result


def get_nearest_time(times: list[time], tz: ZoneInfo) -> datetime:
    cur_time = get_now().astimezone(tz)
    tz_aware_times = sorted([t.replace(tzinfo=tz) for t in times])
    past = []
    future = []
    for t in tz_aware_times:
        tz_aware = t.replace(tzinfo=tz)
        if tz_aware >= cur_time.time():
            future.append(t)
        else:
            past.append(t)
    nearest_time = past[0] if len(future) == 0 else future[0]
    return nearest_time.astimezone('UTC')


# ChatGPT
def next_fire_time(times: list[time], tz: ZoneInfo, now: datetime | None = None) -> datetime:
    """
    Compute the nearest future fire time based on a list of times and a timezone.

    :param times: list of datetime.time objects (naive, assumed to be in tz)
    :param tz: target timezone as zoneinfo.ZoneInfo
    :param now: optional current datetime, defaults to datetime.now(tz)
    :return: datetime of next fire in tz-aware datetime
    """
    now = now or datetime.now(tz)

    # Generate tz-aware datetime for each time today
    today = now.date()
    candidates = []
    for t in times:
        dt = datetime.combine(today, t, tzinfo=tz)
        if dt > now:
            candidates.append(dt)

    # If no candidates today, take the earliest time tomorrow
    if not candidates:
        tomorrow = today + timedelta(days=1)
        candidates = [datetime.combine(tomorrow, t, tzinfo=tz) for t in times]

    # Return the earliest
    candidate = min(candidates)
    return candidate.astimezone(UTC)


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


def nvl(default, *args):
    for arg in args:
        if arg is not None:
            return arg
    return default


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
    "CST": "America/Chicago",  # ⚠ could also mean China
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
