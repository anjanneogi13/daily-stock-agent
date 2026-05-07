from pathlib import Path


def test_main_fails_loudly_when_zero_official_picks_after_filtering():
    text = Path("main.py").read_text()

    assert "if not top:" in text
    assert "No official picks generated after scoring/filtering" in text
    assert "not safe to treat as a successful daily-picks run" in text


def test_daily_picks_workflow_grep_count_cannot_emit_double_zero():
    text = Path(".github/workflows/daily-picks.yml").read_text()

    assert 'grep -c "^$ET_DATE" data/picks_log.csv 2>/dev/null || echo 0' not in text
    assert 'TODAY_ROWS=$(grep -c "^$ET_DATE" data/picks_log.csv 2>/dev/null || true)' in text
    assert 'TODAY_ROWS="${TODAY_ROWS:-0}"' in text


def test_daily_picks_workflow_does_not_stage_picks_log_on_zero_pick_failure():
    text = Path(".github/workflows/daily-picks.yml").read_text()

    assert "No picks_log.csv rows for $ET_DATE; not staging picks_log.csv" in text
    assert 'if [ "$TODAY_ROWS" -gt 0 ]; then' in text
    assert "git add -f data/picks_log.csv" in text
