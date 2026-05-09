"""Live quotes + simple opportunity scanner.

Scans a watchlist of liquid US tickers for sudden momentum + news catalysts
that weren't in the morning picks.
"""
import os, json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

try:
    import yfinance as yf
except ImportError:
    yf = None

from intraday_news import fetch_recent_news, classify_material
from src.opening_range_scanner import detect_opening_range_breakout

# Default watchlist — top liquid US names. Override by creating data/watchlist.txt
DEFAULT_WATCHLIST = [
    # Mega-cap tech
    "AAPL","MSFT","NVDA","GOOGL","META","AMZN","TSLA","AVGO","AMD","NFLX",
    # Semis / AI
    "TSM","ASML","MU","SMCI","ARM","PLTR","CRWD","SNOW","DDOG","NET",
    # Finance
    "JPM","BAC","GS","MS","V","MA","COIN","HOOD",
    # Consumer / health
    "WMT","COST","HD","NKE","SBUX","LLY","UNH","NVO","PFE",
    # Energy / industrial
    "XOM","CVX","CAT","BA","GE","DE",
    # ETFs (sentiment)
    "SPY","QQQ","IWM","XLK","XLF","XLE",
]

def load_watchlist() -> list:
    wl_file = Path("data/watchlist.txt")
    if wl_file.exists():
        return [t.strip().upper() for t in wl_file.read_text().splitlines() if t.strip()]
    return DEFAULT_WATCHLIST

def get_live_quote(ticker: str) -> dict:
    """Returns {price, change_pct, vol_ratio} or {} on failure."""
    if yf is None:
        return {}
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d", interval="5m", prepost=False)
        if hist.empty:
            return {}
        last_close = float(hist["Close"].iloc[-1])
        # previous day close
        daily = t.history(period="5d", interval="1d")
        prev_close = float(daily["Close"].iloc[-2]) if len(daily) >= 2 else last_close
        change_pct = (last_close - prev_close) / prev_close * 100 if prev_close else 0.0
        # volume vs 20-day avg
        avg_vol = float(daily["Volume"].tail(20).mean()) if len(daily) else 0
        today_vol = float(daily["Volume"].iloc[-1]) if len(daily) else 0
        vol_ratio = (today_vol / avg_vol) if avg_vol > 0 else 0
        return {
            "price": last_close,
            "change_pct": change_pct,
            "vol_ratio": vol_ratio,
            "prev_close": prev_close,
        }
    except Exception as e:
        print(f"[quote] {ticker}: {e}")
        return {}

def score_opportunity(quote: dict, has_catalyst: bool) -> float:
    """Simple intraday score 0-100."""
    if not quote:
        return 0
    score = 50
    # Momentum
    score += min(quote.get("change_pct", 0) * 4, 25)   # +1% = +4pts, capped
    # Volume confirmation
    vr = quote.get("vol_ratio", 0)
    if vr >= 2: score += 10
    if vr >= 3: score += 10
    # Catalyst
    if has_catalyst: score += 15
    return max(0, min(100, score))

def fetch_opening_range_bars(ticker: str) -> list:
    """Fetch today's 5-minute regular-session bars for opening-range scan.

    Returns list[dict] in the pure scanner bar shape. Empty list on any
    failure. This function is intentionally best-effort: opening-range scans
    must never break existing intraday monitoring.
    """
    if yf is None:
        return []
    try:
        hist = yf.Ticker(ticker).history(period="1d", interval="5m", prepost=False)
        if hist is None or hist.empty:
            return []

        bars = []
        for idx, row in hist.iterrows():
            bars.append({
                "ts": idx.to_pydatetime() if hasattr(idx, "to_pydatetime") else idx,
                "open": float(row.get("Open", 0) or 0),
                "high": float(row.get("High", 0) or 0),
                "low": float(row.get("Low", 0) or 0),
                "close": float(row.get("Close", 0) or 0),
                "volume": float(row.get("Volume", 0) or 0),
            })
        return bars
    except Exception as e:
        print(f"[opening-range] {ticker}: {e}")
        return []


