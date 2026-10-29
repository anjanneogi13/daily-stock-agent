"""
Deterministic, code-based analytics — no AI required.
Reads picks_log.csv and produces a structured insights report.
Used as fallback when Gemini is unavailable.
"""
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta


def _coach(evaluated, win_rate, avg_r, total_return, tp, sl, avg_rr=2.0):
    """Plain-English code improvement suggestions."""
    suggestions = []
    n = len(evaluated)
    if n < 5:
        return ["📚 **Need more data.** Wait until you have 10-15 evaluated trades before drawing conclusions."]

    # Break-even win rate follows from the ACTUAL planned R:R, not an assumed
    # 2:1 (live swing picks ran at 1.25:1 for months → 44% needed, not 33%).
    be = 100.0 / (1.0 + avg_rr) if avg_rr and avg_rr > 0 else 33.0
    if win_rate < be - 5:
        suggestions.append(
            f"🚨 **Critical: Win rate {win_rate:.0f}% vs {be:.0f}% break-even at R:R {avg_rr:.2f}.** "
            f"Negative expectancy. Action: raise MIN_SCORE by 0.05 OR add a filter (RSI<70, price above 50DMA), "
            f"and/or widen TP relative to SL. Pause live trading."
        )
    elif win_rate < be + 5:
        suggestions.append(
            f"⚠️ **Win rate {win_rate:.0f}% is near break-even ({be:.0f}% at R:R {avg_rr:.2f}).** "
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

    # Official picks only (watch-only rows are not picks).
    if "watch_only" in df.columns:
        df = df[~df["watch_only"].astype(str).str.strip().str.lower().isin(["true", "1", "yes"])].copy()
    df["pick_date"] = pd.to_datetime(df["pick_date"], errors="coerce")
    df["_evaluated_on"] = pd.to_datetime(df.get("evaluated_on"), errors="coerce")
    df["r_multiple"] = pd.to_numeric(df.get("r_multiple"), errors="coerce")
    cutoff = datetime.now() - timedelta(days=period_days)
    recent = df[df["pick_date"] >= cutoff].copy()

    lines = [f"# 📊 {label} Local Analysis ({period_days}d)\n"]

    # Canonical closed set (src/outcome_window): tp_hit / sl_hit / day_close /
    # expired-with-price, windowed by evaluated_on (when the outcome became
    # known). The old filter used pick_date and {tp_hit, sl_hit, "closed"} —
    # it dropped every expired/day_close trade and saw ~1 closed swing per
    # week, so this report said "Not enough evaluated trades" forever.
    closed_mask = (df["evaluation_status"].isin(["tp_hit", "sl_hit", "expired", "day_close"])
                   & df["r_multiple"].notna()
                   & (df["_evaluated_on"].fillna(df["pick_date"]) >= cutoff))
    evaluated = df[closed_mask].copy()
    pending = df[df["evaluation_status"] == "pending"]

    if recent.empty and evaluated.empty:
        lines.append(f"_No picks or closed trades in last {period_days} days. Total picks ever: {len(df)}_")
        _append_code_diag(lines, period_days)
        return "\n".join(lines)

    lines.append(f"**Period:** {period_days}d  •  **Picks made:** {len(recent)}  •  "
                 f"**Closed (by evaluated_on):** {len(evaluated)}  •  **Pending:** {len(pending)}\n")

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
    win_rate = (evaluated["r_multiple"] > 0).sum() / len(evaluated) * 100  # win = R > 0
    rr_series = pd.to_numeric(evaluated.get("risk_reward"), errors="coerce").dropna()
    avg_rr = float(rr_series.mean()) if not rr_series.empty else 2.0
    breakeven_wr = 100.0 / (1.0 + avg_rr) if avg_rr > 0 else 50.0
    avg_r = pd.to_numeric(evaluated.get("r_multiple"), errors="coerce").mean() if "r_multiple" in evaluated else 0
    total_return = pd.to_numeric(evaluated.get("actual_return_pct"), errors="coerce").sum() if "actual_return_pct" in evaluated else 0

    lines.append("\n## 🎯 Headline")
    lines.append(f"- **Win rate (R>0):** {win_rate:.1f}%  ({tp} TP / {sl} SL / "
                 f"{(evaluated['evaluation_status'] == 'expired').sum()} expired / "
                 f"{(evaluated['evaluation_status'] == 'day_close').sum()} day_close)")
    lines.append(f"- **Planned R:R:** {avg_rr:.2f}  →  break-even win rate {breakeven_wr:.0f}%")
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
    for s in _coach(evaluated, win_rate, avg_r, total_return, tp, sl, avg_rr=avg_rr):
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
