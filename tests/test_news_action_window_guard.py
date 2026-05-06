from datetime import datetime, timedelta, timezone

from src.news_signals import add_signal_from_classification, get_ticker_signal
import src.news_signals as ns
import main


def test_news_signal_preserves_action_window(tmp_path, monkeypatch):
    monkeypatch.setattr(ns, "SIGNALS_PATH", tmp_path / "news_signals.json")

    sig = add_signal_from_classification({
        "headline": "EXPD beats earnings",
        "summary": "",
        "classification": {
            "primary_ticker": "EXPD",
            "category": "earnings_beat",
            "sentiment": "bullish",
            "tradeable_score": 0.88,
            "action_window": "intraday",
        },
    })

    assert sig["action_window"] == "intraday"
    assert get_ticker_signal("EXPD")["action_window"] == "intraday"


def test_intraday_news_swing_pick_is_marked_watch_only():
    pick = {
        "ticker": "EXPD",
        "scores": {"momentum": 0.4, "volume": 0.4, "trend": 0.7},
        "news": {"action_window": "intraday"},
        "plan": {},
    }

    ttype = main._safe_trade_type_for_pick(pick["scores"], pick_date="2026-05-05")
    assert ttype == "swing"

    # Lock expected policy text in main.py until this guard is promoted into
    # a smaller pure helper.
    text = open("main.py").read()
    assert "intraday news must not silently become a normal" in text
    assert 'p["watch_only"] = True' in text
