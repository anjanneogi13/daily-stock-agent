"""Position sizing + trade plan."""
from typing import Dict

def position_size(account_size: float, risk_pct: float,
                  entry: float, stop_loss: float) -> int:
    risk_dollars = account_size * (risk_pct / 100.0)
    risk_per_share = abs(entry - stop_loss)
    if risk_per_share <= 0:
        return 0
    return int(risk_dollars // risk_per_share)

def trade_plan(sig: dict, config: dict) -> Dict:
    risk_cfg = config["risk"]
    entry = sig.get("close")
    atr = sig.get("atr_14")
    if not (entry and atr):
        return {}
    sl = round(entry - risk_cfg["stop_loss_atr_mult"] * atr, 2)
    tp = round(entry + risk_cfg["take_profit_atr_mult"] * atr, 2)
    qty = position_size(risk_cfg["account_size"],
                        risk_cfg["risk_per_trade_pct"], entry, sl)
    rr = round((tp - entry) / (entry - sl), 2) if entry > sl else 0
    return {
        "entry": round(entry, 2),
        "stop_loss": sl,
        "take_profit": tp,
        "quantity": qty,
        "risk_dollars": round(qty * (entry - sl), 2),
        "reward_dollars": round(qty * (tp - entry), 2),
        "risk_reward": rr,
    }
