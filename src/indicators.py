"""Technical indicators using the `ta` library."""
import pandas as pd
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 50:
        return df
    out = df.copy()
    out["sma_20"]  = SMAIndicator(out["close"], window=20).sma_indicator()
    out["sma_50"]  = SMAIndicator(out["close"], window=50).sma_indicator()
    out["sma_200"] = SMAIndicator(out["close"], window=200).sma_indicator()
    out["ema_9"]   = EMAIndicator(out["close"], window=9).ema_indicator()
    out["ema_21"]  = EMAIndicator(out["close"], window=21).ema_indicator()
    out["rsi_14"]  = RSIIndicator(out["close"], window=14).rsi()
    macd = MACD(out["close"], window_slow=26, window_fast=12, window_sign=9)
    out["macd"]        = macd.macd()
    out["macd_signal"] = macd.macd_signal()
    out["macd_hist"]   = macd.macd_diff()
    bb = BollingerBands(out["close"], window=20, window_dev=2)
    out["bb_upper"] = bb.bollinger_hband()
    out["bb_lower"] = bb.bollinger_lband()
    out["bb_mid"]   = bb.bollinger_mavg()
    out["atr_14"]   = AverageTrueRange(out["high"], out["low"], out["close"], window=14).average_true_range()
    out["vol_sma_20"] = SMAIndicator(out["volume"], window=20).sma_indicator()
    out["vol_ratio"]  = out["volume"] / out["vol_sma_20"]
    return out

def latest_signals(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last
    def safe(v):
        try:    return float(v)
        except: return None
    return {
        "close":       safe(last.get("close")),
        "sma_20":      safe(last.get("sma_20")),
        "sma_50":      safe(last.get("sma_50")),
        "sma_200":     safe(last.get("sma_200")),
        "ema_9":       safe(last.get("ema_9")),
        "ema_21":      safe(last.get("ema_21")),
        "rsi_14":      safe(last.get("rsi_14")),
        "macd":        safe(last.get("macd")),
        "macd_signal": safe(last.get("macd_signal")),
        "macd_hist":   safe(last.get("macd_hist")),
        "bb_upper":    safe(last.get("bb_upper")),
        "bb_lower":    safe(last.get("bb_lower")),
        "atr_14":      safe(last.get("atr_14")),
        "vol_ratio":   safe(last.get("vol_ratio")),
        "prev_close":  safe(prev.get("close")),
    }
