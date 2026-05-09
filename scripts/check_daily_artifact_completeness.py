#!/usr/bin/env python3
"""Daily Diagnostic Artifact Completeness Check v0 — observe-only.

Builds a present/missing matrix for daily diagnostic artifacts so missing files
are visible and not silently interpreted as success.

Outputs:
- data/artifact_completeness_YYYY-MM-DD.json
- data/artifact_completeness_YYYY-MM-DD.md
"""

from __future__ import annotations

import argparse
import csv
import json
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


ARTIFACTS = [
    {
        "key": "daily_run_status",
        "template": "daily_picks_run_status_{date}.jsonl",
        "kind": "jsonl",
        "level": "critical",
        "description": "Daily official pick pipeline run-status rows.",
    },
    {
        "key": "no_pick_report",
        "template": "daily_picks_no_pick_report_{date}.json",
        "kind": "json",
        "level": "conditional_no_pick",
        "description": "Required when no official picks were produced.",
    },
    {
        "key": "candidate_rejections",
        "template": "daily_picks_candidate_rejections_{date}.json",
        "kind": "json",
        "level": "critical",
        "description": "Candidate diagnostics and rejection/hard-block evidence.",
    },
    {
        "key": "data_readiness",
        "template": "data_readiness_{date}.json",
        "kind": "json",
        "level": "critical",
        "description": "Daily data readiness classification.",
    },
    {
        "key": "candidate_lifecycle",
        "template": "candidate_lifecycle_{date}.json",
        "kind": "json",
        "level": "critical",
        "description": "Candidate/theme leader lifecycle reconstruction.",
    },
    {
        "key": "theme_discovery",
        "template": "theme_discovery_{date}.json",
        "kind": "json",
        "level": "observe_only",
        "description": "Observe-only dynamic theme discovery.",
    },
    {
        "key": "theme_pick_bridge",
        "template": "theme_pick_bridge_{date}.json",
        "kind": "json",
        "level": "observe_only",
        "description": "Observe-only theme-to-pick bridge.",
    },
    {
        "key": "late_daily_ideas",
        "template": "late_daily_ideas_{date}.jsonl",
        "kind": "jsonl",
        "level": "watch_only",
        "description": "Late daily watch-only ideas.",
    },
    {
        "key": "opening_range_observations",
        "template": "opening_range_observations_{date}.jsonl",
        "kind": "jsonl",
        "level": "watch_only",
        "description": "Opening-range watch-only observations.",
    },
    {
        "key": "intraday_momentum_observations",
        "template": "intraday_momentum_observations_{date}.jsonl",
        "kind": "jsonl",
        "level": "watch_only",
        "description": "Intraday momentum watch-only observations.",
    },
]


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        return {"_parse_error": str(exc), "_path": str(path)}


def inspect_jsonl(path: Path) -> dict:
    rows = 0
    parse_errors = 0
    if not path.exists():
        return {"row_count": 0, "parse_errors": 0}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            json.loads(line)
            rows += 1
        except Exception:
            parse_errors += 1
    return {"row_count": rows, "parse_errors": parse_errors}


def inspect_json(path: Path) -> dict:
    if not path.exists():
        return {"parse_error": False, "top_level_keys": []}
    obj = load_json(path, {})
    return {
        "parse_error": isinstance(obj, dict) and "_parse_error" in obj,
        "top_level_keys": list(obj.keys())[:20] if isinstance(obj, dict) else [],
    }


def _date_prefix(value: Any) -> str:
    return str(value or "")[:10]


def official_pick_count(data_dir: Path, date_str: str) -> int:
    readiness = load_json(data_dir / f"data_readiness_{date_str}.json", {})
    if isinstance(readiness, dict) and "official_pick_count" in readiness:
        try:
            return int(readiness.get("official_pick_count") or 0)
        except Exception:
            pass

    path = data_dir / "picks_log.csv"
    if not path.exists():
        return 0

    count = 0
    try:
        with path.open(newline="") as f:
            for row in csv.DictReader(f):
                if _date_prefix(row.get("pick_date")) == date_str:
                    count += 1
    except Exception:
        return 0
    return count


def should_be_required(level: str, *, pick_count: int) -> bool:
    if level == "critical":
        return True
    if level == "conditional_no_pick":
        return pick_count == 0
    return False


