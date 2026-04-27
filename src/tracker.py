"""Performance tracker."""
import pandas as pd, os

def performance_summary(csv_path: str = "data/trades.csv") -> dict:
    if not os.path.exists(csv_path):
        return {"trades": 0, "note": "No trades logged yet."}
    df = pd.read_csv(csv_path)
    return {
        "total_picks": len(df),
        "avg_score": round(df["score"].mean(), 3),
        "avg_risk_reward": round(df["risk_reward"].mean(), 2),
        "tickers_traded": df["ticker"].nunique(),
        "first_pick": df["timestamp"].min(),
        "last_pick": df["timestamp"].max(),
        "note": "Win-rate requires manual outcome tracking.",
    }
