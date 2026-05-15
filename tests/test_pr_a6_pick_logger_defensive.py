"""PR-A6: pick_logger defensive-writes tests.

Audit refs (docs/audit/2026-05-12_FULL_REPO_AUDIT/17_pick_logger.md):
- PL-7   mkdir at module-import time (side effect)
- PL-25  first write missing extrasaction='ignore' (asymmetric)
- PL-31  row["pick_date"] crashes on corrupted row
- PL-32  p["ticker"] crashes whole batch if any pick missing ticker
- PL-33+49 no try/except = single bad pick kills batch + lies about saved
- PL-34  round(None, 3) crashes on None score
- PL-37  defaults risk_reward to 2.0 (audit trail integrity)
"""
import csv
import importlib
from pathlib import Path
import pytest


def _fresh_logger(tmp_path, monkeypatch):
    """Reload pick_logger with LOG_PATH pointing at tmp."""
    import src.pick_logger as pl
    importlib.reload(pl)
    monkeypatch.setattr(pl, "LOG_PATH", tmp_path / "picks_log.csv")
    return pl


def test_pl7_no_mkdir_at_module_import():
    """PL-7: importing pick_logger MUST NOT create data/ on disk."""
    src = Path("src/pick_logger.py").read_text()
    # Find the line with LOG_PATH = Path(...) and check the next non-comment
    # line is NOT a mkdir call at module top.
    lines = src.splitlines()
    log_path_idx = next(i for i, l in enumerate(lines) if l.startswith("LOG_PATH = Path("))
    # Look at the next 3 non-comment, non-blank lines
    for i in range(log_path_idx + 1, log_path_idx + 5):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            continue
        assert "mkdir" not in line, (
            f"PL-7 regression: mkdir found at module top (line {i+1}): {line!r}"
        )
        break  # first real line is enough


def test_pl25_first_write_uses_extrasaction_ignore():
    """PL-25: first-write DictWriter must use extrasaction='ignore'.
    Symmetric with subsequent appends — prevents fresh-deploy crash."""
    src = Path("src/pick_logger.py").read_text()
    body = src[src.find("def _ensure_header"):src.find("def log_picks")]
    assert 'extrasaction="ignore"' in body or "extrasaction='ignore'" in body, (
        "PL-25 regression: first-write DictWriter missing extrasaction='ignore'"
    )


def test_pl32_pick_missing_ticker_does_not_crash(tmp_path, monkeypatch):
    """PL-32: a pick with no ticker must NOT crash the batch."""
    pl = _fresh_logger(tmp_path, monkeypatch)
    picks = [
        {"score": 0.8, "entry": 100.0, "stop_loss": 95.0},  # NO ticker — should be skipped
        {"ticker": "AAPL", "score": 0.9, "entry": 200, "stop_loss": 190},
    ]
    saved = pl.log_picks(picks, regime={"regime": "bull"})
    assert saved == 1, "AAPL should be saved despite first pick having no ticker"


def test_pl34_pick_with_none_score_does_not_crash(tmp_path, monkeypatch):
    """PL-34: round(None, 3) used to crash. Must be None-safe now."""
    pl = _fresh_logger(tmp_path, monkeypatch)
    picks = [
        {"ticker": "AAPL", "score": None, "entry": 100, "stop_loss": 95},
        {"ticker": "MSFT", "score": 0.7,  "entry": 200, "stop_loss": 190},
    ]
    saved = pl.log_picks(picks, regime={"regime": "bull"})
    assert saved == 2, "Both picks must save; None score should round to 0"


def test_pl37_risk_reward_not_defaulted_to_2(tmp_path, monkeypatch):
    """PL-37: if pick has no risk_reward, log empty string — NOT 2.0.
    Defaulting to 2.0 lies about what the pick actually said."""
    pl = _fresh_logger(tmp_path, monkeypatch)
    picks = [{"ticker": "AAPL", "score": 0.9, "entry": 100, "stop_loss": 95}]
    pl.log_picks(picks, regime={"regime": "bull"})
    rows = list(csv.DictReader(pl.LOG_PATH.open()))
    assert rows[0]["risk_reward"] == "", (
        f"PL-37 regression: risk_reward should be empty, got {rows[0]['risk_reward']!r}"
    )


def test_pl33_one_bad_pick_does_not_kill_batch(tmp_path, monkeypatch):
    """PL-33+49: a pick that triggers an exception during write must not
    block subsequent picks. Counter must reflect actual saved count."""
    pl = _fresh_logger(tmp_path, monkeypatch)
    # Inject a pick that will cause writerow to raise.
    # Use an unhashable/non-string in a string-typed field via a __str__ raise.
    class _Boom:
        def __str__(self):
            raise RuntimeError("synthetic write failure")
    picks = [
        {"ticker": "FIRST",  "score": 0.9, "entry": 100, "stop_loss": 95},
        {"ticker": "BOOM",   "score": 0.8, "entry": _Boom(), "stop_loss": 95},  # crashes csv encoding
        {"ticker": "AFTER",  "score": 0.7, "entry": 200, "stop_loss": 190},
    ]
    saved = pl.log_picks(picks, regime={"regime": "bull"})
    # FIRST and AFTER must be saved even if BOOM crashes
    assert saved >= 2, f"PL-33 regression: bad pick killed batch (saved={saved})"
    rows = list(csv.DictReader(pl.LOG_PATH.open()))
    tickers = {r["ticker"] for r in rows}
    assert "FIRST" in tickers and "AFTER" in tickers, (
        f"PL-33 regression: picks before/after bad pick lost. tickers={tickers}"
    )


def test_pl31_corrupted_existing_row_does_not_crash(tmp_path, monkeypatch):
    """PL-31: a corrupted existing row missing pick_date used to crash
    the entire log_picks call."""
    pl = _fresh_logger(tmp_path, monkeypatch)
    # Manually create a picks_log.csv with a corrupt row (missing pick_date)
    pl.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with pl.LOG_PATH.open("w") as f:
        # Write a header + a row with empty pick_date
        f.write("pick_date,ticker,score\n")
        f.write(",CORRUPT,0.5\n")
    # Now try to log a normal pick — should NOT crash on the corrupt row
    saved = pl.log_picks(
        [{"ticker": "GOOD", "score": 0.9, "entry": 100, "stop_loss": 95}],
        regime={"regime": "bull"},
    )
    assert saved == 1, "Normal pick must save despite corrupt existing row"
