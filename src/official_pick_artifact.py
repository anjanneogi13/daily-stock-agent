"""Official pick artifact generation for Lane 1.

Builds and writes contract-compatible official pick artifacts after all gates pass.

Safety:
- no scoring changes,
- no fake picks,
- no paper trading enablement,
- no live trading enablement,
- no alerts.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .github_observability import github_observability_metadata

from .premarket_decision_contract import (
    CONTRACT_VERSION,
    DECISION_OFFICIAL_PICK,
    SCORING_VERSION,
    STRATEGY_LANE,
    STRATEGY_VERSION,
    validate_official_pick,
)


ET = ZoneInfo("America/New_York")



def _safe_ticker(ticker: str) -> str:
    return "".join(ch for ch in str(ticker).upper() if ch.isalnum() or ch in {"_", "-"})


def official_pick_artifact_filename(date_str: str, ticker: str) -> str:
    return f"premarket_official_pick_{date_str}_{_safe_ticker(ticker)}.json"


def official_pick_artifact_id(date_str: str, ticker: str) -> str:
    return f"premarket_official_pick:{date_str}:{_safe_ticker(ticker)}"


def official_pick_decision_id(date_str: str, ticker: str, workflow_run_id: str, commit_sha: str) -> str:
    short_sha = str(commit_sha or "local")[:12]
    return f"{STRATEGY_LANE}:{date_str}:{_safe_ticker(ticker)}:{workflow_run_id or 'local'}:{short_sha}"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_json_safe(v) for v in value[:25]]
    if isinstance(value, dict):
        return {
            str(k): _json_safe(v)
            for k, v in list(value.items())[:75]
            if k not in {"df", "dataframe", "history"}
        }
    return str(value)


def _score_components(pick: dict) -> dict:
    scores = pick.get("scores") if isinstance(pick.get("scores"), dict) else {}
    keys = (
        "composite",
        "day_score",
        "sector_mult",
        "sector_tag",
        "news_boost",
        "vol_ratio",
        "monster_score",
        "watchlist_boost",
    )
    return {key: _json_safe(scores.get(key)) for key in keys if key in scores}


def _risk_dollars(pick: dict) -> float:
    plan = pick.get("plan") if isinstance(pick.get("plan"), dict) else {}
    entry = _safe_float(plan.get("entry") or pick.get("entry"))
    stop_loss = _safe_float(plan.get("stop_loss") or pick.get("stop_loss"))
    quantity = _safe_int(plan.get("quantity") or pick.get("quantity"))
    return round(max(0.0, entry - stop_loss) * max(0, quantity), 2)


def _risk_flags(pick: dict) -> list[str]:
    flags: list[str] = []

    if pick.get("watch_only"):
        flags.append("WATCH_ONLY_FLAG_PRESENT")

    days = pick.get("days_to_earnings")
    try:
        if days is not None and int(days) < 10:
            flags.append("EARNINGS_WITHIN_10_DAYS")
    except (TypeError, ValueError):
        pass

    for warning in pick.get("smell_warnings") or []:
        if isinstance(warning, dict) and warning.get("code"):
            flags.append(f"SMELL_{str(warning['code']).upper()}")

    sanity = pick.get("premarket_sanity") if isinstance(pick.get("premarket_sanity"), dict) else {}
    action = sanity.get("action") or pick.get("premarket_action")
    if action and action != "SAFE":
        flags.append(f"PREMARKET_{str(action).upper()}")

    return sorted(set(flags))


def _selection_reason(pick: dict) -> str:
    ticker = pick.get("ticker", "?")
    scores = pick.get("scores") if isinstance(pick.get("scores"), dict) else {}
    score = scores.get("composite")
    tag = scores.get("sector_tag")
    trade_type = pick.get("trade_type") or scores.get("trade_type") or "swing"
    parts = [f"{ticker} selected as official {trade_type} pick"]
    if score is not None:
        parts.append(f"composite score {score}")
    if tag:
        parts.append(f"tag {tag}")
    sanity = pick.get("premarket_sanity") if isinstance(pick.get("premarket_sanity"), dict) else {}
    if sanity.get("reason"):
        parts.append(f"premarket sanity: {sanity['reason']}")
    return "; ".join(parts) + "."


def _invalidation_conditions(pick: dict) -> list[str]:
    plan = pick.get("plan") if isinstance(pick.get("plan"), dict) else {}
    stop_loss = plan.get("stop_loss")
    take_profit = plan.get("take_profit")
    conditions = [
        "Do not enter if fresh quote is unavailable.",
        "Do not enter if premarket sanity status changes to WATCH_ONLY or SKIP_TODAY.",
        "Do not enter if portfolio risk limits would be exceeded.",
    ]
    if stop_loss not in (None, ""):
        conditions.append(f"Invalid below stop loss {stop_loss}.")
    if take_profit not in (None, ""):
        conditions.append(f"Review/exit near take profit {take_profit}.")
    return conditions


def config_hash(path: "str | Path" = "config.yaml", *, respect_env: bool = True) -> str:
    """Return a REAL content fingerprint of the config file: 'sha256:<64hex>'.

    Vision item #22: makes every artifact traceable to the exact config bytes
    that produced it (the old value was the constant string "config.yaml", so
    picks from different weights were indistinguishable).

    - If CONFIG_VERSION is set in the env and respect_env is True, that explicit
      value wins (lets CI pin an exact label). 
    - On a missing/unreadable file, returns the safe non-hash sentinel
      "config-unavailable" -- never raises, so artifact generation cannot break
      on a config read error.
    """
    if respect_env:
        env = os.getenv("CONFIG_VERSION")
        if env:
            return env
    try:
        data = Path(path).read_bytes()
        return "sha256:" + hashlib.sha256(data).hexdigest()
    except Exception:
        return "config-unavailable"


def build_official_pick_artifact(
    pick: dict,
    *,
    date_str: str | None = None,
    selection_time_et: str | None = None,
    workflow_run_id: str | None = None,
    commit_sha: str | None = None,
    config_version: str | None = None,
    data_readiness_status: str = "ready",
    provider_status: str = "healthy",
    market_session_status: str = "premarket",
    regime: dict | str | None = None,
) -> dict:
    """Build one contract-compatible official pick artifact."""
    now_et = datetime.now(timezone.utc).astimezone(ET).replace(microsecond=0)
    date = date_str or now_et.strftime("%Y-%m-%d")
    selection_time = selection_time_et or now_et.isoformat()

    scores = pick.get("scores") if isinstance(pick.get("scores"), dict) else {}
    plan = pick.get("plan") if isinstance(pick.get("plan"), dict) else {}
    info = pick.get("info_short") if isinstance(pick.get("info_short"), dict) else {}

    ticker = str(pick.get("ticker") or "").strip().upper()
    workflow_run = workflow_run_id or os.getenv("GITHUB_RUN_ID", "local")
    commit = commit_sha or os.getenv("GITHUB_SHA", "local")
    artifact_filename = official_pick_artifact_filename(date, ticker)
    observability = github_observability_metadata()

    payload = {
        "artifact": "premarket_official_pick",
        "date": date,
        "decision": DECISION_OFFICIAL_PICK,
        "decision_id": official_pick_decision_id(date, ticker, workflow_run, commit),
        "artifact_id": official_pick_artifact_id(date, ticker),
        "artifact_filename": artifact_filename,
        "artifact_path": str(Path("data") / artifact_filename),
        "ticker": pick.get("ticker"),
        "company": info.get("name") or pick.get("company") or (str(pick.get("ticker") or "").strip().upper() or "UNKNOWN"),  # PR-A2.6 BUG-A: fall back to ticker so missing company name (e.g. yfinance rate-limited) does NOT silently block today's pick
        "strategy_lane": STRATEGY_LANE,
        "contract_version": CONTRACT_VERSION,
        "strategy_version": STRATEGY_VERSION,
        "scoring_version": SCORING_VERSION,
        "config_version": config_version or config_hash(),  # #22: real content hash, not a constant string
        "selection_time_et": selection_time,
        "workflow_run_id": workflow_run,
        "commit_sha": commit,
        **observability,
        "data_readiness_status": data_readiness_status,
        "provider_status": provider_status,
        "market_session_status": market_session_status,
        "score": _safe_float(scores.get("composite")),
        "score_components": _score_components(pick),
        "entry": _safe_float(plan.get("entry") or pick.get("entry")),
        "stop_loss": _safe_float(plan.get("stop_loss") or pick.get("stop_loss")),
        "take_profit": _safe_float(plan.get("take_profit") or pick.get("take_profit")),
        "risk_reward": _safe_float(plan.get("risk_reward") or pick.get("risk_reward")),
        "quantity": _safe_int(plan.get("quantity") or pick.get("quantity")),
        "risk_dollars": _risk_dollars(pick),
        "regime": _json_safe(regime or pick.get("regime") or "unknown"),
        "risk_flags": _risk_flags(pick),
        "selection_reason": _selection_reason(pick),
        "invalidation_conditions": _invalidation_conditions(pick),
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
    }

    return payload


def official_pick_artifact_path(data_dir: Path, date_str: str, ticker: str) -> Path:
    return data_dir / official_pick_artifact_filename(date_str, ticker)


def write_official_pick_artifacts(
    picks: list[dict],
    *,
    data_dir: Path = Path("data"),
    pipeline: dict | None = None,
    candidate_diagnostics: dict | None = None,
    regime: dict | str | None = None,
    data_readiness_status: str = "ready",
    provider_status: str = "healthy",
    market_session_status: str = "premarket",
    date_str: str | None = None,
    selection_time_et: str | None = None,
) -> dict:
    """Write official pick artifacts and a daily summary artifact.

    date_str and selection_time_et default to current ET when omitted.
    Callers (notably the dry-run script and any backfill tooling) may
    override both so generated artifact filenames/timestamps match the
    caller's target ET date instead of "now".
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    now_dt = datetime.now(timezone.utc).astimezone(ET).replace(microsecond=0)
    if date_str is None:
        date_str = now_dt.strftime("%Y-%m-%d")
    if selection_time_et is None:
        selection_time_et = now_dt.isoformat()

    artifacts = []
    validation_errors: dict[str, list[str]] = {}

    for pick in picks:
        ticker = str(pick.get("ticker") or "").strip().upper()
        payload = build_official_pick_artifact(
            pick,
            date_str=date_str,
            selection_time_et=selection_time_et,
            regime=regime,
            data_readiness_status=data_readiness_status,
            provider_status=provider_status,
            market_session_status=market_session_status,
        )
        path = official_pick_artifact_path(data_dir, date_str, ticker)
        payload["artifact_path"] = str(path)
        errors = validate_official_pick(payload)
        if errors:
            validation_errors[ticker or "?"] = errors
            continue

        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        artifacts.append({
            "ticker": ticker,
            "decision_id": payload["decision_id"],
            "artifact_id": payload["artifact_id"],
            "artifact_filename": payload["artifact_filename"],
            "path": str(path),
            "contract_version": payload["contract_version"],
            "workflow_run_url": payload.get("workflow_run_url", ""),
            "commit_url": payload.get("commit_url", ""),
            "artifact_bundle_name": payload.get("artifact_bundle_name", ""),
            "score": payload["score"],
            "entry": payload["entry"],
            "stop_loss": payload["stop_loss"],
            "take_profit": payload["take_profit"],
            "quantity": payload["quantity"],
        })

    summary = {
        "artifact": "premarket_official_pick_summary",
        "date": date_str,
        "timestamp_et": selection_time_et,
        "strategy_lane": STRATEGY_LANE,
        "contract_version": CONTRACT_VERSION,
        "official_pick_count": len(artifacts),
        "requested_pick_count": len(picks),
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        **github_observability_metadata(),
        "pipeline": _json_safe(pipeline or {}),
        "candidate_diagnostics_available": bool(candidate_diagnostics),
        "artifacts": artifacts,
        "validation_errors": validation_errors,
    }

    summary_path = data_dir / f"premarket_official_pick_summary_{date_str}.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary
