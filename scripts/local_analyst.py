"""
Deterministic, code-based analytics — no AI required.
Reads picks_log.csv and produces a structured insights report.
Used as fallback when Gemini is unavailable.
"""
from pathlib import Path
import pandas as pd
from collections import defaultdict
from datetime import datetime, timedelta

def analyze(period_days=7, label="Weekly"):
    csv = Path("data/picks_log.csv")
    if not csv.exists():
        return f"# 📊 {label} Local Analysis\n\n_No picks_log.csv found yet._"
    
    df = pd.read_csv(csv)
    if df.empty:
        return f"# 📊 {label} Local Analysis\n\n_picks_log.csv is empty._"
    
    # Filter to last N days
    df['pick_date'] = pd.to_datetime(df['pick_date'], errors='coerce')
    cutoff = datetime.now() - timedelta(days=period_days)
    recent = df[df['pick_date'] >= cutoff].copy()
    
    if recent.empty:
        return f"# 📊 {label} Local Analysis\n\n_No picks in the last {period_days} days._\n\nTotal picks ever: {len(df)}"
    
    # Evaluated subset
    evaluated = recent[recent['evaluation_status'].isin(['tp_hit', 'sl_hit', 'closed'])].copy()
    pending = recent[recent['evaluation_status'] == 'pending']
    
    lines = [f"# 📊 {label} Local Analysis ({period_days}d)\n"]
    lines.append(f"**Period:** last {period_days} days  •  **Picks:** {len(recent)}  •  **Evaluated:** {len(evaluated)}  •  **Pending:** {len(pending)}\n")
    
    if evaluated.empty:
        lines.append("\n_Not enough evaluated trades yet for stats. Stay patient — data will accumulate._\n")
        # Still show breakdown of picks made
        if 'tag' in recent.columns:
            tag_counts = recent['tag'].value_counts().head(5)
            lines.append("\n## 🏷️ Picks by tag")
            for tag, n in tag_counts.items():
                lines.append(f"- {tag}: {n}")
        try:
        from code_inspector import report as _code_report
        lines.append("\n\n" + _code_report(period_days))
    except Exception as _e:
        lines.append(f"\n\n_Code-aware diagnostic skipped: {_e}_")
    return "\n".join(lines)
    
    # ── Headline stats ──────────────────────────────
    tp = (evaluated['evaluation_status'] == 'tp_hit').sum()
    sl = (evaluated['evaluation_status'] == 'sl_hit').sum()
    win_rate = tp / len(evaluated) * 100 if len(evaluated) else 0
    avg_r = evaluated['r_multiple'].astype(float).mean() if 'r_multiple' in evaluated else 0
    total_return = evaluated['actual_return_pct'].astype(float).sum() if 'actual_return_pct' in evaluated else 0
    
    lines.append("\n## 🎯 Headline")
    lines.append(f"- **Win rate:** {win_rate:.1f}%  ({tp} TP / {sl} SL)")
    lines.append(f"- **Avg R-multiple:** {avg_r:.2f}")
    lines.append(f"- **Cumulative return:** {total_return:+.2f}%")
    
    # ── Best / worst tickers ────────────────────────
    if 'actual_return_pct' in evaluated.columns:
        ev = evaluated.dropna(subset=['actual_return_pct']).copy()
        ev['actual_return_pct'] = ev['actual_return_pct'].astype(float)
        if not ev.empty:
            top = ev.nlargest(3, 'actual_return_pct')[['ticker', 'actual_return_pct', 'r_multiple']]
            bot = ev.nsmallest(3, 'actual_return_pct')[['ticker', 'actual_return_pct', 'r_multiple']]
            lines.append("\n## 🏆 Top winners")
            for _, r in top.iterrows():
                lines.append(f"- {r['ticker']}: {r['actual_return_pct']:+.2f}% (R={r['r_multiple']})")
            lines.append("\n## 💀 Worst losers")
            for _, r in bot.iterrows():
                lines.append(f"- {r['ticker']}: {r['actual_return_pct']:+.2f}% (R={r['r_multiple']})")
    
    # ── Tag performance ─────────────────────────────
    if 'tag' in evaluated.columns and len(evaluated) >= 3:
        tag_stats = evaluated.groupby('tag').agg(
            n=('ticker', 'count'),
            wins=('evaluation_status', lambda s: (s == 'tp_hit').sum()),
            avg_return=('actual_return_pct', lambda s: pd.to_numeric(s, errors='coerce').mean()),
        ).reset_index()
        tag_stats['win_rate'] = (tag_stats['wins'] / tag_stats['n'] * 100).round(1)
        tag_stats = tag_stats.sort_values('avg_return', ascending=False)
        lines.append("\n## 🏷️ Tag performance")
        for _, r in tag_stats.iterrows():
            lines.append(f"- **{r['tag']}**: {r['n']} trades, {r['win_rate']}% win, avg {r['avg_return']:+.2f}%")
    
    # ── Score bucket analysis ───────────────────────
    if 'score' in evaluated.columns and len(evaluated) >= 5:
        ev = evaluated.copy()
        ev['score'] = pd.to_numeric(ev['score'], errors='coerce')
        ev['actual_return_pct'] = pd.to_numeric(ev['actual_return_pct'], errors='coerce')
        ev['bucket'] = pd.cut(ev['score'], bins=[0, 0.7, 0.8, 0.9, 1.0], labels=['<0.7', '0.7-0.8', '0.8-0.9', '0.9+'])
        bucket = ev.groupby('bucket', observed=True).agg(
            n=('ticker', 'count'),
            avg_return=('actual_return_pct', 'mean'),
            wins=('evaluation_status', lambda s: (s == 'tp_hit').sum()),
        ).reset_index()
        bucket['win_rate'] = (bucket['wins'] / bucket['n'] * 100).round(1)
        lines.append("\n## 📊 Score bucket performance")
        for _, r in bucket.iterrows():
            lines.append(f"- Score {r['bucket']}: {r['n']} trades, {r['win_rate']}% win, avg {r['avg_return']:+.2f}%")
    
    # ── Auto-suggestions ────────────────────────────
    lines.append("\n## 💡 Auto-suggestions")
    suggestions = []
    if win_rate < 40 and len(evaluated) >= 5:
        suggestions.append(f"⚠️ Win rate {win_rate:.0f}% is below 40% — consider raising min_score threshold or tightening entry filters.")
    if avg_r < 0:
        suggestions.append(f"⚠️ Avg R={avg_r:.2f} is negative — risk/reward setup may be miscalibrated. Review stop-loss placement.")
    if 'score' in evaluated.columns and len(evaluated) >= 5:
        ev2 = evaluated.copy()
        ev2['score'] = pd.to_numeric(ev2['score'], errors='coerce')
        ev2['actual_return_pct'] = pd.to_numeric(ev2['actual_return_pct'], errors='coerce')
        low = ev2[ev2['score'] < 0.75]['actual_return_pct'].mean()
        high = ev2[ev2['score'] >= 0.8]['actual_return_pct'].mean()
        if pd.notna(low) and pd.notna(high) and high > low + 1:
            suggestions.append(f"✅ Score ≥0.80 averages {high:+.2f}% vs {low:+.2f}% for <0.75 — raising min_score to 0.78+ may help.")
    if sl > tp * 1.5 and len(evaluated) >= 5:
        suggestions.append(f"⚠️ SL hits ({sl}) significantly exceed TP hits ({tp}) — consider widening TP or tightening entry timing.")
    if not suggestions:
        suggestions.append("✅ No red flags detected. Keep collecting data — meaningful patterns emerge after ~30+ evaluated trades.")
    for s in suggestions:
        lines.append(f"- {s}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    label = sys.argv[2] if len(sys.argv) > 2 else "Weekly"
    print(analyze(days, label))
