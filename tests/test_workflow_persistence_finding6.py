"""Finding #6: signal_journal + learning_journal must be in evaluate.yml's FIRST commit step.

Why: evaluate.yml has 4 telegram-send steps between the first commit (line ~60)
and the last commit (line ~153). If ANY telegram step fails, evaluate exits and
the late commit never runs → journal updates lost.

Lock: signal_journal.jsonl and learning_journal.jsonl must appear in the FIRST
git-add command, not just the last one.
"""
import re
from pathlib import Path


WORKFLOW = Path(".github/workflows/evaluate.yml")


def _extract_git_add_blocks(yaml_text: str) -> list[str]:
    """Return all git-add blocks (handles multi-line continuations)."""
    blocks = []
    lines = yaml_text.split("\n")
    i = 0
    while i < len(lines):
        if "git add" in lines[i]:
            block = lines[i]
            # Collect continuation lines
            while block.rstrip().endswith("\\") and i + 1 < len(lines):
                i += 1
                block += "\n" + lines[i]
            blocks.append(block)
        i += 1
    return blocks


def test_signal_journal_in_first_commit_step():
    """signal_journal.jsonl must appear in the FIRST git-add block."""
    text = WORKFLOW.read_text()
    blocks = _extract_git_add_blocks(text)
    assert len(blocks) >= 1, "expected at least one git add block in evaluate.yml"
    assert "signal_journal.jsonl" in blocks[0], (
        f"signal_journal.jsonl missing from FIRST git-add block — "
        f"if any telegram step fails, journal updates will be lost.\n"
        f"First block:\n{blocks[0]}"
    )


def test_learning_journal_in_first_commit_step():
    """learning_journal.jsonl must also appear in the FIRST git-add block."""
    text = WORKFLOW.read_text()
    blocks = _extract_git_add_blocks(text)
    assert "learning_journal.jsonl" in blocks[0], (
        "learning_journal.jsonl missing from FIRST git-add block — "
        "same risk as signal_journal."
    )


def test_evaluate_workflow_unchanged_in_telegram_intent():
    """Sanity: telegram steps still exist (we only changed git-add lines)."""
    text = WORKFLOW.read_text()
    assert "send_layman_evening.py" in text
    assert "send_exec_telegram.py" in text
