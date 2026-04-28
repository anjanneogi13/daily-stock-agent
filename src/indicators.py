"""Technical indicators — full suite for stock analysis."""
import pandas as pd
import numpy as np


# ============================================================
# CORE INDICATORS
# ============================================================

def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    sig_line = ema(macd_line, signal)
    hist = macd_line - sig_line
    return macd_line, sig_line, hist


def bollinger(series: pd.Series, period: int = 20, std: float = 2.0):
    mid = sma(series, period)
    sd = series.rolling(period).std()
    return mid + std * sd, mid, mid - std * sd


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


# ============================================================
# ADDITIONAL INDICATORS
# ============================================================

def stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3):
    low_min = df["low"].rolling(k_period).min()
    high_max = df["high"].rolling(k_period).max()
    k = 100 * (df["close"] - low_min) / (high_max - low_min).replace(0, np.nan)
    d = k.rolling(d_period).mean()
    return k, d


def obv(df: pd.DataFrame) -> pd.Series:
    direction = np.sign(df["close"].diff()).fillna(0)
    return (direction * df["volume"]).cumsum()


def parabolic_sar(df: pd.DataFrame, af_start: float = 0.02,
                  af_step: float = 0.02, af_max: float = 0.20) -> pd.Series:
    high, low = df["high"].values, df["low"].values
    n = len(df)
    sar = np.zeros(n)
    trend = 1
    af = af_start
    ep = high[0]
    sar[0] = low[0]
    for i in range(1, n):
        sar[i] = sar[i-1] + af * (ep - sar[i-1])
        if trend == 1:
            sar[i] = min(sar[i], low[i-1], low[max(i-2, 0)])
            if low[i] < sar[i]:
                trend = -1; sar[i] = ep; ep = low[i]; af = af_start
            elif high[i] > ep:
                ep = high[i]; af = min(af + af_step, af_max)
        else:
            sar[i] = max(sar[i], high[i-1], high[max(i-2, 0)])
            if high[i] > sar[i]:
                trend = 1; sar[i] = ep; ep = high[i]; af = af_start
            elif low[i] < ep:
                ep = low[i]; af = min(af + af_step, af_max)
    return pd.Series(sar, index=df.index)


