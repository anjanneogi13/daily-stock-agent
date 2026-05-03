"""T51 — US Market Calendar Awareness.

Hardcoded NYSE/NASDAQ holidays for 2026, 2027, 2028 (3 years ahead).
No internet dependency, no surprise breakage when SEC website changes.

ANNUAL RENEWAL: Each January, the Sunday Self-Improvement Report
flags when the calendar needs +1 more year of holidays added.

API:
  is_weekend(date)         → True/False
  is_holiday(date)         → True/False
  is_trading_day(date)     → True if not weekend AND not holiday
  is_early_close(date)     → True for 1 PM ET half-days
  next_trading_day(date)   → next valid trading date
  days_until_renewal()     → N years of holidays still cached
  needs_renewal(threshold) → True if cache < threshold years
"""
from __future__ import annotations
from datetime import date, datetime, timedelta
from typing import Optional, Set


# ═══════════════════════════════════════════════════════════════
# NYSE Holidays — exact closure dates (full-day closures)
# Source: https://www.nyse.com/markets/hours-calendars
# ═══════════════════════════════════════════════════════════════
US_MARKET_HOLIDAYS: Set[str] = {
    # ─────── 2026 ───────
    "2026-01-01",  # New Year's Day
    "2026-01-19",  # MLK Jr Day (3rd Mon Jan)
    "2026-02-16",  # Presidents Day (3rd Mon Feb)
    "2026-04-03",  # Good Friday
    "2026-05-25",  # Memorial Day (last Mon May)
    "2026-06-19",  # Juneteenth
    "2026-07-03",  # Independence Day observed (Jul 4 = Sat)
    "2026-09-07",  # Labor Day (1st Mon Sep)
    "2026-11-26",  # Thanksgiving
    "2026-12-25",  # Christmas

    # ─────── 2027 ───────
    "2027-01-01",  # New Year's Day
    "2027-01-18",  # MLK Jr Day
    "2027-02-15",  # Presidents Day
    "2027-03-26",  # Good Friday
    "2027-05-31",  # Memorial Day
    "2027-06-18",  # Juneteenth observed (Jun 19 = Sat)
    "2027-07-05",  # Independence Day observed (Jul 4 = Sun)
    "2027-09-06",  # Labor Day
    "2027-11-25",  # Thanksgiving
    "2027-12-24",  # Christmas observed (Dec 25 = Sat)

    # ─────── 2028 ───────
    "2028-01-17",  # MLK Jr Day (Jan 1 = Sat, no observance NYE 2028)
    "2028-02-21",  # Presidents Day
    "2028-04-14",  # Good Friday
    "2028-05-29",  # Memorial Day
    "2028-06-19",  # Juneteenth (Mon)
    "2028-07-04",  # Independence Day (Tue)
    "2028-09-04",  # Labor Day
    "2028-11-23",  # Thanksgiving
    "2028-12-25",  # Christmas (Mon)
}

# Half-day closures (1:00 PM ET) — typically before/after major holidays
US_MARKET_EARLY_CLOSE: Set[str] = {
    # ─────── 2026 ───────
    "2026-07-02",  # Day before Jul 4 (Jul 4 = Sat → observed Fri Jul 3 closed,
                   # so Jul 2 = early close per recent NYSE pattern)
    "2026-11-27",  # Black Friday
    "2026-12-24",  # Christmas Eve

    # ─────── 2027 ───────
    "2027-07-02",  # Day before Independence Day (Jul 4 = Sun)
    "2027-11-26",  # Black Friday
    "2027-12-23",  # Day before Christmas observed

    # ─────── 2028 ───────
    "2028-07-03",  # Day before Jul 4
    "2028-11-24",  # Black Friday
}


# ═══════════════════════════════════════════════════════════════
# Core API
# ═══════════════════════════════════════════════════════════════
def _to_date(d) -> date:
    """Normalize input to date object."""
    if d is None:
        return date.today()
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        return datetime.fromisoformat(d.split("T")[0]).date()
    raise TypeError(f"unsupported date type: {type(d)}")


def is_weekend(d=None) -> bool:
    """Saturday (5) or Sunday (6)."""
    return _to_date(d).weekday() >= 5


