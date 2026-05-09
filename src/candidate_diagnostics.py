"""Candidate diagnostics for Lane 1 official premarket decisions.

This module builds JSON-safe diagnostics that explain:
- what candidates existed,
- which candidates were selected,
- which candidates were rejected,
- why finalists were blocked.

It is reporting-only and does not alter scoring, trading, or notifications.
"""

from __future__ import annotations

from typing import Any


def _safe_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_safe_value(v) for v in value[:10]]
    if isinstance(value, dict):
        return {
            str(k): _safe_value(v)
            for k, v in list(value.items())[:30]
            if k not in {"df", "dataframe", "history"}
        }
    return str(value)


def summarize_candidate(candidate: dict | None) -> dict:
    """Return a compact JSON-safe candidate summary."""
    candidate = candidate or {}
    scores = candidate.get("scores") if isinstance(candidate.get("scores"), dict) else {}
    plan = candidate.get("plan") if isinstance(candidate.get("plan"), dict) else {}
    info = candidate.get("info_short") if isinstance(candidate.get("info_short"), dict) else {}
    news_signal = candidate.get("news_signal") if isinstance(candidate.get("news_signal"), dict) else {}
    news = candidate.get("news") if isinstance(candidate.get("news"), dict) else {}
    sanity = candidate.get("premarket_sanity") if isinstance(candidate.get("premarket_sanity"), dict) else {}

    return {
        "ticker": candidate.get("ticker"),
        "company": info.get("name") or candidate.get("company") or "",
        "sector": info.get("sector") or "",
        "score": scores.get("composite"),
        "trade_type": candidate.get("trade_type") or scores.get("trade_type"),
        "sector_tag": scores.get("sector_tag"),
        "day_score": scores.get("day_score"),
        "news_boost": scores.get("news_boost"),
        "news_action_window": (
            scores.get("news_action_window")
            or news_signal.get("action_window")
            or news.get("action_window")
        ),
        "entry": plan.get("entry"),
        "stop_loss": plan.get("stop_loss"),
        "take_profit": plan.get("take_profit"),
        "risk_reward": plan.get("risk_reward"),
        "quantity": plan.get("quantity"),
        "days_to_earnings": candidate.get("days_to_earnings"),
        "watch_only": bool(candidate.get("watch_only") or plan.get("watch_only")),
        "watch_only_reason": candidate.get("watch_only_reason") or plan.get("watch_only_reason") or "",
        "premarket_action": candidate.get("premarket_action") or sanity.get("action"),
        "premarket_actionable": candidate.get("premarket_actionable") if "premarket_actionable" in candidate else sanity.get("actionable"),
        "premarket_reason": candidate.get("premarket_reason") or sanity.get("reason", ""),
        "premarket_gap_pct": sanity.get("gap_pct"),
        "risk_flags": _safe_value(candidate.get("risk_flags") or []),
    }


def _summaries(items: list[dict] | None) -> list[dict]:
    return [summarize_candidate(item) for item in (items or [])]


def _ticker_set(items: list[dict] | None) -> set[str]:
    out = set()
    for item in items or []:
        ticker = str(item.get("ticker") or "").strip().upper()
        if ticker:
            out.add(ticker)
    return out


def _match_candidate_by_ticker(ticker: str, candidates: list[dict] | None) -> dict:
    ticker = str(ticker or "").strip().upper()
    for candidate in candidates or []:
        if str(candidate.get("ticker") or "").strip().upper() == ticker:
            return candidate
    return {}


def _hard_blocked_details(blocked: list[dict] | None, pre_hard: list[dict] | None) -> list[dict]:
    out = []
    for item in blocked or []:
        ticker = item.get("ticker")
        candidate = item.get("candidate") if isinstance(item.get("candidate"), dict) else {}
        if not candidate:
            candidate = _match_candidate_by_ticker(ticker, pre_hard)
        out.append({
            "ticker": ticker,
            "rejection_stage": "hard_block",
            "block_type": item.get("block_type"),
            "reason": item.get("reason"),
            "candidate": summarize_candidate(candidate),
        })
    return out


def _sanity_blocked_details(blocked: list[dict] | None) -> list[dict]:
    out = []
    for item in blocked or []:
        candidate = item.get("candidate") if isinstance(item.get("candidate"), dict) else {}
        out.append({
            "ticker": item.get("ticker"),
            "rejection_stage": "premarket_sanity",
            "action": item.get("action"),
            "reason": item.get("reason"),
            "sanity": _safe_value(item.get("sanity") or {}),
            "candidate": summarize_candidate(candidate),
        })
    return out