def scan_opening_range_opportunities(exclude: set, sent_alerts: set,
                                     max_results: int = 3,
                                     watchlist: list | None = None,
                                     now: datetime | None = None) -> list:
    """Scan watchlist for opening-range breakouts.

    Monitoring-only: returned candidates are watch_only and must not be treated
    as trade instructions.
    """
    tickers = [t for t in (watchlist or load_watchlist()) if t not in exclude]
    candidates = []

    for ticker in tickers:
        quote = get_live_quote(ticker)
        bars = fetch_opening_range_bars(ticker)
        if not quote or not bars:
            continue

        if not opening_range_bars_match_session(bars, now=now):
            session_date = opening_range_bar_session_date(bars, now=now)
            expected_date = (now or datetime.now(timezone.utc)).astimezone(ET).strftime("%Y-%m-%d")
            print(
                f"[opening-range] {ticker}: stale bar session "
                f"{session_date or 'unknown'}; expected {expected_date}; skipping"
            )
            continue

        result = detect_opening_range_breakout(
            ticker,
            bars,
            prev_close=quote.get("prev_close"),
        )
        if not result.get("candidate"):
            continue

        fp = f"OR|{ticker}|{result.get('opening_range', {}).get('start', '')[:16]}"
        if fp in sent_alerts:
            continue
        sent_alerts.add(fp)

        price = result["price"]
        candidates.append({
            "ticker": ticker,
            "price": price,
            "score": 75 + min(float(result.get("breakout_pct") or 0) * 3, 15),
            "entry": result["entry"],
            "sl": result["stop_loss"],
            "tp": result["take_profit"],
            "reason": result["reason"],
            "watch_only": True,
            "mode": "monitoring_only",
            "scanner": "opening_range",
            "opening_range": result["opening_range"],
            "breakout_pct": result["breakout_pct"],
            "volume_ratio": result["volume_ratio"],
            "_opening_range_bars": bars,
        })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:max_results]


def opening_range_observation_path(today: str | None = None) -> Path:
    """Return the JSONL artifact path for opening-range observations."""
    day = today or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return Path("data") / f"opening_range_observations_{day}.jsonl"


ET = ZoneInfo("America/New_York")
NEW_OPPORTUNITY_CUTOFF_MINUTES = 15 * 60 + 15  # 15:15 ET


def new_opportunity_window_open(now: datetime | None = None) -> bool:
    """Return True when it is still reasonable to send new intraday ideas.

    Existing-pick monitoring can continue until close, but new watch-only
    opportunities after 15:15 ET create chase/overnight risk and confused
    product semantics. They should be recorded in future evidence layers,
    not pushed as fresh Telegram opportunities.
    """
    now_et = (now or datetime.now(timezone.utc)).astimezone(ET)
    minutes = now_et.hour * 60 + now_et.minute
    return minutes < NEW_OPPORTUNITY_CUTOFF_MINUTES


def _bar_ts_to_et(value, now: datetime | None = None) -> datetime:
    """Normalize a bar timestamp to America/New_York.

    This helper is intentionally forgiving because yfinance index timestamps
    can arrive as pandas timestamps, Python datetimes, or strings.
    """
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except Exception:
            dt = now or datetime.now(timezone.utc)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ET)


def opening_range_bar_session_date(bars: list[dict], now: datetime | None = None) -> str | None:
    """Return the ET session date represented by fetched opening-range bars."""
    dates = []
    for bar in bars or []:
        if not bar.get("ts"):
            continue
        dates.append(_bar_ts_to_et(bar.get("ts"), now=now).strftime("%Y-%m-%d"))
    return dates[-1] if dates else None


def opening_range_bars_match_session(
    bars: list[dict],
    now: datetime | None = None,
) -> bool:
    """True when fetched bars belong to the current ET session.

    yfinance can return the previous trading day before the current session has
    bars. Opening-range observations must not be emitted from stale-session bars.
    """
    now_et = (now or datetime.now(timezone.utc)).astimezone(ET)
    return opening_range_bar_session_date(bars, now=now) == now_et.strftime("%Y-%m-%d")


