import json
import subprocess
import sys
from pathlib import Path

from scripts.audit_lane1_production_readiness import run_audit


def test_run_audit_passes_and_writes_artifacts(tmp_path):
    result = run_audit(
        date_str="2026-05-09",
        output_dir=tmp_path,
        keep=True,
    )

    assert result["passed"] is True
    assert result["failed_check_count"] == 0
    assert result["paper_trading_enabled"] is False
    assert result["live_trading_enabled"] is False

    json_path = Path(result["json_path"])
    md_path = Path(result["markdown_path"])

    assert json_path.exists()
    assert md_path.exists()

    stored = json.loads(json_path.read_text())
    assert stored["passed"] is True
    assert stored["check_count"] == result["check_count"]
    assert "Lane 1 Production Readiness Audit" in md_path.read_text()


def test_audit_cli_passes_with_output_dir(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts/audit_lane1_production_readiness.py"

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

    assert "Lane 1 production-readiness audit passed" in result.stdout
    assert "paper_trading_enabled: false" in result.stdout
    assert "live_trading_enabled: false" in result.stdout
    assert list(tmp_path.glob("lane1_production_readiness_audit_2026-05-09.json"))
    assert list(tmp_path.glob("lane1_production_readiness_audit_2026-05-09.md"))
