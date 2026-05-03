"""T50 — The Meta-Brain: a brain that reasons about the brain itself.

Reads learning_journal.jsonl + signal_journal.jsonl + pattern_stats and produces:

  1. Weekly self-improvement digest      (what changed about the brain)
  2. Stuck-area detection                (no mutations in N days = stuck)
  3. Hypothesis suggestor                (over/under-performing buckets)
  4. Plain-English summary for Telegram  (for amateur readers)

Output drives the Sunday "Self-Improvement Report" Telegram message.

PHILOSOPHY: This module never mutates anything. It only OBSERVES the
brain's recent behavior and surfaces insights in plain English. The
mutations themselves happen in nightly_conductor.
"""
from __future__ import annotations
import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


JOURNAL = Path("data/learning_journal.jsonl")
PICKS   = Path("data/picks_log.csv")
STATS   = Path("data/pattern_stats.json")


def _to_float(v):
    try: return float(v)
    except (TypeError, ValueError): return None


def _read_jsonl(p: Path) -> List[Dict]:
    if not p.exists(): return []
    out = []
    for line in p.read_text().splitlines():
        if not line.strip(): continue
        try: out.append(json.loads(line))
        except: pass
    return out


# ═══════════════════════════════════════════════════════════════
# 1. Recent mutations (what changed about the brain)
# ═══════════════════════════════════════════════════════════════
def recent_mutations(days: int = 7,
                     journal_path: Optional[Path] = None) -> List[Dict]:
    """Return brain mutation events from the last N days."""
    events = _read_jsonl(journal_path or JOURNAL)
    cutoff = datetime.now() - timedelta(days=days)
    out = []
    for e in events:
        try:
            ts = datetime.fromisoformat(str(e.get("ts","")).split(".")[0])
            if ts >= cutoff:
                out.append(e)
        except Exception:
            continue
    return out


def categorize_mutations(events: List[Dict]) -> Dict[str, List[Dict]]:
    """Group events by kind for easier summarization."""
    by_kind: Dict[str, List[Dict]] = defaultdict(list)
    for e in events:
        by_kind[e.get("kind","unknown")].append(e)
    return dict(by_kind)


# ═══════════════════════════════════════════════════════════════
# 2. Stuck-area detection
# ═══════════════════════════════════════════════════════════════
def detect_stuck_areas(events: List[Dict],
                       stuck_days: int = 14) -> Dict:
    """Flag concerning lack-of-learning patterns."""
    if not events:
        return {"stuck": True, "reason": f"No brain mutations in last {stuck_days}d",
                "severity": "high"}
    # Most-recent mutation age
    latest = max((e.get("ts","") for e in events), default="")
    try:
        last_dt = datetime.fromisoformat(str(latest).split(".")[0])
        age_days = (datetime.now() - last_dt).days
    except Exception:
        age_days = 999
    if age_days >= stuck_days:
        return {"stuck": True, "age_days": age_days,
                "reason": f"Last brain change was {age_days}d ago — possibly stuck",
                "severity": "medium"}
    return {"stuck": False, "age_days": age_days}


# ═══════════════════════════════════════════════════════════════
# 3. Hypothesis suggestor — find buckets worth investigating
# ═══════════════════════════════════════════════════════════════
def suggest_hypotheses(picks_path: Optional[Path] = None,
                       min_n: int = 20,
                       lookback_days: int = 60) -> List[Dict]:
    """Look at recent closed picks. For each tag/sector with n≥min_n,
    flag if win-rate sharply differs from baseline (>15% absolute swing).

    Returns plain-English hypotheses to test next.
    """
    p = picks_path or PICKS
    if not p.exists():
        return []
    cutoff = datetime.now().date() - timedelta(days=lookback_days)
    rows = []
    try:
        with p.open() as f:
            for r in csv.DictReader(f):
                d = r.get("pick_date") or r.get("date")
                if not d: continue
                try:
                    dd = datetime.fromisoformat(str(d).split("T")[0]).date()
                except Exception:
                    continue
                if dd < cutoff: continue
                if r.get("r_multiple") in (None, ""): continue
                rows.append(r)
    except Exception:
        return []
    if not rows:
        return []
    # Baseline win rate
    rs_all = [_to_float(r.get("r_multiple")) for r in rows]
    rs_all = [x for x in rs_all if x is not None]
    if not rs_all: return []
    baseline_wr = sum(1 for x in rs_all if x > 0) / len(rs_all)

    # Group by sector_cat / sector_tag / trade_type
    hypotheses = []
    for group_key in ("sector_cat","sector_tag","trade_type","regime"):
        groups: Dict[str, List[float]] = defaultdict(list)
        for r in rows:
            v = r.get(group_key)
            if not v: continue
            rm = _to_float(r.get("r_multiple"))
            if rm is None: continue
            groups[v].append(rm)
        for label, vals in groups.items():
            if len(vals) < min_n: continue
            wr = sum(1 for x in vals if x > 0) / len(vals)
            delta = wr - baseline_wr
            if abs(delta) >= 0.15:
                direction = "outperforming" if delta > 0 else "underperforming"
                hypotheses.append({
                    "group":     group_key,
                    "label":     label,
                    "n":         len(vals),
                    "win_rate":  round(wr, 3),
                    "baseline":  round(baseline_wr, 3),
                    "delta":     round(delta, 3),
                    "direction": direction,
                    "suggestion":(f"Investigate {group_key}={label!r} "
                                  f"({direction} by {abs(delta)*100:.0f}%, n={len(vals)})"),
                })
    # Sort by absolute delta descending
    hypotheses.sort(key=lambda h: abs(h["delta"]), reverse=True)
    return hypotheses[:5]


