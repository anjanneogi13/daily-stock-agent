"""
Probability Engine v0.1 — Multi-Signal Decision Brain

INTEGRATION SCAFFOLD that wires together all existing intelligence:
  - Layer 1: Empirical price-history base rates (src/stock_stats.py)
  - Layer 2: Market regime conditioning (src/regime.py)
  - Layer 3: News + sentiment posteriors (src/news_classifier.py)
  - Layer 4: Catalyst conditioning (src/earnings.py)
  - Layer 5: Multi-signal combiner (heuristic, not full Bayesian YET)
  - Layer 6: Decision output (SL/TP/buy/trigger prices)

HONEST STATUS: This is v0.1 — REAL integration, HEURISTIC math.
The combiner uses simple multiplicative adjustments based on signal
strength, NOT proper Bayesian inference. Future v0.2 will replace
the combiner with logistic regression trained on historical outcomes.

WHAT IT REPLACES:
  - Hardcoded ATR×1.5 SL → empirical per-stock SL adjusted by signals
  - Arbitrary 3% TP → empirical TP adjusted by regime/news/catalyst
  - One-size-fits-all rules → conditional probability per stock per state

See: docs/BRAIN_ARCHITECTURE.md (Pillars 1-5)
See: docs/PROBABILITY_ENGINE_DESIGN.md
See: docs/decisions/ADR-001
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

# Allow running both as module (python -m src.probability_engine) 
# and as script (python src/probability_engine.py)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.stock_stats import (
    load_stats,
    empirical_sl_pct,
    empirical_tp_pct,
)


# ─── Configuration ─────────────────────────────────────────────────

# Heuristic adjustments applied to empirical base rates.
# These are PRIORS — will be replaced with learned weights in v0.2.

REGIME_ADJUSTMENTS = {
    "bull":         {"sl_mult": 1.0,  "tp_mult": 1.2, "p_win_boost": +0.05},
    "bear":         {"sl_mult": 0.8,  "tp_mult": 0.7, "p_win_boost": -0.10},
    "transition":   {"sl_mult": 0.9,  "tp_mult": 0.9, "p_win_boost": -0.02},
    "unknown":      {"sl_mult": 1.0,  "tp_mult": 1.0, "p_win_boost":  0.0},
}

NEWS_ADJUSTMENTS = {
    # tradeable_score buckets → multipliers on TP and P(win)
    "huge_positive":  {"tp_mult": 1.4, "p_win_boost": +0.12},  # score ≥ 0.9
    "strong_positive":{"tp_mult": 1.2, "p_win_boost": +0.08},  # 0.7-0.9
    "mild_positive":  {"tp_mult": 1.05,"p_win_boost": +0.03},  # 0.5-0.7
    "neutral":        {"tp_mult": 1.0, "p_win_boost":  0.0},   # 0-0.5 or none
    "mild_negative":  {"tp_mult": 0.85,"p_win_boost": -0.05},
    "strong_negative":{"tp_mult": 0.6, "p_win_boost": -0.15},
}

CATALYST_ADJUSTMENTS = {
    # earnings proximity widens SL (volatility expansion) + caps TP confidence
    "imminent":  {"sl_mult": 1.5, "tp_mult": 1.3, "p_win_boost": -0.05},  # ≤3 days
    "near":      {"sl_mult": 1.2, "tp_mult": 1.15,"p_win_boost": +0.02},  # 4-7 days
    "moderate":  {"sl_mult": 1.0, "tp_mult": 1.0, "p_win_boost":  0.0},   # 8-30 days
    "far":       {"sl_mult": 1.0, "tp_mult": 1.0, "p_win_boost":  0.0},   # >30 days
}

# Base prior P(win) before any signals — derived from historical hit rate
# (later: actually compute from picks_log.csv)
DEFAULT_P_WIN_PRIOR = 0.50


# ─── Data classes ──────────────────────────────────────────────────

@dataclass
class SignalState:
    """Snapshot of all conditioning signals for one decision."""
    regime: str = "unknown"           # bull/bear/transition/unknown
    news_score: float = 0.0           # 0-1, from news_classifier
    news_sentiment: str = "neutral"   # bullish/bearish/neutral
    days_to_earnings: Optional[int] = None
    watchlist_boost: float = 0.0      # 0-0.30 from watchlist_score_boost
    vix_level: Optional[float] = None # VIX value if available
    sector_strength: Optional[float] = None  # -1 to +1, sector momentum


@dataclass
class ProbabilisticDecision:
    """Output of the probability engine for one stock decision."""
    ticker: str
    entry_price: float
    
    # Empirical base rates (Layer 1)
    base_sl_pct: Optional[float] = None
    base_tp_pct: Optional[float] = None
    
    # Adjusted by all signals (Layers 2-5)
    final_sl_pct: float = 0.0
    final_tp_pct: float = 0.0
    final_sl_price: float = 0.0
    final_tp_price: float = 0.0
    
    # Buy/sell/trigger zones
    buy_zone_low: float = 0.0
    buy_zone_high: float = 0.0
    trigger_price: float = 0.0
    
    # Probability outputs
    p_win: float = 0.5
    expected_value_pct: float = 0.0
    
    # Audit trail (transparency)
    adjustments_applied: List[str] = field(default_factory=list)
    confidence: str = "low"  # low/medium/high
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ─── Signal classification helpers ─────────────────────────────────

def _classify_news(score: float, sentiment: str) -> str:
    """Convert (score, sentiment) → bucket key for NEWS_ADJUSTMENTS."""
    if score >= 0.9:
        return "huge_positive" if sentiment == "bullish" else "strong_negative"
    elif score >= 0.7:
        return "strong_positive" if sentiment == "bullish" else "strong_negative"
    elif score >= 0.5:
        return "mild_positive" if sentiment == "bullish" else "mild_negative"
    return "neutral"


def _classify_catalyst(days_to_earnings: Optional[int]) -> str:
    """Convert days_to_earnings → bucket key."""
    if days_to_earnings is None:
        return "far"
    if days_to_earnings <= 3:
        return "imminent"
    elif days_to_earnings <= 7:
        return "near"
    elif days_to_earnings <= 30:
        return "moderate"
    return "far"


def _confidence_label(p_win: float, has_stats: bool, n_signals: int) -> str:
    """Heuristic confidence based on signal completeness."""
    if not has_stats:
        return "low"
    if n_signals >= 3 and abs(p_win - 0.5) >= 0.10:
        return "high"
    if n_signals >= 2:
        return "medium"
    return "low"


# ─── MAIN PUBLIC API ───────────────────────────────────────────────

def compute_probabilistic_decision(
    ticker: str,
    entry_price: float,
    signals: Optional[SignalState] = None,
    holding_days: int = 5,
) -> ProbabilisticDecision:
    """
    Main entry point: compute probability-based SL/TP/buy/trigger for a stock.
    
    Combines:
      - Empirical base rates from price history (Layer 1)
      - Regime conditioning (Layer 2)
      - News conditioning (Layer 3)
      - Catalyst conditioning (Layer 4)
      - Multi-signal combiner (Layer 5)
      - Decision output (Layer 6)
    
    Returns ProbabilisticDecision with full audit trail.
    """
    if signals is None:
        signals = SignalState()
    
    decision = ProbabilisticDecision(ticker=ticker, entry_price=entry_price)
    
    # ─── LAYER 1: Empirical base rates ─────────────────────────────
    base_sl = empirical_sl_pct(ticker, target_p_noise=0.30)
    base_tp = empirical_tp_pct(ticker, days=holding_days, target_p_reach=0.50)
    has_stats = base_sl is not None and base_tp is not None
    
    # Fallback if no stats yet for this ticker
    if base_sl is None:
        base_sl = 2.0  # safe default
        decision.adjustments_applied.append("FALLBACK_SL_NO_STATS")
    if base_tp is None:
        base_tp = 1.5  # safe default
        decision.adjustments_applied.append("FALLBACK_TP_NO_STATS")
    
    decision.base_sl_pct = round(base_sl, 4)
    decision.base_tp_pct = round(base_tp, 4)
    
    # Start with base rates
    sl_pct = base_sl
    tp_pct = base_tp
    p_win = DEFAULT_P_WIN_PRIOR
    n_signals = 0
    
    # ─── LAYER 2: Regime conditioning ──────────────────────────────
    regime_key = signals.regime if signals.regime in REGIME_ADJUSTMENTS else "unknown"
    r_adj = REGIME_ADJUSTMENTS[regime_key]
    sl_pct *= r_adj["sl_mult"]
    tp_pct *= r_adj["tp_mult"]
    p_win += r_adj["p_win_boost"]
    if regime_key != "unknown":
        decision.adjustments_applied.append(f"regime={regime_key}")
        n_signals += 1
    
    # ─── LAYER 3: News + sentiment conditioning ────────────────────
    news_bucket = _classify_news(signals.news_score, signals.news_sentiment)
    n_adj = NEWS_ADJUSTMENTS[news_bucket]
    tp_pct *= n_adj["tp_mult"]
    p_win += n_adj["p_win_boost"]
    if news_bucket != "neutral":
        decision.adjustments_applied.append(f"news={news_bucket}({signals.news_score:.2f})")
        n_signals += 1
    
    # ─── LAYER 4: Catalyst (earnings) conditioning ─────────────────
    cat_bucket = _classify_catalyst(signals.days_to_earnings)
    c_adj = CATALYST_ADJUSTMENTS[cat_bucket]
    sl_pct *= c_adj["sl_mult"]
    tp_pct *= c_adj["tp_mult"]
    p_win += c_adj["p_win_boost"]
    if cat_bucket != "far":
        decision.adjustments_applied.append(f"earnings={cat_bucket}({signals.days_to_earnings}d)")
        n_signals += 1
    
    # ─── LAYER 4b: Watchlist boost (already a 0-0.30 score) ────────
    if signals.watchlist_boost > 0.05:
        p_win += signals.watchlist_boost * 0.20  # boost is small contribution
        decision.adjustments_applied.append(f"watchlist=+{signals.watchlist_boost:.2f}")
        n_signals += 1
    
    # ─── LAYER 5: Combine + clip ───────────────────────────────────
    p_win = max(0.05, min(0.95, p_win))  # clip to sane range
    sl_pct = max(0.5, sl_pct)            # never < 0.5%
    tp_pct = max(sl_pct * 1.2, tp_pct)   # ensure R:R >= 1.2
    
    # Expected value: P(win)*TP - P(loss)*SL
    ev_pct = (p_win * tp_pct) - ((1 - p_win) * sl_pct)
    
    # ─── LAYER 6: Convert to actual price levels ───────────────────
    decision.final_sl_pct = round(sl_pct, 4)
    decision.final_tp_pct = round(tp_pct, 4)
    decision.final_sl_price = round(entry_price * (1 - sl_pct / 100), 2)
    decision.final_tp_price = round(entry_price * (1 + tp_pct / 100), 2)
    
    # Buy zone: ±0.5% around entry (room for limit orders)
    decision.buy_zone_low = round(entry_price * 0.995, 2)
    decision.buy_zone_high = round(entry_price * 1.005, 2)
    
    # Trigger price: above entry by 0.3% (momentum confirmation)
    decision.trigger_price = round(entry_price * 1.003, 2)
    
    decision.p_win = round(p_win, 4)
    decision.expected_value_pct = round(ev_pct, 4)
    decision.confidence = _confidence_label(p_win, has_stats, n_signals)
    
    return decision


# ─── Pretty print for Telegram / debugging ─────────────────────────

def format_decision(d: ProbabilisticDecision) -> str:
    """Human-readable summary for Telegram/logs."""
    lines = [
        f"🧠 {d.ticker} @ ${d.entry_price:.2f}  [{d.confidence.upper()} confidence]",
        f"   📊 Base rates:  SL={d.base_sl_pct}%   TP={d.base_tp_pct}%",
        f"   🎯 Final SL:    ${d.final_sl_price}  ({d.final_sl_pct}%)",
        f"   🎯 Final TP:    ${d.final_tp_price}  ({d.final_tp_pct}%)",
        f"   💰 Buy zone:    ${d.buy_zone_low} - ${d.buy_zone_high}",
        f"   🔔 Trigger:     ${d.trigger_price}",
        f"   🎲 P(win):      {d.p_win:.0%}    EV: {d.expected_value_pct:+.2f}%",
    ]
    if d.adjustments_applied:
        lines.append(f"   ⚙️  Signals:    {', '.join(d.adjustments_applied)}")
    return "\n".join(lines)


# ─── CLI for quick testing ─────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    ticker = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    
    # Test 1: No signals (base rates only)
    print("=" * 65)
    print("TEST 1: Base rates only (no signals)")
    print("=" * 65)
    stats = load_stats(ticker)
    if not stats:
        print(f"❌ No stats for {ticker}. Run: python3 src/stock_stats.py {ticker}")
        sys.exit(1)
    price = stats["current_price"]
    d = compute_probabilistic_decision(ticker, price)
    print(format_decision(d))
    
    # Test 2: Bull regime + positive news
    print()
    print("=" * 65)
    print("TEST 2: Bull regime + strong positive news")
    print("=" * 65)
    sig = SignalState(
        regime="bull",
        news_score=0.85,
        news_sentiment="bullish",
        days_to_earnings=14,
    )
    d = compute_probabilistic_decision(ticker, price, signals=sig)
    print(format_decision(d))
    
    # Test 3: Bear regime + earnings imminent
    print()
    print("=" * 65)
    print("TEST 3: Bear regime + earnings in 2 days (high uncertainty)")
    print("=" * 65)
    sig = SignalState(
        regime="bear",
        news_score=0.6,
        news_sentiment="bearish",
        days_to_earnings=2,
    )
    d = compute_probabilistic_decision(ticker, price, signals=sig)
    print(format_decision(d))
    
    # Test 4: Best-case scenario
    print()
    print("=" * 65)
    print("TEST 4: Bull + huge news + watchlist + far earnings (BEST CASE)")
    print("=" * 65)
    sig = SignalState(
        regime="bull",
        news_score=0.95,
        news_sentiment="bullish",
        days_to_earnings=45,
        watchlist_boost=0.25,
    )
    d = compute_probabilistic_decision(ticker, price, signals=sig)
    print(format_decision(d))