"""Phase 2B.4 — exit & capture efficiency metrics.

The headline metric this whole phase is built around:
  capture_efficiency = avg(realized_return) / avg(MFE)

Old system (single TP, no trail): ~30-50% efficiency (gives back gains).
Phase 2B target: ≥70% (locks gains via TP1, trails the rest).
"""
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional

PICKS_LOG = Path("data/picks_log.csv")


def _safe_float(v, default=0.0) -> float:
    try:
        return float(v) if v not in (None, "", "None") else default
    except (TypeError, ValueError):
        return default


def load_picks_for_date(date_str: str) -> List[Dict]:
    """Load all picks_log.csv rows for a given date."""
    if not PICKS_LOG.exists():
        return []
    out = []
    with PICKS_LOG.open() as f:
        for row in csv.DictReader(f):
            if row.get("pick_date") == date_str:
                out.append(row)
    return out


def tier_hit_breakdown(picks: List[Dict]) -> Dict[str, int]:
    """Count picks by tier_status outcome.

    Returns: {"none": N, "tp1_hit": N, "tp2_hit": N, "trailing": N, "closed": N}
    """
    counts = {"none": 0, "tp1_hit": 0, "tp2_hit": 0, "trailing": 0, "closed": 0}
    for p in picks:
        status = (p.get("tier_status") or "none").strip()
        counts[status] = counts.get(status, 0) + 1
    return counts


def trail_stats(picks: List[Dict]) -> Dict:
    """Stats on trailing-stop activations.

    Returns:
      {
        "active_count": N,           # how many had trail activate
        "avg_locked_gain_pct": float, # avg locked-in gain (current_sl vs entry)
        "max_locked_gain_pct": float,
      }
    """
    locked_gains = []
    active = 0
    for p in picks:
        if (p.get("trail_active") or "false").lower() == "true":
            active += 1
            entry = _safe_float(p.get("entry"))
            current_sl = _safe_float(p.get("current_sl"))
            if entry > 0 and current_sl > 0:
                locked_gains.append((current_sl - entry) / entry * 100)
    avg_lock = round(sum(locked_gains) / len(locked_gains), 2) if locked_gains else 0.0
    max_lock = round(max(locked_gains), 2) if locked_gains else 0.0
    return {
        "active_count": active,
        "avg_locked_gain_pct": avg_lock,
        "max_locked_gain_pct": max_lock,
    }


def tp_raise_stats(picks: List[Dict]) -> Dict:
    """Stats on adaptive TP raises.

    Returns:
      {
        "raised_count": N,           # picks with ≥1 raise
        "total_raises": N,           # total raise events across all picks
        "avg_raise_pct": float,      # avg % bump per raise (new_tp vs prev)
      }
    """
    raised_count = 0
    total_raises = 0
    raise_pcts = []
    for p in picks:
        try:
            history = json.loads(p.get("tp_raises") or "[]")
            if not isinstance(history, list) or not history:
                continue
            raised_count += 1
            total_raises += len(history)
            # Compute % bump from original TP
            original_tp = _safe_float(p.get("take_profit"))
            for event in history:
                new_tp = _safe_float(event.get("new_tp"))
                if original_tp > 0 and new_tp > 0:
                    raise_pcts.append((new_tp - original_tp) / original_tp * 100)
        except (json.JSONDecodeError, TypeError):
            continue
    avg_pct = round(sum(raise_pcts) / len(raise_pcts), 2) if raise_pcts else 0.0
    return {
        "raised_count": raised_count,
        "total_raises": total_raises,
        "avg_raise_pct": avg_pct,
    }


def capture_efficiency(picks: List[Dict],
                        exec_report: Optional[Dict] = None) -> Dict:
    """How much of the available move (MFE) did we actually capture?

    capture_pct = avg(actual_return_pct) / avg(mfe_pct) × 100

    Args:
        picks: rows from picks_log.csv
        exec_report: optional dict from data/exec_report_YYYY-MM-DD.json
                     (provides mfe_pct per pick — picks_log doesn't have it)

    Returns:
      {
        "n_evaluated": N,
        "avg_realized_pct": float,
        "avg_mfe_pct": float,
        "capture_pct": float,    # higher = better (target ≥70%)
        "leakage_pct": float,    # 100 - capture_pct (lower = better)
      }
    """
    # Build MFE lookup from exec_report if provided
    mfe_by_ticker = {}
    if exec_report and "picks" in exec_report:
        for ep in exec_report["picks"]:
            t = ep.get("ticker")
            if t:
                mfe_by_ticker[t] = _safe_float(ep.get("mfe_pct"))

    realized = []
    mfes = []
    for p in picks:
        # Need actual_return_pct (from evaluator) and MFE
        ret = p.get("actual_return_pct")
        if ret in (None, "", "None"):
            continue
        ret_val = _safe_float(ret)
        mfe = mfe_by_ticker.get(p.get("ticker"))
        if mfe is None or mfe <= 0:
            continue
        realized.append(ret_val)
        mfes.append(mfe)

    if not realized or sum(mfes) == 0:
        return {
            "n_evaluated": 0,
            "avg_realized_pct": 0.0,
            "avg_mfe_pct": 0.0,
            "capture_pct": 0.0,
            "leakage_pct": 0.0,
        }

    avg_real = sum(realized) / len(realized)
    avg_mfe = sum(mfes) / len(mfes)
    capture = (avg_real / avg_mfe * 100) if avg_mfe > 0 else 0.0
    return {
        "n_evaluated": len(realized),
        "avg_realized_pct": round(avg_real, 2),
        "avg_mfe_pct": round(avg_mfe, 2),
        "capture_pct": round(capture, 1),
        "leakage_pct": round(100 - capture, 1),
    }
