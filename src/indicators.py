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
# NEW INDICATORS
# ============================================================

def stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3):
    """Stochastic Oscillator (%K and %D). 0-100 scale.
    >80 = overbought, <20 = oversold."""
    low_min = df["low"].rolling(k_period).min()
    high_max = df["high"].rolling(k_period).max()
    k = 100 * (df["close"] - low_min) / (high_max - low_min).replace(0, np.nan)
    d = k.rolling(d_period).mean()
    return k, d


def obv(df: pd.DataFrame) -> pd.Series:
    """On-Balance Volume. Cumulative volume weighted by price direction.
    Rising OBV = institutional accumulation."""
    direction = np.sign(df["close"].diff()).fillna(0)
    return (direction * df["volume"]).cumsum()


def parabolic_sar(df: pd.DataFrame, af_start: float = 0.02,
                  af_step: float = 0.02, af_max: float = 0.20) -> pd.Series:
    """Parabolic SAR — trend-following stop level.
    Price above SAR = uptrend; price below SAR = downtrend."""
    high, low = df["high"].values, df["low"].values
    n = len(df)
    sar = np.zeros(n)
    trend = 1  # 1 = up, -1 = down
    af = af_start
    ep = high[0]
    sar[0] = low[0]

    for i in range(1, n):
        sar[i] = sar[i-1] + af * (ep - sar[i-1])
        if trend == 1:
            sar[i] = min(sar[i], low[i-1], low[max(i-2, 0)])
            if low[i] < sar[i]:
                trend = -1
                sar[i] = ep
                ep = low[i]
                af = af_start
            elif high[i] > ep:
                ep = high[i]
                af = min(af + af_step, af_max)
        else:
            sar[i] = max(sar[i], high[i-1], high[max(i-2, 0)])
            if high[i] > sar[i]:
                trend = 1
                sar[i] = ep
                ep = high[i]
                af = af_start
            elif low[i] < ep:
                ep = low[i]
                af = min(af + af_step, af_max)
    return pd.Series(sar, index=df.index)


def fibonacci_levels(df: pd.DataFrame, lookback: int = 60) -> dict:
    """Fibonacci retracement levels from recent swing high/low."""
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


def support_resistance(df: pd.DataFrame, lookback: int = 60,
                        window: int = 5) -> dict:
    """Support = recent significant low; Resistance = recent significant high.
    Uses local extrema over `window` bars."""
    recent = df.tail(lookback)
    highs = recent["high"]
    lows = recent["low"]

    # Local maxima and minima
    res_levels = []
    sup_levels = []
    for i in range(window, len(recent) - window):
        if highs.iloc[i] == highs.iloc[i-window:i+window+1].max():
            res_levels.append(highs.iloc[i])
        if lows.iloc[i] == lows.iloc[i-window:i+window+1].min():
            sup_levels.append(lows.iloc[i])

    close = float(df["close"].iloc[-1])
    # Nearest resistance ABOVE current price
    above = [r for r in res_levels if r > close]
    nearest_resistance = float(min(above)) if above else float(highs.max())
    # Nearest support BELOW current price
    below = [s for s in sup_levels if s < close]
    nearest_support = float(max(below)) if below else float(lows.min())

    return {
        "support": nearest_support,
        "resistance": nearest_resistance,
        "distance_to_support_pct": round((close / nearest_support - 1) * 100, 2),
        "distance_to_resistance_pct": round((nearest_resistance / close - 1) * 100, 2),
    }


# ============================================================
# COMPOSITE: ADD ALL TO DATAFRAME
# ============================================================

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute and attach all indicators to the OHLCV dataframe."""
    if df.empty:
        return df
    d = df.copy()
    c = d["close"]

    # Moving averages
    d["sma_20"] = sma(c, 20)
    d["sma_50"] = sma(c, 50)
    d["sma_200"] = sma(c, 200)
    d["ema_9"] = ema(c, 9)
    d["ema_21"] = ema(c, 21)

    # Momentum
    d["rsi_14"] = rsi(c, 14)
    macd_line, sig_line, hist = macd(c)
    d["macd"], d["macd_signal"], d["macd_hist"] = macd_line, sig_line, hist

    # Volatility
    bb_up, bb_mid, bb_low = bollinger(c)
    d["bb_upper"], d["bb_middle"], d["bb_lower"] = bb_up, bb_mid, bb_low
    d["atr_14"] = atr(d, 14)

    # NEW: Stochastic
    k, dl = stochastic(d)
    d["stoch_k"], d["stoch_d"] = k, dl

    # NEW: OBV
    d["obv"] = obv(d)
    d["obv_ema"] = ema(d["obv"], 20)  # OBV trend

    # NEW: Parabolic SAR
    try:
        d["psar"] = parabolic_sar(d)
    except Exception:
        d["psar"] = np.nan

    # Volume
    d["vol_sma_20"] = sma(d["volume"], 20)
    d["vol_ratio"] = d["volume"] / d["vol_sma_20"]

    return d


def latest_signals(df: pd.DataFrame) -> dict:
    """Snapshot of latest indicator values + key derived signals."""
    if df.empty:
        return {}
    last = df.iloc[-1]
    close = float(last["close"])

    out = {
        "close": close,
        "prev_close": float(df["close"].iloc[-2]) if len(df) > 1 else close,
        "sma_20": float(last["sma_20"]) if pd.notna(last["sma_20"]) else None,
        "sma_50": float(last["sma_50"]) if pd.notna(last["sma_50"]) else None,
        "sma_200": float(last["sma_200"]) if pd.notna(last["sma_200"]) else None,
        "ema_9": float(last["ema_9"]) if pd.notna(last["ema_9"]) else None,
        "ema_21": float(last["ema_21"]) if pd.notna(last["ema_21"]) else None,
        "rsi_14": float(last["rsi_14"]) if pd.notna(last["rsi_14"]) else None,
        "macd": float(last["macd"]) if pd.notna(last["macd"]) else None,
        "macd_signal": float(last["macd_signal"]) if pd.notna(last["macd_signal"]) else None,
        "macd_hist": float(last["macd_hist"]) if pd.notna(last["macd_hist"]) else None,
        "bb_upper": float(last["bb_upper"]) if pd.notna(last["bb_upper"]) else None,
        "bb_middle": float(last["bb_middle"]) if pd.notna(last["bb_middle"]) else None,
        "bb_lower": float(last["bb_lower"]) if pd.notna(last["bb_lower"]) else None,
        "atr_14": float(last["atr_14"]) if pd.notna(last["atr_14"]) else None,
        "vol_ratio": float(last["vol_ratio"]) if pd.notna(last["vol_ratio"]) else None,
        # NEW
        "stoch_k": float(last["stoch_k"]) if pd.notna(last["stoch_k"]) else None,
        "stoch_d": float(last["stoch_d"]) if pd.notna(last["stoch_d"]) else None,
        "obv": float(last["obv"]) if pd.notna(last["obv"]) else None,
        "obv_ema": float(last["obv_ema"]) if pd.notna(last["obv_ema"]) else None,
        "psar": float(last["psar"]) if pd.notna(last["psar"]) else None,
    }

    # Derived signals (boolean flags + percentages for scoring)
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

    # Fibonacci + Support/Resistance (computed on full df)
    try:
        out.update(fibonacci_levels(df))
        out.update(support_resistance(df))
    except Exception:
        pass

    return out
