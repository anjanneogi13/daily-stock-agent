"""Daily Stock Picker — CLI entrypoint."""
import os, yaml
from dotenv import load_dotenv
from rich import print as rprint
from rich.table import Table

from src.universe import get_universe
from src.data_fetcher import fetch_universe_data, fetch_info
from src.indicators import add_indicators, latest_signals
from src.fundamentals import score_fundamentals, passes_filters
from src.news_sentiment import fetch_news, score_sentiment
from src.scorer import composite_score
from src.risk_manager import trade_plan
from src.llm_agent import explain_pick
from src.paper_trader import log_paper_trade

def load_config(path: str = "config.yaml") -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def run():
    load_dotenv()
    cfg = load_config()
    rprint("[bold cyan]Daily Stock Picker Agent[/bold cyan]")
    rprint("[dim]Not financial advice. Paper-trade only.[/dim]\n")

    rprint("[1/5] Loading universe...")
    tickers = get_universe(cfg)

    rprint("[2/5] Fetching market data...")
    data = fetch_universe_data(tickers, period=f"{cfg['strategy']['lookback_days']}d")

    rprint("[3/5] Computing indicators + scoring...")
    candidates = []
    for tk, df in data.items():
        d = add_indicators(df)
        sig = latest_signals(d)
        if not sig.get("close"):
            continue
        info = fetch_info(tk)
        if not passes_filters(info, cfg):
            continue
        fund = score_fundamentals(info)
        news = fetch_news(tk, limit=5)
        sent = score_sentiment(news)
        scores = composite_score(sig, fund, sent, cfg["weights"],
                                 ticker=tk, sector_cfg=cfg.get("sector", {}))
        if scores["composite"] < cfg["output"]["min_score"]:
            continue
        plan = trade_plan(sig, cfg)
        candidates.append({
            "ticker": tk, "scores": scores, "plan": plan, "news": news,
            "info_short": {"name": info.get("shortName", tk),
                           "sector": info.get("sector", "N/A")},
        })

    candidates.sort(key=lambda x: x["scores"]["composite"], reverse=True)
    top = candidates[: cfg["output"]["top_n_picks"]]
    rprint(f"[4/5] {len(candidates)} candidates -> top {len(top)}\n")

    table = Table(title="Top Picks (SEMI=Semiconductor, AI=AI-relevant)")
    for col in ["#","Ticker","Tag","Score","Raw","Mult","Entry","SL","TP","R:R","Qty"]:
        table.add_column(col)
    for i, p in enumerate(top, 1):
        plan = p["plan"]; s = p["scores"]
        table.add_row(str(i), p["ticker"], s.get("sector_tag") or "",
                      f"{s['composite']:.2f}", f"{s['raw_score']:.2f}",
                      f"x{s['sector_mult']}",
                      f"${plan.get('entry','-')}", f"${plan.get('stop_loss','-')}",
                      f"${plan.get('take_profit','-')}",
                      f"{plan.get('risk_reward','-')}", str(plan.get("quantity","-")))
    rprint(table)

    rprint("\n[5/5] Generating rationales + logging...\n")
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
