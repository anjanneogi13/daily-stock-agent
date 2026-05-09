"""Premarket sanity gate for Lane 1 official picks.

This gate runs after candidate selection but before official logging.

It prevents candidates from becoming normal official picks when fresh market
conditions make them unsafe or non-actionable.

Safety:
- no fake picks,
- no paper trading enablement,
- no live trading enablement,
- fail closed to watch-only/skip when fresh price cannot be verified.
"""

from __future__ import annotations

from typing import Any


ACTION_SAFE = "SAFE"
ACTION_HALF_SIZE = "HALF_SIZE"
ACTION_SKIP_TODAY = "SKIP_TODAY"
ACTION_WATCH_ONLY = "WATCH_ONLY"

ACTIONABLE_ACTIONS = {ACTION_SAFE, ACTION_HALF_SIZE}


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _extract_entry_stop(pick: dict) -> tuple[float | None, float | None]:
    plan = pick.get("plan") if isinstance(pick.get("plan"), dict) else {}
    entry = _safe_float(plan.get("entry") or pick.get("entry"))
    stop_loss = _safe_float(plan.get("stop_loss") or pick.get("stop_loss"))
    return entry, stop_loss


def evaluate_premarket_sanity(
    pick: dict,
    *,
    current_price: float | None,
    market_snapshot: dict | None = None,
) -> dict:
    """Evaluate one candidate for official premarket sanity.

    Returns a JSON-safe decision object.
    """
    ticker = pick.get("ticker", "?")
    entry, stop_loss = _extract_entry_stop(pick)
    market = market_snapshot or {}
    global_action = market.get("global_action", "normal")

    base = {
        "ticker": ticker,
        "current_price": current_price,
        "entry": entry,
        "stop_loss": stop_loss,
        "gap_pct": None,
        "action": ACTION_WATCH_ONLY,
        "actionable": False,
        "reason": "fresh quote unavailable",
        "size_multiplier": 0.0,
    }

    if entry is None or entry <= 0:
        base.update({
            "action": ACTION_WATCH_ONLY,
            "actionable": False,
            "reason": "missing or invalid entry price",
        })
        return base

    if stop_loss is None or stop_loss <= 0:
        base.update({
            "action": ACTION_WATCH_ONLY,
            "actionable": False,
            "reason": "missing or invalid stop loss",
        })
        return base

    if current_price is None or current_price <= 0:
        base.update({
            "action": ACTION_WATCH_ONLY,
            "actionable": False,
            "reason": "could not verify fresh price before official selection",
        })
        return base

    gap_pct = (current_price - entry) / entry * 100.0
    sl_buffer_pct = (entry - stop_loss) / entry * 100.0 if entry > 0 else 0.0
    base["gap_pct"] = round(gap_pct, 2)

    if global_action == "skip_all":
        base.update({
            "action": ACTION_SKIP_TODAY,
            "actionable": False,
            "reason": "broad market risk",
        })
        return base

    if current_price <= stop_loss:
        base.update({
            "action": ACTION_SKIP_TODAY,
            "actionable": False,
            "reason": f"price ${current_price:.2f} already at or below stop loss ${stop_loss:.2f}",
        })
        return base

    if sl_buffer_pct > 0 and gap_pct <= -sl_buffer_pct * 0.6:
        base.update({
            "action": ACTION_SKIP_TODAY,
            "actionable": False,
            "reason": f"negative gap {gap_pct:+.1f}% leaves too little stop-loss buffer",
        })
        return base

    if gap_pct >= 3.0:
        base.update({
            "action": ACTION_HALF_SIZE,
            "actionable": True,
            "reason": f"gapped up {gap_pct:+.1f}%; chasing risk requires half size",
            "size_multiplier": 0.5,
        })
        return base

    if global_action == "half":
        base.update({
            "action": ACTION_HALF_SIZE,
            "actionable": True,
            "reason": "market caution requires half size",
            "size_multiplier": 0.5,
        })
        return base

    if gap_pct <= -1.5:
        base.update({
            "action": ACTION_HALF_SIZE,
            "actionable": True,
            "reason": f"negative gap {gap_pct:+.1f}%; reduce size and require careful fill",
            "size_multiplier": 0.5,
        })
        return base

    base.update({
        "action": ACTION_SAFE,
        "actionable": True,
        "reason": "normal official premarket entry conditions",
        "size_multiplier": 1.0,
    })
    return base