def opening_range_bar_path(ticker: str, today: str | None = None) -> Path:
    """Return the JSONL artifact path for one ticker's opening-range bars."""
    day = today or datetime.now(ET).strftime("%Y-%m-%d")
    safe_ticker = str(ticker or "UNKNOWN").upper().replace("/", "-")
    return Path("data") / "opening_range_bars" / day / f"{safe_ticker}.jsonl"


def normalize_opening_range_bar(ticker: str, bar: dict, now: datetime | None = None) -> dict:
    """Normalize a raw 5-minute bar into an auditable JSONL artifact row."""
    ts_et = _bar_ts_to_et(bar.get("ts"), now=now)
    return {
        "date": ts_et.strftime("%Y-%m-%d"),
        "ts": ts_et.isoformat(timespec="seconds"),
        "timestamp_utc": ts_et.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "ticker": str(ticker or "").upper(),
        "artifact": "opening_range_bar",
        "scanner": "opening_range",
        "mode": "monitoring_only",
        "watch_only": True,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "official_pick_stats_mutated": False,
        "open": float(bar.get("open") or 0),
        "high": float(bar.get("high") or 0),
        "low": float(bar.get("low") or 0),
        "close": float(bar.get("close") or 0),
        "volume": float(bar.get("volume") or 0),
        "source": "intraday_scanner",
    }


def _load_existing_opening_range_bar_rows(path: Path) -> list[dict]:
    """Load existing opening-range bar artifact rows, ignoring bad lines."""
    rows: list[dict] = []
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if isinstance(obj, dict):
            rows.append(obj)
    return rows


def _opening_range_bar_dedupe_key(row: dict) -> str:
    return str(row.get("ts") or row.get("timestamp_utc") or "")


def write_opening_range_bar_artifact(
    ticker: str,
    bars: list[dict],
    path: Path | None = None,
    now: datetime | None = None,
    merge_existing: bool = True,
) -> Path | None:
    """Write read-only opening-range bar rows for one ticker.

    Returns the path written, or None when there are no bars.

    The artifact is merge-safe by default. This matters because the first
    opening-range observation often occurs before enough forward bars exist for
    review. Later monitor runs should retain newly available bars without
    duplicating older rows or deleting already retained evidence.
    """
    if not bars:
        return None

    rows = [normalize_opening_range_bar(ticker, bar, now=now) for bar in bars]
    out = path or opening_range_bar_path(ticker, rows[0]["date"])
    out.parent.mkdir(parents=True, exist_ok=True)

    merged: dict[str, dict] = {}
    if merge_existing:
        for row in _load_existing_opening_range_bar_rows(out):
            key = _opening_range_bar_dedupe_key(row)
            if key:
                merged[key] = row

    for row in rows:
        key = _opening_range_bar_dedupe_key(row)
        if key:
            merged[key] = row

    final_rows = sorted(
        merged.values() if merge_existing else rows,
        key=lambda r: str(r.get("ts") or r.get("timestamp_utc") or ""),
    )

    with out.open("w", encoding="utf-8") as f:
        for row in final_rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    return out


def _load_opening_range_observation_rows(path: Path) -> tuple[list[dict], int]:
    """Load opening-range observation rows, returning rows and parse errors."""
    rows: list[dict] = []
    bad = 0
    if not path.exists():
        return rows, bad
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
        except Exception:
            bad += 1
            continue
        if isinstance(obj, dict):
            rows.append(obj)
    return rows, bad


