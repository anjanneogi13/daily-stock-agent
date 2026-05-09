from src.premarket_readiness_gate import build_premarket_readiness_decision


def test_readiness_passes_with_sufficient_fetched_coverage():
    result = build_premarket_readiness_decision(
        universe_count=100,
        fetched_count=40,
        market_data_health={
            "providers": {
                "yfinance": {"attempts": 100, "successes": 40, "errors": 0, "empty": 0}
            },
            "by_stage": {
                "ohlcv": {"attempts": 100, "successes": 40, "errors": 0, "empty": 0}
            },
        },
    )

    assert result["passed"] is True
    assert result["status"] == "ready"
    assert result["primary_no_pick_cause"] == ""


def test_readiness_fails_when_universe_is_empty():
    result = build_premarket_readiness_decision(
        universe_count=0,
        fetched_count=0,
        market_data_health={},
    )

    assert result["passed"] is False
    assert result["status"] == "not_ready_empty_universe"
    assert result["primary_no_pick_cause"] == "NO_PICK_DATA_READINESS_FAILED"


def test_readiness_fails_when_no_market_data_was_fetched():
    result = build_premarket_readiness_decision(
        universe_count=100,
        fetched_count=0,
        market_data_health={
            "by_stage": {
                "ohlcv": {"attempts": 100, "successes": 0, "errors": 100, "empty": 0}
            }
        },
    )

    assert result["passed"] is False
    assert result["status"] == "not_ready_no_market_data"
    assert result["primary_no_pick_cause"] == "NO_PICK_DATA_PROVIDER_DEGRADED"


def test_readiness_fails_when_fetched_coverage_is_too_low():
    result = build_premarket_readiness_decision(
        universe_count=200,
        fetched_count=10,
        market_data_health={},
        min_fetch_coverage=0.25,
        min_fetched_count=25,
    )

    assert result["passed"] is False
    assert result["status"] == "not_ready_low_market_data_coverage"
    assert result["primary_no_pick_cause"] == "NO_PICK_DATA_READINESS_FAILED"
    assert result["required_fetched_count"] == 25


def test_readiness_warns_on_provider_errors_but_passes_when_coverage_is_enough():
    result = build_premarket_readiness_decision(
        universe_count=100,
        fetched_count=35,
        market_data_health={
            "providers": {
                "yfinance": {
                    "attempts": 100,
                    "successes": 35,
                    "errors": 10,
                    "empty": 5,
                    "rate_limited": 2,
                    "unauthorized": 0,
                }
            },
            "by_stage": {
                "ohlcv": {"attempts": 100, "successes": 35, "errors": 10, "empty": 5}
            },
        },
    )

    assert result["passed"] is True
    assert "provider_rate_limited" in result["warnings"]
    assert "ohlcv_errors_present" in result["warnings"]
    assert "ohlcv_empty_results_present" in result["warnings"]


def test_readiness_fails_when_ohlcv_providers_are_fully_degraded():
    result = build_premarket_readiness_decision(
        universe_count=100,
        fetched_count=30,
        market_data_health={
            "by_stage": {
                "ohlcv": {"attempts": 20, "successes": 0, "errors": 20, "empty": 0}
            },
        },
    )

    assert result["passed"] is False
    assert result["status"] == "not_ready_provider_degraded"
    assert result["primary_no_pick_cause"] == "NO_PICK_DATA_PROVIDER_DEGRADED"
