"""Market data provider health telemetry.

This module is intentionally lightweight and dependency-free so production runs
can record provider failures without creating another point of failure.

It helps distinguish:
- no candidate found
- market-data provider degraded/rate-limited
- invalid/delisted ticker noise
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

DATA_DIR = Path("data")
ET = ZoneInfo("America/New_York")
_LOCK = threading.Lock()
MAX_SAMPLES = 30


def _today_et() -> str:
    return datetime.now(timezone.utc).astimezone(ET).strftime("%Y-%m-%d")


def health_path(date_str: str | None = None, data_dir: Path | None = None) -> Path:
    root = data_dir or DATA_DIR
    return root / f"market_data_health_{date_str or _today_et()}.json"


def classify_provider_error(exc_or_message) -> str:
    """Normalize provider errors into operationally useful buckets."""
    if isinstance(exc_or_message, BaseException):
        raw = f"{type(exc_or_message).__name__}: {exc_or_message}"
    else:
        raw = str(exc_or_message or "")

    msg = raw.lower()
    if "yfratelimiterror" in msg or "too many requests" in msg or "rate limit" in msg:
        return "rate_limited"
    if "http error 401" in msg or "unauthorized" in msg:
        return "unauthorized"
    if "http error 404" in msg or "no data found" in msg or "possibly delisted" in msg:
        return "not_found"
    if "timeout" in msg or "timed out" in msg:
        return "timeout"
    if "empty" in msg or "no price data" in msg:
        return "empty"
    return "provider_error"


def _blank_summary(date_str: str) -> dict:
    return {
        "artifact": "market_data_health",
        "date": date_str,
        "timestamp_utc": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "providers": {},
        "by_stage": {},
        "run": {},
        "samples": [],
    }


def _load(path: Path, date_str: str) -> dict:
    if path.exists():
        try:
            data = json.loads(path.read_text())
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return _blank_summary(date_str)


def _save(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload["timestamp_utc"] = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def _provider_bucket(payload: dict, provider: str) -> dict:
    providers = payload.setdefault("providers", {})
    return providers.setdefault(provider, {
        "attempts": 0,
        "successes": 0,
        "empty": 0,
        "errors": 0,
        "rate_limited": 0,
        "unauthorized": 0,
        "not_found": 0,
        "timeout": 0,
        "provider_error": 0,
    })


def _stage_bucket(payload: dict, stage: str) -> dict:
    stages = payload.setdefault("by_stage", {})
    return stages.setdefault(stage, {
        "attempts": 0,
        "successes": 0,
        "empty": 0,
        "errors": 0,
    })


def record_market_data_event(
    *,
    provider: str = "yfinance",
    stage: str,
    ticker: str,
    result: str,
    error_type: str | None = None,
    message: str | None = None,
    date_str: str | None = None,
) -> None:
    """Record one market-data event.

    result should be one of: success, empty, error.
    """
    date = date_str or _today_et()
    path = health_path(date)
    safe_result = result if result in {"success", "empty", "error"} else "error"
    safe_error = error_type or (classify_provider_error(message) if safe_result != "success" else "")

    try:
        with _LOCK:
            payload = _load(path, date)

            pb = _provider_bucket(payload, provider)
            sb = _stage_bucket(payload, stage)

            pb["attempts"] += 1
            sb["attempts"] += 1

            if safe_result == "success":
                pb["successes"] += 1
                sb["successes"] += 1
            elif safe_result == "empty":
                pb["empty"] += 1
                sb["empty"] += 1
            else:
                pb["errors"] += 1
                sb["errors"] += 1
                if safe_error in pb:
                    pb[safe_error] += 1
                else:
                    pb["provider_error"] += 1

            if safe_result != "success":
                samples = payload.setdefault("samples", [])
                if len(samples) < MAX_SAMPLES:
                    samples.append({
                        "provider": provider,
                        "stage": stage,
                        "ticker": ticker,
                        "result": safe_result,
                        "error_type": safe_error,
                        "message": str(message or "")[:240],
                    })

            _save(path, payload)
    except Exception:
        # Telemetry must never break the picker.
        return


def write_market_data_run_summary(
    *,
    universe_count: int | None = None,
    fetched_count: int | None = None,
    scored_count: int | None = None,
    final_pick_count: int | None = None,
    date_str: str | None = None,
) -> None:
    """Attach high-level pipeline counters to today's provider-health artifact."""
    date = date_str or _today_et()
    path = health_path(date)
    try:
        with _LOCK:
            payload = _load(path, date)
            run = payload.setdefault("run", {})
            if universe_count is not None:
                run["universe_count"] = int(universe_count)
            if fetched_count is not None:
                run["fetched_count"] = int(fetched_count)
            if scored_count is not None:
                run["scored_count"] = int(scored_count)
            if final_pick_count is not None:
                run["final_pick_count"] = int(final_pick_count)
            _save(path, payload)
    except Exception:
        return


def summarize_market_data_health(date_str: str | None = None) -> dict:
    """Return today's market-data health summary if present."""
    date = date_str or _today_et()
    path = health_path(date)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text())
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}
