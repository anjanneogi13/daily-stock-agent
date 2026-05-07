from pathlib import Path

DECISION = Path("docs/decisions/2026-05-05-monitoring-first-no-paper-trading.md")
BLUEPRINT = Path("docs/PROJECT_BLUEPRINT.md")
WORK_LOG = Path("docs/WORK_LOG.md")
NEXT_SESSION = Path("docs/NEXT_SESSION.md")


def test_monitoring_first_decision_record_exists():
    assert DECISION.exists()
    text = DECISION.read_text()

    assert "Monitoring-first" in text
    assert "No real-money trading" in text
    assert "No paper trading integration yet" in text
    assert "2 weeks" in text
    assert "another 2 weeks" in text
    assert "day trades" in text
    assert ">60%" in text
    assert "swing trades" in text
    assert ">66%" in text
    assert "monster" in text
    assert ">90%" in text
    assert "positive expectancy" in text


def test_project_blueprint_is_canonical_current_state():
    text = BLUEPRINT.read_text()

    assert "monitoring-ready" in text
    assert "Test suite:" in text
    assert "1360 passed, 29 skipped" in text
    assert "monitoring-only" in text
    assert "must not execute real-money trades" in text
    assert "Paper trading stays blocked" in text
    assert "SMELL_ENFORCE" in text
    assert "BRAIN_ENFORCE_EV" in text
    assert "AUTO_PAUSE_ENABLED" in text


def test_project_blueprint_captures_architecture_and_roadmap():
    text = BLUEPRINT.read_text()

    assert "Core pipeline" in text
    assert "Brain / scoring" in text
    assert "Hearing / news" in text
    assert "Implemented Features" in text
    assert "Current Known Gaps" in text
    assert "Backtester hardening" in text
    assert "Curiosity engine" in text
    assert "Reader engine" in text
    assert "Historical regime engine" in text


def test_work_log_and_next_session_are_present():
    work = WORK_LOG.read_text()
    next_text = NEXT_SESSION.read_text()

    assert "Append-only history" in work
    assert "Documentation consolidation" in work
    assert "LLM agent coverage" in work
    assert "Market news coverage" in work
    assert "Hard blocks coverage" in work

    assert "Fix test/data isolation" in next_text
    assert "performance_stats" in next_text
    assert "Backtester hardening" in next_text
