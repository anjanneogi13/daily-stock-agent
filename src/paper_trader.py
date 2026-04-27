"""Paper-trade logger."""
import os, csv
from datetime import datetime
from typing import Dict

def log_paper_trade(pick: Dict, csv_path: str = "data/trades.csv") -> None:
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    is_new = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(["timestamp","ticker","score","entry","stop_loss",
                        "take_profit","quantity","risk_reward","mode"])
        w.writerow([
            datetime.now().isoformat(timespec="seconds"),
            pick["ticker"],
            pick["scores"]["composite"],
            pick["plan"].get("entry"),
            pick["plan"].get("stop_loss"),
            pick["plan"].get("take_profit"),
            pick["plan"].get("quantity"),
            pick["plan"].get("risk_reward"),
            "paper",
        ])
