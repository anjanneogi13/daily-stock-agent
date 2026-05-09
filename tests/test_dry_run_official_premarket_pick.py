import json
import subprocess
import sys
from pathlib import Path

from scripts.dry_run_official_premarket_pick import run_dry_run
from src.premarket_decision_contract import validate_official_pick


def test_run_dry_run_creates_valid_official_pick_artifact(tmp_path):
    result = run_dry_run(
        output_dir=tmp_path,
        date_str="2026-05-09",
        keep=True,
        ticker="DRYRUN",
    )

    assert result["dry_run"] is True
    assert result["artifact_summary"]["official_pick_count"] == 1
    assert result["artifact_validation_errors"] == []
    assert result["contract_validation_errors"] == []
    assert result["paper_trading_enabled"] is False
    assert result["live_trading_enabled"] is False

    artifact_path = Path(result["official_pick_artifact"])
    payload = json.loads(artifact_path.read_text())

    assert payload["ticker"] == "DRYRUN"
    assert payload["decision"] == "official_pick"
    assert validate_official_pick(payload) == []


def test_dry_run_cli_passes_with_output_dir(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts/dry_run_official_premarket_pick.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--date",
            "2026-05-09",
            "--output-dir",
            str(tmp_path),
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    assert "Lane 1 official premarket dry-run passed" in result.stdout
    assert "paper_trading_enabled: false" in result.stdout
    assert list(tmp_path.glob("premarket_official_pick_2026-05-09_*.json"))
    assert list(tmp_path.glob("dry_run_official_premarket_pick_2026-05-09.json"))
