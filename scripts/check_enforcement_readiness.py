"""F5 (May 4 2026): Score each OBSERVE-mode gate against data-driven readiness.

THE PROBLEM
3 gates ship in OBSERVE-mode (default false):
  - BRAIN_ENFORCE_EV   (main.py:361)
  - AUTO_PAUSE_ENABLED (main.py:395)
  - SMELL_ENFORCE      (main.py:436)

Plan was "flip them on Wednesday" — gut-feel calendar, not data.
This script makes the flip DATA-DRIVEN. When all conditions for a
gate go green, output says "READY — flip env var to true".

THRESHOLDS (intentionally conservative)
- SMELL_ENFORCE       n>=30 picks-with-smell  AND  smell-FP-rate < 20%
- BRAIN_ENFORCE_EV    n>=30 post-floor closed AND  EV-vs-outcome correlation > 0
- AUTO_PAUSE_ENABLED  n>=50 post-floor closed AND  any group WR < 30%

These can be tightened later. Default is "be very sure before
silently dropping picks."

USAGE
  python scripts/check_enforcement_readiness.py
  python scripts/check_enforcement_readiness.py --json   # machine-readable
"""
from __future__ import annotations
import csv
import json
import sys
from datetime import date
from pathlib import Path

# ── Project paths ───────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
PICKS = ROOT / "data/picks_log.csv"

sys.path.insert(0, str(ROOT))
try:
    from src.data_quality import filter_to_quality
except ImportError:
    def filter_to_quality(rows): return rows  # graceful


# ── Helpers ─────────────────────────────────────────────────────
def _load_picks() -> list[dict]:
    if not PICKS.exists():
        return []
    return list(csv.DictReader(PICKS.open()))


def _to_float(v, default=None):
    try:
        return float(v) if v not in (None, "", "None") else default
    except (ValueError, TypeError):
        return default


def _is_closed(r: dict) -> bool:
    return (r.get("evaluation_status") or "") in ("tp_hit", "sl_hit", "expired")


# ── Per-gate readiness checks ──────────────────────────────────
def check_smell_enforce(rows: list[dict]) -> dict:
    """SMELL_ENFORCE ready when we\'ve seen enough smells AND they\'re accurate."""
    closed = [r for r in filter_to_quality(rows) if _is_closed(r)]
    # No smell field exists in picks_log — gate uses log-only data today.
    # Stub: treat as not-ready until smell outcomes are persisted.
    return {
        "gate": "SMELL_ENFORCE",
        "env_var": "SMELL_ENFORCE",
        "ready": False,
        "n_observed": 0,
        "threshold_n": 30,
        "reason": (
            "smell verdicts are not persisted to picks_log yet — "
            "wire smell_blockers field first (separate epic)"
        ),
        "blockers": ["smell_verdicts_not_persisted"],
    }


def check_brain_enforce_ev(rows: list[dict]) -> dict:
    """BRAIN_ENFORCE_EV ready when post-floor closed n>=30 AND EV predicts outcome."""
    closed = [r for r in filter_to_quality(rows) if _is_closed(r)]
    n = len(closed)
    blockers = []
    if n < 30:
        blockers.append(f"n={n} < 30 closed post-floor picks")

    # Correlation between brain_ev_pct and r_multiple (when both present)
    pairs = []
    for r in closed:
        ev = _to_float(r.get("brain_ev_pct"))
        rm = _to_float(r.get("r_multiple"))
        if ev is not None and rm is not None:
            pairs.append((ev, rm))
    correlation = None
    if len(pairs) >= 5:
        try:
            import statistics
            xs = [p[0] for p in pairs]
            ys = [p[1] for p in pairs]
            mx, my = statistics.mean(xs), statistics.mean(ys)
            num = sum((x - mx) * (y - my) for x, y in pairs)
            den_x = sum((x - mx) ** 2 for x in xs) ** 0.5
            den_y = sum((y - my) ** 2 for y in ys) ** 0.5
            if den_x > 0 and den_y > 0:
                correlation = num / (den_x * den_y)
        except Exception:
            pass
    if correlation is None:
        blockers.append("not enough EV-tagged closed picks to compute correlation")
    elif correlation <= 0:
        blockers.append(f"EV-vs-outcome correlation = {correlation:+.2f} (must be > 0)")

    return {
        "gate": "BRAIN_ENFORCE_EV",
        "env_var": "BRAIN_ENFORCE_EV",
        "ready": not blockers,
        "n_observed": n,
        "threshold_n": 30,
        "ev_correlation": correlation,
        "blockers": blockers,
    }


def check_auto_pause(rows: list[dict]) -> dict:
    """AUTO_PAUSE_ENABLED ready when n>=50 post-floor AND a real bad-group exists."""
    closed = [r for r in filter_to_quality(rows) if _is_closed(r)]
    n = len(closed)
    blockers = []
    if n < 50:
        blockers.append(f"n={n} < 50 closed post-floor picks (need volume for group stats)")

    # Group by tag (sector proxy); compute WR per group
    from collections import defaultdict
    by_tag = defaultdict(list)
    for r in closed:
        by_tag[r.get("tag", "none")].append(r)
    bad_groups = []
    for tag, items in by_tag.items():
        if len(items) < 5:  # need min sample
            continue
        wins = sum(1 for r in items if (r.get("evaluation_status") == "tp_hit"))
        wr = wins / len(items)
        if wr < 0.30:
            bad_groups.append({"tag": tag, "n": len(items), "wr": wr})

    if not bad_groups and n >= 50:
        blockers.append("no group has WR<30% with n>=5 — nothing for auto-pause to act on")

    return {
        "gate": "AUTO_PAUSE_ENABLED",
        "env_var": "AUTO_PAUSE_ENABLED",
        "ready": not blockers,
        "n_observed": n,
        "threshold_n": 50,
        "bad_groups": bad_groups,
        "blockers": blockers,
    }


# ── Orchestration ──────────────────────────────────────────────
def run_all() -> list[dict]:
    rows = _load_picks()
    return [
        check_smell_enforce(rows),
        check_brain_enforce_ev(rows),
        check_auto_pause(rows),
    ]


def format_report(results: list[dict]) -> str:
    lines = []
    lines.append("═" * 64)
    lines.append("🚦 ENFORCEMENT READINESS DASHBOARD")
    lines.append("   (auto-flip OBSERVE → ENFORCE when data backs the gate)")
    lines.append("═" * 64)
    for r in results:
        icon = "✅" if r["ready"] else "🟡" if r["n_observed"] > 0 else "⏳"
        lines.append("")
        lines.append(f"{icon}  {r['gate']:22}  n={r['n_observed']}/{r['threshold_n']}")
        if r["ready"]:
            lines.append(f"     READY — set {r['env_var']}=true in workflow env")
        else:
            for b in r["blockers"]:
                lines.append(f"     ✗ {b}")
    lines.append("")
    lines.append("═" * 64)
    lines.append("Re-run: python scripts/check_enforcement_readiness.py")
    return "\n".join(lines)


def main(argv=None):
    argv = argv or sys.argv[1:]
    results = run_all()
    if "--json" in argv:
        print(json.dumps(results, indent=2, default=str))
    else:
        print(format_report(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())
