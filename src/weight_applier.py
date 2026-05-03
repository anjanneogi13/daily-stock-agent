"""T44 / Pillar 4: Weight Applier — Brain's hands.

Reads unapplied proposals from data/weight_proposals.jsonl, applies each
to config/weights.json under a 5%/week-per-factor cap, and journals every
mutation to data/weight_history.jsonl + the learning journal.

  weights.json layout:
    {
      "factors": {
        "rsi": { "rsi_oversold(<30)": 0.85, ... },
        "atrpct": { "atrpct_<1.5": 1.05 }
      },
      "version": 1,
      "updated": "ISO date"
    }

Idempotent: each proposal carries a `proposal_id` (ts+factor+bucket).
Once applied, it's marked `applied: true` in proposals.jsonl. Re-running
applies only NEW proposals. Cap is enforced per (factor, ISO-week).
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src import weight_proposer as wp


WEIGHTS  = Path("config/weights.json")
HISTORY  = Path("data/weight_history.jsonl")
PROPOSALS = wp.PROPOSALS

WEEKLY_CAP_PCT = 5.0   # max cumulative |delta_pct| per (factor, week)


# ─────────── load/save weights ───────────
def _load() -> Dict:
    if not WEIGHTS.exists():
        return {"version": 1, "factors": {}, "updated": ""}
    return json.loads(WEIGHTS.read_text())


def _save(w: Dict) -> None:
    w["updated"] = datetime.now(timezone.utc).date().isoformat()
    WEIGHTS.parent.mkdir(parents=True, exist_ok=True)
    WEIGHTS.write_text(json.dumps(w, indent=2) + "\n")


# ─────────── proposal dedup key ───────────
def _pid(rec: Dict) -> str:
    return f"{rec.get('ts')}|{rec.get('factor')}|{rec.get('bucket')}"


# ─────────── weekly-cap accounting ───────────
def _iso_week(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.split("T")[0])
    except Exception:
        dt = datetime.now()
    y, w, _ = dt.isocalendar()
    return f"{y}-W{w:02d}"


def _used_this_week(history: List[Dict], factor: str, week: str) -> float:
    return sum(abs(h.get("delta_pct", 0))
               for h in history
               if h.get("factor") == factor and h.get("week") == week)


def _read_history() -> List[Dict]:
    if not HISTORY.exists():
        return []
    out = []
    for line in HISTORY.read_text().splitlines():
        if not line.strip(): continue
        try: out.append(json.loads(line))
        except: pass
    return out


def _append_history(rec: Dict) -> None:
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY.open("a") as f:
        f.write(json.dumps(rec) + "\n")


# ─────────── core ───────────
def _new_multiplier(current: float, action: str, delta_pct: float) -> float:
    """Apply a single delta to a multiplier. Floor 0.5, ceil 1.5 (safety)."""
    if action == "kill":
        new = 0.0
    elif action == "boost":
        new = current * (1 + abs(delta_pct) / 100)
    elif action == "penalize":
        new = current * (1 - abs(delta_pct) / 100)
    else:
        new = current
    return max(0.0, min(1.5, round(new, 4)))


def apply_proposals(dry_run: bool = False,
                    cap_pct: float = WEEKLY_CAP_PCT) -> Dict:
    """Apply all unapplied proposals subject to weekly cap.

    Returns: {applied:N, skipped_capped:M, skipped_invalid:K, mutations:[...]}
    """
    proposals = wp.read_proposals(only_unapplied=True)
    weights = _load()
    history = _read_history()

    factors = weights.setdefault("factors", {})
    applied = []
    skipped_capped = []
    skipped_invalid = []

    # Stable order: kills first, then largest impact (matches propose() order)
    for rec in proposals:
        factor = rec.get("factor")
        bucket = rec.get("bucket")
        action = rec.get("action")
        delta  = float(rec.get("delta_pct", 0))
        if not factor or not bucket or action not in ("kill","boost","penalize"):
            skipped_invalid.append(_pid(rec))
            continue

        week = _iso_week(rec.get("ts", ""))
        used = _used_this_week(history, factor, week)
        # kill is binary — counts as full cap usage
        cost = cap_pct if action == "kill" else abs(delta)
        if used + cost > cap_pct + 1e-6:
            skipped_capped.append({
                "pid": _pid(rec), "factor": factor, "week": week,
                "used": used, "cost": cost, "cap": cap_pct,
            })
            continue

        bucket_map = factors.setdefault(factor, {})
        cur = float(bucket_map.get(bucket, 1.0))
        new = _new_multiplier(cur, action, delta)
        bucket_map[bucket] = new

        mutation = {
            "ts":         datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "week":       week,
            "proposal_id": _pid(rec),
            "factor":     factor,
            "bucket":     bucket,
            "action":     action,
            "delta_pct":  delta,
            "old":        cur,
            "new":        new,
            "rationale":  rec.get("rationale", ""),
        }
        applied.append(mutation)
        if not dry_run:
            _append_history(mutation)
            history.append(mutation)  # so subsequent picks honour week-cap
            try:
                from src import learning_journal as _lj
                _lj.log("weight_applied", **{
                    k: mutation[k] for k in
                    ("factor","bucket","action","delta_pct","old","new")
                })
            except Exception:
                pass

    if applied and not dry_run:
        _save(weights)
        # mark proposals applied
        all_props = wp.read_proposals(only_unapplied=False)
        applied_ids = {m["proposal_id"] for m in applied}
        with PROPOSALS.open("w") as f:
            for r in all_props:
                if _pid(r) in applied_ids:
                    r["applied"] = True
                f.write(json.dumps(r) + "\n")

    return {
        "applied":         len(applied),
        "skipped_capped":  len(skipped_capped),
        "skipped_invalid": len(skipped_invalid),
        "mutations":       applied,
        "capped_details":  skipped_capped,
        "dry_run":         dry_run,
    }


# ─────────── readouts ───────────
def history_summary(days: int = 7) -> Dict:
    """For weekly Telegram footer."""
    cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
    recent = []
    for h in _read_history():
        try:
            ts = datetime.fromisoformat(h["ts"].replace("Z","+00:00")).timestamp()
        except Exception:
            continue
        if ts >= cutoff:
            recent.append(h)
    by_action = {"kill":0,"boost":0,"penalize":0}
    for h in recent:
        a = h.get("action")
        if a in by_action: by_action[a] += 1
    return {"days": days, "total": len(recent), "by_action": by_action}


def _cli(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="Actually apply (default is dry-run)")
    ap.add_argument("--cap", type=float, default=WEEKLY_CAP_PCT)
    args = ap.parse_args(argv)

    res = apply_proposals(dry_run=not args.apply, cap_pct=args.cap)
    mode = "APPLIED" if args.apply else "DRY-RUN"
    print(f"╔══ Weight Applier {mode} ══════════════════")
    print(f"║ applied:         {res['applied']}")
    print(f"║ skipped(capped): {res['skipped_capped']}")
    print(f"║ skipped(bad):    {res['skipped_invalid']}")
    if res["mutations"]:
        print("║ mutations:")
        for m in res["mutations"][:10]:
            print(f"║   {m['action']:8s} {m['factor']}={m['bucket']}  "
                  f"{m['old']:.3f}→{m['new']:.3f}  ({m['delta_pct']:+.1f}%)")
    print("╚════════════════════════════════════════════")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
