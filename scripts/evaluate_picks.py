"""Evaluate all pending picks. Run daily after US market close."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pick_evaluator import evaluate_pending
from src.performance_stats import print_dashboard
from src.position_monitor import scan_open_positions, format_telegram_summary

print("Evaluating pending picks...\n")
counts = evaluate_pending()
print(f"\n[summary] evaluated={counts['evaluated']} | "
      f"TP={counts['tp_hits']} | SL={counts['sl_hits']} | "
      f"expired={counts['expired']} | open={counts['still_open']}\n")

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
        print(f"  {emoji} {a['ticker']:6s} {a['trade_type']:5s} "
              f"open {a['days_open']}d (max {a['max_hold']}d)")
    print("\nRun: python3 scripts/send_position_alerts.py to dispatch to Telegram")
else:
    print("✅ All positions within max_hold budget")
