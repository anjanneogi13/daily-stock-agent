#!/usr/bin/env python3
"""Lane 1 production-readiness audit gate.

This is a local/static + synthetic audit for the official premarket decision
lane. It does not call providers, LLMs, Telegram, or GitHub APIs.

Audit coverage:
- official decision contract shape,
- official pick dry-run,
- official no-pick dry-run covering all allowed causes,
- artifact validators,
- workflow wiring,
- user-facing output artifact consumption,
- explicit no paper/live trading safety flags.

Safety:
- reporting/audit only,
- no real picks,
- no provider calls,
- no alerts,
- no paper/live trading.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.dry_run_official_no_pick import run_dry_run as run_no_pick_dry_run
from scripts.dry_run_official_premarket_pick import run_dry_run as run_pick_dry_run
from src.premarket_decision_contract import (
    DECISION_OFFICIAL_NO_PICK,
    DECISION_OFFICIAL_PICK,
    OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES,
    OFFICIAL_NO_PICK_REQUIRED_FIELDS,
    OFFICIAL_PICK_REQUIRED_FIELDS,
    SAFETY_FLAGS,
    STRATEGY_LANE,
    contract_summary,
)


ET = ZoneInfo("America/New_York")


def _default_date() -> str:
    return datetime.now(ET).strftime("%Y-%m-%d")


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _check(condition: bool, name: str, detail: str, checks: list[dict]) -> None:
    checks.append({
        "name": name,
        "passed": bool(condition),
        "detail": detail,
    })


def _required_file_checks(checks: list[dict]) -> None:
    required_paths = [
        "src/premarket_decision_contract.py",
        "src/official_pick_artifact.py",
        "src/official_artifact_loader.py",
        "scripts/validate_daily_no_pick.py",
        "scripts/validate_official_pick_artifacts.py",
        "scripts/dry_run_official_premarket_pick.py",
        "scripts/dry_run_official_no_pick.py",
        "scripts/write_official_workflow_summary.py",
        "tests/test_premarket_decision_contract.py",
        "tests/test_official_pick_artifact.py",
        "tests/test_validate_official_pick_artifacts.py",
        "tests/test_dry_run_official_premarket_pick.py",
        "tests/test_dry_run_official_no_pick.py",
        "tests/test_write_official_workflow_summary.py",
        ".github/workflows/daily-picks.yml",
    ]
    for rel in required_paths:
        _check(Path(rel).exists(), f"required file exists: {rel}", rel, checks)


def _contract_checks(checks: list[dict]) -> None:
    summary = contract_summary()

    _check(
        summary.get("strategy_lane") == STRATEGY_LANE,
        "contract strategy lane is explicit",
        f"strategy_lane={summary.get('strategy_lane')}",
        checks,
    )
    _check(
        DECISION_OFFICIAL_PICK in summary.get("valid_decisions", []),
        "contract includes official pick decision",
        DECISION_OFFICIAL_PICK,
        checks,
    )
    _check(
        DECISION_OFFICIAL_NO_PICK in summary.get("valid_decisions", []),
        "contract includes official no-pick decision",
        DECISION_OFFICIAL_NO_PICK,
        checks,
    )
    _check(
        len(OFFICIAL_PICK_REQUIRED_FIELDS) >= 25,
        "official pick required fields are comprehensive",
        f"count={len(OFFICIAL_PICK_REQUIRED_FIELDS)}",
        checks,
    )
    _check(
        len(OFFICIAL_NO_PICK_REQUIRED_FIELDS) >= 20,
        "official no-pick required fields are comprehensive",
        f"count={len(OFFICIAL_NO_PICK_REQUIRED_FIELDS)}",
        checks,
    )
    _check(
        len(OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES) >= 10,
        "official no-pick cause taxonomy is populated",
        f"count={len(OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES)}",
        checks,
    )
    _check(
        set(SAFETY_FLAGS) == {"paper_trading_enabled", "live_trading_enabled"},
        "contract exposes paper/live trading safety flags",
        f"safety_flags={sorted(SAFETY_FLAGS)}",
        checks,
    )
    _check(
        summary.get("paper_trading_enabled") is False and summary.get("live_trading_enabled") is False,
        "contract summary keeps trading disabled",
        f"paper={summary.get('paper_trading_enabled')} live={summary.get('live_trading_enabled')}",
        checks,
    )


def _dry_run_checks(date_str: str, output_dir: Path, checks: list[dict]) -> dict:
    pick_dir = output_dir / "official_pick"
    no_pick_dir = output_dir / "official_no_pick"

    pick_result = run_pick_dry_run(
        output_dir=pick_dir,
        date_str=date_str,
        keep=True,
        ticker="DRYRUN",
    )
    _check(
        pick_result.get("artifact_summary", {}).get("official_pick_count") == 1,
        "synthetic official pick dry-run produces one valid artifact",
        str(pick_result.get("official_pick_artifact")),
        checks,
    )
    _check(
        pick_result.get("contract_validation_errors") == [],
        "synthetic official pick dry-run contract validation passes",
        str(pick_result.get("contract_validation_errors")),
        checks,
    )
    _check(
        pick_result.get("artifact_validation_errors") == [],
        "synthetic official pick dry-run artifact validation passes",
        str(pick_result.get("artifact_validation_errors")),
        checks,
    )
    _check(
        pick_result.get("paper_trading_enabled") is False and pick_result.get("live_trading_enabled") is False,
        "synthetic official pick dry-run keeps trading disabled",
        f"paper={pick_result.get('paper_trading_enabled')} live={pick_result.get('live_trading_enabled')}",
        checks,
    )

    no_pick_result = run_no_pick_dry_run(
        output_dir=no_pick_dir,
        date_str=date_str,
        cause="all",
        keep=True,
    )
    _check(
        no_pick_result.get("validated_cause_count") == len(OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES),
        "synthetic no-pick dry-run validates all allowed causes",
        f"validated={no_pick_result.get('validated_cause_count')} allowed={len(OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES)}",
        checks,
    )
    _check(
        all(item.get("valid") for item in no_pick_result.get("results", [])),
        "synthetic no-pick fixtures are all valid",
        f"results={len(no_pick_result.get('results', []))}",
        checks,
    )
    _check(
        no_pick_result.get("paper_trading_enabled") is False and no_pick_result.get("live_trading_enabled") is False,
        "synthetic no-pick dry-run keeps trading disabled",
        f"paper={no_pick_result.get('paper_trading_enabled')} live={no_pick_result.get('live_trading_enabled')}",
        checks,
    )

    return {
        "pick_dry_run": pick_result,
        "no_pick_dry_run": no_pick_result,
    }


def _workflow_checks(checks: list[dict]) -> None:
    workflow = _read(Path(".github/workflows/daily-picks.yml"))

    expected_snippets = [
        "dry_run_official_premarket_pick.py",
        "dry_run_official_no_pick.py",
        "validate_official_pick_artifacts.py",
        "validate_daily_no_pick.py",
        "write_official_workflow_summary.py",
        "actions/upload-artifact@v4",
        "official-dry-run-artifacts",
        "official-decision-artifacts",
        "GITHUB_STEP_SUMMARY",
        "premarket_official_pick_*.json",
        "premarket_official_pick_summary_*.json",
        "daily_picks_no_pick_report_*.json",
        "daily_picks_candidate_diagnostics_*.json",
        "daily_picks_candidate_rejections_*.json",
    ]

    for snippet in expected_snippets:
        _check(
            snippet in workflow,
            f"workflow contains {snippet}",
            snippet,
            checks,
        )


def _user_output_checks(checks: list[dict]) -> None:
    email = _read(Path("scripts/format_picks_email.py"))
    telegram = _read(Path("scripts/send_layman_daily.py"))

    _check(
        "official_artifact_loader" in email,
        "GitHub issue formatter consumes official artifacts",
        "scripts/format_picks_email.py",
        checks,
    )
    _check(
        "Official Decision Artifacts" in email,
        "GitHub issue formatter displays official artifact section",
        "scripts/format_picks_email.py",
        checks,
    )
    _check(
        "official_artifact_loader" in telegram,
        "Telegram sender consumes official artifacts",
        "scripts/send_layman_daily.py",
        checks,
    )
    _check(
        "official_selection_reason" in telegram,
        "Telegram sender displays official reason",
        "scripts/send_layman_daily.py",
        checks,
    )
    _check(
        "official_risk_flags" in telegram,
        "Telegram sender displays official risk flags",
        "scripts/send_layman_daily.py",
        checks,
    )


def _safety_scan_checks(checks: list[dict]) -> None:
    files = [
        Path("src/premarket_decision_contract.py"),
        Path("src/official_pick_artifact.py"),
        Path("scripts/dry_run_official_premarket_pick.py"),
        Path("scripts/dry_run_official_no_pick.py"),
        Path("scripts/write_official_workflow_summary.py"),
    ]

    suspicious = []
    for path in files:
        text = _read(path)
        for bad in (
            '"paper_trading_enabled": True',
            "'paper_trading_enabled': True",
            '"live_trading_enabled": True',
            "'live_trading_enabled': True",
        ):
            if bad in text:
                suspicious.append(f"{path}:{bad}")

    _check(
        not suspicious,
        "official Lane 1 files do not enable paper/live trading",
        ", ".join(suspicious) if suspicious else "no enabled trading flags found",
        checks,
    )


def _write_audit_files(result: dict, output_dir: Path, date_str: str) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / f"lane1_production_readiness_audit_{date_str}.json"
    md_path = output_dir / f"lane1_production_readiness_audit_{date_str}.md"

    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Lane 1 Production Readiness Audit",
        "",
        f"- Date: **{date_str}**",
        f"- Status: **{'passed' if result['passed'] else 'failed'}**",
        f"- Passed checks: **{result['passed_check_count']} / {result['check_count']}**",
        "- Paper trading enabled: **false**",
        "- Live trading enabled: **false**",
        "",
        "## Checks",
        "",
        "| Status | Check | Detail |",
        "|---|---|---|",
    ]

    for check in result["checks"]:
        status = "✅" if check["passed"] else "❌"
        detail = str(check["detail"]).replace("|", "\\|")
        lines.append(f"| {status} | {check['name']} | {detail} |")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def run_audit(*, date_str: str, output_dir: Path, keep: bool = True) -> dict:
    checks: list[dict] = []

    _required_file_checks(checks)
    _contract_checks(checks)
    dry_run_results = _dry_run_checks(date_str, output_dir / "dry_runs", checks)
    _workflow_checks(checks)
    _user_output_checks(checks)
    _safety_scan_checks(checks)

    passed_count = sum(1 for check in checks if check["passed"])
    result = {
        "artifact": "lane1_production_readiness_audit",
        "date": date_str,
        "passed": passed_count == len(checks),
        "check_count": len(checks),
        "passed_check_count": passed_count,
        "failed_check_count": len(checks) - passed_count,
        "checks": checks,
        "dry_run_results": dry_run_results,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "kept_output": keep,
    }

    json_path, md_path = _write_audit_files(result, output_dir, date_str)
    result["json_path"] = str(json_path)
    result["markdown_path"] = str(md_path)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=_default_date())
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args()

    temp_dir = None
    if args.output_dir:
        output_dir = Path(args.output_dir)
        keep = True
    else:
        temp_dir = tempfile.mkdtemp(prefix="lane1-production-readiness-audit-")
        output_dir = Path(temp_dir)
        keep = args.keep

    try:
        result = run_audit(date_str=args.date, output_dir=output_dir, keep=keep)
        if result["passed"]:
            print("✅ Lane 1 production-readiness audit passed")
        else:
            print("❌ Lane 1 production-readiness audit failed")
        print(f"- date: {result['date']}")
        print(f"- output_dir: {output_dir}")
        print(f"- passed checks: {result['passed_check_count']}/{result['check_count']}")
        print(f"- audit_json: {result['json_path']}")
        print(f"- audit_markdown: {result['markdown_path']}")
        print("- paper_trading_enabled: false")
        print("- live_trading_enabled: false")

        if not result["passed"]:
            print("\nFailed checks:")
            for check in result["checks"]:
                if not check["passed"]:
                    print(f"- {check['name']}: {check['detail']}")
            return 1

        return 0
    finally:
        if temp_dir and not keep:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
