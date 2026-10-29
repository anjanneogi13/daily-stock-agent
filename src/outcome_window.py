"""Canonical "what closed in this window" selector for every learning report.

Why this exists (audit 2026-10-29 — "why did the weekly/monthly agent never
learn anything?"):

1. Every reflection (weekly_review, weekend_reflection, monthly_xray,
   local_analyst) selected picks by ``pick_date`` inside the last 7/30 days.
   A swing pick holds up to 10 sessions, so a 7-day pick window contains at
   most 1-2 closed trades -> the weekly review said "Need more data" every
   single week while 100+ closed trades sat in picks_log.csv.
2. Each report used a different definition of "closed" ({tp_hit, sl_hit,
   expired} vs {tp_hit, sl_hit, day_close} vs {tp_hit, sl_hit, "closed"}),
   so the same week produced different win rates in different files.

Rules (single source of truth):
- A pick is CLOSED+VERIFIED when evaluation_status is in CLOSED_STATUSES
  **and** it carries a numeric r_multiple. ``expired`` rows without an
  exit_price (settled unverified by the 30-day cutoff) are NOT outcomes.
- Learning reports window closed picks by ``evaluated_on`` (when the result
  became known), never by pick_date.
- Watch-only rows are not official picks and are excluded from learning.
"""
from __future__ import annotations

import csv
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Iterable, List, Optional

PICKS_LOG = Path("data/picks_log.csv")

CLOSED_STATUSES = frozenset({"tp_hit", "sl_hit", "expired", "day_close"})
WIN_STATUSES = frozenset({"tp_hit"})


def _to_float(v) -> Optional[float]:
    if v is None or v == "" or v == "None":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_date(v) -> Optional[date]:
    if not v:
        return None
    try:
        return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def is_official(row: Dict) -> bool:
    return str(row.get("watch_only", "")).strip().lower() not in ("true", "1", "yes")


def is_closed_verified(row: Dict) -> bool:
    """Closed with a real, priced outcome (r_multiple present)."""
    return (row.get("evaluation_status") in CLOSED_STATUSES
            and _to_float(row.get("r_multiple")) is not None)


def is_unverified_expired(row: Dict) -> bool:
    """Settled 'expired' with no exit data — a lost outcome, not a result."""
    return (row.get("evaluation_status") == "expired"
            and _to_float(row.get("r_multiple")) is None)


def outcome_label(row: Dict) -> str:
    """win / loss / flat for a closed+verified row (R-based, flat = 0R)."""
    r = _to_float(row.get("r_multiple"))
    if r is None:
        return "unknown"
    if r > 0:
        return "win"
    if r < 0:
        return "loss"
    return "flat"


def load_rows(path: Optional[Path] = None) -> List[Dict]:
    path = PICKS_LOG if path is None else path
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def picks_in_window(start: date, end: date, rows: Optional[Iterable[Dict]] = None,
                    official_only: bool = True) -> List[Dict]:
    """Official picks whose pick_date falls in [start, end]."""
    rows = load_rows() if rows is None else rows
    out = []
    for r in rows:
        if official_only and not is_official(r):
            continue
        d = _to_date(r.get("pick_date"))
        if d is not None and start <= d <= end:
            out.append(r)
    return out


def outcomes_in_window(start: date, end: date, rows: Optional[Iterable[Dict]] = None,
                       official_only: bool = True) -> List[Dict]:
    """Closed+verified official picks whose evaluated_on falls in [start, end].

    Falls back to pick_date for legacy rows missing evaluated_on.
    """
    rows = load_rows() if rows is None else rows
    out = []
    for r in rows:
        if official_only and not is_official(r):
            continue
        if not is_closed_verified(r):
            continue
        d = _to_date(r.get("evaluated_on")) or _to_date(r.get("pick_date"))
        if d is not None and start <= d <= end:
            out.append(r)
    return out


def summarize(closed: List[Dict]) -> Dict:
    """Headline stats for a list of closed+verified rows."""
    rs = [_to_float(r.get("r_multiple")) for r in closed]
    rs = [x for x in rs if x is not None]
    rets = [_to_float(r.get("actual_return_pct")) for r in closed]
    rets = [x for x in rets if x is not None]
    labels = [outcome_label(r) for r in closed]
    n = len(closed)
    wins = labels.count("win")
    losses = labels.count("loss")
    by_status: Dict[str, int] = {}
    for r in closed:
        s = r.get("evaluation_status") or "unknown"
        by_status[s] = by_status.get(s, 0) + 1
    return {
        "n": n,
        "wins": wins,
        "losses": losses,
        "flats": labels.count("flat"),
        "win_rate": round(wins / n, 3) if n else None,
        "total_r": round(sum(rs), 2) if rs else None,
        "avg_r": round(sum(rs) / len(rs), 3) if rs else None,
        "avg_return_pct": round(sum(rets) / len(rets), 2) if rets else None,
        "by_status": by_status,
    }


def window_report(start: date, end: date, rows: Optional[Iterable[Dict]] = None) -> Dict:
    """Everything a reflection needs: picked, closed (by evaluated_on), pending."""
    rows = load_rows() if rows is None else list(rows)
    picked = picks_in_window(start, end, rows)
    closed = outcomes_in_window(start, end, rows)
    pending = [r for r in rows if is_official(r)
               and r.get("evaluation_status") == "pending"]
    unverified = [r for r in rows if is_official(r) and is_unverified_expired(r)]
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "picked": picked,
        "closed": closed,
        "pending_total": len(pending),
        "unverified_expired_total": len(unverified),
        "summary": summarize(closed),
    }
