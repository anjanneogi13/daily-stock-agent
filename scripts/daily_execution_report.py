"""
Daily Execution Report — full intraday X-ray of each pick.

For every pick from a given date, computes:
  • Did entry limit fill? (intraday low ≤ entry)
  • If filled: which hit first, SL or TP? (chronological)
  • If TP hit: max additional gain after TP (you-left-money-on-table)
  • If SL hit: how much further it dropped (SL saved you)
  • If NO SL was used: worst close + intraday low
  • If NO TP was used: close-of-day return
  • Max favorable / adverse excursion (MFE / MAE)
"""
import csv, sys, json, os
from datetime import datetime, timedelta
from pathlib import Path

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    print("[exec] Missing yfinance/pandas — skipping"); sys.exit(0)

# Date to evaluate: arg or today
date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
print(f"[exec] Evaluating picks from {date_str}\n")

p = Path("data/picks_log.csv")
if not p.exists():
    print("No picks_log.csv"); sys.exit(0)

picks = [r for r in csv.DictReader(p.open()) if r.get("pick_date") == date_str]
if not picks:
    print(f"No picks for {date_str}"); sys.exit(0)

def fetch_intraday(ticker, date):
    """Get 5-min bars for the trading day."""
    try:
        # Fetch 7 days to ensure we cover the date even if weekend/holiday
        start = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=2)).strftime("%Y-%m-%d")
        end = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=2)).strftime("%Y-%m-%d")
        df = yf.Ticker(ticker).history(start=start, end=end, interval="5m", auto_adjust=False)
        if df.empty: return None
        # Filter to the target date in US/Eastern
        df.index = df.index.tz_convert("America/New_York")
        df = df[df.index.strftime("%Y-%m-%d") == date]
        return df if not df.empty else None
    except Exception as e:
        print(f"  ⚠ {ticker}: intraday fetch failed ({e})")
        return None

reports = []
for r in picks:
    t = r["ticker"]
    try:
        entry = float(r["entry"]); sl = float(r["stop_loss"]); tp = float(r["take_profit"])
    except Exception: continue

    df = fetch_intraday(t, date_str)
    if df is None or len(df) < 2:
        reports.append({"ticker": t, "status": "NO_DATA",
                        "entry": entry, "sl": sl, "tp": tp})
        continue

    open_px = float(df["Open"].iloc[0])
    close_px = float(df["Close"].iloc[-1])
    day_high = float(df["High"].max())
    day_low = float(df["Low"].min())

    # Did we fill? (limit buy fills if intraday low ≤ entry, OR if open ≤ entry)
    filled = day_low <= entry
    if not filled:
        reports.append({
            "ticker": t, "status": "NOT_FILLED",
            "entry": entry, "sl": sl, "tp": tp,
            "open": open_px, "close": close_px, "low": day_low, "high": day_high,
            "missed_by_pct": (day_low - entry) / entry * 100,
        })
        continue

    # We filled. Find the bar where we filled (first bar where Low ≤ entry)
    fill_idx = df[df["Low"] <= entry].index[0]
    fill_bar = df.index.get_loc(fill_idx)
    after = df.iloc[fill_bar:]

    # Walk forward bar-by-bar to see SL or TP hit first
    sl_hit_idx = None; tp_hit_idx = None
    for i, (ts, bar) in enumerate(after.iterrows()):
        if bar["Low"] <= sl and sl_hit_idx is None:
            sl_hit_idx = i
        if bar["High"] >= tp and tp_hit_idx is None:
            tp_hit_idx = i
        if sl_hit_idx is not None or tp_hit_idx is not None:
            # If both in same bar (rare), SL conservatively wins
            if sl_hit_idx is not None and tp_hit_idx is not None:
                break
            elif sl_hit_idx is not None or tp_hit_idx is not None:
                break

    mfe = (df["High"].iloc[fill_bar:].max() - entry) / entry * 100  # max favorable
    mae = (df["Low"].iloc[fill_bar:].min() - entry) / entry * 100   # max adverse
    close_ret = (close_px - entry) / entry * 100

    if sl_hit_idx is not None and (tp_hit_idx is None or sl_hit_idx < tp_hit_idx):
        outcome = "SL_HIT"
        # After SL hit, how much further down did it go?
        after_sl = after.iloc[sl_hit_idx:]
        further_low = float(after_sl["Low"].min())
        further_pct = (further_low - sl) / sl * 100  # negative = further drop
        # If no SL had been set, what would close-of-day be?
        no_sl_close_pct = close_ret
        no_sl_worst_pct = mae
        reports.append({
            "ticker": t, "status": outcome, "entry": entry, "sl": sl, "tp": tp,
            "fill_time": fill_idx.strftime("%H:%M"),
            "open": open_px, "close": close_px, "high": day_high, "low": day_low,
            "sl_pct": (sl-entry)/entry*100,
            "further_after_sl_pct": further_pct,
            "no_sl_close_pct": no_sl_close_pct,
            "no_sl_worst_pct": no_sl_worst_pct,
            "mfe_pct": mfe, "mae_pct": mae,
        })
    elif tp_hit_idx is not None:
        outcome = "TP_HIT"
        # After TP hit, how much further up did it go?
        after_tp = after.iloc[tp_hit_idx:]
        further_high = float(after_tp["High"].max())
        further_pct = (further_high - tp) / tp * 100  # positive = more upside left
        no_tp_close_pct = close_ret
        reports.append({
            "ticker": t, "status": outcome, "entry": entry, "sl": sl, "tp": tp,
            "fill_time": fill_idx.strftime("%H:%M"),
            "open": open_px, "close": close_px, "high": day_high, "low": day_low,
            "tp_pct": (tp-entry)/entry*100,
            "further_after_tp_pct": further_pct,
            "no_tp_close_pct": no_tp_close_pct,
            "mfe_pct": mfe, "mae_pct": mae,
        })
    else:
        outcome = "OPEN"  # neither hit by close
        reports.append({
            "ticker": t, "status": outcome, "entry": entry, "sl": sl, "tp": tp,
            "fill_time": fill_idx.strftime("%H:%M"),
            "open": open_px, "close": close_px, "high": day_high, "low": day_low,
            "close_ret_pct": close_ret,
            "mfe_pct": mfe, "mae_pct": mae,
            "no_sl_worst_pct": mae, "no_tp_best_pct": mfe,
        })

