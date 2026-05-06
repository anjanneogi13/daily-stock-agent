"""Evaluate all pending picks. Run daily after US market close.

Import-safe: importing this module must not evaluate or mutate tracked data.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pick_evaluator import evaluate_pending
from src.performance_stats import print_dashboard
from src.position_monitor import scan_open_positions
from src.strategy_breakdown import print_all_breakdowns
from src.risk_metrics import compute_risk_metrics, format_risk_text
from src.auto_pause import compute_score as _ap_score, format_summary as _ap_summary
from src.auto_cooldown import scan_and_cool, format_summary as _cd_summary


def main() -> int:
    print("Evaluating pending picks...\n")
    counts = evaluate_pending()
    print(
        f"\n[summary] evaluated={counts['evaluated']} | "
        f"TP={counts['tp_hits']} | SL={counts['sl_hits']} | "
        f"expired={counts['expired']} | open={counts['still_open']}\n"
    )

    print_dashboard()

    # Position monitor: print alerts (Telegram dispatch is separate script)
    print("\n--- POSITION MONITOR ---")
    alerts = scan_open_positions()
    if alerts:
        over = sum(1 for a in alerts if a["severity"] == "over")
        near = sum(1 for a in alerts if a["severity"] == "near")
        print(f"⏰ {len(alerts)} alert(s): {over} OVERDUE, {near} approaching max-hold")
        for a in alerts:
            emoji = "🚨" if a["severity"] == "over" else "⏰"
            print(
                f"  {emoji} {a['ticker']:6s} {a['trade_type']:5s} "
                f"open {a['days_open']}d (max {a['max_hold']}d)"
            )
        print("\nRun: python3 scripts/send_position_alerts.py to dispatch to Telegram")
    else:
        print("✅ All positions within max_hold budget")

    # Strategy/tag/regime breakdown (Pillar 6 P&L Brain - Weekly metrics)
    print()
    print_all_breakdowns()

    # Risk-adjusted metrics (Pillar 6 — Sharpe/Sortino/Max DD/Calmar)
    print()
    print(format_risk_text(compute_risk_metrics()))

    # Auto-pause status (Pillar 5 — Self-Awareness)
    print()
    print(_ap_summary(_ap_score()))

    # Auto-cooldown (Pillar 4): cool tickers with 3+ consecutive losses
    print("\n--- AUTO-COOLDOWN ---")
    try:
        cd_result = scan_and_cool(apply=True)
        print(_cd_summary(cd_result))
    except Exception as ce:
        print(f"⚠ auto_cooldown skipped: {ce}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