def _apply_half_size(candidate: dict, sanity: dict) -> None:
    plan = candidate.get("plan") if isinstance(candidate.get("plan"), dict) else {}
    qty = _safe_float(plan.get("quantity"), 0.0) or 0.0
    if qty > 0:
        plan["quantity"] = max(1, int(qty * 0.5))
    plan["premarket_size_multiplier"] = 0.5
    plan["premarket_sanity_reason"] = sanity.get("reason", "")
    candidate["plan"] = plan


def apply_premarket_sanity_decisions(
    candidates: list[dict],
    *,
    current_prices: dict[str, float | None],
    market_snapshot: dict | None = None,
) -> tuple[list[dict], list[dict]]:
    """Split candidates into official/actionable and blocked-by-sanity lists."""
    official: list[dict] = []
    blocked: list[dict] = []

    for candidate in candidates:
        ticker = (candidate.get("ticker") or "").strip()
        sanity = evaluate_premarket_sanity(
            candidate,
            current_price=current_prices.get(ticker),
            market_snapshot=market_snapshot,
        )
        candidate["premarket_sanity"] = sanity
        candidate["premarket_action"] = sanity["action"]
        candidate["premarket_reason"] = sanity["reason"]
        candidate["premarket_actionable"] = sanity["actionable"]

        if sanity["action"] == ACTION_HALF_SIZE:
            _apply_half_size(candidate, sanity)

        if sanity["actionable"]:
            official.append(candidate)
        else:
            blocked.append({
                "ticker": ticker,
                "action": sanity["action"],
                "reason": sanity["reason"],
                "candidate": candidate,
                "sanity": sanity,
            })

    return official, blocked


def fetch_latest_price(ticker: str) -> float | None:
    """Fetch latest available daily close defensively.

    This intentionally mirrors the legacy premarket_check safety behavior.
    If a fresh quote cannot be verified, callers should fail closed.
    """
    try:
        import yfinance as yf

        hist = yf.Ticker(ticker).history(period="5d", auto_adjust=False)
        if len(hist):
            return float(hist["Close"].iloc[-1])
    except Exception:
        return None
    return None


def fetch_market_snapshot() -> dict:
    """Fetch broad-market snapshot used by the sanity gate."""
    spy = fetch_latest_price("SPY")
    qqq = fetch_latest_price("QQQ")
    soxx = fetch_latest_price("SOXX")
    vix = fetch_latest_price("^VIX")

    def _pct_change(ticker: str) -> float:
        try:
            import yfinance as yf

            hist = yf.Ticker(ticker).history(period="5d", auto_adjust=False)
            if len(hist) >= 2:
                prev = float(hist["Close"].iloc[-2])
                curr = float(hist["Close"].iloc[-1])
                return (curr - prev) / prev * 100.0
        except Exception:
            return 0.0
        return 0.0

    spy_chg = _pct_change("SPY")
    qqq_chg = _pct_change("QQQ")
    soxx_chg = _pct_change("SOXX")

    warnings: list[str] = []
    global_action = "normal"

    if spy_chg <= -1.5:
        warnings.append(f"SPY down {spy_chg:.1f}% — broad market selloff")
        global_action = "skip_all"
    elif spy_chg <= -0.7:
        warnings.append(f"SPY down {spy_chg:.1f}% — caution")
        global_action = "half"

    if vix is not None and vix >= 25:
        warnings.append(f"VIX at {vix:.1f} — high fear regime")
        global_action = "skip_all"
    elif vix is not None and vix >= 20 and global_action == "normal":
        warnings.append(f"VIX at {vix:.1f} — elevated volatility")
        global_action = "half"

    if soxx_chg <= -2.0:
        warnings.append(f"SOXX down {soxx_chg:.1f}% — semiconductor sector risk")

    return {
        "spy": spy,
        "qqq": qqq,
        "soxx": soxx,
        "vix": vix,
        "spy_change_pct": round(spy_chg, 2),
        "qqq_change_pct": round(qqq_chg, 2),
        "soxx_change_pct": round(soxx_chg, 2),
        "warnings": warnings,
        "global_action": global_action,
    }


def run_premarket_sanity_gate(candidates: list[dict]) -> tuple[list[dict], list[dict], dict]:
    """Fetch fresh prices and apply the premarket sanity gate."""
    market_snapshot = fetch_market_snapshot()
    current_prices = {
        (candidate.get("ticker") or "").strip(): fetch_latest_price((candidate.get("ticker") or "").strip())
        for candidate in candidates
        if (candidate.get("ticker") or "").strip()
    }
    official, blocked = apply_premarket_sanity_decisions(
        candidates,
        current_prices=current_prices,
        market_snapshot=market_snapshot,
    )
    return official, blocked, {
        "market_snapshot": market_snapshot,
        "current_prices": current_prices,
        "official_count": len(official),
        "blocked_count": len(blocked),
    }
