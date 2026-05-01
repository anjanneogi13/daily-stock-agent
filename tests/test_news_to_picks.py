"""Tests for PR #68 — News → Picks pipeline."""
import json
import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from src.watchlist_manager import (
    watchlist_score_boost, _freshness_multiplier, _hours_old,
    get_watchlist_tickers, watchlist_meta,
)


# ═══════════════════════════════════════════════════════════════
# Helper: build mock watchlist
# ═══════════════════════════════════════════════════════════════
def _make_watchlist(items, tmp_path, monkeypatch):
    """Write a fake watchlist.json and patch path."""
    wl = tmp_path / "watchlist.json"
    wl.write_text(json.dumps({"items": items}))
    monkeypatch.setattr("src.watchlist_manager.WATCHLIST_PATH", wl)
    return wl


def _item(ticker, sentiment="bullish", score=1.0, hours_ago=2,
          category="earnings_beat", headline="h"):
    """Build a watchlist item N hours old."""
    added = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
    return {
        "ticker": ticker, "sentiment": sentiment,
        "tradeable_score": score, "category": category,
        "headline": headline, "added_at": added,
        "source": "test",
    }


# ═══════════════════════════════════════════════════════════════
# Freshness multiplier tests
# ═══════════════════════════════════════════════════════════════
def test_freshness_under_4h_doubles():
    """Fresh news (<4h) gets 2× boost."""
    assert _freshness_multiplier(1.0) == 2.0
    assert _freshness_multiplier(3.5) == 2.0


def test_freshness_4_to_8h_is_1_5():
    assert _freshness_multiplier(5.0) == 1.5
    assert _freshness_multiplier(7.5) == 1.5


def test_freshness_8_to_24h_baseline():
    assert _freshness_multiplier(12.0) == 1.0
    assert _freshness_multiplier(23.0) == 1.0


def test_freshness_old_news_decays():
    assert _freshness_multiplier(36.0) == 0.6
    assert _freshness_multiplier(70.0) == 0.3


# ═══════════════════════════════════════════════════════════════
# Boost calculation tests (with fresh/stale news)
# ═══════════════════════════════════════════════════════════════
def test_fresh_bullish_news_boosts_2x(tmp_path, monkeypatch):
    """Fresh bullish news → boost of ~0.30 (was 0.15 max old)."""
    _make_watchlist([_item("LLY", sentiment="bullish", hours_ago=2)],
                    tmp_path, monkeypatch)
    boost = watchlist_score_boost("LLY")
    # tradeable=1.0 * 0.15 * 2.0 (freshness) = 0.30
    assert boost == 0.30


def test_stale_bullish_news_smaller_boost(tmp_path, monkeypatch):
    """36h-old bullish news → 0.6× multiplier → +0.09."""
    _make_watchlist([_item("LLY", sentiment="bullish", hours_ago=36)],
                    tmp_path, monkeypatch)
    boost = watchlist_score_boost("LLY")
    # 1.0 * 0.15 * 0.6 = 0.09
    assert abs(boost - 0.09) < 0.001


def test_fresh_bearish_news_penalizes(tmp_path, monkeypatch):
    """Fresh bearish → -0.30 (excludes from picks effectively)."""
    _make_watchlist([_item("XYZ", sentiment="bearish", hours_ago=2)],
                    tmp_path, monkeypatch)
    boost = watchlist_score_boost("XYZ")
    assert boost == -0.30


def test_no_watchlist_match_returns_zero(tmp_path, monkeypatch):
    _make_watchlist([_item("LLY")], tmp_path, monkeypatch)
    assert watchlist_score_boost("NVDA") == 0.0


def test_boost_capped_at_30(tmp_path, monkeypatch):
    """Even with weirdly high tradeable_score, boost cap = 0.30."""
    _make_watchlist([_item("LLY", score=2.0, hours_ago=1)],
                    tmp_path, monkeypatch)  # 2.0 * 0.15 * 2.0 = 0.60
    assert watchlist_score_boost("LLY") == 0.30  # capped


