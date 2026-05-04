"""T52 — The Layman Translator.

Single module converting technical agent output → plain English a
14-year-old can understand. Used by all 5 layman_* Telegram scripts.

DESIGN PRINCIPLES:
  1. No jargon. Replace every technical term with everyday English.
  2. Short sentences. Friend-explaining-over-coffee voice.
  3. Always answer 'why does this matter?'
  4. Honest. Never sugarcoat losses, never overhype wins.
  5. Keep ALL actionable trading data (entry/SL/TP/qty/hold time).

Technical channel (signal_journal/learning_journal/exec_report) stays
UNCHANGED — that feeds the AI agent's own learning. This module feeds
humans only.
"""
from __future__ import annotations
from typing import Dict, List, Optional


# ═══════════════════════════════════════════════════════════════
# Score → human label
# ═══════════════════════════════════════════════════════════════
def score_to_words(score: Optional[float]) -> str:
    """0.95 → 'excellent', 0.65 → 'decent', 0.40 → 'meh'."""
    if score is None: return "unknown"
    s = float(score)
    if s >= 0.85: return "excellent"
    if s >= 0.70: return "strong"
    if s >= 0.55: return "decent"
    if s >= 0.40: return "okay"
    return "weak"


def confidence_label(score: Optional[float]) -> str:
    if score is None: return "uncertain"
    s = float(score)
    if s >= 0.80: return "very confident"
    if s >= 0.65: return "fairly confident"
    if s >= 0.50: return "moderately confident"
    return "cautious"


def risk_label(risk_pct: float) -> str:
    """1.5% → 'low risk', 4.5% → 'high risk'."""
    if risk_pct < 1.0:  return "very low risk"
    if risk_pct < 2.0:  return "low risk"
    if risk_pct < 3.5:  return "moderate risk"
    if risk_pct < 5.0:  return "higher risk"
    return "high risk"


# ═══════════════════════════════════════════════════════════════
# Money / percent / R-multiple → human
# ═══════════════════════════════════════════════════════════════
def money(amt) -> str:
    """+$45.20 / -$12.00 / $0"""
    try: a = float(amt)
    except (TypeError, ValueError): return "$0"
    if a > 0:  return f"+${a:.2f}"
    if a < 0:  return f"-${abs(a):.2f}"
    return "$0"


def pct(p) -> str:
    try: pp = float(p)
    except (TypeError, ValueError): return "0%"
    if pp > 0:  return f"+{pp:.1f}%"
    if pp < 0:  return f"-{abs(pp):.1f}%"
    return "0%"


def r_multiple_words(r) -> str:
    try: rr = float(r)
    except (TypeError, ValueError): return "no result yet"
    if rr >  1.5: return f"big win ({rr:+.1f}x risk earned)"
    if rr >  0.5: return f"solid win ({rr:+.1f}x risk)"
    if rr >  0:   return f"small win ({rr:+.1f}x risk)"
    if rr > -0.5: return f"small loss ({rr:+.1f}x risk)"
    if rr > -1.0: return f"loss ({rr:+.1f}x risk)"
    return f"full stop-loss hit ({rr:+.1f}x risk)"


