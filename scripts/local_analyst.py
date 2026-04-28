"""
Deterministic, code-based analytics — no AI required.
Reads picks_log.csv and produces a structured insights report.
Used as fallback when Gemini is unavailable.
"""
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta


def _coach(evaluated, win_rate, avg_r, total_return, tp, sl):
    """Plain-English code improvement suggestions."""
    suggestions = []
    n = len(evaluated)
    if n < 5:
        return ["📚 **Need more data.** Wait until you have 10-15 evaluated trades before drawing conclusions."]

    if win_rate < 30:
        suggestions.append(
            f"🚨 **Critical: Win rate {win_rate:.0f}%.** Below random chance for 2:1 R/R. "
            f"Action: raise MIN_SCORE by 0.05, OR add a filter (RSI<70, price above 50DMA). Pause live trading."
        )
    elif win_rate < 40:
        suggestions.append(
            f"⚠️ **Win rate {win_rate:.0f}% is weak.** With 2:1 R/R you need 33% to break even. "
            f"Action: review losers in observations.jsonl for a common pattern, add 1 filter."
        )
    elif win_rate > 65:
        suggestions.append(
            f"✅ **Excellent {win_rate:.0f}% win rate.** Don't over-optimize — could be luck. "
            f"Wait 20+ more trades to confirm."
        )

    if avg_r < -0.3:
        suggestions.append(
            f"🚨 **Avg R = {avg_r:.2f} is severely negative.** Losses bigger than wins. "
            f"Action: widen SL (try ATR×1.5 if currently tighter)."
        )
    elif avg_r < 0:
        suggestions.append(
            f"⚠️ **Avg R = {avg_r:.2f} is negative.** Tighten entries OR widen TP."
        )
    elif avg_r > 1.0:
        suggestions.append(
            f"💎 **Avg R = {avg_r:.2f} is excellent.** Edge is real. Consider scaling position size."
        )

    if sl > 0 and tp / max(sl, 1) < 0.5 and n >= 8:
        suggestions.append(
            f"⚠️ **SL hits ({sl}) ≫ TP hits ({tp}).** TPs may be too far. "
            f"Action: tighten TP to 1.5×R."
        )

    if "score" in evaluated.columns and "actual_return_pct" in evaluated.columns:
        ev = evaluated.copy()
        ev["score"] = pd.to_numeric(ev["score"], errors="coerce")
        ev["actual_return_pct"] = pd.to_numeric(ev["actual_return_pct"], errors="coerce")
        ev = ev.dropna(subset=["score", "actual_return_pct"])
        if len(ev) >= 8:
            corr = ev["score"].corr(ev["actual_return_pct"])
            if corr is not None and not pd.isna(corr):
                if corr > 0.3:
                    suggestions.append(
                        f"✅ **Score predicts returns (corr={corr:.2f}).** Higher score → higher returns. "
                        f"Action: raise MIN_SCORE by 0.05, OR weight position size by score."
                    )
                elif corr < -0.1:
                    suggestions.append(
                        f"🚨 **Score INVERSELY correlates with returns ({corr:.2f}).** "
                        f"Action: scoring formula is broken — review weights."
                    )
                else:
                    suggestions.append(
                        f"⚠️ **Score-return correlation weak ({corr:.2f}).** "
                        f"Action: add features (volume, sector RS, sentiment) or remove low-signal ones."
                    )

    if "tag" in evaluated.columns and "actual_return_pct" in evaluated.columns:
        ev = evaluated.copy()
        ev["actual_return_pct"] = pd.to_numeric(ev["actual_return_pct"], errors="coerce")
        tag_perf = ev.groupby("tag").agg(n=("ticker", "count"), avg=("actual_return_pct", "mean")).reset_index()
        for _, r in tag_perf[(tag_perf["n"] >= 3) & (tag_perf["avg"] < -1)].iterrows():
            suggestions.append(
                f"🚨 **Tag '{r['tag']}' lost {r['avg']:+.1f}% avg over {int(r['n'])} trades.** "
                f"Action: filter out or down-weight this tag."
            )
        for _, r in tag_perf[(tag_perf["n"] >= 3) & (tag_perf["avg"] > 2)].iterrows():
            suggestions.append(
                f"💎 **Tag '{r['tag']}' wins big ({r['avg']:+.1f}% avg).** "
                f"Action: boost score multiplier for this tag."
            )

    if n < 15:
        suggestions.append(
            f"📚 **Only {n} evaluated trades.** Treat suggestions as hypotheses, not conclusions."
        )

    if total_return < -5 and n >= 10:
        suggestions.append(
            f"🚨 **Cumulative {total_return:+.2f}% — strategy bleeding.** Pause live trading, run backtest."
        )

    if not suggestions:
        suggestions.append("✅ No obvious issues detected. Keep collecting data.")
    return suggestions


