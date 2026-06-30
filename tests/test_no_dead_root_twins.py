"""Task 10 (audit 2026-05-12 line 502): keep dead root twins from returning.

Root-level evaluate_picks.py was a STALE TWIN of the live scripts/evaluate_picks.py:
- nothing imports it,
- it reads data/trades.csv (a file the project no longer uses; current code uses
  data/picks_log.csv), so it is also broken,
- the live evaluator that evaluate.yml actually runs is scripts/evaluate_picks.py.

root backtest.py was already deleted in an earlier cleanup.

These guards assert the dead twin stays gone and the LIVE versions survive, so a
stray re-add or bad merge cannot silently resurrect a broken duplicate.

NOTE: top-level app.py is intentionally NOT covered here -- it is a live,
documented Streamlit dashboard (README: `streamlit run app.py`) and must remain.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_root_evaluate_picks_twin_is_gone():
    assert not (ROOT / "evaluate_picks.py").exists(), (
        "root evaluate_picks.py is a dead, broken twin (reads data/trades.csv) "
        "and must stay deleted; the live one is scripts/evaluate_picks.py"
    )


def test_root_backtest_stays_gone():
    assert not (ROOT / "backtest.py").exists(), (
        "root backtest.py (imported a deleted module) must stay deleted"
    )


def test_live_evaluate_picks_script_survives():
    assert (ROOT / "scripts" / "evaluate_picks.py").exists(), (
        "the live evaluator scripts/evaluate_picks.py must NOT be deleted"
    )


def test_live_streamlit_dashboard_survives():
    # app.py is a live, documented dashboard -- guard against accidental removal.
    assert (ROOT / "app.py").exists(), (
        "app.py is a live Streamlit dashboard (README: streamlit run app.py) "
        "and must remain"
    )
