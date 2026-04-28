"""Daily Stock Picker — CLI entrypoint with regime + earnings filters."""
import os, yaml
from dotenv import load_dotenv
from rich import print as rprint
from rich.table import Table
from rich.panel import Panel

from src.universe import get_universe
from src.data_fetcher import fetch_universe_data, fetch_info
from src.indicators import add_indicators, latest_signals
from src.fundamentals import score_fundamentals
from src.cape_ratio import get_cape
from src.fundamentals import passes_filters
from src.news_sentiment import fetch_news, score_sentiment
from src.scorer import composite_score
from src.risk_manager import trade_plan
from src.llm_agent import explain_pick
from src.paper_trader import log_paper_trade
from src.regime import market_regime
from src.earnings import days_to_earnings


def load_config(path: str = "config.yaml") -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def run():
    load_dotenv()
    cfg = load_config()
    rprint("[bold cyan]Daily Stock Picker Agent[/bold cyan]")
    rprint("[dim]Not financial advice. Paper-trade only.[/dim]\n")

    rprint("[1/6] Checking market regime...")
    reg = market_regime()
    color = "green" if reg["bullish"] else "red"
    rprint(Panel.fit(
        f"SPY: ${reg['spy_close']} | 200 SMA: ${reg['spy_sma200']} | "
        f"Distance: {reg.get('distance_pct',0):+.2f}%\n"
        f"Regime: [bold {color}]{reg['regime'].upper()}[/bold {color}]",
        title="Market Regime"))
    if not reg["bullish"]:
        rprint("[yellow]⚠ Bearish regime — being more selective. Min score raised.[/yellow]")
        cfg["output"]["min_score"] = max(cfg["output"]["min_score"], 0.70)

    cape = get_cape()


    if cape.get("cape"):


        rprint(f"[CAPE] S&P 500 Shiller CAPE: {cape['cape']:.2f} — {cape['verdict']} ({cape['percentile']})")


    rprint("[2/6] Loading universe...")
    tickers = get_universe(cfg)

    rprint("[3/6] Fetching market data...")
    data = fetch_universe_data(tickers, period=f"{cfg['strategy']['lookback_days']}d")

    rprint("[4/6] Computing indicators + scoring (parallel, all candidates)...")
    from src.parallel_scorer import score_all
    candidates = score_all(data, cfg, max_workers=10)

    rprint("[5/6] Filtering for earnings risk (skip if earnings in next 5 days)...")
    filtered = []
    for p in candidates[: cfg["output"]["top_n_picks"] * 3]:
        d2e = days_to_earnings(p["ticker"])
        p["days_to_earnings"] = d2e if d2e < 999 else None
        if d2e < 5:
            rprint(f"  [dim]Skipping {p['ticker']} — earnings in {d2e}d[/dim]")
            continue
        filtered.append(p)
        if len(filtered) >= cfg["output"]["top_n_picks"]:
            break

    top = filtered
    rprint(f"\n[6/6] {len(candidates)} candidates -> {len(top)} after earnings filter\n")

    table = Table(title="Top Picks (SEMI=Semiconductor, AI=AI-relevant)")
    for col in ["#","Ticker","Tag","Score","Mult","Entry","SL","TP","R:R","Qty","Earn"]:
        table.add_column(col)
    for i, p in enumerate(top, 1):
        plan = p["plan"]; s = p["scores"]
        e = f"{p.get('days_to_earnings','?')}d" if p.get("days_to_earnings") else "—"
        table.add_row(str(i), p["ticker"], s.get("sector_tag") or "",
                      f"{s['composite']:.2f}", f"x{s['sector_mult']}",
                      f"${plan.get('entry','-')}", f"${plan.get('stop_loss','-')}",
                      f"${plan.get('take_profit','-')}",
                      f"{plan.get('risk_reward','-')}", str(plan.get("quantity","-")),
                      e)
    rprint(table)

    rprint("\n[bold]Rationales:[/bold]\n")
    for p in top:
        rationale = explain_pick(p["ticker"], p["scores"], p["plan"], p["news"],
                                 model=cfg["llm"]["model"])
        rprint(f"[bold yellow]{p['ticker']}[/bold yellow] - {p['info_short']['name']}")
        rprint(rationale); rprint("")
        if os.getenv("TRADING_MODE", "paper") == "paper":
            log_paper_trade(p, cfg["output"]["csv_path"].replace("picks","trades"))

    rprint("[green]Done. Review picks before any real-money action.[/green]")


if __name__ == "__main__":
    run()
