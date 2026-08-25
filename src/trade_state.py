"""Single source of truth for trade/position state (§7 of the reliability overhaul).

Every report (intraday monitor, execution report, position monitor, today's /
weekly performance, hypothesis review) must be a *pure projection* of the
reconciled ledger ``data/picks_log.csv`` through the helpers in this module.
No report may recompute or force outcomes itself.

Canonical position lifecycle::

    PENDING_FILL/OPEN → {CLOSED_TP_WIN | CLOSED_SL_LOSS | CLOSED_TIME_EXIT
                         | EXPIRED_OVERDUE} , plus NO_TRADE (entry never filled)

Legacy ``evaluation_status`` values map onto the canonical states so existing
rows stay backward compatible (no CSV migration required):

    pending/""/open    → OPEN
    tp_hit             → CLOSED_TP_WIN
    sl_hit             → CLOSED_SL_LOSS
    day_close          → CLOSED_TIME_EXIT   (day trade closed at the bell)
    expired            → EXPIRED_OVERDUE    (hold horizon exceeded)
    unreachable_entry  → NO_TRADE           (limit never hit; no position)

Terminal outcomes are written once and are immutable (enforced by
``src.picks_csv.update_pick_row``).  Ages and derived fields are recomputed
deterministically from timestamps — never incremented in place.

Outcome taxonomy (realized results):
    WIN        return >  +FLAT_EPSILON_PCT
    LOSS       return <  -FLAT_EPSILON_PCT
    FLAT       |return| <= FLAT_EPSILON_PCT  (a ≈$0 time-exit is NOT a loss)
    NO_TRADE   unreachable_entry (no money in, no money out)
    UNVERIFIED terminal but no exit data recorded (settled without a price)
"""
from __future__ import annotations

import csv
from datetime import date, datetime, timedelta
from pathlib import Path

LOG_PATH = Path("data/picks_log.csv")

# ─── Canonical states ───────────────────────────────────────────
STATE_OPEN = "OPEN"
STATE_CLOSED_TP_WIN = "CLOSED_TP_WIN"
STATE_CLOSED_SL_LOSS = "CLOSED_SL_LOSS"
STATE_CLOSED_TIME_EXIT = "CLOSED_TIME_EXIT"
STATE_EXPIRED_OVERDUE = "EXPIRED_OVERDUE"
STATE_NO_TRADE = "NO_TRADE"

LEGACY_TO_STATE = {
    "": STATE_OPEN,
    "pending": STATE_OPEN,
    "open": STATE_OPEN,
    "tp_hit": STATE_CLOSED_TP_WIN,
    "sl_hit": STATE_CLOSED_SL_LOSS,
    "day_close": STATE_CLOSED_TIME_EXIT,
    "expired": STATE_EXPIRED_OVERDUE,
    "unreachable_entry": STATE_NO_TRADE,
}

#: legacy evaluation_status values that mean "this position reached its one
#: and only terminal transition" — such rows are immutable.
TERMINAL_STATUSES = frozenset(
    {"tp_hit", "sl_hit", "day_close", "expired", "unreachable_entry"}
)

#: terminal statuses that represent a real position outcome (money at risk).
REALIZED_STATUSES = frozenset({"tp_hit", "sl_hit", "day_close", "expired"})

# ─── Outcome taxonomy ───────────────────────────────────────────
OUTCOME_WIN = "WIN"
OUTCOME_LOSS = "LOSS"
OUTCOME_FLAT = "FLAT"
OUTCOME_NO_TRADE = "NO_TRADE"
OUTCOME_UNVERIFIED = "UNVERIFIED"

#: returns within ±this % are FLAT/BREAKEVEN, not losses.
FLAT_EPSILON_PCT = 0.05

# ─── Shared max-hold policy (calendar days) ─────────────────────
# Single home for the horizon policy; position_monitor and pick_evaluator
# both consume these values so "overdue" means the same thing everywhere.
MAX_HOLD_DAYS = {
    "day": 1,
    "swing": 10,
    "multi": 30,
}
DEFAULT_MAX_HOLD = 14


