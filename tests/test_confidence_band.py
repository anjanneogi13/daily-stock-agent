"""T30: per-pick confidence band emoji."""
import pytest
from src.confidence_band import (
    confidence_band, band_label, HIGH, GOOD, CAUTION, AVOID,
)

# Sample pattern_hint outputs (real shape from src/wisdom_hint.py)
DRAG = "   ⚠ _trade_type=day: 31% win-rate over 42 trades_"
EDGE = "   ✨ _regime=bull: 72% win-rate over 80 trades_"
LESSON = "   🧠 _AUTO: avoid Friday entries_"


class TestDragOverrides:
    def test_drag_low_score_avoid(self):
        assert confidence_band(0.7, DRAG) == AVOID
    def test_drag_high_score_caution(self):
        assert confidence_band(1.5, DRAG) == CAUTION
    def test_drag_at_score_1_caution(self):
        assert confidence_band(1.0, DRAG) == CAUTION


class TestEdgeBoosts:
    def test_edge_high_score_high(self):
        assert confidence_band(1.5, EDGE) == HIGH
    def test_edge_low_score_no_boost(self):
        # edge present but score not >1.2 → falls through to score-based
        assert confidence_band(0.9, EDGE) == GOOD
    def test_edge_borderline_low_score(self):
        assert confidence_band(0.5, EDGE) == CAUTION


class TestScoreOnly:
    def test_high_score_good(self):
        assert confidence_band(1.5, "") == GOOD
    def test_low_score_caution(self):
        assert confidence_band(0.5, "") == CAUTION
    def test_mid_score_good(self):
        assert confidence_band(1.0, "") == GOOD


class TestLessonNudge:
    def test_borderline_with_lesson_caution(self):
        # score 0.9, no drag, but lesson present → CAUTION
        assert confidence_band(0.9, "", LESSON) == CAUTION
    def test_high_score_lesson_still_good(self):
        assert confidence_band(1.5, "", LESSON) == GOOD


class TestRobustness:
    def test_garbage_score(self):
        assert confidence_band("abc", "") == CAUTION  # 0.0 → low
    def test_none_score(self):
        assert confidence_band(None, "") == CAUTION
    def test_none_hints(self):
        assert confidence_band(1.5, None, None) == GOOD


class TestBandLabel:
    def test_all_labels(self):
        assert band_label(HIGH) == "HIGH"
        assert band_label(GOOD) == "GOOD"
        assert band_label(CAUTION) == "CAUTION"
        assert band_label(AVOID) == "AVOID"
    def test_unknown(self):
        assert band_label("?") == "UNKNOWN"
