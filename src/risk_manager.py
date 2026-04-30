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


# ─── ATR-based dynamic stops (Week 2) ─────────────────────────────
def atr_trade_plan(price: float, atr: float, capital: float,
                   risk_pct: float = 0.01, atr_mult_sl: float = 2.0,
                   atr_mult_tp: float = 2.5,  # Tier 1: was 4.0 — too far, now hittable trade_type: str = "swing") -> dict:
    """
    Dynamic SL/TP based on ATR (true volatility), not arbitrary %.
    Day trades use tighter ATR multipliers.
    """
    if trade_type == "day":
        atr_mult_sl, atr_mult_tp = 1.0, 1.5  # Tier 1: was 2.0 — too far for intraday
    if not atr or atr <= 0:
        atr = price * 0.02  # fallback: 2% if ATR missing

    sl = round(price - atr * atr_mult_sl, 2)
    tp = round(price + atr * atr_mult_tp, 2)
    risk_per_share = price - sl
    if risk_per_share <= 0:
        return {"entry": price, "stop_loss": sl, "take_profit": tp,
                "risk_reward": 0, "quantity": 0, "trade_type": trade_type}

    risk_capital = capital * risk_pct
    qty = max(1, int(risk_capital / risk_per_share))
    rr = round((tp - price) / risk_per_share, 2)

    return {
        "entry": round(price, 2),
        "stop_loss": sl,
        "take_profit": tp,
        "risk_reward": rr,
        "quantity": qty,
        "atr": round(atr, 2),
        "trade_type": trade_type,
        "stop_method": f"{atr_mult_sl}xATR",
    }
