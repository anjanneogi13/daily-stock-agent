"""Lane 2 scanner: post-open / late-daily watch-only opportunity lane (v0).

Roadmap source: docs/planning/MULTI_LANE_IMPLEMENTATION_ROADMAP.md, Phase 3.

v0 is a READ-ONLY scanner over locally retained evidence artifacts:

- data/news_signals.json (Hearing / news engine output),
- data/watchlist.json (news watchlist items),
- data/picks_log.csv (read-only, for official-pick dedupe),
- data/late_daily_ideas_YYYY-MM-DD.jsonl (read-only, for cross-lane dedupe).

It performs NO network calls, NO quote lookups, and NO scoring changes.
Price levels are included only when the source payload already carries a
verified price; otherwise levels are honestly reported as unavailable.

Hard rules:

- watch-only output only,
- never official picks,
- never paper trades,
- never buy instructions,
- never mutates picks_log/journals/official artifacts.
"""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from src.performance_source_separation import is_watch_only_row
from src.post_open_contract import IDEA_TYPE, validate_post_open_opportunity

DATA_DIR = Path("data")
ET = ZoneInfo("America/New_York")

MIN_TRADEABLE_SCORE = 0.60
MAX_OPPORTUNITIES = 5

# Post-open lane display-score caps (stricter than the late-daily lane: this
# lane is younger and has no outcome evidence yet).
STANDARD_SCORE_CAP = 90.0
CORPORATE_ACTION_SCORE_CAP = 70.0

_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")

_CORPORATE_ACTION_RE = re.compile(
    r"business\s+combination|merger\s+sub|de-?spac|\bspac\b|deal\s+vote|"
    r"definitive\s+agreement\s+to\s+merge|shareholder\s+vote",
    re.IGNORECASE,
)


def _as_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_iso(value) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def signal_is_fresh(payload: dict, now_dt: datetime, *, max_age_hours: float = 24.0) -> bool:
    """A signal is fresh when not expired and observed within max_age_hours."""
    expires = _parse_iso(payload.get("expires"))
    if expires is not None and now_dt > expires:
        return False
    added_at = _parse_iso(payload.get("added_at"))
    if added_at is None:
        return False
    return (now_dt - added_at).total_seconds() <= max_age_hours * 3600


def is_valid_ticker(ticker: str) -> bool:
    return bool(_TICKER_RE.match(str(ticker or "").strip().upper()))


def _load_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def load_official_pick_tickers_for_date(
    date_str: str,
    picks_log_path: Path = DATA_DIR / "picks_log.csv",
) -> set[str]:
    """Read-only: official (non watch-only) pick tickers already logged today."""
    if not picks_log_path.exists():
        return set()
    tickers: set[str] = set()
    try:
        with picks_log_path.open() as f:
            for row in csv.DictReader(f):
                if (row.get("pick_date") or "").strip() != date_str:
                    continue
                if is_watch_only_row(row):
                    continue
                ticker = (row.get("ticker") or "").strip().upper()
                if ticker:
                    tickers.add(ticker)
    except OSError:
        return set()
    return tickers


def load_late_idea_tickers_for_date(
    date_str: str,
    data_dir: Path = DATA_DIR,
) -> set[str]:
    """Read-only: tickers already surfaced by the late-daily watch-only lane today."""
    path = data_dir / f"late_daily_ideas_{date_str}.jsonl"
    if not path.exists():
        return set()
    tickers: set[str] = set()
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            ticker = str(row.get("ticker") or "").strip().upper()
            if ticker:
                tickers.add(ticker)
    except OSError:
        return set()
    return tickers


def detect_risk_flags(text: str, *, source: str) -> list[str]:
    flags: list[str] = []
    if _CORPORATE_ACTION_RE.search(text or ""):
        flags.extend(["business_combination", "event_structure_uncertain", "no_event_arb_model"])
    if source == "news_signal":
        flags.append("news_only_no_breadth_confirmation")
    flags.append("post_open_lane_unvalidated")
    return flags


def compute_display_score(tradeable_score: float, score_delta: float, risk_flags: list[str]) -> tuple[float, str]:
    base = round(tradeable_score * 100.0, 1)
    boost = round(max(0.0, score_delta) * 100.0 * 0.1, 1)
    raw = base + boost
    cap = CORPORATE_ACTION_SCORE_CAP if "event_structure_uncertain" in risk_flags else STANDARD_SCORE_CAP
    display = min(raw, cap)
    explanation = (
        f"base={base} from tradeable_score={tradeable_score:.3f}; "
        f"positive_score_delta_boost={boost}; raw={raw}; cap={cap} "
        f"(post-open v0 cap — lane has no validated outcome evidence yet); "
        f"display_score={display}"
    )
    return display, explanation


def _reason_against(risk_flags: list[str]) -> str:
    reasons = []
    if "event_structure_uncertain" in risk_flags:
        reasons.append("corporate-action/event structure is uncertain and unmodeled")
    if "news_only_no_breadth_confirmation" in risk_flags:
        reasons.append("evidence is news-only with no breadth confirmation")
    reasons.append("post-open lane is unvalidated: no outcome evidence supports acting on this observation")
    return "; ".join(reasons)


