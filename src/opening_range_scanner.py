"""Opening-range intraday scanner.

Monitoring-only feature: detects early intraday breakout candidates without
creating trades, orders, or paper-trade artifacts.

The module is intentionally pure/testable. Data fetch/integration happens in
later layers; this file only evaluates already-fetched intraday bars.

Expected bar shape:
    {
        "ts": "2026-05-06T09:35:00-04:00",  # or datetime
        "open": 100.0,
        "high": 101.0,
        "low": 99.5,
        "close": 100.8,
        "volume": 123456,
    }
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Iterable, Optional, Sequence
from zoneinfo import ZoneInfo


ET = ZoneInfo("America/New_York")
MARKET_OPEN_ET = time(9, 30)
DEFAULT_RANGE_MINUTES = 15


def _as_dt(value) -> datetime:
    """Normalize timestamp-like values to datetime.

    Naive datetimes are interpreted as America/New_York because intraday bar
    timestamps in tests and CSV-like adapters are usually local market time.
    """
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise TypeError(f"unsupported timestamp type: {type(value)}")

    if dt.tzinfo is None:
        return dt.replace(tzinfo=ET)
    return dt.astimezone(ET)


def _num(bar: dict, key: str, default: float = 0.0) -> float:
    try:
        value = bar.get(key)
        if value in (None, "", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _vol(bar: dict) -> float:
    return _num(bar, "volume", 0.0)


def _session_date(bars: Sequence[dict], session_date: Optional[str | date] = None) -> date:
    if session_date is not None:
        if isinstance(session_date, date):
            return session_date
        return datetime.fromisoformat(str(session_date)).date()

    if not bars:
        raise ValueError("cannot infer session_date from empty bars")

    return _as_dt(bars[0]["ts"]).date()


def opening_range_bounds(
    session_date: str | date,
    range_minutes: int = DEFAULT_RANGE_MINUTES,
) -> tuple[datetime, datetime]:
    """Return [start, end) ET bounds for the opening range."""
    if isinstance(session_date, str):
        d = datetime.fromisoformat(session_date).date()
    else:
        d = session_date

    start = datetime.combine(d, MARKET_OPEN_ET, tzinfo=ET)
    end = start + timedelta(minutes=range_minutes)
    return start, end


def calculate_opening_range(
    bars: Iterable[dict],
    session_date: Optional[str | date] = None,
    range_minutes: int = DEFAULT_RANGE_MINUTES,
    min_bars: int = 3,
) -> dict:
    """Calculate the opening range from intraday bars.

    Returns a dict with ``ready=False`` and blockers when there is not enough
    data. Uses [09:30, 09:30 + range_minutes) ET as the opening window.
    """
    rows = sorted(list(bars), key=lambda b: _as_dt(b["ts"]))
    if not rows:
        return {
            "ready": False,
            "blockers": ["no_intraday_bars"],
            "range_minutes": range_minutes,
            "bar_count": 0,
        }

    d = _session_date(rows, session_date)
    start, end = opening_range_bounds(d, range_minutes=range_minutes)

    range_bars = [
        b for b in rows
        if start <= _as_dt(b["ts"]) < end
    ]

    blockers = []
    if len(range_bars) < min_bars:
        blockers.append(f"opening_range_incomplete: bars={len(range_bars)} < {min_bars}")

    highs = [_num(b, "high") for b in range_bars if _num(b, "high") > 0]
    lows = [_num(b, "low") for b in range_bars if _num(b, "low") > 0]
    closes = [_num(b, "close") for b in range_bars if _num(b, "close") > 0]

    if not highs or not lows or not closes:
        blockers.append("opening_range_missing_prices")

    if blockers:
        return {
            "ready": False,
            "blockers": blockers,
            "range_minutes": range_minutes,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "bar_count": len(range_bars),
        }

    high = max(highs)
    low = min(lows)
    width_pct = ((high - low) / low * 100) if low > 0 else 0.0

    return {
        "ready": True,
        "blockers": [],
        "range_minutes": range_minutes,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "bar_count": len(range_bars),
        "high": round(high, 4),
        "low": round(low, 4),
        "width_pct": round(width_pct, 4),
        "volume": int(sum(_vol(b) for b in range_bars)),
    }


def latest_post_range_bar(
    bars: Iterable[dict],
    session_date: Optional[str | date] = None,
    range_minutes: int = DEFAULT_RANGE_MINUTES,
) -> Optional[dict]:
    """Return the latest bar at/after opening-range end."""
    rows = sorted(list(bars), key=lambda b: _as_dt(b["ts"]))
    if not rows:
        return None

    d = _session_date(rows, session_date)
    _, end = opening_range_bounds(d, range_minutes=range_minutes)
    post = [b for b in rows if _as_dt(b["ts"]) >= end]
    return post[-1] if post else None


def detect_opening_range_breakout(
    ticker: str,
    bars: Iterable[dict],
    *,
    prev_close: Optional[float] = None,
    session_date: Optional[str | date] = None,
    range_minutes: int = DEFAULT_RANGE_MINUTES,
    min_range_bars: int = 3,
    min_volume_ratio: float = 1.5,
    max_extension_pct: float = 3.0,
    max_gap_pct: float = 8.0,
    min_breakout_pct: float = 0.10,
) -> dict:
    """Detect a watch-only opening-range breakout candidate.

    The result always includes ``watch_only=True`` for accepted candidates.
    This feature is monitoring-only until there is enough evidence to promote
    it into actionable planning.
    """
    rows = sorted(list(bars), key=lambda b: _as_dt(b["ts"]))
    orng = calculate_opening_range(
        rows,
        session_date=session_date,
        range_minutes=range_minutes,
        min_bars=min_range_bars,
    )

    if not orng.get("ready"):
        return {
            "ticker": ticker.upper(),
            "candidate": False,
            "watch_only": True,
            "reason": "opening range not ready",
            "opening_range": orng,
            "blockers": list(orng.get("blockers", [])),
        }

    latest = latest_post_range_bar(rows, session_date=session_date, range_minutes=range_minutes)
    if not latest:
        return {
            "ticker": ticker.upper(),
            "candidate": False,
            "watch_only": True,
            "reason": "no post-range bar",
            "opening_range": orng,
            "blockers": ["no_post_range_bar"],
        }

    price = _num(latest, "close")
    high = float(orng["high"])
    low = float(orng["low"])
    breakout_pct = ((price - high) / high * 100) if high > 0 else 0.0
    extension_pct = breakout_pct

    avg_range_bar_volume = (float(orng["volume"]) / max(1, int(orng["bar_count"])))
    volume_ratio = (_vol(latest) / avg_range_bar_volume) if avg_range_bar_volume > 0 else 0.0

    gap_pct = None
    if prev_close and prev_close > 0:
        gap_pct = ((price - prev_close) / prev_close * 100)

    blockers = []
    if price <= high:
        blockers.append("price_not_above_opening_range_high")
    elif breakout_pct < min_breakout_pct:
        blockers.append(f"breakout_pct={breakout_pct:.2f} < {min_breakout_pct:.2f}")

    if volume_ratio < min_volume_ratio:
        blockers.append(f"volume_ratio={volume_ratio:.2f} < {min_volume_ratio:.2f}")

    if extension_pct > max_extension_pct:
        blockers.append(f"anti_chase_extension={extension_pct:.2f}% > {max_extension_pct:.2f}%")

    if gap_pct is not None and abs(gap_pct) > max_gap_pct:
        blockers.append(f"gap_pct={gap_pct:+.2f}% exceeds {max_gap_pct:.2f}%")

    accepted = not blockers
    entry = price
    stop = low
    risk = entry - stop
    take_profit = entry + (1.5 * risk) if risk > 0 else None

    return {
        "ticker": ticker.upper(),
        "candidate": accepted,
        "watch_only": True,
        "mode": "monitoring_only",
        "reason": (
            f"opening-range breakout: +{breakout_pct:.2f}% above OR high, "
            f"{volume_ratio:.1f}x OR bar volume"
            if accepted else
            "blocked by opening-range guardrails"
        ),
        "price": round(price, 4),
        "opening_range": orng,
        "breakout_pct": round(breakout_pct, 4),
        "volume_ratio": round(volume_ratio, 4),
        "gap_pct": round(gap_pct, 4) if gap_pct is not None else None,
        "entry": round(entry, 4) if accepted else None,
        "stop_loss": round(stop, 4) if accepted else None,
        "take_profit": round(take_profit, 4) if accepted and take_profit is not None else None,
        "risk_reward": 1.5 if accepted and risk > 0 else None,
        "blockers": blockers,
    }
