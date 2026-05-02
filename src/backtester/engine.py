"""Backtest orchestration engine.

Walks through historical days, slices data PIT, computes a simple
score, generates a pick, simulates the outcome.

Phase A: uses simple RSI+momentum scoring (no LLM, no news).
"""
from __future__ import annotations
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import List, Dict, Optional

from src.backtester.pit_data import slice_pit, get_forward_window
from src.backtester.outcome_simulator import simulate_outcome


def _simple_score(df_pit: pd.DataFrame) -> Optional[Dict]:
    """Simple price-only score (Phase A baseline).

    Reuses the same logic style as src/scorer.py but without LLM/news.
    Returns None if score < 0.5 (skip pick).
    """
    if df_pit is None or len(df_pit) < 60:
        return None

    closes = df_pit["Close"].values
    highs = df_pit["High"].values
    lows = df_pit["Low"].values

    last = float(closes[-1])

    # RSI(14)
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = gains[-14:].mean() if len(gains) >= 14 else 0
    avg_loss = losses[-14:].mean() if len(losses) >= 14 else 0
    rs = avg_gain / avg_loss if avg_loss > 0 else 100
    rsi = 100 - (100 / (1 + rs))

    # SMA20, SMA50
    sma20 = closes[-20:].mean()
    sma50 = closes[-50:].mean() if len(closes) >= 50 else sma20

    # ATR(14) for SL/TP sizing
    tr = np.maximum(highs[-15:] - lows[-15:],
                    np.maximum(np.abs(highs[-15:] - np.roll(closes, 1)[-15:]),
                               np.abs(lows[-15:] - np.roll(closes, 1)[-15:])))
    atr = float(tr[1:].mean())  # skip first (roll artifact)

    # Score logic (mirrors live scorer's simple components)
    score = 0.0
    if rsi < 35:
        score += 0.30  # oversold
    elif rsi < 50:
        score += 0.15
    if last > sma20:
        score += 0.20  # above short trend
    if last > sma50:
        score += 0.20  # above mid trend
    if sma20 > sma50:
        score += 0.15  # uptrend confirmed

    # Momentum
    pct_5d = (last - closes[-6]) / closes[-6] * 100 if len(closes) >= 6 else 0
    if 0 < pct_5d < 5:
        score += 0.15  # mild positive momentum
    elif pct_5d >= 5:
        score += 0.10  # strong but maybe extended

    score = min(score, 1.0)

    if score < 0.55:
        return None

    # Plan: SL = entry - 1.5 ATR, TP = entry + 3 ATR (1:2 R:R)
    entry = last
    sl = round(entry - 1.5 * atr, 2)
    tp = round(entry + 3.0 * atr, 2)

    return {
        "score": round(score, 3),
        "entry": round(entry, 2),
        "stop_loss": sl,
        "take_profit": tp,
        "rsi": round(float(rsi), 2),
        "atr": round(atr, 4),
        "trade_type": "swing",
    }


