from src.missing_data_gate import (
    apply_missing_data_gate,
    official_pick_required_field_snapshot,
    validate_official_pick_required_data,
)


def candidate():
    return {
        "ticker": "AAPL",
        "trade_type": "swing",
        "scores": {"composite": 0.75},
        "info_short": {"name": "Apple Inc.", "sector": "Technology"},
        "plan": {
            "entry": 100.0,
            "stop_loss": 95.0,
            "take_profit": 110.0,
            "risk_reward": 2.0,
            "quantity": 10,
        },
        "premarket_actionable": True,
        "portfolio_risk": {"passed": True},
    }


def test_valid_candidate_passes_missing_data_gate():
    allowed, blocked, summary = apply_missing_data_gate([candidate()])

    assert [p["ticker"] for p in allowed] == ["AAPL"]
    assert blocked == []
    assert summary["allowed_count"] == 1


def test_missing_ticker_is_blocked():
    c = candidate()
    c["ticker"] = ""

    errors = validate_official_pick_required_data(c)

    assert "ticker is missing" in errors


def test_missing_trade_plan_values_are_blocked():
    c = candidate()
    c["plan"]["entry"] = None
    c["plan"]["quantity"] = 0

    errors = validate_official_pick_required_data(c)

    assert "entry must be positive" in errors
    assert "quantity must be positive" in errors


def test_invalid_trade_plan_relationships_are_blocked():
    c = candidate()
    c["plan"]["stop_loss"] = 101
    c["plan"]["take_profit"] = 99

    errors = validate_official_pick_required_data(c)

    assert "stop_loss must be below entry" in errors
    assert "take_profit must be above entry" in errors


def test_watch_only_candidate_is_blocked():
    c = candidate()
    c["premarket_actionable"] = False

    errors = validate_official_pick_required_data(c)

    assert "premarket_actionable is false" in errors


def test_apply_missing_data_gate_reports_blocked_candidates():
    good = candidate()
    bad = candidate()
    bad["ticker"] = "MSFT"
    bad["plan"]["risk_reward"] = None

    allowed, blocked, summary = apply_missing_data_gate([good, bad])

    assert [p["ticker"] for p in allowed] == ["AAPL"]
    assert [p["ticker"] for p in blocked] == ["MSFT"]
    assert blocked[0]["rejection_stage"] == "missing_data"
    assert "risk_reward must be positive" in blocked[0]["reason"]
    assert summary["blocked_count"] == 1


def test_required_field_snapshot_is_json_safe_and_contains_core_fields():
    snap = official_pick_required_field_snapshot(candidate())

    assert snap["ticker"] == "AAPL"
    assert snap["company"] == "Apple Inc."
    assert snap["score"] == 0.75
    assert snap["entry"] == 100.0
