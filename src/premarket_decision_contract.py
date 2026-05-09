"""Official premarket decision contract for Lane 1.

This module defines the required contract for Lane 1:
Premarket Official Daily Stock Pick.

It is intentionally behavior-neutral:
- does not generate picks,
- does not change scoring,
- does not enable paper trading,
- does not enable live trading,
- does not send alerts,
- does not mutate runtime state.

The purpose is to make the official pick/no-pick contract explicit and testable
before later phases wire it into main.py and the daily-picks workflow.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


STRATEGY_LANE = "premarket_official_daily_pick"

CONTRACT_VERSION = "premarket_decision_contract_v1"
STRATEGY_VERSION = "premarket_official_v1"
SCORING_VERSION = "legacy_composite_v1"

DECISION_OFFICIAL_PICK = "official_pick"
DECISION_OFFICIAL_NO_PICK = "official_no_pick"

VALID_DECISIONS = {
    DECISION_OFFICIAL_PICK,
    DECISION_OFFICIAL_NO_PICK,
}

OFFICIAL_PICK_REQUIRED_FIELDS = (
    "artifact",
    "date",
    "decision",
    "ticker",
    "company",
    "strategy_lane",
    "contract_version",
    "strategy_version",
    "scoring_version",
    "config_version",
    "selection_time_et",
    "workflow_run_id",
    "commit_sha",
    "data_readiness_status",
    "provider_status",
    "market_session_status",
    "score",
    "score_components",
    "entry",
    "stop_loss",
    "take_profit",
    "risk_reward",
    "quantity",
    "risk_dollars",
    "regime",
    "risk_flags",
    "selection_reason",
    "invalidation_conditions",
    "paper_trading_enabled",
    "live_trading_enabled",
)

OFFICIAL_NO_PICK_REQUIRED_FIELDS = (
    "artifact",
    "date",
    "decision",
    "strategy_lane",
    "contract_version",
    "strategy_version",
    "scoring_version",
    "config_version",
    "selection_time_et",
    "workflow_run_id",
    "commit_sha",
    "primary_no_pick_cause",
    "secondary_causes",
    "human_readable_summary",
    "data_readiness_status",
    "provider_status",
    "market_session_status",
    "pipeline",
    "candidate_diagnostics",
    "watch_only_available",
    "next_action",
    "paper_trading_enabled",
    "live_trading_enabled",
)

OFFICIAL_PICK_NUMERIC_FIELDS = (
    "score",
    "entry",
    "stop_loss",
    "take_profit",
    "risk_reward",
    "quantity",
    "risk_dollars",
)

OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES = {
    "NO_PICK_DATA_PROVIDER_DEGRADED",
    "NO_PICK_DATA_READINESS_FAILED",
    "NO_PICK_MARKET_CLOSED",
    "NO_PICK_WINDOW_MISSED",
    "NO_PICK_NO_SCORED_CANDIDATES",
    "NO_PICK_FILTERS_REMOVED_ALL",
    "NO_PICK_ALL_FINALISTS_HARD_BLOCKED",
    "NO_PICK_PREMARKET_SANITY_BLOCKED_ALL",
    "NO_PICK_RISK_GATE_BLOCKED_ALL",
    "NO_PICK_RUNTIME_FAILURE",
    "NO_PICK_UNKNOWN_POST_FILTER_GATING",
}

SAFETY_FLAGS = (
    "paper_trading_enabled",
    "live_trading_enabled",
)


def _is_missing(value: Any) -> bool:
    """Return true for values that violate required-field presence.

    Empty dict/list are allowed because some diagnostics may be intentionally
    present but empty. None and blank strings are not allowed.
    """
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _missing_required_fields(payload: Mapping[str, Any], required: tuple[str, ...]) -> list[str]:
    return [field for field in required if field not in payload or _is_missing(payload.get(field))]


def _validate_safety_flags(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in SAFETY_FLAGS:
        if payload.get(field) is not False:
            errors.append(f"{field} must be false for Lane 1 production-readiness work")
    return errors


def _validate_numeric_fields(payload: Mapping[str, Any], fields: tuple[str, ...]) -> list[str]:
    errors: list[str] = []
    for field in fields:
        value = payload.get(field)
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            errors.append(f"{field} must be numeric")
            continue
        if field in {"score", "risk_reward", "quantity", "risk_dollars"} and numeric < 0:
            errors.append(f"{field} must be non-negative")
        if field in {"entry", "stop_loss", "take_profit"} and numeric <= 0:
            errors.append(f"{field} must be positive")
    return errors


def validate_official_pick(payload: Mapping[str, Any]) -> list[str]:
    """Validate an official premarket pick payload.

    Returns:
        A list of human-readable validation errors. Empty list means valid.
    """
    errors: list[str] = []

    missing = _missing_required_fields(payload, OFFICIAL_PICK_REQUIRED_FIELDS)
    errors.extend(f"missing required field: {field}" for field in missing)

    if payload.get("decision") != DECISION_OFFICIAL_PICK:
        errors.append(f"decision must be {DECISION_OFFICIAL_PICK!r}")

    if payload.get("strategy_lane") != STRATEGY_LANE:
        errors.append(f"strategy_lane must be {STRATEGY_LANE!r}")

    errors.extend(_validate_safety_flags(payload))
    errors.extend(_validate_numeric_fields(payload, OFFICIAL_PICK_NUMERIC_FIELDS))

    score_components = payload.get("score_components")
    if score_components is not None and not isinstance(score_components, Mapping):
        errors.append("score_components must be a mapping")

    risk_flags = payload.get("risk_flags")
    if risk_flags is not None and not isinstance(risk_flags, list):
        errors.append("risk_flags must be a list")

    invalidation_conditions = payload.get("invalidation_conditions")
    if invalidation_conditions is not None and not isinstance(invalidation_conditions, list):
        errors.append("invalidation_conditions must be a list")

    return errors


def validate_official_no_pick(payload: Mapping[str, Any]) -> list[str]:
    """Validate an official premarket no-pick payload.

    Returns:
        A list of human-readable validation errors. Empty list means valid.
    """
    errors: list[str] = []

    missing = _missing_required_fields(payload, OFFICIAL_NO_PICK_REQUIRED_FIELDS)
    errors.extend(f"missing required field: {field}" for field in missing)

    if payload.get("decision") != DECISION_OFFICIAL_NO_PICK:
        errors.append(f"decision must be {DECISION_OFFICIAL_NO_PICK!r}")

    if payload.get("strategy_lane") != STRATEGY_LANE:
        errors.append(f"strategy_lane must be {STRATEGY_LANE!r}")

    primary = payload.get("primary_no_pick_cause")
    if primary and primary not in OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES:
        errors.append(f"unsupported primary_no_pick_cause: {primary}")

    secondary = payload.get("secondary_causes")
    if secondary is not None and not isinstance(secondary, list):
        errors.append("secondary_causes must be a list")

    pipeline = payload.get("pipeline")
    if pipeline is not None and not isinstance(pipeline, Mapping):
        errors.append("pipeline must be a mapping")

    candidate_diagnostics = payload.get("candidate_diagnostics")
    if candidate_diagnostics is not None and not isinstance(candidate_diagnostics, Mapping):
        errors.append("candidate_diagnostics must be a mapping")

    if payload.get("watch_only_available") not in {True, False}:
        errors.append("watch_only_available must be boolean")

    errors.extend(_validate_safety_flags(payload))

    return errors


def validate_official_decision(payload: Mapping[str, Any]) -> list[str]:
    """Validate either official pick or official no-pick payload."""
    decision = payload.get("decision")
    if decision == DECISION_OFFICIAL_PICK:
        return validate_official_pick(payload)
    if decision == DECISION_OFFICIAL_NO_PICK:
        return validate_official_no_pick(payload)
    return [f"decision must be one of {sorted(VALID_DECISIONS)}"]


def contract_summary() -> dict[str, Any]:
    """Return a JSON-safe summary of the Lane 1 decision contract."""
    return {
        "strategy_lane": STRATEGY_LANE,
        "contract_version": CONTRACT_VERSION,
        "strategy_version": STRATEGY_VERSION,
        "scoring_version": SCORING_VERSION,
        "valid_decisions": sorted(VALID_DECISIONS),
        "official_pick_required_fields": list(OFFICIAL_PICK_REQUIRED_FIELDS),
        "official_no_pick_required_fields": list(OFFICIAL_NO_PICK_REQUIRED_FIELDS),
        "official_no_pick_allowed_primary_causes": sorted(OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES),
        "safety_flags": list(SAFETY_FLAGS),
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
    }
