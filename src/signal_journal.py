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
    """Calibrated 2026-05-04 from 39-pick distribution (mean=0.68, p75=0.78).
    
    Old thresholds (<0.7=low, 0.7-0.85=mid, ≥0.85=high) bucketed 93% of
    picks as 'mid' → brain couldn't distinguish good from average.
    
    New thresholds reflect actual agent score distribution, giving each
    bucket meaningful population (~25% each):
      low:       < 0.55   (rare — usually filtered out before pick)
      mid:       0.55-0.70  (typical "OK" pick)
      high:      0.70-0.80  (strong pick)
      very_high: ≥ 0.80   (best-in-day pick — wisdom should heavily weight)
    """
    if score is None: return "unknown"
    try: s = float(score)
    except (TypeError, ValueError): return "unknown"
    # Thresholds based on actual agent score distribution (39 historical picks):
    #   P25=0.72, P50=0.74, P75=0.78, Max=0.85
    # Calibrated to give roughly equal population per bucket.
    if s < 0.72:  return "low"        # bottom 25% of agent picks
    if s < 0.75:  return "mid"        # 25-50%
    if s < 0.79:  return "high"       # 50-75%
    return "very_high"                # top 25% — wisdom should heavily weight


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
    """Volume vs 20-day average. Recalibrated 2026-05-04 to add 'extreme' tier.
    
    Pro traders distinguish 'institutional accumulation' (1.5-3x) from
    'news/blowoff' (>3x). Without this split, smell faculty can't tell
    quality from chaos.
    """
    if vr is None: return "unknown"
    try: v = float(vr)
    except (TypeError, ValueError): return "unknown"
    if v < 0.7:   return "low"        # below-average → weak conviction
    if v < 1.3:   return "normal"     # typical day
    if v < 2.5:   return "high"       # institutional interest
    return "extreme"                  # blowoff / news-driven (caution)


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
    """Brain's win probability estimate. 4 tiers for finer learning.
    
    Below 0.45 = brain is bearish on its own pick (rare, big red flag).
    0.55+ = brain is genuinely confident.
    0.65+ = brain says 'this is a slam dunk' (rare + valuable signal).
    """
    if pw is None: return "unknown"
    try: v = float(pw)
    except (ValueError, TypeError): return "unknown"
    if v < 0.45:   return "low"
    if v < 0.55:   return "mid"
    if v < 0.65:   return "high"
    return "very_high"


def primary_tag(tag: Optional[str]) -> str:
    if not tag: return "none"
    return str(tag).split("/")[0].strip().upper() or "none"


def build_signals(pick: Dict) -> Dict[str, str]:
    """From a pick dict, produce the bucketed signal map.

    DEFENSIVE: tolerates multiple field-naming conventions because picks come
    from different code paths (parallel_scorer, manual, evaluator) with
    inconsistent schemas. Fixed 2026-05-04 after hypothesis report showed
    100% of buckets were 'unknown'.
    """
    scores = pick.get("scores", {}) if isinstance(pick.get("scores"), dict) else {}
    brain  = pick.get("brain", {}) if isinstance(pick.get("brain"), dict) else {}

    composite = (scores.get("composite")
                 or scores.get("composite_score")
                 or pick.get("composite_score")
                 or pick.get("score"))

    tag = (pick.get("tag")
           or scores.get("sector_tag")
           or scores.get("tag"))

    vol_ratio = (pick.get("vol_ratio")
                 or scores.get("vol_ratio"))

    monster = (scores.get("monster_score")
               or pick.get("monster_score"))

    p_win = (brain.get("p_win")
             or pick.get("p_win")
             or pick.get("brain_p_win"))

    return {
        "composite_score_bucket": bucket_composite(composite),
        "regime":                 (pick.get("regime") or "unknown"),
        "tag":                    primary_tag(tag),
        "days_to_earnings_bucket": bucket_d2e(pick.get("days_to_earnings")),
        "vol_ratio_bucket":       bucket_vol(vol_ratio),
        "monster_score_bucket":   bucket_monster(monster),
        "brain_p_win_bucket":     bucket_p_win(p_win),
        "trade_type":             pick.get("trade_type", "swing"),
    }


# ═══════════════════════════════════════════════════════════════
# Append + outcome attachment
# ═══════════════════════════════════════════════════════════════
def log_pick(pick: Dict, regime: Optional[str] = None) -> None:
    """Append a new pick row to the journal.

    PR-A4.5 (2026-05-15): atomic write hardening (audit SJ-33).
    Previously: plain f.write() + implicit close. A crash mid-write produced
    a partial JSON line that broke every subsequent reader (load_closed,
    audit_journal_consistency, hypothesis_engine).

    Now: build the full line in memory FIRST, then issue a single os.write()
    of the complete bytes. POSIX guarantees atomic writes up to PIPE_BUF
    (typically 4096 bytes); journal rows are well under that. Followed by
    fsync so the write survives a power loss.
    """
    import os
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
    line_bytes = (json.dumps(row) + "\n").encode("utf-8")
    if len(line_bytes) > 4000:
        # Defensive: if a journal row ever exceeds PIPE_BUF safety margin,
        # we cannot guarantee atomic append. Loudly fail rather than risk
        # silent partial-line corruption of the entire learning journal.
        raise ValueError(
            f"signal_journal row too large for atomic append: {len(line_bytes)} bytes"
        )
    fd = os.open(str(JOURNAL), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, line_bytes)
        os.fsync(fd)
    finally:
        os.close(fd)


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
                    # Cluster H sample accounting: a ≈0% exit is FLAT, not a
                    # loss — same epsilon as the ledger taxonomy (§7), so the
                    # hypothesis-review win-rate sample matches the ledger's
                    # realized wins+losses instead of counting bell-flats
                    # as losses.
                    from .trade_state import FLAT_EPSILON_PCT
                    ret = actual_return_pct
                    if (ret is not None and abs(ret) <= FLAT_EPSILON_PCT) or \
                            (ret is None and r_multiple == 0):
                        r["outcome"] = "flat"
                    else:
                        r["outcome"] = "win" if r_multiple > 0 else "loss"
                found = True
            rows.append(r)
    if found:
        # PR-A4.5: atomic full-file rewrite via tmp+rename (audit SJ-13).
        # Previously: opened JOURNAL "w" directly. A crash between truncate
        # and final flush produced an empty or half-written journal —
        # permanent loss of every prior signal record.
        # Now: write to .tmp sibling, fsync, then os.replace which is
        # guaranteed atomic on POSIX (and atomic on NTFS too).
        import os
        tmp = JOURNAL.with_suffix(JOURNAL.suffix + ".tmp")
        with tmp.open("w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(str(tmp), str(JOURNAL))
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
