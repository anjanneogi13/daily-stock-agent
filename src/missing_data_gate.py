"""Missing-data fail-closed gate for Lane 1 official premarket picks.

This gate runs after portfolio risk and before official logging.

Purpose:
- prevent incomplete/malformed candidates from becoming official picks,
- preserve explainability for every blocked candidate,
- fail closed into official no-pick if all finalists are incomplete.

It is intentionally reporting/validation only:
- no fake picks,
- no scoring changes,
- no paper trading enablement,
- no live trading enablement.
"""

from __future__ import annotations

from typing import Any


CRITICAL_OFFICIAL_PICK_FIELDS = (
    "ticker",
    "score",
    "trade_type",
    "entry",
    "stop_loss",
    "take_profit",
    "risk_reward",
    "quantity",
)


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _safe_float(value: Any) -> float | None:
    try:
        if _is_blank(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> int | None:
    try:
        if _is_blank(value):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def official_pick_required_field_snapshot(candidate: dict) -> dict:
    """Return normalized fields required for an official logged pick."""
    scores = candidate.get("scores") if isinstance(candidate.get("scores"), dict) else {}
    plan = candidate.get("plan") if isinstance(candidate.get("plan"), dict) else {}
    info = candidate.get("info_short") if isinstance(candidate.get("info_short"), dict) else {}
    sanity = candidate.get("premarket_sanity") if isinstance(candidate.get("premarket_sanity"), dict) else {}
    portfolio_risk = candidate.get("portfolio_risk") if isinstance(candidate.get("portfolio_risk"), dict) else {}

    return {
        "ticker": candidate.get("ticker"),
        "company": info.get("name") or candidate.get("company") or "",
        "sector": info.get("sector") or "",
        "score": scores.get("composite"),
        "trade_type": candidate.get("trade_type") or scores.get("trade_type"),
        "entry": plan.get("entry") or candidate.get("entry"),
        "stop_loss": plan.get("stop_loss") or candidate.get("stop_loss"),
        "take_profit": plan.get("take_profit") or candidate.get("take_profit"),
        "risk_reward": plan.get("risk_reward") or candidate.get("risk_reward"),
        "quantity": plan.get("quantity") or candidate.get("quantity"),
        "premarket_action": candidate.get("premarket_action") or sanity.get("action"),
        "premarket_actionable": candidate.get("premarket_actionable") if "premarket_actionable" in candidate else sanity.get("actionable"),
        "portfolio_risk_passed": portfolio_risk.get("passed") if portfolio_risk else None,
    }


def validate_official_pick_required_data(candidate: dict) -> list[str]:
    """Return missing/malformed critical fields for one official candidate."""
    snap = official_pick_required_field_snapshot(candidate)
    errors: list[str] = []

    if _is_blank(snap["ticker"]):
        errors.append("ticker is missing")

    score = _safe_float(snap["score"])
    if score is None:
        errors.append("score is missing or non-numeric")
    elif score < 0:
        errors.append("score is negative")

    trade_type = str(snap.get("trade_type") or "").strip().lower()
    if trade_type not in {"day", "swing"}:
        errors.append("trade_type must be day or swing")

    entry = _safe_float(snap["entry"])
    stop_loss = _safe_float(snap["stop_loss"])
    take_profit = _safe_float(snap["take_profit"])
    risk_reward = _safe_float(snap["risk_reward"])
    quantity = _safe_int(snap["quantity"])

    if entry is None or entry <= 0:
        errors.append("entry must be positive")
    if stop_loss is None or stop_loss <= 0:
        errors.append("stop_loss must be positive")
    if take_profit is None or take_profit <= 0:
        errors.append("take_profit must be positive")
    if quantity is None or quantity <= 0:
        errors.append("quantity must be positive")
    if risk_reward is None or risk_reward <= 0:
        errors.append("risk_reward must be positive")

    if entry is not None and stop_loss is not None and stop_loss >= entry:
        errors.append("stop_loss must be below entry")
    if entry is not None and take_profit is not None and take_profit <= entry:
        errors.append("take_profit must be above entry")

    # If prior gates stamped these values, require them to remain affirmative.
    if snap.get("premarket_actionable") is False:
        errors.append("premarket_actionable is false")
    if snap.get("portfolio_risk_passed") is False:
        errors.append("portfolio_risk_passed is false")

    return errors


def apply_missing_data_gate(candidates: list[dict]) -> tuple[list[dict], list[dict], dict]:
    """Split candidates into complete official picks and missing-data blocks."""
    allowed: list[dict] = []
    blocked: list[dict] = []

    for candidate in candidates:
        errors = validate_official_pick_required_data(candidate)
        if errors:
            blocked.append({
                "ticker": candidate.get("ticker"),
                "rejection_stage": "missing_data",
                "block_type": "missing_or_malformed_required_data",
                "reason": "; ".join(errors),
                "missing_or_invalid_fields": errors,
                "required_field_snapshot": official_pick_required_field_snapshot(candidate),
                "candidate": candidate,
            })
            continue

        candidate["missing_data_gate"] = {
            "passed": True,
            "required_field_snapshot": official_pick_required_field_snapshot(candidate),
        }
        allowed.append(candidate)

    summary = {
        "input_count": len(candidates),
        "allowed_count": len(allowed),
        "blocked_count": len(blocked),
        "critical_fields": list(CRITICAL_OFFICIAL_PICK_FIELDS),
    }

    return allowed, blocked, summary
