"""Bug #23 (2026-05-05): TODO_BUGS must be a current status ledger.

docs/TODO_BUGS.md is used as an operational issue ledger. It should not be a
stale free-form list after fixes land.
"""

from pathlib import Path


TODO = Path("docs/TODO_BUGS.md")


def test_todo_bugs_has_status_legend_and_sections():
    text = TODO.read_text()

    assert "Status legend" in text
    assert "OPEN" in text
    assert "FIXED" in text
    assert "PARTIAL" in text
    assert "DEFERRED" in text
    assert "Current bug ledger" in text


def test_recent_cleanup_bugs_are_marked_fixed():
    text = TODO.read_text()

    for bug in ["Bug #19", "Bug #20", "Bug #21", "Bug #22"]:
        assert bug in text

    assert "Bug #19" in text and "FIXED" in text and "report issue upsert" in text
    assert "Bug #20" in text and "monitoring-first" in text
    assert "Bug #21" in text and "monitoring readiness" in text
    assert "Bug #22" in text and "full_repo_audit" in text


def test_remaining_known_open_items_are_not_lost():
    text = TODO.read_text()

    assert "Bug #6" in text and "company-name" in text and "FIXED" in text
    assert "Bug #7" in text and "non-trading days" in text
    assert "Bug #11" in text and "days_to_earnings" in text and "FIXED" in text
    assert "Bug #13" in text and "Tiered TP" in text


def test_stale_critical_sector_close_wording_removed():
    text = TODO.read_text()

    assert "sector_close never populated at pick time (CRITICAL" not in text
    assert "CRITICAL — unlocks 4 dead columns" not in text


def test_data_quality_cleanup_bugs_are_marked_fixed():
    text = TODO.read_text()

    assert "Bug #8" in text and "Sector alpha" in text and "FIXED" in text
    assert "Bug #10" in text and "Sector ETF fill rate" in text and "FIXED" in text
    assert "Bug #11" in text and "Earnings data" in text and "FIXED" in text
    assert "backfill_earnings_days.py" in text
    assert "audit_sector_fill_rate.py" in text


def test_company_name_bug_marked_fixed():
    text = TODO.read_text()

    assert "Bug #6" in text
    assert "company-name" in text
    assert "ticker-as-company" in text
    assert "FIXED" in text
