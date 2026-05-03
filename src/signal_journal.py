"""
Signal Journal — append-only log of WHICH signals were active for each pick,
plus the outcome once the pick closes.

Used by hypothesis_engine.py to test "does signal X actually predict edge?"

Format: data/signal_journal.jsonl
Each line:
  {
    "pick_date": "2026-05-04",
    "ticker": "NVDA",
    "signals": {
       "composite_score_bucket": "high",
       "regime": "bull",
       "tag": "SEMI",
       "days_to_earnings_bucket": "near",
       "vol_ratio_bucket": "high",
       "monster_score_bucket": "monster",
       "brain_p_win_bucket": "high",
       "trade_type": "swing",
    },
    "outcome": null,        # filled later when closed
    "r_multiple": null,
    "actual_return_pct": null,
    "evaluated_on": null,
  }

Outcomes are attached by attach_outcome() once pick_evaluator closes the pick.
"""
import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

JOURNAL = Path("data/signal_journal.jsonl")
JOURNAL.parent.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# Bucketing helpers (deterministic, tested)
# ═══════════════════════════════════════════════════════════════
def bucket_composite(score: Optional[float]) -> str:
    if score is None: return "unknown"
    if score < 0.7:   return "low"
    if score < 0.85:  return "mid"
    return "high"


def bucket_d2e(d2e: Optional[int]) -> str:
    if d2e is None or d2e == "" or d2e == "none": return "none"
    try:
        d = int(d2e)
    except (ValueError, TypeError):
        return "none"
    if d < 0:   return "none"
    if d <= 3:  return "imminent"
    if d <= 7:  return "near"
    return "far"


def bucket_vol(vr: Optional[float]) -> str:
    if vr is None: return "unknown"
    if vr < 1.0:   return "low"
    if vr < 1.5:   return "normal"
    return "high"


def bucket_monster(ms: Optional[float]) -> str:
    if ms is None: return "none"
    try:
        v = float(ms)
    except (ValueError, TypeError):
        return "none"
    if v < 0.3:    return "none"
    if v < 0.6:    return "mid"
    return "monster"


def bucket_p_win(pw: Optional[float]) -> str:
    if pw is None: return "unknown"
    try:
        v = float(pw)
    except (ValueError, TypeError):
        return "unknown"
    if v < 0.45:   return "low"
    if v < 0.55:   return "mid"
    return "high"


def primary_tag(tag: Optional[str]) -> str:
    if not tag: return "none"
    return str(tag).split("/")[0].strip().upper() or "none"


def build_signals(pick: Dict) -> Dict[str, str]:
    """From a pick dict (with scores subdict), produce the bucketed signal map."""
    scores = pick.get("scores", {}) if "scores" in pick else pick
    brain  = pick.get("brain", {}) or {}
    return {
        "composite_score_bucket": bucket_composite(scores.get("composite")),
        "regime":                 (pick.get("regime") or "unknown"),
        "tag":                    primary_tag(scores.get("sector_tag") or pick.get("tag")),
        "days_to_earnings_bucket": bucket_d2e(pick.get("days_to_earnings")),
        "vol_ratio_bucket":       bucket_vol(pick.get("vol_ratio") or scores.get("vol_ratio")),
        "monster_score_bucket":   bucket_monster(scores.get("monster_score")),
        "brain_p_win_bucket":     bucket_p_win(brain.get("p_win")),
        "trade_type":             pick.get("trade_type", "swing"),
    }


# ═══════════════════════════════════════════════════════════════
# Append + outcome attachment
# ═══════════════════════════════════════════════════════════════
def log_pick(pick: Dict, regime: Optional[str] = None) -> None:
    """Append a new pick row to the journal."""
    entry_pick = dict(pick)
    if regime and not entry_pick.get("regime"):
        entry_pick["regime"] = regime
    signals = build_signals(entry_pick)
    row = {
        "pick_date":         pick.get("pick_date") or datetime.now().strftime("%Y-%m-%d"),
        "ticker":            pick.get("ticker"),
        "signals":           signals,
        "outcome":           None,
        "r_multiple":        None,
        "actual_return_pct": None,
        "evaluated_on":      None,
    }
    with JOURNAL.open("a") as f:
        f.write(json.dumps(row) + "\n")


def attach_outcome(ticker: str, pick_date: str,
                   r_multiple: Optional[float],
                   actual_return_pct: Optional[float],
                   evaluated_on: str) -> bool:
    """Find the matching pick row and fill outcome fields. Returns True if found."""
    if not JOURNAL.exists():
        return False
    rows = []
    found = False
    with JOURNAL.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (r.get("ticker") == ticker
                    and r.get("pick_date") == pick_date
                    and r.get("outcome") is None):
                r["r_multiple"]        = r_multiple
                r["actual_return_pct"] = actual_return_pct
                r["evaluated_on"]      = evaluated_on
                if r_multiple is not None:
                    r["outcome"] = "win" if r_multiple > 0 else "loss"
                found = True
            rows.append(r)
    if found:
        with JOURNAL.open("w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
    return found


def load_closed() -> list:
    """Return all journal rows that have an outcome attached."""
    if not JOURNAL.exists():
        return []
    out = []
    with JOURNAL.open() as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("outcome") in ("win", "loss"):
                out.append(r)
    return out
