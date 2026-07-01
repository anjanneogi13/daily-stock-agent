"""Guard test for Task 1 (issue #290): durable brain-state files must be tracked.

Root cause (audit 2026-06-24, Section 3 #1, Task 1):
  data/weight_history.jsonl, data/pattern_stats.json, and data/agent_memoir.json
  were gitignored and never committed, so the nightly `git add -f` silently
  no-opped when the conductor produced nothing new (the file didn't exist on
  disk at commit time).  As a result:
    - weight_history.jsonl reset every night  → 5%/week cap silently became 5%/night
    - pattern_stats.json  reset every night  → calibration/suppression continuity lost
    - agent_memoir.json   reset every night  → brain "memory" lost

These three assertions are tripwires: if a future merge or bad rebase drops the
seed files, CI will fail immediately rather than silently regressing to the
amnesiac nightly-reset behaviour.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_weight_history_jsonl_exists():
    """data/weight_history.jsonl must be present (seeded as empty file)."""
    path = ROOT / "data" / "weight_history.jsonl"
    assert path.exists(), (
        "data/weight_history.jsonl is missing — it drives the 5%/week weight "
        "cap accounting and must be tracked in the repo (issue #290). "
        "Seed it as an empty file and add !data/weight_history.jsonl to .gitignore."
    )


def test_pattern_stats_json_exists_and_is_object():
    """data/pattern_stats.json must be present and parse as a JSON object."""
    path = ROOT / "data" / "pattern_stats.json"
    assert path.exists(), (
        "data/pattern_stats.json is missing — it drives calibration / "
        "factor-suppression continuity and must be tracked in the repo (issue #290). "
        "Seed it as '{}' and add !data/pattern_stats.json to .gitignore."
    )
    data = json.loads(path.read_text())
    assert isinstance(data, dict), (
        f"data/pattern_stats.json must parse as a JSON object (dict), got {type(data)}"
    )


def test_agent_memoir_json_exists_and_is_object():
    """data/agent_memoir.json must be present and parse as a JSON object."""
    path = ROOT / "data" / "agent_memoir.json"
    assert path.exists(), (
        "data/agent_memoir.json is missing — it is the brain's persistent memory "
        "and must be tracked in the repo (issue #290). "
        "Seed it as '{}' and add !data/agent_memoir.json to .gitignore."
    )
    data = json.loads(path.read_text())
    assert isinstance(data, dict), (
        f"data/agent_memoir.json must parse as a JSON object (dict), got {type(data)}"
    )
