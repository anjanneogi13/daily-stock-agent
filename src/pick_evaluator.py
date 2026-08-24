"""Evaluates pending picks: did they hit TP, SL, or stay open?
Logic:
- For each pending pick from past N days, fetch OHLC since pick date.
- Walk bars within the pick's hold horizon (trade_state.max_hold_days):
  intraday HIGH >= take_profit → TP hit; intraday LOW <= stop_loss → SL hit.
- Corrupt bars (implausible single-day move vs prior close) are skipped so a
  bad print can never book a win or a loss (Cluster F).
- Day trades force-close at their first session's close (day_close).
- Past the horizon → force-close 'expired' (EXPIRED_OVERDUE) exactly once,
  with a DETERMINISTIC evaluated_on (horizon session, never "today") so
  re-running any day is idempotent and stale rows can't resurrect in daily
  reports (Cluster B/E, §7)."""
import csv
from datetime import datetime, timedelta
from pathlib import Path
import yfinance as yf
import pandas as pd
from .signal_journal import attach_outcome as _journal_attach
from .sector_benchmark import resolve_sector_etf
from .price_sanity import plausible_bar
from .trade_state import max_hold_days

LOG_PATH = Path("data/picks_log.csv")
MAX_DAYS_OPEN = 20   # legacy hard cap; per-type horizon from trade_state applies first
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
    """Atomically rewrite picks_log.csv.

    Crash-safety (May 11 2026): write to a sibling .tmp file then atomically
    rename onto the real path. If the process is killed mid-write, the real
    picks_log.csv is left intact rather than truncated/empty. tmp.replace()
    is atomic on POSIX filesystems.
    """
    if not rows:
        return
    fields = list(rows[0].keys())
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = LOG_PATH.with_suffix(LOG_PATH.suffix + ".tmp")
    with tmp.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    tmp.replace(LOG_PATH)


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


def _resolve_sector_etf_for_row(row: dict) -> str:
    """Resolve a row's sector benchmark ETF from persisted fields/tag/sector.

    Legacy rows may have blank sector_etf even though their tag contains enough
    information, e.g. "SEMI / AI" -> SOXX. Fall back to SPY so sector-alpha
    learning has a benchmark instead of staying blank forever.
    """
    existing = (row.get("sector_etf") or "").strip()
    if existing:
        return existing

    tag = (
        row.get("tag")
        or row.get("sector_tag")
        or row.get("scores_sector_tag")
        or ""
    )
    sector = (
        row.get("sector")
        or row.get("yfinance_sector")
        or row.get("info_sector")
        or ""
    )
    return resolve_sector_etf(sector=sector, tag=tag) or "SPY"


def _ensure_sector_benchmark_anchor(row: dict) -> tuple[str, float | None]:
    """Ensure row has sector_etf and sector_close at pick time.

    Returns (etf, close). If the resolved ETF cannot be fetched, falls back to
    SPY and rewrites both anchor fields when SPY succeeds.
    """
    pick_date = (row.get("pick_date") or "").strip()
    etf = _resolve_sector_etf_for_row(row)
    row["sector_etf"] = etf

    sec_pick_str = (row.get("sector_close") or "").strip()
    if sec_pick_str:
        try:
            return etf, float(sec_pick_str)
        except Exception:
            pass

    if not pick_date:
        return etf, None

    sec_at_pick = _etf_close_on(etf, pick_date)
    if sec_at_pick is not None:
        row["sector_close"] = str(round(sec_at_pick, 2))
        return etf, sec_at_pick

    if etf != "SPY":
        spy_at_pick = _etf_close_on("SPY", pick_date)
        if spy_at_pick is not None:
            row["sector_etf"] = "SPY"
            row["sector_close"] = str(round(spy_at_pick, 2))
            return "SPY", spy_at_pick

    return etf, None


