from pathlib import Path

BLUEPRINT = Path("docs/PROJECT_BLUEPRINT.md")
WORK_LOG = Path("docs/WORK_LOG.md")
TODO_STUB = Path("docs/TODO_BUGS.md")


def test_todo_bugs_is_now_a_compatibility_stub():
    text = TODO_STUB.read_text()

    assert "PROJECT_BLUEPRINT.md" in text
    assert "WORK_LOG.md" in text
    assert "NEXT_SESSION.md" in text
    assert "Historical copy" in text


def test_work_log_preserves_recent_fix_history():
    text = WORK_LOG.read_text()

    assert "Documentation consolidation" in text
    assert "Daily picks persistence hardening" in text
    assert "Telegram delivery reliability" in text
    assert "Tiered exits reserved schema" in text
    assert "Hard blocks coverage" in text
    assert "Earnings analyzer coverage" in text
    assert "Market news coverage" in text
    assert "LLM agent coverage" in text


def test_project_blueprint_preserves_current_known_gaps():
    text = BLUEPRINT.read_text()

    assert "Current Known Gaps" in text
    assert "data/picks_log.csv" in text
    assert "data/signal_journal.jsonl" in text
    assert "performance_stats" in text
    assert "paper_trader" in text
    assert "picks_csv" in text
    assert "monster_data" in text
    assert "cape_ratio" in text


def test_project_blueprint_preserves_monitoring_policy():
    text = BLUEPRINT.read_text()

    assert "monitoring-only" in text
    assert "Paper trading stays blocked" in text
    assert ">60%" in text
    assert ">66%" in text
    assert ">90%" in text
    assert "positive expectancy" in text


def test_project_blueprint_preserves_data_quality_history_summary():
    text = BLUEPRINT.read_text()

    assert "Data-quality audits" in text or "Data-quality" in text
    assert "Core data-quality audits are green" in text
    assert "full_repo_audit.py" in text