# ═══════════════════════════════════════════════════════════════
# Pick → friend-explains description (KEEPS all actionable data)
# ═══════════════════════════════════════════════════════════════
def pick_to_layman(pick: Dict, idx: int = 1) -> str:
    """Translate one pick row to plain English. Includes:
       BUY PRICE, STOP-LOSS, TARGET PRICE, QUANTITY, HOLDING TIME, RISK LEVEL.
    """
    def _f(key, default=0.0):
        try: return float(pick.get(key, default) or default)
        except (TypeError, ValueError): return default

    t = pick.get("ticker", "?")
    score = _f("composite_score") or _f("score")
    entry = _f("entry") or _f("buy_price")
    sl    = _f("sl")    or _f("stop_loss")
    tp    = _f("tp")    or _f("target_price") or _f("take_profit")
    qty   = int(_f("qty") or _f("position_size"))
    ttype = (pick.get("trade_type", "") or "swing").lower()

    risk_pct   = ((entry - sl) / entry * 100) if entry and sl else 0
    reward_pct = ((tp - entry) / entry * 100) if entry and tp else 0
    rr = (reward_pct / risk_pct) if risk_pct > 0 else 0

    quality = score_to_words(score)
    risk_lvl = risk_label(risk_pct) if risk_pct else "unknown risk"

    if ttype == "day":
        hold = "📆 *Hold for:* TODAY ONLY — sell before market closes (~4 hours max)"
    else:
        hold = "📆 *Hold for:* a few days to a few weeks (sell when target or stop hits)"

    cost = entry * qty if entry and qty else 0
    max_loss = abs(entry - sl) * qty if entry and sl and qty else 0
    max_gain = abs(tp - entry) * qty if entry and tp and qty else 0

    lines = [
        f"*{idx}. {t}* — looks {quality} 🎯",
        f"💵 *Buy at:* ~${entry:.2f}  ·  *Quantity:* {qty} shares  (cost ~${cost:,.0f})",
        f"🛑 *Stop-loss (auto-exit):* ${sl:.2f}  ({pct(-risk_pct)}, you'd lose ~{money(-max_loss)})",
        f"🎯 *Target price (take profit):* ${tp:.2f}  ({pct(reward_pct)}, you'd gain ~{money(max_gain)})",
        hold,
        f"⚖️ *Risk level:* {risk_lvl}  ·  *Reward vs Risk:* {rr:.1f}x",
    ]
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# Outcome → friend-explains line
# ═══════════════════════════════════════════════════════════════
def outcome_to_layman(outcome: Dict) -> str:
    t = outcome.get("ticker", "?")
    status = (outcome.get("status", "") or "").upper()
    try: pnl = float(outcome.get("pnl_dollar") or outcome.get("pnl") or 0)
    except (TypeError, ValueError): pnl = 0
    try: r = float(outcome.get("r_multiple")) if outcome.get("r_multiple") not in (None, "") else None
    except (TypeError, ValueError): r = None

    if status in ("TP_HIT", "WIN"):
        return f"✅ *{t}* — hit profit target ({money(pnl)})"
    if status in ("SL_HIT", "LOSS"):
        return f"❌ *{t}* — hit stop-loss ({money(pnl)})"
    if status == "EOD_CLOSE":
        e = "✅" if pnl > 0 else "⚠️"
        return f"{e} *{t}* — closed at end of day ({money(pnl)})"
    if status == "OPEN":
        return f"⏳ *{t}* — still holding"
    return f"❔ *{t}* — {status.lower() or 'unclear'} ({money(pnl)})"


# ═══════════════════════════════════════════════════════════════
# Verdict — overall day/week/month performance
# ═══════════════════════════════════════════════════════════════
def verdict_line(wins: int, losses: int, total_pnl: float = 0) -> str:
    n = wins + losses
    if n == 0: return "📭 No closed trades yet"
    wr = wins / n
    if wr >= 0.70 and total_pnl > 0: return "🎯 GREAT — agent crushed it today"
    if wr >= 0.55 and total_pnl > 0: return "✅ SOLID — more wins than losses"
    if wr >= 0.45 and total_pnl > 0: return "🟢 OK — slight edge"
    if total_pnl > 0:                return "🟢 NET POSITIVE — winners covered losers"
    if wr >= 0.45:                   return "🟡 MIXED — even win rate but small loss"
    return "🔴 TOUGH — agent took a hit today"


def beat_market_line(agent_pct: Optional[float], spy_pct: Optional[float]) -> str:
    if agent_pct is None or spy_pct is None:
        return ""
    diff = agent_pct - spy_pct
    if abs(diff) < 0.1:
        return f"📊 Agent {pct(agent_pct)} vs market {pct(spy_pct)} — about even"
    if diff > 0:
        return f"📊 Agent {pct(agent_pct)} vs market {pct(spy_pct)} — *beat the market by {abs(diff):.1f}%* 🎉"
    return f"📊 Agent {pct(agent_pct)} vs market {pct(spy_pct)} — *trailed market by {abs(diff):.1f}%*"


# ═══════════════════════════════════════════════════════════════
# Section dividers / headers
# ═══════════════════════════════════════════════════════════════
def header(emoji: str, title: str, subtitle: str = "") -> str:
    out = [f"{emoji} *{title}*"]
    if subtitle: out.append(f"_{subtitle}_")
    out.append("")
    return "\n".join(out)


def footer_explainer() -> str:
    return ("\n────────\n"
            "_💡 The agent learns from every trade. "
            "Stop-loss = automatic safety exit. "
            "Target = where it locks in profit._")
