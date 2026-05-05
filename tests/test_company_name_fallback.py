"""Bug #6: company-name fallback must not persist ticker as fake company name."""

from unittest.mock import Mock


def test_fetch_info_falls_back_to_blank_company_name(monkeypatch):
    from src import data_fetcher

    fake_ticker = Mock()
    fake_ticker.fast_info.last_price = 100
    fake_ticker.fast_info.ten_day_average_volume = 1_000_000
    fake_ticker.fast_info.market_cap = 1_000_000_000
    fake_ticker.info = {"longName": "FAKE", "shortName": "FAKE"}

    monkeypatch.setattr(data_fetcher.yf, "Ticker", lambda *args, **kwargs: fake_ticker)
    monkeypatch.setattr(data_fetcher, "HAS_FINNHUB", False)

    info = data_fetcher.fetch_info("FAKE")

    assert info["name"] == ""
    assert info["shortName"] == ""
    assert info["longName"] is None


def test_fetch_info_uses_real_company_name(monkeypatch):
    from src import data_fetcher

    fake_ticker = Mock()
    fake_ticker.fast_info.last_price = 200
    fake_ticker.fast_info.ten_day_average_volume = 1_000_000
    fake_ticker.fast_info.market_cap = 2_000_000_000
    fake_ticker.info = {"longName": "Example Technologies Inc.", "shortName": "EX"}

    monkeypatch.setattr(data_fetcher.yf, "Ticker", lambda *args, **kwargs: fake_ticker)
    monkeypatch.setattr(data_fetcher, "HAS_FINNHUB", False)

    info = data_fetcher.fetch_info("EX")

    assert info["name"] == "Example Technologies Inc."
    assert info["shortName"] == "Example Technologies Inc."
    assert info["longName"] == "Example Technologies Inc."


def test_parallel_scorer_info_short_name_does_not_fall_back_to_ticker(monkeypatch):
    from src import parallel_scorer as ps

    monkeypatch.setattr(ps, "add_indicators", lambda df: df)
    monkeypatch.setattr(ps, "latest_signals", lambda df: {
        "close": 100,
        "atr_14": 2,
        "vol_ratio": 1.2,
    })
    monkeypatch.setattr(ps, "fetch_info", lambda tk: {
        "name": "",
        "longName": None,
        "shortName": "",
        "sector": "Technology",
        "currentPrice": 100,
        "averageVolume": 1_000_000,
    })
    monkeypatch.setattr(ps, "passes_filters", lambda info, cfg: True)
    monkeypatch.setattr(ps, "score_fundamentals", lambda info: 0.5)
    monkeypatch.setattr(ps, "fetch_news", lambda tk, limit=5: [])
    monkeypatch.setattr(ps, "score_sentiment", lambda news: 0.5)
    monkeypatch.setattr(ps, "composite_score", lambda *args, **kwargs: {
        "composite": 0.9,
        "sector_tag": "TECH",
    })
    monkeypatch.setattr(ps, "watchlist_score_boost", lambda tk: 0)
    monkeypatch.setattr(ps, "day_trading_score", lambda sig, news_boost=0: {
        "day_score": 0.1,
        "day_reason": "",
        "day_components": {},
    })
    monkeypatch.setattr(ps, "classify_with_day_score", lambda scores, day_score, sig=None: "swing")
    monkeypatch.setattr(ps, "atr_trade_plan", lambda *args, **kwargs: {
        "entry": 100,
        "stop_loss": 95,
        "take_profit": 110,
        "trade_type": "swing",
    })
    monkeypatch.setattr(ps, "score_monster", lambda **kwargs: {
        "monster_score": 0.0,
        "monster_reasons": [],
        "is_monster": False,
    })
    monkeypatch.setattr(ps, "get_monster_data", lambda tk: {})
    monkeypatch.setattr(ps, "_d2e", lambda tk: 30)
    monkeypatch.setattr(ps, "_build_signals", lambda pick: {})
    monkeypatch.setattr(ps, "_wisdom_consult", lambda tk, signals: {
        "warnings": [],
        "boosts": [],
        "kill": None,
        "score_adj": 0.0,
    })

    cfg = {
        "output": {"min_score": 0.1},
        "weights": {},
        "risk": {"capital": 10_000},
        "monster": {"fetch_short_float": False},
        "_regime": "bull",
    }

    result = ps._score_one("FAKE", object(), cfg)

    assert result is not None
    assert result["ticker"] == "FAKE"
    assert result["info_short"]["name"] == ""
    assert result["info_short"]["sector"] == "Technology"
