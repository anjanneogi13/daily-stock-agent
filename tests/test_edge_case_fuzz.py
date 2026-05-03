"""T23: edge-case + fuzz hardening for prod-critical modules.

These run daily inside main.py. They MUST NEVER crash, even on:
  - empty data
  - malformed/missing fields
  - corrupt JSONL lines
  - future-dated timestamps
  - Unicode and exotic ticker symbols
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src import wisdom_base, auto_pause, auto_cooldown


# ════════════════════════════════════════════════════════════════
# auto_pause edge cases
# ════════════════════════════════════════════════════════════════

class TestAutoPauseEdges:
    def test_empty_closed_list(self):
        r = auto_pause.compute_score(closed=[])
        assert isinstance(r, dict)
        assert "score" in r

    def test_single_trade(self):
        r = auto_pause.compute_score(closed=[{
            "ticker": "X", "outcome": "loss", "r_multiple": -1.0,
            "evaluated_on": "2026-05-01", "pick_date": "2026-04-25",
        }])
        assert isinstance(r, dict)

    def test_missing_outcome_field(self):
        # Should not crash on rows without 'outcome'
        r = auto_pause.compute_score(closed=[
            {"ticker": "X", "pick_date": "2026-05-01"},
            {"ticker": "Y", "outcome": "win", "r_multiple": 1.0,
             "evaluated_on": "2026-05-01"},
        ])
        assert isinstance(r, dict)

    def test_string_r_multiples(self):
        # CSV reads everything as strings
        r = auto_pause.compute_score(closed=[
            {"ticker": "X", "outcome": "loss", "r_multiple": "-1.0",
             "evaluated_on": "2026-05-01"},
            {"ticker": "Y", "outcome": "win",  "r_multiple": "2.5",
             "evaluated_on": "2026-05-02"},
        ])
        assert isinstance(r["score"], int)

    def test_garbage_r_multiples(self):
        r = auto_pause.compute_score(closed=[
            {"ticker": "X", "outcome": "loss", "r_multiple": "N/A",
             "evaluated_on": "2026-05-01"},
            {"ticker": "Y", "outcome": "loss", "r_multiple": "",
             "evaluated_on": "2026-05-02"},
            {"ticker": "Z", "outcome": "loss", "r_multiple": None,
             "evaluated_on": "2026-05-03"},
        ])
        assert isinstance(r, dict)

    def test_future_dated_trades(self):
        future = (datetime.now() + timedelta(days=365)).date().isoformat()
        r = auto_pause.compute_score(closed=[
            {"ticker": "X", "outcome": "loss", "r_multiple": -1.0,
             "evaluated_on": future},
        ])
        assert isinstance(r, dict)

    def test_classify_extremes(self):
        for s in [0, 3, 6, 10, -5, 99]:
            r = auto_pause.classify(s)
            assert isinstance(r, str) and len(r) > 0

    def test_consecutive_losses_handles_no_loss(self):
        n = auto_pause.consecutive_losses([
            {"outcome": "win"}, {"outcome": "win"}
        ])
        assert n == 0

    def test_format_summary_never_crashes(self):
        for score in [0, 3, 6, 10, -1, 99]:
            r = {"score": score, "reasons": ["x"], "stats": {}}
            try:
                auto_pause.format_summary(r)
            except Exception as e:
                pytest.fail(f"format_summary crashed on score={score}: {e}")


# ════════════════════════════════════════════════════════════════
# auto_cooldown edge cases
# ════════════════════════════════════════════════════════════════

class TestAutoCooldownEdges:
    def test_empty_closed(self, monkeypatch):
        monkeypatch.setattr(auto_cooldown, "load_closed", lambda: [])
        r = auto_cooldown.scan_and_cool(apply=False)
        assert r["candidates"] == []
        assert r["dry_run"] is True

    def test_no_losses(self, monkeypatch):
        monkeypatch.setattr(auto_cooldown, "load_closed", lambda: [
            {"ticker": "WIN", "outcome": "win", "evaluated_on": "2026-05-01"},
            {"ticker": "WIN", "outcome": "win", "evaluated_on": "2026-05-02"},
        ])
        r = auto_cooldown.scan_and_cool(apply=False)
        assert r["candidates"] == []

    def test_loss_then_win_resets_streak(self, monkeypatch):
        monkeypatch.setattr(auto_cooldown, "load_closed", lambda: [
            {"ticker": "X", "outcome": "loss", "evaluated_on": "2026-05-01"},
            {"ticker": "X", "outcome": "loss", "evaluated_on": "2026-05-02"},
            {"ticker": "X", "outcome": "win",  "evaluated_on": "2026-05-03"},
            {"ticker": "X", "outcome": "loss", "evaluated_on": "2026-05-04"},
        ])
        r = auto_cooldown.scan_and_cool(apply=False, threshold=3)
        assert r["candidates"] == []  # streak reset after the win

    def test_unknown_outcome_ignored(self, monkeypatch):
        monkeypatch.setattr(auto_cooldown, "load_closed", lambda: [
            {"ticker": "X", "outcome": "OPEN",   "evaluated_on": "2026-05-01"},
            {"ticker": "X", "outcome": "PARTIAL","evaluated_on": "2026-05-02"},
            {"ticker": "X", "outcome": None,     "evaluated_on": "2026-05-03"},
        ])
        r = auto_cooldown.scan_and_cool(apply=False)
        assert r["candidates"] == []

    def test_apply_false_writes_nothing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(wisdom_base, "KILL", tmp_path / "kill.json")
        monkeypatch.setattr(wisdom_base, "LESSONS", tmp_path / "lessons.jsonl")
        monkeypatch.setattr(auto_cooldown, "load_closed", lambda: [
            {"ticker": "BAD", "outcome": "loss",
             "evaluated_on": f"2026-05-0{i}"} for i in range(1, 4)
        ])
        auto_cooldown.scan_and_cool(apply=False)
        assert wisdom_base.get_kill_list() == {}
        assert wisdom_base.load_active_lessons(0.0) == []


# ════════════════════════════════════════════════════════════════
# wisdom_base edge cases
# ════════════════════════════════════════════════════════════════

class TestWisdomBaseEdges:
    @pytest.fixture
    def isolated(self, tmp_path, monkeypatch):
        monkeypatch.setattr(wisdom_base, "LESSONS",  tmp_path / "lessons.jsonl")
        monkeypatch.setattr(wisdom_base, "PATTERNS", tmp_path / "patterns.jsonl")
        monkeypatch.setattr(wisdom_base, "KILL",     tmp_path / "kill.json")
        return tmp_path

    def test_load_lessons_empty_file(self, isolated):
        assert wisdom_base.load_active_lessons() == []

    def test_load_lessons_corrupt_lines_skipped(self, isolated):
        f = isolated / "lessons.jsonl"
        f.write_text(
            "this is not json\n"
            + json.dumps({"text": "ok", "confidence": 0.9, "active": True}) + "\n"
            + "{broken json\n"
            + json.dumps({"text": "ok2", "confidence": 0.8, "active": True}) + "\n"
        )
        out = wisdom_base.load_active_lessons(min_confidence=0.0)
        assert len(out) >= 2  # corrupt lines skipped, valid kept

    def test_kill_list_corrupt_json_returns_empty(self, isolated):
        (isolated / "kill.json").write_text("{not valid json")
        # Must not crash
        try:
            kl = wisdom_base.get_kill_list()
            assert isinstance(kl, dict)
        except Exception as e:
            pytest.fail(f"get_kill_list crashed on corrupt JSON: {e}")

    def test_kill_list_expired_entries_filtered(self, isolated):
        wisdom_base.add_to_kill_list("EXPD", reason="old", cool_off_days=-1,
                                      source="test")
        kl = wisdom_base.get_kill_list()
        assert "EXPD" not in kl  # already expired

    def test_unicode_ticker(self, isolated):
        wisdom_base.add_to_kill_list("BRK.A", reason="x", cool_off_days=10,
                                      source="test")
        assert "BRK.A" in wisdom_base.get_kill_list()

    def test_remove_nonexistent_ticker(self, isolated):
        # Must not crash, just return False/None
        try:
            r = wisdom_base.remove_from_kill_list("NEVER_ADDED")
            assert r in (False, 0, None)
        except Exception as e:
            pytest.fail(f"remove_from_kill_list crashed: {e}")

    def test_add_lesson_long_text(self, isolated):
        long = "x" * 5000
        wisdom_base.add_lesson(text=long, source="t", confidence=0.8,
                                tags=[], author="t")
        out = wisdom_base.load_active_lessons(0.0)
        assert any(L["text"] == long for L in out)

    def test_stats_always_returns_keys(self, isolated):
        s = wisdom_base.stats()
        assert "active_lessons" in s
        assert "active_patterns" in s
        assert "kill_list_size" in s

    def test_is_killed_clean_ticker(self, isolated):
        assert wisdom_base.is_killed("CLEAN") in (None, False, {})
