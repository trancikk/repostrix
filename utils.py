from datetime import datetime, timezone, timedelta


def get_now() -> datetime:
    return datetime.now(timezone.utc)


def get_now_hour() -> datetime:
    return get_now().replace(second=0, microsecond=0, minute=0)


def get_next_n_hours(n: int) -> datetime:
    return get_now_hour() + timedelta(hours=n)


def to_number(string: str) -> int:
    try:
        return int(string)
    except ValueError:
        return 0
