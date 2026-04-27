"""Backtest top picks on historical data."""
import yaml
from rich import print as rprint
from rich.table import Table
from src.universe import get_universe
from src.data_fetcher import fetch_universe_data
from src.backtester import backtest_simple


def main():
    with open("config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    rprint("[bold cyan]Backtest — RSI Mean-Reversion[/bold cyan]\n")
    tickers = get_universe(cfg)[:50]  # cap at 50 for speed
    data = fetch_universe_data(tickers, period="2y")

    results = []
    for tk, df in data.items():
        r = backtest_simple(df, rsi_buy=35, rsi_sell=70)
        if r:
            r["ticker"] = tk
            results.append(r)

    results.sort(key=lambda x: x["sharpe"], reverse=True)
    top20 = results[:20]

    table = Table(title="Backtest Results (Top 20 by Sharpe)")
    for col in ["#", "Ticker", "Total %", "Win %", "Sharpe", "MaxDD %", "Trades"]:
        table.add_column(col)
    for i, r in enumerate(top20, 1):
        table.add_row(str(i), r["ticker"],
                      f"{r['total_return_pct']}",
                      f"{r['win_rate_pct']}",
                      f"{r['sharpe']}",
                      f"{r['max_drawdown_pct']}",
                      str(r["trades"]))
    rprint(table)


if __name__ == "__main__":
    main()
