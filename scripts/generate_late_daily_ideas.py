#!/usr/bin/env python3
"""Generate late watch-only daily ideas after the official premarket window.

This is a monitoring-only fallback for missed official daily picks.

It intentionally does NOT:
- create official picks,
- write to data/picks_log.csv,
- write to data/signal_journal.jsonl as official picks,
- create paper trades,
- enable live trading.

Output:
- data/late_daily_ideas_YYYY-MM-DD.jsonl
- data/late_daily_ideas_YYYY-MM-DD.md
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


try:
    import yfinance as yf
except Exception:  # pragma: no cover - dependency may be unavailable locally
    yf = None


ET = ZoneInfo("America/New_York")
DATA_DIR = Path("data")

MIN_TEXT_LEN = 12
VALID_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,6}$")
ACQUISITION_EVENT_RE = re.compile(
    r"(to acquire|acquire all|all outstanding shares|all-cash transaction|"
    r"per share|/shr|merger agreement|definitive agreement|take private|buyout)",
    re.IGNORECASE,
)

BUSINESS_COMBINATION_RE = re.compile(r"business combination|de-?spac|de spac", re.IGNORECASE)
MERGER_SUB_RE = re.compile(r"merger sub|merger subsidiary", re.IGNORECASE)
DEAL_VOTE_RE = re.compile(
    r"(shareholders? approve|shareholder vote|stockholder vote|special meeting|"
    r"proposals? related to business combination)",
    re.IGNORECASE,
)
CORPORATE_ACTION_RE = re.compile(
    r"(reverse split|stock split|redemption|warrant|rights offering|"
    r"exchange offer|tender offer|going private|takeover bid)",
    re.IGNORECASE,
)

STANDARD_NEWS_ONLY_SCORE_CAP = 95.0
EVENT_STRUCTURE_UNCERTAIN_SCORE_CAP = 75.0


def _as_float(value, default: float = 0.0) -> float:
    try:
        if value in (None, "", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _now_et(now: datetime | None = None) -> datetime:
    return (now or datetime.now(timezone.utc)).astimezone(ET)


def late_ideas_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"late_daily_ideas_{date_str}.jsonl"


def late_ideas_markdown_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"late_daily_ideas_{date_str}.md"


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def is_valid_ticker(ticker: str) -> bool:
    if not ticker:
        return False
    if not VALID_TICKER_RE.match(ticker):
        return False
    # Avoid known non-US/non-equity style symbols until we have a better
    # multi-asset late-ideas architecture.
    if ":" in ticker or ticker.endswith("USD"):
        return False
    return True


def has_enough_evidence(payload: dict) -> bool:
    headline = str(payload.get("headline") or "").strip()
    rationale = str(payload.get("rationale") or "").strip()
    return len(headline) >= MIN_TEXT_LEN or len(rationale) >= MIN_TEXT_LEN


def classify_catalyst_type(text: str) -> str:
    """Classify catalysts that need special watch-only handling."""
    raw = str(text or "").strip()
    if ACQUISITION_EVENT_RE.search(raw):
        return "acquisition_event_arbitrage"
    if (
        BUSINESS_COMBINATION_RE.search(raw)
        or MERGER_SUB_RE.search(raw)
        or DEAL_VOTE_RE.search(raw)
        or CORPORATE_ACTION_RE.search(raw)
    ):
        return "corporate_action_event_structure_uncertain"
    return "standard"


def detect_risk_flags(text: str, *, source: str) -> list[str]:
    """Detect late-news risks that should reduce score confidence."""
    raw = str(text or "")
    flags: list[str] = []

    if BUSINESS_COMBINATION_RE.search(raw):
        flags.append("business_combination")
    if re.search(r"\bspac\b|de-?spac|de spac", raw, re.IGNORECASE):
        flags.append("spac_or_de_spac")
    if MERGER_SUB_RE.search(raw):
        flags.append("merger_sub")
    if DEAL_VOTE_RE.search(raw):
        flags.append("deal_vote")
    if CORPORATE_ACTION_RE.search(raw):
        flags.append("corporate_action")

    if flags:
        flags.extend(["event_structure_uncertain", "no_event_arb_model"])

    if source in {"news_signal", "watchlist"}:
        flags.append("news_only_no_breadth_confirmation")

    # Preserve order while de-duping.
    return list(dict.fromkeys(flags))


def compute_display_score(
    *,
    tradeable_score: float,
    score_delta: float,
    risk_flags: list[str],
) -> tuple[float, str]:
    """Compute a capped 0-100 display score for late watch-only ideas.

    The display score is intentionally more conservative than the raw
    tradeable_score + positive score_delta sum. Late watch-only ideas are
    evidence, not official picks, and news-only ideas should not casually
    display as 100/100.
    """
    base = max(0.0, min(100.0, tradeable_score * 100.0))
    positive_delta = max(0.0, score_delta) * 100.0
    raw = max(0.0, min(100.0, base + positive_delta))

    cap = STANDARD_NEWS_ONLY_SCORE_CAP
    cap_reason = "standard late-news cap prevents news-only 100/100 display"
    event_flags = {
        "business_combination",
        "spac_or_de_spac",
        "merger_sub",
        "deal_vote",
        "corporate_action",
        "event_structure_uncertain",
        "no_event_arb_model",
    }
    if any(flag in event_flags for flag in risk_flags):
        cap = EVENT_STRUCTURE_UNCERTAIN_SCORE_CAP
        cap_reason = "corporate-action/event-structure cap; no event-arb model"

    score = round(min(raw, cap), 2)
    explanation = (
        f"base={base:.1f} from tradeable_score={tradeable_score:.3f}; "
        f"positive_score_delta_boost={positive_delta:.1f}; "
        f"raw={raw:.1f}; cap={cap:.1f} ({cap_reason}); "
        f"display_score={score:.1f}"
    )
    return score, explanation


def fetch_market_context(ticker: str) -> dict:
    """Best-effort quote/company enrichment.

    If yfinance is unavailable or quote lookup fails, return {}. The caller can
    decide whether to skip or keep the idea.
    """
    if yf is None:
        return {}

    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d", interval="5m", prepost=False)
        if hist is None or hist.empty:
            return {}

        price = float(hist["Close"].iloc[-1])
        day_low = float(hist["Low"].tail(78).min()) if "Low" in hist else None
        day_high = float(hist["High"].tail(78).max()) if "High" in hist else None

        prev_close = None
        daily = t.history(period="5d", interval="1d")
        if daily is not None and len(daily) >= 2:
            prev_close = float(daily["Close"].iloc[-2])

        company_name = ""
        try:
            info = getattr(t, "info", {}) or {}
            company_name = (
                info.get("shortName")
                or info.get("longName")
                or info.get("displayName")
                or ""
            )
        except Exception:
            company_name = ""

        change_pct = None
        if prev_close and prev_close > 0:
            change_pct = ((price - prev_close) / prev_close) * 100

        return {
            "company_name": company_name,
            "current_price": round(price, 2),
            "day_low": round(day_low, 2) if day_low else None,
            "day_high": round(day_high, 2) if day_high else None,
            "prev_close": round(prev_close, 2) if prev_close else None,
            "change_pct": round(change_pct, 2) if change_pct is not None else None,
        }
    except Exception as exc:
        print(f"[late-ideas] quote enrichment skipped for {ticker}: {exc}")
        return {}


def build_watch_only_levels(price: float) -> dict:
    """Create simple watch-only levels similar to a normal pick layout.

    These are observation levels only, not orders.
    """
    entry = round(price, 2)
    stop_loss = round(price * 0.985, 2)  # approx 1.5% risk
    take_profit = round(price * 1.03, 2)  # approx 3.0% upside
    risk = max(entry - stop_loss, 0.01)
    reward = max(take_profit - entry, 0.0)

    return {
        "watch_buy_price": entry,
        "watch_stop_loss": stop_loss,
        "watch_take_profit": take_profit,
        "risk_reward": round(reward / risk, 2) if risk else None,
        "level_basis": "current delayed quote; simple 1.5% SL / 3.0% TP observation levels",
    }


def _candidate_from_payload(
    payload: dict,
    *,
    source: str,
    now: datetime,
    min_score: float,
    require_quote: bool,
) -> dict | None:
    ticker = str(payload.get("ticker") or payload.get("primary_ticker") or "").strip().upper()
    if not is_valid_ticker(ticker):
        return None

    if not has_enough_evidence(payload):
        return None

    sentiment = str(payload.get("sentiment") or "").strip().lower()
    if sentiment and sentiment != "bullish":
        # v1 only surfaces long-side watch-only ideas. No short architecture yet.
        return None

    action_window = payload.get("action_window")
    if str(action_window or "").strip().lower() == "ignore":
        return None

    if payload.get("hard_block") is True:
        return None

    tradeable_score = _as_float(payload.get("tradeable_score"), 0.0)
    score_delta = _as_float(payload.get("score_delta"), 0.0)
    if tradeable_score < min_score:
        return None

    headline = str(payload.get("headline") or "").strip()
    rationale = str(payload.get("rationale") or "").strip()
    reason = rationale or headline or f"{source} late watch-only idea"

    evidence_text = f"{headline} {rationale}"
    catalyst_type = classify_catalyst_type(evidence_text)
    risk_flags = detect_risk_flags(evidence_text, source=source)

    # Acquisition / all-cash deal headlines are not normal momentum setups.
    # Until the product has a proper event-arb lane with deal-price parsing and
    # spread/risk display, suppress them from late watch-only ideas.
    if catalyst_type == "acquisition_event_arbitrage":
        return None

    market = fetch_market_context(ticker)
    company_name = market.get("company_name") or payload.get("company_name") or ""

    if require_quote and not market.get("current_price"):
        return None

    # Product safety: do not surface unresolved ticker/entity ideas. This blocks
    # cases like a blank-company, no-quote "X" row from a TMX Group headline.
    if not market.get("current_price") and not str(company_name).strip():
        return None

    levels = {}
    if market.get("current_price"):
        levels = build_watch_only_levels(float(market["current_price"]))

    score, score_explanation = compute_display_score(
        tradeable_score=tradeable_score,
        score_delta=score_delta,
        risk_flags=risk_flags,
    )

    generated_at = _now_et(now)
    date_str = generated_at.strftime("%Y-%m-%d")

    return {
        "date": date_str,
        "generated_at_et": generated_at.isoformat(timespec="seconds"),
        "idea_type": "late_daily_watch_only",
        "mode": "monitoring_only",
        "watch_only": True,
        "official_premarket_pick": False,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "ticker": ticker,
        "company_name": company_name,
        "source": source,
        "score": score,
        "tradeable_score": tradeable_score,
        "score_delta": score_delta,
        "score_explanation": score_explanation,
        "risk_flags": risk_flags,
        "sentiment": sentiment or "unknown",
        "action_window": action_window,
        "catalyst_type": catalyst_type,
        "headline": headline,
        "reason": reason,
        "url": payload.get("url") or "",
        "current_price": market.get("current_price"),
        "day_low": market.get("day_low"),
        "day_high": market.get("day_high"),
        "prev_close": market.get("prev_close"),
        "change_pct": market.get("change_pct"),
        **levels,
        "warning": (
            "Generated after the official 09:20 ET premarket cutoff. "
            "Monitoring-only. Not a buy instruction. Not an official daily pick."
        ),
    }


def build_late_ideas(
    *,
    news_signals_path: Path = DATA_DIR / "news_signals.json",
    watchlist_path: Path = DATA_DIR / "watchlist.json",
    max_results: int = 5,
    min_score: float = 0.40,
    now: datetime | None = None,
    require_quote: bool = False,
) -> list[dict]:
    now_dt = now or datetime.now(timezone.utc)
    by_ticker: dict[str, dict] = {}

    news_signals = load_json(news_signals_path, {})
    if isinstance(news_signals, dict):
        for payload in news_signals.values():
            if not isinstance(payload, dict):
                continue
            cand = _candidate_from_payload(
                payload,
                source="news_signal",
                now=now_dt,
                min_score=min_score,
                require_quote=require_quote,
            )
            if cand and cand["score"] > by_ticker.get(cand["ticker"], {}).get("score", -1):
                by_ticker[cand["ticker"]] = cand

    watchlist = load_json(watchlist_path, {})
    items = []
    if isinstance(watchlist, dict):
        raw = watchlist.get("items", [])
        if isinstance(raw, list):
            items = raw
    elif isinstance(watchlist, list):
        items = watchlist

    for payload in items:
        if not isinstance(payload, dict):
            continue
        cand = _candidate_from_payload(
            payload,
            source="watchlist",
            now=now_dt,
            min_score=min_score,
            require_quote=require_quote,
        )
        if cand and cand["score"] > by_ticker.get(cand["ticker"], {}).get("score", -1):
            by_ticker[cand["ticker"]] = cand

    out = sorted(
        by_ticker.values(),
        key=lambda x: (
            1 if x.get("current_price") else 0,  # quoted ideas first
            -float(x.get("score") or 0),
            str(x.get("ticker") or ""),
        ),
    )
    return out[:max_results]


def _display_name(idea: dict) -> str:
    name = str(idea.get("company_name") or "").strip()
    return f"{idea['ticker']} — {name}" if name else idea["ticker"]


def _source_label(source: str) -> str:
    return str(source or "unknown").replace("_", "-")


def _level_text(idea: dict) -> list[str]:
    if idea.get("watch_buy_price") is None:
        return [
            "   Price levels: unavailable — quote lookup failed.",
            "   Do not act without manually checking live price, spread, and news.",
        ]

    return [
        f"   Watch-only reference level: ${float(idea['watch_buy_price']):.2f}",
        f"   Watch-only SL: ${float(idea['watch_stop_loss']):.2f}",
        f"   Watch-only TP: ${float(idea['watch_take_profit']):.2f}",
        f"   R/R: {float(idea.get('risk_reward') or 0):.2f}",
    ]


def format_markdown(ideas: list[dict], *, now: datetime | None = None) -> str:
    now_et = _now_et(now)
    lines = [
        "⚠️ PREMARKET WINDOW MISSED — LATE WATCH-ONLY DAILY IDEAS",
        "",
        f"Time: {now_et.strftime('%Y-%m-%d %H:%M ET')}",
        "",
        "Official daily picks were NOT sent because the 09:20 ET cutoff has passed.",
        "The ideas below are late watch-only monitoring ideas, not official premarket picks.",
        "Monitoring-only. Not buy instructions. Not paper trades.",
        "",
    ]

    if not ideas:
        lines.extend([
            "No qualified late watch-only ideas were found from current news/watchlist evidence.",
            "",
            "Educational only. Not financial advice.",
        ])
        return "\n".join(lines)

    for i, idea in enumerate(ideas, 1):
        action = idea.get("action_window") or "unspecified"
        headline = idea.get("headline") or idea.get("reason") or ""
        change = idea.get("change_pct")
        change_text = f" | Change: {change:+.2f}%" if isinstance(change, (int, float)) else ""

        risk_flags = idea.get("risk_flags") or []
        risk_text = ", ".join(risk_flags) if risk_flags else "none"
        explanation = idea.get("score_explanation") or "score explanation unavailable"

        lines.extend([
            f"{i}. { _display_name(idea) } — score {float(idea['score']):.1f}/100",
            f"   Source: {_source_label(idea.get('source', 'unknown'))} | Window: {action}{change_text}",
            f"   Score note: {explanation}",
            f"   Risk flags: {risk_text}",
            *_level_text(idea),
            f"   Catalyst: {headline[:220]}",
            "   WATCH ONLY — do not treat as an official pick or buy instruction.",
            "",
        ])

    lines.append("Educational only. Not financial advice.")
    msg = "\n".join(lines)
    return msg[:3950] + "\n\n(truncated)" if len(msg) > 4000 else msg


def write_outputs(ideas: list[dict], *, data_dir: Path = DATA_DIR, now: datetime | None = None) -> tuple[Path, Path]:
    now_et = _now_et(now)
    date_str = now_et.strftime("%Y-%m-%d")
    data_dir.mkdir(parents=True, exist_ok=True)

    jsonl = late_ideas_path(date_str, data_dir=data_dir)
    with jsonl.open("w", encoding="utf-8") as f:
        for idea in ideas:
            f.write(json.dumps(idea, sort_keys=True) + "\n")

    md = late_ideas_markdown_path(date_str, data_dir=data_dir)
    md.write_text(format_markdown(ideas, now=now), encoding="utf-8")
    return jsonl, md


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--min-score", type=float, default=0.40)
    parser.add_argument(
        "--require-quote",
        action="store_true",
        help="Skip ideas without current quote enrichment.",
    )
    args = parser.parse_args(argv)

    ideas = build_late_ideas(
        max_results=args.max_results,
        min_score=args.min_score,
        require_quote=args.require_quote,
    )
    jsonl, md = write_outputs(ideas)
    count_file = Path("/tmp/late_daily_ideas_count")
    count_file.write_text(str(len(ideas)))

    print(f"[late-ideas] wrote {len(ideas)} idea(s) to {jsonl}")
    print(f"[late-ideas] markdown: {md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
