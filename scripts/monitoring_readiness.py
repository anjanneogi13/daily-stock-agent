"""Monitoring readiness dashboard.

Bug #21 / Product gate (2026-05-05)

Paper trading is forbidden until monitoring-only performance clears
post-floor gates by trade type:

  - day trades >60% win rate plus positive expectancy
  - swing trades >66% win rate plus positive expectancy
  - monster / long holder picks >90% win rate plus positive expectancy

This script is intentionally conservative:
  - post-floor rows only by default
  - closed outcomes only
  - win rate alone is not enough; avg R must be > 0
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
PICKS_LOG = ROOT / "data" / "picks_log.csv"

DATA_QUALITY_FLOOR = "2026-05-02"

CLOSED_STATUSES = {
    "tp_hit",
    "sl_hit",
    "expired",
    "day_close",
}

THRESHOLDS = {
    "day": 0.60,
    "swing": 0.66,
    "monster": 0.90,
}

DEFAULT_MIN_N = 30


def _to_float(value, default=None):
    try:
        if value in (None, "", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _is_true(value) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _is_closed(row: dict) -> bool:
    return (row.get("evaluation_status") or "").strip() in CLOSED_STATUSES


def _is_win(row: dict) -> bool:
    return (row.get("evaluation_status") or "").strip() == "tp_hit"


def classify_bucket(row: dict) -> str:
    """Classify row into day / swing / monster.

    Monster overrides trade_type because it represents a separate founder
    thesis: rare high-conviction long-holder candidates.
    """
    monster_score = _to_float(row.get("monster_score"), 0.0) or 0.0
    if _is_true(row.get("is_monster")) or monster_score >= 0.90:
        return "monster"

    trade_type = (row.get("trade_type") or "").strip().lower()
    if trade_type == "day":
        return "day"
    return "swing"


def evaluate_bucket(bucket: str, rows: Iterable[dict], threshold: float, min_n: int = DEFAULT_MIN_N) -> dict:
    closed = [r for r in rows if _is_closed(r)]
    n = len(closed)
    wins = sum(1 for r in closed if _is_win(r))

    r_values = [
        _to_float(r.get("r_multiple"))
        for r in closed
        if _to_float(r.get("r_multiple")) is not None
    ]

    win_rate = (wins / n) if n else None
    avg_r = (sum(r_values) / len(r_values)) if r_values else None
    positive_expectancy = avg_r is not None and avg_r > 0

    blockers = []
    if n < min_n:
        blockers.append(f"n_closed={n} < {min_n}")
    if win_rate is None:
        blockers.append("no closed trades")
    elif win_rate <= threshold:
        blockers.append(f"win_rate={win_rate:.1%} <= target {threshold:.0%}")
    if avg_r is None:
        blockers.append("avg_r unavailable")
    elif avg_r <= 0:
        blockers.append(f"avg_r={avg_r:+.2f} <= 0")

    return {
        "bucket": bucket,
        "threshold": threshold,
        "min_n": min_n,
        "n_closed": n,
        "wins": wins,
        "losses": n - wins,
        "win_rate": round(win_rate, 4) if win_rate is not None else None,
        "avg_r": round(avg_r, 4) if avg_r is not None else None,
        "positive_expectancy": positive_expectancy,
        "ready": not blockers,
        "blockers": blockers,
    }


def load_rows(path: Path = PICKS_LOG) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def run_all(rows: list[dict] | None = None, floor: str = DATA_QUALITY_FLOOR, min_n: int = DEFAULT_MIN_N) -> list[dict]:
    if rows is None:
        rows = load_rows()

    post_floor = [
        r for r in rows
        if (r.get("pick_date") or "") >= floor
    ]

    buckets = defaultdict(list)
    for row in post_floor:
        buckets[classify_bucket(row)].append(row)

    return [
        evaluate_bucket("day", buckets.get("day", []), THRESHOLDS["day"], min_n=min_n),
        evaluate_bucket("swing", buckets.get("swing", []), THRESHOLDS["swing"], min_n=min_n),
        evaluate_bucket("monster", buckets.get("monster", []), THRESHOLDS["monster"], min_n=min_n),
    ]


def format_report(results: list[dict], floor: str = DATA_QUALITY_FLOOR) -> str:
    lines = []
    lines.append("═" * 72)
    lines.append("📡 MONITORING READINESS DASHBOARD")
    lines.append("   Paper trading remains forbidden until all gates pass.")
    lines.append(f"   Data floor: {floor}")
    lines.append("═" * 72)

    for r in results:
        icon = "✅" if r["ready"] else "⏳" if r["n_closed"] == 0 else "🟡"
        wr = "n/a" if r["win_rate"] is None else f"{r['win_rate']:.1%}"
        ar = "n/a" if r["avg_r"] is None else f"{r['avg_r']:+.2f}R"
        lines.append("")
        lines.append(
            f"{icon} {r['bucket'].upper():8s} "
            f"n={r['n_closed']}/{r['min_n']} "
            f"wins={r['wins']} losses={r['losses']} "
            f"win_rate={wr} target>{r['threshold']:.0%} "
            f"avg_R={ar}"
        )
        if r["ready"]:
            lines.append("   READY for paper-trading eligibility gate.")
        else:
            for b in r["blockers"]:
                lines.append(f"   ✗ {b}")

    lines.append("")
    lines.append("Rule: win rate alone is not enough; average R / expectancy must be positive.")
    lines.append("═" * 72)
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--floor", default=DATA_QUALITY_FLOOR, help="Minimum pick_date to include")
    parser.add_argument("--min-n", type=int, default=DEFAULT_MIN_N, help="Minimum closed trades per bucket")
    args = parser.parse_args(argv)

    results = run_all(floor=args.floor, min_n=args.min_n)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_report(results, floor=args.floor))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
