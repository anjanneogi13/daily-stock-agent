import pytest

from src.provider_failure_taxonomy import (
    CANONICAL_FAILURE_TYPES,
    classify_legacy_provider_error,
    classify_provider_failure,
    classify_provider_failure_detail,
    failure_type_for_legacy_error_bucket,
    is_canonical_failure_type,
    legacy_error_bucket_for_failure_type,
)


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("YFRateLimitError: Too Many Requests", "rate_limited"),
        ("HTTP 429 rate limit exceeded", "rate_limited"),
        ("request timed out waiting for response", "timeout"),
        ("US market CLOSED (weekend)", "market_closed"),
        ("not_refreshed_stale_session", "stale_data"),
        ("HTTP Error 404: No data found, possibly delisted", "symbol_not_found"),
        ("missing quote currentPrice", "missing_quote"),
        ("provider returned no opening-range bars", "missing_intraday_bars"),
        ("empty OHLCV dataframe", "missing_history"),
        ("empty response from provider", "empty_response"),
        ("HTTP Error 401: Unauthorized", "provider_exception"),
    ],
)
def test_classify_provider_failure_canonical_labels(message, expected):
    assert classify_provider_failure(message) == expected
    assert expected in CANONICAL_FAILURE_TYPES
    assert is_canonical_failure_type(expected)


def test_unknown_provider_failure_is_captured():
    assert classify_provider_failure("") == "unknown_provider_failure"
    assert classify_provider_failure(None) == "unknown_provider_failure"


@pytest.mark.parametrize(
    ("failure_type", "expected_legacy"),
    [
        ("rate_limited", "rate_limited"),
        ("timeout", "timeout"),
        ("symbol_not_found", "not_found"),
        ("missing_history", "empty"),
        ("missing_intraday_bars", "empty"),
        ("empty_response", "empty"),
        ("provider_exception", "provider_error"),
        ("unknown_provider_failure", "provider_error"),
    ],
)
def test_legacy_error_bucket_mapping(failure_type, expected_legacy):
    assert legacy_error_bucket_for_failure_type(failure_type) == expected_legacy


@pytest.mark.parametrize(
    ("legacy", "expected_failure_type"),
    [
        ("rate_limited", "rate_limited"),
        ("timeout", "timeout"),
        ("not_found", "symbol_not_found"),
        ("empty", "empty_response"),
        ("unauthorized", "provider_exception"),
        ("provider_error", "provider_exception"),
    ],
)
def test_failure_type_for_legacy_error_bucket(legacy, expected_failure_type):
    assert failure_type_for_legacy_error_bucket(legacy) == expected_failure_type


def test_classify_legacy_provider_error_preserves_existing_public_buckets():
    assert classify_legacy_provider_error("Too Many Requests") == "rate_limited"
    assert classify_legacy_provider_error("HTTP Error 404: No data found") == "not_found"
    assert classify_legacy_provider_error("timed out waiting") == "timeout"
    assert classify_legacy_provider_error("empty OHLCV dataframe") == "empty"


def test_classify_provider_failure_detail_returns_both_labels():
    detail = classify_provider_failure_detail("provider returned no opening-range bars")

    assert detail.failure_type == "missing_intraday_bars"
    assert detail.legacy_error_bucket == "empty"
    assert "opening-range bars" in detail.reason
