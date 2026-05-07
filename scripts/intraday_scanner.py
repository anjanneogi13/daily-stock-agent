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
                                     watchlist: list | None = None) -> list:
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
        })

    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates[:max_results]


def opening_range_observation_path(today: str | None = None) -> Path:
    """Return the JSONL artifact path for opening-range observations."""
    day = today or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return Path("data") / f"opening_range_observations_{day}.jsonl"


ET = ZoneInfo("America/New_York")


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
    with out.open("a") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    return len(rows)



def scan_for_new_opportunities(exclude: set, sent_alerts: set, max_results: int = 3) -> list:
    """Scan watchlist for new intraday opportunities.

    Opening-range breakouts are checked first and returned as monitoring-only
    watch-only ideas. The legacy momentum scan remains as a fallback.
    """
    opening_range = scan_opening_range_opportunities(
        exclude=exclude,
        sent_alerts=sent_alerts,
        max_results=max_results,
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
