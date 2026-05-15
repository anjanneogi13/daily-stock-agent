"""PR-A4.5: signal_journal atomic-write hardening tests.

Audit refs: SJ-13 (attach_outcome rewrite), SJ-33 (log_pick append),
BUG-M107 (main.py quarantine of failed writes).
"""
import json
import os
import re
from pathlib import Path
import pytest

import src.signal_journal as sj


def test_log_pick_uses_atomic_os_write(tmp_path, monkeypatch):
    """log_pick must use os.open/os.write/os.fsync for atomic append.
    Plain f.write() in append mode does NOT guarantee atomic write to disk."""
    journal = tmp_path / "j.jsonl"
    monkeypatch.setattr(sj, "JOURNAL", journal)
    pick = {"ticker": "TEST", "pick_date": "2026-05-15", "scores": {"composite": 0.8}}
    sj.log_pick(pick, regime="bull")
    lines = journal.read_text().strip().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["ticker"] == "TEST"
    assert rec["pick_date"] == "2026-05-15"


def test_log_pick_rejects_oversize_row(tmp_path, monkeypatch):
    """Defensive: rows larger than PIPE_BUF safety margin must raise rather
    than risk silent partial-line corruption of the journal."""
    journal = tmp_path / "j.jsonl"
    monkeypatch.setattr(sj, "JOURNAL", journal)
    pick = {
        "ticker": "TEST",
        "pick_date": "2026-05-15",
        "scores": {"composite": 0.8, "sector_tag": "X" * 5000},
    }
    with pytest.raises(ValueError, match="too large for atomic append"):
        sj.log_pick(pick)


def test_log_pick_source_uses_os_open_and_fsync():
    """Hard guard: verify the source file actually contains the atomic
    primitives. Easy to accidentally regress to f.write() in a future
    refactor; this test prevents that."""
    src = Path("src/signal_journal.py").read_text()
    assert "os.open(str(JOURNAL)" in src, "log_pick must use os.open for atomic append"
    assert "os.write(fd, line_bytes)" in src, "log_pick must use os.write"
    assert "os.fsync(fd)" in src, "log_pick must fsync after write"


def test_attach_outcome_uses_tmp_rename_pattern():
    """Hard guard: attach_outcome rewrite must use tmp+os.replace pattern.
    A direct JOURNAL.open('w') is the bug we're fixing."""
    src = Path("src/signal_journal.py").read_text()
    # Within the attach_outcome function body
    body = src[src.find("def attach_outcome"):src.find("def load_closed")]
    assert "os.replace(str(tmp), str(JOURNAL))" in body, (
        "attach_outcome must rewrite via tmp+os.replace for atomicity"
    )
    assert "os.fsync(f.fileno())" in body, (
        "attach_outcome must fsync the tmp file before rename"
    )


def test_attach_outcome_works_end_to_end(tmp_path, monkeypatch):
    """Functional: attach_outcome still works correctly after refactor."""
    journal = tmp_path / "j.jsonl"
    monkeypatch.setattr(sj, "JOURNAL", journal)
    sj.log_pick({"ticker": "TEST", "pick_date": "2026-05-15"}, regime="bull")
    found = sj.attach_outcome("TEST", "2026-05-15",
                              r_multiple=1.5, actual_return_pct=3.2,
                              evaluated_on="2026-05-16")
    assert found is True
    rec = json.loads(journal.read_text().strip().splitlines()[0])
    assert rec["outcome"] == "win"
    assert rec["r_multiple"] == 1.5
    assert rec["actual_return_pct"] == 3.2


def test_main_py_quarantines_journal_failures():
    """When main.py's per-pick try/except catches a journal failure, it
    MUST also append to data/signal_journal_failures.jsonl so we have an
    audit trail (audit BUG-M107)."""
    src = Path("main.py").read_text()
    assert "data/signal_journal_failures.jsonl" in src, (
        "main.py must quarantine failed journal writes for recovery"
    )
    assert "_quarantine" in src, (
        "main.py must use a quarantine variable for clarity"
    )


def test_no_partial_line_after_atomic_write(tmp_path, monkeypatch):
    """Concretely: after log_pick returns, the journal must contain a
    well-formed JSON line ending in newline. No partial lines, no dangling
    commas, no truncation."""
    journal = tmp_path / "j.jsonl"
    monkeypatch.setattr(sj, "JOURNAL", journal)
    for i in range(5):
        sj.log_pick({"ticker": f"T{i}", "pick_date": "2026-05-15"}, regime="bull")
    raw = journal.read_text()
    assert raw.endswith("\n"), "every line must end in newline"
    lines = raw.strip().splitlines()
    assert len(lines) == 5
    for line in lines:
        json.loads(line)  # must parse cleanly
