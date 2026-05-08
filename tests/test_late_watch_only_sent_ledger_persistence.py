from pathlib import Path


def test_daily_picks_missed_window_commits_late_ideas_sent_ledger():
    text = Path(".github/workflows/daily-picks.yml").read_text()

    assert "data/late_daily_ideas_sent_*.json" in text
    assert "data/late_daily_ideas_*.jsonl" in text
    assert "data/late_daily_ideas_*.md" in text


def test_independent_late_watch_only_commits_late_ideas_sent_ledger():
    text = Path(".github/workflows/late_watch_only.yml").read_text()

    assert "data/late_daily_ideas_sent_*.json" in text
    assert "data/late_daily_ideas_*.jsonl" in text
    assert "data/late_daily_ideas_*.md" in text