def max_hold_days(trade_type: str) -> int:
    """Max calendar days a position of this type may stay open."""
    return MAX_HOLD_DAYS.get((trade_type or "").strip().lower(), DEFAULT_MAX_HOLD)


def _parse_date(s: str) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def expected_close_date(row: dict) -> date | None:
    """Deterministic horizon-crossing date: pick_date + max_hold.

    Used when force-closing overdue positions so a re-run always produces the
    same ``evaluated_on`` (idempotent replay — never "today").
    """
    pick_d = _parse_date(row.get("pick_date", ""))
    if pick_d is None:
        return None
    return pick_d + timedelta(days=max_hold_days(row.get("trade_type", "")))


# ─── Position identity & provenance ─────────────────────────────
def position_source(row: dict) -> str:
    """Source tag for provenance labeling: 'official' or 'watch_only'."""
    wo = str(row.get("watch_only") or "").strip().lower()
    if wo in ("1", "true", "yes", "y", "watch", "watch_only"):
        return "watch_only"
    return "official"


def position_id(row: dict) -> str:
    """Stable position identity = ticker + open_date + source.

    Prevents e.g. FTH held from Aug 17 being merged/double-counted with an
    FTH late idea emitted Aug 18.
    """
    return "|".join(
        [
            (row.get("ticker") or "").strip().upper(),
            (row.get("pick_date") or "").strip(),
            position_source(row),
        ]
    )


def provenance_label(row: dict, today: str | None = None) -> str:
    """Human label for monitor lines: open date + source + carryover flag."""
    src = "watch-only reference" if position_source(row) == "watch_only" else "official pick"
    pick_date = (row.get("pick_date") or "").strip()
    label = f"{src} {pick_date}" if pick_date else src
    if today and pick_date and pick_date < today:
        label += " · carryover"
    return label


# ─── State & outcome projections ────────────────────────────────
def state_of(row: dict) -> str:
    """Canonical state for a ledger row."""
    legacy = (row.get("evaluation_status") or "").strip().lower()
    return LEGACY_TO_STATE.get(legacy, STATE_OPEN)


def is_terminal(row: dict) -> bool:
    return (row.get("evaluation_status") or "").strip().lower() in TERMINAL_STATUSES


def is_open(row: dict) -> bool:
    return not is_terminal(row)


def return_pct(row: dict) -> float | None:
    try:
        v = row.get("actual_return_pct")
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def pnl_dollar(row: dict) -> float:
    """Realized dollar P&L (0.0 when qty/entry/return unknown)."""
    try:
        explicit = row.get("pnl_dollar")
        if explicit not in (None, ""):
            return float(explicit)
    except (TypeError, ValueError):
        pass
    ret = return_pct(row)
    try:
        entry = float(row.get("entry") or 0)
        qty = float(row.get("qty") or row.get("position_size") or 0)
    except (TypeError, ValueError):
        return 0.0
    if ret is None:
        return 0.0
    return entry * qty * ret / 100.0


def classify_outcome(row: dict) -> str:
    """Bucket a terminal row: WIN / LOSS / FLAT / NO_TRADE / UNVERIFIED.

    Uses realized return %, not exit label, so a profitable day_close counts
    as a WIN and a ≈0% expired time-exit counts as FLAT — never a loss.
    """
    legacy = (row.get("evaluation_status") or "").strip().lower()
    if legacy == "unreachable_entry":
        return OUTCOME_NO_TRADE
    ret = return_pct(row)
    if ret is None:
        # terminal but no exit data — settled without a verifiable price.
        return OUTCOME_UNVERIFIED
    if ret > FLAT_EPSILON_PCT:
        return OUTCOME_WIN
    if ret < -FLAT_EPSILON_PCT:
        return OUTCOME_LOSS
    return OUTCOME_FLAT


# ─── Ledger loading ─────────────────────────────────────────────
def load_ledger(path: Path | str | None = None) -> list[dict]:
    p = Path(path) if path else LOG_PATH
    if not p.exists():
        return []
    with p.open() as f:
        return list(csv.DictReader(f))


