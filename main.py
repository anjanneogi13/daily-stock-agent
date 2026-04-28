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
from src.pick_logger import log_picks
from src.market_news import get_market_briefing
from src.earnings_analyzer import analyze_earnings
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



    # ===== Daily Market Briefing =====
    rprint("\n[bold cyan]📰 Daily Market Briefing...[/bold cyan]")
    briefing = get_market_briefing()
    sent = briefing.get("sentiment", "neutral")
    sscore = briefing.get("score", 0.5)
    scolor = "green" if sent == "bullish" else "red" if sent == "bearish" else "yellow"
    panel_text = f"[bold {scolor}]{sent.upper()}[/bold {scolor}] (score: {sscore:.2f})\n"
    panel_text += f"[dim]{briefing.get('summary','')}[/dim]\n"
    if briefing.get("key_catalysts"):
        panel_text += "\n📈 [green]Catalysts:[/green]\n"
        for c2 in briefing["key_catalysts"][:3]:
            panel_text += f"  • {c2}\n"
    if briefing.get("key_risks"):
        panel_text += "\n⚠ [red]Risks:[/red]\n"
        for rk in briefing["key_risks"][:3]:
            panel_text += f"  • {rk}\n"
    rprint(Panel.fit(panel_text.rstrip(), title="Market Sentiment"))

    # Apply sentiment modifier to min_score
    if sent == "bearish":
        cfg["output"]["min_score"] = max(cfg["output"]["min_score"], 0.72)
        rprint("[yellow]⚠ Bearish news sentiment — tightening min_score to 0.72[/yellow]")
    elif sent == "bullish" and sscore >= 0.65:
        rprint("[green]✓ Bullish news sentiment — keeping standard filters[/green]")

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


    # ===== Earnings Quality Analysis on filtered picks =====
    rprint("[5b/6] Analyzing earnings quality (beats, surprises, analyst trends)...")
    for p in filtered:
        try:
            ea = analyze_earnings(p["ticker"])
            p["earnings"] = ea
            # Blend earnings_quality into composite (12% weight)
            eq = ea.get("earnings_quality", 0.5)
            old_score = p["scores"]["composite"]
            new_score = round(old_score * 0.88 + eq * 0.12, 3)
            p["scores"]["composite_pre_earnings"] = old_score
            p["scores"]["composite"] = new_score
        except Exception as e:
            rprint(f"  [dim]earnings err for {p['ticker']}: {e}[/dim]")
            p["earnings"] = {}
    # Re-sort by new composite
    filtered.sort(key=lambda x: x["scores"]["composite"], reverse=True)

    top = filtered
    rprint(f"\n[6/6] {len(candidates)} candidates -> {len(top)} after earnings filter\n")

    table = Table(title="Top Picks (SEMI=Semiconductor, AI=AI-relevant)")
    for col in ["#","Ticker","Tag","Score","EQ","Beat%","AnaBuy%","Entry","SL","TP","R:R","Qty","Earn"]:
        table.add_column(col)
    for i, p in enumerate(top, 1):
        plan = p["plan"]; s = p["scores"]; ea = p.get("earnings", {})
        e = f"{p.get('days_to_earnings','?')}d" if p.get("days_to_earnings") else "—"
        eq = f"{ea.get('earnings_quality',0):.2f}" if ea.get("earnings_quality") is not None else "—"
        br = f"{int(ea['beat_rate']*100)}%" if ea.get("beat_rate") is not None else "—"
        ab = f"{ea['analyst_buy_pct']:.0f}%" if ea.get("analyst_buy_pct") is not None else "—"
        table.add_row(str(i), p["ticker"], s.get("sector_tag") or "",
                      f"{s['composite']:.2f}", eq, br, ab,
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

    # ===== Log picks for performance tracking =====
    try:
        picks_for_log = []
        for p in top:
            picks_for_log.append({
                "ticker": p["ticker"],
                "company": p.get("info_short", {}).get("name", ""),
                "tag": p["scores"].get("sector_tag") or "",
                "score": p["scores"].get("composite", 0),
                "multiplier": p["scores"].get("sector_mult", 1.0),
                "entry": p["plan"].get("entry"),
                "stop_loss": p["plan"].get("stop_loss"),
                "take_profit": p["plan"].get("take_profit"),
                "risk_reward": p["plan"].get("risk_reward", 2.0),
                "qty": p["plan"].get("quantity", 0),
                "days_to_earnings": p.get("days_to_earnings"),
            })
        n = log_picks(picks_for_log, reg, cape if 'cape' in dir() else None)
        rprint(f"[dim][log] Saved {n} picks to data/picks_log.csv[/dim]")
    except Exception as e:
        rprint(f"[red][log] Could not save picks: {e}[/red]")

    rprint("[green]Done. Review picks before any real-money action.[/green]")


if __name__ == "__main__":
    run()
