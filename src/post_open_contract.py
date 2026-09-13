"""Lane 2 contract: post-open / late-daily watch-only opportunity lane.

Roadmap source: docs/planning/MULTI_LANE_IMPLEMENTATION_ROADMAP.md, Phase 3.

This module defines the required contract for Lane 2:
Post-open / late-daily watch-only opportunities.

It is intentionally behavior-neutral:
- does not generate opportunities,
- does not change scoring,
- does not enable paper trading,
- does not enable live trading,
- does not send alerts,
- does not mutate runtime state.

Lane 2 hard rules (from the roadmap):

- watch-only, monitoring-only,
- NOT official picks,
- NOT paper trades,
- NOT buy instructions,
- must not mutate data/picks_log.csv,
- must not mutate official pick artifacts,
- outputs are never counted in official pick statistics.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any


STRATEGY_LANE = "post_open_watch_only_opportunity"

CONTRACT_VERSION = "post_open_contract_v1"
STRATEGY_VERSION = "post_open_watch_only_v0"

DECISION_WATCH_ONLY_OPPORTUNITIES = "watch_only_opportunities"
DECISION_NO_OPPORTUNITY = "no_opportunity"

VALID_DECISIONS = {
    DECISION_WATCH_ONLY_OPPORTUNITIES,
    DECISION_NO_OPPORTUNITY,
}

IDEA_TYPE = "post_open_watch_only"

# Required fields for each opportunity row inside the watchlist artifact.
OPPORTUNITY_REQUIRED_FIELDS = (
    "ticker",
    "date",
    "idea_type",
    "source",
    "headline",
    "sentiment",
    "observed_at_et",
    "score",
    "risk_flags",
    "reason_against",
    "watch_only",
    "official_premarket_pick",
    "paper_trading_enabled",
    "live_trading_enabled",
)

# Top-level required fields for the watchlist artifact.
WATCHLIST_REQUIRED_FIELDS = (
    "artifact",
    "date",
    "decision",
    "strategy_lane",
    "contract_version",
    "strategy_version",
    "generated_at_utc",
    "opportunity_count",
    "opportunities",
    "data_readiness",
    "watch_only",
    "official_pick_stats_impact",
    "paper_trading_enabled",
    "live_trading_enabled",
)

# Top-level required fields for the no-opportunity artifact.
NO_OPPORTUNITY_REQUIRED_FIELDS = (
    "artifact",
    "date",
    "decision",
    "strategy_lane",
    "contract_version",
    "strategy_version",
    "generated_at_utc",
    "primary_no_opportunity_cause",
    "human_readable_summary",
    "data_readiness",
    "watch_only",
    "official_pick_stats_impact",
    "paper_trading_enabled",
    "live_trading_enabled",
)

NO_OPPORTUNITY_ALLOWED_PRIMARY_CAUSES = {
    "NO_OPPORTUNITY_NO_FRESH_SIGNALS",
    "NO_OPPORTUNITY_ALL_BELOW_THRESHOLD",
    "NO_OPPORTUNITY_ALL_FILTERED",
    "NO_OPPORTUNITY_INPUTS_MISSING",
    "NO_OPPORTUNITY_MARKET_CLOSED",
    "NO_OPPORTUNITY_TOO_LATE_IN_SESSION",
}

SAFETY_FLAGS = (
    "paper_trading_enabled",
    "live_trading_enabled",
)

# User-facing copy rules: Lane 2 wording must never look like an executable
# instruction. These patterns are rejected in copy fields (headline stays raw
# news text and is exempt; `reason` and level labels are checked).
_FORBIDDEN_ACTION_PATTERNS = (
    re.compile(r"\bbuy\s+now\b", re.IGNORECASE),
    re.compile(r"\bsell\s+now\b", re.IGNORECASE),
    re.compile(r"^\s*buy\b", re.IGNORECASE),
    re.compile(r"^\s*sell\b", re.IGNORECASE),
    re.compile(r"\bplace\s+(a\s+)?(market|limit)\s+order\b", re.IGNORECASE),
    re.compile(r"\bexecute\s+(the\s+)?trade\b", re.IGNORECASE),
    re.compile(r"\benter\s+(a\s+)?position\b", re.IGNORECASE),
    re.compile(r"\benter\s+now\b", re.IGNORECASE),
)

COPY_FIELDS_CHECKED_FOR_ACTION_WORDING = ("reason", "level_basis", "warning")


def has_forbidden_action_wording(text: str) -> bool:
    """Return True when user-facing copy reads like an executable instruction."""
    value = str(text or "")
    return any(pattern.search(value) for pattern in _FORBIDDEN_ACTION_PATTERNS)


def _is_missing(value: Any) -> bool:
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
            errors.append(f"{field} must be false for Lane 2 watch-only work")
    return errors


def _validate_watch_only_flags(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("watch_only") is not True:
        errors.append("watch_only must be true")
    return errors


def validate_post_open_opportunity(row: Mapping[str, Any]) -> list[str]:
    """Validate a single Lane 2 opportunity row.

    Returns a list of human-readable validation errors. Empty list = valid.
    """
    errors: list[str] = []

    missing = _missing_required_fields(row, OPPORTUNITY_REQUIRED_FIELDS)
    errors.extend(f"missing required field: {field}" for field in missing)

    if row.get("idea_type") != IDEA_TYPE:
        errors.append(f"idea_type must be {IDEA_TYPE!r}")

    errors.extend(_validate_watch_only_flags(row))

    if row.get("official_premarket_pick") is not False:
        errors.append("official_premarket_pick must be false")

    errors.extend(_validate_safety_flags(row))

    risk_flags = row.get("risk_flags")
    if risk_flags is not None and not isinstance(risk_flags, list):
        errors.append("risk_flags must be a list")

    for field in ("watch_reference_price", "watch_stop_loss", "watch_take_profit"):
        value = row.get(field)
        if value is None:
            continue
        try:
            if float(value) <= 0:
                errors.append(f"{field} must be positive when present")
        except (TypeError, ValueError):
            errors.append(f"{field} must be numeric when present")

    for field in COPY_FIELDS_CHECKED_FOR_ACTION_WORDING:
        if has_forbidden_action_wording(row.get(field)):
            errors.append(f"{field} contains forbidden executable-action wording")

    return errors


def validate_post_open_watchlist(payload: Mapping[str, Any]) -> list[str]:
    """Validate the Lane 2 watchlist artifact payload."""
    errors: list[str] = []

    missing = _missing_required_fields(payload, WATCHLIST_REQUIRED_FIELDS)
    errors.extend(f"missing required field: {field}" for field in missing)

    if payload.get("decision") != DECISION_WATCH_ONLY_OPPORTUNITIES:
        errors.append(f"decision must be {DECISION_WATCH_ONLY_OPPORTUNITIES!r}")

    if payload.get("strategy_lane") != STRATEGY_LANE:
        errors.append(f"strategy_lane must be {STRATEGY_LANE!r}")

    if payload.get("official_pick_stats_impact") != "none":
        errors.append("official_pick_stats_impact must be 'none'")

    errors.extend(_validate_watch_only_flags(payload))
    errors.extend(_validate_safety_flags(payload))

    opportunities = payload.get("opportunities")
    if not isinstance(opportunities, list):
        errors.append("opportunities must be a list")
        return errors

    if payload.get("opportunity_count") != len(opportunities):
        errors.append("opportunity_count must match len(opportunities)")

    if not opportunities:
        errors.append(
            "watchlist artifact must contain at least one opportunity; "
            "use the no-opportunity artifact otherwise"
        )

    for index, row in enumerate(opportunities):
        if not isinstance(row, Mapping):
            errors.append(f"opportunities[{index}] must be a mapping")
            continue
        for error in validate_post_open_opportunity(row):
            errors.append(f"opportunities[{index}]: {error}")

    return errors


def validate_post_open_no_opportunity(payload: Mapping[str, Any]) -> list[str]:
    """Validate the Lane 2 no-opportunity artifact payload."""
    errors: list[str] = []

    missing = _missing_required_fields(payload, NO_OPPORTUNITY_REQUIRED_FIELDS)
    errors.extend(f"missing required field: {field}" for field in missing)

    if payload.get("decision") != DECISION_NO_OPPORTUNITY:
        errors.append(f"decision must be {DECISION_NO_OPPORTUNITY!r}")

    if payload.get("strategy_lane") != STRATEGY_LANE:
        errors.append(f"strategy_lane must be {STRATEGY_LANE!r}")

    primary = payload.get("primary_no_opportunity_cause")
    if primary and primary not in NO_OPPORTUNITY_ALLOWED_PRIMARY_CAUSES:
        errors.append(f"unsupported primary_no_opportunity_cause: {primary}")

    if payload.get("official_pick_stats_impact") != "none":
        errors.append("official_pick_stats_impact must be 'none'")

    errors.extend(_validate_watch_only_flags(payload))
    errors.extend(_validate_safety_flags(payload))

    return errors


def validate_post_open_decision(payload: Mapping[str, Any]) -> list[str]:
    """Validate either Lane 2 decision artifact payload."""
    decision = payload.get("decision")
    if decision == DECISION_WATCH_ONLY_OPPORTUNITIES:
        return validate_post_open_watchlist(payload)
    if decision == DECISION_NO_OPPORTUNITY:
        return validate_post_open_no_opportunity(payload)
    return [f"decision must be one of {sorted(VALID_DECISIONS)}"]


def contract_summary() -> dict[str, Any]:
    """Return a JSON-safe summary of the Lane 2 contract."""
    return {
        "strategy_lane": STRATEGY_LANE,
        "contract_version": CONTRACT_VERSION,
        "strategy_version": STRATEGY_VERSION,
        "valid_decisions": sorted(VALID_DECISIONS),
        "idea_type": IDEA_TYPE,
        "opportunity_required_fields": list(OPPORTUNITY_REQUIRED_FIELDS),
        "watchlist_required_fields": list(WATCHLIST_REQUIRED_FIELDS),
        "no_opportunity_required_fields": list(NO_OPPORTUNITY_REQUIRED_FIELDS),
        "no_opportunity_allowed_primary_causes": sorted(NO_OPPORTUNITY_ALLOWED_PRIMARY_CAUSES),
        "safety_flags": list(SAFETY_FLAGS),
        "official_pick_stats_impact": "none",
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
    }
