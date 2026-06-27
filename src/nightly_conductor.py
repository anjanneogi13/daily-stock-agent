"""T50 — Nightly Brain Maintenance Conductor.

Single orchestrator that runs every brain self-improvement step in the
correct order, each wrapped in try/except so one failure can't break the
chain. Emits a structured summary to learning_journal.

ORDER MATTERS:
  1. Pattern engine universe scan       → data/patterns.jsonl
  2. Pattern stats aggregator           → data/pattern_stats.json
  3. Pattern auto_enable_disable        → kill bad patterns, reactivate
  4. Calibration + weight_proposer      → propose tweaks based on accuracy
  5. Weight applier                     → apply under 5%/wk safe cap
  6. Auto-promote consistent patterns   → patterns → wisdom lessons
  7. Lesson GC                          → drop stale lessons
  8. Emit summary                       → learning_journal "nightly_brain_run"
"""
from __future__ import annotations
import csv
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


WATCHLIST_PATH = Path("data/watchlist.json")
PICKS_LOG      = Path("data/picks_log.csv")


def _step(name: str, fn, summary: Dict) -> None:
    """Run one step, capture result or error into summary."""
    try:
        result = fn() or {}
        summary["steps"][name] = {"ok": True, "result": result}
    except Exception as e:
        summary["steps"][name] = {
            "ok": False,
            "error": f"{type(e).__name__}: {e}",
            "traceback": traceback.format_exc().splitlines()[-3:],
        }


def _load_universe_for_scan(max_tickers: int = 100) -> List[str]:
    """Use bullish-news watchlist + recent pick tickers as scan universe.
    Avoids slamming yfinance with full 5000-ticker scan nightly.
    """
    out = set()
    # 1. Watchlist tickers
    if WATCHLIST_PATH.exists():
        try:
            wl = json.loads(WATCHLIST_PATH.read_text())
            for it in wl.get("items", []):
                t = it.get("ticker")
                if t: out.add(str(t).upper())
        except Exception:
            pass
    # 2. Recent picks (last 30d)
    if PICKS_LOG.exists():
        try:
            with PICKS_LOG.open() as f:
                for r in csv.DictReader(f):
                    t = r.get("ticker")
                    if t: out.add(str(t).upper())
        except Exception:
            pass
    return sorted(out)[:max_tickers]


# ═══════════════════════════════════════════════════════════════
# Step implementations
# ═══════════════════════════════════════════════════════════════
def _step_pattern_scan(tickers: Optional[List[str]] = None,
                       max_tickers: int = 100) -> Dict:
    from src.pattern_engine import scan_ticker, persist
    from src.regime import market_regime
    regime = (market_regime() or {}).get("regime", "unknown")
    tickers = tickers or _load_universe_for_scan(max_tickers=max_tickers)
    all_matches = []
    for t in tickers:
        ms = scan_ticker(t, regime=regime)
        all_matches.extend(ms)
    n = persist(all_matches) if all_matches else 0
    return {"tickers_scanned": len(tickers), "matches_found": len(all_matches),
            "matches_persisted": n, "regime": regime}


def _step_pattern_stats() -> Dict:
    from src import pattern_stats as ps
    stats = ps.build_stats()
    ps.save(stats)
    n_patterns = sum(1 for k in stats if not k.startswith("_"))
    return {"patterns_with_stats": n_patterns}


def _step_pattern_auto_enable_disable() -> Dict:
    from src.pattern_layer import auto_enable_disable
    res = auto_enable_disable()
    return {"disabled": res.get("disabled", []),
            "reactivated": res.get("reactivated", [])}


def _step_calibration_propose() -> Dict:
    """Run calibration → generate proposals from per-factor accuracy."""
    from src import calibration as cal
    from src import weight_proposer as wp
    if not PICKS_LOG.exists():
        return {"skipped": "no picks_log"}
    with PICKS_LOG.open() as f:
        rows = [r for r in csv.DictReader(f) if r.get("r_multiple") not in (None, "")]
    if len(rows) < 10:
        return {"skipped": f"only {len(rows)} closed picks (need 10)"}
    # Build per-factor report → proposals
    try:
        report = cal.per_factor_report(rows)
    except Exception:
        return {"skipped": "calibration.per_factor_report failed"}
    run_id = f"nightly_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    proposals = wp.propose(report, run_id=run_id) if report else []
    n = wp.write_proposals(proposals) if proposals else 0
    return {"factors_analyzed": len(report), "proposals_written": n,
            "run_id": run_id}


