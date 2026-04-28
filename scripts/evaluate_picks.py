"""Evaluate all pending picks. Run daily after US market close."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pick_evaluator import evaluate_pending
from src.performance_stats import print_dashboard

print("Evaluating pending picks...\n")
counts = evaluate_pending()
print(f"\n[summary] evaluated={counts['evaluated']} | "
      f"TP={counts['tp_hits']} | SL={counts['sl_hits']} | "
      f"expired={counts['expired']} | open={counts['still_open']}\n")

print_dashboard()
