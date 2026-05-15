"""
Hard Enforcement Layer (PR #84)
═══════════════════════════════════════════════════════════════
The agent's INSTINCTS are good (premarket check correctly flagged
ARM/AVGO/RMBS as SKIP TODAY on Apr 28). The agent's IMPULSE
CONTROL was missing (it traded them anyway).

This module is the prefrontal cortex: NON-NEGOTIABLE filters
that override the scoring system.

Three new blocks (additive to existing sector/tag caps in scorer.py):
  1. PENNY STOCK BLOCK     — price < $5 (would've stopped SLNH @ $1.66)
  2. SL BUFFER BLOCK       — entry-to-SL < 3% (stop too tight = whipsaw)
  3. WEAK SECTOR BLOCK     — sector ETF down ≥ 2% premarket
                              (would've stopped all 6 Apr 28 semi losses)

Each block is conservative (better skip than lose).
All blocks are logged to data/hard_blocks_log.json for audit.
"""
from typing import List, Dict, Tuple
from pathlib import Path
import json
from datetime import datetime

try:
    import yfinance as yf
    YF_OK = True
except ImportError:
    YF_OK = False

# ─── Tunable thresholds (conservative defaults) ──────────────────
MIN_PRICE = 5.00                  # No penny stocks
# ─── Tiered SL minimums by price (BUG-5 fix, May 2 2026) ─────────
# Liquid mega-caps need tighter stops than volatile small caps.
# Aligns with Probability Engine vision (docs/PROBABILITY_ENGINE_DESIGN.md)
SL_MIN_TIERS = [
    (100.0, 1.5),   # Mega-cap (≥$100): 1.5% min — NVDA, AVGO, MSFT, etc.
    (30.0,  2.0),   # Mid-cap ($30-99):  2.0% min — RMBS, mid-tier
    (10.0,  2.5),   # Small-cap ($10-29): 2.5% min
    (0.0,   3.0),   # Micro-cap (<$10):  3.0% min — needs wider stops
]


def get_min_sl_pct(price: float) -> float:
    """
    Tiered SL minimum based on stock price (proxy for liquidity/volatility).
    Mega-caps trade tighter; small caps need more room.
    """
    try:
        p = float(price)
    except (ValueError, TypeError):
        return 3.0  # safe default
    for threshold, min_pct in SL_MIN_TIERS:
        if p >= threshold:
            return min_pct
    return 3.0



# ─── Ticker cooldown (BUG-4 fix, May 2 2026) ──────────────────────
# Prevent same ticker from being picked repeatedly within N days.
# Aligns with Pillar 4 (Feedback Loop): wait for outcome before re-picking.
COOLDOWN_DAYS = 3  # PR-A2 F2-2: was 5, too restrictive for daily-pick cadence
PICKS_LOG_PATH = Path("data/picks_log.csv")


def _get_recent_pick_dates() -> Dict[str, str]:
    """
    Read picks_log.csv and return {ticker: most_recent_LOSING_pick_date}.

    PR-A2 F2-2b: Only LOSING trades trigger cooldown. Winners and still-open
    positions do NOT cool the ticker — the agent must be free to follow through
    on momentum and to re-evaluate tickers it has not actually lost on.

    Returns empty dict on any failure (fail-safe).
    """
    recent = {}
    if not PICKS_LOG_PATH.exists():
        return recent
    LOSING_STATUSES = {
        "sl_hit", "expired_loss", "max_hold_loss",
        "max_hold_exceeded_force_closed",  # treated as effective loss for safety
    }
    try:
        import csv
        with open(PICKS_LOG_PATH, "r", encoding="utf-8-sig") as f:  # PR-A7 (audit HB-12): handle BOM
            reader = csv.DictReader(f)
            for row in reader:
                ticker = (row.get("ticker") or "").strip().upper()
                pick_date = (row.get("pick_date") or "").strip()
                status = (row.get("evaluation_status") or "").strip().lower()
                # PR-A2 F2-2b: skip non-losses
                if status not in LOSING_STATUSES:
                    continue
                if ticker and pick_date:
                    if ticker not in recent or pick_date > recent[ticker]:
                        recent[ticker] = pick_date
    except Exception:
        pass
    return recent
SECTOR_ETF_DROP_THRESHOLD = -5.0  # PR-A2 F2-3: was -2%, killed mean-reversion plays. Block only on genuine sector crisis.

