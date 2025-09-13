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
