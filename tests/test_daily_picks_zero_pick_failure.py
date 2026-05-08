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

def test_main_writes_no_pick_evidence_report_before_zero_pick_failure():
    text = Path("main.py").read_text()

    assert "def _write_daily_picks_no_pick_report" in text
    assert "daily_picks_no_pick_report_" in text
    assert "pipeline[\"final_pick_count\"] = len(top)" in text
    assert "_write_daily_picks_no_pick_report(reason, pipeline, diagnostics)" in text
    assert "data-provider/rate-limit/no-candidate" in text


def test_main_includes_market_data_health_in_no_pick_report():
    text = Path("main.py").read_text()

    assert "market_data_health" in text
    assert "summarize_market_data_health" in text
    assert "write_market_data_run_summary" in text


def test_main_limits_scoring_workers_to_reduce_provider_rate_limits():
    text = Path("main.py").read_text()

    assert "DAILY_SCORER_WORKERS" in text
    assert 'os.getenv("DAILY_SCORER_WORKERS", "4")' in text
    assert "max_workers=scorer_workers" in text

def test_daily_picks_workflow_commits_market_data_health_artifacts():
    text = Path(".github/workflows/daily-picks.yml").read_text()

    assert "data/market_data_health_*.json" in text
    assert text.count("data/market_data_health_*.json") >= 2


def test_daily_picks_failure_recovery_commits_market_health_and_hard_block_evidence():
    text = Path(".github/workflows/daily-picks.yml").read_text()

    post_send = text.split("- name: Commit post-send artifacts", 1)[1]

    assert "data/market_data_health_*.json" in post_send
    assert "data/hard_blocks_log.json" in post_send
    assert "data/daily_picks_no_pick_report_*.json" in post_send
    assert "data/daily_picks_no_pick_report_*.md" in post_send
    assert "data/daily_picks_candidate_rejections_*.json" in post_send
    assert "data/daily_picks_candidate_rejections_*.md" in post_send
