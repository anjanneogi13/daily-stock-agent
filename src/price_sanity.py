"""Quote sanity gate (Cluster F) — one validation for entry, monitoring, close.

Free ~15-min-delayed data plus split/ticker/symbol-mapping errors can produce
implausible prints (e.g. MRNA 2026-08-19: entry $62.96 / TP $66.72 quoted at
$117–$174, +86%…+176% intraday). Such prints must never drive trailing-SL
bookkeeping, TP/SL closes, or performance stats.

Policy:
  * Every consumed price is validated against a reference (entry, prior peak,
    or previous close) with a configurable single-interval plausibility bound.
  * A deviating quote is rejected/quarantined unless corroborated by an
    independent price agreeing within a small tolerance.
  * Ratios near common split factors are flagged as suspected corporate
    action / symbol-mapping mismatch.
  * On rejection callers must hold state ("stale quote — unverified") rather
    than fabricate movement, and log the gap.

Consumers:
  * scripts/intraday_monitor.py — gates monitoring quotes and TP/SL closes.
  * src/pick_evaluator.py       — gates daily bars in the TP/SL walk.
  * scripts/premarket_check.py  — gates the fresh-quote entry check.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

#: max plausible single-interval move (percent) vs. the reference price.
#: +170% intraday on a large-cap must not be trusted; genuine moves beyond
#: this bound require corroboration from an independent quote.
DEFAULT_MAX_MOVE_PCT = 25.0

#: two prices within this tolerance corroborate each other.
CORROBORATION_TOLERANCE_PCT = 2.0

#: common split/reverse-split factors → suspected corporate action.
_SPLIT_FACTORS = (2.0, 3.0, 4.0, 5.0, 10.0, 20.0)
_SPLIT_FACTOR_TOLERANCE = 0.03  # ±3%

REASON_OK = "ok"
REASON_NO_REFERENCE = "no_reference"
REASON_NON_POSITIVE = "non_positive_price"
REASON_IMPLAUSIBLE_MOVE = "implausible_move"
REASON_CORROBORATED = "corroborated_large_move"

QUARANTINE_DIR = Path("data")


def _suspected_corporate_action(price: float, reference: float) -> str | None:
    """Detect ratios near common split factors (both directions)."""
    if price <= 0 or reference <= 0:
        return None
    ratio = price / reference
    for f in _SPLIT_FACTORS:
        if abs(ratio - f) / f <= _SPLIT_FACTOR_TOLERANCE:
            return f"price/reference ratio ≈ {f:g}x — possible reverse-split or symbol mismatch"
        inv = 1.0 / f
        if abs(ratio - inv) / inv <= _SPLIT_FACTOR_TOLERANCE:
            return f"price/reference ratio ≈ 1/{f:g} — possible split-unadjusted print or symbol mismatch"
    return None


def validate_quote(
    price: float | None,
    reference: float | None,
    *,
    max_move_pct: float = DEFAULT_MAX_MOVE_PCT,
    corroborating_price: float | None = None,
    corroboration_tolerance_pct: float = CORROBORATION_TOLERANCE_PCT,
) -> dict:
    """Validate a quote against a reference price.

    Returns a dict:
        ok (bool)                — safe to consume this price
        reason (str)             — one of the REASON_* constants
        deviation_pct (float|None)
        suspected_action (str|None) — split/symbol-mismatch hint

    ``corroborating_price`` must come from an INDEPENDENT source (e.g. a
    second data provider); an out-of-bound move agreeing with it within
    tolerance is accepted as a real (corroborated) move.
    """
    try:
        price = float(price) if price is not None else None
    except (TypeError, ValueError):
        price = None
    if price is None or price <= 0:
        return {"ok": False, "reason": REASON_NON_POSITIVE,
                "deviation_pct": None, "suspected_action": None}

    try:
        reference = float(reference) if reference not in (None, "") else None
    except (TypeError, ValueError):
        reference = None
    if reference is None or reference <= 0:
        # Nothing to compare against — cannot judge plausibility.
        return {"ok": True, "reason": REASON_NO_REFERENCE,
                "deviation_pct": None, "suspected_action": None}

    deviation_pct = (price - reference) / reference * 100.0
    if abs(deviation_pct) <= max_move_pct:
        return {"ok": True, "reason": REASON_OK,
                "deviation_pct": round(deviation_pct, 2), "suspected_action": None}

    suspected = _suspected_corporate_action(price, reference)

    if corroborating_price:
        try:
            corr = float(corroborating_price)
        except (TypeError, ValueError):
            corr = 0.0
        if corr > 0 and abs(price - corr) / corr * 100.0 <= corroboration_tolerance_pct:
            return {"ok": True, "reason": REASON_CORROBORATED,
                    "deviation_pct": round(deviation_pct, 2),
                    "suspected_action": suspected}

    return {"ok": False, "reason": REASON_IMPLAUSIBLE_MOVE,
            "deviation_pct": round(deviation_pct, 2),
            "suspected_action": suspected}


def plausible_bar(prev_close: float | None, high: float, low: float,
                  *, max_move_pct: float = DEFAULT_MAX_MOVE_PCT) -> bool:
    """Sanity-check a daily OHLC bar against the previous close.

    Used by the evaluator's TP/SL walk so a corrupt bar cannot book a win or
    a loss. Bars with no reference are accepted (cannot judge).
    """
    if prev_close is None or prev_close <= 0:
        return True
    try:
        high = float(high)
        low = float(low)
    except (TypeError, ValueError):
        return False
    if low <= 0 or high <= 0 or high < low:
        return False
    up = (high - prev_close) / prev_close * 100.0
    down = (prev_close - low) / prev_close * 100.0
    return up <= max_move_pct and down <= max_move_pct


def log_quarantine(ticker: str, price, reference, check: dict,
                   context: str, data_dir: Path | None = None) -> None:
    """Append a quarantined-quote record for observability (best effort)."""
    try:
        d = data_dir or QUARANTINE_DIR
        d.mkdir(parents=True, exist_ok=True)
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = d / f"quote_quarantine_{day}.jsonl"
        rec = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "ticker": ticker,
            "price": price,
            "reference": reference,
            "reason": check.get("reason"),
            "deviation_pct": check.get("deviation_pct"),
            "suspected_action": check.get("suspected_action"),
            "context": context,
        }
        with path.open("a") as f:
            f.write(json.dumps(rec) + "\n")
    except Exception as e:  # never break monitoring because logging failed
        print(f"[price-sanity] quarantine log failed for {ticker}: {e}")
