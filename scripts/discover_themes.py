#!/usr/bin/env python3
"""Dynamic Theme Discovery Radar v0 — observe-only.

Outputs:
- data/theme_discovery_YYYY-MM-DD.json
- data/theme_discovery_YYYY-MM-DD.md

Safety:
- observe-only
- no official score boost
- no paper trading
- no live trading
- no buy instructions
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean


DATA_DIR = Path("data")

SAFETY = {
    "observe_only": True,
    "official_score_boost_enabled": False,
    "production_scoring_effect": False,
    "paper_trading_enabled": False,
    "live_trading_enabled": False,
    "buy_instructions_enabled": False,
}

THEME_STOPWORDS = {
    "a", "about", "above", "adj", "after", "ahead", "all", "and", "announces",
    "are", "as", "at", "be", "beat", "beats", "between", "billion", "boost",
    "buy", "by", "cash", "close", "company", "conference", "corp", "corporation",
    "day", "down", "eps", "estimate", "estimates", "following", "for", "forecast",
    "from", "group", "guidance", "has", "holdings", "in", "inc", "international",
    "into", "its", "llc", "ltd", "maintains", "market", "million", "monday",
    "news", "of", "on", "over", "plc", "price", "q1", "q2", "q3", "q4",
    "raises", "rating", "report", "reports", "revenue", "sales", "shares",
    "stock", "target", "the", "their", "to", "today", "up", "update", "versus",
    "with", "yoy",

    # Generic market/news-provider words. These are evidence types, not themes.
    "analyst", "analysts", "buy", "capital", "earnings", "eps", "est", "estimate",
    "estimates", "estim", "estimat", "fy2026", "guidance", "maintain", "maintains",
    "miss", "misses", "outperform", "overweight", "pt", "sees", "ubs", "underweight",

    # Generic phrasing from classifier rationales/headlines.
    "action", "announc", "both", "but", "catalyst", "consensus", "creat", "drives",
    "expect", "expectations", "immediate", "indicat", "loss", "meaningful", "midpoint",
    "positive", "pressure", "represent", "result", "results", "significant",

    # Still too generic for theme leadership.
    "agreement", "business", "cut", "despite", "double", "forecasts", "lowers",
    "morgan", "operational", "stanley", "surprise", "that", "typically",

    # Broad non-theme labels that tend to come from classifier wording.
    "adjust", "beating", "exceed", "follow", "increase", "other", "performance",
    "raise", "strong", "trading", "upgrad",

    # Common analyst/provider names; useful evidence, not theme labels.
    "canaccord", "genuity",
}


def _safe_float(value, default: float | None = 0.0) -> float | None:
    try:
        if value in (None, "", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def _normalize_token(token: str) -> str:
    token = token.lower().strip("-_ ")
    replacements = {
        "semiconductors": "semiconductor",
        "chips": "chip",
        "agents": "agent",
        "models": "model",
        "launches": "launch",
        "launched": "launch",
    }
    if token in replacements:
        return replacements[token]
    if token.endswith("ing") and len(token) > 7:
        return token[:-3]
    if token.endswith("ed") and len(token) > 7:
        return token[:-2]
    if token.endswith("es") and len(token) > 7:
        return token[:-2]
    return token


def _tokenize(text: str) -> list[str]:
    raw = re.findall(r"[A-Za-z][A-Za-z0-9+\-]{1,}", str(text or ""))
    terms = []
    for token in raw:
        t = _normalize_token(token)
        if not t or t in THEME_STOPWORDS:
            continue
        if len(t) < 3 and t not in {"ai", "ev"}:
            continue
        if t.isdigit():
            continue
        terms.append(t)
    return terms


def extract_theme_terms(evidence: dict, *, max_terms: int = 12) -> list[str]:
    """Extract candidate theme terms from evidence text.

    Candidate themes are derived from the input evidence, not selected from a
    fixed founder-provided answer list.
    """
    category_text = str(evidence.get("category") or "").replace("_", " ")
    priority_tokens = _tokenize(category_text)

    fields = [
        evidence.get("category"),
        evidence.get("sector"),
        evidence.get("tag"),
        evidence.get("sector_tag"),
        evidence.get("company_name"),
        evidence.get("company"),
        evidence.get("headline"),
        evidence.get("rationale"),
    ]
    tokens = _tokenize(" ".join(str(x or "") for x in fields))

    bigrams = [
        f"{tokens[i]} {tokens[i + 1]}"
        for i in range(len(tokens) - 1)
        if tokens[i] != tokens[i + 1]
    ]

    # Keep unigrams first so direct evidence terms such as "ai", "cloud",
    # "robotics", or "security" are not crowded out by many one-off bigrams.
    token_counts = Counter(tokens)
    bigram_counts = Counter(bigrams)

    ranked_tokens = sorted(token_counts, key=lambda t: (-token_counts[t], t))
    ranked_bigrams = sorted(bigram_counts, key=lambda t: (-bigram_counts[t], t))

    # Preserve explicit structured labels (for example product_launch) before
    # free-text terms compete for the remaining slots.
    ranked: list[str] = []
    for term in priority_tokens:
        if term not in ranked:
            ranked.append(term)

    priority_bigram = " ".join(priority_tokens[:2]) if len(priority_tokens) >= 2 else ""
    if priority_bigram and priority_bigram not in ranked:
        ranked.append(priority_bigram)

    unigram_limit = min(len(ranked_tokens), max(6, max_terms // 2))
    for term in ranked_tokens[:unigram_limit]:
        if term not in ranked:
            ranked.append(term)
        if len(ranked) >= max_terms:
            return ranked[:max_terms]

    # Reserve room for phrase evidence so "generative ai" / "cloud security"
    # style themes survive, while direct unigrams still lead.
    for term in ranked_bigrams:
        if term not in ranked:
            ranked.append(term)
        if len(ranked) >= max_terms:
            break
    return ranked[:max_terms]


def _watchlist_items(raw) -> list[dict]:
    if isinstance(raw, dict):
        items = raw.get("items", [])
        return [x for x in items if isinstance(x, dict)] if isinstance(items, list) else []
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    return []


def _news_signal_items(raw) -> list[dict]:
    if isinstance(raw, dict):
        return [x for x in raw.values() if isinstance(x, dict)]
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    return []


def load_evidence(*, data_dir: Path) -> tuple[list[dict], dict]:
    watchlist_path = data_dir / "watchlist.json"
    news_signals_path = data_dir / "news_signals.json"
    picks_log_path = data_dir / "picks_log.csv"

    evidence: list[dict] = []

    for item in _watchlist_items(load_json(watchlist_path, {})):
        ticker = str(item.get("ticker") or "").upper()
        if ticker:
            evidence.append({**item, "ticker": ticker, "source": "watchlist", "watch_only": True})

    for item in _news_signal_items(load_json(news_signals_path, {})):
        ticker = str(item.get("ticker") or "").upper()
        if ticker:
            evidence.append({**item, "ticker": ticker, "source": "news_signal", "watch_only": True})

    if picks_log_path.exists():
        try:
            with picks_log_path.open(newline="") as f:
                for row in csv.DictReader(f):
                    ticker = str(row.get("ticker") or "").upper()
                    if ticker:
                        evidence.append({
                            **row,
                            "ticker": ticker,
                            "source": "picks_log",
                            "watch_only": str(row.get("watch_only") or "").lower() in {"1", "true", "yes"},
                        })
        except Exception:
            pass

    input_status = {
        "watchlist": {
            "path": str(watchlist_path),
            "exists": watchlist_path.exists(),
            "rows": sum(1 for e in evidence if e["source"] == "watchlist"),
        },
        "news_signals": {
            "path": str(news_signals_path),
            "exists": news_signals_path.exists(),
            "rows": sum(1 for e in evidence if e["source"] == "news_signal"),
        },
        "picks_log": {
            "path": str(picks_log_path),
            "exists": picks_log_path.exists(),
            "rows": sum(1 for e in evidence if e["source"] == "picks_log"),
        },
    }
    return evidence, input_status


def _theme_id(term: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", term.lower()).strip("_") or "unknown_theme"


def _sentiment_score(rows: list[dict]) -> float:
    score = 0
    for row in rows:
        sentiment = str(row.get("sentiment") or "").lower()
        if sentiment == "bullish":
            score += 1
        elif sentiment == "bearish":
            score -= 1
    return score / len(rows) if rows else 0.0


def _pick_returns(rows: list[dict]) -> list[float]:
    out = []
    for row in rows:
        if row.get("source") != "picks_log":
            continue
        value = _safe_float(row.get("actual_return_pct"), None)
        if value is not None:
            out.append(value)
    return out


RETURN_FIELD_ALIASES = {
    "one_day_return_pct": ("return_1d_pct", "one_day_return_pct", "1d_return_pct"),
    "five_day_return_pct": ("return_5d_pct", "five_day_return_pct", "5d_return_pct"),
    "twenty_day_return_pct": ("return_20d_pct", "twenty_day_return_pct", "20d_return_pct"),
    "sixty_day_return_pct": ("return_60d_pct", "sixty_day_return_pct", "60d_return_pct"),
}

RELATIVE_STRENGTH_FIELD_ALIASES = {
    "relative_strength_vs_spy_pct": ("relative_strength_vs_spy_pct", "spy_relative_strength_pct", "alpha_pct"),
    "relative_strength_vs_qqq_pct": ("relative_strength_vs_qqq_pct", "qqq_relative_strength_pct"),
    "sector_alpha_pct": ("sector_alpha_pct",),
}


def _first_float(row: dict, keys: tuple[str, ...]) -> float | None:
    for key in keys:
        value = _safe_float(row.get(key), None)
        if value is not None:
            return value
    return None


def _boolish(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "breakout", "new_high"}


def _count_boolish(rows: list[dict], keys: tuple[str, ...]) -> int:
    count = 0
    for row in rows:
        if any(_boolish(row.get(key)) for key in keys):
            count += 1
    return count


def _avg(values: list[float]) -> float | None:
    return round(mean(values), 4) if values else None


def _provider_evidence(date_str: str, data_dir: Path) -> dict:
    readiness = load_json(data_dir / f"data_readiness_{date_str}.json", {})
    health = load_json(data_dir / f"market_data_health_{date_str}.json", {})

    failure_type_totals: Counter[str] = Counter()
    if isinstance(health, dict):
        for provider in (health.get("providers") or {}).values():
            if not isinstance(provider, dict):
                continue
            for failure_type, value in (provider.get("failure_types") or {}).items():
                try:
                    failure_type_totals[str(failure_type)] += int(value or 0)
                except Exception:
                    continue

    return {
        "data_readiness_available": bool(readiness),
        "market_data_health_available": bool(health),
        "data_provider_status": readiness.get("data_provider_status", "") if isinstance(readiness, dict) else "",
        "official_pick_readiness_status": readiness.get("official_pick_readiness_status", "") if isinstance(readiness, dict) else "",
        "failure_type_totals": dict(sorted(failure_type_totals.items())),
    }


def _theme_market_evidence(rows: list[dict], *, date_str: str, data_dir: Path) -> dict:
    """Build observe-only market-evidence enrichment from existing fields only.

    No live fetches are performed. Missing evidence is explicitly reported.
    """
    return_values: dict[str, list[float]] = {}
    for output_key, aliases in RETURN_FIELD_ALIASES.items():
        vals = [
            value for value in (_first_float(row, aliases) for row in rows)
            if value is not None
        ]
        return_values[output_key] = vals

    relative_values: dict[str, list[float]] = {}
    for output_key, aliases in RELATIVE_STRENGTH_FIELD_ALIASES.items():
        vals = [
            value for value in (_first_float(row, aliases) for row in rows)
            if value is not None
        ]
        relative_values[output_key] = vals

    sector_etfs = sorted({
        str(row.get("sector_etf") or "").upper()
        for row in rows
        if str(row.get("sector_etf") or "").strip()
    })

    new_high_count = _count_boolish(rows, ("new_high", "is_new_high", "new_52w_high"))
    breakout_count = _count_boolish(rows, ("breakout", "is_breakout", "breakout_signal"))
    overextension_count = _count_boolish(rows, ("overextended", "is_overextended", "crowding_warning"))

    avg_returns = {key: _avg(vals) for key, vals in return_values.items()}
    avg_relative = {key: _avg(vals) for key, vals in relative_values.items()}

    evidence_points = (
        sum(len(vals) for vals in return_values.values())
        + sum(len(vals) for vals in relative_values.values())
        + len(sector_etfs)
        + new_high_count
        + breakout_count
        + overextension_count
    )

    provider = _provider_evidence(date_str, data_dir)

    if evidence_points == 0:
        return {
            "market_evidence_status": "unavailable_missing_market_evidence_fields",
            "missing_market_evidence_reason": (
                "No 1D/5D/20D/60D return, relative-strength, sector ETF, "
                "new-high, breakout, or overextension fields were available in theme evidence rows."
            ),
            "tickers_with_return_evidence": 0,
            **avg_returns,
            **avg_relative,
            "sector_etfs": [],
            "sector_etf_confirmation_status": "unavailable_missing_sector_etf_evidence",
            "new_high_count": 0,
            "breakout_count": 0,
            "overextension_count": 0,
            "market_quality_score_adjustment": 0.0,
            "provider_evidence": provider,
        }

    tickers_with_return_evidence = len({
        str(row.get("ticker") or "").upper()
        for row in rows
        if any(_first_float(row, aliases) is not None for aliases in RETURN_FIELD_ALIASES.values())
    })

    # Observe-only theme quality adjustment. This affects only this theme-radar
    # artifact, never official scoring.
    positive_return_avg = mean([
        value for value in [
            avg_returns.get("one_day_return_pct"),
            avg_returns.get("five_day_return_pct"),
            avg_returns.get("twenty_day_return_pct"),
            avg_returns.get("sixty_day_return_pct"),
        ]
        if value is not None
    ]) if any(v is not None for v in avg_returns.values()) else 0.0

    relative_avg = mean([
        value for value in [
            avg_relative.get("relative_strength_vs_spy_pct"),
            avg_relative.get("relative_strength_vs_qqq_pct"),
            avg_relative.get("sector_alpha_pct"),
        ]
        if value is not None
    ]) if any(v is not None for v in avg_relative.values()) else 0.0

    adjustment = 0.0
    adjustment += max(-5.0, min(5.0, positive_return_avg * 0.15))
    adjustment += max(-5.0, min(5.0, relative_avg * 0.20))
    adjustment += min(4.0, (new_high_count + breakout_count) * 0.75)
    adjustment -= min(4.0, overextension_count * 0.75)

    return {
        "market_evidence_status": "available_from_existing_evidence_fields",
        "missing_market_evidence_reason": "",
        "tickers_with_return_evidence": tickers_with_return_evidence,
        **avg_returns,
        **avg_relative,
        "sector_etfs": sector_etfs,
        "sector_etf_confirmation_status": (
            "available_from_picks_log" if sector_etfs else "unavailable_missing_sector_etf_evidence"
        ),
        "new_high_count": new_high_count,
        "breakout_count": breakout_count,
        "overextension_count": overextension_count,
        "market_quality_score_adjustment": round(adjustment, 4),
        "provider_evidence": provider,
    }


def classify_lifecycle(metrics: dict) -> str:
    breadth = metrics["breadth"]
    news_count = metrics["news_count"]
    watchlist_count = metrics["watchlist_count"]
    avg_tradeable = metrics["avg_tradeable_score"] or 0.0
    sentiment = metrics["sentiment_score"]
    avg_pick_return = metrics["avg_pick_return_pct"]

    if avg_pick_return is not None and avg_pick_return <= -5 and breadth >= 3:
        return "failed_theme"
    if sentiment < -0.25 and breadth >= 3:
        return "distribution_warning"
    if breadth >= 10 and avg_tradeable >= 0.80 and sentiment >= 0.45:
        return "crowded_momentum"
    if breadth >= 5 and avg_tradeable >= 0.70 and sentiment >= 0.35:
        return "confirmed_leadership"
    if breadth >= 3 and (news_count + watchlist_count) >= 3 and sentiment >= 0.20:
        return "emerging_theme"
    if (news_count + watchlist_count) >= 2 and breadth < 3:
        return "news_hype_unconfirmed"
    return "candidate_theme"


def _theme_risk_flags(metrics: dict, lifecycle_state: str, market_evidence: dict | None = None) -> list[str]:
    flags = ["observe_only_theme"]
    market_evidence = market_evidence or {}

    if lifecycle_state == "news_hype_unconfirmed":
        flags.append("news_hype_unconfirmed")
    if lifecycle_state == "crowded_momentum":
        flags.append("crowding_risk")
    if lifecycle_state in {"distribution_warning", "failed_theme"}:
        flags.append("negative_or_deteriorating_evidence")
    if metrics["breadth"] < 3:
        flags.append("low_breadth")
    if metrics["avg_tradeable_score"] is None:
        flags.append("missing_tradeable_score")

    if market_evidence.get("market_evidence_status") == "available_from_existing_evidence_fields":
        flags.append("market_evidence_available")
        if market_evidence.get("overextension_count", 0):
            flags.append("overextension_or_crowding_evidence")
    else:
        flags.append("price_relative_strength_unavailable_v0")

    return list(dict.fromkeys(flags))


def build_theme_discovery(
    *,
    date_str: str,
    data_dir: Path = DATA_DIR,
    min_evidence: int = 2,
) -> dict:
    evidence, input_status = load_evidence(data_dir=data_dir)

    buckets: dict[str, list[dict]] = defaultdict(list)
    for row in evidence:
        for term in extract_theme_terms(row):
            buckets[term].append(row)

    themes = []
    for term, rows in buckets.items():
        tickers = sorted({str(r.get("ticker") or "").upper() for r in rows if r.get("ticker")})
        source_counts = Counter(str(r.get("source") or "unknown") for r in rows)
        tradeable_scores = [
            _safe_float(r.get("tradeable_score"), None)
            for r in rows
            if _safe_float(r.get("tradeable_score"), None) is not None
        ]
        score_deltas = [
            _safe_float(r.get("score_delta"), None)
            for r in rows
            if _safe_float(r.get("score_delta"), None) is not None
        ]
        returns = _pick_returns(rows)

        metrics = {
            "theme": term,
            "theme_id": _theme_id(term),
            "breadth": len(tickers),
            "evidence_rows": len(rows),
            "news_count": source_counts.get("news_signal", 0),
            "watchlist_count": source_counts.get("watchlist", 0),
            "pick_log_count": source_counts.get("picks_log", 0),
            "avg_tradeable_score": round(mean(tradeable_scores), 4) if tradeable_scores else None,
            "avg_score_delta": round(mean(score_deltas), 4) if score_deltas else None,
            "sentiment_score": round(_sentiment_score(rows), 4),
            "avg_pick_return_pct": round(mean(returns), 4) if returns else None,
        }

        if metrics["evidence_rows"] < min_evidence or metrics["breadth"] < 1:
            continue

        lifecycle_state = classify_lifecycle(metrics)
        market_evidence = _theme_market_evidence(rows, date_str=date_str, data_dir=data_dir)
        metrics["market_quality_score_adjustment"] = market_evidence["market_quality_score_adjustment"]

        theme_score = (
            min(metrics["breadth"], 12) * 5
            + min(metrics["evidence_rows"], 20) * 2
            + max(metrics["sentiment_score"], -1) * 10
            + ((metrics["avg_tradeable_score"] or 0) * 25)
        )
        if metrics["avg_pick_return_pct"] is not None:
            theme_score += max(-10, min(10, metrics["avg_pick_return_pct"]))
        theme_score += market_evidence["market_quality_score_adjustment"]

        evidence_examples = []
        seen_tickers = set()
        for row in rows:
            ticker = str(row.get("ticker") or "").upper()
            if ticker in seen_tickers:
                continue
            seen_tickers.add(ticker)
            evidence_examples.append({
                "ticker": ticker,
                "source": row.get("source"),
                "sentiment": row.get("sentiment") or "",
                "tradeable_score": _safe_float(row.get("tradeable_score"), None),
                "headline": row.get("headline") or row.get("rationale") or row.get("company") or "",
            })
            if len(evidence_examples) >= 6:
                break

        themes.append({
            **metrics,
            "theme_score": round(max(0.0, min(100.0, theme_score)), 2),
            "lifecycle_state": lifecycle_state,
            "tickers": tickers[:25],
            "evidence_examples": evidence_examples,
            "market_evidence": market_evidence,
            "risk_flags": _theme_risk_flags(metrics, lifecycle_state, market_evidence),
        })

    themes.sort(key=lambda t: (-t["theme_score"], -t["breadth"], t["theme"]))

    return {
        "artifact": "theme_discovery",
        "date": date_str,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        **SAFETY,
        "source_files": {
            "watchlist": str(data_dir / "watchlist.json"),
            "news_signals": str(data_dir / "news_signals.json"),
            "picks_log": str(data_dir / "picks_log.csv"),
            "data_readiness": str(data_dir / f"data_readiness_{date_str}.json"),
            "market_data_health": str(data_dir / f"market_data_health_{date_str}.json"),
        },
        "input_status": input_status,
        "data_provider_status": {
            "market_evidence": "available_when_existing_evidence_fields_present_else_reported_missing",
            "price_leadership": "derived_from_existing_new_high_breakout_fields_when_present",
            "one_day_return": "available_when_return_1d_pct_or_alias_present",
            "five_day_return": "available_when_return_5d_pct_or_alias_present",
            "twenty_day_return": "available_when_return_20d_pct_or_alias_present",
            "sixty_day_return": "available_when_return_60d_pct_or_alias_present",
            "relative_strength_vs_spy_qqq": "available_when_relative_strength_fields_or_alpha_pct_present",
            "sector_etf_confirmation": "available_from_picks_log_sector_etf_when_present",
            "overextension_crowding": "available_when_overextension_fields_present",
            "provider_status": _provider_evidence(date_str, data_dir),
            "news_clustering": "available",
            "watchlist_breadth": "available",
            "pick_log_return_evidence": "available_when_evaluated_rows_exist",
        },
        "method": {
            "version": "v1_observe_only_market_evidence",
            "description": (
                "Extracts candidate theme terms from watchlist, news-signal, and picks-log text; "
                "scores breadth, sentiment, tradeable-score evidence, pick-log outcomes, and "
                "observe-only market evidence when existing artifact fields are present. "
                "Missing market evidence is reported, not guessed. Does not apply official score boosts "
                "or trading instructions."
            ),
            "min_evidence": min_evidence,
        },
        "themes": themes,
        "theme_count": len(themes),
        "safety_flags": [
            "observe_only",
            "not_official_scoring",
            "not_paper_trade",
            "not_live_trade",
            "no_buy_instructions",
            "theme_candidates_derived_from_evidence",
        ],
    }


def theme_json_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"theme_discovery_{date_str}.json"


def theme_markdown_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"theme_discovery_{date_str}.md"


def format_markdown(report: dict) -> str:
    lines = [
        "# Dynamic Theme Discovery Radar",
        "",
        "Observe-only. Not official scoring. Not buy instructions. Not paper/live trading.",
        "",
        f"- Date: **{report['date']}**",
        f"- Theme candidates: **{report['theme_count']}**",
        f"- Official score boost enabled: **{str(report['official_score_boost_enabled']).lower()}**",
        f"- Production scoring effect: **{str(report.get('production_scoring_effect')).lower()}**",
        f"- Paper trading enabled: **{str(report['paper_trading_enabled']).lower()}**",
        f"- Live trading enabled: **{str(report['live_trading_enabled']).lower()}**",
        "",
        "## Data Provider Status",
    ]

    for key, value in report["data_provider_status"].items():
        lines.append(f"- {key}: **{value}**")

    lines.extend(["", "## Top Themes"])
    if not report["themes"]:
        lines.append("- No candidate themes met the evidence threshold.")
    else:
        for theme in report["themes"][:20]:
            tickers = ", ".join(theme["tickers"][:12]) or "n/a"
            lines.extend([
                (
                    f"- **{theme['theme']}** "
                    f"({theme['lifecycle_state']}, score={theme['theme_score']}, "
                    f"breadth={theme['breadth']}, evidence={theme['evidence_rows']})"
                ),
                f"  - Tickers: `{tickers}`",
                (
                    "  - Evidence: "
                    f"news={theme['news_count']}, watchlist={theme['watchlist_count']}, "
                    f"pick_log={theme['pick_log_count']}, "
                    f"avg_tradeable={theme['avg_tradeable_score']}, "
                    f"sentiment={theme['sentiment_score']}, "
                    f"avg_pick_return={theme['avg_pick_return_pct']}"
                ),
                (
                    "  - Market evidence: "
                    f"status={theme.get('market_evidence', {}).get('market_evidence_status')}, "
                    f"1d={theme.get('market_evidence', {}).get('one_day_return_pct')}, "
                    f"5d={theme.get('market_evidence', {}).get('five_day_return_pct')}, "
                    f"20d={theme.get('market_evidence', {}).get('twenty_day_return_pct')}, "
                    f"60d={theme.get('market_evidence', {}).get('sixty_day_return_pct')}, "
                    f"vs_spy={theme.get('market_evidence', {}).get('relative_strength_vs_spy_pct')}, "
                    f"adjustment={theme.get('market_evidence', {}).get('market_quality_score_adjustment')}"
                ),
                f"  - Risk flags: `{', '.join(theme['risk_flags'])}`",
            ])
            for ex in theme["evidence_examples"][:3]:
                headline = str(ex.get("headline") or "")[:140]
                lines.append(f"    - {ex.get('ticker')} [{ex.get('source')}]: {headline}")

    lines.extend([
        "",
        "## Safety",
        "- Observe-only theme radar.",
        "- Does not change official scoring.",
        "- Does not create picks.",
        "- Does not enable paper or live trading.",
        "- No buy instructions.",
    ])
    return "\n".join(lines)


def write_outputs(report: dict, *, data_dir: Path = DATA_DIR) -> tuple[Path, Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    date_str = report["date"]

    json_path = theme_json_path(date_str, data_dir=data_dir)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    md_path = theme_markdown_path(date_str, data_dir=data_dir)
    md_path.write_text(format_markdown(report) + "\n", encoding="utf-8")
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    parser.add_argument("--min-evidence", type=int, default=2)
    args = parser.parse_args(argv)

    report = build_theme_discovery(
        date_str=args.date,
        data_dir=Path(args.data_dir),
        min_evidence=args.min_evidence,
    )
    json_path, md_path = write_outputs(report, data_dir=Path(args.data_dir))

    print(f"[theme-discovery] wrote {report['theme_count']} theme(s) to {json_path}")
    print(f"[theme-discovery] markdown: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
