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
from src.monster_hunt import apply_monster_treatment
from src.sector_benchmark import resolve_sector_etf
from src.signal_journal import log_pick as _journal_log_pick
from src.auto_pause import compute_score as _pause_score, format_summary as _pause_fmt
from src.pause_state import is_paused as _is_paused, maybe_auto_pause as _maybe_pause, format_pause_alert as _pause_alert
from src.market_calendar import is_trading_day as _is_td, reason_market_closed as _why_closed, next_trading_day as _next_td
from src.github_observability import github_observability_metadata

def _safe_trade_type_for_pick(scores: dict, pick_date=None, sig: dict = None, gap_pct: float = 0.0) -> str:
    """Calendar-safe DAY/SWING classifier.

    Bug #7: a day trade should never be emitted for a non-trading day.
    Manual dispatches, backfills, or calendar mismatches can run the picker
    when the US market is closed. In that case, downgrade would-be DAY picks
    to SWING instead of sending an impossible intraday alert.
    """
    ttype = classify_trade_type(scores, sig=sig, gap_pct=gap_pct)
    if ttype == "day" and not _is_td(pick_date):
        return "swing"
    return ttype


def _yf_ticker_for_sector_benchmark(symbol: str):
    """Small seam for tests around yfinance sector benchmark fetches."""
    import yfinance as yf
    return yf.Ticker(symbol)


def _latest_close_for_sector_benchmark(symbol: str) -> float | None:
    """Fetch latest close for an ETF symbol, returning None on empty/error."""
    try:
        hist = _yf_ticker_for_sector_benchmark(symbol).history(period="2d")
        if len(hist):
            return float(hist["Close"].iloc[-1])
    except Exception:
        return None
    return None


def _sector_benchmark_for_pick(pick: dict) -> tuple[str, float | None]:
    """Return (sector_etf, sector_close) for a pick with SPY fallback.

    Bug #8/#10: sector alpha learning needs sector_close populated at pick time.
    If the resolved sector ETF has no quote, fall back to SPY so the row still
    has a usable benchmark rather than a blank sector_close.
    """
    sector = pick.get("info_short", {}).get("sector", "")
    tag = pick.get("scores", {}).get("sector_tag") or ""
    etf = resolve_sector_etf(sector=sector, tag=tag) or "SPY"

    close = _latest_close_for_sector_benchmark(etf)
    if close is not None:
        return etf, close

    if etf != "SPY":
        spy_close = _latest_close_for_sector_benchmark("SPY")
        if spy_close is not None:
            return "SPY", spy_close

    return etf, None



# Auto-seed wisdom base on every run (idempotent — safe)
try:
    import subprocess, sys as _sys
    subprocess.run([_sys.executable, "scripts/bootstrap_wisdom.py"],
                   check=False, capture_output=True, timeout=10)
except Exception:
    pass


