"""Bug #22 (2026-05-05): full_repo_audit output must remain accurate.

Regression targets:
  - TOTAL python lines must not be computed with an unquoted shell glob.
  - Audit should include the monitoring-readiness dashboard.
  - Audit should not keep stale "smell verdicts not persisted" pending check
    after smell persistence was fixed.
"""

from pathlib import Path


AUDIT = Path("scripts/full_repo_audit.py")


def test_python_line_count_uses_quoted_find_pattern():
    src = AUDIT.read_text()

    assert "find src scripts tests -name '*.py'" in src
    assert "find src scripts tests -name *.py" not in src


def test_audit_includes_monitoring_readiness_dashboard():
    src = AUDIT.read_text()

    assert "MONITORING READINESS" in src
    assert "scripts/monitoring_readiness.py" in src


def test_audit_removes_stale_smell_not_persisted_pending_check():
    src = AUDIT.read_text()

    assert "Smell verdicts not persisted on picks_log" not in src
    assert "smell_verdicts_not_persisted" not in src


def test_audit_includes_earnings_fill_rate_dashboard():
    src = AUDIT.read_text()

    assert "EARNINGS FILL-RATE" in src
    assert "scripts/audit_earnings_fill_rate.py" in src
