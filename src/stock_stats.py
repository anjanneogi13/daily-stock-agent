"""
Pillar 1 (Probability Engine) — Layer 1: Per-Stock Statistical Foundation

Computes empirical statistics for each stock in the universe:
  • Return distributions (1d, 5d, 10d, 20d) — mean, std, percentiles
  • Volatility (rolling 20/60/180 day windows)
  • ATR at multiple windows
  • Drawdown profiles
  • Bounce-back rates from drawdowns

These statistics REPLACE arbitrary thresholds (1.5×ATR, RSI 30, 3% SL)
with empirically-derived probability-based decisions.

See: docs/PROBABILITY_ENGINE_DESIGN.md
See: docs/BRAIN_ARCHITECTURE.md (Pillar 1)
See: docs/decisions/ADR-001-probability-over-rules.md
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

try:
    import yfinance as yf
    YF_OK = True
except ImportError:
    YF_OK = False

# ─── Configuration ─────────────────────────────────────────────────
STATS_DIR = Path("data/stock_stats")
HISTORY_DAYS = 365 * 2  # 2 years of daily history
RETURN_WINDOWS = [1, 5, 10, 20]  # forward-return periods (days)
VOL_WINDOWS = [20, 60, 180]  # rolling volatility windows (days)
PERCENTILES = [5, 10, 25, 50, 75, 90, 95]  # for noise-band analysis


# ─── Core computation functions ────────────────────────────────────

def _fetch_history(ticker: str, days: int = HISTORY_DAYS) -> Optional[pd.DataFrame]:
    """Fetch OHLCV history. Returns None on failure."""
    if not YF_OK:
        return None
    try:
        end = datetime.now()
        start = end - timedelta(days=days)
        df = yf.Ticker(ticker).history(
            start=start.strftime("%Y-%m-%d"),
            end=end.strftime("%Y-%m-%d"),
            auto_adjust=False,
        )
        if df.empty or len(df) < 60:
            return None
        df = df.rename(columns=str.lower)  # close/open/high/low/volume
        return df
    except Exception:
        return None


def _compute_returns(df: pd.DataFrame) -> Dict:
    """
    Compute forward-return distributions for each window.
    Returns: {window_days: {mean, std, p5, p10, p25, p50, p75, p90, p95, n}}
    """
    out = {}
    closes = df["close"].values
    for w in RETURN_WINDOWS:
        if len(closes) <= w:
            continue
        # Forward return: (price[t+w] - price[t]) / price[t]
        rets = (closes[w:] - closes[:-w]) / closes[:-w]
        rets = rets[~np.isnan(rets)]
        if len(rets) < 30:
            continue
        stats = {
            "n": int(len(rets)),
            "mean_pct": round(float(np.mean(rets)) * 100, 4),
            "std_pct": round(float(np.std(rets)) * 100, 4),
            "skew": round(float(pd.Series(rets).skew()), 4),
            "kurtosis": round(float(pd.Series(rets).kurtosis()), 4),
        }
        for p in PERCENTILES:
            stats[f"p{p}_pct"] = round(float(np.percentile(rets, p)) * 100, 4)
        out[f"{w}d"] = stats
    return out


def _compute_volatility(df: pd.DataFrame) -> Dict:
    """Rolling annualized volatility for each window."""
    out = {}
    daily_rets = df["close"].pct_change().dropna()
    if len(daily_rets) < 20:
        return out
    for w in VOL_WINDOWS:
        if len(daily_rets) < w:
            continue
        rolling_std = daily_rets.rolling(w).std().dropna()
        if rolling_std.empty:
            continue
        out[f"{w}d"] = {
            "current_pct": round(float(rolling_std.iloc[-1]) * 100, 4),
            "median_pct": round(float(rolling_std.median()) * 100, 4),
            "p25_pct": round(float(rolling_std.quantile(0.25)) * 100, 4),
            "p75_pct": round(float(rolling_std.quantile(0.75)) * 100, 4),
            "annualized_pct": round(float(rolling_std.iloc[-1]) * np.sqrt(252) * 100, 4),
        }
    return out


def _compute_atr(df: pd.DataFrame) -> Dict:
    """Average True Range at multiple windows (as % of price)."""
    out = {}
    h, l, c = df["high"].values, df["low"].values, df["close"].values
    if len(c) < 30:
        return out
    prev_c = np.roll(c, 1)
    prev_c[0] = c[0]
    tr = np.maximum.reduce([h - l, np.abs(h - prev_c), np.abs(l - prev_c)])
    for w in [14, 30, 60]:
        if len(tr) < w:
            continue
        atr = pd.Series(tr).rolling(w).mean().iloc[-1]
        atr_pct = (atr / c[-1]) * 100
        out[f"{w}d"] = {
            "atr_abs": round(float(atr), 4),
            "atr_pct": round(float(atr_pct), 4),
        }
    return out


def _compute_drawdowns(df: pd.DataFrame) -> Dict:
    """Drawdown statistics: typical depth, recovery time."""
    closes = df["close"].values
    if len(closes) < 60:
        return {}
    rolling_max = pd.Series(closes).cummax()
    drawdowns = (closes - rolling_max) / rolling_max
    dd = drawdowns[drawdowns < -0.01]  # ignore flat periods
    if len(dd) < 10:
        return {}
    return {
        "current_pct": round(float(drawdowns.iloc[-1]) * 100, 4),
        "max_pct": round(float(drawdowns.min()) * 100, 4),
        "median_pct": round(float(dd.median()) * 100, 4),
        "p10_pct": round(float(np.percentile(dd, 10)) * 100, 4),
        "p25_pct": round(float(np.percentile(dd, 25)) * 100, 4),
    }


def _compute_bounce_rates(df: pd.DataFrame) -> Dict:
    """
    For each drawdown level, what % of time did price recover within N days?
    Answers: "If NVDA drops 3%, P(recovery in 5 days) = ?"
    """
    closes = df["close"].values
    if len(closes) < 100:
        return {}
    daily_rets = pd.Series(closes).pct_change()
    out = {}
    for drop_pct in [1, 2, 3, 5]:
        # Find days where stock dropped by this %
        drop_days = np.where(daily_rets <= -drop_pct / 100)[0]
        if len(drop_days) < 5:
            continue
        recovered_5d = 0
        recovered_10d = 0
        for d in drop_days:
            base = closes[d]
            # Did it recover (cross prior peak) within 5/10 days?
            prior_peak = closes[max(0, d - 5):d].max() if d >= 5 else base
            window_5 = closes[d + 1:min(len(closes), d + 6)]
            window_10 = closes[d + 1:min(len(closes), d + 11)]
            if len(window_5) > 0 and window_5.max() >= prior_peak:
                recovered_5d += 1
            if len(window_10) > 0 and window_10.max() >= prior_peak:
                recovered_10d += 1
        out[f"drop_{drop_pct}pct"] = {
            "n_occurrences": int(len(drop_days)),
            "p_recover_5d": round(recovered_5d / len(drop_days), 4),
            "p_recover_10d": round(recovered_10d / len(drop_days), 4),
        }
    return out


# ─── Main public API ───────────────────────────────────────────────

def compute_stock_stats(ticker: str) -> Optional[Dict]:
    """
    Compute complete statistical profile for a stock.
    Returns None on data fetch failure.
    """
    df = _fetch_history(ticker)
    if df is None:
        return None
    
    current_price = float(df["close"].iloc[-1])
    
    profile = {
        "ticker": ticker.upper(),
        "computed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_start": df.index[0].strftime("%Y-%m-%d"),
        "data_end": df.index[-1].strftime("%Y-%m-%d"),
        "n_days": len(df),
        "current_price": round(current_price, 4),
        "returns": _compute_returns(df),
        "volatility": _compute_volatility(df),
        "atr": _compute_atr(df),
        "drawdowns": _compute_drawdowns(df),
        "bounce_rates": _compute_bounce_rates(df),
    }
    return profile


def save_stats(profile: Dict, base_dir: Path = STATS_DIR) -> Path:
    """Save stats to data/stock_stats/{TICKER}.json"""
    base_dir.mkdir(parents=True, exist_ok=True)
    path = base_dir / f"{profile['ticker']}.json"
    path.write_text(json.dumps(profile, indent=2))
    return path


def load_stats(ticker: str, base_dir: Path = STATS_DIR) -> Optional[Dict]:
    """Load saved stats for a ticker, or None if not yet computed."""
    path = base_dir / f"{ticker.upper()}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


# ─── Probability-based decision helpers (Pillar 1 deliverable) ─────

def empirical_sl_pct(ticker: str, target_p_noise: float = 0.30) -> Optional[float]:
    """
    Empirical SL based on stock's actual volatility distribution.
    
    Returns: SL % below entry where P(daily move ≤ -SL) ≈ target_p_noise
    
    Example: For NVDA, if daily moves ≤ -1.4% happen ~25% of time,
             SL of 1.4% means SL only triggered when in worst 25%.
    """
    stats = load_stats(ticker)
    if not stats or "returns" not in stats or "1d" not in stats["returns"]:
        return None
    r = stats["returns"]["1d"]
    
    # Available percentiles in our data: 5, 10, 25, 50, 75, 90, 95
    # User wants P(noise) = X% → interpolate to nearest available
    available = [5, 10, 25, 50, 75, 90, 95]
    target_pct = int(round(target_p_noise * 100))
    
    # Find closest available percentile
    closest = min(available, key=lambda p: abs(p - target_pct))
    pct_key = f"p{closest}_pct"
    
    if pct_key not in r:
        return None
    
    val = r[pct_key]
    # Only meaningful if it's a downside (negative) percentile
    if val >= 0:
        return None
    return round(abs(val), 4)


def empirical_tp_pct(ticker: str, days: int = 5, target_p_reach: float = 0.50) -> Optional[float]:
    """
    Empirical TP based on what's reachable in N days with probability target.
    
    Returns: TP % above entry where P(forward return ≥ TP) ≈ target_p_reach
    
    Logic: P(return >= X) = target → X = quantile(1 - target)
           So target_p_reach=0.50 means we need the 50th percentile (median)
           target_p_reach=0.25 means we need the 75th percentile
    """
    stats = load_stats(ticker)
    if not stats or "returns" not in stats or f"{days}d" not in stats["returns"]:
        return None
    r = stats["returns"][f"{days}d"]
    
    # Quantile we need: 1 - target_p_reach
    needed_quantile = int(round((1 - target_p_reach) * 100))
    available = [5, 10, 25, 50, 75, 90, 95]
    closest = min(available, key=lambda p: abs(p - needed_quantile))
    pct_key = f"p{closest}_pct"
    
    if pct_key not in r:
        return None
    tp_pct = r[pct_key]
    if tp_pct <= 0:
        return None  # No positive TP achievable at this probability
    return round(tp_pct, 4)


# ─── CLI for quick testing ─────────────────────────────────────────

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    print(f"Computing stats for {ticker}...")
    profile = compute_stock_stats(ticker)
    if profile is None:
        print(f"❌ Failed to fetch data for {ticker}")
        sys.exit(1)
    path = save_stats(profile)
    print(f"✓ Saved to {path}")
    print(f"  Days of data: {profile['n_days']}")
    print(f"  Current price: ${profile['current_price']}")
    if "1d" in profile["returns"]:
        r1d = profile["returns"]["1d"]
        print(f"  Daily return p10/p50/p90: {r1d.get('p10_pct')}% / {r1d.get('p50_pct')}% / {r1d.get('p90_pct')}%")
    sl = empirical_sl_pct(ticker)
    tp = empirical_tp_pct(ticker, days=5)
    print(f"  Empirical SL (P_noise=30%): {sl}%")
    print(f"  Empirical TP (5d, P_reach=50%): {tp}%")