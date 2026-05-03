"""Tests for Pillar 2 — Wisdom Base + Consultant."""
import sys, json, tempfile, shutil
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

import src.wisdom_base as wb
import src.wisdom_consultant as wc


def _isolate_wisdom_dir(tmp):
    """Redirect wisdom file paths into a temp dir so tests don't pollute real data."""
    wb.ROOT     = Path(tmp)
    wb.LESSONS  = wb.ROOT / "lessons.jsonl"
    wb.PATTERNS = wb.ROOT / "patterns.jsonl"
    wb.KILL     = wb.ROOT / "kill_list.json"
    wb.ROOT.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# Lessons
# ═══════════════════════════════════════════════════════════════
def test_add_and_load_lesson(tmp_path):
    _isolate_wisdom_dir(tmp_path)
    wb.add_lesson("Test lesson", source="manual", confidence=0.8, tags=["t"])
    lessons = wb.load_active_lessons(min_confidence=0.5)
    assert len(lessons) == 1
    assert lessons[0]["text"] == "Test lesson"


def test_low_confidence_filtered(tmp_path):
    _isolate_wisdom_dir(tmp_path)
    wb.add_lesson("low", confidence=0.2)
    wb.add_lesson("high", confidence=0.9)
    out = wb.load_active_lessons(min_confidence=0.5)
    assert len(out) == 1
    assert out[0]["text"] == "high"


def test_deactivate_lesson(tmp_path):
    _isolate_wisdom_dir(tmp_path)
    wb.add_lesson("KEEP this", confidence=0.9)
    wb.add_lesson("DROP this one", confidence=0.9)
    n = wb.deactivate_lesson("DROP")
    assert n == 1
    assert len(wb.load_active_lessons(0.5)) == 1


# ═══════════════════════════════════════════════════════════════
# Patterns
# ═══════════════════════════════════════════════════════════════
def test_add_pattern(tmp_path):
    _isolate_wisdom_dir(tmp_path)
    wb.add_pattern("regime", "bull", "edge", 0.7, 20, 0.012)
    ps = wb.load_active_patterns()
    assert len(ps) == 1
    assert ps[0]["effect"] == "edge"


# ═══════════════════════════════════════════════════════════════
# Kill list
# ═══════════════════════════════════════════════════════════════
def test_kill_list_add_and_check(tmp_path):
    _isolate_wisdom_dir(tmp_path)
    wb.add_to_kill_list("UNH", "test", cool_off_days=30)
    assert wb.is_killed("UNH") is not None
    assert wb.is_killed("unh") is not None  # case insensitive
    assert wb.is_killed("AAPL") is None


def test_kill_list_auto_expire(tmp_path):
    _isolate_wisdom_dir(tmp_path)
    # Manually create an already-expired entry
    wb._save_kill({
        "OLD": {
            "reason": "x",
            "added_at": (datetime.now() - timedelta(days=20)).isoformat(),
            "expires_at": (datetime.now() - timedelta(days=1)).isoformat(),
            "source": "test",
        }
    })
    active = wb.get_kill_list()
    assert "OLD" not in active


def test_remove_from_kill(tmp_path):
    _isolate_wisdom_dir(tmp_path)
    wb.add_to_kill_list("X", "r")
    assert wb.remove_from_kill_list("X") is True
    assert wb.remove_from_kill_list("Y") is False


# ═══════════════════════════════════════════════════════════════
# Consultant
# ═══════════════════════════════════════════════════════════════
def test_consult_no_signals_no_effect(tmp_path):
    _isolate_wisdom_dir(tmp_path)
    r = wc.consult_before_pick("X", {"regime": "bull"})
    assert r["score_adj"] == 0.0
    assert r["warnings"] == []
    assert r["boosts"] == []


def test_consult_kill_warning(tmp_path):
    _isolate_wisdom_dir(tmp_path)
    wb.add_to_kill_list("UNH", "tested loser")
    r = wc.consult_before_pick("UNH", {"regime": "bull"})
    assert r["kill"] is not None
    assert any("KILL" in w for w in r["warnings"])


def test_consult_pattern_boost_capped(tmp_path):
    _isolate_wisdom_dir(tmp_path)
    # Add 5 edges → would be +0.10, but cap is +0.05
    for sig in ["a", "b", "c", "d", "e"]:
        wb.add_pattern(sig, "x", "edge", 0.7, 20, 0.01)
    sigs = {s: "x" for s in ["a", "b", "c", "d", "e"]}
    r = wc.consult_before_pick("T", sigs)
    assert r["score_adj"] <= 0.05 + 1e-9
    assert len(r["boosts"]) == 5


def test_consult_drag_warning(tmp_path):
    _isolate_wisdom_dir(tmp_path)
    wb.add_pattern("regime", "bear", "drag", 0.2, 15, 0.03)
    r = wc.consult_before_pick("X", {"regime": "bear"})
    assert any("DRAG" in w for w in r["warnings"])
    assert r["score_adj"] < 0