# ═══════════════════════════════════════════════════════════════
# Watchlist tickers filter tests (used by universe.py)
# ═══════════════════════════════════════════════════════════════
def test_get_watchlist_tickers_bullish_only(tmp_path, monkeypatch):
    _make_watchlist([
        _item("LLY", sentiment="bullish"),
        _item("XYZ", sentiment="bearish"),
        _item("GOOGL", sentiment="bullish"),
    ], tmp_path, monkeypatch)
    bullish = get_watchlist_tickers(bullish_only=True)
    assert "LLY" in bullish
    assert "GOOGL" in bullish
    assert "XYZ" not in bullish


def test_get_watchlist_tickers_includes_all_when_flag_off(tmp_path, monkeypatch):
    _make_watchlist([
        _item("LLY", sentiment="bullish"),
        _item("XYZ", sentiment="bearish"),
    ], tmp_path, monkeypatch)
    all_tickers = get_watchlist_tickers(bullish_only=False)
    assert "LLY" in all_tickers
    assert "XYZ" in all_tickers


# ═══════════════════════════════════════════════════════════════
# Universe expansion tests
# ═══════════════════════════════════════════════════════════════
def test_universe_includes_watchlist_tickers(tmp_path, monkeypatch):
    """PR #68: watchlist tickers should be added to scoring universe."""
    _make_watchlist([
        _item("PLTR", sentiment="bullish"),
        _item("LLY", sentiment="bullish"),
    ], tmp_path, monkeypatch)

    # Mock SP500 to return small list (simulating PLTR/LLY not in it)
    monkeypatch.setattr("src.universe.get_sp500_tickers",
                        lambda: ["AAPL", "MSFT", "NVDA"])
    monkeypatch.setattr("src.universe.get_semi_tickers",
                        lambda min_ai_weight=0: [])

    from src.universe import get_universe
    cfg = {
        "universe": {
            "source": "sp500",
            "include_watchlist": True,
            "semiconductors": {"always_include": False},
            "excluded_tickers": [],
        }
    }
    universe = get_universe(cfg)
    assert "PLTR" in universe, "Watchlist ticker not added to universe"
    assert "LLY" in universe, "Watchlist ticker not added to universe"
    assert "AAPL" in universe  # base S&P preserved


def test_universe_skips_watchlist_when_disabled(tmp_path, monkeypatch):
    """If config.include_watchlist=False, don't expand."""
    _make_watchlist([_item("PLTR", sentiment="bullish")], tmp_path, monkeypatch)
    monkeypatch.setattr("src.universe.get_sp500_tickers",
                        lambda: ["AAPL"])
    monkeypatch.setattr("src.universe.get_semi_tickers",
                        lambda min_ai_weight=0: [])

    from src.universe import get_universe
    cfg = {
        "universe": {
            "source": "sp500",
            "include_watchlist": False,
            "semiconductors": {"always_include": False},
            "excluded_tickers": [],
        }
    }
    universe = get_universe(cfg)
    assert "PLTR" not in universe


def test_universe_excluded_tickers_still_filtered(tmp_path, monkeypatch):
    """Excluded list still wins over watchlist."""
    _make_watchlist([_item("PLTR", sentiment="bullish")], tmp_path, monkeypatch)
    monkeypatch.setattr("src.universe.get_sp500_tickers", lambda: ["AAPL"])
    monkeypatch.setattr("src.universe.get_semi_tickers",
                        lambda min_ai_weight=0: [])

    from src.universe import get_universe
    cfg = {
        "universe": {
            "source": "sp500",
            "include_watchlist": True,
            "semiconductors": {"always_include": False},
            "excluded_tickers": ["PLTR"],   # PLTR excluded
        }
    }
    universe = get_universe(cfg)
    assert "PLTR" not in universe, "Exclusion should beat watchlist"


# ═══════════════════════════════════════════════════════════════
# Metadata test
# ═══════════════════════════════════════════════════════════════
def test_watchlist_meta_returns_full_info(tmp_path, monkeypatch):
    _make_watchlist([_item("LLY", hours_ago=2, headline="LLY beats Q1 earnings")],
                    tmp_path, monkeypatch)
    meta = watchlist_meta("LLY")
    assert meta["ticker"] == "LLY"
    assert meta["freshness_mult"] == 2.0
    assert meta["boost_applied"] == 0.30
    assert "LLY beats" in meta["headline"]


def test_watchlist_meta_returns_empty_for_unknown(tmp_path, monkeypatch):
    _make_watchlist([], tmp_path, monkeypatch)
    assert watchlist_meta("NVDA") == {}