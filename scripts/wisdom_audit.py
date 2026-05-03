"""Wisdom Audit — inspect what the agent currently believes.

Shows lessons, active empirical patterns, and the kill list in
one printable view. Use for sanity checks and weekly reviews.

Usage:
    python3 scripts/wisdom_audit.py            # full report
    python3 scripts/wisdom_audit.py --json     # machine-readable
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.wisdom_base import (
    load_active_lessons,
    load_active_patterns,
    get_kill_list,
    stats,
)


def _hr(label: str) -> str:
    return f"\n{'═' * 60}\n  {label}\n{'═' * 60}"


def _fmt_pct(x):
    try:
        return f"{float(x):.0%}"
    except Exception:
        return "?"


def render_text() -> str:
    out = []
    s = stats()
    out.append(_hr("WISDOM AUDIT"))
    out.append(f"Generated: {datetime.now().isoformat(timespec='seconds')}")
    out.append(f"Lessons (active): {s.get('active_lessons', 0)}")
    out.append(f"Patterns (active): {s.get('active_patterns', 0)}")
    out.append(f"Kill list (active): {s.get('kill_list_size', 0)}")

    # Lessons
    out.append(_hr(f"📚 LESSONS"))
    lessons = sorted(load_active_lessons(min_confidence=0.0),
                     key=lambda L: -float(L.get("confidence", 0)))
    if not lessons:
        out.append("  (none)")
    for L in lessons:
        conf = float(L.get("confidence", 0))
        emoji = "🟢" if conf >= 0.8 else "🟡" if conf >= 0.6 else "⚪"
        tags = ",".join(L.get("tags", []))
        src = L.get("source", "?")
        out.append(f"  {emoji} [{conf:.2f}] {L.get('text','')[:80]}")
        out.append(f"      ↳ source={src} tags={tags}")

    # Patterns
    out.append(_hr(f"🔬 EMPIRICAL PATTERNS"))
    patterns = sorted(load_active_patterns(),
                      key=lambda p: float(p.get("p_value", 1)))
    if not patterns:
        out.append("  (none)")
    for p in patterns:
        eff = p.get("effect", "?")
        emoji = "📈" if eff == "edge" else "📉" if eff == "drag" else "•"
        out.append(
            f"  {emoji} {eff.upper():5s} {p.get('signal','?')}={p.get('bucket','?')} "
            f"WR={_fmt_pct(p.get('win_rate'))} n={p.get('sample_n','?')} "
            f"p={float(p.get('p_value', 1)):.3f}"
        )

    # Kill list
    out.append(_hr(f"🥶 KILL LIST"))
    kl = get_kill_list()
    if not kl:
        out.append("  (none)")
    now = datetime.now()
    for tk, e in sorted(kl.items()):
        try:
            exp = datetime.fromisoformat(e.get("expires_at", ""))
            days = max(0, (exp.date() - now.date()).days)
        except Exception:
            days = "?"
        out.append(f"  🥶 {tk:6s} cooling {days}d  source={e.get('source','?'):14s} "
                   f"reason={e.get('reason','?')[:50]}")

    out.append("")
    return "\n".join(out)


def render_json() -> str:
    return json.dumps({
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "stats":     stats(),
        "lessons":   load_active_lessons(min_confidence=0.0),
        "patterns":  load_active_patterns(),
        "kill_list": get_kill_list(),
    }, indent=2, default=str)


def main():
    ap = argparse.ArgumentParser(description="Wisdom audit report")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    args = ap.parse_args()
    print(render_json() if args.json else render_text())


if __name__ == "__main__":
    main()
