"""Auto-cooldown engine — Pillar 4.

Rule: If a ticker has 3 consecutive LOSSES in the signal journal
(no wins in between), auto-add it to the wisdom kill-list with a
14-day cool-off. Stops the agent from re-picking burning tickers.

Reads:  signal_journal closed picks  (chronological by pick_date)
Writes: data/wisdom/kill_list.json    (via wisdom_base.add_to_kill_list)

Idempotent: Already-killed tickers are skipped.
Observe-mode by default: scan_and_cool() returns dry-run unless apply=True.
"""
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from src.signal_journal import load_closed
from src import wisdom_base


CONSECUTIVE_LOSS_THRESHOLD = 3
DEFAULT_COOL_OFF_DAYS      = 14


def _consecutive_losses_by_ticker(closed: List[Dict]) -> Dict[str, int]:
    """For each ticker, count trailing consecutive losses (most-recent end of journal)."""
    # Group by ticker, sort each list by evaluated_on (or pick_date) ascending
    by_ticker: Dict[str, List[Dict]] = defaultdict(list)
    for r in closed:
        if r.get("outcome") in ("win", "loss"):
            by_ticker[r["ticker"]].append(r)

    result: Dict[str, int] = {}
    for tk, rows in by_ticker.items():
        rows.sort(key=lambda r: (r.get("evaluated_on") or r.get("pick_date") or ""))
        # Count trailing losses
        trailing = 0
        for r in reversed(rows):
            if r["outcome"] == "loss":
                trailing += 1
            else:
                break
        result[tk] = trailing
    return result


def find_candidates(closed: Optional[List[Dict]] = None,
                     threshold: int = CONSECUTIVE_LOSS_THRESHOLD
                     ) -> List[Tuple[str, int]]:
    """Return [(ticker, n_losses), ...] for tickers at or above threshold."""
    closed = closed if closed is not None else load_closed()
    counts = _consecutive_losses_by_ticker(closed)
    return sorted(
        [(tk, n) for tk, n in counts.items() if n >= threshold],
        key=lambda x: -x[1],
    )


def scan_and_cool(apply: bool = False,
                   cool_off_days: int = DEFAULT_COOL_OFF_DAYS,
                   threshold: int = CONSECUTIVE_LOSS_THRESHOLD,
                   ) -> Dict:
    """Scan closed picks; cool off any ticker with >=threshold trailing losses.

    Args:
        apply: If False (default), dry-run only — returns candidates without writing.
        cool_off_days: Days to cool off the ticker.
        threshold: Number of consecutive losses required to trigger.

    Returns:
        {
          'candidates': [(ticker, n_losses), ...],   # all ticker hitting threshold
          'newly_cooled': [ticker, ...],             # actually added (apply=True)
          'already_cooled': [ticker, ...],           # already on kill_list
          'dry_run': bool,
        }
    """
    candidates = find_candidates(threshold=threshold)
    newly_cooled = []
    already_cooled = []

    if apply:
        for tk, n in candidates:
            if wisdom_base.is_killed(tk):
                already_cooled.append(tk)
                continue
            wisdom_base.add_to_kill_list(
                ticker=tk,
                reason=f"auto-cooldown: {n} consecutive losses",
                cool_off_days=cool_off_days,
                source="auto_cooldown",
            )
            # T22: compound the wisdom — write a lesson alongside the kill
            try:
                from datetime import datetime as _dt
                wisdom_base.add_lesson(
                    text=(f"{tk} cooled {cool_off_days}d after {n} consecutive "
                          f"losses (auto-cooldown {_dt.now().date().isoformat()})"),
                    source="auto_cooldown",
                    confidence=0.65,  # observed but not yet validated long-term
                    tags=["cooldown", "auto", tk],
                    author="system",
                )
            except Exception:
                pass  # never block the cooldown action
            newly_cooled.append(tk)
    else:
        # Dry-run still classifies for reporting
        for tk, _ in candidates:
            if wisdom_base.is_killed(tk):
                already_cooled.append(tk)
            else:
                newly_cooled.append(tk)

    return {
        "candidates":     candidates,
        "newly_cooled":   newly_cooled,
        "already_cooled": already_cooled,
        "dry_run":        not apply,
    }


def format_summary(result: Dict) -> str:
    """Telegram-ready summary line."""
    lines = [f"🛑 *Auto-Cooldown* {'(DRY RUN)' if result['dry_run'] else '(APPLIED)'}"]
    if not result["candidates"]:
        lines.append("  ✅ No tickers hit the loss threshold")
        return "\n".join(lines)
    if result["newly_cooled"]:
        verb = "Would cool" if result["dry_run"] else "Cooled"
        # Map ticker → loss count
        cnt = dict(result["candidates"])
        items = [f"{tk} ({cnt.get(tk, '?')}L)" for tk in result["newly_cooled"]]
        lines.append(f"  🥶 {verb}: {', '.join(items)}")
    if result["already_cooled"]:
        lines.append(f"  ♻️ Already cooled: {', '.join(result['already_cooled'])}")
    return "\n".join(lines)
