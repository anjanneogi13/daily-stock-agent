import json
import subprocess
import sys
from pathlib import Path

from scripts.dry_run_official_no_pick import build_no_pick_fixture, run_dry_run
from scripts.validate_daily_no_pick import validate_no_pick_report
from src.premarket_decision_contract import OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES


def test_build_no_pick_fixture_validates_all_allowed_causes():
    for cause in OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES:
        payload = build_no_pick_fixture(cause, "2026-05-09")
        assert payload["primary_no_pick_cause"] == cause
        assert payload["decision"] == "official_no_pick"
        assert payload["paper_trading_enabled"] is False
        assert payload["live_trading_enabled"] is False
        assert validate_no_pick_report(payload) == []


def test_run_dry_run_all_causes_writes_summary_and_artifacts(tmp_path):
    summary = run_dry_run(
        output_dir=tmp_path,
        date_str="2026-05-09",
        cause="all",
        keep=True,
    )

    assert summary["dry_run"] is True
    assert summary["validated_cause_count"] == len(OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES)
    assert summary["paper_trading_enabled"] is False
    assert summary["live_trading_enabled"] is False
    assert all(result["valid"] for result in summary["results"])

    summary_path = tmp_path / "dry_run_official_no_pick_2026-05-09.json"
    assert summary_path.exists()

    stored = json.loads(summary_path.read_text())
    assert stored["validated_cause_count"] == len(OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES)


def test_dry_run_no_pick_cli_passes_for_all_causes(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts/dry_run_official_no_pick.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--date",
            "2026-05-09",
            "--output-dir",
            str(tmp_path),
            "--cause",
            "all",
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    assert "Lane 1 official no-pick dry-run passed" in result.stdout
    assert "paper_trading_enabled: false" in result.stdout
    assert "live_trading_enabled: false" in result.stdout
    assert list(tmp_path.glob("*/daily_picks_no_pick_report_2026-05-09.json"))