def _portfolio_risk_blocked_details(blocked: list[dict] | None) -> list[dict]:
    out = []
    for item in blocked or []:
        candidate = item.get("candidate") if isinstance(item.get("candidate"), dict) else {}
        out.append({
            "ticker": item.get("ticker"),
            "rejection_stage": "portfolio_risk",
            "block_type": item.get("block_type"),
            "reason": item.get("reason"),
            "detail": _safe_value(item.get("detail") or {}),
            "candidate": summarize_candidate(candidate),
        })
    return out


def _missing_data_blocked_details(blocked: list[dict] | None) -> list[dict]:
    out = []
    for item in blocked or []:
        candidate = item.get("candidate") if isinstance(item.get("candidate"), dict) else {}
        out.append({
            "ticker": item.get("ticker"),
            "rejection_stage": "missing_data",
            "block_type": item.get("block_type"),
            "reason": item.get("reason"),
            "missing_or_invalid_fields": _safe_value(item.get("missing_or_invalid_fields") or []),
            "required_field_snapshot": _safe_value(item.get("required_field_snapshot") or {}),
            "candidate": summarize_candidate(candidate),
        })
    return out


def build_candidate_diagnostics(
    *,
    pipeline: dict | None = None,
    scored_candidates: list[dict] | None = None,
    filtered_candidates: list[dict] | None = None,
    capped_candidates: list[dict] | None = None,
    pre_hard_block_candidates: list[dict] | None = None,
    hard_blocked_candidates: list[dict] | None = None,
    post_hard_block_candidates: list[dict] | None = None,
    pre_premarket_sanity_candidates: list[dict] | None = None,
    premarket_sanity_blocked_candidates: list[dict] | None = None,
    portfolio_risk_blocked_candidates: list[dict] | None = None,
    missing_data_blocked_candidates: list[dict] | None = None,
    selected_picks: list[dict] | None = None,
    extra_rejections: list[dict] | None = None,
    extra: dict | None = None,
) -> dict:
    """Build complete JSON-safe candidate diagnostics."""
    pipeline = pipeline or {}
    selected = _summaries(selected_picks)
    hard_blocked = _hard_blocked_details(hard_blocked_candidates, pre_hard_block_candidates)
    sanity_blocked = _sanity_blocked_details(premarket_sanity_blocked_candidates)
    portfolio_risk_blocked = _portfolio_risk_blocked_details(portfolio_risk_blocked_candidates)
    missing_data_blocked = _missing_data_blocked_details(missing_data_blocked_candidates)

    scored_set = _ticker_set(scored_candidates)
    filtered_set = _ticker_set(filtered_candidates)
    capped_set = _ticker_set(capped_candidates)
    selected_set = _ticker_set(selected_picks)

    rejected_candidates = []
    rejected_candidates.extend(hard_blocked)
    rejected_candidates.extend(sanity_blocked)
    rejected_candidates.extend(portfolio_risk_blocked)
    rejected_candidates.extend(missing_data_blocked)
    for item in extra_rejections or []:
        rejected_candidates.append(_safe_value(item))

    diagnostics = {
        "diagnostics_available": True,
        "pipeline": _safe_value(pipeline),
        "stage_counts": {
            "universe_count": int(pipeline.get("universe_count") or 0),
            "fetched_count": int(pipeline.get("fetched_count") or 0),
            "scored_count": len(scored_candidates or []),
            "filtered_count": len(filtered_candidates or []),
            "capped_count": len(capped_candidates or []),
            "pre_hard_block_pick_count": len(pre_hard_block_candidates or []),
            "hard_blocked_count": len(hard_blocked),
            "post_hard_block_pick_count": len(post_hard_block_candidates or []),
            "pre_premarket_sanity_pick_count": len(pre_premarket_sanity_candidates or []),
            "premarket_sanity_blocked_count": len(sanity_blocked),
            "portfolio_risk_blocked_count": len(portfolio_risk_blocked),
            "missing_data_blocked_count": len(missing_data_blocked),
            "selected_pick_count": len(selected),
            "rejected_candidate_count": len(rejected_candidates),
            "scored_not_filtered_count": len(scored_set - filtered_set) if scored_set and filtered_candidates is not None else 0,
            "filtered_not_capped_count": len(filtered_set - capped_set) if filtered_set and capped_candidates is not None else 0,
            "selected_ticker_count": len(selected_set),
        },
        "selected_picks": selected,
        "rejected_candidates": rejected_candidates,
        "pre_hard_block_candidates": _summaries(pre_hard_block_candidates),
        "hard_blocked_candidates": hard_blocked,
        "post_hard_block_candidates": _summaries(post_hard_block_candidates),
        "pre_premarket_sanity_candidates": _summaries(pre_premarket_sanity_candidates),
        "premarket_sanity_blocked_candidates": sanity_blocked,
        "portfolio_risk_blocked_candidates": portfolio_risk_blocked,
        "missing_data_blocked_candidates": missing_data_blocked,
    }

    if extra:
        diagnostics["extra"] = _safe_value(extra)

    return diagnostics