def closed_rows(rows: list[dict]) -> list[dict]:
    return [r for r in rows if is_terminal(r)]


def closed_on(rows: list[dict], day: str) -> list[dict]:
    """Rows whose terminal transition happened exactly on `day` (strict daily
    scoping — the fix for the ever-growing 'today' dump)."""
    return [r for r in rows if is_terminal(r) and (r.get("evaluated_on") or "")[:10] == day]


def closed_between(rows: list[dict], start: str, end: str) -> list[dict]:
    """Rows closed in the inclusive [start, end] window (by close date)."""
    out = []
    for r in rows:
        if not is_terminal(r):
            continue
        d = (r.get("evaluated_on") or "")[:10]
        if d and start <= d <= end:
            out.append(r)
    return out


def open_positions(rows: list[dict]) -> list[dict]:
    """Positions still open (non-terminal) — the exact monitored set."""
    return [r for r in rows if is_open(r) and (r.get("ticker") or "").strip()]


def days_open(row: dict, today: date | None = None) -> int | None:
    """Age recomputed deterministically from timestamps (never incremented)."""
    pick_d = _parse_date(row.get("pick_date", ""))
    if pick_d is None:
        return None
    if today is None:
        today = date.today()
    return (today - pick_d).days


def is_overdue(row: dict, today: date | None = None) -> bool:
    if is_terminal(row):
        return False
    age = days_open(row, today)
    if age is None:
        return False
    return age >= max_hold_days(row.get("trade_type", ""))


# ─── Summaries (shared by daily / weekly / hypothesis views) ────
def summarize(rows: list[dict]) -> dict:
    """Bucketed summary of terminal rows. Wins/losses/flats/no-trades are
    separate buckets; the headline reflects real realized outcomes only."""
    buckets = {
        OUTCOME_WIN: [],
        OUTCOME_LOSS: [],
        OUTCOME_FLAT: [],
        OUTCOME_NO_TRADE: [],
        OUTCOME_UNVERIFIED: [],
    }
    for r in rows:
        if not is_terminal(r):
            continue
        buckets[classify_outcome(r)].append(r)
    realized = buckets[OUTCOME_WIN] + buckets[OUTCOME_LOSS] + buckets[OUTCOME_FLAT]
    return {
        "wins": len(buckets[OUTCOME_WIN]),
        "losses": len(buckets[OUTCOME_LOSS]),
        "flats": len(buckets[OUTCOME_FLAT]),
        "no_trades": len(buckets[OUTCOME_NO_TRADE]),
        "unverified": len(buckets[OUTCOME_UNVERIFIED]),
        "closed": sum(len(v) for v in buckets.values()),
        "realized": len(realized),
        "total_pnl": sum(pnl_dollar(r) for r in realized),
        "buckets": buckets,
    }


def reconcile_counts(rows: list[dict], start: str, end: str) -> dict:
    """Reconciliation projection: per-day terminal counts must sum to the
    range total (daily-sum == weekly == hypothesis-review sample).

    Returns {"daily": {date: summary}, "range": summary, "consistent": bool}.
    """
    in_range = closed_between(rows, start, end)
    daily: dict[str, dict] = {}
    for r in in_range:
        d = (r.get("evaluated_on") or "")[:10]
        daily.setdefault(d, []).append(r)
    daily_summaries = {d: summarize(rs) for d, rs in sorted(daily.items())}
    range_summary = summarize(in_range)
    consistent = (
        sum(s["closed"] for s in daily_summaries.values()) == range_summary["closed"]
        and sum(s["wins"] for s in daily_summaries.values()) == range_summary["wins"]
        and sum(s["losses"] for s in daily_summaries.values()) == range_summary["losses"]
        and sum(s["flats"] for s in daily_summaries.values()) == range_summary["flats"]
    )
    return {"daily": daily_summaries, "range": range_summary, "consistent": consistent}
