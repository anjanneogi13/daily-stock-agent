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

    # ═══════════════════════════════════════════════════════════════
    # 🚨 EARLY EXIT GUARD (2026-05-02): Skip if today already logged.
    # Why: GitHub cron multi-fires (Apr 28 = 2 runs, May 1 = 3 runs)
    # bypassed the tag cap (which is per-run, not per-day).
    # This guard makes ALL subsequent same-day runs no-op.
    # ═══════════════════════════════════════════════════════════════
    import csv as _csv
    from datetime import date as _date
    from pathlib import Path as _Path
    _today = _date.today().strftime("%Y-%m-%d")
    _log = _Path("data/picks_log.csv")
    if _log.exists():
        with _log.open() as _f:
            for _row in _csv.DictReader(_f):
                if _row.get("pick_date") == _today:
                    rprint(f"[yellow]⏭  SKIP: picks already logged for {_today} (multi-fire guard)[/yellow]")
                    return

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

    # ═══════════════════════════════════════════════════════════════
    # PR #77: Apply news signals (boost/penalty from recent news)
    # ═══════════════════════════════════════════════════════════════
    rprint("[5c.5/6] Applying news signals (boost/penalty from classified news)...")
    try:
        from src.news_signals import get_ticker_boost
        boosted_count = 0
        for p in capped:
            boost = get_ticker_boost(p["ticker"])
            if abs(boost) >= 0.01:
                old = p["scores"]["composite"]
                new = round(max(0.0, min(1.0, old + boost)), 4)
                p["scores"]["news_boost"] = boost
                p["scores"]["composite_pre_news"] = old
                p["scores"]["composite"] = new
                boosted_count += 1
                arrow = "⬆" if boost > 0 else "⬇"
                rprint(f"  {arrow} {p['ticker']:6s}  {old:.3f} → {new:.3f}  ({boost:+.2f})")
        if boosted_count == 0:
            rprint("  [dim]No active news signals for current picks[/dim]")
        else:
            rprint(f"  [green]✓ {boosted_count} picks adjusted by news signals[/green]")
        # Re-sort by new composite score
        capped.sort(key=lambda x: x["scores"]["composite"], reverse=True)
    except Exception as e:
        rprint(f"  [yellow]⚠ News signals unavailable: {e}[/yellow]")

    # Trim to final pick count
    top = capped[: cfg["output"]["top_n_picks"]]

    # ═══════════════════════════════════════════════════════════════
    # PR #84: HARD ENFORCEMENT LAYER (the prefrontal cortex)
    # Blocks: penny stocks, tight SL, weak sector ETF
    # ═══════════════════════════════════════════════════════════════
    rprint("[5d/6] Applying hard blocks (penny / SL buffer / weak sectors)...")
    from src.hard_blocks import apply_hard_blocks
    pre_block_count = len(top)
    top, blocked = apply_hard_blocks(top, check_sectors=True)
    if blocked:
        rprint(f"  [red]🚫 HARD BLOCKED: {len(blocked)} picks[/red]")
        for b in blocked:
            rprint(f"    • {b['ticker']:6s}  [{b['block_type']}]  {b['reason']}")
    else:
        rprint(f"  [green]✓ All {pre_block_count} picks passed hard blocks[/green]")
    # ═══════════════════════════════════════════════════════════════
    # PILLAR 1: PROBABILITY ENGINE v0.1 (May 2 2026)
    # Run brain on each pick. ADDITIVE — does NOT replace existing SL/TP.
    # Stores brain output in p["brain"] for Telegram comparison + audit.
    # See: docs/BRAIN_ARCHITECTURE.md, src/probability_engine.py
    # ═══════════════════════════════════════════════════════════════
    rprint("[5e/6] Running probability engine (Pillar 1) on picks...")
    try:
        from src.probability_engine import (
            compute_probabilistic_decision,
            SignalState,
        )
        regime_label = reg.get("regime", "unknown") if isinstance(reg, dict) else "unknown"
        brain_count = 0
        for p in top:
            try:
                ticker = p["ticker"]
                entry_price = float(p["plan"].get("entry") or 0)
                if entry_price <= 0:
                    continue
                # Pull conditioning signals from existing pick context
                news_data = p.get("news", {}) or {}
                news_score = float(news_data.get("tradeable_score", 0) or 0)
                news_sentiment = news_data.get("sentiment", "neutral") or "neutral"
                signals = SignalState(
                    regime=regime_label,
                    news_score=news_score,
                    news_sentiment=news_sentiment,
                    days_to_earnings=p.get("days_to_earnings"),
                    watchlist_boost=float(p["scores"].get("watchlist_boost", 0) or 0),
                )
                decision = compute_probabilistic_decision(ticker, entry_price, signals=signals)
                # Store as audit trail; do NOT mutate plan yet
                p["brain"] = {
                    "p_win": decision.p_win,
                    "ev_pct": decision.expected_value_pct,
                    "brain_sl": decision.final_sl_price,
                    "brain_tp": decision.final_tp_price,
                    "brain_sl_pct": decision.final_sl_pct,
                    "brain_tp_pct": decision.final_tp_pct,
                    "confidence": decision.confidence,
                    "signals": decision.adjustments_applied,
                }
                brain_count += 1
            except Exception as e:
                p["brain"] = {"error": str(e)}
        rprint(f"  [green]✓ Brain analyzed {brain_count}/{len(top)} picks[/green]")
        # Show brain decisions
        for p in top:
            b = p.get("brain", {})
            if "p_win" in b:
                ev_color = "green" if b["ev_pct"] > 0 else "red"
                rprint(
                    f"    🧠 {p['ticker']:6s}  "
                    f"P(win)={b['p_win']:.0%}  "
                    f"EV=[{ev_color}]{b['ev_pct']:+.2f}%[/{ev_color}]  "
                    f"brain_SL=${b['brain_sl']}  brain_TP=${b['brain_tp']}  "
                    f"[{b['confidence']}]"
                )
    except Exception as e:
        rprint(f"  [yellow]⚠ Probability engine skipped: {e}[/yellow]")
    # ═══════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════
    # PILLAR 1 EV GATE (May 2 2026) — opt-in via env vars
    # OBSERVE-MODE by default: logs vetoes but doesn't filter.
    # To activate: set BRAIN_ENFORCE_EV=true in workflow env.
    # ═══════════════════════════════════════════════════════════════
    enforce_ev = os.getenv("BRAIN_ENFORCE_EV", "false").lower() == "true"
    ev_min_pct = float(os.getenv("BRAIN_EV_MIN_PCT", "-1.0"))
    ev_vetoes = []
    for p in top:
        b = p.get("brain", {}) or {}
        ev = b.get("ev_pct")
        if ev is not None and ev < ev_min_pct:
            ev_vetoes.append({
                "ticker": p["ticker"],
                "ev_pct": ev,
                "p_win": b.get("p_win"),
                "confidence": b.get("confidence"),
            })
    if ev_vetoes:
        mode = "ENFORCED" if enforce_ev else "OBSERVE-ONLY"
        rprint(f"  [yellow]🧮 EV gate ({mode}, threshold={ev_min_pct:+.2f}%): {len(ev_vetoes)} pick(s) flagged[/yellow]")
        for v in ev_vetoes:
            rprint(
                f"    {'❌' if enforce_ev else '⚠ '} {v['ticker']:6s}  "
                f"EV={v['ev_pct']:+.2f}%  P(win)={v['p_win']:.0%}  [{v['confidence']}]"
            )
        if enforce_ev:
            veto_set = {v["ticker"] for v in ev_vetoes}
            top = [p for p in top if p["ticker"] not in veto_set]
            rprint(f"  [yellow]🧮 Filtered: {len(top)} picks remain after EV enforcement[/yellow]")
    else:
        rprint(f"  [dim]🧮 EV gate: 0 vetoes (threshold={ev_min_pct:+.2f}%, mode={'ENFORCED' if enforce_ev else 'OBSERVE'})[/dim]")
    # ═══════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════
    # PILLAR 5 AUTO-PAUSE (May 2 2026) — opt-in via env var
    # OBSERVE-MODE by default: logs paused groups but doesn't filter.
    # To activate: set AUTO_PAUSE_ENABLED=true in workflow env.
    # ═══════════════════════════════════════════════════════════════
    enforce_pause = os.getenv("AUTO_PAUSE_ENABLED", "false").lower() == "true"
    pause_lookback = int(os.getenv("AUTO_PAUSE_LOOKBACK_DAYS", "30"))
    try:
        from src.auto_pause import get_paused_set
        paused_tags = get_paused_set("tag", lookback_days=pause_lookback)
        paused_types = get_paused_set("trade_type", lookback_days=pause_lookback)
        pause_vetoes = []
        for p_ in top:
            tag = (p_.get("tag") or "").strip()
            tt = (p_.get("trade_type") or "").strip()
            if tag in paused_tags:
                pause_vetoes.append((p_["ticker"], "tag", tag, paused_tags[tag]))
            elif tt in paused_types:
                pause_vetoes.append((p_["ticker"], "trade_type", tt, paused_types[tt]))
        if pause_vetoes:
            mode = "ENFORCED" if enforce_pause else "OBSERVE-ONLY"
            rprint(f"  [yellow]🛑 Auto-pause ({mode}): {len(pause_vetoes)} pick(s) flagged[/yellow]")
            for tk, dim, val, why in pause_vetoes:
                rprint(f"    {'❌' if enforce_pause else '⚠ '} {tk:6s}  {dim}={val!r}  reason: {why}")
            if enforce_pause:
                veto_set = {v[0] for v in pause_vetoes}
                top = [p_ for p_ in top if p_["ticker"] not in veto_set]
                rprint(f"  [yellow]🛑 Filtered: {len(top)} picks remain after auto-pause[/yellow]")
        else:
            rprint(f"  [dim]🛑 Auto-pause: 0 vetoes (mode={'ENFORCED' if enforce_pause else 'OBSERVE'}, lookback={pause_lookback}d)[/dim]")
    except Exception as e:
        rprint(f"  [yellow]⚠ Auto-pause skipped: {e}[/yellow]")
    # ═══════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════
    # WEEK 3: Auto-tag DAY vs SWING
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
            brain = p.get("brain", {}) or {}
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
                # PILLAR 1 audit fields (May 2 2026)
                "brain_p_win": brain.get("p_win"),
                "brain_ev_pct": brain.get("ev_pct"),
                "brain_sl": brain.get("brain_sl"),
                "brain_tp": brain.get("brain_tp"),
                "brain_confidence": brain.get("confidence"),
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
