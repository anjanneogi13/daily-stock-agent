"""
💎 MONSTER HUNT MODE — Pillar 3 Foundation v0.1

Scores each candidate 0.0-1.0 on "asymmetric upside potential."
High-scoring (>= 0.6) picks get monster treatment:
  - Wider stop (5% vs default ~3%)
  - Aggressive TP (25%+ vs default 5-8%)
  - SMALLER position (1-2% vs default 3-5%) — lottery sizing

Boost factors (sum to max 1.0, capped):
    +0.20  earnings within 7 days       (catalyst proximity)
    +0.20  short_pct_of_float > 15%     (squeeze potential)
    +0.15  float_shares < 50M           (low float = explosive)
    +0.15  RVOL > 1.5x                  (institutional interest)
    +0.15  bullish news on watchlist    (narrative tailwind)
    +0.10  composite >= 0.85            (top-decile quality)
    +0.05  catalyst combo (earnings<=14d AND RVOL>1.2)

Threshold: 0.60 (configurable in config.yaml monster.threshold)

Designed to be ADDITIVE — never blocks normal picks, only ADDS info.
"""
from typing import Dict, Optional


def score_monster(
    composite: float,
    days_to_earnings: Optional[int],
    short_pct_of_float: Optional[float],
    float_shares: Optional[float],
    vol_ratio: Optional[float],
    has_bullish_news: bool = False,
) -> Dict:
    """
    Compute monster_score in [0.0, 1.0] from raw signals.

    Returns dict with score, components, reasons, is_monster bool.
    All inputs may be None — missing data contributes 0 (no penalty).
    """
    components = {}
    reasons = []

    # 1. Earnings catalyst proximity
    if days_to_earnings is not None and 0 <= days_to_earnings <= 7:
        components["earnings_proximity"] = 0.20
        reasons.append(f"earnings in {days_to_earnings}d")
    else:
        components["earnings_proximity"] = 0.0

    # 2. Short squeeze potential
    if short_pct_of_float is not None and short_pct_of_float > 0.15:
        components["short_squeeze"] = 0.20
        reasons.append(f"short {short_pct_of_float*100:.0f}%")
    else:
        components["short_squeeze"] = 0.0

    # 3. Low float (explosive moves)
    if float_shares is not None and 0 < float_shares < 50_000_000:
        components["low_float"] = 0.15
        reasons.append(f"float {float_shares/1e6:.0f}M")
    else:
        components["low_float"] = 0.0

    # 4. Elevated relative volume
    if vol_ratio is not None and vol_ratio > 1.5:
        components["rvol_elevated"] = 0.15
        reasons.append(f"RVOL {vol_ratio:.1f}x")
    else:
        components["rvol_elevated"] = 0.0

    # 5. Bullish news catalyst
    if has_bullish_news:
        components["bullish_news"] = 0.15
        reasons.append("bullish news")
    else:
        components["bullish_news"] = 0.0

    # 6. Top-decile composite (quality gate)
    if composite is not None and composite >= 0.85:
        components["top_decile"] = 0.10
        reasons.append(f"score {composite:.2f}")
    else:
        components["top_decile"] = 0.0

    # 7. Catalyst combo bonus (earnings near + volume spike = setup confirmed)
    if (days_to_earnings is not None and 0 <= days_to_earnings <= 14
            and vol_ratio is not None and vol_ratio > 1.2):
        components["catalyst_combo"] = 0.05
        reasons.append("catalyst+vol combo")
    else:
        components["catalyst_combo"] = 0.0

    score = round(min(1.0, sum(components.values())), 3)

    return {
        "monster_score": score,
        "monster_components": components,
        "monster_reasons": reasons,
        "is_monster": score >= 0.60,
    }


def apply_monster_treatment(
    pick: Dict,
    monster_score: float,
    account_size: float = 10000.0,
    monster_position_pct: float = 1.5,
) -> Dict:
    """
    If pick is a monster (score >= 0.6), override SL/TP/qty for asymmetric setup.

    Returns the SAME pick dict with monster_* fields added and (if monster)
    SL widened to 5%, TP widened to +25%, qty reduced to lottery sizing.
    """
    pick["monster_score"] = monster_score
    pick["is_monster"] = monster_score >= 0.60

    if not pick["is_monster"]:
        return pick

    # Override SL/TP for monster setup
    entry = float(pick.get("entry") or 0)
    if entry <= 0:
        return pick

    monster_sl = round(entry * 0.95, 2)   # 5% wider stop
    monster_tp = round(entry * 1.25, 2)   # 25% target
    monster_risk_dollars = account_size * (monster_position_pct / 100.0)
    monster_qty = max(1, int(monster_risk_dollars / max(entry - monster_sl, 0.01)))

    pick["original_sl_pre_monster"] = pick.get("stop_loss")
    pick["original_tp_pre_monster"] = pick.get("take_profit")
    pick["original_qty_pre_monster"] = pick.get("qty")

    pick["stop_loss"] = monster_sl
    pick["take_profit"] = monster_tp
    pick["qty"] = monster_qty
    pick["risk_reward"] = round((monster_tp - entry) / max(entry - monster_sl, 0.01), 2)

    return pick
