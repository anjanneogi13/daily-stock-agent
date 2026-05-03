"""T29: auto-promote significant patterns → wisdom lessons."""
import pytest
from src import wisdom_base, auto_promote


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(wisdom_base, "LESSONS",  tmp_path / "lessons.jsonl")
    monkeypatch.setattr(wisdom_base, "PATTERNS", tmp_path / "patterns.jsonl")
    monkeypatch.setattr(wisdom_base, "KILL",     tmp_path / "kill.json")
    return tmp_path


def _add_p(signal, bucket, effect="drag", win_rate=0.30,
           sample_n=50, p_value=0.005):
    wisdom_base.add_pattern(
        signal=signal, bucket=bucket, effect=effect,
        win_rate=win_rate, sample_n=sample_n, p_value=p_value,
    )


# ═════════════════════════════════════════════════════════════
class TestPromotionGate:
    def test_no_patterns_returns_empty(self, isolated):
        assert auto_promote.promote_patterns() == []

    def test_qualifying_drag_promoted(self, isolated):
        _add_p("trade_type", "day", effect="drag",
               win_rate=0.31, sample_n=42, p_value=0.005)
        out = auto_promote.promote_patterns()
        assert len(out) == 1
        assert "day" in out[0]["text"].lower()
        assert "avoid" in out[0]["text"].lower()
        assert out[0]["source"] == "auto_promote"

    def test_qualifying_edge_promoted(self, isolated):
        _add_p("regime", "bull", effect="edge",
               win_rate=0.72, sample_n=80, p_value=0.001)
        out = auto_promote.promote_patterns()
        assert len(out) == 1
        assert "favor" in out[0]["text"].lower()

    def test_low_sample_excluded(self, isolated):
        _add_p("trade_type", "day", sample_n=10)  # < 40
        assert auto_promote.promote_patterns() == []

    def test_high_p_value_excluded(self, isolated):
        _add_p("regime", "bull", p_value=0.20)  # > 0.01
        assert auto_promote.promote_patterns() == []

    def test_unknown_signal_excluded(self, isolated):
        _add_p("moon_phase", "full")
        assert auto_promote.promote_patterns() == []

    def test_neither_drag_nor_edge_excluded(self, isolated):
        _add_p("trade_type", "swing", effect="neutral")
        assert auto_promote.promote_patterns() == []

    def test_empty_bucket_excluded(self, isolated):
        _add_p("trade_type", "")
        assert auto_promote.promote_patterns() == []


# ═════════════════════════════════════════════════════════════
class TestIdempotency:
    def test_double_run_no_dupes(self, isolated):
        _add_p("trade_type", "day", win_rate=0.31,
               sample_n=42, p_value=0.005)

        first  = auto_promote.promote_patterns()
        second = auto_promote.promote_patterns()

        assert len(first) == 1
        assert len(second) == 0  # already promoted

    def test_marker_tag_present(self, isolated):
        _add_p("regime", "chop", win_rate=0.30,
               sample_n=60, p_value=0.002)
        out = auto_promote.promote_patterns()
        marker = auto_promote._marker("regime", "chop")
        assert marker in out[0]["tags"]

    def test_three_distinct_patterns_all_promoted(self, isolated):
        _add_p("trade_type", "day",   win_rate=0.31, sample_n=42, p_value=0.005)
        _add_p("regime",     "chop",  win_rate=0.30, sample_n=60, p_value=0.003)
        _add_p("sector",     "XLE",   win_rate=0.28, sample_n=55, p_value=0.001)
        out = auto_promote.promote_patterns()
        assert len(out) == 3


# ═════════════════════════════════════════════════════════════
class TestConfidence:
    def test_low_p_high_conf(self):
        assert auto_promote._confidence_from_p(0.001) == 0.95
    def test_high_p_low_conf(self):
        assert auto_promote._confidence_from_p(0.05) >= 0.7
    def test_clamped_lower(self):
        assert auto_promote._confidence_from_p(1.0) == 0.7
    def test_clamped_upper(self):
        assert auto_promote._confidence_from_p(-99) == 0.95
    def test_garbage_returns_floor(self):
        assert auto_promote._confidence_from_p("xx") == 0.7


# ═════════════════════════════════════════════════════════════
class TestDryRun:
    def test_dry_run_writes_nothing(self, isolated):
        _add_p("trade_type", "day", win_rate=0.31,
               sample_n=42, p_value=0.005)
        out = auto_promote.promote_patterns(dry_run=True)
        assert len(out) == 1
        assert out[0]["_dry_run"] is True
        # No lesson actually persisted
        assert wisdom_base.load_active_lessons(min_confidence=0.0) == []


# ═════════════════════════════════════════════════════════════
class TestCLI:
    def test_cli_no_patterns(self, isolated, capsys):
        rc = auto_promote._cli([])
        assert rc == 0
        assert "No patterns" in capsys.readouterr().out

    def test_cli_promotes(self, isolated, capsys):
        _add_p("trade_type", "day", win_rate=0.31,
               sample_n=42, p_value=0.005)
        rc = auto_promote._cli([])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Promoted 1" in out

    def test_cli_dry_run(self, isolated, capsys):
        _add_p("regime", "bull", effect="edge",
               win_rate=0.72, sample_n=80, p_value=0.001)
        rc = auto_promote._cli(["--dry-run"])
        out = capsys.readouterr().out
        assert rc == 0
        assert "Would promote" in out
        assert wisdom_base.load_active_lessons(min_confidence=0.0) == []
