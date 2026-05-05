"""Bug #20 / Product Decision (2026-05-05): docs must encode monitoring-first launch.

The founder decision:
  - no real-money launch
  - no paper trading integration yet
  - monitor for 2 weeks
  - continue architecture build
  - monitor/test another 2 weeks
  - paper trading only if trade-type thresholds and expectancy gates pass
"""

from pathlib import Path


DECISION = Path("docs/decisions/2026-05-05-monitoring-first-no-paper-trading.md")
ARCH = Path("docs/ARCHITECTURE.md")
ROADMAP = Path("docs/FINAL_ROADMAP.md")
HEALTH = Path("docs/REPO_HEALTH.md")


def test_monitoring_first_decision_record_exists():
    assert DECISION.exists()
    text = DECISION.read_text()

    assert "Monitoring-first launch" in text
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


def test_architecture_mentions_monitoring_first_status():
    text = ARCH.read_text()

    assert "Monitoring-first launch" in text
    assert "paper trading is deferred" in text
    assert "real-money trading is forbidden" in text


def test_final_roadmap_mentions_monitoring_phase_before_features():
    text = ROADMAP.read_text()

    assert "Phase 5: Monitoring & Stabilization" in text
    assert "2-week observation" in text
    assert "second 2-week validation" in text
    assert "paper trading eligibility" in text


def test_repo_health_current_test_count_and_recent_fixes():
    text = HEALTH.read_text()

    assert "1208 passed, 28 skipped" in text
    assert "report issue upsert" in text
    assert "smell verdict persistence" in text
    assert "full_repo_audit import-safe and CSV-safe" in text