# Sector → ETF mapping (for premarket sector check)
SECTOR_ETF = {
    "Technology":             "XLK",
    "Communication Services": "XLC",
    "Financial Services":     "XLF",
    "Financials":             "XLF",
    "Energy":                 "XLE",
    "Healthcare":             "XLV",
    "Consumer Cyclical":      "XLY",
    "Consumer Defensive":     "XLP",
    "Industrials":            "XLI",
    "Real Estate":            "XLRE",
    "Utilities":              "XLU",
    "Materials":              "XLB",
}

# PR-A7 (audit HB-29): real per-date cache (docstring previously lied about caching)
_WEAK_SECTORS_CACHE: dict = {}

# Tag-based ETF mapping (catches what yfinance sector misses)
TAG_ETF = {
    "SEMI":  "SOXX",   # semiconductors
    "AI":    "QQQ",    # PR-A7 (audit HB-22): was SOXX which wrongly blocked META/MSFT/GOOGL
    "BIOTECH": "XBI",
    "BANK":  "XLF",
    "OIL":   "XLE",
}


def _safe_pct_change(ticker: str) -> float:
    """Get ticker's last-day % change. Returns 0.0 on any failure (fail-safe)."""
    if not YF_OK:
        return 0.0
    try:
        h = yf.Ticker(ticker).history(period="3d", auto_adjust=False)
        if len(h) >= 2:
            prev = float(h["Close"].iloc[-2])
            curr = float(h["Close"].iloc[-1])
            return (curr - prev) / prev * 100
    except Exception:
        pass
    return 0.0


def get_weak_sectors() -> Dict[str, float]:
    """
    Returns {sector_name_or_tag: pct_change} for any sector/tag ETF
    down ≥ SECTOR_ETF_DROP_THRESHOLD.
    
    Cached to avoid repeated yfinance calls within a single run.
    PR-A7 (audit HB-29): cache is now REAL (per-date in-process).
    """
    from datetime import date as _d
    _key = _d.today().isoformat()
    if _key in _WEAK_SECTORS_CACHE:
        return _WEAK_SECTORS_CACHE[_key]
    weak = {}
    
    # Check sector ETFs
    for sector, etf in SECTOR_ETF.items():
        chg = _safe_pct_change(etf)
        if chg <= SECTOR_ETF_DROP_THRESHOLD:
            weak[sector] = round(chg, 2)
    
    # Check tag ETFs (SEMI, AI, etc.)
    for tag, etf in TAG_ETF.items():
        chg = _safe_pct_change(etf)
        if chg <= SECTOR_ETF_DROP_THRESHOLD:
            weak[tag] = round(chg, 2)
    
    _WEAK_SECTORS_CACHE[_key] = weak  # PR-A7 (audit HB-29)
    return weak


# ─── Individual block checks ─────────────────────────────────────

def _block_penny(pick: dict) -> Tuple[bool, str]:
    """BLOCK 1: No stocks under $5 (penny stock filter)."""
    entry = pick.get("plan", {}).get("entry") or pick.get("entry")
    if entry is None:
        return False, "missing entry price (broken upstream pick)"  # M2: fail-closed
    try:
        if float(entry) < MIN_PRICE:
            return False, f"penny stock (${float(entry):.2f} < ${MIN_PRICE})"
    except (ValueError, TypeError):
        pass
    return True, ""


def _block_sl_buffer(pick: dict) -> Tuple[bool, str]:
    """
    BLOCK 2: Stop-loss must be at least min_sl_pct below entry.
    Tiered by price (BUG-5 fix): mega-caps allowed tighter stops.
    """
    plan = pick.get("plan", {})
    entry = plan.get("entry") or pick.get("entry")
    sl = plan.get("stop_loss") or pick.get("stop_loss")
    if entry and not sl:
        return False, "missing stop_loss (broken upstream pick)"  # M2b: fail-closed
    if not (entry and sl):
        return True, ""
    try:
        entry_f, sl_f = float(entry), float(sl)
        if entry_f <= 0:
            return True, ""
        buffer_pct = (entry_f - sl_f) / entry_f * 100
        min_sl = get_min_sl_pct(entry_f)
        if buffer_pct < min_sl:
            return False, f"SL too tight ({buffer_pct:.1f}% < {min_sl:.1f}% for ${entry_f:.0f} stock)"
    except (ValueError, TypeError, ZeroDivisionError):
        pass
    return True, ""



