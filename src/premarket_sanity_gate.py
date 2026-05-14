"""Premarket sanity gate for Lane 1 official premarket SUGGESTIONS.

PR-A (2026-05-14) behavior changes:
  1. Multi-provider fetch with per-call timeout:
     yfinance intraday -> finnhub -> stooq -> yfinance daily.
     Batch runs in parallel via ThreadPoolExecutor.
  2. When fresh price cannot be verified, candidate is NOT blocked.
     It is marked HALF_SIZE with provider_unverified=True. The agent's
     job is to suggest daily; "couldn't fetch" is not a reason to deny
     all suggestions for the day.
  3. Block-all may only be triggered by REAL safety conditions:
     price already <= stop_loss, gap too negative, or market skip_all.

Safety: no fake picks, no paper trading, no live trading.
"""

from __future__ import annotations

import concurrent.futures
import time
from typing import Any


ACTION_SAFE = "SAFE"
ACTION_HALF_SIZE = "HALF_SIZE"
ACTION_SKIP_TODAY = "SKIP_TODAY"
ACTION_WATCH_ONLY = "WATCH_ONLY"

ACTIONABLE_ACTIONS = {ACTION_SAFE, ACTION_HALF_SIZE}

_PRICE_CACHE: dict = {}
_PRICE_CACHE_TTL = 60.0
_FETCH_TIMEOUT = 5.0
_BATCH_TIMEOUT = 60.0


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


# ── Provider fallback chain ──────────────────────────────────────────────────

def _yf_intraday(ticker: str) -> float | None:
    import yfinance as yf
    hist = yf.Ticker(ticker).history(period="1d", interval="1m", auto_adjust=False)
    if len(hist):
        return float(hist["Close"].iloc[-1])
    return None


def _yf_daily(ticker: str) -> float | None:
    import yfinance as yf
    hist = yf.Ticker(ticker).history(period="5d", auto_adjust=False)
    if len(hist):
        return float(hist["Close"].iloc[-1])
    return None


def _finnhub_quote(ticker: str) -> float | None:
    try:
        from src import finnhub_data
    except Exception:
        return None
    fn = (
        getattr(finnhub_data, "get_latest_price", None)
        or getattr(finnhub_data, "get_quote", None)
        or getattr(finnhub_data, "latest_price", None)
    )
    if not callable(fn):
        return None
    try:
        v = fn(ticker)
        if isinstance(v, dict):
            v = v.get("c") or v.get("price") or v.get("close")
        return float(v) if v else None
    except Exception:
        return None


def _stooq_daily(ticker: str) -> float | None:
    try:
        from src.market_data_providers import stooq
    except Exception:
        return None
    fn = (
        getattr(stooq, "get_latest_price", None)
        or getattr(stooq, "fetch_latest", None)
    )
    if not callable(fn):
        return None
    try:
        v = fn(ticker)
        if isinstance(v, dict):
            v = v.get("close") or v.get("price")
        return float(v) if v else None
    except Exception:
        return None


def _call_with_timeout(fn, ticker: str, timeout: float = _FETCH_TIMEOUT) -> float | None:
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            return ex.submit(fn, ticker).result(timeout=timeout)
    except Exception:
        return None


def _fetch_with_fallbacks(ticker: str) -> float | None:
    """Try providers in order with per-call timeout. 60s in-process cache."""
    now = time.monotonic()
    cached = _PRICE_CACHE.get(ticker)
    if cached and (now - cached[0]) < _PRICE_CACHE_TTL:
        return cached[1]

    for fn in (_yf_intraday, _finnhub_quote, _stooq_daily, _yf_daily):
        try:
            v = _call_with_timeout(fn, ticker)
            if v is not None and v > 0:
                _PRICE_CACHE[ticker] = (now, float(v))
                return float(v)
        except Exception:
            continue

    _PRICE_CACHE[ticker] = (now, None)
    return None


# Public alias kept for backward compat
def fetch_latest_price(ticker: str) -> float | None:
    return _fetch_with_fallbacks(ticker)


# ── Sanity decision ──────────────────────────────────────────────────────────

