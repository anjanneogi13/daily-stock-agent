from pathlib import Path


WF = Path(".github/workflows/intraday_monitor.yml")


def _text():
    return WF.read_text()


def test_intraday_monitor_commits_opening_range_run_status():
    text = _text()

    assert "data/opening_range_run_status_*.jsonl" in text
    assert "data/opening_range_observations_*.jsonl" in text


def test_intraday_monitor_force_adds_ignored_runtime_artifacts():
    text = _text()

    assert "git add -f data/intraday_alerts_*.json" in text
    assert "git add -f data/opening_range_observations_*.jsonl" in text
    assert "git add -f data/opening_range_run_status_*.jsonl" in text


def test_intraday_telegram_sender_runs_from_actions_script_path(tmp_path):
    """Regression: sender imports intraday_scanner, which imports src.*.

    GitHub Actions runs `python scripts/send_intraday_telegram.py`; the sender
    must add repo root to sys.path before importing intraday_scanner.
    """
    import os
    import subprocess
    import sys
    from pathlib import Path

    repo = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env.pop("TELEGRAM_BOT_TOKEN", None)
    env.pop("TELEGRAM_CHAT_ID", None)
    env.pop("TELEGRAM_GROUP_CHAT_ID", None)

    result = subprocess.run(
        [sys.executable, str(repo / "scripts/send_intraday_telegram.py")],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0
    assert "Missing creds" in result.stdout
    assert list((tmp_path / "data").glob("opening_range_run_status_*.jsonl"))
