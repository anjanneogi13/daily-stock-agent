# Daily Stock Agent — Project Blueprint

**Last updated:** 2026-05-06
**Status:** monitoring-ready, not paper-trading-ready, not live-execution-ready
**Test suite:** 1284 passed, 28 skipped
**Mode:** monitoring-only

## Purpose

This is the canonical source of truth for architecture, current state, roadmap, features, known gaps, and operating policy.

## Current State

The repo is healthy for monitoring mode:

- CI is green.
- Main workflows are present.
- Core data-quality audits are green.
- Recent persistence and Telegram dedup bugs are fixed.
- Daily-picks timing hard gate is implemented.
- Stale/unverified premarket prices become watch-only instead of actionable.
- Intraday news cannot silently become normal swing picks; it is marked watch-only until intraday planning matures.
- Closed-status logic is aligned between enforcement and monitoring readiness dashboards.
- Legacy local paper logging is opt-in only and disabled by default.
- Major undercovered modules now have tests.
- Paper trading remains intentionally deferred.

The agent may recommend, monitor, explain, evaluate, report, and learn.

The agent must not execute real-money trades or paper trades yet.

## Safety Gates

Paper trading stays blocked until post-floor closed outcomes clear:

| Bucket | Required win rate | Extra gate |
|---|---:|---|
| Day trades | >60% | positive expectancy |
| Swing trades | >66% | positive expectancy |
| Monster / long-holder picks | >90% | positive expectancy |

Authority:

- `python scripts/monitoring_readiness.py`
- `python scripts/check_enforcement_readiness.py`

Do not manually flip:

- `SMELL_ENFORCE`
- `BRAIN_ENFORCE_EV`
- `AUTO_PAUSE_ENABLED`

## Architecture

Core pipeline:

1. Universe selection
2. Data fetch
3. Scoring
4. Pattern/news/regime/wisdom enrichment
5. Hard blocks and risk checks
6. Pick logging
7. Telegram send
8. Intraday monitoring
9. Evaluation
10. Journal updates
11. Learning/calibration
12. Reports and audits

Key areas:

| Area | Modules |
|---|---|
| Brain / scoring | `parallel_scorer.py`, `scorer.py`, `probability_engine.py` |
| Risk / heart | `risk_manager.py`, `weight_applier.py`, `auto_pause.py`, `hard_blocks.py` |
| Sight / patterns | `pattern_engine.py`, `pattern_layer.py`, `src/patterns/` |
| Hearing / news | `news_engine.py`, `news_signals.py`, `market_news.py`, `llm_agent.py`, `watchlist_manager.py`, `data/watchlist.json` |
| Touch / regime | `regime.py`, `market_guard.py`, `market_calendar.py` |
| Learning | `learning_journal.py`, `signal_journal.py`, `calibration.py`, `weight_proposer.py` |
| Wisdom | `wisdom_base.py`, `wisdom_hint.py`, `wisdom_consultant.py` |
| Tactical sixth sense | `hypothesis_engine.py` |
| Monitoring | `position_monitor.py`, `scripts/intraday_monitor.py` |
| Audit | `scripts/full_repo_audit.py`, `scripts/audit_*`, readiness scripts |

## Implemented Features

- Daily stock picks.
- Telegram recommendations.
- Intraday monitoring.
- Outcome evaluation.
- Layman reporting.
- Learning journals.
- Signal journals.
- Pattern engine.
- News/watchlist engine.
- Wisdom base.
- Hypothesis engine.
- Calibration and weight proposal.
- Agent memoir.
- Hard blocks.
- Smell faculty.
- Data-quality audits.
- Monitoring and enforcement readiness dashboards.

## Current Known Gaps

These are not urgent blockers:

1. Tracked-data test isolation is clean as of 2026-05-06:
   - `data/learning_journal.jsonl` side effects fixed.
   - `data/picks_log.csv` audited clean.
   - `data/signal_journal.jsonl` audited clean.
2. Remaining undercovered modules:
   - `performance_stats`
   - `paper_trader`
   - `picks_csv`
   - `monster_data`
   - `cape_ratio`
3. Closed-status logic should be aligned between readiness scripts.
4. Backtester exists but needs hardening.

## Reserved / Inactive Schema

Tiered exit fields are reserved schema only:

- `tp1`
- `tp2`
- `qty_t1`
- `qty_t2`
- `qty_t3`
- `tier_status`

They are not active scale-out execution logic.

## Roadmap

Immediate next work:

1. Audit remaining test/data isolation for `picks_log.csv` and `signal_journal.jsonl`.
2. Add tests for `performance_stats`.
3. Add tests for smaller modules.
4. Add tests for smaller modules.
5. Harden backtester.
6. Build opening-range intraday scanner.

Planned future features:

1. Backtester hardening.
2. Faculty reachability audit.
3. Hearing LLM integration.
4. Curiosity engine.
5. Reader engine.
6. Historical regime engine.
7. Proactive smell.
8. Deferred power-user features:
   - Telegram inline buttons.
   - Sector rotation alerts.
   - Earnings-week awareness.
   - Premarket gap awareness.
   - Adaptive Kelly-light sizing.
   - Backtest rerunner.
   - Read-only dashboard.

## Agent Maturity / Intelligence Roadmap

The project now tracks real-world trading intelligence maturity in `docs/AGENT_MATURITY_TRACKER.md`.

Key maturity lanes:

1. Premarket swing picks.
2. Intraday opportunities.
3. Monster hunt / long-term compounders.

Major roadmap additions:

- Premarket timing hard gate.
- Price freshness / stale-entry protection.
- News action-window enforcement.
- Opening-range intraday scanner.
- Fundamental-quality and pump-risk smell.
- Monster-hunt thesis engine.
- Quarterly/yearly P&L and earnings analyzer.
- Reader/wisdom ingestion from legal market-learning sources.
- Historical regime learning.
- Historical chart and pattern replay learning.

These features remain monitoring-only until tested and readiness gates approve promotion.

## Documentation Policy

Use these canonical docs:

| File | Purpose |
|---|---|
| `docs/PROJECT_BLUEPRINT.md` | Architecture, current state, feature inventory, roadmap |
| `docs/WORK_LOG.md` | Append-only record of every meaningful change |
| `docs/NEXT_SESSION.md` | Daily next-session handoff |
| `docs/AGENT_MATURITY_TRACKER.md` | Trading intelligence maturity, daily lessons, and future learning roadmap |

After every bug fix, feature, or process change:

1. Update `docs/WORK_LOG.md`.
2. Update `docs/NEXT_SESSION.md`.
3. Update this file if architecture/current state/roadmap changed.
4. Keep CI green.