def refresh_opening_range_bar_artifacts_for_observations(
    observation_path: Path | None = None,
    today: str | None = None,
    now: datetime | None = None,
    fetcher=None,
) -> dict:
    """Refresh bar artifacts for already-recorded opening-range observations.

    This repairs the retention gap where a candidate is observed before enough
    forward bars exist. Existing sent-alert de-duping can prevent the same
    candidate from being emitted again, so this function independently refreshes
    bar artifacts for tickers already present in the observation artifact.

    Observe-only: this does not create candidates, alerts, picks, or trades.
    """
    now_et = (now or datetime.now(timezone.utc)).astimezone(ET)
    day = today or now_et.strftime("%Y-%m-%d")
    obs_path = observation_path or opening_range_observation_path(day)
    rows, parse_errors = _load_opening_range_observation_rows(obs_path)

    tickers = sorted({
        str(r.get("ticker") or "").upper()
        for r in rows
        if r.get("scanner") == "opening_range" and r.get("watch_only") is True and r.get("ticker")
    })

    fetch = fetcher or fetch_opening_range_bars
    ticker_status: dict[str, dict] = {}
    refreshed_count = 0

    for ticker in tickers:
        bars = fetch(ticker)
        if not bars:
            ticker_status[ticker] = {
                "status": "not_refreshed_no_bars",
                "bar_count": 0,
                "reason": "provider returned no opening-range bars",
            }
            continue

        if not opening_range_bars_match_session(bars, now=now):
            ticker_status[ticker] = {
                "status": "not_refreshed_stale_session",
                "bar_count": len(bars),
                "reason": (
                    f"bar session {opening_range_bar_session_date(bars, now=now) or 'unknown'} "
                    f"does not match expected session {day}"
                ),
            }
            continue

        path = write_opening_range_bar_artifact(ticker, bars, now=now, merge_existing=True)
        retained_rows = _load_existing_opening_range_bar_rows(path) if path else []
        ticker_status[ticker] = {
            "status": "refreshed",
            "bar_count": len(bars),
            "retained_bar_count": len(retained_rows),
            "path": str(path) if path else "",
            "reason": "bar artifact refreshed/merged for existing opening-range observation",
        }
        refreshed_count += 1

    return {
        "artifact": "opening_range_bar_retention_refresh",
        "date": day,
        "observation_path": str(obs_path),
        "observation_file_exists": obs_path.exists(),
        "observation_count": len(rows),
        "observation_parse_errors": parse_errors,
        "ticker_count": len(tickers),
        "refreshed_count": refreshed_count,
        "skipped_count": len(tickers) - refreshed_count,
        "ticker_status": ticker_status,
        "observe_only": True,
        "production_scoring_effect": False,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "buy_instructions_enabled": False,
    }



def intraday_momentum_observation_path(today: str | None = None) -> Path:
    """Return the JSONL artifact path for generic momentum observations.

    Date is ET-scoped because this artifact answers questions about the US
    trading session.
    """
    day = today or datetime.now(ET).strftime("%Y-%m-%d")
    return Path("data") / f"intraday_momentum_observations_{day}.jsonl"


def build_intraday_momentum_observation(candidate: dict, now: datetime | None = None) -> dict:
    """Normalize a generic momentum candidate into an auditable observation row.

    This is not a trade record. It is monitoring-only evidence for later review
    and outcome joins.
    """
    now_et = (now or datetime.now(timezone.utc)).astimezone(ET)
    return {
        "date": now_et.strftime("%Y-%m-%d"),
        "ts": now_et.isoformat(timespec="seconds"),
        "timestamp_utc": now_et.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "ticker": candidate.get("ticker"),
        "scanner": "momentum",
        "source": "intraday_scanner",
        "mode": "monitoring_only",
        "watch_only": True,
        "candidate": True,
        "price": candidate.get("price"),
        "score": candidate.get("score"),
        "entry_observe": candidate.get("entry"),
        "stop_loss_observe": candidate.get("sl"),
        "take_profit_observe": candidate.get("tp"),
        "reason": candidate.get("reason", ""),
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "ready_for_paper_trading": False,
        "warning": "Monitoring-only. Not an official pick, not a paper trade, not a buy instruction.",
    }


