"""Vectorized RSI mean-reversion backtest."""
import pandas as pd
from .indicators import add_indicators

pd.set_option("future.no_silent_downcasting", True)


def backtest_simple(df: pd.DataFrame, rsi_buy: float = 35,
                    rsi_sell: float = 70) -> dict:
    if df.empty or len(df) < 50:
        return {}
    d = add_indicators(df).dropna()
    if d.empty:
        return {}
    d["signal"] = 0
    d.loc[d["rsi_14"] < rsi_buy, "signal"] = 1
    d.loc[d["rsi_14"] > rsi_sell, "signal"] = -1
    d["position"] = (d["signal"].replace(0, pd.NA)
                     .ffill().fillna(0).infer_objects(copy=False).astype(float))
    d["ret"] = d["close"].pct_change().fillna(0)
    d["strategy_ret"] = d["position"].shift(1).fillna(0) * d["ret"]
    total_return = (1 + d["strategy_ret"]).prod() - 1
    win_rate = (d["strategy_ret"] > 0).sum() / max((d["strategy_ret"] != 0).sum(), 1)
    sharpe = (d["strategy_ret"].mean() / d["strategy_ret"].std() * (252 ** 0.5)) \
             if d["strategy_ret"].std() else 0
    cum = (1 + d["strategy_ret"]).cumprod()
    max_dd = (cum.cummax() - cum).max()
    return {
        "total_return_pct": round(total_return * 100, 2),
        "win_rate_pct": round(win_rate * 100, 2),
        "sharpe": round(sharpe, 2),
        "max_drawdown_pct": round(max_dd * 100, 2),
        "trades": int((d["signal"] != 0).sum()),
    }