def evaluate_premarket_sanity(
    pick: dict,
    *,
    current_price: float | None,
    market_snapshot: dict | None = None,
) -> dict:
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
        "action": ACTION_SAFE,
        "actionable": True,
        "reason": "normal official premarket entry conditions",
        "size_multiplier": 1.0,
        "provider_unverified": False,
    }

    if entry is None or entry <= 0:
        base.update({
            "action": ACTION_WATCH_ONLY, "actionable": False,
            "reason": "missing or invalid entry price", "size_multiplier": 0.0,
        })
        return base

    if stop_loss is None or stop_loss <= 0:
        base.update({
            "action": ACTION_WATCH_ONLY, "actionable": False,
            "reason": "missing or invalid stop loss", "size_multiplier": 0.0,
        })
        return base

    # PR-A change: provider failure does NOT block the daily suggestion.
    if current_price is None or current_price <= 0:
        if global_action == "skip_all":
            base.update({
                "action": ACTION_SKIP_TODAY, "actionable": False,
                "reason": "broad market risk and provider unverified",
                "size_multiplier": 0.0, "provider_unverified": True,
            })
            return base
        base.update({
            "action": ACTION_HALF_SIZE, "actionable": True,
            "reason": "fresh price unavailable from any provider; reduced size",
            "size_multiplier": 0.5, "provider_unverified": True,
        })
        return base

    gap_pct = (current_price - entry) / entry * 100.0
    sl_buffer_pct = (entry - stop_loss) / entry * 100.0 if entry > 0 else 0.0
    base["gap_pct"] = round(gap_pct, 2)

    if global_action == "skip_all":
        base.update({"action": ACTION_SKIP_TODAY, "actionable": False,
                     "reason": "broad market risk", "size_multiplier": 0.0})
        return base

    if current_price <= stop_loss:
        base.update({
            "action": ACTION_SKIP_TODAY, "actionable": False,
            "reason": f"price ${current_price:.2f} already at or below stop loss ${stop_loss:.2f}",
            "size_multiplier": 0.0,
        })
        return base

    if sl_buffer_pct > 0 and gap_pct <= -sl_buffer_pct * 0.6:
        base.update({
            "action": ACTION_SKIP_TODAY, "actionable": False,
            "reason": f"negative gap {gap_pct:+.1f}% leaves too little stop-loss buffer",
            "size_multiplier": 0.0,
        })
        return base

    if gap_pct >= 3.0:
        base.update({"action": ACTION_HALF_SIZE,
                     "reason": f"gapped up {gap_pct:+.1f}%; chasing risk requires half size",
                     "size_multiplier": 0.5})
        return base

    if global_action == "half":
        base.update({"action": ACTION_HALF_SIZE,
                     "reason": "market caution requires half size",
                     "size_multiplier": 0.5})
        return base

    if gap_pct <= -1.5:
        base.update({"action": ACTION_HALF_SIZE,
                     "reason": f"negative gap {gap_pct:+.1f}%; reduce size and require careful fill",
                     "size_multiplier": 0.5})
        return base

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
    candidates: list[dict], *, current_prices: dict[str, float | None],
    market_snapshot: dict | None = None,
) -> tuple[list[dict], list[dict]]:
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


def fetch_market_snapshot() -> dict:
    spy = _fetch_with_fallbacks("SPY")
    qqq = _fetch_with_fallbacks("QQQ")
    soxx = _fetch_with_fallbacks("SOXX")
    vix = _fetch_with_fallbacks("^VIX")

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
        "spy": spy, "qqq": qqq, "soxx": soxx, "vix": vix,
        "spy_change_pct": round(spy_chg, 2),
        "qqq_change_pct": round(qqq_chg, 2),
        "soxx_change_pct": round(soxx_chg, 2),
        "warnings": warnings,
        "global_action": global_action,
    }


def run_premarket_sanity_gate(candidates: list[dict]) -> tuple[list[dict], list[dict], dict]:
    """Parallel multi-provider price fetch with timeouts, then apply gate."""
    market_snapshot = fetch_market_snapshot()

    tickers = [
        (c.get("ticker") or "").strip()
        for c in candidates
        if (c.get("ticker") or "").strip()
    ]
    current_prices: dict[str, float | None] = {t: None for t in tickers}

    if tickers:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            futures = {ex.submit(_fetch_with_fallbacks, t): t for t in tickers}
            try:
                for fut in concurrent.futures.as_completed(futures, timeout=_BATCH_TIMEOUT):
                    t = futures[fut]
                    try:
                        current_prices[t] = fut.result()
                    except Exception:
                        current_prices[t] = None
            except concurrent.futures.TimeoutError:
                # Whole-batch wall clock exceeded; remaining tickers stay None.
                # Sanity gate now treats None as HALF_SIZE, not block.
                pass

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
        "provider_unverified_count": sum(
            1 for c in candidates
            if (c.get("premarket_sanity") or {}).get("provider_unverified")
        ),
    }