# Save raw json
Path("data").mkdir(exist_ok=True)
out_path = Path(f"data/exec_report_{date_str}.json")
out_path.write_text(json.dumps({"date": date_str, "picks": reports}, indent=2))

# ---- Human-readable summary ----
print("="*78)
print(f"📊 DAILY EXECUTION REPORT — {date_str}")
print("="*78)

filled = [r for r in reports if r["status"] not in ("NOT_FILLED","NO_DATA")]
print(f"\n📌 {len(reports)} picks  |  Filled: {len(filled)}  |  Not filled: {sum(1 for r in reports if r['status']=='NOT_FILLED')}\n")

for r in reports:
    t = r["ticker"]; s = r["status"]
    print(f"━━━ {t} ━━━ [{s}]")
    print(f"  Plan:  Entry ${r['entry']:.2f}  SL ${r['sl']:.2f}  TP ${r['tp']:.2f}")

    if s == "NO_DATA":
        print("  ❌ No intraday data available\n"); continue

    if s == "NOT_FILLED":
        print(f"  📊 Day: O ${r['open']:.2f} H ${r['high']:.2f} L ${r['low']:.2f} C ${r['close']:.2f}")
        print(f"  ⚠️  Limit not hit — missed by {r['missed_by_pct']:+.2f}% (low never reached entry)\n")
        continue

    print(f"  ⏱  Filled at {r['fill_time']} ET")
    print(f"  📊 Day: O ${r['open']:.2f} H ${r['high']:.2f} L ${r['low']:.2f} C ${r['close']:.2f}")
    print(f"  📈 MFE (best unrealized): {r['mfe_pct']:+.2f}%   MAE (worst): {r['mae_pct']:+.2f}%")

    if s == "TP_HIT":
        print(f"  ✅ TP HIT → locked in {r['tp_pct']:+.2f}%")
        print(f"  💸 Left on table: {r['further_after_tp_pct']:+.2f}% extra upside after TP")
        print(f"  📍 If NO TP set: close-of-day return would be {r['no_tp_close_pct']:+.2f}%")
    elif s == "SL_HIT":
        print(f"  🛑 SL HIT → loss capped at {r['sl_pct']:+.2f}%")
        print(f"  📉 SL saved you: dropped another {r['further_after_sl_pct']:+.2f}% after SL")
        print(f"  ⚠️  If NO SL set: worst intraday {r['no_sl_worst_pct']:+.2f}%, close {r['no_sl_close_pct']:+.2f}%")
    elif s == "OPEN":
        print(f"  ⏳ Still open at close → unrealized {r['close_ret_pct']:+.2f}%")
        print(f"  📍 If NO SL: same — best intraday {r['no_tp_best_pct']:+.2f}%, worst {r['no_sl_worst_pct']:+.2f}%")
    print()

# Aggregate stats
print("="*78)
print("📈 AGGREGATE")
print("="*78)
tps = [r for r in reports if r["status"]=="TP_HIT"]
sls = [r for r in reports if r["status"]=="SL_HIT"]
opens = [r for r in reports if r["status"]=="OPEN"]
nf = [r for r in reports if r["status"]=="NOT_FILLED"]
print(f"  ✅ TP hits:    {len(tps)}")
print(f"  🛑 SL hits:    {len(sls)}")
print(f"  ⏳ Still open: {len(opens)}")
print(f"  ⚠️  Not filled: {len(nf)}")

if filled:
    avg_mfe = sum(r["mfe_pct"] for r in filled)/len(filled)
    avg_mae = sum(r["mae_pct"] for r in filled)/len(filled)
    print(f"\n  Avg MFE (best): {avg_mfe:+.2f}%")
    print(f"  Avg MAE (worst): {avg_mae:+.2f}%")

print(f"\n💾 Raw data: data/exec_report_{date_str}.json")
