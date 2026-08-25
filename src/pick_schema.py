"""Pick schema validation — Cluster A (metadata completeness).

An official (non-watch-only) pick must carry the full actionable field set
(the Aug-20-2026 reference shape): trade_type, entry, stop_loss, take_profit,
qty and a composite score. A watch-only pick must carry a specific
``watch_only_reason``. Nothing may be emitted "actionable-shaped but empty" —
the Aug 17/21 failure mode where every pick was silently degraded to WATCH
ONLY with no metadata.

``enforce_pick_schema`` never drops a pick: an official pick failing
validation is downgraded to watch-only with reason
``schema_incomplete: <missing fields>`` so the gap is explicit, logged, and
auditable instead of silently un-actionable.
"""
from __future__ import annotations

# Required for a fully actionable official pick (numeric fields must be > 0).
REQUIRED_ACTIONABLE_NUMERIC = ("entry", "stop_loss", "take_profit", "qty")
VALID_TRADE_TYPES = ("day", "swing", "multi")


def _pos_num(v) -> bool:
    try:
        return float(v) > 0
    except (TypeError, ValueError):
        return False


def validate_pick(p: dict) -> tuple[bool, list[str]]:
    """Validate one pick dict (pre-logging shape from the pipeline).

    Returns (ok, problems). Watch-only picks require a specific reason;
    official picks require the full actionable field set.
    """
    problems: list[str] = []
    if not (p.get("ticker") or "").strip():
        problems.append("missing ticker")

    if p.get("watch_only"):
        reason = (p.get("watch_only_reason") or "").strip()
        if not reason:
            problems.append("watch_only pick missing watch_only_reason")
        return (not problems, problems)

    ttype = (p.get("trade_type") or "").strip().lower()
    if ttype not in VALID_TRADE_TYPES:
        problems.append(f"trade_type missing/invalid: {ttype!r}")
    for field in REQUIRED_ACTIONABLE_NUMERIC:
        if not _pos_num(p.get(field)):
            problems.append(f"{field} missing/non-positive: {p.get(field)!r}")
    if p.get("score") in (None, ""):
        problems.append("composite score missing")

    # Long-only level sanity: SL below entry, TP above entry.
    if _pos_num(p.get("entry")) and _pos_num(p.get("stop_loss")) and _pos_num(p.get("take_profit")):
        entry, sl, tp = float(p["entry"]), float(p["stop_loss"]), float(p["take_profit"])
        if not (sl < entry < tp):
            problems.append(f"levels not ordered SL<entry<TP: {sl}/{entry}/{tp}")

    return (not problems, problems)


def enforce_pick_schema(picks: list[dict]) -> list[dict]:
    """Gate a batch of picks before logging/sending.

    Official picks that fail validation are downgraded IN PLACE to watch-only
    with an explicit, specific reason — never emitted actionable-shaped but
    empty, and never silently dropped.
    """
    for p in picks:
        ok, problems = validate_pick(p)
        if ok:
            continue
        detail = "; ".join(problems)
        if p.get("watch_only"):
            # Watch-only missing its reason: make the gap explicit.
            p["watch_only_reason"] = (p.get("watch_only_reason") or "").strip() or \
                "unspecified (schema gate: reason was empty)"
            print(f"[pick_schema] WATCH-ONLY reason gap for {p.get('ticker','?')}: {detail}")
        else:
            p["watch_only"] = True
            p["watch_only_reason"] = f"schema_incomplete: {detail}"
            print(f"[pick_schema] DOWNGRADE {p.get('ticker','?')} → watch-only ({detail})")
    return picks
