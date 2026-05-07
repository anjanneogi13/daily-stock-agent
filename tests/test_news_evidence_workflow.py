from pathlib import Path
import re


WORKFLOW = Path(".github/workflows/news_evidence.yml")


def _text() -> str:
    return WORKFLOW.read_text()


def test_news_evidence_workflow_exists_and_is_monitoring_only():
    text = _text()

    assert "name: News Evidence" in text
    assert "workflow_dispatch" in text
    assert "30 22 * * 1-5" in text
    assert 'TRADING_MODE: "monitoring"' in text
    assert 'PAPER_TRADING_ENABLED: "false"' in text
    assert 'LIVE_TRADING_ENABLED: "false"' in text
    assert 'SMELL_ENFORCE: "false"' in text
    assert 'BRAIN_ENFORCE_EV: "false"' in text
    assert 'AUTO_PAUSE_ENABLED: "false"' in text


def test_news_evidence_workflow_runs_no_write_preflights_before_writes():
    text = _text()

    outcome_no_write = text.index("Preflight no-write outcome attribution")
    report_no_write = text.index("Preflight no-write evidence report")
    outcome_write = text.index("Generate news outcome attribution artifact")
    report_write = text.index("Generate news evidence report artifacts")

    assert outcome_no_write < outcome_write
    assert report_no_write < report_write
    assert "--no-write" in text
    assert "scripts/news_signal_outcome_attribution.py" in text
    assert "scripts/news_signal_evidence_report.py" in text


def test_news_evidence_workflow_commits_only_reporting_artifacts():
    text = _text()

    assert "data/news_signal_outcomes_${{ steps.params.outputs.report_date }}.jsonl" in text
    assert "data/news_signal_evidence_report_${{ steps.params.outputs.report_date }}.json" in text
    assert "data/news_signal_evidence_report_${{ steps.params.outputs.report_date }}.md" in text
    assert "news evidence report ${{ steps.params.outputs.report_date }} [skip ci]" in text

    commit_block = text.split("Commit news evidence artifacts", 1)[1]
    git_add_lines = "\n".join(
        line for line in commit_block.splitlines()
        if "git add" in line or "data/" in line
    )

    forbidden = [
        "data/picks_log.csv",
        "data/signal_journal.jsonl",
        "data/learning_journal.jsonl",
        "data/premarket_check.json",
        "data/telegram_sent.json",
    ]
    for path in forbidden:
        assert path not in git_add_lines


def test_news_evidence_workflow_checks_official_state_not_mutated():
    text = _text()

    safety = text.split("Safety check official state was not mutated", 1)[1].split(
        "Commit news evidence artifacts", 1
    )[0]

    assert "git diff --exit-code --" in safety
    assert "data/picks_log.csv" in safety
    assert "data/signal_journal.jsonl" in safety
    assert "data/learning_journal.jsonl" in safety
    assert "data/premarket_check.json" in safety
    assert "data/telegram_sent.json" in safety


def test_news_evidence_workflow_has_manual_parameters_and_validation():
    text = _text()

    assert "date:" in text
    assert "max_items:" in text
    assert "horizon_days:" in text
    assert "REPORT_DATE=" in text
    assert "MAX_ITEMS=" in text
    assert "HORIZON_DAYS=" in text
    assert "Invalid REPORT_DATE" in text
    assert "Invalid MAX_ITEMS" in text
    assert "Invalid HORIZON_DAYS" in text
    assert re.search(r"grep -Eq '\^\[0-9\]\{4\}-\[0-9\]\{2\}-\[0-9\]\{2\}\$'", text)