def vwap(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Rolling Volume-Weighted Average Price."""
    typical = (df["high"] + df["low"] + df["close"]) / 3.0
    pv = (typical * df["volume"]).rolling(period).sum()
    v = df["volume"].rolling(period).sum()
    return pv / v.replace(0, np.nan)


def adx(df: pd.DataFrame, period: int = 14):
    """ADX (trend strength), +DI, -DI. >25 = strong trend."""
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    up_move = high.diff()
    down_move = -low.diff()
    plus_dm = ((up_move > down_move) & (up_move > 0)).astype(float) * up_move
    minus_dm = ((down_move > up_move) & (down_move > 0)).astype(float) * down_move
    atr_w = tr.ewm(alpha=1/period, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr_w.replace(0, np.nan)
    minus_di = 100 * minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr_w.replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx_line = dx.ewm(alpha=1/period, adjust=False).mean()
    return adx_line, plus_di, minus_di


def candlestick_patterns(df: pd.DataFrame) -> dict:
    if len(df) < 3:
        return {}
    last, prev, prev2 = df.iloc[-1], df.iloc[-2], df.iloc[-3]
    o, h, l, c = float(last["open"]), float(last["high"]), float(last["low"]), float(last["close"])
    po, pc = float(prev["open"]), float(prev["close"])
    body = abs(c - o)
    rng = max(h - l, 1e-9)
    upper_wick = h - max(c, o)
    lower_wick = min(c, o) - l

    p = {
        "bullish_engulfing": (pc < po) and (c > o) and (c >= po) and (o <= pc),
        "bearish_engulfing": (pc > po) and (c < o) and (c <= po) and (o >= pc),
        "hammer": (lower_wick >= 2 * body) and (upper_wick <= body) and (c > o),
        "shooting_star": (upper_wick >= 2 * body) and (lower_wick <= body) and (c < o),
        "doji": body / rng < 0.1,
        "morning_star": (
            float(prev2["close"]) < float(prev2["open"])
            and abs(pc - po) / max(float(prev["high"]) - float(prev["low"]), 1e-9) < 0.3
            and c > o and c > (float(prev2["open"]) + float(prev2["close"])) / 2
        ),
        "evening_star": (
            float(prev2["close"]) > float(prev2["open"])
            and abs(pc - po) / max(float(prev["high"]) - float(prev["low"]), 1e-9) < 0.3
            and c < o and c < (float(prev2["open"]) + float(prev2["close"])) / 2
        ),
    }
    p["bullish_signal"] = any(p[k] for k in ["bullish_engulfing", "hammer", "morning_star"])
    p["bearish_signal"] = any(p[k] for k in ["bearish_engulfing", "shooting_star", "evening_star"])
    return p


def fibonacci_levels(df: pd.DataFrame, lookback: int = 60) -> dict:
    recent = df.tail(lookback)
    swing_high = float(recent["high"].max())
    swing_low = float(recent["low"].min())
    diff = swing_high - swing_low
    return {
        "fib_0": swing_low,
        "fib_236": swing_low + 0.236 * diff,
        "fib_382": swing_low + 0.382 * diff,
        "fib_50": swing_low + 0.500 * diff,
        "fib_618": swing_low + 0.618 * diff,
        "fib_786": swing_low + 0.786 * diff,
        "fib_100": swing_high,
    }


def support_resistance(df: pd.DataFrame, lookback: int = 60, window: int = 5) -> dict:
    recent = df.tail(lookback)
    highs, lows = recent["high"], recent["low"]
    res_levels, sup_levels = [], []
    for i in range(window, len(recent) - window):
        if highs.iloc[i] == highs.iloc[i-window:i+window+1].max():
            res_levels.append(highs.iloc[i])
        if lows.iloc[i] == lows.iloc[i-window:i+window+1].min():
            sup_levels.append(lows.iloc[i])
    close = float(df["close"].iloc[-1])
    above = [r for r in res_levels if r > close]
    below = [s for s in sup_levels if s < close]
    nearest_res = float(min(above)) if above else float(highs.max())
    nearest_sup = float(max(below)) if below else float(lows.min())
    return {
        "support": nearest_sup,
        "resistance": nearest_res,
        "distance_to_support_pct": round((close / nearest_sup - 1) * 100, 2),
        "distance_to_resistance_pct": round((nearest_res / close - 1) * 100, 2),
    }


# ============================================================
# COMPOSITE
# ============================================================

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    d = df.copy()
    c = d["close"]

    d["sma_20"] = sma(c, 20)
    d["sma_50"] = sma(c, 50)
    d["sma_200"] = sma(c, 200)
    d["ema_9"] = ema(c, 9)
    d["ema_21"] = ema(c, 21)

    d["rsi_14"] = rsi(c, 14)
    macd_line, sig_line, hist = macd(c)
    d["macd"], d["macd_signal"], d["macd_hist"] = macd_line, sig_line, hist

    bb_up, bb_mid, bb_low = bollinger(c)
    d["bb_upper"], d["bb_middle"], d["bb_lower"] = bb_up, bb_mid, bb_low
    d["atr_14"] = atr(d, 14)

    k, dl = stochastic(d)
    d["stoch_k"], d["stoch_d"] = k, dl

    d["obv"] = obv(d)
    d["obv_ema"] = ema(d["obv"], 20)

    try:
        d["psar"] = parabolic_sar(d)
    except Exception:
        d["psar"] = np.nan

    d["vwap_20"] = vwap(d)

    adx_line, plus_di, minus_di = adx(d)
    d["adx"], d["plus_di"], d["minus_di"] = adx_line, plus_di, minus_di

    d["vol_sma_20"] = sma(d["volume"], 20)
    d["vol_ratio"] = d["volume"] / d["vol_sma_20"]

    return d


def latest_signals(df: pd.DataFrame) -> dict:
    if df.empty:
        return {}
    last = df.iloc[-1]
    close = float(last["close"])

    def _f(col):
        v = last.get(col)
        return float(v) if pd.notna(v) else None

    out = {
        "close": close,
        "prev_close": float(df["close"].iloc[-2]) if len(df) > 1 else close,
        "sma_20": _f("sma_20"), "sma_50": _f("sma_50"), "sma_200": _f("sma_200"),
        "ema_9": _f("ema_9"), "ema_21": _f("ema_21"),
        "rsi_14": _f("rsi_14"),
        "macd": _f("macd"), "macd_signal": _f("macd_signal"), "macd_hist": _f("macd_hist"),
        "bb_upper": _f("bb_upper"), "bb_middle": _f("bb_middle"), "bb_lower": _f("bb_lower"),
        "atr_14": _f("atr_14"),
        "vol_ratio": _f("vol_ratio"),
        "stoch_k": _f("stoch_k"), "stoch_d": _f("stoch_d"),
        "obv": _f("obv"), "obv_ema": _f("obv_ema"),
        "psar": _f("psar"),
        "vwap_20": _f("vwap_20"),
        "adx": _f("adx"), "plus_di": _f("plus_di"), "minus_di": _f("minus_di"),
    }

    # Derived flags
    if out["bb_upper"] and out["bb_lower"]:
        bb_range = out["bb_upper"] - out["bb_lower"]
        out["bb_position"] = (close - out["bb_lower"]) / bb_range if bb_range else 0.5
    else:
        out["bb_position"] = 0.5

    out["above_psar"] = (out["psar"] is not None and close > out["psar"])
    out["stoch_oversold"] = (out["stoch_k"] is not None and out["stoch_k"] < 20)
    out["stoch_overbought"] = (out["stoch_k"] is not None and out["stoch_k"] > 80)
    out["obv_rising"] = (out["obv"] is not None and out["obv_ema"] is not None
                        and out["obv"] > out["obv_ema"])

    # ADX trend strength
    out["strong_trend"] = (out["adx"] is not None and out["adx"] > 25)
    out["di_bullish"] = (out["plus_di"] is not None and out["minus_di"] is not None
                         and out["plus_di"] > out["minus_di"])

    # VWAP position
    if out["vwap_20"]:
        out["above_vwap"] = close > out["vwap_20"]
        out["vwap_distance_pct"] = round((close / out["vwap_20"] - 1) * 100, 2)
    else:
        out["above_vwap"] = False
        out["vwap_distance_pct"] = 0

    # Candlestick patterns
    try:
        patterns = candlestick_patterns(df)
        out.update({f"cdl_{k}": v for k, v in patterns.items()})
    except Exception:
        pass

    # Fibonacci + Support/Resistance
    try:
        out.update(fibonacci_levels(df))
        out.update(support_resistance(df))
    except Exception:
        pass

    return out
