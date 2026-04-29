"""Evaluates pending picks: did they hit TP, SL, or stay open?
Logic:
- For each pending pick from past N days, fetch OHLC since pick date.
- If intraday HIGH >= take_profit → TP hit (count from first day reaching it).
- Else if intraday LOW <= stop_loss → SL hit.
- Else if 20+ trading days passed → mark expired with current return.
- Else → still open."""
import csv
from datetime import datetime, timedelta
from pathlib import Path
import yfinance as yf
import pandas as pd

LOG_PATH = Path("data/picks_log.csv")
MAX_DAYS_OPEN = 20   # mark expired after this many trading days
EVAL_LOOKBACK_DAYS = 30   # only evaluate picks from past N days


def _load_picks() -> list:
    if not LOG_PATH.exists():
        return []
    with LOG_PATH.open() as f:
        return list(csv.DictReader(f))


def _save_picks(rows: list):
    if not rows:
        return
    fields = list(rows[0].keys())
    with LOG_PATH.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def _fetch_ohlc(ticker: str, start: str) -> pd.DataFrame:
    """Fetch daily OHLC from start date to today."""
    try:
        df = yf.download(ticker, start=start, progress=False, auto_adjust=False)
        if df.empty:
            return pd.DataFrame()
        # Flatten multi-index columns if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        print(f"  [eval] {ticker} fetch error: {e}")
        return pd.DataFrame()


def evaluate_pending() -> dict:
    """Walk through pending picks, mark TP/SL/expired."""
    rows = _load_picks()
    if not rows:
        print("[eval] No picks logged yet.")
        return {"evaluated": 0, "tp_hits": 0, "sl_hits": 0, "expired": 0, "still_open": 0}

    today = datetime.now().date()
    cutoff = today - timedelta(days=EVAL_LOOKBACK_DAYS)

    counts = {"evaluated": 0, "tp_hits": 0, "sl_hits": 0, "expired": 0, "still_open": 0}

    for row in rows:
        if row["evaluation_status"] != "pending":
            continue
        try:
            pick_date = datetime.strptime(row["pick_date"], "%Y-%m-%d").date()
        except Exception:
            continue
        if pick_date < cutoff:
            # too old, mark expired with no exit data
            row["evaluation_status"] = "expired"
            row["evaluated_on"] = today.isoformat()
            counts["expired"] += 1
            continue

        ticker = row["ticker"]
        entry = float(row["entry"])
        sl = float(row["stop_loss"])
        tp = float(row["take_profit"])

        df = _fetch_ohlc(ticker, pick_date.isoformat())
        if df.empty:
            counts["still_open"] += 1
            continue

        # Walk day by day from pick_date forward (entry is NEXT trading day after pick)
        outcome = None
        exit_price = None
        exit_date = None
        for date, bar in df.iterrows():
            # Only evaluate bars AFTER the pick date — entry is next day
            if date.date() <= pick_date:
                continue
            high = float(bar["High"])
            low = float(bar["Low"])
            # Same-day BOTH hit: use Open as tie-breaker (whichever level is closer to Open hit first)
            if low <= sl and high >= tp:
                open_px = float(bar["Open"])
                dist_to_tp = abs(tp - open_px)
                dist_to_sl = abs(open_px - sl)
                # If Open is closer to TP than to SL, price likely traveled UP first → TP hit first
                if dist_to_tp < dist_to_sl:
                    outcome = "tp_hit"
                    exit_price = tp
                else:
                    outcome = "sl_hit"
                    exit_price = sl
                exit_date = date
                print(f"  [tie-break] {row['ticker']} {date.date()}: Open=${open_px:.2f} → {outcome} (dTP=${dist_to_tp:.2f} dSL=${dist_to_sl:.2f})")
                break
            elif low <= sl:
                outcome = "sl_hit"
                exit_price = sl
                exit_date = date
                break
            elif high >= tp:
                outcome = "tp_hit"
                exit_price = tp
                exit_date = date
                break

        if outcome:
            row["evaluation_status"] = outcome
            row["evaluated_on"] = exit_date.strftime("%Y-%m-%d")
            row["exit_price"] = round(exit_price, 4)
            ret = (exit_price - entry) / entry * 100
            row["actual_return_pct"] = round(ret, 2)
            risk = entry - sl
            row["r_multiple"] = round((exit_price - entry) / risk, 2) if risk > 0 else 0
            counts[outcome.replace("_hit", "_hits")] += 1
            counts["evaluated"] += 1
            print(f"  ✅ {ticker}: {outcome.upper()} on {exit_date.date()} | exit ${exit_price:.2f} | {ret:+.2f}% | {row['r_multiple']}R")
        else:
            # Days elapsed since pick
            days_elapsed = (today - pick_date).days
            if days_elapsed >= MAX_DAYS_OPEN:
                # Mark expired with last close
                last_close = float(df["Close"].iloc[-1])
                row["evaluation_status"] = "expired"
                row["evaluated_on"] = today.isoformat()
                row["exit_price"] = round(last_close, 4)
                ret = (last_close - entry) / entry * 100
                row["actual_return_pct"] = round(ret, 2)
                risk = entry - sl
                row["r_multiple"] = round((last_close - entry) / risk, 2) if risk > 0 else 0
                counts["expired"] += 1
                counts["evaluated"] += 1
                print(f"  ⏰ {ticker}: EXPIRED after {days_elapsed}d | exit ${last_close:.2f} | {ret:+.2f}% | {row['r_multiple']}R")
            else:
                counts["still_open"] += 1
                print(f"  🟡 {ticker}: still open ({days_elapsed}d since pick)")

    _save_picks(rows)
    return counts
