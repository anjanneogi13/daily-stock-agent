"""T39: Weight-Delta Proposer (Pillar 3.5 — C3).

READS calibration output and PROPOSES weight adjustments. Writes to
data/weight_proposals.jsonl. **Never auto-applies** — humans (or a
future C5/C6 with safety caps) must approve.

Decision rule per bucket:
  - skip if n < min_n (default 30)
  - bias_R = mean_r vs overall mean_r
  - propose: action="boost"  if bias_R > +0.10
  - propose: action="penalize" if bias_R < -0.10
  - propose: action="kill"    if bias_R < -0.30 AND win_rate < 0.35
  - delta_pct = clamp(bias_R * 25, -5, +5)   # max ±5%/week per pillar
  - confidence = min(1.0, sqrt(n / 100))     # √n scaling, caps at n=100

Each proposal:
  {
    "ts":         iso timestamp,
    "run_id":     backtest run id,
    "factor":     "rsi" | "score" | ...,
    "bucket":     "rsi_oversold(<30)",
    "n":          33,
    "win_rate":   0.273,
    "mean_r":     -0.278,
    "bias_r":     -0.36,
    "action":     "kill" | "penalize" | "boost",
    "delta_pct":  -5.0,
    "confidence": 0.57,
    "rationale":  "human-readable",
    "applied":    false
  }

CLI:
  python -m src.weight_proposer propose [--run latest] [--min-n 30] [--dry-run]
  python -m src.weight_proposer history [--limit 20]
  python -m src.weight_proposer review [--unapplied]
"""
from __future__ import annotations
import argparse
import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src import calibration as cal

PROPOSALS = Path("data/weight_proposals.jsonl")

BIAS_BOOST_THRESHOLD    = 0.10   # mean_r above overall by this → boost
BIAS_PENALIZE_THRESHOLD = -0.10  # mean_r below overall by this → penalize
KILL_BIAS_THRESHOLD     = -0.30  # combined with low win_rate → kill
KILL_WIN_RATE_MAX       = 0.35
DELTA_CAP               = 5.0    # max ±% adjustment per proposal
DELTA_MULTIPLIER        = 25     # bias_r 0.20 → 5% delta


@dataclass
class Proposal:
    ts:         str
    run_id:     str
    factor:     str
    bucket:     str
    n:          int
    win_rate:   float
    mean_r:     float
    bias_r:     float
    action:     str        # "boost" | "penalize" | "kill"
    delta_pct:  float
    confidence: float
    rationale:  str
    applied:    bool = False

    def as_dict(self) -> Dict:
        return asdict(self)


# ───────────────── proposal generation ─────────────────

def _classify(bias_r: float, win_rate: float) -> Optional[str]:
    if bias_r < KILL_BIAS_THRESHOLD and win_rate < KILL_WIN_RATE_MAX:
        return "kill"
    if bias_r > BIAS_BOOST_THRESHOLD:
        return "boost"
    if bias_r < BIAS_PENALIZE_THRESHOLD:
        return "penalize"
    return None  # too neutral to act on


def _delta_pct(bias_r: float, action: str) -> float:
    """Map bias to a capped ±% delta. Kill always = -DELTA_CAP."""
    if action == "kill":
        return -DELTA_CAP
    raw = bias_r * DELTA_MULTIPLIER
    return max(-DELTA_CAP, min(DELTA_CAP, round(raw, 2)))


def _confidence(n: int) -> float:
    """√n scaling, caps at n=100."""
    if n <= 0:
        return 0.0
    return round(min(1.0, math.sqrt(n / 100)), 3)


def _rationale(factor: str, bucket: str, n: int, wr: float,
               mean_r: float, bias_r: float, action: str) -> str:
    sign = "+" if bias_r >= 0 else ""
    return (f"{factor}={bucket}: n={n}, win_rate={wr:.0%}, "
            f"mean_R={mean_r:+.3f} ({sign}{bias_r:+.3f} vs overall) → {action}")


