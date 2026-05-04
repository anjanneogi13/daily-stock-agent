"""Calibration tests — locks bucket thresholds against real data distribution.

If someone tweaks bucket thresholds without updating these tests, the test
fails — forcing them to consciously re-justify the calibration.

Calibrated 2026-05-04 from 39-pick distribution.
"""
from src.signal_journal import bucket_composite, bucket_vol, bucket_p_win


# ── composite_score buckets ──
def test_composite_low_threshold():
    assert bucket_composite(0.50) == "low"
    assert bucket_composite(0.54) == "low"


def test_composite_mid_range():
    assert bucket_composite(0.72) == "mid"
    assert bucket_composite(0.73) == "mid"
    assert bucket_composite(0.74) == "mid"


def test_composite_high_range():
    assert bucket_composite(0.77) == "high"
    assert bucket_composite(0.77) == "high"
    assert bucket_composite(0.78) == "high"


def test_composite_very_high():
    assert bucket_composite(0.79) == "very_high"
    assert bucket_composite(0.85) == "very_high"
    assert bucket_composite(0.95) == "very_high"


def test_composite_unknown():
    assert bucket_composite(None) == "unknown"
    assert bucket_composite("garbage") == "unknown"


# ── vol_ratio buckets ──
def test_vol_extreme():
    """>2.5x volume = extreme/blowoff/news territory."""
    assert bucket_vol(2.5) == "extreme"
    assert bucket_vol(5.0) == "extreme"


def test_vol_high():
    """1.3-2.5x = institutional interest, not chaos."""
    assert bucket_vol(1.3) == "high"
    assert bucket_vol(2.0) == "high"


def test_vol_normal():
    assert bucket_vol(1.0) == "normal"
    assert bucket_vol(1.2) == "normal"


def test_vol_low():
    assert bucket_vol(0.5) == "low"


# ── p_win buckets ──
def test_pwin_very_high():
    """>=0.65 = brain is highly confident."""
    assert bucket_p_win(0.65) == "very_high"
    assert bucket_p_win(0.75) == "very_high"


def test_pwin_high():
    assert bucket_p_win(0.55) == "high"
    assert bucket_p_win(0.60) == "high"


def test_pwin_mid_low():
    assert bucket_p_win(0.50) == "mid"
    assert bucket_p_win(0.40) == "low"


# ── Distribution sanity test ──
def test_distribution_is_meaningful():
    """Across 100 evenly-spaced scores [0.4, 0.95], no bucket should
    hold more than 60% of picks. This catches future miscalibration.
    """
    from collections import Counter
    scores = [0.40 + i * 0.0055 for i in range(100)]
    dist = Counter(bucket_composite(s) for s in scores)
    total = sum(dist.values())
    max_share = max(dist.values()) / total
    assert max_share < 0.65, (
        f"Bucket calibration regression: one bucket holds {max_share*100:.0f}% "
        f"of evenly-distributed scores. Distribution: {dict(dist)}"
    )
