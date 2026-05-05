"""Bug #19 (2026-05-05): workflow report issues must be upserted, not duplicated.

Problem:
  daily-picks.yml and evaluate.yml create a new GitHub issue every time they run.
  Re-runs produce duplicate Daily Picks / Performance / Execution Report issues.

Contract:
  - Shared JS helper exists for issue upsert.
  - Helper lists open issues, exact-matches title, updates if found, creates otherwise.
  - Workflows use the helper instead of raw github.rest.issues.create blocks.
"""

from pathlib import Path


HELPER = Path(".github/scripts/upsert_issue.js")
DAILY = Path(".github/workflows/daily-picks.yml")
EVALUATE = Path(".github/workflows/evaluate.yml")


def test_issue_upsert_helper_exists_and_updates_existing_issue():
    assert HELPER.exists(), "Missing shared .github/scripts/upsert_issue.js helper"

    src = HELPER.read_text()

    assert "async function upsertIssue" in src
    assert "listForRepo" in src
    assert "issues.update" in src
    assert "issues.create" in src
    assert "i.title === title" in src
    assert "module.exports" in src


def test_daily_picks_workflow_uses_issue_upsert_helper():
    src = DAILY.read_text()

    assert "upsert_issue.js" in src
    assert "upsertIssue" in src
    assert "github.rest.issues.create({" not in src


def test_evaluate_workflow_uses_issue_upsert_helper_for_both_reports():
    src = EVALUATE.read_text()

    assert "upsert_issue.js" in src
    assert src.count("upsertIssue") >= 2
    assert "github.rest.issues.create({" not in src