# ═══════════════════════════════════════════════════════════════
# 4. Plain-English summary (for Telegram)
# ═══════════════════════════════════════════════════════════════
def _human_summary_of_mutations(by_kind: Dict[str, List[Dict]]) -> List[str]:
    """Translate mutation events into 'a friend explaining over coffee'."""
    out = []
    if "weight_applied" in by_kind:
        n = len(by_kind["weight_applied"])
        out.append(f"📊 Adjusted how it weighs {n} signal(s) when scoring stocks")
    if "pattern_disabled" in by_kind:
        names = [e.get("pattern","?") for e in by_kind["pattern_disabled"]]
        out.append(f"🚫 Stopped using {len(names)} chart pattern(s) that were losing money: {', '.join(names[:3])}")
    if "pattern_enabled" in by_kind:
        names = [e.get("pattern","?") for e in by_kind["pattern_enabled"]]
        out.append(f"✅ Re-enabled {len(names)} pattern(s) that started working again: {', '.join(names[:3])}")
    if "lesson_promoted" in by_kind or "pattern_promoted" in by_kind:
        n = len(by_kind.get("lesson_promoted", [])) + len(by_kind.get("pattern_promoted", []))
        out.append(f"📚 Learned {n} new trading lesson(s) from its own track record")
    if "lesson_demoted" in by_kind:
        n = len(by_kind["lesson_demoted"])
        out.append(f"🗑 Forgot {n} lesson(s) that turned out to be wrong")
    if "nightly_brain_run" in by_kind:
        n = len(by_kind["nightly_brain_run"])
        out.append(f"🌙 Ran its nightly maintenance check {n} time(s)")
    return out


def build_self_improvement_digest(days: int = 7) -> Dict:
    """Master function — assembles everything for the Sunday Telegram."""
    events    = recent_mutations(days)
    by_kind   = categorize_mutations(events)
    stuck     = detect_stuck_areas(events)
    hyps      = suggest_hypotheses()
    plain     = _human_summary_of_mutations(by_kind)
    # 🗓 T51 — Calendar renewal warning
    calendar_warning = None
    try:
        from src.market_calendar import renewal_message, years_remaining
        calendar_warning = renewal_message()
        cal_years_left = years_remaining()
    except Exception:
        cal_years_left = None
    return {
        "days":       days,
        "n_events":   len(events),
        "by_kind":    {k: len(v) for k, v in by_kind.items()},
        "stuck":      stuck,
        "hypotheses": hyps,
        "plain_english": plain,
        "calendar_warning": calendar_warning,
        "calendar_years_remaining": cal_years_left,
    }


def format_telegram_digest(digest: Dict) -> str:
    """Render the digest as a plain-English Telegram message."""
    L = []
    L.append("🧠 *Your AI Trader's Weekly Self-Improvement Report*")
    L.append("")
    L.append(f"_Looking back at the last {digest.get('days',7)} days..._")
    L.append("")

    plain = digest.get("plain_english", [])
    if plain:
        L.append("*✨ This week your brain made itself smarter in these ways:*")
        for line in plain:
            L.append(f"  • {line}")
    else:
        L.append("*🧘 Quiet week — no big self-changes.*")
        L.append("  This is normal when the strategy is performing in line with expectations.")
    L.append("")

    stuck = digest.get("stuck", {})
    if stuck.get("stuck"):
        L.append("*⚠️ Heads up:*")
        L.append(f"  {stuck.get('reason','(no detail)')}")
        L.append(f"  _Severity: {stuck.get('severity','low')}_")
        L.append("")

    hyps = digest.get("hypotheses", [])
    if hyps:
        L.append("*🔍 Areas it's investigating next:*")
        for h in hyps[:3]:
            tag = h.get("label","?")
            wr_pct = h.get("win_rate",0)*100
            base_pct = h.get("baseline",0)*100
            direction = "winning more" if h["delta"] > 0 else "losing more"
            L.append(f"  • Picks tagged *{tag}* are {direction} than average "
                     f"({wr_pct:.0f}% vs {base_pct:.0f}% baseline, {h['n']} trades)")
    # 🗓 T51 — calendar renewal heads-up (annual)
    if digest.get("calendar_warning"):
        L.append("")
        L.append("*📅 Maintenance heads-up:*")
        L.append(f"  {digest['calendar_warning']}")
    L.append("")
    L.append("_Remember: this brain learns from every trade. Some weeks it changes a lot, some weeks it just observes._")
    return "\n".join(L)
