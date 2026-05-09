from pathlib import Path


def test_classify_provider_error_buckets_yfinance_failures():
    from src.market_data_health import classify_provider_error

    assert classify_provider_error("YFRateLimitError: Too Many Requests") == "rate_limited"
    assert classify_provider_error("HTTP Error 401: Unauthorized") == "unauthorized"
    assert classify_provider_error("HTTP Error 404: No data found") == "not_found"
    assert classify_provider_error("timed out waiting for response") == "timeout"


def test_record_market_data_event_writes_provider_summary(tmp_path, monkeypatch):
    import src.market_data_health as health

    monkeypatch.setattr(health, "DATA_DIR", tmp_path)

    health.record_market_data_event(
        provider="yfinance",
        stage="ohlcv",
        ticker="ABC",
        result="error",
        error_type="rate_limited",
        message="Too Many Requests",
        date_str="2026-05-07",
    )
    health.record_market_data_event(
        provider="yfinance",
        stage="ohlcv",
        ticker="XYZ",
        result="success",
        date_str="2026-05-07",
    )
    health.write_market_data_run_summary(
        universe_count=10,
        fetched_count=8,
        scored_count=5,
        final_pick_count=0,
        date_str="2026-05-07",
    )

    summary = health.summarize_market_data_health("2026-05-07")

    assert summary["providers"]["yfinance"]["attempts"] == 2
    assert summary["providers"]["yfinance"]["successes"] == 1
    assert summary["providers"]["yfinance"]["errors"] == 1
    assert summary["providers"]["yfinance"]["rate_limited"] == 1
    assert summary["by_stage"]["ohlcv"]["attempts"] == 2
    assert summary["run"]["universe_count"] == 10
    assert summary["run"]["fetched_count"] == 8
    assert summary["run"]["scored_count"] == 5
    assert summary["run"]["final_pick_count"] == 0
    assert summary["samples"][0]["ticker"] == "ABC"

def test_record_market_data_event_adds_canonical_failure_type(tmp_path, monkeypatch):
    import src.market_data_health as health

    monkeypatch.setattr(health, "DATA_DIR", tmp_path)

    health.record_market_data_event(
        provider="yfinance",
        stage="ohlcv",
        ticker="MISS",
        result="empty",
        message="empty OHLCV dataframe",
        date_str="2026-05-07",
    )
    health.record_market_data_event(
        provider="yfinance",
        stage="ohlcv",
        ticker="RATE",
        result="error",
        error_type="rate_limited",
        message="Too Many Requests",
        date_str="2026-05-07",
    )

    summary = health.summarize_market_data_health("2026-05-07")

    provider = summary["providers"]["yfinance"]
    assert provider["failure_types"]["empty_response"] == 1
    assert provider["failure_types"]["rate_limited"] == 1
    assert summary["samples"][0]["failure_type"] == "empty_response"
    assert summary["samples"][1]["failure_type"] == "rate_limited"