def _step_weight_apply() -> Dict:
    from src.weight_applier import apply_proposals
    res = apply_proposals(dry_run=False)
    def _count(v):
        if v is None: return 0
        if isinstance(v, int): return v
        try: return len(v)
        except TypeError: return 0
    return {
        "applied":         _count(res.get("applied")),
        "skipped_capped":  _count(res.get("skipped_capped")),
        "skipped_invalid": _count(res.get("skipped_invalid")),
    }


def _step_auto_promote() -> Dict:
    from src.auto_promote import promote_patterns
    res = promote_patterns()
    if isinstance(res, list):
        return {"promoted": len(res)}
    return {"promoted": res.get("promoted", 0) if isinstance(res, dict) else 0}


def _step_lesson_gc() -> Dict:
    from src.lesson_gc import gc_stale
    res = gc_stale()
    if isinstance(res, list):
        return {"gc_removed": len(res)}
    if isinstance(res, dict):
        return {"gc_removed": res.get("removed", 0)}
    return {"gc_removed": 0}


# ═══════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════
def _step_agent_memoir() -> Dict:
    """Step 8 (added 2026-05-04): regenerate agent's self-portrait."""
    from experimental.agent_memoir import write_memoir
    m = write_memoir()
    return {
        "lifetime_trades": m["lifetime_stats"]["closed_trades"],
        "win_rate":        m["lifetime_stats"]["win_rate"],
        "has_biggest_win": m["biggest_win"] is not None,
        "has_biggest_loss": m["biggest_loss"] is not None,
    }


def run_nightly(scan_tickers: Optional[List[str]] = None,
                deep_mode: Optional[bool] = None) -> Dict:
    """Run the full nightly brain maintenance cycle. Returns summary dict.

    deep_mode=True triggers extended scan (used on weekends/holidays when
    no morning picks need to be scored — brain has spare capacity).
    If None, auto-detects from today's market status.
    """
    summary: Dict = {
        "ts": datetime.now().isoformat(),
        "steps": {},
    }

    # 🗓 T51 — Auto-detect deep mode based on market status
    if deep_mode is None:
        try:
            from src.market_calendar import is_trading_day, market_status_today
            deep_mode = not is_trading_day()
            summary["market_status"] = market_status_today()
        except Exception:
            deep_mode = False
    summary["deep_mode"] = deep_mode

    # On deep-mode days (market closed), scan a much larger universe
    _scan_count = 300 if deep_mode else 100
    _step("pattern_scan",
          lambda: _step_pattern_scan(scan_tickers, max_tickers=_scan_count),
          summary)
    _step("pattern_stats",      _step_pattern_stats, summary)
    _step("pattern_auto_e_d",   _step_pattern_auto_enable_disable, summary)
    _step("calibration_propose",_step_calibration_propose, summary)
    _step("weight_apply",       _step_weight_apply, summary)
    _step("auto_promote",       _step_auto_promote, summary)
    _step("lesson_gc",          _step_lesson_gc, summary)
    _step("agent_memoir",       _step_agent_memoir, summary)

    # Emit single nightly_brain_run event
    try:
        from src import learning_journal as lj
        ok = sum(1 for s in summary["steps"].values() if s.get("ok"))
        fail = len(summary["steps"]) - ok
        lj.log("nightly_brain_run",
               steps_ok=ok, steps_failed=fail,
               summary={k: v.get("result") if v.get("ok") else "FAIL"
                        for k, v in summary["steps"].items()})
    except Exception:
        pass

    summary["ok_count"]   = sum(1 for s in summary["steps"].values() if s.get("ok"))
    summary["fail_count"] = sum(1 for s in summary["steps"].values() if not s.get("ok"))
    return summary


def format_summary_text(summary: Dict) -> str:
    """Plain-text representation for logs / CI output."""
    lines = [f"🧠 Nightly Brain Run — {summary.get('ts','')}"]
    lines.append(f"   ✅ {summary.get('ok_count',0)} ok · ❌ {summary.get('fail_count',0)} failed")
    lines.append("")
    for name, step in summary.get("steps", {}).items():
        icon = "✅" if step.get("ok") else "❌"
        if step.get("ok"):
            lines.append(f"   {icon} {name}: {step.get('result')}")
        else:
            lines.append(f"   {icon} {name}: {step.get('error')}")
    return "\n".join(lines)
