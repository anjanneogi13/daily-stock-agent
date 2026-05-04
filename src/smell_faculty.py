"""👃 SMELL FACULTY — Proactive danger detection.

Sniffs out red flags BEFORE a pick is finalized. Returns a list of warnings
that get displayed to user + can optionally block the pick if severity = HIGH.

Founder principle (PHILOSOPHY.md):
  'The agent should warn like a wise friend, not just block silently.'

Severity levels:
  CRITICAL  — Block the pick. User trust > one trade.
  HIGH      — Show prominent warning in Telegram.
  MED       — Show as note.
  LOW       — Log only, don't surface to user.

Each smell is a pure function of (pick, signals) → optional Warning.
Easy to test, easy to add new ones.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class Smell:
    code: str              # e.g., "earnings_imminent"
    severity: str          # CRITICAL | HIGH | MED | LOW
    message: str           # Human-readable warning
    blocking: bool = False # If True, the pick gets blocked


# ═══════════════════════════════════════════════════════════════
# Individual smells (each is independent + testable)
# ═══════════════════════════════════════════════════════════════

def smell_earnings_imminent(pick: Dict, sig: Dict) -> Optional[Smell]:
    """Earnings within 3 trading days = high gap risk."""
    d2e = pick.get("days_to_earnings")
    if d2e is None or d2e == "":
        return None
    try:
        d = int(d2e)
    except (TypeError, ValueError):
        return None
    if d < 0:
        return None
    if d <= 1:
        return Smell("earnings_tomorrow", "CRITICAL",
                     f"⚠ Earnings in {d} day — gap risk extreme. Consider waiting.",
                     blocking=True)
    if d <= 3:
        return Smell("earnings_imminent", "HIGH",
                     f"⚠ Earnings in {d} days — expect volatility. Use smaller size.")
    if d <= 7:
        return Smell("earnings_soon", "MED",
                     f"📅 Earnings in {d} days — be ready to exit before announcement.")
    return None


def smell_extreme_rsi(pick: Dict, sig: Dict) -> Optional[Smell]:
    """RSI > 80 (overbought) or < 20 (oversold but for swing buys, just overbought)."""
    rsi = sig.get("rsi") or pick.get("rsi")
    if rsi is None:
        return None
    try:
        r = float(rsi)
    except (TypeError, ValueError):
        return None
    if r >= 85:
        return Smell("rsi_blowoff", "CRITICAL",
                     f"⚠ RSI {r:.0f} — extreme overbought, blowoff risk. Wait for pullback.",
                     blocking=True)
    if r >= 75:
        return Smell("rsi_overbought", "HIGH",
                     f"⚠ RSI {r:.0f} — overbought, may pull back before continuing.")
    return None


def smell_volume_spike(pick: Dict, sig: Dict) -> Optional[Smell]:
    """Vol ratio > 3x = possible blowoff or news-driven move."""
    vr = sig.get("vol_ratio") or pick.get("vol_ratio")
    if vr is None:
        return None
    try:
        v = float(vr)
    except (TypeError, ValueError):
        return None
    if v >= 4.0:
        return Smell("volume_extreme", "HIGH",
                     f"📊 Volume {v:.1f}x average — likely news-driven, verify catalyst.")
    return None


def smell_gap_up(pick: Dict, sig: Dict) -> Optional[Smell]:
    """Today's open > 4% above yesterday's close = chasing."""
    open_pct = sig.get("gap_pct") or pick.get("gap_pct")
    if open_pct is None:
        return None
    try:
        g = float(open_pct)
    except (TypeError, ValueError):
        return None
    if g >= 5.0:
        return Smell("gap_up_chasing", "HIGH",
                     f"⚠ Gapped up {g:.1f}% — chasing risk, entry may be poor.")
    if g >= 3.0:
        return Smell("gap_up_modest", "MED",
                     f"📈 Gapped up {g:.1f}% — be patient on entry.")
    return None


def smell_low_liquidity(pick: Dict, sig: Dict) -> Optional[Smell]:
    """Avg daily volume < 500k shares = hard to exit cleanly."""
    avg_vol = sig.get("avg_volume") or pick.get("avg_volume")
    if avg_vol is None:
        return None
    try:
        v = float(avg_vol)
    except (TypeError, ValueError):
        return None
    if v < 100_000:
        return Smell("liquidity_critical", "CRITICAL",
                     f"⚠ Avg volume {v:,.0f}/day — illiquid, exits may slip.",
                     blocking=True)
    if v < 500_000:
        return Smell("liquidity_low", "HIGH",
                     f"⚠ Avg volume {v:,.0f}/day — low liquidity, use limit orders.")
    return None


def smell_tight_stop(pick: Dict, sig: Dict) -> Optional[Smell]:
    """Stop-loss < 1% from entry = likely to whipsaw out on noise."""
    try:
        entry = float(pick.get("entry") or 0)
        sl = float(pick.get("stop_loss") or 0)
    except (TypeError, ValueError):
        return None
    if entry <= 0 or sl <= 0:
        return None
    risk_pct = (entry - sl) / entry * 100
    if 0 < risk_pct < 0.8:
        return Smell("stop_too_tight", "HIGH",
                     f"⚠ Stop only {risk_pct:.1f}% away — likely to trigger on normal noise.")
    return None


# ═══════════════════════════════════════════════════════════════
# Registry — add new smells here
# ═══════════════════════════════════════════════════════════════
def smell_stale_price(pick: Dict, sig: Dict) -> Optional[Smell]:
    """Cross-check pick price against Finnhub /quote (E2c).

    Catches:
      - Stale yfinance prices (low-volume tickers occasionally lag)
      - Wrong-ticker disasters (would have caught the XXYYZZ123 case)
      - Pre/post-market price confusion
      - Delisted tickers (yfinance returns None or last known price)

    Severity tiers:
      - >5% disagreement → CRITICAL + blocking (don't trade bad data)
      - 2-5% disagreement → HIGH (warn in Telegram, allow trade)
      - <2% or Finnhub down → no smell (clean)

    NOTE: Adds ~0.3-1s per pick (one HTTP call). Acceptable overhead
    for end-of-day pipeline running on ~5-15 final picks.
    """
    ticker = pick.get("ticker")
    primary_price = pick.get("entry") or pick.get("currentPrice") or pick.get("price")
    if not ticker or primary_price is None:
        # Can't validate without inputs — let other smells (or upstream
        # fetch_info validation) catch the missing-data case.
        return None

    try:
        from src.finnhub_data import cross_validate_price
    except Exception:
        return None  # if helper missing, skip silently

    try:
        v = cross_validate_price(ticker, float(primary_price))
    except Exception:
        return None

    # Hard block: price disagreement >5% → likely bad data
    if not v["is_valid"]:
        # Distinguish "primary invalid" from "disagreement"
        if v.get("disagreement_pct"):
            return Smell(
                code="stale_price",
                severity="CRITICAL",
                blocking=True,
                message=(
                    f"Price disagreement {v['disagreement_pct']}% "
                    f"(yfinance ${primary_price:.2f} vs finnhub "
                    f"${v['second_price']:.2f}) — likely stale or wrong"
                ),
            )
        else:
            return Smell(
                code="stale_price",
                severity="CRITICAL",
                blocking=True,
                message=f"Invalid price for {ticker}: {v['reason']}",
            )

    # Soft warn: 2-5% disagreement (worth flagging but allow trade)
    if v.get("should_warn"):
        return Smell(
            code="stale_price",
            severity="HIGH",
            blocking=False,
            message=(
                f"Price drift {v['disagreement_pct']}% between sources "
                f"(yfinance ${primary_price:.2f} vs finnhub "
                f"${v['second_price']:.2f}) — verify before manual entry"
            ),
        )

    # Clean — no smell
    return None


ALL_SMELLS = [
    smell_earnings_imminent,
    smell_extreme_rsi,
    smell_volume_spike,
    smell_gap_up,
    smell_low_liquidity,
    smell_tight_stop,
    smell_stale_price,   # E2c.2 — cross-validate yfinance price vs Finnhub
]


def sniff(pick: Dict, sig: Optional[Dict] = None) -> List[Smell]:
    """Run all smells, return warnings sorted by severity."""
    sig = sig or {}
    warnings: List[Smell] = []
    for fn in ALL_SMELLS:
        try:
            w = fn(pick, sig)
            if w:
                warnings.append(w)
        except Exception:
            # A broken smell shouldn't break the agent
            continue
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MED": 2, "LOW": 3}
    warnings.sort(key=lambda w: severity_order.get(w.severity, 99))
    return warnings


def has_blocking_smell(pick: Dict, sig: Optional[Dict] = None) -> Optional[Smell]:
    """Returns the first CRITICAL+blocking smell, or None."""
    for w in sniff(pick, sig):
        if w.blocking:
            return w
    return None


def format_for_telegram(warnings: List[Smell]) -> str:
    """Render smells as Telegram-friendly bullet list."""
    if not warnings:
        return ""
    lines = ["", "*⚠ Smell-test warnings:*"]
    for w in warnings:
        lines.append(f"  • {w.message}")
    return "\n".join(lines)
