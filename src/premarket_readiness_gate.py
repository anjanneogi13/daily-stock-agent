"""Premarket data-readiness gate for Lane 1.

This module decides whether the official premarket pick lane has enough market
data to proceed from universe/data fetch into scoring and official selection.

It is intentionally conservative:
- no fake picks,
- no paper trading,
- no live trading,
- fail closed into official no-pick when critical data is missing.
"""

from __future__ import annotations

from typing import Any


DEFAULT_MIN_FETCH_COVERAGE = 0.25
DEFAULT_MIN_FETCHED_COUNT = 25


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return default


def _provider_attempt_summary(market_data_health: dict | None) -> dict:
    health = market_data_health or {}
    providers = health.get("providers") if isinstance(health.get("providers"), dict) else {}
    by_stage = health.get("by_stage") if isinstance(health.get("by_stage"), dict) else {}

    provider_attempts = 0
    provider_successes = 0
    provider_errors = 0
    provider_empty = 0
    provider_rate_limited = 0
    provider_unauthorized = 0

    for stats in providers.values():
        if not isinstance(stats, dict):
            continue
        provider_attempts += _safe_int(stats.get("attempts"))
        provider_successes += _safe_int(stats.get("successes"))
        provider_errors += _safe_int(stats.get("errors"))
        provider_empty += _safe_int(stats.get("empty"))
        provider_rate_limited += _safe_int(stats.get("rate_limited"))
        provider_unauthorized += _safe_int(stats.get("unauthorized"))

    ohlcv = by_stage.get("ohlcv") if isinstance(by_stage.get("ohlcv"), dict) else {}
    ohlcv_attempts = _safe_int(ohlcv.get("attempts"))
    ohlcv_successes = _safe_int(ohlcv.get("successes"))
    ohlcv_errors = _safe_int(ohlcv.get("errors"))
    ohlcv_empty = _safe_int(ohlcv.get("empty"))

    return {
        "provider_attempts": provider_attempts,
        "provider_successes": provider_successes,
        "provider_errors": provider_errors,
        "provider_empty": provider_empty,
        "provider_rate_limited": provider_rate_limited,
        "provider_unauthorized": provider_unauthorized,
        "ohlcv_attempts": ohlcv_attempts,
        "ohlcv_successes": ohlcv_successes,
        "ohlcv_errors": ohlcv_errors,
        "ohlcv_empty": ohlcv_empty,
    }


def build_premarket_readiness_decision(
    *,
    universe_count: int,
    fetched_count: int,
    market_data_health: dict | None = None,
    min_fetch_coverage: float = DEFAULT_MIN_FETCH_COVERAGE,
    min_fetched_count: int = DEFAULT_MIN_FETCHED_COUNT,
) -> dict:
    """Return a JSON-safe readiness decision for Lane 1.

    The gate passes only when enough OHLCV data was fetched to make official
    scoring meaningful.

    This is a pre-selection gate. It should run before scoring/final selection.
    """

    universe_count = _safe_int(universe_count)
    fetched_count = _safe_int(fetched_count)
    min_fetch_coverage = max(0.0, min(1.0, _safe_float(min_fetch_coverage, DEFAULT_MIN_FETCH_COVERAGE)))
    min_fetched_count = max(1, _safe_int(min_fetched_count, DEFAULT_MIN_FETCHED_COUNT))

    provider_summary = _provider_attempt_summary(market_data_health)
    required_by_coverage = int(universe_count * min_fetch_coverage)
    required_fetched_count = max(1, min(min_fetched_count, required_by_coverage or min_fetched_count))

    fetch_coverage = round(fetched_count / universe_count, 4) if universe_count > 0 else 0.0

    warnings: list[str] = []

    if provider_summary["provider_rate_limited"] > 0:
        warnings.append("provider_rate_limited")
    if provider_summary["provider_unauthorized"] > 0:
        warnings.append("provider_unauthorized")
    if provider_summary["ohlcv_empty"] > 0:
        warnings.append("ohlcv_empty_results_present")
    if provider_summary["ohlcv_errors"] > 0:
        warnings.append("ohlcv_errors_present")

    if universe_count <= 0:
        return {
            "passed": False,
            "status": "not_ready_empty_universe",
            "primary_no_pick_cause": "NO_PICK_DATA_READINESS_FAILED",
            "human_readable_summary": "Official premarket pick skipped because the candidate universe was empty.",
            "universe_count": universe_count,
            "fetched_count": fetched_count,
            "fetch_coverage": fetch_coverage,
            "required_fetched_count": required_fetched_count,
            "warnings": warnings,
            "provider_summary": provider_summary,
        }

    if fetched_count <= 0:
        return {
            "passed": False,
            "status": "not_ready_no_market_data",
            "primary_no_pick_cause": "NO_PICK_DATA_PROVIDER_DEGRADED",
            "human_readable_summary": "Official premarket pick skipped because no OHLCV market data was fetched.",
            "universe_count": universe_count,
            "fetched_count": fetched_count,
            "fetch_coverage": fetch_coverage,
            "required_fetched_count": required_fetched_count,
            "warnings": warnings,
            "provider_summary": provider_summary,
        }

    if fetched_count < required_fetched_count:
        return {
            "passed": False,
            "status": "not_ready_low_market_data_coverage",
            "primary_no_pick_cause": "NO_PICK_DATA_READINESS_FAILED",
            "human_readable_summary": (
                "Official premarket pick skipped because fetched market-data coverage "
                f"was too low: {fetched_count}/{universe_count} tickers."
            ),
            "universe_count": universe_count,
            "fetched_count": fetched_count,
            "fetch_coverage": fetch_coverage,
            "required_fetched_count": required_fetched_count,
            "warnings": warnings,
            "provider_summary": provider_summary,
        }

    ohlcv_attempts = provider_summary["ohlcv_attempts"]
    ohlcv_successes = provider_summary["ohlcv_successes"]
    ohlcv_errors = provider_summary["ohlcv_errors"]
    ohlcv_empty = provider_summary["ohlcv_empty"]

    if ohlcv_attempts >= 10 and ohlcv_successes == 0 and (ohlcv_errors + ohlcv_empty) >= ohlcv_attempts:
        return {
            "passed": False,
            "status": "not_ready_provider_degraded",
            "primary_no_pick_cause": "NO_PICK_DATA_PROVIDER_DEGRADED",
            "human_readable_summary": "Official premarket pick skipped because OHLCV providers were degraded.",
            "universe_count": universe_count,
            "fetched_count": fetched_count,
            "fetch_coverage": fetch_coverage,
            "required_fetched_count": required_fetched_count,
            "warnings": warnings,
            "provider_summary": provider_summary,
        }

    return {
        "passed": True,
        "status": "ready",
        "primary_no_pick_cause": "",
        "human_readable_summary": "Premarket data readiness gate passed.",
        "universe_count": universe_count,
        "fetched_count": fetched_count,
        "fetch_coverage": fetch_coverage,
        "required_fetched_count": required_fetched_count,
        "warnings": warnings,
        "provider_summary": provider_summary,
    }


def assert_premarket_readiness_or_no_pick(**kwargs) -> dict:
    """Convenience wrapper for callers that want the decision payload."""
    return build_premarket_readiness_decision(**kwargs)