def propose(rows: List[Dict], run_id: str,
            min_n: int = 30) -> List[Proposal]:
    """Generate proposals from a list of pick rows."""
    if not rows:
        return []

    overall = cal.overall_summary(rows)
    overall_mean_r = overall["mean_r"]

    factor_report = cal.per_factor_report(rows, min_n=min_n)
    ts = datetime.now().isoformat(timespec="seconds")

    proposals: List[Proposal] = []
    for factor, table in factor_report.items():
        # exit_status is descriptive (sl_hit / tp_hit etc), not a knob
        # we can twist — skip it from auto-proposals.
        if factor == "exit_status":
            continue
        for bucket_row in table:
            n = bucket_row["n"]
            if n < min_n:
                continue
            wr = bucket_row["win_rate"]
            mean_r = bucket_row["mean_r"]
            bias_r = round(mean_r - overall_mean_r, 3)
            action = _classify(bias_r, wr)
            if action is None:
                continue
            proposals.append(Proposal(
                ts=ts,
                run_id=run_id,
                factor=factor,
                bucket=bucket_row["bucket"],
                n=n,
                win_rate=wr,
                mean_r=mean_r,
                bias_r=bias_r,
                action=action,
                delta_pct=_delta_pct(bias_r, action),
                confidence=_confidence(n),
                rationale=_rationale(factor, bucket_row["bucket"], n, wr,
                                     mean_r, bias_r, action),
            ))
    # Sort: kills first, then biggest |delta| × confidence
    proposals.sort(key=lambda p: (
        0 if p.action == "kill" else 1,
        -abs(p.delta_pct) * p.confidence,
    ))
    return proposals


# ───────────────── persistence ─────────────────

def write_proposals(proposals: List[Proposal],
                    path: Optional[Path] = None) -> int:
    if not proposals:
        return 0
    path = path or PROPOSALS
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        for p in proposals:
            f.write(json.dumps(p.as_dict()) + "\n")
    return len(proposals)


def read_proposals(path: Optional[Path] = None,
                   limit: Optional[int] = None,
                   only_unapplied: bool = False) -> List[Dict]:
    path = path or PROPOSALS
    if not path.exists():
        return []
    out: List[Dict] = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if only_unapplied and rec.get("applied"):
                continue
            out.append(rec)
    if limit:
        out = out[-limit:]
    return out


# ───────────────── CLI ─────────────────

def _fmt_proposal(p: Dict) -> str:
    icon = {"kill": "🔴", "penalize": "🟠", "boost": "🟢"}.get(p["action"], "⚪")
    return (f"  {icon} {p['action']:8} "
            f"Δ{p['delta_pct']:+.1f}%  "
            f"conf={p['confidence']:.2f}  "
            f"{p['factor']}={p['bucket']:24s} "
            f"(n={p['n']}, win={p['win_rate']:.0%}, R={p['mean_r']:+.3f})")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="weight_proposer",
                                 description="T39: weight-delta proposer (READ-ONLY)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_pro = sub.add_parser("propose", help="generate proposals from a backtest run")
    p_pro.add_argument("--run", default="latest")
    p_pro.add_argument("--min-n", type=int, default=30)
    p_pro.add_argument("--dry-run", action="store_true",
                       help="print but don't persist")

    p_hist = sub.add_parser("history", help="show recent proposals")
    p_hist.add_argument("--limit", type=int, default=20)

    p_rev = sub.add_parser("review", help="show actionable proposals")
    p_rev.add_argument("--unapplied", action="store_true", default=True)

    args = ap.parse_args(argv)

    if args.cmd == "propose":
        run_dir = cal._resolve_run(args.run)
        rows = cal.load_picks(run_dir)
        proposals = propose(rows, run_dir.name, min_n=args.min_n)
        if not proposals:
            print(f"📭 no proposals for run {run_dir.name} "
                  f"(min_n={args.min_n}, all buckets too neutral)")
            return 0

        print(f"\n🧠 PROPOSALS — run {run_dir.name}  ({len(proposals)} total)")
        print(f"   Thresholds: boost>+{BIAS_BOOST_THRESHOLD} R · "
              f"penalize<{BIAS_PENALIZE_THRESHOLD} R · "
              f"kill<{KILL_BIAS_THRESHOLD}R & win<{KILL_WIN_RATE_MAX:.0%}")
        for p in proposals:
            print(_fmt_proposal(p.as_dict()))

        if args.dry_run:
            print(f"\n[DRY-RUN] would have written {len(proposals)} to {PROPOSALS}")
        else:
            n = write_proposals(proposals)
            print(f"\n✅ wrote {n} proposals → {PROPOSALS}")
        return 0

    if args.cmd == "history":
        rows = read_proposals(limit=args.limit)
        if not rows:
            print(f"(no proposals yet — run `propose` first)")
            return 0
        print(f"\n📜 last {len(rows)} proposals:")
        for r in rows:
            applied = "✓" if r.get("applied") else " "
            print(f"  [{applied}] {r['ts']}  ", _fmt_proposal(r).strip())
        return 0

    if args.cmd == "review":
        rows = read_proposals(only_unapplied=True)
        if not rows:
            print("✅ no unapplied proposals — you're caught up")
            return 0
        print(f"\n👀 {len(rows)} UNAPPLIED proposals (review & decide):")
        for r in rows:
            print(_fmt_proposal(r))
        print(f"\n  These are READ-ONLY suggestions. Auto-apply ships in T-future (C6) with safety caps.")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