def _add_sector_alpha(row: dict, exit_date_str: str, pick_return_pct: float) -> str:
    """Mirror of _add_spy_alpha but for the pick's sector ETF.

    Also repairs legacy rows missing sector_etf/sector_close by resolving the
    benchmark from row metadata and fetching the pick-date ETF close.
    """
    etf, sec_at_pick = _ensure_sector_benchmark_anchor(row)
    if not etf or sec_at_pick is None:
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
        return {"evaluated": 0, "tp_hits": 0, "sl_hits": 0, "expired": 0, "still_open": 0, "unreachable_entry": 0, "day_close": 0}

    today = datetime.now().date()
    cutoff = today - timedelta(days=EVAL_LOOKBACK_DAYS)

    counts = {"evaluated": 0, "tp_hits": 0, "sl_hits": 0, "expired": 0, "still_open": 0, "unreachable_entry": 0, "day_close": 0}

    for row in rows:
        if row["evaluation_status"] != "pending":
            continue
        try:
            pick_date = datetime.strptime(row["pick_date"], "%Y-%m-%d").date()
        except Exception:
            continue
        max_hold = max_hold_days(row.get("trade_type", ""))
        horizon_date = pick_date + timedelta(days=max_hold)
        if pick_date < cutoff:
            # too old, mark expired with no exit data — settled UNVERIFIED.
            # Deterministic evaluated_on = horizon date, NOT today: re-running
            # must not stamp a new close date each run (§7 idempotency; this
            # was the "45 stale FLAT tickers re-closed daily" bug).
            row["evaluation_status"] = "expired"
            row["evaluated_on"] = horizon_date.isoformat()
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

        # ─── F3 (May 4 2026): unreachable_entry detection ─────────
        # If logged entry is OUTSIDE [low, high] of the pick_date bar,
        # the trade was never executable (stale price / overnight gap).
        # Mark as 'unreachable_entry' instead of letting the day-walk
        # spuriously mark it sl_hit (because price gapped through SL too).
        # Discovered Apr 28 SEMI bloodbath: 6 picks logged at prices
        # $2-$20 ABOVE that day's actual high → impossible to fill.
        try:
            pick_bar = df.loc[df.index.date == pick_date]
        except Exception:
            pick_bar = df.iloc[0:0]
        if len(pick_bar):
            pb_high = float(pick_bar["High"].iloc[0])
            pb_low = float(pick_bar["Low"].iloc[0])
            # Allow 0.5% tolerance for data-source rounding differences
            tol = entry * 0.005
            if entry > pb_high + tol or entry < pb_low - tol:
                row["evaluation_status"] = "unreachable_entry"
                row["evaluated_on"] = pick_date.isoformat()
                row["exit_price"] = ""
                row["actual_return_pct"] = ""
                row["r_multiple"] = ""
                counts.setdefault("unreachable_entry", 0)
                counts["unreachable_entry"] += 1
                print(f"  🚫 {ticker}: unreachable_entry — logged ${entry:.2f} "
                      f"outside [{pb_low:.2f}, {pb_high:.2f}] on {pick_date}")
                continue

        # Walk day by day from pick_date forward, bounded by the hold horizon
        # (a swing cannot book a TP/SL after it should already have been
        # force-closed) and gated by bar plausibility (Cluster F: a corrupt
        # print must never book a win or a loss).
        outcome = None
        exit_price = None
        exit_date = None
        prev_close = entry  # entry is the validated reference for bar 1
        is_day_trade = (row.get("trade_type", "") or "").lower() == "day"
        for date, bar in df.iterrows():
            # BUG-2 FIX (May 2 2026): include pick_date bar.
            # Picks generate during US session (committed ~12 ET = ~16 UTC),
            # so the entry day IS pick_date, not pick_date+1.
            # Skipping pick_date caused 32 picks to stay 'pending' forever
            # when SL/TP hit on the same trading day.
            if date.date() < pick_date:
                continue
            if date.date() > horizon_date:
                break
            high = float(bar["High"])
            low = float(bar["Low"])
            if not plausible_bar(prev_close, high, low):
                print(f"  🧯 {ticker} {date.date()}: bar quarantined "
                      f"(H={high:.2f} L={low:.2f} vs prev close {prev_close:.2f}) — skipped")
                continue
            prev_close = float(bar["Close"])
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
            if is_day_trade:
                # Day trades live one session only — never book a TP/SL from
                # a later bar; the day_close branch below settles them.
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
                print(f"[eval] WARN journal_attach failed for {row.get('ticker','?')}: {_e}")  # M9
            counts[outcome.replace("_hit", "_hits")] += 1
            counts["evaluated"] += 1
            alpha_str = f" | α={row.get('alpha_pct','?')}%" if row.get('alpha_pct') is not None else ""
            print(f"  ✅ {ticker}: {outcome.upper()} on {exit_date.date()} | exit ${exit_price:.2f} | {ret:+.2f}% | {row['r_multiple']}R{alpha_str}")
        else:
            # ── Day-trade rule (Bug #5, May 5 2026): force-close at pick_date Close ──
            # Day trades MUST close same session. If neither SL nor TP hit during
            # pick_date, mark 'day_close' with exit = pick_date Close. Without this,
            # day-picks like MPWR (2026-05-02) drifted as unintentional swings until
            # the 20-day expiry caught them — corrupting both win-rate and learning.
            if (row.get("trade_type", "").lower() == "day"):
                # Prefer the exact pick_date bar; if pick_date was a non-trading
                # day (weekend/holiday — see MPWR 2026-05-02 case), fall back to
                # the FIRST trading bar at-or-after pick_date. evaluated_on
                # records the actual session date, not the calendar pick_date.
                pick_bar_match = df[df.index.date == pick_date]
                if not len(pick_bar_match):
                    pick_bar_match = df[df.index.date >= pick_date].head(1)
                if len(pick_bar_match):
                    pick_close = float(pick_bar_match["Close"].iloc[0])
                    actual_close_date = pick_bar_match.index[0].date()
                    row["evaluation_status"] = "day_close"
                    row["evaluated_on"] = actual_close_date.isoformat()
                    row["exit_price"] = round(pick_close, 4)
                    ret = (pick_close - entry) / entry * 100
                    row["actual_return_pct"] = round(ret, 2)
                    risk = entry - sl
                    row["r_multiple"] = round((pick_close - entry) / risk, 2) if risk > 0 else 0
                    row["spy_close_at_exit"] = _add_spy_alpha(row, actual_close_date.isoformat(), ret)
                    row["sector_close_at_exit"] = _add_sector_alpha(row, actual_close_date.isoformat(), ret)
                    try:
                        _journal_attach(
                            ticker=row.get("ticker"),
                            pick_date=row.get("pick_date"),
                            r_multiple=float(row.get("r_multiple")) if row.get("r_multiple") not in (None, "", "None") else None,
                            actual_return_pct=float(ret) if ret is not None else None,
                            evaluated_on=actual_close_date.isoformat(),
                        )
                    except Exception as _e:
                        print(f"[eval] WARN journal_attach (day_close) failed for {row.get('ticker','?')}: {_e}")
                    counts["day_close"] += 1
                    counts["evaluated"] += 1
                    print(f"  📅 {ticker}: DAY_CLOSE on {actual_close_date} | exit ${pick_close:.2f} | {ret:+.2f}% | {row['r_multiple']}R")
                    continue

            # Hold-horizon force-close (Cluster B/E): a swing that exceeds its
            # max hold becomes EXPIRED_OVERDUE ('expired') exactly once, at a
            # DETERMINISTIC date/price — the last in-horizon session — never
            # "today's" values. Re-running any day yields identical output.
            days_elapsed = (today - pick_date).days
            if days_elapsed >= max_hold:
                horizon_bars = df[(df.index.date >= pick_date) & (df.index.date <= horizon_date)]
                if len(horizon_bars):
                    exit_bar_date = horizon_bars.index[-1].date()
                    last_close = float(horizon_bars["Close"].iloc[-1])
                else:
                    exit_bar_date = horizon_date
                    last_close = None
                row["evaluation_status"] = "expired"
                row["evaluated_on"] = exit_bar_date.isoformat()
                if last_close is None:
                    # settled without a verifiable price → UNVERIFIED outcome
                    row["exit_price"] = ""
                    row["actual_return_pct"] = ""
                    row["r_multiple"] = ""
                    counts["expired"] += 1
                    counts["evaluated"] += 1
                    print(f"  ⏰ {ticker}: EXPIRED after {days_elapsed}d (max {max_hold}d) | no price data — settled unverified")
                    continue
                row["exit_price"] = round(last_close, 4)
                ret = (last_close - entry) / entry * 100
                row["actual_return_pct"] = round(ret, 2)
                risk = entry - sl
                row["r_multiple"] = round((last_close - entry) / risk, 2) if risk > 0 else 0
                # SPY relative perf for expired picks
                row["spy_close_at_exit"] = _add_spy_alpha(row, exit_bar_date.isoformat(), ret)
                row["sector_close_at_exit"] = _add_sector_alpha(row, exit_bar_date.isoformat(), ret)
                try:
                    _journal_attach(
                        ticker=row.get("ticker"),
                        pick_date=row.get("pick_date"),
                        r_multiple=float(row.get("r_multiple")) if row.get("r_multiple") not in (None, "", "None") else None,
                        actual_return_pct=float(ret) if ret is not None else None,
                        evaluated_on=exit_bar_date.isoformat(),
                    )
                except Exception as _e:
                    print(f"[eval] WARN journal_attach (expired) failed for {row.get('ticker','?')}: {_e}")  # M9
                counts["expired"] += 1
                counts["evaluated"] += 1
                alpha_str = f" | α={row.get('alpha_pct','?')}%" if row.get('alpha_pct') is not None else ""
                print(f"  ⏰ {ticker}: EXPIRED after {days_elapsed}d (max {max_hold}d) | exit ${last_close:.2f} on {exit_bar_date} | {ret:+.2f}% | {row['r_multiple']}R{alpha_str}")
            else:
                counts["still_open"] += 1
                print(f"  🟡 {ticker}: still open ({days_elapsed}d since pick)")

    _save_picks(rows)
    return counts
