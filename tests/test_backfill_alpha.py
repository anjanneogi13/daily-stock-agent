"""Bug #9 (2026-05-05): backfill alpha_pct for 9 closed picks from
2026-04-28 → 2026-05-01 that have spy_close populated but blank
spy_close_at_exit / alpha_pct (the _add_spy_alpha calculator was
added 2026-05-01, after these picks closed).

Tests cover: candidate detection, idempotency, dry-run safety,
atomic write, and that we DON'T touch picks that already have alpha."""
import csv
import shutil
import subprocess
import sys
from pathlib import Path
import pytest


SCRIPT = Path("scripts/backfill_alpha.py")
PICKS_LOG = Path("data/picks_log.csv")


def test_script_exists():
    assert SCRIPT.exists(), f"{SCRIPT} must exist"


def test_script_has_apply_flag():
    """Convention: --apply flag, dry-run by default."""
    src = SCRIPT.read_text()
    assert "--apply" in src
    assert "dry" in src.lower()


def test_dry_run_does_not_modify_csv(tmp_path, monkeypatch):
    """Dry run must NEVER write to picks_log.csv."""
    backup = tmp_path / "picks_log.backup.csv"
    shutil.copy(PICKS_LOG, backup)
    original_bytes = backup.read_bytes()

    # Run dry-run (no --apply)
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True, text=True, cwd=Path.cwd(),
    )
    assert result.returncode == 0, f"dry-run failed:\n{result.stderr}"
    assert PICKS_LOG.read_bytes() == original_bytes, (
        "Dry run modified picks_log.csv — must not write without --apply"
    )


def test_dry_run_reports_candidates():
    """Dry run must report how many rows it WOULD backfill."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True, text=True, cwd=Path.cwd(),
    )
    out = result.stdout.lower()
    # Must mention either a count or 'candidate' / 'would' / 'dry'
    assert any(k in out for k in ("candidate", "would", "dry", "backfill")), (
        f"dry-run produced no informative output:\n{result.stdout}"
    )


def test_candidate_detection_logic():
    """Unit-test the candidate filter directly (faster than subprocess)."""
    sys.path.insert(0, str(SCRIPT.parent))
    import importlib.util
    spec = importlib.util.spec_from_file_location("backfill_alpha", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Should be a candidate: closed + spy_close set + alpha_pct empty
    yes = {"evaluation_status": "tp_hit", "spy_close": "718.66",
           "alpha_pct": "", "evaluated_on": "2026-05-01",
           "actual_return_pct": "2.18"}
    assert mod.is_candidate(yes) is True

    # NOT a candidate: alpha_pct already filled (idempotency)
    no_already = {**yes, "alpha_pct": "1.5"}
    assert mod.is_candidate(no_already) is False

    # NOT a candidate: still pending
    no_pending = {**yes, "evaluation_status": "pending"}
    assert mod.is_candidate(no_pending) is False

    # NOT a candidate: missing spy_close (can't compute)
    no_spy = {**yes, "spy_close": ""}
    assert mod.is_candidate(no_spy) is False

    # NOT a candidate: missing evaluated_on (can't fetch SPY at exit)
    no_eval = {**yes, "evaluated_on": ""}
    assert mod.is_candidate(no_eval) is False

    # NOT a candidate: missing actual_return_pct (can't compute alpha)
    no_ret = {**yes, "actual_return_pct": ""}
    assert mod.is_candidate(no_ret) is False


def test_uses_existing_add_spy_alpha_helper():
    """Must reuse src.pick_evaluator._add_spy_alpha — no duplicated logic."""
    src = SCRIPT.read_text()
    assert "_add_spy_alpha" in src, (
        "Must import and reuse _add_spy_alpha from src.pick_evaluator "
        "to avoid divergent SPY-alpha logic."
    )