def append_intraday_momentum_observations(
    candidates: list[dict],
    path: Path | None = None,
    now: datetime | None = None,
) -> int:
    """Append watch-only generic momentum observations to a JSONL artifact.

    Returns number of rows written. Non-momentum or non-watch-only opportunities
    are ignored so opening-range observations remain in their dedicated artifact.
    """
    rows = [
        build_intraday_momentum_observation(c, now=now)
        for c in candidates
        if c.get("scanner") == "momentum" and c.get("watch_only") is True
    ]

    if not rows:
        return 0

    out = path or intraday_momentum_observation_path(rows[0]["date"])
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    return len(rows)


def opening_range_run_status_path(today: str | None = None) -> Path:
    """Return the JSONL artifact path for opening-range run status.

    Date is ET-scoped because this artifact answers operational questions about
    the US trading session.
    """
    day = today or datetime.now(ET).strftime("%Y-%m-%d")
    return Path("data") / f"opening_range_run_status_{day}.jsonl"


def build_opening_range_run_status(
    *,
    event: str,
    result: str,
    reason: str = "",
    candidate_count: int = 0,
    alert_count: int = 0,
    observation_count: int = 0,
    telegram_sent: bool | None = None,
    now: datetime | None = None,
) -> dict:
    """Build a monitoring-only run-status row for opening-range/intraday scans."""
    now_et = (now or datetime.now(timezone.utc)).astimezone(ET)
    return {
        "date": now_et.strftime("%Y-%m-%d"),
        "timestamp_et": now_et.isoformat(timespec="seconds"),
        "timestamp_utc": now_et.astimezone(timezone.utc).isoformat(timespec="seconds"),
        "workflow": "intraday-monitor",
        "scanner": "opening_range",
        "event": event,
        "result": result,
        "reason": reason,
        "candidate_count": int(candidate_count or 0),
        "alert_count": int(alert_count or 0),
        "observation_count": int(observation_count or 0),
        "telegram_sent": telegram_sent,
        "mode": "monitoring_only",
        "watch_only": True,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "github": {
            "workflow": os.getenv("GITHUB_WORKFLOW", ""),
            "event_name": os.getenv("GITHUB_EVENT_NAME", ""),
            "run_id": os.getenv("GITHUB_RUN_ID", ""),
            "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT", ""),
            "sha": os.getenv("GITHUB_SHA", ""),
            "ref": os.getenv("GITHUB_REF", ""),
        },
    }


def append_opening_range_run_status(
    *,
    event: str,
    result: str,
    reason: str = "",
    candidate_count: int = 0,
    alert_count: int = 0,
    observation_count: int = 0,
    telegram_sent: bool | None = None,
    path: Path | None = None,
    now: datetime | None = None,
) -> Path:
    """Append one opening-range run-status row and return the path written."""
    record = build_opening_range_run_status(
        event=event,
        result=result,
        reason=reason,
        candidate_count=candidate_count,
        alert_count=alert_count,
        observation_count=observation_count,
        telegram_sent=telegram_sent,
        now=now,
    )
    out = path or opening_range_run_status_path(record["date"])
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
    return out


def build_opening_range_observation(candidate: dict, now: datetime | None = None) -> dict:
    """Normalize an opening-range candidate into an auditable observation row.

    This is not a trade record. It is a monitoring-only observation for later
    review/backtesting.
    """
    ts = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")
    opening_range = candidate.get("opening_range") or {}

    return {
        "ts": ts,
        "ticker": candidate.get("ticker"),
        "scanner": "opening_range",
        "mode": "monitoring_only",
        "watch_only": True,
        "candidate": True,
        "price": candidate.get("price"),
        "score": candidate.get("score"),
        "entry_observe": candidate.get("entry"),
        "stop_loss_observe": candidate.get("sl"),
        "take_profit_observe": candidate.get("tp"),
        "reason": candidate.get("reason", ""),
        "opening_range_start": opening_range.get("start"),
        "opening_range_end": opening_range.get("end"),
        "opening_range_high": opening_range.get("high"),
        "opening_range_low": opening_range.get("low"),
        "opening_range_width_pct": opening_range.get("width_pct"),
        "opening_range_volume": opening_range.get("volume"),
        "breakout_pct": candidate.get("breakout_pct"),
        "volume_ratio": candidate.get("volume_ratio"),
        "source": "intraday_scanner",
    }


