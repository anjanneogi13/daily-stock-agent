from pathlib import Path


def test_intraday_workflow_commits_opening_range_observations():
    workflow = Path(".github/workflows/intraday_monitor.yml").read_text()

    assert "data/opening_range_observations_*.jsonl" in workflow
    assert "data/intraday_alerts_*.json" in workflow

def test_intraday_monitor_workflow_commits_opening_range_bar_artifacts():
    text = Path(".github/workflows/intraday_monitor.yml").read_text()

    assert "data/opening_range_bars" in text
    assert "find data/opening_range_bars -type f -name '*.jsonl'" in text
    assert "git add -f" in text
