from src.premarket_decision_contract import (
    CONTRACT_VERSION,
    DECISION_OFFICIAL_NO_PICK,
    DECISION_OFFICIAL_PICK,
    SCORING_VERSION,
    STRATEGY_LANE,
    STRATEGY_VERSION,
    contract_summary,
    validate_official_decision,
    validate_official_no_pick,
    validate_official_pick,
)


def valid_pick_payload():
    return {
        "artifact": "premarket_official_decision",
        "date": "2026-05-09",
        "decision": DECISION_OFFICIAL_PICK,
        "ticker": "AAPL",
        "company": "Apple Inc.",
        "strategy_lane": STRATEGY_LANE,
        "contract_version": CONTRACT_VERSION,
        "strategy_version": STRATEGY_VERSION,
        "scoring_version": SCORING_VERSION,
        "config_version": "test-config",
        "selection_time_et": "2026-05-09T08:45:00-04:00",
        "workflow_run_id": "123",
        "commit_sha": "abc123",
        "data_readiness_status": "ready",
        "provider_status": "healthy",
        "market_session_status": "premarket",
        "score": 0.72,
        "score_components": {"trend": 0.7},
        "entry": 100.0,
        "stop_loss": 95.0,
        "take_profit": 110.0,
        "risk_reward": 2.0,
        "quantity": 20,
        "risk_dollars": 100.0,
        "regime": "bull",
        "risk_flags": [],
        "selection_reason": "highest qualified candidate",
        "invalidation_conditions": ["breaks stop loss"],
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
    }


def valid_no_pick_payload():
    return {
        "artifact": "premarket_official_decision",
        "date": "2026-05-09",
        "decision": DECISION_OFFICIAL_NO_PICK,
        "strategy_lane": STRATEGY_LANE,
        "contract_version": CONTRACT_VERSION,
        "strategy_version": STRATEGY_VERSION,
        "scoring_version": SCORING_VERSION,
        "config_version": "test-config",
        "selection_time_et": "2026-05-09T08:45:00-04:00",
        "workflow_run_id": "123",
        "commit_sha": "abc123",
        "primary_no_pick_cause": "NO_PICK_NO_SCORED_CANDIDATES",
        "secondary_causes": [],
        "human_readable_summary": "No candidates passed scoring.",
        "data_readiness_status": "ready",
        "provider_status": "healthy",
        "market_session_status": "premarket",
        "pipeline": {"universe_count": 10, "final_pick_count": 0},
        "candidate_diagnostics": {"selected_pick_count": 0},
        "watch_only_available": False,
        "next_action": "Do not fabricate official picks.",
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
    }


def test_contract_summary_exposes_required_lane_metadata():
    summary = contract_summary()

    assert summary["strategy_lane"] == STRATEGY_LANE
    assert summary["contract_version"] == CONTRACT_VERSION
    assert summary["paper_trading_enabled"] is False
    assert summary["live_trading_enabled"] is False
    assert DECISION_OFFICIAL_PICK in summary["valid_decisions"]
    assert DECISION_OFFICIAL_NO_PICK in summary["valid_decisions"]
    assert "ticker" in summary["official_pick_required_fields"]
    assert "primary_no_pick_cause" in summary["official_no_pick_required_fields"]


def test_valid_official_pick_payload_passes_contract():
    assert validate_official_pick(valid_pick_payload()) == []
    assert validate_official_decision(valid_pick_payload()) == []


def test_official_pick_requires_ticker_and_safe_flags():
    payload = valid_pick_payload()
    payload.pop("ticker")
    payload["paper_trading_enabled"] = True

    errors = validate_official_pick(payload)

    assert "missing required field: ticker" in errors
    assert "paper_trading_enabled must be false for Lane 1 production-readiness work" in errors


def test_official_pick_requires_numeric_trade_plan():
    payload = valid_pick_payload()
    payload["entry"] = "not-a-number"
    payload["risk_reward"] = -1

    errors = validate_official_pick(payload)

    assert "entry must be numeric" in errors
    assert "risk_reward must be non-negative" in errors


def test_valid_official_no_pick_payload_passes_contract():
    assert validate_official_no_pick(valid_no_pick_payload()) == []
    assert validate_official_decision(valid_no_pick_payload()) == []


def test_official_no_pick_requires_supported_primary_cause():
    payload = valid_no_pick_payload()
    payload["primary_no_pick_cause"] = "RANDOM_UNKNOWN_CAUSE"

    errors = validate_official_no_pick(payload)

    assert "unsupported primary_no_pick_cause: RANDOM_UNKNOWN_CAUSE" in errors


def test_official_no_pick_requires_diagnostics_and_safe_flags():
    payload = valid_no_pick_payload()
    payload.pop("candidate_diagnostics")
    payload["live_trading_enabled"] = True

    errors = validate_official_no_pick(payload)

    assert "missing required field: candidate_diagnostics" in errors
    assert "live_trading_enabled must be false for Lane 1 production-readiness work" in errors


def test_validate_official_decision_rejects_unknown_decision():
    errors = validate_official_decision({"decision": "watch_only"})

    assert "decision must be one of" in errors[0]
