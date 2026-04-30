"""Daily Stock Picker — CLI entrypoint with regime + earnings filters + Week 3 wiring."""
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
from src.market_guard import vix_level, spy_trend, sector_strength, classify_trade_type
from src.premarket_filter import gap_check
from src.scorer import apply_sector_cap
from src.risk_manager import atr_trade_plan
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
    rprint("[dim]Not financial advice. Educational only.[/dim]\n")

    # ═══════════════════════════════════════════════════════════════
    # WEEK 2 GUARDS: VIX + SPY trend + Sector strength
    # ═══════════════════════════════════════════════════════════════
    rprint("[bold cyan]🛡️  Market Guards[/bold cyan]")
    vix = vix_level()
    spy = spy_trend()
    sectors = sector_strength()
    weak_sectors = {s: 2 for s, v in sectors.items() if v.get("weak")}

    rprint(f"  VIX={vix:.1f}  SPY>50DMA={spy['above_50dma']}  SPY>200DMA={spy['above_200dma']}")
    if weak_sectors:
        rprint(f"  [yellow]⚠ Weak sectors today (will cap at 2): {list(weak_sectors.keys())}[/yellow]")

    # Adjust pick count based on guards
    base_picks = cfg["output"]["top_n_picks"]
    adjusted_picks = base_picks
    if vix > 30:
        rprint(f"  [red]🚨 VIX={vix:.1f} > 30 — high volatility, reducing picks 50%[/red]")
        adjusted_picks = max(3, base_picks // 2)
    if not spy["above_50dma"]:
        rprint(f"  [red]🚨 SPY below 50DMA — defensive mode, reducing picks 50%[/red]")
        adjusted_picks = min(adjusted_picks, max(3, base_picks // 2))
    if adjusted_picks != base_picks:
        cfg["output"]["top_n_picks"] = adjusted_picks
        rprint(f"  [yellow]Pick count: {base_picks} → {adjusted_picks}[/yellow]")

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
    for p in candidates[: cfg["output"]["top_n_picks"] * 4]:  # 4x buffer for sector cap
        d2e = days_to_earnings(p["ticker"])
        p["days_to_earnings"] = d2e if d2e < 999 else None
        if d2e < 5:
            rprint(f"  [dim]Skipping {p['ticker']} — earnings in {d2e}d[/dim]")
            continue
        if d2e >= 999:
            rprint(f"  [dim yellow]⚠ {p['ticker']} earnings date unknown — included with caution[/dim yellow]")
        filtered.append(p)
        if len(filtered) >= cfg["output"]["top_n_picks"] * 3:
            break

    # ===== Earnings Quality Analysis =====
    rprint("[5b/6] Analyzing earnings quality (beats, surprises, analyst trends)...")
    for p in filtered:
        try:
            ea = analyze_earnings(p["ticker"])
            p["earnings"] = ea
            eq = ea.get("earnings_quality", 0.5)
            old_score = p["scores"]["composite"]
            new_score = round(old_score * 0.88 + eq * 0.12, 3)
            p["scores"]["composite_pre_earnings"] = old_score
            p["scores"]["composite"] = new_score
        except Exception as e:
            rprint(f"  [dim]earnings err for {p['ticker']}: {e}[/dim]")
            p["earnings"] = {}
    filtered.sort(key=lambda x: x["scores"]["composite"], reverse=True)

    # ═══════════════════════════════════════════════════════════════
    # WEEK 3: Sector concentration cap (with weak-sector tightening)
    # ═══════════════════════════════════════════════════════════════
    rprint("[5c/6] Applying sector concentration cap...")
    pre_cap = len(filtered)
    # Pad info_short.sector if missing (for cap to work)
    for p in filtered:
        if "info_short" not in p:
            p["info_short"] = {}
        if not p["info_short"].get("sector"):
            p["info_short"]["sector"] = p["scores"].get("sector_tag") or "Unknown"
    capped = apply_sector_cap(filtered, max_per_sector=2, reduced_sectors=weak_sectors)
    # Tier 1 fix: hard cap 2 per primary tag (SEMI, AI, etc.) — catches what yfinance sector misses
    from src.scorer import apply_tag_cap
    pre = len(capped)
    capped = apply_tag_cap(capped, max_per_tag=2)
    if len(capped) < pre:
        print(f'[tag_cap] {pre} → {len(capped)} after tag cap (max 2 per primary tag)')
    rprint(f"  [dim]Sector cap: {pre_cap} → {len(capped)} (max 4/sector, weak={list(weak_sectors.keys()) or 'none'})[/dim]")

    # Trim to final pick count
    top = capped[: cfg["output"]["top_n_picks"]]

    # ═══════════════════════════════════════════════════════════════
    # WEEK 3: Auto-tag DAY vs SWING
    # ═══════════════════════════════════════════════════════════════
    rprint("[5d/6] Auto-tagging trade type (DAY vs SWING)...")
    for p in top:
        ttype = classify_trade_type(p["scores"])
        p["trade_type"] = ttype
        # Also stamp into plan for downstream LLM prompt
        if "plan" in p and isinstance(p["plan"], dict):
            p["plan"]["trade_type"] = ttype
    day_n = sum(1 for p in top if p["trade_type"] == "day")
    swing_n = sum(1 for p in top if p["trade_type"] == "swing")
    rprint(f"  [dim]Tagged: 🔥 {day_n} DAY · ⚡ {swing_n} SWING[/dim]")

    rprint(f"\n[6/6] {len(candidates)} candidates -> {len(top)} final picks\n")

    table = Table(title="Top Picks")
    for col in ["#","Type","Ticker","Sector","Score","EQ","Beat%","Entry","SL","TP","R:R","Qty","Earn"]:
        table.add_column(col)
    for i, p in enumerate(top, 1):
        plan = p["plan"]; s = p["scores"]; ea = p.get("earnings", {})
        e = f"{p.get('days_to_earnings','?')}d" if p.get("days_to_earnings") else "—"
        eq = f"{ea.get('earnings_quality',0):.2f}" if ea.get("earnings_quality") is not None else "—"
        br = f"{int(ea['beat_rate']*100)}%" if ea.get("beat_rate") is not None else "—"
        type_emoji = "🔥 DAY" if p["trade_type"] == "day" else "⚡ SWG"
        table.add_row(str(i), type_emoji, p["ticker"],
                      p.get("info_short", {}).get("sector", "—")[:12],
                      f"{s['composite']:.2f}", eq, br,
                      f"${plan.get('entry','-')}", f"${plan.get('stop_loss','-')}",
                      f"${plan.get('take_profit','-')}",
                      f"{plan.get('risk_reward','-')}", str(plan.get("quantity","-")),
                      e)
    rprint(table)

    rprint("\n[bold]Rationales:[/bold]\n")
    for p in top:
        rationale = explain_pick(p["ticker"], p["scores"], p["plan"], p["news"],
                                 model=cfg["llm"]["model"])
        emoji = "🔥" if p["trade_type"] == "day" else "⚡"
        rprint(f"[bold yellow]{emoji} {p['ticker']}[/bold yellow] - {p['info_short'].get('name','')} ({p['trade_type'].upper()})")
        rprint(rationale); rprint("")
        if os.getenv("TRADING_MODE", "paper") == "paper":
            log_paper_trade(p, cfg["output"]["csv_path"].replace("picks","trades"))

    # ===== Log picks (now includes trade_type) =====
    try:
        picks_for_log = []
        for p in top:
            picks_for_log.append({
                "ticker": p["ticker"],
                "company": p.get("info_short", {}).get("name", ""),
                "tag": p["scores"].get("sector_tag") or "",
                "trade_type": p.get("trade_type", "swing"),
                "score": p["scores"].get("composite", 0),
                "multiplier": p["scores"].get("sector_mult", 1.0),
                "entry": p["plan"].get("entry"),
                "stop_loss": p["plan"].get("stop_loss"),
                "take_profit": p["plan"].get("take_profit"),
                "risk_reward": p["plan"].get("risk_reward", 2.0),
                "qty": p["plan"].get("quantity", 0),
                "days_to_earnings": p.get("days_to_earnings"),
            })
        n = log_picks(picks_for_log, reg, cape if "cape" in dir() else None)
        if n == 0 and len(picks_for_log) > 0:
            rprint(f"[yellow][log] All {len(picks_for_log)} picks already logged earlier today (dedup) — none added[/yellow]")
        else:
            rprint(f"[dim][log] Saved {n}/{len(picks_for_log)} picks to data/picks_log.csv[/dim]")
    except Exception as e:
        rprint(f"[red][log] Could not save picks: {e}[/red]")

    rprint("[green]Done. Review picks before any real-money action.[/green]")


if __name__ == "__main__":
    run()
