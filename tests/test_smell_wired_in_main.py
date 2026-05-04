"""E4 — Lock that smell faculty is wired into main.py pipeline.

Without this test, future refactors could silently remove the smell
gate and we'd have no idea (regression to dead-code state)."""
import re
from pathlib import Path


MAIN_PY = Path("main.py").read_text()


def test_main_imports_smell_helpers():
    assert "from src.smell_faculty import" in MAIN_PY, \
        "main.py must import smell_faculty"
    assert "sniff" in MAIN_PY and "has_blocking_smell" in MAIN_PY, \
        "main.py must call sniff/has_blocking_smell"


def test_smell_runs_on_top_picks():
    """The smell loop must iterate over `top` (the finalists list)."""
    # Find the smell section
    assert "SMELL FACULTY" in MAIN_PY, "smell section must be marked"
    section = MAIN_PY[MAIN_PY.find("SMELL FACULTY"):]
    section = section[:section.find("WEEK 3: Auto-tag")]
    assert "for p in top:" in section, \
        "smell must iterate finalists (`top`)"


def test_smell_has_observe_and_enforce_modes():
    """Like EV gate + auto-pause, smell must support env-var enforcement."""
    assert "SMELL_ENFORCE" in MAIN_PY, \
        "smell must expose SMELL_ENFORCE env var"


def test_smell_runs_before_trade_type_tagging():
    """Smell must run BEFORE picks ship (before trade_type/Telegram)."""
    smell_idx = MAIN_PY.find("SMELL FACULTY")
    tagging_idx = MAIN_PY.find("Auto-tagging trade type")
    assert smell_idx > 0 and tagging_idx > 0
    assert smell_idx < tagging_idx, \
        "smell must run BEFORE trade_type tagging (i.e., before shipping)"


def test_smell_runs_after_ev_and_pause_gates():
    """Smell is the final gate — runs after EV + auto-pause."""
    smell_idx = MAIN_PY.find("SMELL FACULTY")
    ev_idx = MAIN_PY.find("PILLAR 1 EV GATE")
    pause_idx = MAIN_PY.find("PILLAR 5 AUTO-PAUSE")
    assert smell_idx > ev_idx, "smell must run AFTER EV gate"
    assert smell_idx > pause_idx, "smell must run AFTER auto-pause"
