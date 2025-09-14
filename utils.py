import asyncio
from datetime import datetime, timezone, timedelta


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