def append_opening_range_observations(candidates: list[dict],
                                      path: Path | None = None,
                                      now: datetime | None = None) -> int:
    """Append watch-only opening-range observations to a JSONL artifact.

    Returns number of rows written. Non-opening-range or non-watch-only
    opportunities are ignored so legacy momentum alerts do not pollute this
    artifact.
    """
    rows = [
        build_opening_range_observation(c, now=now)
        for c in candidates
        if c.get("scanner") == "opening_range" and c.get("watch_only") is True
    ]

    if not rows:
        return 0

    out = path or opening_range_observation_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")

    for candidate in candidates:
        if candidate.get("scanner") != "opening_range" or candidate.get("watch_only") is not True:
            continue
        bars = candidate.get("_opening_range_bars") or []
        if bars:
            write_opening_range_bar_artifact(str(candidate.get("ticker") or ""), bars, now=now)

    return len(rows)



def scan_for_new_opportunities(
    exclude: set,
    sent_alerts: set,
    max_results: int = 3,
    now: datetime | None = None,
) -> list:
    """Scan watchlist for new intraday opportunities.

    Opening-range breakouts are checked first and returned as monitoring-only
    watch-only ideas. The legacy momentum scan remains as a fallback.
    """
    if not new_opportunity_window_open(now=now):
        now_et = (now or datetime.now(timezone.utc)).astimezone(ET)
        print(f"[scanner] New intraday opportunities suppressed after 15:15 ET ({now_et.strftime('%H:%M')} ET)")
        return []

    opening_range = scan_opening_range_opportunities(
        exclude=exclude,
        sent_alerts=sent_alerts,
        max_results=max_results,
        now=now,
    )
    if len(opening_range) >= max_results:
        return opening_range[:max_results]

    watchlist = [t for t in load_watchlist() if t not in exclude]
    candidates = list(opening_range)

    for ticker in watchlist:
        quote = get_live_quote(ticker)
        if not quote or quote.get("change_pct", 0) < 1.5:
            continue  # need >+1.5% intraday move
        if quote.get("vol_ratio", 0) < 1.5:
            continue  # need volume confirmation

        # Catalyst?
        news = fetch_recent_news(ticker, lookback_min=120)
        catalyst_headline = None
        for n in news:
            cat = classify_material(n.get("headline", ""))
            if cat in ("upgrade", "earnings", "guidance", "ma"):
                catalyst_headline = n.get("headline", "")[:120]
                break

        score = score_opportunity(quote, has_catalyst=bool(catalyst_headline))
        if score < 70:
            continue

        # Dedupe across runs
        fp = f"NEW|{ticker}|{int(score/10)}"
        if fp in sent_alerts:
            continue
        sent_alerts.add(fp)

        price = quote["price"]
        # Simple entry/SL/TP at 1.5% / 3% (R:R = 2.0)
        candidates.append({
            "ticker": ticker,
            "price": price,
            "score": score,
            "morning_score": 0,  # unknown — placeholder
            "entry": round(price, 2),
            "sl": round(price * 0.985, 2),
            "tp": round(price * 1.03, 2),
            "reason": catalyst_headline or f"+{quote['change_pct']:.1f}% on {quote['vol_ratio']:.1f}× volume",
            "watch_only": True,
            "mode": "monitoring_only",
            "scanner": "momentum",
        })

    # Opening-range candidates are intentionally prioritized over legacy
    # momentum alerts. They are time-sensitive early-session observations and
    # should remain first even if a generic momentum score is slightly higher.
    candidates.sort(
        key=lambda x: (
            0 if x.get("scanner") == "opening_range" else 1,
            -float(x.get("score") or 0),
        )
    )
    return candidates[:max_results]
