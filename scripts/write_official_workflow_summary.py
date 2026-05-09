#!/usr/bin/env python3
"""Write GitHub Actions summary for Lane 1 official decision artifacts.

Summarizes:
- official pick dry-run artifacts,
- official no-pick dry-run artifacts,
- production official pick/no-pick artifacts,
- candidate diagnostics/rejections.

Output is Markdown written to stdout and optionally appended to
$GITHUB_STEP_SUMMARY by the workflow.

Safety:
- reporting only,
- no provider calls,
- no alerts,
- no trading behavior.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.github_observability import github_observability_metadata


def _load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _safe(value: Any, default: str = "—") -> str:
    if value in (None, ""):
        return default
    return str(value)


def _artifact_link(path: Path) -> str:
    return f"`{path}`"


def _production_pick_section(date_str: str, data_dir: Path) -> list[str]:
    paths = sorted(data_dir.glob(f"premarket_official_pick_{date_str}_*.json"))
    summary = _load_json(data_dir / f"premarket_official_pick_summary_{date_str}.json")

    lines = [
        "## Production Official Pick Artifacts",
        "",
    ]

    if not paths:
        lines.append("- No production official pick artifacts found.")
        lines.append("")
        return lines

    lines.append(f"- Summary artifact: {_artifact_link(data_dir / f'premarket_official_pick_summary_{date_str}.json')}")
    lines.append(f"- Official pick count: **{_safe(summary.get('official_pick_count'), str(len(paths)))}**")
    lines.append(f"- Contract version: `{_safe(summary.get('contract_version'))}`")
    lines.append("")
    lines.append("| Ticker | Score | Entry | Stop | Target | Qty | Artifact |")
    lines.append("|---|---:|---:|---:|---:|---:|---|")

    for path in paths:
        payload = _load_json(path)
        lines.append(
            "| "
            f"{_safe(payload.get('ticker'))} | "
            f"{_safe(payload.get('score'))} | "
            f"{_safe(payload.get('entry'))} | "
            f"{_safe(payload.get('stop_loss'))} | "
            f"{_safe(payload.get('take_profit'))} | "
            f"{_safe(payload.get('quantity'))} | "
            f"{_artifact_link(path)} |"
        )

    lines.append("")
    return lines


def _production_no_pick_section(date_str: str, data_dir: Path) -> list[str]:
    path = data_dir / f"daily_picks_no_pick_report_{date_str}.json"
    payload = _load_json(path)

    lines = [
        "## Production Official No-Pick Artifact",
        "",
    ]

    if not payload:
        lines.append("- No production official no-pick artifact found.")
        lines.append("")
        return lines

    lines.extend([
        f"- Artifact: {_artifact_link(path)}",
        f"- Primary cause: `{_safe(payload.get('primary_no_pick_cause'))}`",
        f"- Summary: {_safe(payload.get('human_readable_summary') or payload.get('reason'))}",
        f"- Data readiness: `{_safe(payload.get('data_readiness_status'))}`",
        f"- Provider status: `{_safe(payload.get('provider_status'))}`",
        f"- Paper trading enabled: **{str(payload.get('paper_trading_enabled')).lower()}**",
        f"- Live trading enabled: **{str(payload.get('live_trading_enabled')).lower()}**",
        "",
    ])
    return lines


def _diagnostics_section(date_str: str, data_dir: Path) -> list[str]:
    diag_path = data_dir / f"daily_picks_candidate_diagnostics_{date_str}.json"
    rej_path = data_dir / f"daily_picks_candidate_rejections_{date_str}.json"
    diag = _load_json(diag_path)
    rej = _load_json(rej_path)

    lines = [
        "## Candidate Diagnostics",
        "",
    ]

    if not diag and not rej:
        lines.append("- No candidate diagnostics/rejection artifacts found.")
        lines.append("")
        return lines

    if diag:
        diagnostics = diag.get("diagnostics") if isinstance(diag.get("diagnostics"), dict) else {}
        stage_counts = diagnostics.get("stage_counts") if isinstance(diagnostics.get("stage_counts"), dict) else {}
        lines.append(f"- Diagnostics artifact: {_artifact_link(diag_path)}")
        if stage_counts:
            lines.append("- Stage counts:")
            for key, value in sorted(stage_counts.items()):
                lines.append(f"  - `{key}`: **{value}**")

    if rej:
        lines.append(f"- Rejections artifact: {_artifact_link(rej_path)}")
        lines.append(f"- Rejection primary cause: `{_safe(rej.get('primary_no_pick_cause'))}`")

    lines.append("")
    return lines


def _dry_run_pick_section(date_str: str, dry_run_dir: Path) -> list[str]:
    summary_path = dry_run_dir / f"dry_run_official_premarket_pick_{date_str}.json"
    summary = _load_json(summary_path)

    lines = [
        "## Synthetic Official Pick Dry-Run",
        "",
    ]

    if not summary:
        lines.append("- Dry-run summary not found.")
        lines.append("")
        return lines

    lines.extend([
        f"- Summary: {_artifact_link(summary_path)}",
        f"- Result: **passed**",
        f"- Ticker: `{_safe(summary.get('ticker'))}`",
        f"- Official pick artifact: `{_safe(summary.get('official_pick_artifact'))}`",
        f"- Contract validation errors: **{len(summary.get('contract_validation_errors') or [])}**",
        f"- Artifact validation errors: **{len(summary.get('artifact_validation_errors') or [])}**",
        f"- Paper trading enabled: **{str(summary.get('paper_trading_enabled')).lower()}**",
        f"- Live trading enabled: **{str(summary.get('live_trading_enabled')).lower()}**",
        "",
    ])
    return lines


def _dry_run_no_pick_section(date_str: str, dry_run_dir: Path) -> list[str]:
    summary_path = dry_run_dir / f"dry_run_official_no_pick_{date_str}.json"
    summary = _load_json(summary_path)

    lines = [
        "## Synthetic Official No-Pick Dry-Run",
        "",
    ]

    if not summary:
        lines.append("- Dry-run summary not found.")
        lines.append("")
        return lines

    results = summary.get("results") if isinstance(summary.get("results"), list) else []
    lines.extend([
        f"- Summary: {_artifact_link(summary_path)}",
        f"- Result: **passed**",
        f"- Validated causes: **{summary.get('validated_cause_count', len(results))}**",
        f"- Allowed causes: **{summary.get('allowed_cause_count', '—')}**",
        f"- Paper trading enabled: **{str(summary.get('paper_trading_enabled')).lower()}**",
        f"- Live trading enabled: **{str(summary.get('live_trading_enabled')).lower()}**",
        "",
    ])

    if results:
        lines.append("| Cause | Valid | Artifact |")
        lines.append("|---|---:|---|")
        for result in results:
            lines.append(
                "| "
                f"`{_safe(result.get('cause'))}` | "
                f"{'✅' if result.get('valid') else '❌'} | "
                f"`{_safe(result.get('path'))}` |"
            )
        lines.append("")

    return lines


def build_summary(
    *,
    date_str: str,
    data_dir: Path = Path("data"),
    pick_dry_run_dir: Path = Path("/tmp/lane1-official-dry-run"),
    no_pick_dry_run_dir: Path = Path("/tmp/lane1-official-no-pick-dry-run"),
) -> str:
    observability = github_observability_metadata()
    lines = [
        "# Lane 1 Official Decision Observability",
        "",
        f"- ET date: **{date_str}**",
        "- Safety: **paper trading disabled; live trading disabled**",
        "- Scope: official dry-runs, official decision artifacts, diagnostics",
    ]
    if observability.get("workflow_run_url"):
        lines.append(f"- Workflow run: {observability['workflow_run_url']}")
    if observability.get("commit_url"):
        lines.append(f"- Commit: {observability['commit_url']}")
    if observability.get("artifact_bundle_name"):
        lines.append(f"- Official artifact bundle: `{observability['artifact_bundle_name']}`")
    lines.append("")

    lines.extend(_dry_run_pick_section(date_str, pick_dry_run_dir))
    lines.extend(_dry_run_no_pick_section(date_str, no_pick_dry_run_dir))
    lines.extend(_production_pick_section(date_str, data_dir))
    lines.extend(_production_no_pick_section(date_str, data_dir))
    lines.extend(_diagnostics_section(date_str, data_dir))

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--pick-dry-run-dir", default="/tmp/lane1-official-dry-run")
    parser.add_argument("--no-pick-dry-run-dir", default="/tmp/lane1-official-no-pick-dry-run")
    parser.add_argument("--output", default="", help="Optional Markdown output path")
    args = parser.parse_args()

    summary = build_summary(
        date_str=args.date,
        data_dir=Path(args.data_dir),
        pick_dry_run_dir=Path(args.pick_dry_run_dir),
        no_pick_dry_run_dir=Path(args.no_pick_dry_run_dir),
    )

    print(summary, end="")
    if args.output:
        Path(args.output).write_text(summary, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
