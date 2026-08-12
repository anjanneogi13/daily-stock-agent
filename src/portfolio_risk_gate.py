"""Portfolio risk gate for Lane 1 official premarket SUGGESTIONS.

PR-A (2026-05-14) — agent is SUGGESTION-ONLY. It does not trade and does not
hold real positions. Pending rows in data/picks_log.csv are TRACKING rows for
weekly/monthly/yearly "if-you-had-bought" reports, NOT held positions.

Therefore this gate must NOT use the count of pending tracking rows as
"open positions" to compute available slots. Doing so jammed the gate
permanently May 11-14 2026 (NO_PICK_RISK_GATE_BLOCKED_ALL).

This gate is now a SAME-DAY DIVERSITY gate:
  - max_new_picks_per_day caps today's accepted suggestions (default 5).
  - max_per_sector / max_per_tag count only today's accepted candidates.
  - Per-candidate sanity (entry/SL/TP/qty/RR/risk%) unchanged.

Safety contract preserved: no fake picks, no paper trading, no live trading,
fail closed on malformed risk fields per-candidate.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


PICKS_LOG_PATH = Path("data/picks_log.csv")

DEFAULT_MAX_NEW_PICKS_PER_DAY = 5
DEFAULT_MAX_PER_SECTOR = 2
DEFAULT_MAX_PER_TAG = 2
DEFAULT_MIN_RISK_REWARD = 1.0
DEFAULT_MAX_PAIRWISE_CORRELATION = 0.7
DEFAULT_CORR_LOOKBACK_DAYS = 60
MIN_CORR_OVERLAP_OBS = 30  # need >=30 aligned return points to trust a correlation


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    # Bug fix (issue: only ~1 pick/day): `int(float(value or 0))` turned a
    # MISSING config key (None) into 0 instead of the caller's default, so
    # max_per_sector/max_per_tag collapsed to max(1, 0) == 1 and
    # corr_lookback_days to 2. Missing/blank must mean "use the default".
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _candidate_sector(candidate: dict) -> str:
    info = candidate.get("info_short") if isinstance(candidate.get("info_short"), dict) else {}
    return str(info.get("sector") or "Unknown").strip() or "Unknown"


# Placeholder sector labels that must NOT share one capped bucket. When the
# data provider cannot resolve a real sector it returns "N/A"/"Unknown"; with
# a shared bucket the whole day collapsed to max_per_sector picks total.
_UNKNOWN_SECTOR_LABELS = {"", "unknown", "n/a", "na", "none"}


def _is_unknown_sector(sector: str) -> bool:
    return str(sector or "").strip().lower() in _UNKNOWN_SECTOR_LABELS


def _candidate_tag(candidate: dict) -> str:
    scores = candidate.get("scores") if isinstance(candidate.get("scores"), dict) else {}
    raw = str(candidate.get("tag") or scores.get("sector_tag") or "").strip()
    return raw.split(" / ")[0].strip().upper() if raw else ""


def _candidate_score(candidate: dict) -> float:
    scores = candidate.get("scores") if isinstance(candidate.get("scores"), dict) else {}
    return _safe_float(scores.get("composite"), 0.0) or 0.0


def _trade_plan(candidate: dict) -> dict:
    plan = candidate.get("plan")
    return plan if isinstance(plan, dict) else {}


def _risk_profile(candidate: dict, account_size: float) -> dict:
    plan = _trade_plan(candidate)
    entry = _safe_float(plan.get("entry") or candidate.get("entry"))
    stop_loss = _safe_float(plan.get("stop_loss") or candidate.get("stop_loss"))
    take_profit = _safe_float(plan.get("take_profit") or candidate.get("take_profit"))
    quantity = _safe_int(plan.get("quantity") or candidate.get("quantity"), 0)
    risk_reward = _safe_float(plan.get("risk_reward") or candidate.get("risk_reward"))

    risk_dollars = None
    risk_pct = None
    if entry is not None and stop_loss is not None and quantity > 0:
        risk_dollars = max(0.0, (entry - stop_loss) * quantity)
        risk_pct = (risk_dollars / account_size * 100.0) if account_size > 0 else None

    return {
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "quantity": quantity,
        "risk_reward": risk_reward,
        "risk_dollars": round(risk_dollars, 2) if risk_dollars is not None else None,
        "risk_pct": round(risk_pct, 4) if risk_pct is not None else None,
    }


def load_open_positions_from_picks_log(path: Path = PICKS_LOG_PATH) -> list[dict]:
    """Load currently-pending tracking rows from picks_log.csv.

    NOTE (PR-A): RESERVED FOR REPORTING (weekly/monthly/yearly
    "if-you-had-bought" reports). NO LONGER consumed by the portfolio
    risk gate for slot accounting.
    """
    if not path.exists():
        # PR-A7 (audit PRG-21): was a SILENT fail-open. Now LOUD: operator
        # sees that downstream slot/concentration math has no history input.
        print(f"[portfolio_risk_gate] WARN: {path} missing — gate operating on empty history")
        return []
    rows: list[dict] = []
    try:
        with path.open(newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                status = str(row.get("evaluation_status") or "").strip().lower()
                watch_only = str(row.get("watch_only") or "").strip().lower() in {"1", "true", "yes"}
                if status == "pending" and not watch_only:
                    rows.append(row)
    except Exception:
        return []
    return rows


def build_portfolio_risk_config(cfg: dict | None) -> dict:
    cfg = cfg or {}
    risk = cfg.get("risk") if isinstance(cfg.get("risk"), dict) else {}

    account_size = _safe_float(risk.get("account_size"), 10000.0) or 10000.0
    risk_per_trade_pct = _safe_float(risk.get("risk_per_trade_pct"), 1.0) or 1.0

    raw_max_new = risk.get("max_new_picks_per_day", risk.get("max_positions", DEFAULT_MAX_NEW_PICKS_PER_DAY))
    return {
        "account_size": account_size,
        "risk_per_trade_pct": risk_per_trade_pct,
        "max_new_picks_per_day": max(1, _safe_int(raw_max_new, DEFAULT_MAX_NEW_PICKS_PER_DAY)),
        # Legacy alias kept for any downstream reader. Equal to max_new_picks_per_day now.
        "max_positions": max(1, _safe_int(raw_max_new, DEFAULT_MAX_NEW_PICKS_PER_DAY)),
        "max_per_sector": max(1, _safe_int(risk.get("max_per_sector"), DEFAULT_MAX_PER_SECTOR)),
        "max_per_tag": max(1, _safe_int(risk.get("max_per_tag"), DEFAULT_MAX_PER_TAG)),
        "min_risk_reward": _safe_float(risk.get("min_risk_reward"), DEFAULT_MIN_RISK_REWARD) or DEFAULT_MIN_RISK_REWARD,
        "max_pairwise_correlation": _safe_float(
            risk.get("max_pairwise_correlation"), DEFAULT_MAX_PAIRWISE_CORRELATION
        ),
        "corr_lookback_days": max(2, _safe_int(risk.get("corr_lookback_days"), DEFAULT_CORR_LOOKBACK_DAYS)),
    }


def _closes_from_history(history: Any, ticker: str):
    """Return a pandas Series of closes for `ticker`, or None.

    Robust to the normalized OHLCV frames (lowercase "close") AND raw
    yfinance frames ("Close"). Returns None on anything unusable so the
    caller can fail OPEN (never reject a pick because of missing/odd data).
    """
    if not history:
        return None
    frame = history.get(ticker) if hasattr(history, "get") else None
    if frame is None:
        return None
    try:
        # Accept a DataFrame (preferred) or a bare Series of closes.
        if hasattr(frame, "columns"):
            col = None
            for cand in ("close", "Close", "adj_close", "Adj Close"):
                if cand in frame.columns:
                    col = cand
                    break
            if col is None:
                return None
            series = frame[col]
        else:
            series = frame  # assume already a close series
        series = series.dropna()
        if len(series) == 0:
            return None
        return series
    except Exception:
        return None


def _pairwise_return_correlation(a_closes, b_closes, lookback: int):
    """Pearson correlation of daily % returns over the last `lookback` days,
    aligned on common dates. Returns None when there is insufficient overlap
    or any computation problem (caller treats None as "no rejection").
    """
    try:
        import pandas as pd  # local import: keep module import light + optional
        a = a_closes.tail(lookback + 1)
        b = b_closes.tail(lookback + 1)
        df = pd.concat([a, b], axis=1, join="inner")
        if df.shape[0] < 2:
            return None
        returns = df.pct_change().dropna()
        if returns.shape[0] < MIN_CORR_OVERLAP_OBS:
            return None  # thin overlap -> fail OPEN (do not reject)
        col_a = returns.iloc[:, 0]
        col_b = returns.iloc[:, 1]
        # Guard against a flat (zero-variance) series -> correlation undefined.
        if float(col_a.std()) == 0.0 or float(col_b.std()) == 0.0:
            return None
        corr = float(col_a.corr(col_b))
        if corr != corr:  # NaN check
            return None
        return corr
    except Exception:
        return None


def evaluate_candidate_portfolio_risk(
    candidate: dict,
    *,
    risk_config: dict,
    sector_counts: dict[str, int],
    tag_counts: dict[str, int],
) -> tuple[bool, str, dict]:
    account_size = risk_config["account_size"]
    profile = _risk_profile(candidate, account_size)
    sector = _candidate_sector(candidate)
    tag = _candidate_tag(candidate)

    detail = {
        "ticker": candidate.get("ticker"),
        "sector": sector,
        "tag": tag,
        "risk_profile": profile,
        "risk_config": risk_config,
    }

    if profile["entry"] is None or profile["entry"] <= 0:
        return False, "missing or invalid entry price", detail
    if profile["stop_loss"] is None or profile["stop_loss"] <= 0:
        return False, "missing or invalid stop loss", detail
    if profile["stop_loss"] >= profile["entry"]:
        return False, "stop loss is not below entry", detail
    if profile["take_profit"] is None or profile["take_profit"] <= profile["entry"]:
        return False, "take profit is not above entry", detail
    if profile["quantity"] <= 0:
        return False, "quantity is zero or missing", detail
    if profile["risk_reward"] is None or profile["risk_reward"] < risk_config["min_risk_reward"]:
        return False, f"risk/reward below minimum {risk_config['min_risk_reward']}", detail

    max_risk_pct = risk_config["risk_per_trade_pct"] * 1.05
    if profile["risk_pct"] is None or profile["risk_pct"] > max_risk_pct:
        return False, f"per-trade risk {profile['risk_pct']}% exceeds limit {max_risk_pct:.2f}%", detail

    if not _is_unknown_sector(sector) and sector_counts.get(sector, 0) >= risk_config["max_per_sector"]:
        return False, f"daily sector cap reached for {sector}", detail
    if tag and tag_counts.get(tag, 0) >= risk_config["max_per_tag"]:
        return False, f"daily tag cap reached for {tag}", detail

    return True, "ok", detail


def apply_portfolio_risk_gate(
    candidates: list[dict],
    cfg: dict | None,
    *,
    existing_positions: list[dict] | None = None,
    price_history: dict[str, Any] | None = None,
) -> tuple[list[dict], list[dict], dict]:
    """PR-A: existing_positions is IGNORED for slot accounting (kept in
    signature for backward compat). Today-only diversity cap.
    """
    risk_config = build_portfolio_risk_config(cfg)
    max_new = risk_config["max_new_picks_per_day"]

    sector_counts: dict[str, int] = {}
    tag_counts: dict[str, int] = {}

    # Task 8 (#28): 60-day return correlation guard. Disabled when threshold
    # >= 1.0 or no price_history supplied. Additive + fail-open: a correlation
    # problem must never zero-out the day, so it can only REJECT extra picks,
    # never cause a NO_PICK on its own.
    corr_threshold = risk_config.get("max_pairwise_correlation")
    corr_lookback = int(risk_config.get("corr_lookback_days", DEFAULT_CORR_LOOKBACK_DAYS))
    corr_enabled = bool(
        price_history
        and corr_threshold is not None
        and corr_threshold < 1.0
    )
    # ticker -> close series, cached for accepted finalists only.
    accepted_close_series: dict[str, Any] = {}
    correlation_rejections = 0

    allowed: list[dict] = []
    blocked: list[dict] = []

    for candidate in sorted(candidates, key=_candidate_score, reverse=True):
        ticker = candidate.get("ticker")

        if len(allowed) >= max_new:
            blocked.append({
                "ticker": ticker,
                "rejection_stage": "portfolio_risk",
                "block_type": "max_new_picks_per_day",
                "reason": f"reached max {max_new} new suggestions for today",
                "candidate": candidate,
                "detail": {"max_new_picks_per_day": max_new},
            })
            continue

        ok, reason, detail = evaluate_candidate_portfolio_risk(
            candidate,
            risk_config=risk_config,
            sector_counts=sector_counts,
            tag_counts=tag_counts,
        )
        if not ok:
            blocked.append({
                "ticker": ticker,
                "rejection_stage": "portfolio_risk",
                "block_type": "risk_limit",
                "reason": reason,
                "candidate": candidate,
                "detail": detail,
            })
            continue

        # Task 8 (#28): reject if too correlated with an already-accepted finalist.
        if corr_enabled:
            try:
                this_closes = _closes_from_history(price_history, ticker)
                if this_closes is not None:
                    worst = None  # (corr, other_ticker)
                    for other_tk, other_closes in accepted_close_series.items():
                        corr = _pairwise_return_correlation(this_closes, other_closes, corr_lookback)
                        if corr is None:
                            continue
                        if corr > corr_threshold and (worst is None or corr > worst[0]):
                            worst = (corr, other_tk)
                    if worst is not None:
                        correlation_rejections += 1
                        blocked.append({
                            "ticker": ticker,
                            "rejection_stage": "portfolio_risk",
                            "block_type": "correlation",
                            "reason": (
                                f"{corr_lookback}d return corr {worst[0]:.2f} with "
                                f"{worst[1]} exceeds {corr_threshold:.2f}"
                            ),
                            "candidate": candidate,
                            "detail": {
                                **detail,
                                "correlation": round(worst[0], 4),
                                "correlated_with": worst[1],
                                "correlation_threshold": corr_threshold,
                            },
                        })
                        continue
            except Exception as _ce:  # fail OPEN: never let corr math drop the day
                print(f"[portfolio_risk_gate] correlation check skipped for {ticker}: {_ce}")

        sector = detail["sector"]
        tag = detail["tag"]
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
        if tag:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        if corr_enabled:
            _cs = _closes_from_history(price_history, ticker)
            if _cs is not None:
                accepted_close_series[ticker] = _cs

        candidate["portfolio_risk"] = {
            "passed": True,
            "risk_profile": detail["risk_profile"],
            "risk_config": risk_config,
        }
        allowed.append(candidate)

    summary = {
        "risk_config": risk_config,
        "max_new_picks_per_day": max_new,
        # Legacy keys kept (set to None) so old readers don't crash.
        "open_position_count": None,
        "available_slots": None,
        "input_count": len(candidates),
        "allowed_count": len(allowed),
        "blocked_count": len(blocked),
        "today_sector_counts": sector_counts,
        "today_tag_counts": tag_counts,
        "final_sector_counts": sector_counts,
        "final_tag_counts": tag_counts,
        "correlation_guard_enabled": corr_enabled,
        "correlation_threshold": corr_threshold,
        "correlation_rejections": correlation_rejections,
    }
    return allowed, blocked, summary
