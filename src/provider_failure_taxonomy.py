"""Provider failure taxonomy.

Canonical observe-only labels for provider/data failures across reports.

This module does not fetch data, score candidates, create picks, or alter
trading behavior. It only classifies already-observed failures.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CANONICAL_FAILURE_TYPES = {
    "rate_limited",
    "timeout",
    "empty_response",
    "stale_data",
    "missing_quote",
    "missing_history",
    "missing_intraday_bars",
    "market_closed",
    "symbol_not_found",
    "provider_exception",
    "unknown_provider_failure",
}


LEGACY_ERROR_BUCKET_BY_FAILURE_TYPE = {
    "rate_limited": "rate_limited",
    "timeout": "timeout",
    "empty_response": "empty",
    "stale_data": "provider_error",
    "missing_quote": "provider_error",
    "missing_history": "empty",
    "missing_intraday_bars": "empty",
    "market_closed": "provider_error",
    "symbol_not_found": "not_found",
    "provider_exception": "provider_error",
    "unknown_provider_failure": "provider_error",
}


FAILURE_TYPE_BY_LEGACY_ERROR_BUCKET = {
    "rate_limited": "rate_limited",
    "timeout": "timeout",
    "empty": "empty_response",
    "not_found": "symbol_not_found",
    "unauthorized": "provider_exception",
    "provider_error": "provider_exception",
}


@dataclass(frozen=True)
class ProviderFailureClassification:
    """Structured provider failure classification."""

    failure_type: str
    legacy_error_bucket: str
    reason: str


def _raw_text(exc_or_message: Any) -> str:
    if isinstance(exc_or_message, BaseException):
        return f"{type(exc_or_message).__name__}: {exc_or_message}"
    return str(exc_or_message or "")


def classify_provider_failure(
    exc_or_message: Any = "",
    *,
    result: str | None = None,
    stage: str | None = None,
    status: str | None = None,
) -> str:
    """Return the canonical provider failure type.

    The canonical taxonomy is intentionally broader than the historical
    market-data health buckets. Existing callers that need the old buckets
    should use ``legacy_error_bucket_for_failure_type`` or
    ``classify_legacy_provider_error``.
    """
    raw = " ".join(
        part
        for part in [
            _raw_text(exc_or_message),
            str(result or ""),
            str(stage or ""),
            str(status or ""),
        ]
        if part
    )
    msg = raw.lower()

    if not msg.strip():
        return "unknown_provider_failure"

    if (
        "yfratelimiterror" in msg
        or "too many requests" in msg
        or "rate limit" in msg
        or "rate_limited" in msg
        or "429" in msg
    ):
        return "rate_limited"

    if "timeout" in msg or "timed out" in msg or "read timed out" in msg:
        return "timeout"

    if (
        "market closed" in msg
        or "weekend" in msg
        or "holiday" in msg
        or "outside market hours" in msg
    ):
        return "market_closed"

    if (
        "stale" in msg
        or "stale_session" in msg
        or "not_refreshed_stale_session" in msg
        or "previous trading day" in msg
    ):
        return "stale_data"

    if (
        "http error 404" in msg
        or "404" in msg
        or "not found" in msg
        or "no data found" in msg
        or "possibly delisted" in msg
        or "symbol_not_found" in msg
        or "delisted" in msg
    ):
        return "symbol_not_found"

    if (
        "missing quote" in msg
        or "missing_quote" in msg
        or "no quote" in msg
        or "quote unavailable" in msg
        or "missing currentprice" in msg
        or "missing current price" in msg
    ):
        return "missing_quote"

    if (
        "missing intraday" in msg
        or "missing_intraday_bars" in msg
        or "no intraday bars" in msg
        or "no opening-range bars" in msg
        or "provider returned no opening-range bars" in msg
        or "no forward bars" in msg
    ):
        return "missing_intraday_bars"

    if (
        "empty ohlcv" in msg
        or "empty history" in msg
        or "missing history" in msg
        or "missing_history" in msg
        or "no price data" in msg
    ):
        return "missing_history"

    if "empty" in msg or "empty_response" in msg or "blank response" in msg:
        return "empty_response"

    if (
        "unauthorized" in msg
        or "http error 401" in msg
        or "connection" in msg
        or "network" in msg
        or "ssl" in msg
        or "provider_error" in msg
        or "provider_exception" in msg
        or "exception" in msg
        or "error" in msg
    ):
        return "provider_exception"

    return "unknown_provider_failure"


def legacy_error_bucket_for_failure_type(failure_type: str) -> str:
    """Map canonical taxonomy to historical market-data health bucket."""
    return LEGACY_ERROR_BUCKET_BY_FAILURE_TYPE.get(
        failure_type,
        "provider_error",
    )


def failure_type_for_legacy_error_bucket(error_bucket: str) -> str:
    """Map historical market-data health bucket to canonical taxonomy."""
    return FAILURE_TYPE_BY_LEGACY_ERROR_BUCKET.get(
        str(error_bucket or ""),
        "unknown_provider_failure",
    )


def classify_legacy_provider_error(exc_or_message: Any = "") -> str:
    """Compatibility wrapper returning historical market-data health buckets.

    Preserve the older public bucket names used by ``market_data_health`` tests
    and summaries. Canonical taxonomy still maps unauthorized/API/auth failures
    to ``provider_exception``.
    """
    msg = _raw_text(exc_or_message).lower()
    if "http error 401" in msg or "unauthorized" in msg:
        return "unauthorized"
    return legacy_error_bucket_for_failure_type(
        classify_provider_failure(exc_or_message)
    )


def classify_provider_failure_detail(
    exc_or_message: Any = "",
    *,
    result: str | None = None,
    stage: str | None = None,
    status: str | None = None,
    legacy_error_bucket: str | None = None,
) -> ProviderFailureClassification:
    """Return canonical and legacy provider failure labels together."""
    if legacy_error_bucket:
        failure_type = failure_type_for_legacy_error_bucket(legacy_error_bucket)
        if failure_type == "unknown_provider_failure":
            failure_type = classify_provider_failure(
                exc_or_message,
                result=result,
                stage=stage,
                status=status,
            )
    else:
        failure_type = classify_provider_failure(
            exc_or_message,
            result=result,
            stage=stage,
            status=status,
        )

    return ProviderFailureClassification(
        failure_type=failure_type,
        legacy_error_bucket=legacy_error_bucket_for_failure_type(failure_type),
        reason=_raw_text(exc_or_message)[:240],
    )


def is_canonical_failure_type(value: str) -> bool:
    return value in CANONICAL_FAILURE_TYPES
