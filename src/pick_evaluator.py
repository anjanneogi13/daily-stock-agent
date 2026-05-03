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
from .signal_journal import attach_outcome as _journal_attach

LOG_PATH = Path("data/picks_log.csv")
MAX_DAYS_OPEN = 20   # mark expired after this many trading days
EVAL_LOOKBACK_DAYS = 30   # only evaluate picks from past N days


def _load_picks() -> list:
    if not LOG_PATH.exists():
        return []
    with LOG_PATH.open() as f:
        rows = list(csv.DictReader(f))
    # Ensure new SPY/alpha columns exist on all rows (May 2 2026)
    new_fields = ["spy_close_at_exit", "spy_return_pct", "alpha_pct",
                  "sector_etf", "sector_close", "sector_close_at_exit",
                  "sector_return_pct", "sector_alpha_pct"]
    for r in rows:
        for f in new_fields:
            if f not in r:
                r[f] = ""
    return rows


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


_SPY_CACHE = {}

def _spy_close_on(date_str: str) -> float | None:
    """Get SPY closing price on or nearest trading day to given date.
    Cached to avoid repeated yf.download calls during evaluator run."""
    if date_str in _SPY_CACHE:
        return _SPY_CACHE[date_str]
    try:
        from datetime import datetime as _dt, timedelta as _td
        target = _dt.strptime(date_str, "%Y-%m-%d").date()
        # Fetch a 5-day window to handle weekends/holidays
        start = (target - _td(days=5)).isoformat()
        end = (target + _td(days=2)).isoformat()
        df = yf.download("SPY", start=start, end=end, progress=False, auto_adjust=False)
        if df.empty:
            _SPY_CACHE[date_str] = None
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        # Find the row at-or-before target date
        df = df[df.index.date <= target]
        if df.empty:
            _SPY_CACHE[date_str] = None
            return None
        val = float(df["Close"].iloc[-1])
        _SPY_CACHE[date_str] = val
        return val
    except Exception as e:
        print(f"  [spy] {date_str} fetch error: {e}")
        _SPY_CACHE[date_str] = None
        return None


def _add_spy_alpha(row: dict, exit_date_str: str, pick_return_pct: float) -> str:
    """Compute SPY return over hold period and stash alpha in row.
    Returns spy_close_at_exit (str) or empty string on failure."""
    spy_at_pick_str = row.get("spy_close", "")
    if not spy_at_pick_str:
        row["alpha_pct"] = None
        return ""
    try:
        spy_at_pick = float(spy_at_pick_str)
    except Exception:
        row["alpha_pct"] = None
        return ""
    spy_at_exit = _spy_close_on(exit_date_str)
    if spy_at_exit is None or spy_at_pick <= 0:
        row["alpha_pct"] = None
        return ""
    spy_return = (spy_at_exit - spy_at_pick) / spy_at_pick * 100
    row["spy_return_pct"] = round(spy_return, 2)
    row["alpha_pct"] = round(pick_return_pct - spy_return, 2)
    return str(round(spy_at_exit, 2))


def _etf_close_on(etf: str, date_str: str) -> float | None:
    """Fetch ETF close on date_str. Used for sector-alpha calc."""
    if not etf:
        return None
    try:
        from datetime import datetime, timedelta
        d = datetime.strptime(date_str, "%Y-%m-%d")
        df = _fetch_ohlc(etf, (d - timedelta(days=5)).strftime("%Y-%m-%d"))
        if df is None or df.empty:
            return None
        df = df[df.index <= d.strftime("%Y-%m-%d")]
        if df.empty:
            return None
        return float(df["Close"].iloc[-1])
    except Exception as e:
        print(f"  [sector] {etf} {date_str} fetch error: {e}")
        return None


def _add_sector_alpha(row: dict, exit_date_str: str, pick_return_pct: float) -> str:
    """Mirror of _add_spy_alpha but for the pick's sector ETF."""
    etf = row.get("sector_etf") or ""
    sec_pick_str = row.get("sector_close", "")
    if not etf or not sec_pick_str:
        row["sector_alpha_pct"] = None
        return ""
    try:
        sec_at_pick = float(sec_pick_str)
    except Exception:
        row["sector_alpha_pct"] = None
        return ""
    sec_at_exit = _etf_close_on(etf, exit_date_str)
    if sec_at_exit is None or sec_at_pick <= 0:
        row["sector_alpha_pct"] = None
        return ""
    sec_return = (sec_at_exit - sec_at_pick) / sec_at_pick * 100
    row["sector_return_pct"] = round(sec_return, 2)
    row["sector_alpha_pct"] = round(pick_return_pct - sec_return, 2)
    return str(round(sec_at_exit, 2))


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
            # BUG-2 FIX (May 2 2026): include pick_date bar.
            # Picks generate during US session (committed ~12 ET = ~16 UTC),
            # so the entry day IS pick_date, not pick_date+1.
            # Skipping pick_date caused 32 picks to stay 'pending' forever
            # when SL/TP hit on the same trading day.
            if date.date() < pick_date:
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
            # SPY relative perf (May 2 2026): alpha vs benchmark
            row["spy_close_at_exit"] = _add_spy_alpha(row, exit_date.strftime("%Y-%m-%d"), ret)
            row["sector_close_at_exit"] = _add_sector_alpha(row, exit_date.strftime("%Y-%m-%d"), ret)
            try:
                _journal_attach(
                    ticker=row.get("ticker"),
                    pick_date=row.get("pick_date"),
                    r_multiple=float(row.get("r_multiple")) if row.get("r_multiple") not in (None, "", "None") else None,
                    actual_return_pct=float(ret) if ret is not None else None,
                    evaluated_on=exit_date.strftime("%Y-%m-%d"),
                )
            except Exception as _e:
                pass
            counts[outcome.replace("_hit", "_hits")] += 1
            counts["evaluated"] += 1
            alpha_str = f" | α={row.get('alpha_pct','?')}%" if row.get('alpha_pct') is not None else ""
            print(f"  ✅ {ticker}: {outcome.upper()} on {exit_date.date()} | exit ${exit_price:.2f} | {ret:+.2f}% | {row['r_multiple']}R{alpha_str}")
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
                # SPY relative perf for expired picks
                row["spy_close_at_exit"] = _add_spy_alpha(row, today.isoformat(), ret)
                row["sector_close_at_exit"] = _add_sector_alpha(row, today.isoformat(), ret)
                try:
                    _journal_attach(
                        ticker=row.get("ticker"),
                        pick_date=row.get("pick_date"),
                        r_multiple=float(row.get("r_multiple")) if row.get("r_multiple") not in (None, "", "None") else None,
                        actual_return_pct=float(ret) if ret is not None else None,
                        evaluated_on=today.isoformat(),
                    )
                except Exception:
                    pass
                counts["expired"] += 1
                counts["evaluated"] += 1
                alpha_str = f" | α={row.get('alpha_pct','?')}%" if row.get('alpha_pct') is not None else ""
                print(f"  ⏰ {ticker}: EXPIRED after {days_elapsed}d | exit ${last_close:.2f} | {ret:+.2f}% | {row['r_multiple']}R{alpha_str}")
            else:
                counts["still_open"] += 1
                print(f"  🟡 {ticker}: still open ({days_elapsed}d since pick)")

    _save_picks(rows)
    return counts
