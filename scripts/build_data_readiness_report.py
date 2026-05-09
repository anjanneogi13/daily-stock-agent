#!/usr/bin/env python3
"""Daily Data Readiness Report v0 — observe-only.

Determines whether the system had enough daily artifacts/data to judge official
pick behavior. This report does not alter scoring or create picks.

Outputs:
- data/data_readiness_YYYY-MM-DD.json
- data/data_readiness_YYYY-MM-DD.md
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATA_DIR = Path("data")

SAFETY = {
    "observe_only": True,
    "production_scoring_effect": False,
    "official_score_boost_enabled": False,
    "paper_trading_enabled": False,
    "live_trading_enabled": False,
    "buy_instructions_enabled": False,
}

NO_PICK_CLASSIFICATIONS = {
    "strategy_driven_no_qualified_candidates",
    "data_provider_failure",
    "pipeline_incomplete",
    "diagnostics_missing",
    "market_closed_or_no_run_expected",
    "mixed_or_uncertain",
}


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        return {"_parse_error": str(exc), "_path": str(path)}


def load_jsonl(path: Path) -> tuple[list[dict], int]:
    rows: list[dict] = []
    bad = 0
    if not path.exists():
        return rows, bad
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                rows.append(obj)
        except Exception:
            bad += 1
    return rows, bad


def _date_prefix(value: Any) -> str:
    return str(value or "")[:10]


def _read_picks_for_date(path: Path, date_str: str) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    try:
        with path.open(newline="") as f:
            for row in csv.DictReader(f):
                if _date_prefix(row.get("pick_date")) == date_str:
                    rows.append(row)
    except Exception:
        return []
    return rows


def _latest_jsonl_record(path: Path) -> dict:
    rows, _bad = load_jsonl(path)
    return rows[-1] if rows else {}


def _contains_provider_failure_text(obj: Any) -> bool:
    text = json.dumps(obj, sort_keys=True, default=str).lower()
    tokens = [
        "provider",
        "rate limit",
        "rate_limit",
        "timeout",
        "missing quote",
        "missing history",
        "missing intraday",
        "no forward bars",
        "data_insufficient",
        "no-candidate",
        "no_candidate",
        "market data",
        "data failure",
        "fetch failed",
    ]
    return any(tok in text for tok in tokens)


def _diagnostic_counts(rejection_obj: Any) -> dict:
    diag = rejection_obj.get("diagnostics", rejection_obj) if isinstance(rejection_obj, dict) else {}
    if not isinstance(diag, dict):
        return {
            "pre_hard_block_candidate_count": 0,
            "hard_blocked_candidate_count": 0,
            "rejected_candidate_count": 0,
            "selected_pick_count": 0,
        }

    return {
        "pre_hard_block_candidate_count": len(diag.get("pre_hard_block_candidates") or []),
        "hard_blocked_candidate_count": len(diag.get("hard_blocked_candidates") or []),
        "rejected_candidate_count": len(diag.get("rejected_candidates") or []),
        "selected_pick_count": len(diag.get("selected_picks") or []),
    }


def _opening_range_status(rows: list[dict]) -> dict:
    quality_counter = Counter(
        str(r.get("opening_range_quality_status") or r.get("quality_status") or "unknown")
        for r in rows
    )
    volume_counter = Counter(
        str(r.get("opening_range_volume_status") or r.get("volume_status") or "unknown")
        for r in rows
    )

    no_forward = 0
    for row in rows:
        status_text = json.dumps(row, sort_keys=True, default=str).lower()
        if (
            "data_insufficient_no_forward_bars" in status_text
            or "not_evaluable_no_forward_bars" in status_text
            or "no forward bars" in status_text
        ):
            no_forward += 1

    return {
        "observation_count": len(rows),
        "quality_status_counts": dict(sorted(quality_counter.items())),
        "volume_status_counts": dict(sorted(volume_counter.items())),
        "no_forward_bars_count": no_forward,
        "has_no_forward_bars": no_forward > 0,
    }


def classify_no_pick(
    *,
    official_pick_count: int,
    daily_run_status_available: bool,
    no_pick_report_available: bool,
    rejection_artifact_available: bool,
    candidate_diagnostics_available: bool,
    provider_failure_evidence: bool,
    watch_only_lane_count: int,
    theme_bridge_available: bool,
) -> str:
    """Classify no-pick/readiness outcome without inventing missing reasons."""
    if official_pick_count > 0:
        return "strategy_driven_no_qualified_candidates"

    if not daily_run_status_available and not no_pick_report_available and not rejection_artifact_available:
        return "pipeline_incomplete"

    if provider_failure_evidence:
        return "data_provider_failure"

    if not candidate_diagnostics_available:
        return "diagnostics_missing"

    if rejection_artifact_available and candidate_diagnostics_available:
        return "strategy_driven_no_qualified_candidates"

    if watch_only_lane_count == 0 and theme_bridge_available:
        return "mixed_or_uncertain"

    return "mixed_or_uncertain"


def _official_pick_readiness_status(classification: str, official_pick_count: int) -> str:
    if official_pick_count > 0:
        return "official_picks_available"
    if classification == "pipeline_incomplete":
        return "not_ready_pipeline_incomplete"
    if classification == "data_provider_failure":
        return "not_ready_data_provider_failure"
    if classification == "diagnostics_missing":
        return "not_ready_diagnostics_missing"
    if classification == "strategy_driven_no_qualified_candidates":
        return "ready_no_qualified_candidates"
    return "readiness_uncertain"


def _warnings(
    *,
    daily_run_status_available: bool,
    no_pick_report_available: bool,
    rejection_artifact_available: bool,
    candidate_diagnostics_available: bool,
    watch_only_lane_count: int,
    opening_range: dict,
    provider_failure_evidence: bool,
    theme_bridge_available: bool,
) -> list[str]:
    out: list[str] = []
    if not daily_run_status_available:
        out.append("daily_run_status_missing")
    if not no_pick_report_available:
        out.append("no_pick_report_missing")
    if not rejection_artifact_available:
        out.append("candidate_rejection_artifact_missing")
    if not candidate_diagnostics_available:
        out.append("candidate_diagnostics_missing")
    if watch_only_lane_count == 0:
        out.append("watch_only_lanes_missing_or_empty")
    if opening_range.get("has_no_forward_bars"):
        out.append("opening_range_no_forward_bars_detected")
    if provider_failure_evidence:
        out.append("provider_or_market_data_failure_evidence_detected")
    if theme_bridge_available and (not rejection_artifact_available or watch_only_lane_count == 0):
        out.append("theme_bridge_reports_missing_daily_inputs")
    return list(dict.fromkeys(out))


def build_data_readiness_report(
    *,
    date_str: str,
    data_dir: Path = DATA_DIR,
) -> dict:
    run_status_path = data_dir / f"daily_picks_run_status_{date_str}.jsonl"
    no_pick_report_path = data_dir / f"daily_picks_no_pick_report_{date_str}.json"
    rejection_path = data_dir / f"daily_picks_candidate_rejections_{date_str}.json"
    late_daily_path = data_dir / f"late_daily_ideas_{date_str}.jsonl"
    opening_range_path = data_dir / f"opening_range_observations_{date_str}.jsonl"
    intraday_momentum_path = data_dir / f"intraday_momentum_observations_{date_str}.jsonl"
    theme_bridge_path = data_dir / f"theme_pick_bridge_{date_str}.json"
    picks_log_path = data_dir / "picks_log.csv"

    run_status_rows, run_status_bad = load_jsonl(run_status_path)
    latest_run_status = run_status_rows[-1] if run_status_rows else {}

    no_pick_report = load_json(no_pick_report_path, {})
    rejection_obj = load_json(rejection_path, {})
    theme_bridge = load_json(theme_bridge_path, {})

    late_rows, late_bad = load_jsonl(late_daily_path)
    opening_rows, opening_bad = load_jsonl(opening_range_path)
    momentum_rows, momentum_bad = load_jsonl(intraday_momentum_path)

    official_rows = _read_picks_for_date(picks_log_path, date_str)

    diagnostic_counts = _diagnostic_counts(rejection_obj)
    candidate_diagnostics_available = (
        rejection_path.exists()
        and bool(rejection_obj)
        and not isinstance(rejection_obj, list)
        and (
            bool(rejection_obj.get("diagnostics_available"))
            or any(v > 0 for v in diagnostic_counts.values())
            or "diagnostics" in rejection_obj
        )
    )

    opening_status = _opening_range_status(opening_rows)

    theme_bridge_input_status = (
        theme_bridge.get("input_status", {}) if isinstance(theme_bridge, dict) else {}
    )

    provider_failure_evidence = any(
        [
            _contains_provider_failure_text(latest_run_status),
            _contains_provider_failure_text(no_pick_report),
            _contains_provider_failure_text(rejection_obj),
            opening_status["has_no_forward_bars"],
        ]
    )

    watch_only_lane_count = len(late_rows) + len(opening_rows) + len(momentum_rows)

    classification = classify_no_pick(
        official_pick_count=len(official_rows),
        daily_run_status_available=run_status_path.exists() and bool(run_status_rows),
        no_pick_report_available=no_pick_report_path.exists(),
        rejection_artifact_available=rejection_path.exists(),
        candidate_diagnostics_available=candidate_diagnostics_available,
        provider_failure_evidence=provider_failure_evidence,
        watch_only_lane_count=watch_only_lane_count,
        theme_bridge_available=theme_bridge_path.exists(),
    )

    official_status = _official_pick_readiness_status(classification, len(official_rows))

    input_status = {
        "daily_run_status_available": run_status_path.exists() and bool(run_status_rows),
        "daily_run_status_parse_errors": run_status_bad,
        "no_pick_report_available": no_pick_report_path.exists(),
        "rejection_artifact_available": rejection_path.exists(),
        "candidate_diagnostics_available": candidate_diagnostics_available,
        "picks_log_available": picks_log_path.exists(),
        "theme_bridge_available": theme_bridge_path.exists(),
        "late_daily_ideas_available": late_daily_path.exists(),
        "opening_range_observations_available": opening_range_path.exists(),
        "intraday_momentum_observations_available": intraday_momentum_path.exists(),
    }

    watch_only_lanes = {
        "late_daily_ideas": {
            "path": str(late_daily_path),
            "exists": late_daily_path.exists(),
            "rows": len(late_rows),
            "parse_errors": late_bad,
        },
        "opening_range_observations": {
            "path": str(opening_range_path),
            "exists": opening_range_path.exists(),
            "rows": len(opening_rows),
            "parse_errors": opening_bad,
            **opening_status,
        },
        "intraday_momentum_observations": {
            "path": str(intraday_momentum_path),
            "exists": intraday_momentum_path.exists(),
            "rows": len(momentum_rows),
            "parse_errors": momentum_bad,
        },
    }

    warnings = _warnings(
        daily_run_status_available=input_status["daily_run_status_available"],
        no_pick_report_available=input_status["no_pick_report_available"],
        rejection_artifact_available=input_status["rejection_artifact_available"],
        candidate_diagnostics_available=candidate_diagnostics_available,
        watch_only_lane_count=watch_only_lane_count,
        opening_range=opening_status,
        provider_failure_evidence=provider_failure_evidence,
        theme_bridge_available=input_status["theme_bridge_available"],
    )

    return {
        "artifact": "data_readiness",
        "date": date_str,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **SAFETY,
        "official_pick_readiness_status": official_status,
        "no_pick_classification": classification,
        "data_provider_status": (
            "provider_or_market_data_failure_evidence_detected"
            if provider_failure_evidence
            else "no_provider_failure_evidence_in_available_artifacts"
        ),
        "official_pick_count": len(official_rows),
        "official_pick_tickers": sorted(str(r.get("ticker") or "").upper() for r in official_rows if r.get("ticker")),
        "input_status": input_status,
        "candidate_diagnostics": {
            "path": str(rejection_path),
            "available": rejection_path.exists(),
            **diagnostic_counts,
        },
        "watch_only_lanes": watch_only_lanes,
        "theme_bridge_input_status": theme_bridge_input_status,
        "latest_run_status": latest_run_status,
        "readiness_warnings": warnings,
        "source_files": {
            "daily_run_status": str(run_status_path),
            "no_pick_report": str(no_pick_report_path),
            "candidate_rejections": str(rejection_path),
            "picks_log": str(picks_log_path),
            "late_daily_ideas": str(late_daily_path),
            "opening_range_observations": str(opening_range_path),
            "intraday_momentum_observations": str(intraday_momentum_path),
            "theme_pick_bridge": str(theme_bridge_path),
        },
        "safety_flags": [
            "observe_only",
            "not_official_scoring",
            "no_production_scoring_effect",
            "not_paper_trade",
            "not_live_trade",
            "no_buy_instructions",
        ],
    }


def data_readiness_json_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"data_readiness_{date_str}.json"


def data_readiness_markdown_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"data_readiness_{date_str}.md"


def format_markdown(report: dict) -> str:
    lines = [
        "# Daily Data Readiness Report",
        "",
        "Observe-only. This report does not alter scoring or create picks.",
        "",
        f"- Date: **{report['date']}**",
        f"- Official pick readiness status: **{report['official_pick_readiness_status']}**",
        f"- No-pick classification: **{report['no_pick_classification']}**",
        f"- Data provider status: **{report['data_provider_status']}**",
        f"- Official pick count: **{report['official_pick_count']}**",
        f"- Official tickers: `{', '.join(report['official_pick_tickers']) or 'none'}`",
        "",
        "## Input Status",
    ]

    for key, value in report["input_status"].items():
        lines.append(f"- {key}: **{value}**")

    lines.extend(["", "## Candidate Diagnostics"])
    for key, value in report["candidate_diagnostics"].items():
        lines.append(f"- {key}: **{value}**")

    lines.extend(["", "## Watch-Only Lanes"])
    for lane, info in report["watch_only_lanes"].items():
        lines.append(f"- **{lane}**")
        for key, value in info.items():
            lines.append(f"  - {key}: **{value}**")

    lines.extend(["", "## Theme Bridge Input Status"])
    if report["theme_bridge_input_status"]:
        for key, value in report["theme_bridge_input_status"].items():
            lines.append(f"- {key}: **{value}**")
    else:
        lines.append("- No theme bridge input status available.")

    lines.extend(["", "## Readiness Warnings"])
    if report["readiness_warnings"]:
        for warning in report["readiness_warnings"]:
            lines.append(f"- `{warning}`")
    else:
        lines.append("- No readiness warnings detected from available artifacts.")

    lines.extend([
        "",
        "## Safety",
        "- Observe-only readiness report.",
        "- Does not alter official scoring.",
        "- Does not create picks.",
        "- Does not enable paper or live trading.",
        "- No buy instructions.",
    ])
    return "\n".join(lines)


def write_outputs(report: dict, *, data_dir: Path = DATA_DIR) -> tuple[Path, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = data_readiness_json_path(report["date"], data_dir=data_dir)
    md_path = data_readiness_markdown_path(report["date"], data_dir=data_dir)

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_markdown(report) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    args = parser.parse_args(argv)

    report = build_data_readiness_report(date_str=args.date, data_dir=Path(args.data_dir))
    json_path, md_path = write_outputs(report, data_dir=Path(args.data_dir))

    print(f"[data-readiness] wrote {json_path}")
    print(f"[data-readiness] markdown {md_path}")
    print(f"[data-readiness] classification {report['no_pick_classification']}")
    print(f"[data-readiness] status {report['official_pick_readiness_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