def analyze(period_days=7, label="Weekly"):
    csv = Path("data/picks_log.csv")
    if not csv.exists():
        return f"# 📊 {label} Local Analysis\n\n_No picks_log.csv yet._"
    df = pd.read_csv(csv)
    if df.empty:
        return f"# 📊 {label} Local Analysis\n\n_picks_log.csv is empty._"

    df["pick_date"] = pd.to_datetime(df["pick_date"], errors="coerce")
    cutoff = datetime.now() - timedelta(days=period_days)
    recent = df[df["pick_date"] >= cutoff].copy()

    lines = [f"# 📊 {label} Local Analysis ({period_days}d)\n"]

    if recent.empty:
        lines.append(f"_No picks in last {period_days} days. Total picks ever: {len(df)}_")
        _append_code_diag(lines, period_days)
        return "\n".join(lines)

    evaluated = recent[recent["evaluation_status"].isin(["tp_hit", "sl_hit", "closed"])].copy()
    pending = recent[recent["evaluation_status"] == "pending"]

    lines.append(f"**Period:** {period_days}d  •  **Picks:** {len(recent)}  •  **Evaluated:** {len(evaluated)}  •  **Pending:** {len(pending)}\n")

    if evaluated.empty:
        lines.append("_Not enough evaluated trades yet for stats._\n")
        if "tag" in recent.columns:
            lines.append("\n## 🏷️ Picks by tag")
            for tag, n in recent["tag"].value_counts().head(5).items():
                lines.append(f"- {tag}: {n}")
        _append_code_diag(lines, period_days)
        return "\n".join(lines)

    # Headline stats
    tp = (evaluated["evaluation_status"] == "tp_hit").sum()
    sl = (evaluated["evaluation_status"] == "sl_hit").sum()
    win_rate = tp / len(evaluated) * 100
    avg_r = pd.to_numeric(evaluated.get("r_multiple"), errors="coerce").mean() if "r_multiple" in evaluated else 0
    total_return = pd.to_numeric(evaluated.get("actual_return_pct"), errors="coerce").sum() if "actual_return_pct" in evaluated else 0

    lines.append("\n## 🎯 Headline")
    lines.append(f"- **Win rate:** {win_rate:.1f}%  ({tp} TP / {sl} SL)")
    lines.append(f"- **Avg R-multiple:** {avg_r:.2f}")
    lines.append(f"- **Cumulative return:** {total_return:+.2f}%")

    if "actual_return_pct" in evaluated.columns:
        ev = evaluated.copy()
        ev["actual_return_pct"] = pd.to_numeric(ev["actual_return_pct"], errors="coerce")
        ev = ev.dropna(subset=["actual_return_pct"])
        if not ev.empty:
            top = ev.nlargest(3, "actual_return_pct")
            bot = ev.nsmallest(3, "actual_return_pct")
            lines.append("\n## 🏆 Top winners")
            for _, r in top.iterrows():
                lines.append(f"- {r['ticker']}: {r['actual_return_pct']:+.2f}% (R={r.get('r_multiple','-')})")
            lines.append("\n## 💀 Worst losers")
            for _, r in bot.iterrows():
                lines.append(f"- {r['ticker']}: {r['actual_return_pct']:+.2f}% (R={r.get('r_multiple','-')})")

    if "tag" in evaluated.columns and len(evaluated) >= 3:
        ev = evaluated.copy()
        ev["actual_return_pct"] = pd.to_numeric(ev.get("actual_return_pct"), errors="coerce")
        tag_stats = ev.groupby("tag").agg(
            n=("ticker", "count"),
            wins=("evaluation_status", lambda s: (s == "tp_hit").sum()),
            avg_return=("actual_return_pct", "mean"),
        ).reset_index()
        tag_stats["win_rate"] = (tag_stats["wins"] / tag_stats["n"] * 100).round(1)
        lines.append("\n## 🏷️ Tag performance")
        for _, r in tag_stats.sort_values("avg_return", ascending=False).iterrows():
            lines.append(f"- **{r['tag']}**: {r['n']} trades, {r['win_rate']}% win, avg {r['avg_return']:+.2f}%")

    if "score" in evaluated.columns and len(evaluated) >= 5:
        ev = evaluated.copy()
        ev["score"] = pd.to_numeric(ev["score"], errors="coerce")
        ev["actual_return_pct"] = pd.to_numeric(ev["actual_return_pct"], errors="coerce")
        ev["bucket"] = pd.cut(ev["score"], bins=[0, 0.7, 0.8, 0.9, 1.0], labels=["<0.7", "0.7-0.8", "0.8-0.9", "0.9+"])
        bucket = ev.groupby("bucket", observed=True).agg(
            n=("ticker", "count"),
            avg_return=("actual_return_pct", "mean"),
            wins=("evaluation_status", lambda s: (s == "tp_hit").sum()),
        ).reset_index()
        bucket["win_rate"] = (bucket["wins"] / bucket["n"] * 100).round(1)
        lines.append("\n## 📊 Score bucket performance")
        for _, r in bucket.iterrows():
            lines.append(f"- Score {r['bucket']}: {r['n']} trades, {r['win_rate']}% win, avg {r['avg_return']:+.2f}%")

    lines.append("\n## 💡 Code Improvement Suggestions (plain English)")
    for s in _coach(evaluated, win_rate, avg_r, total_return, tp, sl):
        lines.append(f"\n{s}")

    _append_code_diag(lines, period_days)
    lines.append("\n\n---\n_Deterministic rules, not AI. Use as hypotheses to test._")
    return "\n".join(lines)


def _append_code_diag(lines, period_days):
    """Append code-aware diagnostic from code_inspector if available."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from code_inspector import report as _cr
        lines.append("\n\n" + _cr(period_days))
    except Exception as e:
        lines.append(f"\n\n_Code-aware diagnostic skipped: {e}_")


if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    label = sys.argv[2] if len(sys.argv) > 2 else "Weekly"
    print(analyze(days, label))