def load_config(path: str = "config.yaml") -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _candidate_report_value(value):
    """Return a JSON-safe compact representation for candidate diagnostics."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_candidate_report_value(v) for v in value[:10]]
    if isinstance(value, dict):
        return {
            str(k): _candidate_report_value(v)
            for k, v in list(value.items())[:30]
            if k not in {"df", "dataframe", "history"}
        }
    return str(value)


def _summarize_candidate_for_report(candidate: dict) -> dict:
    """Compact candidate summary for no-pick / rejection diagnostics."""
    scores = candidate.get("scores") or {}
    plan = candidate.get("plan") or {}
    info = candidate.get("info_short") or {}
    news_signal = candidate.get("news_signal") or {}
    news = candidate.get("news") or {}

    return {
        "ticker": candidate.get("ticker"),
        "company": info.get("name") or candidate.get("company") or "",
        "sector": info.get("sector") or "",
        "score": scores.get("composite"),
        "trade_type": candidate.get("trade_type") or scores.get("trade_type"),
        "sector_tag": scores.get("sector_tag"),
        "day_score": scores.get("day_score"),
        "news_boost": scores.get("news_boost"),
        "news_action_window": (
            scores.get("news_action_window")
            or news_signal.get("action_window")
            or (news.get("action_window") if isinstance(news, dict) else None)
        ),
        "entry": plan.get("entry"),
        "stop_loss": plan.get("stop_loss"),
        "take_profit": plan.get("take_profit"),
        "risk_reward": plan.get("risk_reward"),
        "days_to_earnings": candidate.get("days_to_earnings"),
        "watch_only": bool(candidate.get("watch_only") or plan.get("watch_only")),
        "watch_only_reason": candidate.get("watch_only_reason") or plan.get("watch_only_reason") or "",
    }


def _classify_no_pick_cause(pipeline: dict | None, market_data_health: dict | None, diagnostics: dict | None = None) -> tuple[str, list[str], str]:
    """Classify why official Daily Picks produced no final picks."""
    pipe = pipeline or {}
    health = market_data_health or {}
    diag = diagnostics or {}
    secondary = []

    providers = health.get("providers") or {}
    yf_stats = providers.get("yfinance") or {}
    yf_errors = int(yf_stats.get("errors") or 0)
    yf_attempts = int(yf_stats.get("attempts") or 0)
    yf_rate_limited = int(yf_stats.get("rate_limited") or 0)

    if yf_attempts and (yf_rate_limited > 0 or yf_errors / max(yf_attempts, 1) >= 0.20):
        secondary.append("YFINANCE_PROVIDER_DEGRADED")

    if (health.get("by_stage") or {}).get("ohlcv", {}).get("errors", 0):
        secondary.append("OHLCV_PROVIDER_ERRORS_PRESENT")

    sanity_blocked = diag.get("premarket_sanity_blocked_candidates")
    pre_sanity = diag.get("pre_premarket_sanity_candidates")
    if isinstance(sanity_blocked, list) and sanity_blocked and isinstance(pre_sanity, list) and len(sanity_blocked) >= len(pre_sanity):
        primary = "NO_PICK_PREMARKET_SANITY_BLOCKED_ALL"
        summary = "No official picks were generated because all finalists were blocked by the premarket sanity gate."
        return primary, sorted(set(secondary)), summary

    risk_blocked = diag.get("portfolio_risk_blocked_candidates")
    pre_risk = diag.get("pre_portfolio_risk_candidates")
    if isinstance(risk_blocked, list) and risk_blocked and isinstance(pre_risk, list) and len(risk_blocked) >= len(pre_risk):
        primary = "NO_PICK_RISK_GATE_BLOCKED_ALL"
        summary = "No official picks were generated because all finalists were blocked by the portfolio risk gate."
        return primary, sorted(set(secondary)), summary

    missing_data_blocked = diag.get("missing_data_blocked_candidates")
    pre_missing_data = diag.get("pre_missing_data_candidates")
    if (
        isinstance(missing_data_blocked, list)
        and missing_data_blocked
        and isinstance(pre_missing_data, list)
        and len(missing_data_blocked) >= len(pre_missing_data)
    ):
        primary = "NO_PICK_DATA_READINESS_FAILED"
        summary = "No official picks were generated because all finalists had missing or malformed required official-pick data."
        return primary, sorted(set(secondary)), summary

    readiness_gate = diag.get("readiness_gate") if isinstance(diag.get("readiness_gate"), dict) else {}
    if readiness_gate and readiness_gate.get("passed") is False:
        primary = readiness_gate.get("primary_no_pick_cause") or "NO_PICK_DATA_READINESS_FAILED"
        summary = (
            readiness_gate.get("human_readable_summary")
            or "No official picks were generated because premarket data readiness failed."
        )
        for warning in readiness_gate.get("warnings") or []:
            secondary.append(str(warning).upper())
        return primary, sorted(set(secondary)), summary

    final_count = int(pipe.get("final_pick_count") or 0)
    scored_count = int(pipe.get("scored_count") or 0)
    fetched_count = int(pipe.get("fetched_count") or 0)
    filtered_count = int(pipe.get("filtered_count") or 0)
    pre_hard = int(pipe.get("pre_hard_block_pick_count") or 0)
    hard_blocked = int(pipe.get("hard_blocked_count") or 0)

    if final_count > 0:
        primary = "PICKS_AVAILABLE"
        summary = f"{final_count} official pick(s) were available."
    elif fetched_count == 0:
        primary = "NO_PICK_DATA_PROVIDER_DEGRADED"
        summary = "No official picks were generated because no market data was fetched."
    elif scored_count == 0:
        primary = "NO_PICK_NO_SCORED_CANDIDATES"
        summary = "No official picks were generated because no candidates survived scoring."
    elif filtered_count == 0:
        primary = "NO_PICK_FILTERS_REMOVED_ALL"
        summary = "No official picks were generated because filters removed all scored candidates."
    elif pre_hard > 0 and hard_blocked >= pre_hard:
        primary = "NO_PICK_ALL_FINALISTS_HARD_BLOCKED"
        summary = f"No official picks were generated because all {pre_hard} finalist candidate(s) were hard-blocked."
    elif diag.get("runtime_failure"):
        primary = "NO_PICK_RUNTIME_FAILURE"
        summary = "No official picks were generated because the runtime failed."
    else:
        primary = "NO_PICK_UNKNOWN_POST_FILTER_GATING"
        summary = "No official picks were generated after scoring/filtering/gating; inspect candidate diagnostics."

    return primary, sorted(set(secondary)), summary



def _write_daily_picks_candidate_diagnostics_report(pipeline: dict | None, diagnostics: dict | None, *, official_premarket_pick: bool) -> None:
    """Persist candidate diagnostics for successful or no-pick official runs."""
    try:
        import json
        from datetime import datetime, timezone
        from pathlib import Path
        from zoneinfo import ZoneInfo

        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        now_dt_utc = datetime.now(timezone.utc).replace(microsecond=0)
        now_utc = now_dt_utc.isoformat().replace("+00:00", "Z")
        date_str = now_dt_utc.astimezone(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
        diag = diagnostics or {}

        payload = {
            "artifact": "daily_picks_candidate_diagnostics",
            "date": date_str,
            "timestamp_utc": now_utc,
            "mode": "monitoring_only",
            "official_premarket_pick": bool(official_premarket_pick),
            "paper_trading_enabled": False,
            "live_trading_enabled": False,
            "ready_for_paper_trading": False,
            "pipeline": pipeline or {},
            "diagnostics": diag,
            "diagnostics_available": bool(diag),
        }

        (data_dir / f"daily_picks_candidate_diagnostics_{date_str}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n"
        )

        lines = [
            "# Daily Picks Candidate Diagnostics",
            "",
            "Monitoring-only diagnostic artifact. Not buy instructions.",
            "",
            f"- Date: **{date_str}**",
            f"- Official premarket pick available: **{str(bool(official_premarket_pick)).lower()}**",
            "- Paper trading enabled: **false**",
            "- Live trading enabled: **false**",
            "",
            "## Stage Counts",
        ]
        for key, value in sorted((diag.get("stage_counts") or {}).items()):
            lines.append(f"- {key}: **{value}**")

        selected = diag.get("selected_picks") or []
        lines.extend(["", "## Selected Official Picks"])
        if selected:
            for item in selected:
                lines.append(
                    f"- {item.get('ticker')}: score=**{item.get('score')}**, "
                    f"action=**{item.get('premarket_action') or 'official'}**, "
                    f"R:R=**{item.get('risk_reward')}**"
                )
        else:
            lines.append("- None.")

        rejected = diag.get("rejected_candidates") or []
        lines.extend(["", "## Rejected Candidates"])
        if rejected:
            for item in rejected:
                lines.append(
                    f"- {item.get('ticker')}: **{item.get('rejection_stage', 'unknown')}** — "
                    f"{item.get('reason') or item.get('block_type') or item.get('action') or 'no reason recorded'}"
                )
        else:
            lines.append("- None recorded.")

        (data_dir / f"daily_picks_candidate_diagnostics_{date_str}.md").write_text(
            "\n".join(lines) + "\n"
        )
    except Exception:
        pass



def _write_daily_picks_no_pick_report(reason: str, pipeline: dict | None = None, diagnostics: dict | None = None) -> None:
    """Persist a no-pick evidence artifact for operational learning."""
    try:
        import json
        from datetime import datetime, timezone
        from pathlib import Path

        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        from zoneinfo import ZoneInfo
        from src.premarket_decision_contract import (
            CONTRACT_VERSION,
            DECISION_OFFICIAL_NO_PICK,
            SCORING_VERSION,
            STRATEGY_LANE,
            STRATEGY_VERSION,
        )

        now_dt_utc = datetime.now(timezone.utc).replace(microsecond=0)
        now_utc = now_dt_utc.isoformat().replace("+00:00", "Z")
        now_et = now_dt_utc.astimezone(ZoneInfo("America/New_York")).isoformat()
        date_str = now_et[:10]

        payload = {
            "artifact": "daily_picks_no_pick_report",
            "date": date_str,
            "timestamp_utc": now_utc,
            "decision": DECISION_OFFICIAL_NO_PICK,
            "strategy_lane": STRATEGY_LANE,
            "contract_version": CONTRACT_VERSION,
            "strategy_version": STRATEGY_VERSION,
            "scoring_version": SCORING_VERSION,
            "config_version": os.getenv("CONFIG_VERSION", "config.yaml"),
            "selection_time_et": now_et,
            "workflow_run_id": os.getenv("GITHUB_RUN_ID", "local"),
            "commit_sha": os.getenv("GITHUB_SHA", "local"),
            **github_observability_metadata(),
            "mode": "monitoring_only",
            "official_premarket_pick": False,
            "paper_trading_enabled": False,
            "live_trading_enabled": False,
            "ready_for_paper_trading": False,
            "reason": reason,
            "pipeline": pipeline or {},
            "market_data_health": {},
            "candidate_diagnostics": diagnostics or {},
            "watch_only_available": False,
            "next_action": "Use watch-only fallback only; do not fabricate official picks.",
        }

        try:
            from src.market_data_health import summarize_market_data_health
            payload["market_data_health"] = summarize_market_data_health() or {}
        except Exception:
            payload["market_data_health"] = {}

        primary_cause, secondary_causes, human_summary = _classify_no_pick_cause(
            pipeline or {},
            payload.get("market_data_health") or {},
            diagnostics or {},
        )
        payload["primary_no_pick_cause"] = primary_cause
        payload["secondary_causes"] = secondary_causes
        payload["human_readable_summary"] = human_summary
        payload["diagnostics"] = diagnostics or {}
        payload["candidate_diagnostics"] = diagnostics or {}

        if primary_cause == "NO_PICK_DATA_PROVIDER_DEGRADED":
            payload["data_readiness_status"] = "not_ready_data_provider_degraded"
            payload["provider_status"] = "degraded"
        elif primary_cause == "NO_PICK_DATA_READINESS_FAILED":
            payload["data_readiness_status"] = "not_ready_data_readiness_failed"
            payload["provider_status"] = "unknown"
        elif primary_cause in {"NO_PICK_NO_SCORED_CANDIDATES", "NO_PICK_FILTERS_REMOVED_ALL"}:
            payload["data_readiness_status"] = "ready_no_qualified_candidates"
            payload["provider_status"] = "healthy"
        elif primary_cause == "NO_PICK_ALL_FINALISTS_HARD_BLOCKED":
            payload["data_readiness_status"] = "ready_all_finalists_hard_blocked"
            payload["provider_status"] = "healthy"
        elif primary_cause == "NO_PICK_PREMARKET_SANITY_BLOCKED_ALL":
            payload["data_readiness_status"] = "ready_all_finalists_blocked_by_premarket_sanity"
            payload["provider_status"] = "healthy"
        elif primary_cause == "NO_PICK_RISK_GATE_BLOCKED_ALL":
            payload["data_readiness_status"] = "ready_all_finalists_blocked_by_portfolio_risk"
            payload["provider_status"] = "healthy"
        elif primary_cause == "NO_PICK_RUNTIME_FAILURE":
            payload["data_readiness_status"] = "not_ready_runtime_failure"
            payload["provider_status"] = "unknown"
        else:
            payload["data_readiness_status"] = "readiness_uncertain"
            payload["provider_status"] = "unknown"
        payload["market_session_status"] = "premarket"

        (data_dir / f"daily_picks_no_pick_report_{date_str}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n"
        )

        lines = [
            "# Daily Picks No-Pick Report",
            "",
            "Monitoring-only failure evidence. No official picks were generated.",
            "",
            f"- Date: **{date_str}**",
            f"- Reason: **{reason}**",
            f"- Primary no-pick cause: **{payload.get('primary_no_pick_cause')}**",
            f"- Summary: **{payload.get('human_readable_summary')}**",
            "- Paper trading enabled: **false**",
            "- Live trading enabled: **false**",
            "- Official premarket pick: **false**",
            "",
            "## Pipeline",
        ]
        for key, value in sorted((pipeline or {}).items()):
            lines.append(f"- {key}: **{value}**")

        if payload.get("market_data_health"):
            lines.extend(["", "## Market Data Health"])
            providers = payload["market_data_health"].get("providers", {})
            for provider, stats in sorted(providers.items()):
                lines.append(
                    f"- {provider}: attempts=**{stats.get('attempts', 0)}**, "
                    f"successes=**{stats.get('successes', 0)}**, "
                    f"errors=**{stats.get('errors', 0)}**, "
                    f"rate_limited=**{stats.get('rate_limited', 0)}**, "
                    f"unauthorized=**{stats.get('unauthorized', 0)}**"
                )

        if payload.get("secondary_causes"):
            lines.extend(["", "## Secondary Causes"])
            for cause in payload["secondary_causes"]:
                lines.append(f"- {cause}")

        diag = payload.get("diagnostics") or {}
        if diag.get("hard_blocked_candidates"):
            lines.extend(["", "## Hard-Blocked Finalists"])
            for item in diag["hard_blocked_candidates"]:
                lines.append(
                    f"- {item.get('ticker')}: **{item.get('block_type')}** — {item.get('reason')}"
                )

        (data_dir / f"daily_picks_no_pick_report_{date_str}.md").write_text(
            "\n".join(lines) + "\n"
        )

        diag = payload.get("diagnostics") or {}
        if diag:
            _write_daily_picks_candidate_diagnostics_report(
                pipeline or {},
                diag,
                official_premarket_pick=False,
            )
            rejection_payload = {
                "artifact": "daily_picks_candidate_rejections",
                "date": date_str,
                "timestamp_utc": now_utc,
                "mode": "monitoring_only",
                "official_premarket_pick": False,
                "paper_trading_enabled": False,
                "live_trading_enabled": False,
                "ready_for_paper_trading": False,
                "primary_no_pick_cause": payload.get("primary_no_pick_cause"),
                "secondary_causes": payload.get("secondary_causes", []),
                "pipeline": pipeline or {},
                "diagnostics": diag,
            }
            (data_dir / f"daily_picks_candidate_rejections_{date_str}.json").write_text(
                json.dumps(rejection_payload, indent=2, sort_keys=True) + "\n"
            )

            def _candidate_markdown_details(candidate: dict) -> str:
                if not isinstance(candidate, dict) or not candidate:
                    return "details unavailable"
                parts = []
                for key in (
                    "score",
                    "sector",
                    "sector_tag",
                    "trade_type",
                    "entry",
                    "stop_loss",
                    "take_profit",
                    "risk_reward",
                    "news_action_window",
                    "watch_only",
                    "watch_only_reason",
                ):
                    value = candidate.get(key)
                    if value not in (None, ""):
                        parts.append(f"{key}={value}")
                return ", ".join(parts) if parts else "details unavailable"

            rejection_lines = [
                "# Daily Picks Candidate Rejection Report",
                "",
                "Monitoring-only diagnostic artifact. Not official picks. Not buy instructions.",
                "",
                f"- Date: **{date_str}**",
                f"- Primary no-pick cause: **{payload.get('primary_no_pick_cause')}**",
                f"- Summary: **{payload.get('human_readable_summary')}**",
                "- Paper trading enabled: **false**",
                "- Live trading enabled: **false**",
                "",
                "## Pre-Hard-Block Finalists",
            ]

            pre_hard = diag.get("pre_hard_block_candidates") or []
            if pre_hard:
                for item in pre_hard:
                    rejection_lines.append(
                        f"- {item.get('ticker')}: {_candidate_markdown_details(item)}"
                    )
            else:
                rejection_lines.append("- None recorded.")

            rejection_lines.extend(["", "## Hard-Blocked Finalists"])
            hard_blocked = diag.get("hard_blocked_candidates") or []
            if hard_blocked:
                for item in hard_blocked:
                    candidate = item.get("candidate") if isinstance(item.get("candidate"), dict) else {}
                    rejection_lines.append(
                        f"- {item.get('ticker')}: **{item.get('block_type')}** — "
                        f"{item.get('reason')} ({_candidate_markdown_details(candidate)})"
                    )
            else:
                rejection_lines.append("- None recorded.")
            (data_dir / f"daily_picks_candidate_rejections_{date_str}.md").write_text(
                "\n".join(rejection_lines) + "\n"
            )
    except Exception:
        # Do not hide the original no-pick failure if reporting fails.
        pass


def _should_log_paper_trade() -> bool:
    """Return True only when legacy local paper-trade logging is explicit.

    The project is monitoring-only by default. Leaving TRADING_MODE unset must
    not create paper-trade artifacts or imply paper-trading readiness.
    """
    return os.getenv("TRADING_MODE", "monitoring").strip().lower() == "paper"


def run():
    load_dotenv()
    cfg = load_config()
    pipeline = {
        "universe_count": 0,
        "fetched_count": 0,
        "scored_count": 0,
        "filtered_count": 0,
        "capped_count": 0,
        "pre_hard_block_pick_count": 0,
        "hard_blocked_count": 0,
        "post_hard_block_pick_count": 0,
        "final_pick_count": 0,
        "scorer_workers": 0,
    }
    rprint("[bold cyan]Daily Stock Picker Agent[/bold cyan]")
    rprint("[dim]Not financial advice. Educational only.[/dim]\n")

    # ═══════════════════════════════════════════════════════════════
    # PILLAR 4 ENFORCE: Skip entire run if agent is paused
    # ═══════════════════════════════════════════════════════════════
    # 🗓 T51 — Skip if US market closed (weekend or holiday). Defensive.
    try:
        if not _is_td():
            _reason = _why_closed() or "unknown"
            _nxt = _next_td()
            rprint(f"[yellow bold]🗓 US market CLOSED today ({_reason}). Next trading day: {_nxt}. Skipping picks.[/yellow bold]")
            return
    except Exception as _e:
        rprint(f"[dim]market-calendar check failed: {_e} — proceeding[/dim]")

    _ps = _is_paused()
    if _ps["paused"]:
        rprint("[red bold]🚨 AGENT PAUSED — skipping today's run[/red bold]")
        rprint(f"[red]   Reason: {_ps['reason']}[/red]")
        rprint(f"[red]   Until:  {_ps['until']} ({_ps['days_remaining']}d remaining)[/red]")
        rprint(f"[dim]   Override: python scripts/unpause.py[/dim]")
        # Write minimal pause-day artifact for the Telegram sender
        try:
            from pathlib import Path as _P
            import json as _j
            _P("data").mkdir(exist_ok=True)
            _P("data/last_run_paused.json").write_text(_j.dumps({
                "paused": True, "date": _ps["until"], **_ps
            }, indent=2))
        except Exception:
            pass
        return  # ← HARD STOP. No picks, no journaling, no Telegram picks.

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
    pipeline["universe_count"] = len(tickers)

    rprint("[3/6] Fetching market data...")
    data = fetch_universe_data(tickers, period=f"{cfg['strategy']['lookback_days']}d")
    pipeline["fetched_count"] = len(data)

    rprint("[3b/6] Checking premarket data readiness...")
    try:
        from src.market_data_health import summarize_market_data_health
        from src.premarket_readiness_gate import build_premarket_readiness_decision

        market_data_health = summarize_market_data_health() or {}
        readiness = build_premarket_readiness_decision(
            universe_count=pipeline["universe_count"],
            fetched_count=pipeline["fetched_count"],
            market_data_health=market_data_health,
            min_fetch_coverage=float(os.getenv("PREMARKET_MIN_FETCH_COVERAGE", "0.25")),
            min_fetched_count=int(os.getenv("PREMARKET_MIN_FETCHED_COUNT", "25")),
        )
        pipeline["data_readiness_status"] = readiness.get("status")
        pipeline["data_readiness_passed"] = bool(readiness.get("passed"))

        if not readiness.get("passed"):
            diagnostics = {"readiness_gate": readiness}
            _write_daily_picks_no_pick_report(
                readiness.get("human_readable_summary")
                or "Official premarket pick skipped because data readiness failed.",
                pipeline,
                diagnostics,
            )
            rprint(f"[yellow]Premarket data readiness failed: {readiness.get('status')}[/yellow]")
            rprint("[green]Done. No official premarket pick today.[/green]")
            return

        rprint(f"  [green]✓ Data readiness passed ({readiness.get('fetched_count')}/{readiness.get('universe_count')} fetched)[/green]")
    except Exception as e:
        pipeline["data_readiness_status"] = "readiness_gate_error"
        pipeline["data_readiness_passed"] = False
        diagnostics = {"readiness_gate_error": str(e)}
        _write_daily_picks_no_pick_report(
            "Official premarket pick skipped because the data-readiness gate failed unexpectedly.",
            pipeline,
            diagnostics,
        )
        rprint(f"[red]Premarket data readiness gate failed unexpectedly: {e}[/red]")
        rprint("[green]Done. No official premarket pick today.[/green]")
        return

    rprint("[4/6] Computing indicators + scoring (parallel, all candidates)...")
    from src.parallel_scorer import score_all
    scorer_workers = int(os.getenv("DAILY_SCORER_WORKERS", "4"))
    pipeline["scorer_workers"] = scorer_workers
    rprint(f"[dim]Scoring workers: {scorer_workers} (set DAILY_SCORER_WORKERS to override)[/dim]")
    candidates = score_all(data, cfg, max_workers=scorer_workers)
    pipeline["scored_count"] = len(candidates)
    try:
        from src.market_data_health import write_market_data_run_summary
        write_market_data_run_summary(scored_count=len(candidates))
    except Exception:
        pass

    rprint("[5/6] Filtering for earnings risk + wisdom kill list...")
    filtered = []
    _killed_dropped = []
    _earnings_dropped = []
    _wisdom_alerts  = []
    for p in candidates[: cfg["output"]["top_n_picks"] * 4]:  # 4x buffer for sector cap
        # Pillar 2/4: hard-drop tickers on the wisdom kill list
        if p["scores"].get("wisdom_kill"):
            _killed_dropped.append({
                "ticker": p["ticker"],
                "rejection_stage": "wisdom_kill",
                "reason": "on cooldown or kill list",
                "candidate": _summarize_candidate_for_report(p),
            })
            rprint(f"  [red]🥶 DROP {p['ticker']} — on cooldown (kill list)[/red]")
            continue

        # Surface wisdom warnings/boosts so they're visible (observe-mode)
        _ww = p["scores"].get("wisdom_warnings") or []
        _wb = p["scores"].get("wisdom_boosts")   or []
        for _w in _ww:
            rprint(f"  [yellow]⚠ {p['ticker']}: {_w}[/yellow]")
            _wisdom_alerts.append((p["ticker"], "warn", _w))
        for _b in _wb:
            rprint(f"  [green]✨ {p['ticker']}: {_b}[/green]")
            _wisdom_alerts.append((p["ticker"], "boost", _b))

        d2e = days_to_earnings(p["ticker"])
        p["days_to_earnings"] = d2e if d2e < 999 else None
        if d2e < 5:
            _earnings_dropped.append({
                "ticker": p["ticker"],
                "rejection_stage": "earnings_risk",
                "reason": f"earnings in {d2e}d",
                "candidate": _summarize_candidate_for_report(p),
            })
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
    pipeline["filtered_count"] = len(filtered)

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
    pipeline["capped_count"] = len(capped)
    rprint(f"  [dim]Sector cap: {pre_cap} → {len(capped)} (max 4/sector, weak={list(weak_sectors.keys()) or 'none'})[/dim]")

    # ═══════════════════════════════════════════════════════════════
    # PR #77: Apply news signals (boost/penalty from recent news)
    # ═══════════════════════════════════════════════════════════════
    rprint("[5c.5/6] Applying news signals (boost/penalty from classified news)...")
    try:
        from src.news_signals import get_ticker_boost, get_ticker_signal
        boosted_count = 0
        for p in capped:
            signal = get_ticker_signal(p["ticker"])
            boost = get_ticker_boost(p["ticker"])
            if signal:
                p["news_signal"] = signal
                action_window = signal.get("action_window")
                if action_window:
                    p["scores"]["news_action_window"] = action_window
                    p.setdefault("news", {})["action_window"] = action_window
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
    pre_hard_block_candidates = list(top)
    pipeline["pre_hard_block_pick_count"] = len(top)


    # ═══════════════════════════════════════════════════════════════
    # PR #84: HARD ENFORCEMENT LAYER (the prefrontal cortex)
    # Blocks: penny stocks, tight SL, weak sector ETF
    # ═══════════════════════════════════════════════════════════════
    rprint("[5d/6] Applying hard blocks (penny / SL buffer / weak sectors)...")
    from src.hard_blocks import apply_hard_blocks
    pre_block_count = len(top)
    top, blocked = apply_hard_blocks(top, check_sectors=True)
    pipeline["hard_blocked_count"] = len(blocked)
    pipeline["post_hard_block_pick_count"] = len(top)
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
    # E4 (May 4 2026): SMELL FACULTY — final sanity filter
    # Runs sniff() on each pick, drops blockers (CRITICAL severity),
    # attaches non-blocking warnings to pick['smell_warnings'] for
    # downstream Telegram display.
    #
    # OBSERVE-MODE by default: logs blockers but doesn't filter.
    # To activate: set SMELL_ENFORCE=true in workflow env.
    #
    # Currently catches: stale_price (E2c.2 cross-source disagreement),
    # tight_stop (SL <0.8% — likely noise), and others in ALL_SMELLS.
    # ═══════════════════════════════════════════════════════════════
    enforce_smell = os.getenv("SMELL_ENFORCE", "false").lower() == "true"
    try:
        from src.smell_faculty import sniff, has_blocking_smell
        smell_blockers = []
        smell_warned = 0
        for p in top:
            sig = p.get("signals") or {}
            blocker = has_blocking_smell(p, sig)
            if blocker:
                smell_blockers.append({
                    "ticker": p["ticker"],
                    "code": blocker.code,
                    "message": blocker.message,
                })
                continue
            warnings = sniff(p, sig)
            if warnings:
                p["smell_warnings"] = [
                    {"code": w.code, "severity": w.severity, "message": w.message}
                    for w in warnings
                ]
                smell_warned += 1
        if smell_blockers:
            mode = "ENFORCED" if enforce_smell else "OBSERVE-ONLY"
            rprint(f"  [red]👃 Smell faculty ({mode}): {len(smell_blockers)} pick(s) flagged[/red]")
            for b in smell_blockers:
                rprint(f"    {'❌' if enforce_smell else '⚠ '} {b['ticker']:6s}  [{b['code']}]  {b['message']}")
            if enforce_smell:
                veto_set = {b["ticker"] for b in smell_blockers}
                top = [p for p in top if p["ticker"] not in veto_set]
                rprint(f"  [red]👃 Filtered: {len(top)} picks remain after smell enforcement[/red]")
        else:
            rprint(f"  [dim]👃 Smell faculty: 0 blockers (mode={'ENFORCED' if enforce_smell else 'OBSERVE'}, {smell_warned} non-blocking warnings)[/dim]")
    except Exception as _se:
        rprint(f"  [yellow]⚠ Smell faculty skipped: {_se}[/yellow]")
    # ═══════════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════════
    # WEEK 3: Auto-tag DAY vs SWING
    # ═══════════════════════════════════════════════════════════════
    # WEEK 3: Auto-tag DAY vs SWING
    # ═══════════════════════════════════════════════════════════════
    pipeline["final_pick_count"] = len(top)
    try:
        from src.market_data_health import write_market_data_run_summary
        write_market_data_run_summary(final_pick_count=len(top))
    except Exception:
        pass
    if not top:
        reason = (
            "No official picks generated after scoring/filtering/gating. "
            "This is not safe to treat as a successful daily-picks run; "
            "check data-provider/rate-limit/no-candidate logs and use watch-only fallback if needed."
        )
        hard_blocked_candidates = []
        for b in blocked:
            item = dict(b)
            match = next(
                (p for p in pre_hard_block_candidates if p.get("ticker") == b.get("ticker")),
                {},
            )
            item["candidate"] = _summarize_candidate_for_report(match) if match else {}
            hard_blocked_candidates.append(item)

        try:
            from src.candidate_diagnostics import build_candidate_diagnostics
            diagnostics = build_candidate_diagnostics(
                pipeline=pipeline,
                scored_candidates=candidates,
                filtered_candidates=filtered,
                capped_candidates=capped,
                pre_hard_block_candidates=pre_hard_block_candidates,
                hard_blocked_candidates=hard_blocked_candidates,
                post_hard_block_candidates=top,
                selected_picks=[],
                extra_rejections=_killed_dropped + _earnings_dropped,
            )
        except Exception:
            diagnostics = {
                "pre_hard_block_candidates": [
                    _summarize_candidate_for_report(p) for p in pre_hard_block_candidates
                ],
                "hard_blocked_candidates": hard_blocked_candidates,
                "rejected_candidates": _killed_dropped + _earnings_dropped,
            }
        _write_daily_picks_no_pick_report(reason, pipeline, diagnostics)
        rprint("[yellow]No official picks generated. Valid no-pick diagnostics were written.[/yellow]")
        rprint("[green]Done. No official premarket pick today.[/green]")
        return

    rprint("[5d/6] Auto-tagging trade type (DAY vs SWING)...")
    for p in top:
        ttype = _safe_trade_type_for_pick(p["scores"], pick_date=_today)
        p["trade_type"] = ttype

        # Product guard: intraday news must not silently become a normal
        # multi-day swing pick. Until intraday execution planning is mature,
        # mark these as watch-only instead of actionable swing trades.
        action_window = (
            p.get("news", {}).get("action_window")
            or p.get("scores", {}).get("news_action_window")
        )
        if action_window == "intraday" and ttype == "swing":
            p["watch_only"] = True
            p["watch_only_reason"] = (
                "news action window is intraday; not enough confirmation "
                "for a normal swing entry"
            )
            if "plan" in p and isinstance(p["plan"], dict):
                p["plan"]["watch_only"] = True
                p["plan"]["watch_only_reason"] = p["watch_only_reason"]

        # Also stamp into plan for downstream LLM prompt
        if "plan" in p and isinstance(p["plan"], dict):
            p["plan"]["trade_type"] = ttype
    day_n = sum(1 for p in top if p["trade_type"] == "day")
    swing_n = sum(1 for p in top if p["trade_type"] == "swing")
    rprint(f"  [dim]Tagged: 🔥 {day_n} DAY · ⚡ {swing_n} SWING[/dim]")

    rprint("[5f/6] Applying premarket sanity gate before official logging...")
    pre_sanity_candidates = list(top)
    pipeline["pre_premarket_sanity_pick_count"] = len(pre_sanity_candidates)
    try:
        from src.premarket_sanity_gate import run_premarket_sanity_gate

        top, sanity_blocked, sanity_summary = run_premarket_sanity_gate(pre_sanity_candidates)
        pipeline["premarket_sanity_blocked_count"] = len(sanity_blocked)
        pipeline["post_premarket_sanity_pick_count"] = len(top)
        pipeline["final_pick_count"] = len(top)

        if sanity_blocked:
            rprint(f"  [yellow]⚠ Premarket sanity blocked {len(sanity_blocked)} candidate(s)[/yellow]")
            for item in sanity_blocked:
                rprint(
                    f"    • {item.get('ticker')}: "
                    f"{item.get('action')} — {item.get('reason')}"
                )
        else:
            rprint("  [green]✓ All candidates passed premarket sanity[/green]")

        if not top:
            try:
                from src.candidate_diagnostics import build_candidate_diagnostics
                diagnostics = build_candidate_diagnostics(
                    pipeline=pipeline,
                    scored_candidates=candidates,
                    filtered_candidates=filtered,
                    capped_candidates=capped,
                    pre_hard_block_candidates=pre_hard_block_candidates,
                    hard_blocked_candidates=blocked,
                    post_hard_block_candidates=pre_sanity_candidates,
                    pre_premarket_sanity_candidates=pre_sanity_candidates,
                    premarket_sanity_blocked_candidates=sanity_blocked,
                    selected_picks=[],
                    extra_rejections=_killed_dropped + _earnings_dropped,
                    extra={"premarket_sanity_summary": sanity_summary},
                )
            except Exception:
                diagnostics = {
                    "pre_hard_block_candidates": [
                        _summarize_candidate_for_report(p) for p in pre_hard_block_candidates
                    ],
                    "pre_premarket_sanity_candidates": [
                        _summarize_candidate_for_report(p) for p in pre_sanity_candidates
                    ],
                    "premarket_sanity_blocked_candidates": [
                        {
                            "ticker": item.get("ticker"),
                            "action": item.get("action"),
                            "reason": item.get("reason"),
                            "sanity": item.get("sanity", {}),
                            "candidate": _summarize_candidate_for_report(item.get("candidate", {})),
                        }
                        for item in sanity_blocked
                    ],
                    "premarket_sanity_summary": sanity_summary,
                    "rejected_candidates": _killed_dropped + _earnings_dropped,
                }
            _write_daily_picks_no_pick_report(
                "No official picks generated because all finalists were blocked by the premarket sanity gate.",
                pipeline,
                diagnostics,
            )
            rprint("[yellow]No official picks generated after premarket sanity gate.[/yellow]")
            rprint("[green]Done. No official premarket pick today.[/green]")
            return
    except Exception as e:
        pipeline["premarket_sanity_gate_error"] = str(e)
        pipeline["final_pick_count"] = 0
        diagnostics = {
            "pre_premarket_sanity_candidates": [
                _summarize_candidate_for_report(p) for p in pre_sanity_candidates
            ],
            "premarket_sanity_gate_error": str(e),
        }
        _write_daily_picks_no_pick_report(
            "No official picks generated because the premarket sanity gate failed unexpectedly.",
            pipeline,
            diagnostics,
        )
        rprint(f"[red]Premarket sanity gate failed unexpectedly: {e}[/red]")
        rprint("[green]Done. No official premarket pick today.[/green]")
        return

    rprint("[5g/6] Applying portfolio risk gate before official logging...")
    pre_portfolio_risk_candidates = list(top)
    pipeline["pre_portfolio_risk_pick_count"] = len(pre_portfolio_risk_candidates)
    try:
        from src.portfolio_risk_gate import apply_portfolio_risk_gate, load_open_positions_from_picks_log

        open_positions = load_open_positions_from_picks_log()
        top, risk_blocked, risk_summary = apply_portfolio_risk_gate(
            top,
            cfg,
            existing_positions=open_positions,
        )
        pipeline["portfolio_risk_blocked_count"] = len(risk_blocked)
        pipeline["post_portfolio_risk_pick_count"] = len(top)
        pipeline["final_pick_count"] = len(top)

        if risk_blocked:
            rprint(f"  [yellow]⚠ Portfolio risk gate blocked {len(risk_blocked)} candidate(s)[/yellow]")
            for item in risk_blocked:
                rprint(
                    f"    • {item.get('ticker')}: "
                    f"{item.get('block_type')} — {item.get('reason')}"
                )
        else:
            rprint("  [green]✓ All candidates passed portfolio risk gate[/green]")

        if not top:
            try:
                from src.candidate_diagnostics import build_candidate_diagnostics
                diagnostics = build_candidate_diagnostics(
                    pipeline=pipeline,
                    scored_candidates=candidates,
                    filtered_candidates=filtered,
                    capped_candidates=capped,
                    pre_hard_block_candidates=pre_hard_block_candidates,
                    hard_blocked_candidates=blocked,
                    post_hard_block_candidates=pre_sanity_candidates,
                    pre_premarket_sanity_candidates=pre_sanity_candidates,
                    premarket_sanity_blocked_candidates=sanity_blocked,
                    portfolio_risk_blocked_candidates=risk_blocked,
                    selected_picks=[],
                    extra_rejections=_killed_dropped + _earnings_dropped,
                    extra={
                        "premarket_sanity_summary": sanity_summary,
                        "portfolio_risk_summary": risk_summary,
                        "pre_portfolio_risk_candidates": [
                            _summarize_candidate_for_report(p) for p in pre_portfolio_risk_candidates
                        ],
                    },
                )
                diagnostics["pre_portfolio_risk_candidates"] = [
                    _summarize_candidate_for_report(p) for p in pre_portfolio_risk_candidates
                ]
            except Exception:
                diagnostics = {
                    "pre_portfolio_risk_candidates": [
                        _summarize_candidate_for_report(p) for p in pre_portfolio_risk_candidates
                    ],
                    "portfolio_risk_blocked_candidates": [
                        {
                            "ticker": item.get("ticker"),
                            "block_type": item.get("block_type"),
                            "reason": item.get("reason"),
                            "detail": item.get("detail", {}),
                            "candidate": _summarize_candidate_for_report(item.get("candidate", {})),
                        }
                        for item in risk_blocked
                    ],
                    "portfolio_risk_summary": risk_summary,
                    "rejected_candidates": _killed_dropped + _earnings_dropped,
                }

            _write_daily_picks_no_pick_report(
                "No official picks generated because all finalists were blocked by the portfolio risk gate.",
                pipeline,
                diagnostics,
            )
            rprint("[yellow]No official picks generated after portfolio risk gate.[/yellow]")
            rprint("[green]Done. No official premarket pick today.[/green]")
            return
    except Exception as e:
        pipeline["portfolio_risk_gate_error"] = str(e)
        pipeline["final_pick_count"] = 0
        diagnostics = {
            "pre_portfolio_risk_candidates": [
                _summarize_candidate_for_report(p) for p in pre_portfolio_risk_candidates
            ],
            "portfolio_risk_gate_error": str(e),
        }
        _write_daily_picks_no_pick_report(
            "No official picks generated because the portfolio risk gate failed unexpectedly.",
            pipeline,
            diagnostics,
        )
        rprint(f"[red]Portfolio risk gate failed unexpectedly: {e}[/red]")
        rprint("[green]Done. No official premarket pick today.[/green]")
        return

    rprint("[5h/6] Applying missing-data fail-closed gate before official logging...")
    pre_missing_data_candidates = list(top)
    pipeline["pre_missing_data_pick_count"] = len(pre_missing_data_candidates)
    try:
        from src.missing_data_gate import apply_missing_data_gate

        top, missing_data_blocked, missing_data_summary = apply_missing_data_gate(top)
        pipeline["missing_data_blocked_count"] = len(missing_data_blocked)
        pipeline["post_missing_data_pick_count"] = len(top)
        pipeline["final_pick_count"] = len(top)

        if missing_data_blocked:
            rprint(f"  [yellow]⚠ Missing-data gate blocked {len(missing_data_blocked)} candidate(s)[/yellow]")
            for item in missing_data_blocked:
                rprint(f"    • {item.get('ticker')}: {item.get('reason')}")
        else:
            rprint("  [green]✓ All candidates passed missing-data gate[/green]")

        if not top:
            try:
                from src.candidate_diagnostics import build_candidate_diagnostics
                diagnostics = build_candidate_diagnostics(
                    pipeline=pipeline,
                    scored_candidates=candidates,
                    filtered_candidates=filtered,
                    capped_candidates=capped,
                    pre_hard_block_candidates=pre_hard_block_candidates,
                    hard_blocked_candidates=blocked,
                    post_hard_block_candidates=pre_sanity_candidates,
                    pre_premarket_sanity_candidates=pre_sanity_candidates,
                    premarket_sanity_blocked_candidates=sanity_blocked,
                    portfolio_risk_blocked_candidates=risk_blocked,
                    missing_data_blocked_candidates=missing_data_blocked,
                    selected_picks=[],
                    extra_rejections=_killed_dropped + _earnings_dropped,
                    extra={
                        "premarket_sanity_summary": sanity_summary,
                        "portfolio_risk_summary": risk_summary,
                        "missing_data_summary": missing_data_summary,
                        "pre_portfolio_risk_candidates": [
                            _summarize_candidate_for_report(p) for p in pre_portfolio_risk_candidates
                        ],
                        "pre_missing_data_candidates": [
                            _summarize_candidate_for_report(p) for p in pre_missing_data_candidates
                        ],
                    },
                )
                diagnostics["pre_portfolio_risk_candidates"] = [
                    _summarize_candidate_for_report(p) for p in pre_portfolio_risk_candidates
                ]
                diagnostics["pre_missing_data_candidates"] = [
                    _summarize_candidate_for_report(p) for p in pre_missing_data_candidates
                ]
            except Exception:
                diagnostics = {
                    "pre_missing_data_candidates": [
                        _summarize_candidate_for_report(p) for p in pre_missing_data_candidates
                    ],
                    "missing_data_blocked_candidates": [
                        {
                            "ticker": item.get("ticker"),
                            "block_type": item.get("block_type"),
                            "reason": item.get("reason"),
                            "missing_or_invalid_fields": item.get("missing_or_invalid_fields", []),
                            "required_field_snapshot": item.get("required_field_snapshot", {}),
                            "candidate": _summarize_candidate_for_report(item.get("candidate", {})),
                        }
                        for item in missing_data_blocked
                    ],
                    "missing_data_summary": missing_data_summary,
                    "rejected_candidates": _killed_dropped + _earnings_dropped,
                }

            _write_daily_picks_no_pick_report(
                "No official picks generated because all finalists had missing or malformed required official-pick data.",
                pipeline,
                diagnostics,
            )
            rprint("[yellow]No official picks generated after missing-data gate.[/yellow]")
            rprint("[green]Done. No official premarket pick today.[/green]")
            return
    except Exception as e:
        pipeline["missing_data_gate_error"] = str(e)
        pipeline["final_pick_count"] = 0
        diagnostics = {
            "pre_missing_data_candidates": [
                _summarize_candidate_for_report(p) for p in pre_missing_data_candidates
            ],
            "missing_data_gate_error": str(e),
        }
        _write_daily_picks_no_pick_report(
            "No official picks generated because the missing-data gate failed unexpectedly.",
            pipeline,
            diagnostics,
        )
        rprint(f"[red]Missing-data gate failed unexpectedly: {e}[/red]")
        rprint("[green]Done. No official premarket pick today.[/green]")
        return

    try:
        from src.candidate_diagnostics import build_candidate_diagnostics
        selection_diagnostics = build_candidate_diagnostics(
            pipeline=pipeline,
            scored_candidates=candidates,
            filtered_candidates=filtered,
            capped_candidates=capped,
            pre_hard_block_candidates=pre_hard_block_candidates,
            hard_blocked_candidates=blocked,
            post_hard_block_candidates=pre_sanity_candidates,
            pre_premarket_sanity_candidates=pre_sanity_candidates,
            premarket_sanity_blocked_candidates=sanity_blocked,
            portfolio_risk_blocked_candidates=risk_blocked,
            missing_data_blocked_candidates=missing_data_blocked,
            selected_picks=top,
            extra_rejections=_killed_dropped + _earnings_dropped,
            extra={
                "premarket_sanity_summary": sanity_summary,
                "portfolio_risk_summary": risk_summary,
                "missing_data_summary": missing_data_summary,
                "pre_portfolio_risk_candidates": [
                    _summarize_candidate_for_report(p) for p in pre_portfolio_risk_candidates
                ],
                "pre_missing_data_candidates": [
                    _summarize_candidate_for_report(p) for p in pre_missing_data_candidates
                ],
            },
        )
        selection_diagnostics["pre_portfolio_risk_candidates"] = [
            _summarize_candidate_for_report(p) for p in pre_portfolio_risk_candidates
        ]
        selection_diagnostics["pre_missing_data_candidates"] = [
            _summarize_candidate_for_report(p) for p in pre_missing_data_candidates
        ]
        _write_daily_picks_candidate_diagnostics_report(
            pipeline,
            selection_diagnostics,
            official_premarket_pick=True,
        )
    except Exception as e:
        selection_diagnostics = {}
        rprint(f"[yellow]⚠ candidate diagnostics skipped: {e}[/yellow]")

    rprint("[5i/6] Writing official pick artifacts...")
    try:
        from src.official_pick_artifact import write_official_pick_artifacts

        artifact_summary = write_official_pick_artifacts(
            top,
            pipeline=pipeline,
            candidate_diagnostics=selection_diagnostics,
            regime=reg,
            data_readiness_status=pipeline.get("data_readiness_status") or "ready",
            provider_status="healthy",
            market_session_status="premarket",
        )
        if artifact_summary.get("validation_errors"):
            pipeline["official_pick_artifact_validation_errors"] = artifact_summary["validation_errors"]
            _write_daily_picks_no_pick_report(
                "No official picks generated because official pick artifact validation failed.",
                pipeline,
                {
                    "selected_picks": [
                        _summarize_candidate_for_report(p) for p in top
                    ],
                    "artifact_validation_errors": artifact_summary["validation_errors"],
                    "artifact_summary": artifact_summary,
                },
            )
            rprint("[red]Official pick artifact validation failed; no official picks will be logged.[/red]")
            rprint("[green]Done. No official premarket pick today.[/green]")
            return

        official_artifact_trace = {
            item.get("ticker"): item
            for item in artifact_summary.get("artifacts", [])
            if isinstance(item, dict) and item.get("ticker")
        }
        for pick in top:
            trace = official_artifact_trace.get(str(pick.get("ticker") or "").strip().upper())
            if trace:
                pick["official_decision_id"] = trace.get("decision_id", "")
                pick["official_artifact_id"] = trace.get("artifact_id", "")
                pick["official_artifact_path"] = trace.get("path", "")
                pick["official_contract_version"] = trace.get("contract_version", "")
        rprint(f"  [green]✓ Wrote {artifact_summary.get('official_pick_count', 0)} official pick artifact(s)[/green]")
    except Exception as e:
        pipeline["official_pick_artifact_error"] = str(e)
        _write_daily_picks_no_pick_report(
            "No official picks generated because official pick artifact generation failed unexpectedly.",
            pipeline,
            {
                "selected_picks": [
                    _summarize_candidate_for_report(p) for p in top
                ],
                "official_pick_artifact_error": str(e),
            },
        )
        rprint(f"[red]Official pick artifact generation failed unexpectedly: {e}[/red]")
        rprint("[green]Done. No official premarket pick today.[/green]")
        return

    rprint(f"\n[6/6] {len(candidates)} candidates -> {len(top)} final official picks\n")

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
        if _should_log_paper_trade():
            log_paper_trade(p, cfg["output"]["csv_path"].replace("picks","trades"))

    # ===== Log picks (now includes trade_type) =====
    try:
        # 💎 Apply monster treatment (overrides SL/TP/qty for high-conviction picks)
        try:
            _mcfg = cfg.get("monster", {})
            if _mcfg.get("enabled", True):
                _mthr = _mcfg.get("threshold", 0.60)
                _macct = cfg.get("risk", {}).get("account_size", 10000.0)
                _mpos = _mcfg.get("position_pct", 1.5)
                _monsters = 0
                for _p in top:
                    _ms = _p["scores"].get("monster_score", 0) or 0
                    if _ms >= _mthr:
                        _pdict = {
                            "ticker": _p["ticker"],
                            "entry": _p["plan"].get("entry"),
                            "stop_loss": _p["plan"].get("stop_loss"),
                            "take_profit": _p["plan"].get("take_profit"),
                            "qty": _p["plan"].get("quantity"),
                        }
                        _treated = apply_monster_treatment(_pdict, _ms, _macct, _mpos)
                        _p["plan"]["stop_loss"] = _treated["stop_loss"]
                        _p["plan"]["take_profit"] = _treated["take_profit"]
                        _p["plan"]["quantity"] = _treated["qty"]
                        _p["plan"]["risk_reward"] = _treated["risk_reward"]
                        _p["is_monster"] = True
                        _monsters += 1
                if _monsters:
                    rprint(f"[bold magenta]💎 {_monsters} MONSTER pick(s) — wider SL, +25% TP, lottery sizing[/bold magenta]")
        except Exception as _e:
            rprint(f"[yellow]⚠ monster treatment skipped: {_e}[/yellow]")

        picks_for_log = []
        # Bug #8/#10: sector benchmark — fetch each ETF close once, with SPY
        # fallback when the sector ETF quote is unavailable.
        try:
            _sector_cache = {}
            for _p in top:
                _cache_key = (
                    _p.get("info_short", {}).get("sector", ""),
                    _p.get("scores", {}).get("sector_tag") or "",
                )
                if _cache_key not in _sector_cache:
                    _sector_cache[_cache_key] = _sector_benchmark_for_pick(_p)
                _p["_sector_etf"], _p["_sector_close"] = _sector_cache[_cache_key]
        except Exception as _se:
            rprint(f"[yellow]⚠ sector benchmark fetch skipped: {_se}[/yellow]")

        for p in top:
            brain = p.get("brain", {}) or {}

            # Bug #17A (2026-05-05): persist smell faculty verdicts for
            # enforcement-readiness learning. Compact pipe-separated strings
            # keep CSV readable while preserving all observe-mode warnings.
            _smells = p.get("smell_warnings") or []
            _smell_codes = "|".join(str(x.get("code", "")) for x in _smells if isinstance(x, dict))
            _smell_severities = "|".join(str(x.get("severity", "")) for x in _smells if isinstance(x, dict))
            _smell_messages = "|".join(
                str(x.get("message", "")).replace("|", "/")
                for x in _smells if isinstance(x, dict)
            )

            # Bug #8b (2026-05-05): dict.get(key, default) returns None when
            # key exists with None value (cache miss / fetch failure). Use
            # `or default` to coerce None → fallback. Otherwise None propagates
            # to csv.DictWriter which writes empty string, killing sector alpha.
            _setf = p.get("_sector_etf") or "SPY"
            _sclose = p.get("_sector_close") or ""
            picks_for_log.append({
                "ticker": p["ticker"],
                "company": p.get("info_short", {}).get("name", ""),
                "tag": p["scores"].get("sector_tag") or "",
                "trade_type": p.get("trade_type") or "swing",  # Bug #14: coerce None
                "watch_only": p.get("watch_only") or False,
                "watch_only_reason": p.get("watch_only_reason") or "",
                "news_action_window": (
                    p.get("news", {}).get("action_window")
                    or p.get("scores", {}).get("news_action_window")
                    or ""
                ),
                "official_decision_id": p.get("official_decision_id", ""),
                "official_artifact_id": p.get("official_artifact_id", ""),
                "official_artifact_path": p.get("official_artifact_path", ""),
                "official_contract_version": p.get("official_contract_version", ""),
                "score": p["scores"].get("composite") or 0,  # Bug #14: coerce None
                "multiplier": p["scores"].get("sector_mult") or 1.0,  # Bug #14
                "entry": p["plan"].get("entry"),
                "stop_loss": p["plan"].get("stop_loss"),
                "take_profit": p["plan"].get("take_profit"),
                "risk_reward": p["plan"].get("risk_reward") or 2.0,  # Bug #14
                "qty": p["plan"].get("quantity") or 0,  # Bug #14: coerce None
                "days_to_earnings": p.get("days_to_earnings"),
                # PILLAR 1 audit fields (May 2 2026)
                "brain_p_win": brain.get("p_win"),
                "brain_ev_pct": brain.get("ev_pct"),
                "brain_sl": brain.get("brain_sl"),
                "brain_tp": brain.get("brain_tp"),
                "brain_confidence": brain.get("confidence"),
                "vol_ratio": p["scores"].get("vol_ratio"),
                # 💎 Monster Hunt audit
                "monster_score": p["scores"].get("monster_score") or 0,  # Bug #14
                "is_monster": p.get("is_monster") or p["scores"].get("is_monster") or False,  # Bug #16: preserve root flag
                # Smell Faculty audit (Bug #17A)
                "smell_codes": _smell_codes,
                "smell_severities": _smell_severities,
                "smell_messages": _smell_messages,
                # Sector benchmark (T3 May 3 2026)
                "sector_etf": _setf,
                "sector_close": _sclose,
            })
        n = log_picks(picks_for_log, reg, cape if "cape" in dir() else None)
        # Pillar 1 Layer 4: signal journal (append signals + bucketed view)
        # HARDENED 2026-05-04: per-pick try/except + LOUD errors.
        # Previous batch try/except silently swallowed all picks if ONE failed.
        # Brain operated blind 2026-05-02 to 2026-05-04 due to silent failure.
        _regime_str = (reg or {}).get("regime") or "unknown"
        _journal_logged = 0
        _journal_errors = 0
        for _p in top:
            try:
                _scores = _p.get("scores", {}) or {}
                _row = {
                    "ticker":           _p.get("ticker"),
                    "scores":           _scores,
                    "brain":            _p.get("brain", {}) or {},
                    "regime":           _regime_str,
                    "trade_type":       _p.get("trade_type", "swing"),
                    "days_to_earnings": _p.get("days_to_earnings"),
                    "vol_ratio":        _scores.get("vol_ratio"),
                    "tag":              _scores.get("sector_tag"),
                }
                _journal_log_pick(_row, regime=_regime_str)
                _journal_logged += 1
            except Exception as _je:
                _journal_errors += 1
                import traceback
                rprint(f"[red]🚨 signal_journal FAILED for {_p.get('ticker','?')}: {_je}[/red]")
                rprint(f"[red]{traceback.format_exc()}[/red]")
        if _journal_logged > 0:
            rprint(f"[green][journal] Logged {_journal_logged}/{len(top)} picks to signal_journal.jsonl[/green]")
        if _journal_errors > 0:
            rprint(f"[red][journal] ⚠ {_journal_errors} picks FAILED to journal — brain will learn from incomplete data[/red]")

        # Pillar 4: pause signal + auto-trigger if enforced
        try:
            _pause = _pause_score()
            rprint("")
            for _line in _pause_fmt(_pause).split("\n"):
                _clean = _line.replace("*", "")
                rprint(f"[dim]{_clean}[/dim]")

            # Auto-pause if config.enforced AND score >= threshold
            _new = _maybe_pause(_pause)
            if _new:
                rprint(f"[red]🚨 AUTO-PAUSE TRIGGERED — agent paused until {_new['until']}[/red]")
        except Exception as _pe:
            rprint(f"[yellow]⚠ pause_signal calc skipped: {_pe}[/yellow]")
        if n == 0 and len(picks_for_log) > 0:
            rprint(f"[yellow][log] All {len(picks_for_log)} picks already logged earlier today (dedup) — none added[/yellow]")
        else:
            rprint(f"[dim][log] Saved {n}/{len(picks_for_log)} picks to data/picks_log.csv[/dim]")
    except Exception as e:
        rprint(f"[red][log] Could not save picks: {e}[/red]")

    rprint("[green]Done. Review picks before any real-money action.[/green]")


if __name__ == "__main__":
    run()
