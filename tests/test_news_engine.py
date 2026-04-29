"""Smoke tests for Phase 2A: news engine + classifier + watchlist."""
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.news_classifier import _heuristic_fallback, classify_news
from src.watchlist_manager import (
    add_from_news, get_watchlist, get_watchlist_tickers,
    watchlist_score_boost, _prune_expired, WATCHLIST_PATH
)


# ═══ News Classifier Tests ═══════════════════════════════════════
def test_heuristic_bullish_detection():
    item = {
        "headline": "AAPL beats earnings, raises guidance",
        "summary": "Apple posts record quarter",
        "ticker_list": ["AAPL"],
        "source": "alpaca",
        "published_at": datetime.now().isoformat(),
    }
    result = _heuristic_fallback(item)
    cls = result["classification"]
    assert cls["sentiment"] == "bullish"
    assert cls["sentiment_score"] > 0.5
    assert cls["tradeable_score"] > 0


def test_heuristic_bearish_detection():
    item = {
        "headline": "TSLA misses Q1, downgrade by analysts",
        "summary": "Tesla disappoints on margins",
        "ticker_list": ["TSLA"],
        "source": "alpaca",
        "published_at": datetime.now().isoformat(),
    }
    result = _heuristic_fallback(item)
    cls = result["classification"]
    assert cls["sentiment"] == "bearish"
    assert cls["sentiment_score"] < 0.5


def test_heuristic_neutral_for_routine_news():
    item = {
        "headline": "Company X to hold investor day next week",
        "summary": "Routine corporate event scheduled",
        "ticker_list": ["X"],
        "source": "yahoo",
        "published_at": datetime.now().isoformat(),
    }
    result = _heuristic_fallback(item)
    cls = result["classification"]
    assert cls["sentiment"] == "neutral"


# ═══ Watchlist Manager Tests ═════════════════════════════════════
def _reset_watchlist():
    if WATCHLIST_PATH.exists():
        WATCHLIST_PATH.unlink()


def test_watchlist_adds_high_score_news():
    _reset_watchlist()
    items = [{
        "headline": "MXL beats earnings 25%",
        "url": "https://test.com",
        "source": "alpaca",
        "ticker_list": ["MXL"],
        "classification": {
            "sentiment": "bullish",
            "tradeable_score": 0.85,
            "primary_ticker": "MXL",
            "category": "earnings_beat",
            "rationale": "huge beat",
            "action_window": "intraday",
        }
    }]
    added = add_from_news(items)
    assert len(added) == 1
    assert "MXL" in get_watchlist_tickers()


def test_watchlist_skips_low_score_news():
    _reset_watchlist()
    items = [{
        "headline": "Random small news",
        "url": "https://test.com",
        "source": "yahoo",
        "ticker_list": ["RANDOM"],
        "classification": {
            "sentiment": "neutral",
            "tradeable_score": 0.2,
            "primary_ticker": "RANDOM",
            "category": "other",
            "rationale": "noise",
            "action_window": "ignore",
        }
    }]
    added = add_from_news(items)
    assert len(added) == 0
    assert "RANDOM" not in get_watchlist_tickers()


def test_watchlist_dedup_updates_score():
    _reset_watchlist()
    base = {
        "headline": "Initial headline",
        "url": "https://test.com",
        "source": "yahoo",
        "ticker_list": ["XYZ"],
        "classification": {
            "sentiment": "bullish",
            "tradeable_score": 0.6,
            "primary_ticker": "XYZ",
            "category": "upgrade",
            "rationale": "first",
            "action_window": "next_day",
        }
    }
    add_from_news([base])
    # Second item with HIGHER score should update
    base["classification"]["tradeable_score"] = 0.9
    base["classification"]["rationale"] = "second"
    add_from_news([base])

    wl = get_watchlist()
    xyz = next(it for it in wl if it["ticker"] == "XYZ")
    assert xyz["tradeable_score"] == 0.9


def test_watchlist_score_boost_bullish():
    _reset_watchlist()
    items = [{
        "headline": "Test",
        "url": "",
        "source": "alpaca",
        "ticker_list": ["BOOST"],
        "classification": {
            "sentiment": "bullish",
            "tradeable_score": 0.8,
            "primary_ticker": "BOOST",
            "category": "earnings_beat",
            "rationale": "test",
            "action_window": "next_day",
        }
    }]
    add_from_news(items)
    boost = watchlist_score_boost("BOOST")
    assert 0 < boost <= 0.15
    assert watchlist_score_boost("NOT_THERE") == 0.0


def test_watchlist_score_boost_bearish_negative():
    _reset_watchlist()
    items = [{
        "headline": "Test",
        "url": "",
        "source": "alpaca",
        "ticker_list": ["BAD"],
        "classification": {
            "sentiment": "bearish",
            "tradeable_score": 0.7,
            "primary_ticker": "BAD",
            "category": "earnings_miss",
            "rationale": "test",
            "action_window": "next_day",
        }
    }]
    add_from_news(items)
    boost = watchlist_score_boost("BAD")
    assert boost < 0


def test_watchlist_expiry_pruning():
    _reset_watchlist()
    expired = {
        "ticker": "OLD",
        "tradeable_score": 0.8,
        "sentiment": "bullish",
        "added_at": (datetime.now(timezone.utc) - timedelta(hours=100)).isoformat(),
    }
    fresh = {
        "ticker": "NEW",
        "tradeable_score": 0.7,
        "sentiment": "bullish",
        "added_at": datetime.now(timezone.utc).isoformat(),
    }
    pruned = _prune_expired([expired, fresh])
    assert len(pruned) == 1
    assert pruned[0]["ticker"] == "NEW"


def test_watchlist_returns_sorted_by_score():
    _reset_watchlist()
    items = [
        {"headline": "h1", "url": "", "source": "alpaca", "ticker_list": ["LOW"],
         "classification": {"sentiment": "bullish", "tradeable_score": 0.55,
                            "primary_ticker": "LOW", "category": "other",
                            "rationale": "", "action_window": "next_day"}},
        {"headline": "h2", "url": "", "source": "alpaca", "ticker_list": ["HIGH"],
         "classification": {"sentiment": "bullish", "tradeable_score": 0.95,
                            "primary_ticker": "HIGH", "category": "earnings_beat",
                            "rationale": "", "action_window": "intraday"}},
    ]
    add_from_news(items)
    wl = get_watchlist_tickers()
    assert wl[0] == "HIGH"
    assert wl[1] == "LOW"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))