"""G1-G4 (May 4 2026): Lock workflow persistence for ALL data writers."""
import re
from pathlib import Path

WORKFLOWS = Path(".github/workflows")


def _git_add_files_in(wf_name: str) -> set[str]:
    """Find all data/ paths on any line that has `git add`."""
    text = (WORKFLOWS / wf_name).read_text()
    files = set()
    for line in text.split("\n"):
        if "git add" in line:
            for tok in re.findall(r"data/[\w./*-]+", line):
                # Skip glob patterns when checking specific files
                files.add(tok)
    return files


def _persisted_anywhere(filename: str) -> list[str]:
    found = []
    for wf in WORKFLOWS.glob("*.yml"):
        if filename in _git_add_files_in(wf.name):
            found.append(wf.name)
    return found


# G1
def test_learning_journal_persisted():
    assert _persisted_anywhere("data/learning_journal.jsonl"), \
        "learning_journal.jsonl (788 entries) not committed by any workflow"

# G2
def test_agent_memoir_persisted():
    assert _persisted_anywhere("data/agent_memoir.json"), \
        "agent_memoir.json (soul memory) not committed"

# G3
def test_last_regime_persisted():
    assert _persisted_anywhere("data/last_regime.json"), \
        "last_regime.json not committed"

# G4
def test_hard_blocks_log_persisted():
    assert _persisted_anywhere("data/hard_blocks_log.json"), \
        "hard_blocks_log.json not committed"

# F6 regression
def test_news_signals_persisted():
    assert "data/news_signals.json" in _git_add_files_in("news_engine.yml")

# Always
def test_picks_log_persisted():
    assert _persisted_anywhere("data/picks_log.csv")
