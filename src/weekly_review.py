"""
Weekly Self-Assessment — Pillar 5 v0.1

Every Sunday the agent grades itself on the past 7 days:
  - Performance metrics
  - What worked / What failed (auto-detected patterns)
  - Wisdom base changes
  - Recommended next-week action

Output: one Telegram message + one markdown snapshot in reports/weekly/.
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from .quarterly_report import _load_picks_in_range, _summary_metrics, _to_float
from .wisdom_base import stats as wisdom_stats, load_active_patterns
from .strategy_breakdown import breakdown_by
from .sector_breakdown import sector_breakdown, format_sector_panel


REPORTS = Path("reports/weekly")
REPORTS.mkdir(parents=True, exist_ok=True)


def grade(metrics: Dict) -> str:
    """Honest letter grade based on R + alpha."""
    if metrics["closed_picks"] == 0:
        return "⚪ N/A (no closed picks)"
    total_r = metrics.get("total_r") or 0
    alpha   = metrics.get("avg_alpha_spy") or 0
    if total_r > 3 and alpha > 1:    return "🟢 A (strong)"
    if total_r > 1 and alpha > 0:    return "🟢 B (solid)"
    if total_r > 0:                  return "🟡 C+ (positive)"
    if total_r > -2:                 return "🟡 C- (mixed)"
    if total_r > -5:                 return "🟠 D (poor)"
    return "🔴 F (crisis — pause review needed)"


def what_worked(picks: List[Dict]) -> List[str]:
    notes = []
    closed = [p for p in picks if p.get("evaluation_status") in {"tp_hit", "sl_hit", "day_close"}]
    if not closed:
        return ["(no closed picks this week)"]

    # Trade-type breakdown
    bd_tt = breakdown_by("trade_type", closed)
    for row in bd_tt:
        if row["n"] >= 2 and (row.get("avg_r") or 0) > 0.5:
            notes.append(f"{row['group'].upper()} trades won "
                         f"{row['wins']}/{row['n']} (avg R {row['avg_r']:+.2f})")

    # Tag winners
    bd_tag = breakdown_by("tag", closed)
    for row in bd_tag:
        if row["n"] >= 2 and (row.get("avg_r") or 0) > 0.5:
            notes.append(f"{row['group']} tag profitable "
                         f"({row['wins']}/{row['n']}, R {row['total_r']:+.1f})")

    return notes or ["(no clearly winning categories yet)"]



def rules_violated_on_losers(picks):
    """B6: For each loser, list high-conf book/lesson rules whose
    triggers fire — i.e., rules we 'violated' by taking the trade.

    Returns list of strings, max 5 entries.
    """
    try:
        from src.wisdom_base import lessons_for_context
    except Exception:
        return []
    out = []
    for p in picks or []:
        try:
            r = float(p.get("r_multiple") or 0)
        except (TypeError, ValueError):
            continue
        if r >= 0:
            continue  # only losers
        ctx = {
            "drawdown_pct":  abs(float(p.get("actual_return_pct") or 0)),
            "regime":        str(p.get("regime") or "").lower(),
            "trade_type":    str(p.get("trade_type") or "").lower(),
            "tag":           str(p.get("tag") or "").lower(),
            "r_multiple":    r,
            "days_held":     p.get("days_held"),
        }
        try:
            ls = lessons_for_context(ctx, min_confidence=0.85)
        except Exception:
            ls = []
        if not ls:
            continue
        best = max(ls, key=lambda L: L.get("confidence", 0))
        text = (best.get("text") or "")[:80]
        out.append(f"• {p.get('ticker','?')}: violated _{text}_")
        if len(out) >= 5:
            break
    return out

def what_failed(picks: List[Dict]) -> List[str]:
    notes = []
    closed = [p for p in picks if p.get("evaluation_status") in {"tp_hit", "sl_hit", "day_close"}]
    if not closed:
        return []

    bd_tt = breakdown_by("trade_type", closed)
    for row in bd_tt:
        if row["n"] >= 2 and (row.get("avg_r") or 0) < -0.3:
            notes.append(f"{row['group'].upper()} trades lost "
                         f"{row['losses']}/{row['n']} — review SL/entry")

    bd_tag = breakdown_by("tag", closed)
    for row in bd_tag:
        if row["n"] >= 2 and (row.get("avg_r") or 0) < -0.3:
            notes.append(f"{row['group']} tag losing "
                         f"({row['losses']}/{row['n']}, R {row['total_r']:+.1f})")

    return notes


def recommended_actions(metrics: Dict, failed: List[str], grade_str: str) -> List[str]:
    actions = []
    if "F " in grade_str or "F (" in grade_str:
        actions.append("⚠️ FAILING WEEK — review entries, consider 50% size cut")

    if (metrics.get("avg_alpha_sec") or 0) < -2:
        actions.append("Sector α negative — picks are losing to sector ETFs")

    if (metrics.get("win_rate") or 0) < 0.3 and metrics["closed_picks"] >= 4:
        actions.append("Win rate <30% — tighten composite_score threshold")

    if any("SWING" in f for f in failed):
        actions.append("Reduce SWING allocation 50% next week")
    if any("DAY" in f for f in failed):
        actions.append("Reduce DAY allocation 50% next week")

    if not actions:
        actions.append("Continue current strategy — nothing flagged")

    actions.append("Run `python scripts/run_hypothesis_review.py` for L4 findings")
    return actions


def build_report(end_date: datetime = None) -> Dict:
    end = end_date or datetime.now()
    start = end - timedelta(days=7)
    picks = _load_picks_in_range(start, end)
    metrics = _summary_metrics(picks)
    g = grade(metrics)
    won = what_worked(picks)
    lost = what_failed(picks)
    actions = recommended_actions(metrics, lost, g)
    wstats = wisdom_stats()
    sectors = sector_breakdown(picks)

    return {
        "start_date": start.strftime("%b %d"),
        "end_date":   end.strftime("%b %d"),
        "grade":      g,
        "metrics":    metrics,
        "worked":     won,
        "failed":     lost,
        "wisdom":     wstats,
        "sectors":    sectors,
        "actions":    actions,
    }


def format_telegram(r: Dict) -> str:
    m = r["metrics"]
    lines = []
    lines.append(f"🪞 *Weekly Self-Assessment — {r['start_date']} → {r['end_date']}*")
    lines.append("")
    lines.append(f"*GRADE:* {r['grade']}")
    lines.append("")
    lines.append("📊 *7d Performance*")
    if m["closed_picks"]:
        lines.append(f"• {m['total_picks']} picks · {m['closed_picks']} closed · "
                     f"WR {m['win_rate']:.0%}")
        if m['total_r'] is not None:
            lines.append(f"• Total R: {m['total_r']:+.2f} · "
                         f"avg ret {m['avg_return_pct']:+.2f}%")
        if m['avg_alpha_spy'] is not None:
            lines.append(f"• α vs SPY: {m['avg_alpha_spy']:+.2f}%")
        if m['avg_alpha_sec'] is not None:
            lines.append(f"• α vs Sector: {m['avg_alpha_sec']:+.2f}%")
    else:
        lines.append("• No closed picks this week")

    lines.append("")
    lines.append("🩺 *Weekly Post-Mortem*")
    lines.append("_(per-pick attribution — what the brain got right vs wrong this week)_")
    lines.append("")
    lines.append("✅ *What worked*")
    for w in r["worked"]:
        lines.append(f"• {w}")

    if r["failed"]:
        lines.append("")
        lines.append("❌ *What failed*")
        for f in r["failed"]:
            lines.append(f"• {f}")

    if r.get("sectors"):
        lines.append("")
        lines.append(format_sector_panel(r["sectors"]))

    lines.append("")
    lines.append("🧠 *Wisdom base*")
    lines.append(f"• {r['wisdom']['active_lessons']} lessons · "
                 f"{r['wisdom']['active_patterns']} patterns · "
                 f"{r['wisdom']['kill_list_size']} on kill list")


    # T40: Calibration brain footer (safe — degrades to nothing on error)
    try:
        from src.calibration import telegram_footer_lines, open_proposals_summary
        cal_lines = telegram_footer_lines()
        prop_line = open_proposals_summary()
        if cal_lines or prop_line:
            lines.append("")
            lines.append("📐 *Calibration brain*")
            lines.extend(cal_lines)
            if prop_line:
                lines.append(prop_line)
    except Exception:
        pass


    # Pillar 1 status footer (Layer 4 hypothesis + Layer 5 self-awareness)
    try:
        from src import auto_pause as ap
        from src import pause_state as ps
        from src.signal_journal import load_closed as _journal_closed

        p1_lines = []

        # Layer 5: pause-status snapshot
        try:
            score = ap.compute_score()
            paused = ps.is_paused()
            label = ap.classify(score["score"])
            p1_lines.append(f"• 🛡 Self-awareness: {label} "
                            f"(score {score['score']}/10, "
                            f"{'PAUSED' if paused.get('paused') else 'active'})")
        except Exception:
            pass

        # Layer 4: hypothesis-journal coverage
        try:
            closed = _journal_closed()
            if closed:
                wins = sum(1 for c in closed if c.get("outcome") == "win")
                p1_lines.append(f"• 🧪 Hypothesis journal: {len(closed)} closed picks "
                                f"({wins} wins, base WR {wins/len(closed):.0%})")
        except Exception:
            pass

        if p1_lines:
            lines.append("")
            lines.append("🧠 *Probability engine (Pillar 1)*")
            lines.extend(p1_lines)
    except Exception:
        pass


    # Pillar 4 — learning-journal & weight-history footer
    try:
        from src import learning_journal as _lj
        from src import weight_applier as _wa
        lj = _lj.summary(days=7)
        wh = _wa.history_summary(days=7)
        if lj["total"] or wh["total"]:
            lines.append("")
            lines.append("🧠 *Brain learned this week (Pillar 4)*")
            if lj["total"]:
                bk = lj["by_kind"]
                bits = []
                if bk.get("lesson_added"):     bits.append(f"+{bk['lesson_added']} lessons")
                if bk.get("pattern_promoted"): bits.append(f"+{bk['pattern_promoted']} patterns")
                if bk.get("kill_listed"):      bits.append(f"+{bk['kill_listed']} kill-listed")
                if bk.get("lesson_deactivated"): bits.append(f"-{bk['lesson_deactivated']} stale")
                if bits:
                    lines.append("• 📚 " + " · ".join(bits))
            if wh["total"]:
                ba = wh["by_action"]
                lines.append(f"• ⚖ Weights moved: {wh['total']} "
                             f"({ba['boost']} boost · {ba['penalize']} penalize · "
                             f"{ba['kill']} kill)")
    except Exception:
        pass


    # Pillar 5 — rolling 30d edge with 95% CIs
    try:
        from src import self_awareness as _sa
        sa_stats = _sa.rolling_window(30)
        sa_block = _sa.format_footer(sa_stats)
        if sa_block:
            lines.append("")
            lines.append("🛡 *Self-awareness (Pillar 5)*")
            lines.append(sa_block)
    except Exception:
        pass


    # Pillar 6 — Week-over-Week trend + per-sector P&L
    try:
        from src.wow_trend import compare as _wow, format_footer as _wow_fmt
        cmp = _wow(picks)
        wow_block = _wow_fmt(cmp)
        if wow_block:
            lines.append("")
            lines.append("📈 *Week-over-Week (Pillar 6)*")
            lines.append(wow_block)
    except Exception:
        pass

    try:
        from src.sector_pnl import per_sector_pnl as _spnl, format_table as _spnl_tbl
        rows = _spnl(picks)
        if rows:
            lines.append("")
            lines.append("💰 *Per-sector P&L (Pillar 6)*")
            lines.append(_spnl_tbl(rows))
    except Exception:
        pass

    lines.append("")
    lines.append("📋 *Recommended action*")
    for a in r["actions"]:
        lines.append(f"• {a}")

    return "\n".join(lines)


def format_markdown(r: Dict) -> str:
    """Same content but markdown-friendly for the snapshot file."""
    text = format_telegram(r)
    # Strip Telegram markdown asterisks for cleaner MD
    return text.replace("*", "**")


def save_snapshot(r: Dict) -> Path:
    fname = f"weekly_{datetime.now().strftime('%Y_%m_%d')}.md"
    out = REPORTS / fname
    out.write_text(format_markdown(r))
    return out
