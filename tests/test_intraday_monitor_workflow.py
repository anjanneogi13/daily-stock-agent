from pathlib import Path


WF = Path(".github/workflows/intraday_monitor.yml")


def _text():
    return WF.read_text()


def test_intraday_monitor_commits_opening_range_run_status():
    text = _text()

    assert "data/opening_range_run_status_*.jsonl" in text
    assert "data/opening_range_observations_*.jsonl" in text
