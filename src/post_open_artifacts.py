"""Lane 2 artifact writers: post-open watch-only opportunity lane.

Roadmap source: docs/planning/MULTI_LANE_IMPLEMENTATION_ROADMAP.md, Phase 3.

Artifacts owned by this lane (and only this lane):

- data/post_open_watchlist_YYYY-MM-DD.json
- data/post_open_opportunity_report_YYYY-MM-DD.md
- data/post_open_no_opportunity_YYYY-MM-DD.json
- data/post_open_run_status_YYYY-MM-DD.jsonl

Safety:

- never writes data/picks_log.csv,
- never writes data/signal_journal.jsonl,
- never writes data/learning_journal.jsonl,
- never writes official pick / no-pick artifacts,
- every artifact validates against src/post_open_contract.py before writing.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from src.post_open_contract import (
    CONTRACT_VERSION,
    DECISION_NO_OPPORTUNITY,
    DECISION_WATCH_ONLY_OPPORTUNITIES,
    STRATEGY_LANE,
    STRATEGY_VERSION,
    validate_post_open_no_opportunity,
    validate_post_open_watchlist,
)

DATA_DIR = Path("data")


def watchlist_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"post_open_watchlist_{date_str}.json"


def report_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"post_open_opportunity_report_{date_str}.md"


def no_opportunity_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"post_open_no_opportunity_{date_str}.json"


def run_status_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"post_open_run_status_{date_str}.jsonl"


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _base_payload(date_str: str, decision: str) -> dict:
    return {
        "date": date_str,
        "decision": decision,
        "strategy_lane": STRATEGY_LANE,
        "contract_version": CONTRACT_VERSION,
        "strategy_version": STRATEGY_VERSION,
        "generated_at_utc": _now_utc_iso(),
        "workflow_run_id": os.getenv("GITHUB_RUN_ID", "local"),
        "commit_sha": os.getenv("GITHUB_SHA", "local"),
        "mode": "monitoring_only",
        "watch_only": True,
        "official_pick_stats_impact": "none",
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
    }


def build_watchlist_payload(
    *,
    date_str: str,
    opportunities: list[dict],
    data_readiness: dict,
) -> dict:
    payload = _base_payload(date_str, DECISION_WATCH_ONLY_OPPORTUNITIES)
    payload.update({
        "artifact": "post_open_watchlist",
        "opportunity_count": len(opportunities),
        "opportunities": opportunities,
        "data_readiness": data_readiness,
    })
    return payload


def build_no_opportunity_payload(
    *,
    date_str: str,
    cause: str,
    summary: str,
    data_readiness: dict,
    counts: dict | None = None,
) -> dict:
    payload = _base_payload(date_str, DECISION_NO_OPPORTUNITY)
    payload.update({
        "artifact": "post_open_no_opportunity",
        "primary_no_opportunity_cause": cause,
        "human_readable_summary": summary,
        "data_readiness": data_readiness,
        "counts": counts or {},
    })
    return payload


def _levels_text(row: dict) -> list[str]:
    if row.get("watch_reference_price") is None:
        return ["  - Price levels: unavailable — no verified quote. Do not act without checking live data."]
    lines = [
        f"  - Watch-only reference level: ${float(row['watch_reference_price']):.2f}",
    ]
    if row.get("watch_stop_loss") is not None:
        lines.append(f"  - Watch-only SL observation: ${float(row['watch_stop_loss']):.2f}")
    if row.get("watch_take_profit") is not None:
        lines.append(f"  - Watch-only TP observation: ${float(row['watch_take_profit']):.2f}")
    return lines


def format_watchlist_markdown(payload: dict) -> str:
    lines = [
        "# Post-Open Watch-Only Opportunities (Lane 2 v0)",
        "",
        "Watch-only monitoring evidence. NOT official daily picks. NOT buy instructions.",
        "Not counted in official pick statistics.",
        "",
        f"- Date: **{payload['date']}**",
        f"- Opportunities observed: **{payload['opportunity_count']}**",
        f"- Strategy lane: `{payload['strategy_lane']}`",
        "- Paper trading enabled: **false**",
        "- Live trading enabled: **false**",
        "",
    ]
    for row in payload.get("opportunities", []):
        name = row.get("company_name") or ""
        title = f"{row['ticker']} — {name}" if name else row["ticker"]
        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"- Source: `{row.get('source')}` | Sentiment: {row.get('sentiment')}")
        lines.append(f"- Observed at: {row.get('observed_at_et')}")
        lines.append(f"- Watch score: {row.get('score')}")
        if row.get("headline"):
            lines.append(f"- Evidence: {row['headline']}")
        if row.get("reason_against"):
            lines.append(f"- Reason against: {row['reason_against']}")
        if row.get("risk_flags"):
            lines.append(f"- Risk flags: {', '.join(row['risk_flags'])}")
        lines.extend(_levels_text(row))
        lines.append("")
    lines.extend([
        "---",
        "",
        "_Watch-only observation levels are reference levels, not entries._",
        "_This lane must not mutate official picks, journals, or performance stats._",
        "",
    ])
    return "\n".join(lines)


def write_watchlist_artifacts(payload: dict, *, data_dir: Path = DATA_DIR) -> dict:
    errors = validate_post_open_watchlist(payload)
    if errors:
        raise RuntimeError("post-open watchlist failed validation: " + "; ".join(errors))

    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = watchlist_path(payload["date"], data_dir)
    md_path = report_path(payload["date"], data_dir)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_watchlist_markdown(payload), encoding="utf-8")
    return {"json_path": str(json_path), "markdown_path": str(md_path), "valid": True}


def write_no_opportunity_artifact(payload: dict, *, data_dir: Path = DATA_DIR) -> dict:
    errors = validate_post_open_no_opportunity(payload)
    if errors:
        raise RuntimeError("post-open no-opportunity failed validation: " + "; ".join(errors))

    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = no_opportunity_path(payload["date"], data_dir)
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"json_path": str(json_path), "valid": True}


def append_run_status(
    *,
    date_str: str,
    event: str,
    data_dir: Path = DATA_DIR,
    **fields,
) -> Path:
    """Append one run-status event row to the Lane 2 run-status ledger."""
    data_dir.mkdir(parents=True, exist_ok=True)
    path = run_status_path(date_str, data_dir)
    row = {
        "timestamp_utc": _now_utc_iso(),
        "date": date_str,
        "lane": STRATEGY_LANE,
        "event": event,
        "workflow_run_id": os.getenv("GITHUB_RUN_ID", "local"),
        "watch_only": True,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        **fields,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
    return path