def _block_recent_pick(pick: dict, recent_dates: Dict[str, str]) -> Tuple[bool, str]:
    """
    BLOCK 5: Skip tickers picked within COOLDOWN_DAYS.
    Prevents picking TSM 4× in 5 days (BUG-4).
    """
    ticker = (pick.get("ticker") or "").strip().upper()
    if not ticker or ticker not in recent_dates:
        return True, ""
    
    last_date_str = recent_dates[ticker]
    try:
        last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        days_since = (today - last_date).days
        if days_since < COOLDOWN_DAYS:
            return False, f"recent pick ({days_since}d ago, cooldown {COOLDOWN_DAYS}d)"
    except (ValueError, TypeError):
        pass
    return True, ""

def _block_weak_sector(pick: dict, weak_sectors: Dict[str, float]) -> Tuple[bool, str]:
    """BLOCK 3: Skip stocks in sectors/tags whose ETF is down ≥2% premarket."""
    if not weak_sectors:
        return True, ""
    
    sector = (pick.get("info_short", {}).get("sector") or "").strip()
    tag_raw = (pick.get("scores", {}).get("sector_tag") or pick.get("tag") or "").strip()
    # M3: iterate all tags so "AI / SEMI" checks BOTH. We do this in caller below.
    primary_tag = tag_raw.split(" / ")[0].strip().upper() if tag_raw else ""
    
    # Match by sector name (case-insensitive)
    for weak_name, chg in weak_sectors.items():
        if not weak_name:
            continue
        if sector.lower() == weak_name.lower():
            return False, f"sector '{weak_name}' down {chg}% premarket"
        # Match by tag (e.g. SEMI tag when SOXX is down)
        if primary_tag and primary_tag == weak_name.upper():
            return False, f"tag '{primary_tag}' ETF down {chg}% premarket"
    
    return True, ""


def _block_catastrophic_news(pick: dict) -> Tuple[bool, str]:
    """BLOCK 4 (PR #77): Hard block on catastrophic news (bankruptcy etc.)."""
    try:
        from src.news_signals import is_hard_blocked
        ticker = pick.get("ticker", "")
        if not ticker:
            return True, ""
        blocked, reason = is_hard_blocked(ticker)
        if blocked:
            return False, f"catastrophic news ({reason})"
    except Exception:
        pass
    return True, ""


# ─── Master function ─────────────────────────────────────────────

def apply_hard_blocks(picks: List[Dict],
                      check_sectors: bool = True) -> Tuple[List[Dict], List[Dict]]:
    """
    Apply all hard blocks to picks list.
    
    Returns:
        (passed_picks, blocked_picks)
        Each blocked entry: {ticker, reason, block_type}
    """
    if not picks:
        return [], []
    
    # Fetch weak sectors ONCE (single network round-trip)
    weak_sectors = get_weak_sectors() if check_sectors else {}
    
    # Fetch recent pick dates ONCE (BUG-4 cooldown check)
    recent_dates = _get_recent_pick_dates()
    
    passed = []
    blocked = []
    
    for pick in picks:
        ticker = pick.get("ticker", "?")
        
        # Run blocks in priority order (cheapest first)
        checks = [
            ("catastrophic_news", _block_catastrophic_news(pick)),  # PR #77
            ("penny_stock",       _block_penny(pick)),
            ("sl_too_tight",      _block_sl_buffer(pick)),
            ("recent_pick",       _block_recent_pick(pick, recent_dates)),  # BUG-4
            ("weak_sector",       _block_weak_sector(pick, weak_sectors)),
        ]
        
        block_reason = None
        block_type = None
        for btype, (ok, reason) in checks:
            if not ok:
                block_reason = reason
                block_type = btype
                break
        
        if block_reason:
            blocked.append({
                "ticker": ticker,
                "reason": block_reason,
                "block_type": block_type,
            })
        else:
            passed.append(pick)
    
    # Audit log: append to data/hard_blocks_log.json (keep last 100 entries)
    if blocked:
        try:
            log_path = Path("data/hard_blocks_log.json")
            log_path.parent.mkdir(exist_ok=True)
            existing = []
            if log_path.exists() and log_path.stat().st_size > 0:
                try:
                    existing = json.loads(log_path.read_text())
                except Exception:
                    existing = []
            existing.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "weak_sectors": weak_sectors,
                "blocked_count": len(blocked),
                "passed_count": len(passed),
                "blocked": blocked,
            })
            log_path.write_text(json.dumps(existing[-1000:], indent=2))  # PR-A7 (audit HB-72): was 100 (~100d), now 1000 (~3yr)
        except Exception as e:
            print(f"[hard_blocks] Could not write audit log: {e}")
    
    return passed, blocked
