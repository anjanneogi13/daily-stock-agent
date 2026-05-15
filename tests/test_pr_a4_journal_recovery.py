"""PR-A4: signal_journal recovery + workflow-stage fix.

Real-world bug: 2026-05-15 AMAT was logged to picks_log.csv but never
journaled because daily-picks.yml omitted signal_journal.jsonl from
'git add'. The F4 guardian test caught the resulting drift.
"""
import re
from pathlib import Path


def test_workflow_stages_signal_journal_in_main_commit():
    """daily-picks.yml MUST stage signal_journal.jsonl in the main commit step.
    Without this, every successful pick silently drifts the journal."""
    text = Path(".github/workflows/daily-picks.yml").read_text()
    main_commit_block = re.search(
        r"Commit results \(with retry safety\).*?Premarket sanity",
        text, re.DOTALL,
    )
    assert main_commit_block, "could not locate main commit step"
    assert "data/signal_journal.jsonl" in main_commit_block.group(0), (
        "signal_journal.jsonl missing from main commit's git-add — "
        "this is the bug that lost AMAT's journal entry on 2026-05-15"
    )


def test_workflow_stages_signal_journal_in_post_send_commit():
    """Same invariant for the post-send commit step (defense in depth)."""
    text = Path(".github/workflows/daily-picks.yml").read_text()
    post_send_block = re.search(
        r"Commit post-send artifacts.*?\Z", text, re.DOTALL,
    )
    assert post_send_block, "could not locate post-send commit step"
    assert "data/signal_journal.jsonl" in post_send_block.group(0), (
        "signal_journal.jsonl missing from post-send commit's git-add"
    )


def test_recovery_script_exists_and_is_callable():
    """The recovery script must exist for future drift events."""
    p = Path("scripts/recover_missing_journal_entries.py")
    assert p.exists(), "recovery script must exist for future drift events"
    text = p.read_text()
    assert "from src import signal_journal as sj" in text, (
        "recovery must use the real signal_journal module, not invent its own write path"
    )
    assert "sj.log_pick(" in text, (
        "recovery must call the same log_pick code path main.py uses"
    )
