"""P1 (COFOUNDER_AUDIT_2026-06-24 #3 / audit PV-X2): picks_csv.update_pick_row
must write atomically (tmp file + os.replace) so an interrupted write cannot
truncate or empty the durable picks_log.csv.

Current code opens LOG_PATH in "w" (truncate) mode and rewrites in place. If the
process is killed mid-write -- which happens because the intraday monitor calls
this repeatedly during market hours alongside a concurrent git-rebase-push loop
-- the multi-year pick history can be left half-written or empty.

pick_evaluator._save_picks already solved this exact problem with tmp+replace;
update_pick_row must use the same pattern.
"""
import csv
import importlib

import pytest


HEADER = ["pick_date", "ticker", "evaluation_status", "exit_price"]
ROWS = [
    {"pick_date": "2026-06-30", "ticker": "AAA", "evaluation_status": "pending", "exit_price": ""},
    {"pick_date": "2026-06-30", "ticker": "BBB", "evaluation_status": "pending", "exit_price": ""},
    {"pick_date": "2026-06-29", "ticker": "CCC", "evaluation_status": "tp_hit", "exit_price": "12.5"},
]


def _write_csv(path):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER)
        w.writeheader()
        w.writerows(ROWS)


def _read_rows(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _module_with_log(tmp_path, monkeypatch):
    """Import picks_csv with LOG_PATH pointed at a temp file."""
    import src.picks_csv as picks_csv
    importlib.reload(picks_csv)
    log = tmp_path / "picks_log.csv"
    monkeypatch.setattr(picks_csv, "LOG_PATH", log)
    return picks_csv, log


def test_successful_update_applies_and_leaves_no_tmp(tmp_path, monkeypatch):
    picks_csv, log = _module_with_log(tmp_path, monkeypatch)
    _write_csv(log)

    ok = picks_csv.update_pick_row("2026-06-30", "AAA", {"evaluation_status": "sl_hit", "exit_price": "9.0"})
    assert ok is True

    rows = _read_rows(log)
    aaa = [r for r in rows if r["ticker"] == "AAA"][0]
    assert aaa["evaluation_status"] == "sl_hit"
    assert aaa["exit_price"] == "9.0"
    # all rows preserved
    assert {r["ticker"] for r in rows} == {"AAA", "BBB", "CCC"}
    # no leftover tmp file
    leftovers = list(tmp_path.glob("*.tmp"))
    assert leftovers == [], f"atomic write left a tmp file behind: {leftovers}"


def test_interrupted_update_does_not_corrupt_original(tmp_path, monkeypatch):
    """If the write is interrupted mid-way, the ORIGINAL picks_log.csv must
    survive intact (atomic = all-or-nothing). On the current in-place truncate
    implementation, LOG_PATH is opened in 'w' (truncating it) BEFORE the rows
    are written, so an exception here destroys the history -> this test fails
    until update_pick_row writes to a tmp file first."""
    picks_csv, log = _module_with_log(tmp_path, monkeypatch)
    _write_csv(log)
    original = log.read_text()

    # Make the CSV row-writing blow up partway through the rewrite.
    real_writerows = csv.DictWriter.writerows

    def boom(self, rowdicts):
        # write nothing, simulate a crash/kill during the write
        raise RuntimeError("simulated crash mid-write")

    monkeypatch.setattr(csv.DictWriter, "writerows", boom)

    with pytest.raises(RuntimeError):
        picks_csv.update_pick_row("2026-06-30", "AAA", {"evaluation_status": "sl_hit"})

    monkeypatch.setattr(csv.DictWriter, "writerows", real_writerows)

    # The durable file must be UNCHANGED (atomic write protects it).
    assert log.exists(), "picks_log.csv was deleted by an interrupted write!"
    assert log.read_text() == original, (
        "picks_log.csv was corrupted/truncated by an interrupted write -- "
        "update_pick_row must write to a tmp file then os.replace."
    )
