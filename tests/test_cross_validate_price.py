"""E2c — Cross-source price validation tests.

Locks behavior so future refactors can't accidentally:
  - Accept None/zero/negative prices
  - Block trades when Finnhub is down (false positive)
  - Miss large disagreements between data sources
"""
from unittest.mock import patch
from src.finnhub_data import fetch_finnhub_quote, cross_validate_price


# ── fetch_finnhub_quote ──────────────────────────────────────────
def test_fetch_quote_no_api_key_returns_graceful():
    """No API key → returns dict with current=None and error, no exception."""
    import os
    with patch.dict(os.environ, {"FINNHUB_API_KEY": ""}, clear=False):
        if "FINNHUB_API_KEY" in os.environ:
            del os.environ["FINNHUB_API_KEY"]
        q = fetch_finnhub_quote("NVDA")
    assert q["current"] is None
    assert q["source"] == "finnhub"
    assert "error" in q


# ── cross_validate_price ─────────────────────────────────────────
def test_validate_rejects_none_price():
    v = cross_validate_price("NVDA", None)
    assert v["is_valid"] is False
    assert "invalid" in v["reason"].lower()


def test_validate_rejects_zero_price():
    v = cross_validate_price("NVDA", 0)
    assert v["is_valid"] is False


def test_validate_rejects_negative_price():
    v = cross_validate_price("NVDA", -5.0)
    assert v["is_valid"] is False


def test_validate_passes_when_second_source_unavailable():
    """If Finnhub is down (no key), don't block trades — pass with note."""
    with patch("src.finnhub_data.fetch_finnhub_quote") as mock_q:
        mock_q.return_value = {"current": None, "error": "no_api_key"}
        v = cross_validate_price("NVDA", 198.50)
    assert v["is_valid"] is True
    assert v["should_warn"] is False
    assert "no second source" in v["reason"].lower()


def test_validate_passes_when_prices_agree():
    """Agreement within 2% threshold = clean pass."""
    with patch("src.finnhub_data.fetch_finnhub_quote") as mock_q:
        mock_q.return_value = {"current": 199.00, "source": "finnhub"}
        v = cross_validate_price("NVDA", 198.50)
    assert v["is_valid"] is True
    assert v["should_warn"] is False
    assert v["disagreement_pct"] < 1.0


def test_validate_warns_on_2pct_disagreement():
    """2-5% disagreement = warn but don't block."""
    with patch("src.finnhub_data.fetch_finnhub_quote") as mock_q:
        mock_q.return_value = {"current": 195.00, "source": "finnhub"}  # 3.5% off
        v = cross_validate_price("NVDA", 202.00)
    assert v["is_valid"] is True
    assert v["should_warn"] is True
    assert v["disagreement_pct"] > 2.0


def test_validate_blocks_on_5pct_plus_disagreement():
    """5%+ disagreement = block (likely bad data, don't trade)."""
    with patch("src.finnhub_data.fetch_finnhub_quote") as mock_q:
        mock_q.return_value = {"current": 180.00, "source": "finnhub"}  # ~10% off
        v = cross_validate_price("NVDA", 200.00)
    assert v["is_valid"] is False
    assert "disagreement" in v["reason"].lower()


def test_validate_returns_disagreement_pct():
    with patch("src.finnhub_data.fetch_finnhub_quote") as mock_q:
        mock_q.return_value = {"current": 100.00, "source": "finnhub"}
        v = cross_validate_price("X", 102.00)
    assert v["disagreement_pct"] is not None
    assert 1.5 < v["disagreement_pct"] < 2.5


def test_validate_custom_thresholds():
    """Tighter thresholds → stricter blocking."""
    with patch("src.finnhub_data.fetch_finnhub_quote") as mock_q:
        mock_q.return_value = {"current": 100.50, "source": "finnhub"}  # 0.5% off
        v = cross_validate_price("X", 100.00,
                                 warn_threshold_pct=0.3,
                                 block_threshold_pct=0.4)
    assert v["is_valid"] is False  # 0.5% > 0.4% block threshold