def build_artifact_completeness_report(
    *,
    date_str: str,
    data_dir: Path = DATA_DIR,
) -> dict:
    pick_count = official_pick_count(data_dir, date_str)

    checks = []
    for spec in ARTIFACTS:
        path = data_dir / spec["template"].format(date=date_str)
        exists = path.exists()
        required = should_be_required(spec["level"], pick_count=pick_count)

        extra = inspect_jsonl(path) if spec["kind"] == "jsonl" else inspect_json(path)

        present_status = "present" if exists else "missing"
        if exists and spec["kind"] == "jsonl" and extra.get("row_count", 0) == 0:
            present_status = "present_empty"
        if exists and (
            extra.get("parse_errors", 0) if spec["kind"] == "jsonl" else extra.get("parse_error")
        ):
            present_status = "present_parse_error"

        if not exists and required:
            severity = "critical"
        elif not exists:
            severity = "warning"
        elif present_status == "present_parse_error":
            severity = "critical" if required else "warning"
        elif present_status == "present_empty":
            severity = "warning"
        else:
            severity = "ok"

        checks.append({
            "key": spec["key"],
            "path": str(path),
            "kind": spec["kind"],
            "level": spec["level"],
            "required": required,
            "exists": exists,
            "status": present_status,
            "severity": severity,
            "description": spec["description"],
            **extra,
        })

    missing_critical = [c["key"] for c in checks if c["severity"] == "critical"]
    warnings = [c["key"] for c in checks if c["severity"] == "warning"]
    present = [c["key"] for c in checks if c["exists"]]
    missing = [c["key"] for c in checks if not c["exists"]]

    if missing_critical:
        completeness_status = "missing_critical_artifacts"
    elif warnings:
        completeness_status = "missing_or_empty_noncritical_artifacts"
    else:
        completeness_status = "complete"

    return {
        "artifact": "artifact_completeness",
        "date": date_str,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **SAFETY,
        "completeness_status": completeness_status,
        "official_pick_count": pick_count,
        "summary": {
            "artifact_count": len(checks),
            "present_count": len(present),
            "missing_count": len(missing),
            "missing_critical_count": len(missing_critical),
            "warning_count": len(warnings),
            "present": present,
            "missing": missing,
            "missing_critical": missing_critical,
            "warnings": warnings,
        },
        "checks": checks,
        "safety_flags": [
            "observe_only",
            "not_official_scoring",
            "no_production_scoring_effect",
            "not_paper_trade",
            "not_live_trade",
            "no_buy_instructions",
        ],
    }


def artifact_completeness_json_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"artifact_completeness_{date_str}.json"


def artifact_completeness_markdown_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"artifact_completeness_{date_str}.md"


def format_markdown(report: dict) -> str:
    lines = [
        "# Daily Artifact Completeness Report",
        "",
        "Observe-only. This report does not alter scoring or create picks.",
        "",
        f"- Date: **{report['date']}**",
        f"- Completeness status: **{report['completeness_status']}**",
        f"- Official pick count: **{report['official_pick_count']}**",
        f"- Present artifacts: **{report['summary']['present_count']}**",
        f"- Missing artifacts: **{report['summary']['missing_count']}**",
        f"- Missing critical artifacts: **{report['summary']['missing_critical_count']}**",
        f"- Warnings: **{report['summary']['warning_count']}**",
        "",
        "## Missing Critical Artifacts",
    ]

    if report["summary"]["missing_critical"]:
        for key in report["summary"]["missing_critical"]:
            lines.append(f"- `{key}`")
    else:
        lines.append("- None")

    lines.extend(["", "## Warning Artifacts"])
    if report["summary"]["warnings"]:
        for key in report["summary"]["warnings"]:
            lines.append(f"- `{key}`")
    else:
        lines.append("- None")

    lines.extend(["", "## Artifact Matrix"])
    for c in report["checks"]:
        lines.append(
            f"- **{c['key']}** — `{c['status']}` / severity=`{c['severity']}` / required=`{c['required']}`"
        )
        lines.append(f"  - Path: `{c['path']}`")
        lines.append(f"  - Level: `{c['level']}`")
        if c["kind"] == "jsonl":
            lines.append(f"  - Rows: **{c.get('row_count', 0)}**")
            lines.append(f"  - Parse errors: **{c.get('parse_errors', 0)}**")
        else:
            lines.append(f"  - Parse error: **{c.get('parse_error', False)}**")

    lines.extend([
        "",
        "## Safety",
        "- Observe-only artifact completeness report.",
        "- Does not alter official scoring.",
        "- Does not create picks.",
        "- Does not enable paper or live trading.",
        "- No buy instructions.",
    ])
    return "\n".join(lines)


def write_outputs(report: dict, *, data_dir: Path = DATA_DIR) -> tuple[Path, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    json_path = artifact_completeness_json_path(report["date"], data_dir=data_dir)
    md_path = artifact_completeness_markdown_path(report["date"], data_dir=data_dir)

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_markdown(report) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    args = parser.parse_args(argv)

    report = build_artifact_completeness_report(date_str=args.date, data_dir=Path(args.data_dir))
    json_path, md_path = write_outputs(report, data_dir=Path(args.data_dir))

    print(f"[artifact-completeness] wrote {json_path}")
    print(f"[artifact-completeness] markdown {md_path}")
    print(f"[artifact-completeness] status {report['completeness_status']}")
    print(f"[artifact-completeness] missing critical {report['summary']['missing_critical']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
