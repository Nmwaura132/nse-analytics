"""
NSE market hours utility.
NSE trades Monday–Friday, 09:00–15:00 East Africa Time (UTC+3).
Import this module everywhere market-hours awareness is needed.
"""
from datetime import datetime, time
from zoneinfo import ZoneInfo

NAIROBI_TZ = ZoneInfo("Africa/Nairobi")

_OPEN  = time(9,  0)
_CLOSE = time(15, 0)


def now_eat() -> datetime:
    return datetime.now(tz=NAIROBI_TZ)


def is_market_open() -> bool:
    """True if NSE is currently in session (Mon-Fri 09:00-15:00 EAT)."""
    now = now_eat()
    if now.weekday() >= 5:          # Sat=5, Sun=6
        return False
    return _OPEN <= now.time() <= _CLOSE


def get_market_status() -> str:
    return "OPEN" if is_market_open() else "CLOSED"


def minutes_to_open() -> int | None:
    """Minutes until market opens. None if already open or weekend."""
    now = now_eat()
    if now.weekday() >= 5 or is_market_open():
        return None
    if now.time() < _OPEN:
        delta = datetime.combine(now.date(), _OPEN) - now.replace(tzinfo=None)
        return int(delta.total_seconds() // 60)
    return None