def run_backtest(
    tickers: List[str],
    ohlcv: Dict[str, pd.DataFrame],
    start_date: str,
    end_date: str,
    top_n_per_day: int = 5,
    max_hold_days: int = 10,
    output_dir: str = "data/backtest_results",
) -> Dict:
    """Run a full backtest over a date range.

    Args:
        tickers: list of tickers to consider each day
        ohlcv: dict of ticker -> full OHLCV DataFrame (will be PIT-sliced)
        start_date, end_date: 'YYYY-MM-DD'
        top_n_per_day: max picks per simulated day
        max_hold_days: outcome simulation window
        output_dir: where to write picks.csv + metrics.json + report.md
    """
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(output_dir) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[backtest] run_id={run_id}")
    print(f"[backtest] tickers={len(tickers)}, range={start_date}→{end_date}")
    print(f"[backtest] top_n_per_day={top_n_per_day}, max_hold={max_hold_days}d")

    # Generate trading day list (rough — uses any ticker's index intersected)
    # For robustness, use SPY-like ticker if present, else first ticker
    ref_ticker = "SPY" if "SPY" in ohlcv else tickers[0]
    ref_df = ohlcv.get(ref_ticker)
    if ref_df is None or ref_df.empty:
        return {"error": "no reference ticker data"}

    if not isinstance(ref_df.index, pd.DatetimeIndex):
        ref_df.index = pd.to_datetime(ref_df.index)

    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    sim_days = ref_df[(ref_df.index >= start_ts) & (ref_df.index <= end_ts)].index

    print(f"[backtest] {len(sim_days)} trading days to simulate")

    all_picks = []

    for day_i, sim_day in enumerate(sim_days):
        as_of = sim_day.date()

        # Score every ticker as of this day
        scored = []
        for tk in tickers:
            df = ohlcv.get(tk)
            if df is None:
                continue
            df_pit = slice_pit(df, as_of=as_of, min_history_days=60)
            if df_pit is None:
                continue
            plan = _simple_score(df_pit)
            if plan:
                plan["ticker"] = tk
                plan["pick_date"] = str(as_of)
                scored.append(plan)

        # Sort by score, take top N
        scored.sort(key=lambda x: x["score"], reverse=True)
        top = scored[:top_n_per_day]

        # Simulate outcome for each
        for pick in top:
            df = ohlcv[pick["ticker"]]
            forward = get_forward_window(df, as_of=as_of, n_days=max_hold_days + 1)
            # Skip pick day itself (entry = next-day open in real life)
            # For simplicity v1: entry on same day's close, look at next bars
            outcome = simulate_outcome(
                forward,
                entry=pick["entry"],
                stop_loss=pick["stop_loss"],
                take_profit=pick["take_profit"],
                max_hold_days=max_hold_days,
            )
            pick.update(outcome)
            all_picks.append(pick)

        if (day_i + 1) % 20 == 0:
            print(f"  [{day_i+1}/{len(sim_days)}] picks so far: {len(all_picks)}")

    # Write picks.csv
    csv_path = out_dir / "picks.csv"
    if all_picks:
        keys = list(all_picks[0].keys())
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(all_picks)

    # Compute metrics
    from src.backtester.metrics import compute_metrics, breakdown_by
    metrics = compute_metrics(all_picks)
    by_status = breakdown_by(all_picks, "exit_status")

    summary = {
        "run_id": run_id,
        "config": {
            "tickers": tickers,
            "start_date": start_date,
            "end_date": end_date,
            "top_n_per_day": top_n_per_day,
            "max_hold_days": max_hold_days,
        },
        "overall": metrics,
        "by_exit_status": by_status,
    }

    with open(out_dir / "metrics.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Markdown report
    with open(out_dir / "report.md", "w") as f:
        f.write(f"# 📊 Backtest Report — {run_id}\n\n")
        f.write(f"**Range:** {start_date} → {end_date}  \n")
        f.write(f"**Tickers:** {len(tickers)}  \n")
        f.write(f"**Total picks simulated:** {metrics['n_picks']}\n\n")
        f.write(f"## Headline Metrics\n\n")
        for k, v in metrics.items():
            f.write(f"- **{k}**: {v}\n")
        f.write(f"\n## Exit Status Breakdown\n\n")
        for status, m in by_status.items():
            f.write(f"### {status} ({m.get('n_picks',0)} picks)\n")
            f.write(f"- avg_r: {m.get('avg_r')}  \n")
            f.write(f"- win_rate: {m.get('win_rate_pct')}%  \n\n")
        f.write(f"\n## ⚠ Known Limitations (v1)\n\n")
        f.write("- **Survivorship bias**: only tests tickers in current universe\n")
        f.write("- **No slippage/commission modeling**\n")
        f.write("- **No news, no LLM** (Phase A baseline)\n")
        f.write("- **Conservative SL-first** when both touched same day\n")

    print(f"\n[backtest] ✅ Done. Output: {out_dir}")
    print(f"[backtest] 📊 {metrics['n_picks']} picks | "
          f"win={metrics['win_rate_pct']}% | "
          f"avgR={metrics['avg_r']} | "
          f"Sharpe={metrics['sharpe_annualized']}")

    return summary
