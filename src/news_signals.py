"""
News Signals (PR #77)
═══════════════════════════════════════════════════════════════
Converts news classifications into actionable score adjustments
that main.py applies during pick scoring.

PROBLEM SOLVED:
  Before: News engine spammed Telegram with 80+ alerts/day, but
          NONE influenced the actual picks. Pure noise.
  After:  Each classified news item creates a SCORE BOOST/PENALTY
          for the affected ticker, with a TTL (time-to-live).
          main.py reads these signals during composite scoring.

DATA FLOW:
  news_engine → news_classifier → news_signals.json → main.py scoring
                                                    → hard_blocks (if catastrophic)

CATALYST → SCORE MAPPING (conservative, tunable):
  
  BULLISH (boost ticker):
    fda_approval      → +0.15 (30 days)
    earnings_beat     → +0.10 (7 days)
    guidance_raise    → +0.10 (14 days)
    ma_target         → +0.20 (30 days, premium catalyst)
    ma_acquirer       → +0.05 (14 days)
    upgrade           → +0.05 (5 days)
    product_launch    → +0.05 (7 days)
  
  BEARISH (penalize ticker):
    earnings_miss     → -0.10 (7 days)
    guidance_cut      → -0.15 (14 days)
    downgrade         → -0.05 (5 days)
    fda_rejection     → -0.20 (30 days)
    lawsuit           → -0.10 (14 days)
  
  CATASTROPHIC (hard block — PR #84 integration):
    BANKRUPTCY_RISK   → -1.00 (forever, manual clear)
      (detected from headline keywords: bankruptcy, going concern,
       cease operations, wind down, delisting)
"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

SIGNALS_PATH = Path("data/news_signals.json")
NEWS_LOG_PATH = Path("data/news_log.jsonl")
WATCHLIST_PATH = Path("data/watchlist.json")

# ─── Catalyst → (score_delta, ttl_days) ──────────────────────────
CATALYST_RULES = {
    # BULLISH
    "fda_approval":   ( +0.15, 30),
    "earnings_beat":  ( +0.10,  7),
    "guidance_raise": ( +0.10, 14),
    "ma_target":      ( +0.20, 30),  # acquired-target premium
    "ma_acquirer":    ( +0.05, 14),
    "upgrade":        ( +0.05,  5),
    "product_launch": ( +0.05,  7),
    
    # BEARISH
    "earnings_miss":  ( -0.10,  7),
    "guidance_cut":   ( -0.15, 14),
    "downgrade":      ( -0.05,  5),
    "fda_rejection":  ( -0.20, 30),
    "lawsuit":        ( -0.10, 14),
}

# Catastrophic keywords → hard block flag
CATASTROPHIC_KEYWORDS = [
    "bankruptcy", "chapter 11", "chapter 7",
    "going concern", "going-concern",
    "cease operations", "wind down", "winding down",
    "delisting", "delisted", "nasdaq letter",  # warning shots
    "asset disposal", "liquidation", "liquidating",
    "wipeout", "worthless",
]

# Positive headline + negative price reaction is not the same as a clean
# bullish catalyst. This catches EVC-style cases where "good" news is sold.
NEGATIVE_REACTION_PHRASES = [
    "shares fall",
    "shares fell",
    "shares drop",
    "shares dropped",
    "stock falls",
    "stock fell",
    "stock drops",
    "stock dropped",
    "falls after",
    "fell after",
    "drops after",
    "dropped after",
    "down after",
    "lower after",
    "slumps after",
    "slumped after",
    "tumbles after",
    "tumbled after",
    "falls despite",
    "fell despite",
    "drops despite",
    "dropped despite",
    "down despite",
    "lower despite",
    "slumps despite",
    "tumbles despite",
    "selloff after",
    "sell-off after",
    "sold off after",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_catastrophic(headline: str, summary: str = "") -> bool:
    """Detect bankruptcy/wind-down language in news text."""
    text = (headline + " " + summary).lower()
    return any(kw in text for kw in CATASTROPHIC_KEYWORDS)


def _has_negative_reaction(headline: str, summary: str = "") -> bool:
    """Return True when headline/summary says the stock sold off despite news."""
    text = " ".join(
        " ".join(str(x or "").lower().replace("—", " ").replace("–", " ").split())
        for x in [headline, summary]
    )
    return any(phrase in text for phrase in NEGATIVE_REACTION_PHRASES)


def _apply_negative_reaction_penalty(delta: float) -> tuple[float, bool]:
    """Fade bullish boosts when the market reaction is explicitly negative.

    A positive catalyst that is sold should not receive a normal boost.
    Convert it into a small penalty so the scorer treats it as evidence of
    distribution/expectations risk rather than a clean catalyst.
    """
    if delta <= 0:
        return delta, False
    return -min(0.03, max(0.01, abs(delta) * 0.30)), True


def _load_signals() -> Dict:
    """Load existing signals or return empty dict."""
    if not SIGNALS_PATH.exists():
        return {}
    try:
        return json.loads(SIGNALS_PATH.read_text())
    except Exception:
        return {}


def _save_signals(signals: Dict) -> None:
    """Atomic write to avoid corruption."""
    SIGNALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = SIGNALS_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(signals, indent=2))
    tmp.replace(SIGNALS_PATH)


def _purge_expired(signals: Dict) -> Dict:
    """Remove signals past their expiry date."""
    now = datetime.now(timezone.utc)
    fresh = {}
    for ticker, sig in signals.items():
        try:
            expires = datetime.fromisoformat(sig["expires"].replace("Z", "+00:00"))
            if expires >= now:
                fresh[ticker] = sig
        except (KeyError, ValueError, TypeError):
            continue
    return fresh


# ─── Public API: add signal from news classification ─────────────

def add_signal_from_classification(item: Dict) -> Optional[Dict]:
    """
    Process a classified news item and update news_signals.json
    if it produces an actionable score adjustment.
    
    Returns the new signal dict (or None if no signal generated).
    """
    cls = item.get("classification", {})
    ticker = cls.get("primary_ticker")
    if not ticker:
        return None
    
    headline = item.get("headline", "")
    summary = item.get("summary", "")
    category = cls.get("category", "other")
    sentiment = cls.get("sentiment", "neutral")
    score_pct = cls.get("tradeable_score", 0)
    
    # Catastrophic check FIRST (overrides everything)
    if _is_catastrophic(headline, summary):
        signal = {
            "ticker": ticker,
            "score_delta": -1.0,
            "catalyst": "BANKRUPTCY_RISK",
            "headline": headline[:200],
            "added_at": _now_iso(),
            "expires": (datetime.now(timezone.utc) + timedelta(days=180)).isoformat(),
            "hard_block": True,
        }
    elif category in CATALYST_RULES:
        delta, ttl = CATALYST_RULES[category]
        # Modulate by tradeable_score (low confidence = smaller delta)
        # tradeable_score 0.7 → 100% delta, 0.5 → 71% delta, 0.3 → 43% delta
        confidence = min(1.0, max(0.3, score_pct / 0.7))
        adjusted_delta = round(delta * confidence, 3)
        negative_reaction = _has_negative_reaction(headline, summary)
        if negative_reaction:
            adjusted_delta, _ = _apply_negative_reaction_penalty(adjusted_delta)
            adjusted_delta = round(adjusted_delta, 3)
        
        signal = {
            "ticker": ticker,
            "score_delta": adjusted_delta,
            "catalyst": category,
            "sentiment": sentiment,
            "tradeable_score": score_pct,
            "action_window": cls.get("action_window"),
            "headline": headline[:200],
            "added_at": _now_iso(),
            "expires": (datetime.now(timezone.utc) + timedelta(days=ttl)).isoformat(),
            "hard_block": False,
            "negative_reaction": negative_reaction,
        }
    else:
        return None  # category not in our rule set (e.g. "other", "rumor")
    
    # Merge into signals (last write wins; can be improved with stacking later)
    signals = _load_signals()
    signals = _purge_expired(signals)
    
    # If existing signal for ticker, only OVERWRITE if new signal is stronger
    existing = signals.get(ticker)
    if existing:
        # Hard block always wins
        if signal["hard_block"]:
            signals[ticker] = signal
        # Otherwise: keep the larger absolute delta
        elif abs(signal["score_delta"]) > abs(existing.get("score_delta", 0)):
            signals[ticker] = signal
        # Else: keep existing
    else:
        signals[ticker] = signal
    
    _save_signals(signals)
    return signal


# ─── Public API: read signals during scoring ─────────────────────

def get_ticker_signal(ticker: str) -> dict:
    """Return the active, unexpired news signal for a ticker, or {}."""
    signals = _load_signals()
    sig = signals.get(ticker)
    if not sig:
        return {}

    try:
        expires = datetime.fromisoformat(sig["expires"].replace("Z", "+00:00"))
        if expires < datetime.now(timezone.utc):
            return {}
    except (KeyError, ValueError, TypeError):
        return {}

    return sig


def get_ticker_boost(ticker: str) -> float:
    """
    Returns score adjustment for ticker (-1.0 to +0.20).
    Returns 0.0 if no active signal.
    
    Called by main.py during composite scoring:
        boost = get_ticker_boost(p['ticker'])
        p['scores']['composite'] = max(0, min(1, composite + boost))
    """
    signals = _load_signals()
    sig = signals.get(ticker)
    if not sig:
        return 0.0
    
    # Auto-purge if expired
    try:
        expires = datetime.fromisoformat(sig["expires"].replace("Z", "+00:00"))
        if expires < datetime.now(timezone.utc):
            return 0.0
    except (KeyError, ValueError, TypeError):
        return 0.0
    
    return float(sig.get("score_delta", 0.0))


def is_hard_blocked(ticker: str) -> tuple[bool, str]:
    """
    Returns (True, reason) if ticker has a catastrophic news signal.
    Used by hard_blocks.py BLOCK 4.
    """
    signals = _load_signals()
    sig = signals.get(ticker)
    if not sig:
        return False, ""
    if not sig.get("hard_block"):
        return False, ""
    
    catalyst = sig.get("catalyst", "unknown")
    headline = sig.get("headline", "")[:100]
    return True, f"{catalyst}: {headline}"


def rebuild_from_news_log(days_back: int = 30) -> Dict:
    """
    One-time: scan news_log.jsonl and rebuild news_signals.json from scratch.
    Useful for initial seeding from existing news history.
    """
    if not NEWS_LOG_PATH.exists():
        print("[news_signals] No news_log.jsonl yet — nothing to rebuild")
        return {}
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    processed = 0
    signals_added = 0
    
    with NEWS_LOG_PATH.open() as f:
        for line in f:
            try:
                item = json.loads(line)
            except Exception:
                continue
            
            # Check if item is recent enough
            published = item.get("published_at", "")
            if published:
                try:
                    pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    if pub_dt < cutoff:
                        continue
                except Exception:
                    pass
            
            processed += 1
            sig = add_signal_from_classification(item)
            if sig:
                signals_added += 1
    
    final = _load_signals()
    print(f"[news_signals] Rebuild: processed {processed} items, "
          f"created {signals_added} signals, "
          f"final state has {len(final)} active tickers")
    return final


def stats() -> dict:
    """Return current signals state for diagnostics."""
    signals = _load_signals()
    fresh = _purge_expired(signals)
    bullish = [t for t, s in fresh.items() if s.get("score_delta", 0) > 0]
    bearish = [t for t, s in fresh.items() if s.get("score_delta", 0) < 0 and not s.get("hard_block")]  # M7: catches deltas <-0.5 too
    blocks  = [t for t, s in fresh.items() if s.get("hard_block")]
    return {
        "total_active": len(fresh),
        "bullish_count": len(bullish),
        "bearish_count": len(bearish),
        "hard_blocks": blocks,  # show full list (usually short)
        "top_bullish": sorted(bullish, key=lambda t: -fresh[t]["score_delta"])[:5],
        "top_bearish": sorted(bearish, key=lambda t: fresh[t]["score_delta"])[:5],
    }


if __name__ == "__main__":
    # CLI usage:
    #   python -m src.news_signals rebuild   → rebuild from news_log.jsonl
    #   python -m src.news_signals stats     → show current state
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "rebuild":
        rebuild_from_news_log(days_back=14)
    print(json.dumps(stats(), indent=2, default=str))
