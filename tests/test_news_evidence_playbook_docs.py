from pathlib import Path


PLAYBOOK = Path("docs/playbook/NEWS_EVIDENCE_REPORTS.md")


def test_news_evidence_playbook_exists_and_documents_artifacts():
    text = PLAYBOOK.read_text()

    assert "News Evidence Reports Playbook" in text
    assert "data/news_signal_outcomes_YYYY-MM-DD.jsonl" in text
    assert "data/news_signal_evidence_report_YYYY-MM-DD.json" in text
    assert "data/news_signal_evidence_report_YYYY-MM-DD.md" in text
    assert ".github/workflows/news_evidence.yml" in text


def test_news_evidence_playbook_locks_safety_constraints():
    text = PLAYBOOK.read_text()

    assert "Do not start paper trading" in text
    assert "Do not enable real-money trading" in text
    assert "mode=monitoring_only" in text
    assert "official_pick_stats_mutated=false" in text
    assert "paper_trading_enabled=false" in text
    assert "live_trading_enabled=false" in text


def test_news_evidence_playbook_documents_no_write_and_official_diff_check():
    text = PLAYBOOK.read_text()

    assert "--no-write" in text
    assert "data/picks_log.csv" in text
    assert "data/signal_journal.jsonl" in text
    assert "data/learning_journal.jsonl" in text
    assert "git diff --" in text


def test_news_evidence_playbook_warns_against_small_sample_tuning():
    text = PLAYBOOK.read_text()

    assert "30–50 evaluated rows" in text
    assert "Do not tune catalyst scoring from a tiny sample" in text
    assert "paper/live trading readiness" in text