def is_holiday(d=None) -> bool:
    """Full-day market closure (NYSE-observed holiday)."""
    return _to_date(d).isoformat() in US_MARKET_HOLIDAYS


def is_early_close(d=None) -> bool:
    """1:00 PM ET early close day."""
    return _to_date(d).isoformat() in US_MARKET_EARLY_CLOSE


def is_trading_day(d=None) -> bool:
    """True iff the US market is OPEN that day (full or half session)."""
    dd = _to_date(d)
    return not is_weekend(dd) and not is_holiday(dd)


def reason_market_closed(d=None) -> Optional[str]:
    """Returns 'weekend' / 'holiday' / None if open."""
    dd = _to_date(d)
    if is_weekend(dd):
        return "weekend"
    if is_holiday(dd):
        return "holiday"
    return None


def next_trading_day(d=None, max_lookahead: int = 14) -> date:
    """Find next valid trading day (skip weekends + holidays)."""
    dd = _to_date(d)
    for i in range(1, max_lookahead + 1):
        candidate = dd + timedelta(days=i)
        if is_trading_day(candidate):
            return candidate
    raise RuntimeError(f"No trading day found within {max_lookahead} days of {dd}")


def previous_trading_day(d=None, max_lookback: int = 14) -> date:
    """Find previous valid trading day (skip weekends + holidays)."""
    dd = _to_date(d)
    for i in range(1, max_lookback + 1):
        candidate = dd - timedelta(days=i)
        if is_trading_day(candidate):
            return candidate
    raise RuntimeError(f"No trading day found within {max_lookback} days before {dd}")


# ═══════════════════════════════════════════════════════════════
# Annual renewal awareness
# ═══════════════════════════════════════════════════════════════
def cached_years() -> Set[int]:
    """Distinct years currently in the holiday cache."""
    return {int(d.split("-")[0]) for d in US_MARKET_HOLIDAYS}


def years_remaining(today=None) -> int:
    """How many full years from today are still in the cache."""
    today = _to_date(today)
    max_year = max(cached_years())
    return max_year - today.year


def needs_renewal(threshold_years: int = 2, today=None) -> bool:
    """True if cache has < threshold_years remaining."""
    return years_remaining(today) < threshold_years


def renewal_urgency(today=None) -> str:
    """Returns 'none', 'soft' (~18mo lead), 'urgent' (<6mo), 'critical' (<2mo)."""
    today = _to_date(today)
    max_year = max(cached_years())
    months_left = (max_year - today.year) * 12 + (12 - today.month)
    if months_left > 18:  return "none"
    if months_left > 6:   return "soft"
    if months_left > 2:   return "urgent"
    return "critical"


def renewal_message(today=None) -> Optional[str]:
    """Plain-English heads-up. Escalates as deadline approaches."""
    urgency = renewal_urgency(today)
    if urgency == "none":
        return None
    today = _to_date(today)
    max_year = max(cached_years())
    next_year_needed = max_year + 1
    icon = {"soft": "📅", "urgent": "⚠️", "critical": "🚨"}[urgency]
    suffix = {
        "soft":     "soon (no rush — plenty of lead time).",
        "urgent":   "in the next month or two.",
        "critical": "THIS WEEK — agent will silently break on next holiday otherwise.",
    }[urgency]
    return (f"{icon} Holiday calendar runs out after {max_year}. "
            f"Add {next_year_needed} holidays to src/market_calendar.py {suffix}")


# ═══════════════════════════════════════════════════════════════
# Plain-English helpers (for Telegram / logs)
# ═══════════════════════════════════════════════════════════════
def market_status_today(today=None) -> dict:
    """Comprehensive snapshot for today (used by main.py + intraday)."""
    dd = _to_date(today)
    closed = reason_market_closed(dd)
    return {
        "date":          dd.isoformat(),
        "is_trading_day":closed is None,
        "is_weekend":    is_weekend(dd),
        "is_holiday":    is_holiday(dd),
        "is_early_close":is_early_close(dd),
        "closed_reason": closed,
        "next_open":     next_trading_day(dd).isoformat() if closed else dd.isoformat(),
    }
