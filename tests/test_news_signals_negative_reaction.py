import json
from datetime import datetime, timedelta, timezone

from src import news_signals


def _item(headline, category="guidance_raise", ticker="EVC", score=0.9, sentiment="bullish"):
    return {
        "headline": headline,
        "summary": "",
        "classification": {
            "primary_ticker": ticker,
            "category": category,
            "sentiment": sentiment,
            "tradeable_score": score,
            "action_window": "swing",
        },
    }


def test_negative_reaction_helper_detects_sold_good_news():
    assert news_signals._has_negative_reaction("EVC shares fall despite guidance raise")
    assert news_signals._has_negative_reaction("Company beats estimates, stock drops after report")
    assert not news_signals._has_negative_reaction("Company raises guidance after strong quarter")


def test_negative_reaction_fades_bullish_signal_to_small_penalty(tmp_path, monkeypatch):
    path = tmp_path / "news_signals.json"
    monkeypatch.setattr(news_signals, "SIGNALS_PATH", path)

    sig = news_signals.add_signal_from_classification(
        _item("EVC shares fall despite guidance raise")
    )

    assert sig is not None
    assert sig["ticker"] == "EVC"
    assert sig["catalyst"] == "guidance_raise"
    assert sig["negative_reaction"] is True
    assert sig["score_delta"] < 0
    assert sig["score_delta"] >= -0.03

    saved = json.loads(path.read_text())
    assert saved["EVC"]["negative_reaction"] is True


def test_clean_bullish_signal_keeps_positive_boost(tmp_path, monkeypatch):
    path = tmp_path / "news_signals.json"
    monkeypatch.setattr(news_signals, "SIGNALS_PATH", path)

    sig = news_signals.add_signal_from_classification(
        _item("EVC raises full-year guidance after strong demand")
    )

    assert sig is not None
    assert sig["negative_reaction"] is False
    assert sig["score_delta"] > 0


def test_negative_reaction_does_not_weaken_bearish_penalty(tmp_path, monkeypatch):
    path = tmp_path / "news_signals.json"
    monkeypatch.setattr(news_signals, "SIGNALS_PATH", path)

    sig = news_signals.add_signal_from_classification(
        _item(
            "EVC shares fall after guidance cut",
            category="guidance_cut",
            sentiment="bearish",
        )
    )

    assert sig is not None
    assert sig["score_delta"] < 0
    assert sig["negative_reaction"] is True


def test_hard_block_still_wins_over_negative_reaction(tmp_path, monkeypatch):
    path = tmp_path / "news_signals.json"
    monkeypatch.setattr(news_signals, "SIGNALS_PATH", path)

    sig = news_signals.add_signal_from_classification({
        "headline": "EVC shares fall after company warns about going concern",
        "summary": "",
        "classification": {
            "primary_ticker": "EVC",
            "category": "guidance_raise",
            "sentiment": "bullish",
            "tradeable_score": 0.9,
        },
    })

    assert sig is not None
    assert sig["hard_block"] is True
    assert sig["score_delta"] == -1.0
    assert sig["catalyst"] == "BANKRUPTCY_RISK"