def _candidate_from_payload(
    payload: dict,
    *,
    source: str,
    date_str: str,
    now_et: datetime,
    min_score: float,
) -> dict | None:
    ticker = str(payload.get("ticker") or payload.get("primary_ticker") or "").strip().upper()
    if not is_valid_ticker(ticker):
        return None
    if payload.get("hard_block") is True:
        return None

    sentiment = str(payload.get("sentiment") or "").strip().lower()
    score_delta = _as_float(payload.get("score_delta"), 0.0)
    if sentiment != "bullish" and not (sentiment == "" and score_delta > 0):
        return None

    tradeable_score = _as_float(payload.get("tradeable_score"), 0.0)
    if tradeable_score < min_score:
        return None

    headline = str(payload.get("headline") or "").strip()
    rationale = str(payload.get("rationale") or "").strip()
    if not headline and not rationale:
        return None

    risk_flags = detect_risk_flags(f"{headline} {rationale}", source=source)
    display_score, score_explanation = compute_display_score(tradeable_score, score_delta, risk_flags)

    price = payload.get("current_price")
    reference_price = None
    stop_loss = None
    take_profit = None
    level_basis = "no verified quote available; levels omitted (read-only v0 scanner does no lookups)"
    price_value = _as_float(price, 0.0)
    if price_value > 0:
        reference_price = round(price_value, 4)
        stop_loss = round(price_value * 0.985, 4)
        take_profit = round(price_value * 1.03, 4)
        level_basis = "source-payload price; simple 1.5% SL / 3.0% TP watch-only observation levels"

    row = {
        "ticker": ticker,
        "date": date_str,
        "idea_type": IDEA_TYPE,
        "source": source,
        "company_name": str(payload.get("company_name") or "").strip(),
        "headline": headline or rationale,
        "sentiment": sentiment or "bullish",
        "observed_at_et": now_et.isoformat(),
        "score": display_score,
        "score_explanation": score_explanation,
        "tradeable_score": tradeable_score,
        "score_delta": score_delta,
        "risk_flags": risk_flags,
        "reason_against": _reason_against(risk_flags),
        "watch_reference_price": reference_price,
        "watch_stop_loss": stop_loss,
        "watch_take_profit": take_profit,
        "level_basis": level_basis,
        "url": str(payload.get("url") or ""),
        "warning": (
            "Post-open watch-only observation. Monitoring-only. Not an official "
            "daily pick. Not an instruction to transact."
        ),
        "watch_only": True,
        "official_premarket_pick": False,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
    }

    errors = validate_post_open_opportunity(row)
    if errors:
        return None
    return row


def scan_post_open_opportunities(
    *,
    date_str: str,
    now: datetime | None = None,
    data_dir: Path = DATA_DIR,
    news_signals_path: Path | None = None,
    watchlist_path: Path | None = None,
    picks_log_path: Path | None = None,
    min_score: float = MIN_TRADEABLE_SCORE,
    max_results: int = MAX_OPPORTUNITIES,
) -> dict:
    """Scan retained local evidence for post-open watch-only opportunities.

    Returns a dict with `opportunities`, `counts`, and `data_readiness`.
    Read-only with respect to every input.
    """
    now_dt = now or datetime.now(timezone.utc)
    now_et = now_dt.astimezone(ET)

    news_signals_path = news_signals_path or (data_dir / "news_signals.json")
    watchlist_path = watchlist_path or (data_dir / "watchlist.json")
    picks_log_path = picks_log_path or (data_dir / "picks_log.csv")

    official_today = load_official_pick_tickers_for_date(date_str, picks_log_path)
    late_ideas_today = load_late_idea_tickers_for_date(date_str, data_dir)

    counts = {
        "news_signals_seen": 0,
        "watchlist_items_seen": 0,
        "stale_or_expired": 0,
        "skipped_official_pick_today": 0,
        "skipped_late_idea_duplicate": 0,
        "rejected_or_below_threshold": 0,
        "accepted": 0,
    }

    by_ticker: dict[str, dict] = {}

    def _consider(payload: dict, source: str) -> None:
        if not isinstance(payload, dict):
            return
        if not signal_is_fresh(payload, now_dt):
            counts["stale_or_expired"] += 1
            return
        candidate = _candidate_from_payload(
            payload, source=source, date_str=date_str, now_et=now_et, min_score=min_score
        )
        if candidate is None:
            counts["rejected_or_below_threshold"] += 1
            return
        ticker = candidate["ticker"]
        if ticker in official_today:
            counts["skipped_official_pick_today"] += 1
            return
        if ticker in late_ideas_today:
            counts["skipped_late_idea_duplicate"] += 1
            return
        if candidate["score"] > by_ticker.get(ticker, {}).get("score", -1):
            by_ticker[ticker] = candidate

    news_signals = _load_json(news_signals_path, {})
    if isinstance(news_signals, dict):
        for payload in news_signals.values():
            counts["news_signals_seen"] += 1
            _consider(payload, "news_signal")

    watchlist = _load_json(watchlist_path, {})
    items = []
    if isinstance(watchlist, dict) and isinstance(watchlist.get("items"), list):
        items = watchlist["items"]
    elif isinstance(watchlist, list):
        items = watchlist
    for payload in items:
        counts["watchlist_items_seen"] += 1
        _consider(payload, "watchlist")

    opportunities = sorted(
        by_ticker.values(),
        key=lambda row: (-float(row.get("score") or 0), str(row.get("ticker") or "")),
    )[:max_results]
    counts["accepted"] = len(opportunities)

    data_readiness = {
        "news_signals_available": news_signals_path.exists(),
        "watchlist_available": watchlist_path.exists(),
        "picks_log_available": picks_log_path.exists(),
        "late_daily_ideas_available": (data_dir / f"late_daily_ideas_{date_str}.jsonl").exists(),
        "quote_provider_used": False,
        "quote_provider_note": "v0 read-only scanner performs no quote lookups",
    }

    return {
        "opportunities": opportunities,
        "counts": counts,
        "data_readiness": data_readiness,
    }
