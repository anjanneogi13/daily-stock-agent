import json

from scripts.write_official_workflow_summary import build_summary


def test_build_summary_includes_dry_runs_and_production_artifacts(tmp_path):
    data_dir = tmp_path / "data"
    pick_dry = tmp_path / "pick-dry"
    no_pick_dry = tmp_path / "no-pick-dry"
    data_dir.mkdir()
    pick_dry.mkdir()
    no_pick_dry.mkdir()

    (pick_dry / "dry_run_official_premarket_pick_2026-05-09.json").write_text(json.dumps({
        "dry_run": True,
        "ticker": "DRYRUN",
        "official_pick_artifact": str(pick_dry / "premarket_official_pick_2026-05-09_DRYRUN.json"),
        "contract_validation_errors": [],
        "artifact_validation_errors": [],
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
    }))

    (no_pick_dry / "dry_run_official_no_pick_2026-05-09.json").write_text(json.dumps({
        "dry_run": True,
        "validated_cause_count": 11,
        "allowed_cause_count": 11,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "results": [
            {
                "cause": "NO_PICK_DATA_READINESS_FAILED",
                "valid": True,
                "path": str(no_pick_dry / "NO_PICK_DATA_READINESS_FAILED/daily_picks_no_pick_report_2026-05-09.json"),
            }
        ],
    }))

    (data_dir / "premarket_official_pick_summary_2026-05-09.json").write_text(json.dumps({
        "official_pick_count": 1,
        "contract_version": "premarket_decision_contract_v1",
    }))
    (data_dir / "premarket_official_pick_2026-05-09_AAPL.json").write_text(json.dumps({
        "ticker": "AAPL",
        "score": 0.8,
        "entry": 100,
        "stop_loss": 95,
        "take_profit": 110,
        "quantity": 10,
    }))
    (data_dir / "daily_picks_candidate_diagnostics_2026-05-09.json").write_text(json.dumps({
        "diagnostics": {
            "stage_counts": {
                "selected_pick_count": 1,
            }
        }
    }))

    summary = build_summary(
        date_str="2026-05-09",
        data_dir=data_dir,
        pick_dry_run_dir=pick_dry,
        no_pick_dry_run_dir=no_pick_dry,
    )

    assert "# Lane 1 Official Decision Observability" in summary
    assert "Synthetic Official Pick Dry-Run" in summary
    assert "Synthetic Official No-Pick Dry-Run" in summary
    assert "Production Official Pick Artifacts" in summary
    assert "AAPL" in summary
    assert "NO_PICK_DATA_READINESS_FAILED" in summary
    assert "paper trading disabled; live trading disabled" in summary


def test_build_summary_handles_missing_artifacts(tmp_path):
    summary = build_summary(
        date_str="2026-05-09",
        data_dir=tmp_path / "missing-data",
        pick_dry_run_dir=tmp_path / "missing-pick-dry",
        no_pick_dry_run_dir=tmp_path / "missing-no-pick-dry",
    )

    assert "Dry-run summary not found." in summary
    assert "No production official pick artifacts found." in summary
    assert "No production official no-pick artifact found." in summary

def test_build_summary_includes_github_observability_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_SERVER_URL", "https://github.com")
    monkeypatch.setenv("GITHUB_REPOSITORY", "anjanneogi13/daily-stock-agent")
    monkeypatch.setenv("GITHUB_RUN_ID", "987654")
    monkeypatch.setenv("GITHUB_SHA", "abcdef1234567890")

    summary = build_summary(
        date_str="2026-05-09",
        data_dir=tmp_path / "missing-data",
        pick_dry_run_dir=tmp_path / "missing-pick-dry",
        no_pick_dry_run_dir=tmp_path / "missing-no-pick-dry",
    )

    assert "Workflow run: https://github.com/anjanneogi13/daily-stock-agent/actions/runs/987654" in summary
    assert "Commit: https://github.com/anjanneogi13/daily-stock-agent/commit/abcdef1234567890" in summary
    assert "Official artifact bundle: `official-decision-artifacts-987654`" in summary
