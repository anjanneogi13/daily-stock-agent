"""Backtest orchestration engine — v1.1.

v1.1 fixes:
  1. Ticker cooldown (no re-pick same ticker within N days)
  2. Gap-down fill simulation (fills below stop on gap)
  3. RSI overbought penalty in scorer (mirror live system)
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
    """v1.1 scorer — adds RSI overbought penalty."""
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

    # ─── v1.1 FIX: HARD REJECT extreme overbought ──────
    if rsi >= 75:
        return None  # never pick at RSI 75+ (was AAPL@82, TSM@72 problem)

    sma20 = closes[-20:].mean()
    sma50 = closes[-50:].mean() if len(closes) >= 50 else sma20

    tr = np.maximum(highs[-15:] - lows[-15:],
                    np.maximum(np.abs(highs[-15:] - np.roll(closes, 1)[-15:]),
                               np.abs(lows[-15:] - np.roll(closes, 1)[-15:])))
    atr = float(tr[1:].mean())

    score = 0.0
    if rsi < 35:
        score += 0.30
    elif rsi < 50:
        score += 0.20
    elif rsi < 65:
        score += 0.10  # mild reward
    elif rsi < 75:
        score -= 0.10  # ── v1.1: penalty for 65-74 (overbought zone)

    if last > sma20:
        score += 0.20
    if last > sma50:
        score += 0.20
    if sma20 > sma50:
        score += 0.15

    pct_5d = (last - closes[-6]) / closes[-6] * 100 if len(closes) >= 6 else 0
    if 0 < pct_5d < 5:
        score += 0.15
    elif pct_5d >= 8:
        score -= 0.10  # ── v1.1: penalty for parabolic (extended)
    elif pct_5d >= 5:
        score += 0.05

    score = max(0.0, min(score, 1.0))

    if score < 0.55:
        return None

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
    cooldown_days: int = 5,                # ── v1.1
    output_dir: str = "data/backtest_results",
) -> Dict:
    """v1.1: adds cooldown_days param to mirror live system."""
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = Path(output_dir) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[backtest v1.1] run_id={run_id}")
    print(f"[backtest] tickers={len(tickers)}, range={start_date}→{end_date}")
    print(f"[backtest] top_n={top_n_per_day}, max_hold={max_hold_days}d, cooldown={cooldown_days}d")

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
    last_picked: Dict[str, datetime] = {}  # ── v1.1: cooldown tracker

    for day_i, sim_day in enumerate(sim_days):
        as_of = sim_day.date()

        scored = []
        for tk in tickers:
            # ── v1.1 FIX: cooldown check ─────────────────
            if tk in last_picked:
                days_since = (sim_day - last_picked[tk]).days
                if days_since < cooldown_days:
                    continue  # skip — still in cooldown

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

        scored.sort(key=lambda x: x["score"], reverse=True)
        top = scored[:top_n_per_day]

        for pick in top:
            df = ohlcv[pick["ticker"]]
            forward = get_forward_window(df, as_of=as_of, n_days=max_hold_days + 1)
            outcome = simulate_outcome(
                forward,
                entry=pick["entry"],
                stop_loss=pick["stop_loss"],
                take_profit=pick["take_profit"],
                max_hold_days=max_hold_days,
            )
            pick.update(outcome)
            all_picks.append(pick)
            last_picked[pick["ticker"]] = sim_day  # ── v1.1: record pick

        if (day_i + 1) % 50 == 0:
            print(f"  [{day_i+1}/{len(sim_days)}] picks so far: {len(all_picks)}")

    csv_path = out_dir / "picks.csv"
    if all_picks:
        keys = list(all_picks[0].keys())
        with open(csv_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(all_picks)

    from src.backtester.metrics import compute_metrics, breakdown_by
    metrics = compute_metrics(all_picks)
    by_status = breakdown_by(all_picks, "exit_status")
    by_trade_type = breakdown_by(all_picks, "trade_type")

    summary = {
        "run_id": run_id,
        "version": "v1.1",
        "config": {
            "tickers": tickers,
            "start_date": start_date,
            "end_date": end_date,
            "top_n_per_day": top_n_per_day,
            "max_hold_days": max_hold_days,
            "cooldown_days": cooldown_days,
        },
        "overall": metrics,
        "by_exit_status": by_status,
        "by_trade_type": by_trade_type,
    }

    with open(out_dir / "metrics.json", "w") as f:
        json.dump(summary, f, indent=2)

    with open(out_dir / "report.md", "w") as f:
        f.write(f"# 📊 Backtest Report v1.1 — {run_id}\n\n")
        f.write(f"**Range:** {start_date} → {end_date}  \n")
        f.write(f"**Tickers:** {len(tickers)}  \n")
        f.write(f"**Cooldown:** {cooldown_days} days  \n")
        f.write(f"**Total picks simulated:** {metrics['n_picks']}\n\n")
        f.write(f"## Headline Metrics\n\n")
        for k, v in metrics.items():
            f.write(f"- **{k}**: {v}\n")
        f.write(f"\n## Exit Status Breakdown\n\n")
        for status, m in by_status.items():
            f.write(f"### {status} ({m.get('n_picks',0)} picks)\n")
            f.write(f"- avg_r: {m.get('avg_r')}  \n")
            f.write(f"- win_rate: {m.get('win_rate_pct')}%  \n\n")

    print(f"\n[backtest] ✅ Done. Output: {out_dir}")
    print(f"[backtest] 📊 {metrics['n_picks']} picks | "
          f"win={metrics['win_rate_pct']}% | "
          f"avgR={metrics['avg_r']} | "
          f"Sharpe={metrics['sharpe_annualized']}")

    return summary
