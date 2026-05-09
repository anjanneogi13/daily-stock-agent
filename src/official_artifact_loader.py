"""Load official Lane 1 pick artifacts for user-facing outputs.

Used by Telegram/GitHub issue formatters so public output is tied to the
validated official decision artifacts, not just CSV rows.

Reporting-only:
- no scoring changes,
- no pick generation,
- no trading behavior.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def official_pick_artifacts_for_date(date_str: str, data_dir: Path = Path("data")) -> dict[str, dict]:
    """Return official pick artifacts keyed by uppercase ticker."""
    artifacts: dict[str, dict] = {}
    for path in sorted(data_dir.glob(f"premarket_official_pick_{date_str}_*.json")):
        payload = _load_json(path)
        ticker = str(payload.get("ticker") or "").strip().upper()
        if ticker:
            payload["_artifact_path"] = str(path)
            artifacts[ticker] = payload
    return artifacts


def official_pick_summary_for_date(date_str: str, data_dir: Path = Path("data")) -> dict:
    path = data_dir / f"premarket_official_pick_summary_{date_str}.json"
    payload = _load_json(path)
    if payload:
        payload["_artifact_path"] = str(path)
    return payload


def _merge_non_empty(target: dict, key: str, value: Any) -> None:
    if value not in (None, ""):
        target[key] = value


def enrich_pick_row_with_artifact(row: dict, artifact: dict | None) -> dict:
    """Merge official artifact fields into a CSV row-shaped dict.

    CSV-compatible keys are preserved for legacy formatters.
    Artifact-only metadata is added with explicit names.
    """
    out = dict(row)
    artifact = artifact or {}
    if not artifact:
        out["official_artifact_present"] = False
        return out

    out["official_artifact_present"] = True
    out["official_artifact_path"] = artifact.get("_artifact_path", "")
    out["official_decision"] = artifact.get("decision", "")
    out["official_contract_version"] = artifact.get("contract_version", "")
    out["official_strategy_lane"] = artifact.get("strategy_lane", "")
    out["official_selection_reason"] = artifact.get("selection_reason", "")
    out["official_invalidation_conditions"] = artifact.get("invalidation_conditions", [])
    out["official_risk_flags"] = artifact.get("risk_flags", [])
    out["official_score_components"] = artifact.get("score_components", {})

    _merge_non_empty(out, "ticker", artifact.get("ticker"))
    _merge_non_empty(out, "company", artifact.get("company"))
    _merge_non_empty(out, "score", artifact.get("score"))
    _merge_non_empty(out, "entry", artifact.get("entry"))
    _merge_non_empty(out, "stop_loss", artifact.get("stop_loss"))
    _merge_non_empty(out, "take_profit", artifact.get("take_profit"))
    _merge_non_empty(out, "risk_reward", artifact.get("risk_reward"))
    _merge_non_empty(out, "qty", artifact.get("quantity"))
    _merge_non_empty(out, "risk_dollars", artifact.get("risk_dollars"))
    _merge_non_empty(out, "regime", artifact.get("regime"))

    return out


def enrich_pick_rows_with_artifacts(rows: list[dict], date_str: str, data_dir: Path = Path("data")) -> list[dict]:
    artifacts = official_pick_artifacts_for_date(date_str, data_dir=data_dir)
    enriched = []
    for row in rows:
        ticker = str(row.get("ticker") or "").strip().upper()
        enriched.append(enrich_pick_row_with_artifact(row, artifacts.get(ticker)))
    return enriched
