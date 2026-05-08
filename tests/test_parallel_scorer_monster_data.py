"""Tests for Daily Picks monster-data enrichment pressure controls."""
import pandas as pd


def _df():
    return pd.DataFrame({
        "Open": [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
        "High": [11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25],
        "Low": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
        "Close": [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24],
        "Volume": [1_000_000] * 15,
    })


def _cfg(monster=None):
    return {
        "output": {"min_score": 0.0},
        "weights": {},
        "sector": {},
        "risk": {"capital": 10000},
        "monster": monster or {},
    }


def _patch_common(monkeypatch, ps):
    monkeypatch.setattr(ps, "add_indicators", lambda df: df)
    monkeypatch.setattr(ps, "latest_signals", lambda df: {
        "close": 24,
        "atr_14": 1.0,
        "vol_ratio": 1.2,
    })
    monkeypatch.setattr(ps, "fetch_info", lambda tk: {
        "name": "Example Corp",
        "sector": "Technology",
        "marketCap": 1_000_000_000,
        "avg_daily_volume": 1_000_000,
        "price": 24,
    })
    monkeypatch.setattr(ps, "passes_filters", lambda info, cfg: True)
    monkeypatch.setattr(ps, "score_fundamentals", lambda info: {"fundamental_score": 0.8})
    monkeypatch.setattr(ps, "fetch_news", lambda tk, limit=5: [])
    monkeypatch.setattr(ps, "score_sentiment", lambda news: {"sentiment": "neutral", "score": 0.5})
    monkeypatch.setattr(ps, "composite_score", lambda *a, **k: {"composite": 0.9, "sector_tag": "TECH"})
    monkeypatch.setattr(ps, "watchlist_score_boost", lambda tk: 0.0)
    monkeypatch.setattr(ps, "day_trading_score", lambda sig, news_boost=0: {
        "day_score": 0.2,
        "day_reason": "test",
        "day_components": {},
    })
    monkeypatch.setattr(ps, "classify_with_day_score", lambda scores, day_score, sig=None: "swing")
    monkeypatch.setattr(ps, "atr_trade_plan", lambda price, atr, capital, trade_type, regime: {
        "entry": price,
        "stop_loss": price - atr,
        "take_profit": price + atr * 2,
        "risk_reward": 2.0,
        "quantity": 1,
        "trade_type": trade_type,
        "regime": regime,
    })
    monkeypatch.setattr(ps, "_d2e", lambda tk: 30)
    monkeypatch.setattr(ps, "_wisdom_consult", lambda tk, signals: {
        "warnings": [],
        "boosts": [],
        "kill": False,
        "score_adj": 0.0,
    })
    monkeypatch.setattr(ps, "_build_signals", lambda row: {})


def test_monster_data_not_fetched_by_default(monkeypatch):
    import src.parallel_scorer as ps

    _patch_common(monkeypatch, ps)
    calls = []

    def fake_get_monster_data(tk):
        calls.append(tk)
        return {"short_pct_of_float": 10.0, "float_shares": 1_000_000}

    monkeypatch.setattr(ps, "get_monster_data", fake_get_monster_data)
    monkeypatch.setattr(ps, "score_monster", lambda **kwargs: {
        "monster_score": 0.0,
        "monster_reasons": [],
        "is_monster": False,
    })

    result = ps._score_one("AAPL", _df(), _cfg())

    assert result is not None
    assert calls == []


def test_monster_data_fetch_is_explicit_opt_in(monkeypatch):
    import src.parallel_scorer as ps

    _patch_common(monkeypatch, ps)
    calls = []

    def fake_get_monster_data(tk):
        calls.append(tk)
        return {"short_pct_of_float": 10.0, "float_shares": 1_000_000}

    monkeypatch.setattr(ps, "get_monster_data", fake_get_monster_data)
    monkeypatch.setattr(ps, "score_monster", lambda **kwargs: {
        "monster_score": 0.5,
        "monster_reasons": ["test"],
        "is_monster": False,
    })

    result = ps._score_one("AAPL", _df(), _cfg({"fetch_short_float": True}))

    assert result is not None
    assert calls == ["AAPL"]
