"""Smoke tests — run with: pytest -v"""
import pandas as pd
import numpy as np
from src.scorer import composite_score, score_trend, score_momentum, sector_bonus
from src.risk_manager import position_size, trade_plan
from src.semiconductors import is_semi, get_semi_tickers, get_semi_meta
from src.indicators import add_indicators, latest_signals
from src.fundamentals import score_fundamentals

def _fake_df(n=120):
    np.random.seed(0)
    price = 100 + np.cumsum(np.random.randn(n))
    return pd.DataFrame({
        "open": price, "high": price + 1, "low": price - 1,
        "close": price, "volume": np.random.randint(1e6, 5e6, n),
    })

def test_semi_lookup():
    assert is_semi("NVDA")
    assert not is_semi("JPM")
    assert "NVDA" in get_semi_tickers()
    assert get_semi_meta("NVDA")["ai_weight"] == 1.0

def test_indicators_run():
    df = add_indicators(_fake_df())
    sig = latest_signals(df)
    assert sig["close"] is not None
    assert sig["rsi_14"] is not None

def test_scorer_bounds():
    sig = {"close": 100, "sma_20": 99, "sma_50": 98, "sma_200": 95,
           "rsi_14": 55, "macd": 1, "macd_signal": 0.5, "macd_hist": 0.5,
           "atr_14": 2, "vol_ratio": 1.5}
    weights = {"trend": 0.25, "momentum": 0.20, "volatility": 0.10,
               "volume": 0.15, "fundamentals": 0.15, "sentiment": 0.15}
    s = composite_score(sig, 0.7, 0.6, weights,
                        ticker="NVDA", sector_cfg={"semi_boost": 1.10, "ai_boost": 0.20})
    assert 0 <= s["composite"] <= 1
    assert s["sector_mult"] > 1.0

def test_sector_bonus_non_semi():
    b = sector_bonus("JPM", {"semi_boost": 1.10, "ai_boost": 0.20})
    assert b["multiplier"] == 1.0

def test_position_size():
    qty = position_size(10000, 1.0, 100, 95)
    assert qty == 20

def test_trade_plan():
    sig = {"close": 100, "atr_14": 2}
    cfg = {"risk": {"account_size": 10000, "risk_per_trade_pct": 1.0,
                    "stop_loss_atr_mult": 1.5, "take_profit_atr_mult": 3.0}}
    p = trade_plan(sig, cfg)
    assert p["entry"] == 100
    assert p["stop_loss"] == 97.0
    assert p["take_profit"] == 106.0
    assert p["risk_reward"] == 2.0

def test_fundamentals_neutral():
    assert score_fundamentals({}) == 0.5
