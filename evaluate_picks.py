"""Evaluate past picks vs actual price action.
Run weekly to see if your agent's picks actually worked."""
import pandas as pd
from datetime import datetime, timedelta
from rich import print as rprint
from rich.table import Table
from src.data_fetcher import fetch_ohlcv


def evaluate(csv_path: str = "data/trades.csv", lookback_days: int = 30):
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        rprint("[red]No trades.csv yet. Run the agent first.[/red]")
        return

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    cutoff = datetime.now() - timedelta(days=lookback_days)
    df = df[df["timestamp"] >= cutoff]

    if df.empty:
        rprint("[yellow]No picks in the lookback window.[/yellow]")
        return

    results = []
    for _, row in df.iterrows():
        tk = row["ticker"]
        entry = float(row["entry"])
        sl = float(row["stop_loss"])
        tp = float(row["take_profit"])
        pick_date = row["timestamp"].date()
        # Get price action since pick date
        hist = fetch_ohlcv(tk, period="3mo")
        if hist.empty:
            continue
        hist = hist[hist.index.date >= pick_date]
        if hist.empty:
            continue
        max_high = hist["high"].max()
        min_low = hist["low"].min()
        last_close = hist["close"].iloc[-1]
        # Did TP or SL hit first?
        outcome = "OPEN"
        for _, bar in hist.iterrows():
            if bar["low"] <= sl:
                outcome = "SL HIT"; break
            if bar["high"] >= tp:
                outcome = "TP HIT"; break
        pnl_pct = (last_close / entry - 1) * 100
        results.append({
            "ticker": tk, "date": pick_date, "score": row["score"],
            "entry": entry, "last": round(last_close, 2),
            "max": round(max_high, 2), "min": round(min_low, 2),
            "pnl_pct": round(pnl_pct, 2), "outcome": outcome,
        })

    if not results:
        rprint("[yellow]No evaluable picks.[/yellow]"); return

    rdf = pd.DataFrame(results)
    table = Table(title=f"Pick Evaluation (last {lookback_days} days)")
    for c in ["Ticker","Date","Score","Entry","Last","P/L %","Outcome"]:
        table.add_column(c)
    for _, r in rdf.iterrows():
        color = "green" if r["pnl_pct"] > 0 else "red"
        table.add_row(r["ticker"], str(r["date"]), f"{r['score']:.2f}",
                      f"${r['entry']}", f"${r['last']}",
                      f"[{color}]{r['pnl_pct']:+.2f}%[/{color}]", r["outcome"])
    rprint(table)

    # Summary
    win = (rdf["pnl_pct"] > 0).sum()
    total = len(rdf)
    avg = rdf["pnl_pct"].mean()
    rprint(f"\n[bold]Summary:[/bold] {win}/{total} winners ({win/total*100:.1f}%), "
           f"avg P/L: [{'green' if avg > 0 else 'red'}]{avg:+.2f}%[/]")
    tp_hits = (rdf["outcome"] == "TP HIT").sum()
    sl_hits = (rdf["outcome"] == "SL HIT").sum()
    rprint(f"TP hits: {tp_hits} | SL hits: {sl_hits} | Open: {total - tp_hits - sl_hits}")


if __name__ == "__main__":
    evaluate(lookback_days=30)
