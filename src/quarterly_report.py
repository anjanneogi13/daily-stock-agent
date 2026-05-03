"""
Quarterly Report Generator — Pillar 6 v0.1

Produces a narrative markdown summary of the past N days (default 90).
Sources: picks_log.csv, signal_journal.jsonl, wisdom artifacts, git log.

Output: reports/quarterly_YYYY_QN.md
"""
import csv
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
from typing import Dict, List, Optional


PICKS_LOG = Path("data/picks_log.csv")
JOURNAL   = Path("data/signal_journal.jsonl")
REPORTS   = Path("reports")
REPORTS.mkdir(parents=True, exist_ok=True)


def _to_float(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _load_picks_in_range(start: datetime, end: datetime) -> List[Dict]:
    if not PICKS_LOG.exists():
        return []
    out = []
    with PICKS_LOG.open() as f:
        for r in csv.DictReader(f):
            try:
                d = datetime.strptime(r.get("pick_date", ""), "%Y-%m-%d")
            except ValueError:
                continue
            if start <= d <= end:
                out.append(r)
    return out


def _git_log_since(start: datetime) -> List[str]:
    try:
        out = subprocess.check_output(
            ["git", "log", f"--since={start.strftime('%Y-%m-%d')}",
             "--oneline", "--no-merges"],
            text=True, timeout=10,
        )
        return [line.strip() for line in out.strip().split("\n") if line.strip()]
    except Exception:
        return []


def _quarter_label(d: datetime) -> str:
    q = (d.month - 1) // 3 + 1
    return f"{d.year}_Q{q}"


def _summary_metrics(picks: List[Dict]) -> Dict:
    closed_set = {"tp_hit", "sl_hit", "expired"}
    closed = [p for p in picks if p.get("evaluation_status") in closed_set]

    wins   = [p for p in closed if p.get("evaluation_status") == "tp_hit"]
    losses = [p for p in closed if p.get("evaluation_status") == "sl_hit"]
    expired = [p for p in closed if p.get("evaluation_status") == "expired"]

    rs = [_to_float(p.get("r_multiple")) for p in closed]
    rs = [x for x in rs if x is not None]
    rets = [_to_float(p.get("actual_return_pct")) for p in closed]
    rets = [x for x in rets if x is not None]
    alphas = [_to_float(p.get("alpha_pct")) for p in closed]
    alphas = [x for x in alphas if x is not None]
    sec_alphas = [_to_float(p.get("sector_alpha_pct")) for p in closed]
    sec_alphas = [x for x in sec_alphas if x is not None]

    n = len(closed)
    return {
        "total_picks":   len(picks),
        "closed_picks":  n,
        "wins":          len(wins),
        "losses":        len(losses),
        "expired":       len(expired),
        "win_rate":      round(len(wins) / n, 3) if n else None,
        "total_r":       round(sum(rs), 2) if rs else None,
        "avg_r":         round(sum(rs) / len(rs), 2) if rs else None,
        "avg_return_pct": round(sum(rets) / len(rets), 2) if rets else None,
        "avg_alpha_spy": round(sum(alphas) / len(alphas), 2) if alphas else None,
        "avg_alpha_sec": round(sum(sec_alphas) / len(sec_alphas), 2) if sec_alphas else None,
    }


def _top_movers(picks: List[Dict], k: int = 5):
    closed = [p for p in picks if _to_float(p.get("r_multiple")) is not None]
    closed.sort(key=lambda p: _to_float(p.get("r_multiple"), 0), reverse=True)
    winners = closed[:k]
    losers  = sorted(closed, key=lambda p: _to_float(p.get("r_multiple"), 0))[:k]
    return winners, losers


def _journal_summary(start: datetime, end: datetime) -> Dict:
    if not JOURNAL.exists():
        return {"closed_in_journal": 0, "edges": 0, "drags": 0}
    rows = []
    with JOURNAL.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            try:
                d = datetime.strptime(r.get("pick_date", ""), "%Y-%m-%d")
            except Exception:
                continue
            if start <= d <= end and r.get("outcome") in ("win", "loss"):
                rows.append(r)
    if not rows:
        return {"closed_in_journal": 0, "edges": 0, "drags": 0}
    try:
        from .hypothesis_engine import analyze
    except ImportError:
        from hypothesis_engine import analyze
    res = analyze(rows)
    return {
        "closed_in_journal": len(rows),
        "edges": len(res.get("edges", [])),
        "drags": len(res.get("drags", [])),
        "edges_detail": res.get("edges", []),
        "drags_detail": res.get("drags", []),
    }


def _wisdom_summary() -> Dict:
    try:
        from .wisdom_base import stats, load_active_lessons, get_kill_list
    except ImportError:
        from wisdom_base import stats, load_active_lessons, get_kill_list
    return {
        "stats":        stats(),
        "lessons_top":  load_active_lessons(min_confidence=0.8)[:5],
        "kill_list":    list(get_kill_list().keys()),
    }


def generate_report(days: int = 90,
                     end_date: Optional[datetime] = None) -> Path:
    end = end_date or datetime.now()
    start = end - timedelta(days=days)
    picks = _load_picks_in_range(start, end)
    metrics = _summary_metrics(picks)
    winners, losers = _top_movers(picks, k=5)
    journal = _journal_summary(start, end)
    wisdom  = _wisdom_summary()
    commits = _git_log_since(start)

    label = _quarter_label(end)
    out_path = REPORTS / f"quarterly_{label}.md"

    md = []
    md.append(f"# 📊 Quarterly Report — {label.replace('_', ' ')}")
    md.append("")
    md.append(f"**Period:** {start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')} "
              f"({days} days)")
    md.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC")
    md.append("")

    # ── Headline numbers ──
    md.append("## 🎯 Headline")
    md.append("")
    md.append(f"- **Total picks:** {metrics['total_picks']}")
    md.append(f"- **Closed:** {metrics['closed_picks']}  "
              f"({metrics['wins']} wins · {metrics['losses']} losses · "
              f"{metrics['expired']} expired)")
    if metrics['win_rate'] is not None:
        md.append(f"- **Win rate:** {metrics['win_rate']:.1%}")
    if metrics['total_r'] is not None:
        md.append(f"- **Total R:** {metrics['total_r']:+.2f}  "
                  f"(avg {metrics['avg_r']:+.2f}/pick)")
    if metrics['avg_return_pct'] is not None:
        md.append(f"- **Avg return %:** {metrics['avg_return_pct']:+.2f}%")
    if metrics['avg_alpha_spy'] is not None:
        md.append(f"- **Avg α vs SPY:** {metrics['avg_alpha_spy']:+.2f}%")
    if metrics['avg_alpha_sec'] is not None:
        md.append(f"- **Avg α vs Sector ETF:** {metrics['avg_alpha_sec']:+.2f}%  "
                  f"_(true picker edge)_")
    md.append("")

    # ── Top winners ──
    md.append("## 🏆 Top 5 Winners (by R-multiple)")
    md.append("")
    md.append("| Ticker | Tag | Entry | Exit | Return % | R |")
    md.append("|---|---|---|---|---|---|")
    for w in winners:
        md.append(f"| {w.get('ticker','?')} | {w.get('tag','—')} | "
                  f"${w.get('entry','?')} | ${w.get('exit_price','?')} | "
                  f"{_to_float(w.get('actual_return_pct'),0):+.2f}% | "
                  f"{_to_float(w.get('r_multiple'),0):+.2f} |")
    md.append("")

    # ── Top losers ──
    md.append("## 💀 Top 5 Losers (by R-multiple)")
    md.append("")
    md.append("| Ticker | Tag | Entry | Exit | Return % | R |")
    md.append("|---|---|---|---|---|---|")
    for L in losers:
        md.append(f"| {L.get('ticker','?')} | {L.get('tag','—')} | "
                  f"${L.get('entry','?')} | ${L.get('exit_price','?')} | "
                  f"{_to_float(L.get('actual_return_pct'),0):+.2f}% | "
                  f"{_to_float(L.get('r_multiple'),0):+.2f} |")
    md.append("")

    # ── Hypothesis findings ──
    md.append("## 🧠 Hypothesis Engine Findings")
    md.append("")
    md.append(f"- Closed picks in journal: **{journal['closed_in_journal']}**")
    md.append(f"- Significant edges:       **{journal.get('edges', 0)}**")
    md.append(f"- Significant drags:       **{journal.get('drags', 0)}**")
    md.append("")
    if journal.get("edges_detail"):
        md.append("### Edges (statistically significant winners)")
        md.append("")
        for e in journal["edges_detail"][:10]:
            md.append(f"- ✅ `{e['signal']}={e['bucket']}` "
                      f"WR={e['win_rate']:.0%} (Δ{e['vs_base']:+.0%}) "
                      f"n={e['n']} p={e['p_value']:.3f}")
        md.append("")
    if journal.get("drags_detail"):
        md.append("### Drags (statistically significant losers)")
        md.append("")
        for d in journal["drags_detail"][:10]:
            md.append(f"- ❌ `{d['signal']}={d['bucket']}` "
                      f"WR={d['win_rate']:.0%} (Δ{d['vs_base']:+.0%}) "
                      f"n={d['n']} p={d['p_value']:.3f}")
        md.append("")

    # ── Wisdom base ──
    md.append("## 📚 Wisdom Base State")
    md.append("")
    md.append(f"- {wisdom['stats']['active_lessons']} active lessons")
    md.append(f"- {wisdom['stats']['active_patterns']} active patterns")
    md.append(f"- {wisdom['stats']['kill_list_size']} tickers on kill list: "
              f"`{', '.join(wisdom['kill_list']) or '—'}`")
    md.append("")
    if wisdom['lessons_top']:
        md.append("### Top high-confidence lessons")
        md.append("")
        for L in wisdom['lessons_top']:
            txt = L.get('text', '')[:200]
            md.append(f"- _{L.get('source','?')}/{L.get('confidence',0):.2f}_ — {txt}")
        md.append("")

    # ── System changes (git log) ──
    md.append("## 🛠 System Changes (commits)")
    md.append("")
    if commits:
        md.append(f"`{len(commits)}` commits in this period. Top 25:")
        md.append("")
        for c in commits[:25]:
            md.append(f"- `{c}`")
    else:
        md.append("_No commits found in window._")
    md.append("")

    # ── Footer ──
    md.append("---")
    md.append("")
    md.append("_Auto-generated by `scripts/quarterly_report.py`. "
              "Pillar 6 v0.1 — Sunday May 3 2026 sprint._")
    md.append("")

    out_path.write_text("\n".join(md))
    return out_path
