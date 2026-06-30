"""Task 4 (#18, audit 'relabel path'): the kill-switch is ADVISORY ONLY.

Locks the honest labeling so it cannot silently regress back to implying an
active/automatic pause. The agent is observe-only by default and its pause
state is non-durable, so user-facing text must not claim it auto-pauses.
"""
from src.auto_pause import format_summary


def test_high_score_summary_is_advisory_not_active_brake():
    # A RED-tier result (>=8) is where the old text claimed "would PAUSE".
    result = {
        "score": 9,
        "level": "🔴 RED",
        "reasons": ["🔴 5 consecutive losses"],
        "would_pause": True,
        "enforced": False,
    }
    out = format_summary(result)
    # Must clearly say it does NOT auto-pause / is advisory.
    low = out.lower()
    assert "advisory" in low or "does not auto-pause" in low, \
        f"summary must label itself advisory-only, got: {out!r}"
    # Must NOT imply an armed/active brake with the old phrasing.
    assert "would pause" not in low, "stale 'would PAUSE' phrasing must be gone"
    assert "enforce-mode active" not in low


def test_clear_score_summary_unchanged_semantics():
    result = {
        "score": 0,
        "level": "🟢 GREEN",
        "reasons": [],
        "would_pause": False,
        "enforced": False,
    }
    out = format_summary(result)
    assert "PAUSE SIGNAL" in out  # header preserved
    assert "all clear" in out.lower()
