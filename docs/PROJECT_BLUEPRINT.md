# Daily Stock Agent — Project Blueprint

**Last updated:** 2026-05-08
**Status:** monitoring-ready, not paper-trading-ready, not live-execution-ready
**Test suite:** 1561 passed, 30 skipped
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
- Daily-picks workflow reliability was hardened with frequent guarded premarket attempts and pre-cutoff watchdog alerts.
- Daily-picks run-status artifacts record workflow/watchdog outcomes for operational learning.
- Late watch-only daily ideas preserve learning evidence after missed official premarket windows without polluting official pick stats.
- Stale/unverified premarket prices become watch-only instead of actionable.
- Intraday news cannot silently become normal swing picks; it is marked watch-only until intraday planning matures.
- Closed-status logic is aligned between enforcement and monitoring readiness dashboards.
- Minor documentation consistency cleanup completed on 2026-05-06.
- Legacy local paper logging is opt-in only and disabled by default.
- Major undercovered modules now have tests.
- Paper trading remains intentionally deferred.
- Paper trading activation checklist added on 2026-05-06.
- Intraday Monitor force-adds intended runtime artifacts under ignored `data/` so operational evidence persists from GitHub Actions.
- Opening-range run-status artifacts record whether the intraday/opening-range scanner ran, skipped, completed, found candidates, wrote observations, and sent/skipped Telegram.
- Missed-window Telegram and late watch-only ideas are sent as one combined warning message.
- Late watch-only daily ideas now include quote-enriched watch-only BUY/Entry, SL, TP, and R/R levels after missed official premarket windows.
- Opening-range observation collection has begun; 4 watch-only observations existed after the 2026-05-06 session, all safety-compliant.
- Watch-only learning report v1 inventories late daily ideas, opening-range observations, and intraday dedupe fingerprints without touching official pick stats.
- Intraday momentum watch-only observations are now persisted structurally for future watch-only outcome learning.
- News Engine run-status artifacts now record fetch/classify/signal/watchlist counts for schedule observability.
- News Engine now uses a 120-minute default lookback, configurable via `NEWS_LOOKBACK_MINUTES`, and records the lookback in run-status artifacts.
- News Signal Evidence Report inventories news logs, active signals, watchlist, run status, late ideas, and official pick news fields without mutating stats.
- News signal outcome attribution scaffold can evaluate 1D/3D future returns for news evidence while preserving monitoring-only safety.
- News Signal Evidence Report now includes optional news signal outcome summaries when `data/news_signal_outcomes_YYYY-MM-DD.jsonl` exists.
- News Evidence workflow can generate outcome/report artifacts after market close while preserving monitoring-only safety.
- News Evidence workflow keeps compact Markdown/outcome artifacts in git and uploads the larger JSON report as a short-retention workflow artifact.
- Late watch-only Telegram dedupe prevents repeated fallback sends for the same ET date unless forced manually.
- Late watch-only copy avoids action-like BUY wording and suppresses unresolved ticker/entity ideas.
- New intraday opportunity Telegram pushes are suppressed after 15:15 ET to avoid late-day chase/overnight-risk alerts.
- Intraday Telegram copy uses observed/reference-level wording rather than implying executable entries.
- Official daily OHLCV now has a Stooq fallback behind yfinance for the Daily Picks data-fetch path.
- News signals fade bullish boosts into small penalties when headlines indicate negative market reaction.
- Monster Hunter / Long-Term Compounder Analyst architecture is documented as a research-only, monitoring-only future lane in `docs/strategy/MONSTER_HUNTER_DESIGN.md`.
- Product failure modes, mitigations, and market win strategy are documented in `docs/strategy/PRODUCT_FAILURE_AND_WIN_STRATEGY.md`.
- Planning documentation now separates future backlog, data contracts, notification architecture, and candidate lifecycle rules under `docs/planning/`.
- Import-time side effects in intraday Telegram sender and intraday monitor tests are isolated; full-suite tests no longer mutate tracked opening-range run-status artifacts.

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

## Product Architecture Roadmap

The canonical product vision and remaining roadmap live in:

- `docs/planning/PRODUCT_ARCHITECTURE_ROADMAP.md`

This roadmap documents the intended multi-strategy stock intelligence system, including:

- premarket official daily picks,
- post-open daily opportunities,
- intraday picks,
- monster hunter,
- consistent compounders,
- long-term opportunities,
- performance, execution, and x-ray reports,
- missed-opportunity analysis,
- no-pick intelligence,
- market regime awareness,
- chart and technical analysis,
- book/research learning,
- historical backtesting,
- walk-forward validation,
- risk management,
- paper/live execution promotion gates,
- explainability, auditability, and strategy versioning.

Safety remains unchanged: observe-only is the default until explicit strategy, risk, reporting, and execution gates pass.


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
3. Closed-status logic is aligned between readiness scripts as of 2026-05-06.
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

1. Keep paper/live trading disabled.
2. Continue monitoring the next market-day Daily Stock Picks schedule:
   - official picks before 09:20 ET, or
   - combined missed-window late watch-only message after cutoff.
3. Continue reviewing Intraday Monitor / opening-range scheduled runs and status artifacts.
4. Next product feature candidate: watch-only learning evidence layer so late daily ideas, intraday monitor ideas, and opening-range observations can be evaluated separately from official picks.
5. Next opening-range feature candidate: bar artifact capture for future outcome/backtest joins.
6. Continue adding tests for undercovered smaller modules and hardening backtest tooling.

Planned future features:

1. Backtester hardening.
2. Faculty reachability audit.
3. Hearing LLM integration.
4. Curiosity engine.
5. Reader engine.
6. Historical regime engine.
7. Proactive smell.
8. Monster Hunter / Long-Term Compounder Analyst:
   - 6-month to 5-year research lane,
   - secular theme radar,
   - full fundamental and P&L analysis,
   - ETF/mutual fund/institutional focus analysis,
   - thesis state machine,
   - research-only reports before any scoring influence.
9. Deferred power-user features:
   - Telegram inline buttons.
   - Sector rotation alerts.
   - Earnings-week awareness.
   - Premarket gap awareness.
   - Adaptive Kelly-light sizing.
   - Backtest rerunner.
   - Read-only dashboard.

## Agent Maturity / Intelligence Roadmap

The project now tracks real-world trading intelligence maturity in `docs/strategy/AGENT_MATURITY_TRACKER.md`.

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
| `docs/strategy/AGENT_MATURITY_TRACKER.md` | Trading intelligence maturity, daily lessons, and future learning roadmap |
| `docs/strategy/MONSTER_HUNTER_DESIGN.md` | Long-term compounder / monster-stock research architecture |
| `docs/strategy/PRODUCT_FAILURE_AND_WIN_STRATEGY.md` | Product failure modes, mitigations, and market win strategy |
| `docs/playbook/NEWS_EVIDENCE_REPORTS.md` | Operator playbook for News Evidence workflow and manual report generation |
| `docs/planning/README.md` | Planning documentation index |
| `docs/planning/FEATURE_BACKLOG.md` | Long-term feature backlog and implementation phases |
| `docs/planning/DATA_CONTRACTS.md` | Data artifact contracts, ownership rules, and safety boundaries |
| `docs/planning/NOTIFICATION_ARCHITECTURE.md` | Notification classifications, wording rules, and shared sender design |
| `docs/planning/CANDIDATE_LIFECYCLE.md` | Candidate states, transitions, readiness gates, and anti-corruption rules |

After every bug fix, feature, or process change:

1. Update `docs/WORK_LOG.md`.
2. Update `docs/NEXT_SESSION.md`.
3. Update this file if architecture/current state/roadmap changed.
4. Update relevant `docs/planning/` files if future design, data contracts, notification rules, or candidate lifecycle rules changed.
5. Keep CI green.

Session handoff for 2026-05-08 is documented in `docs/sessions/SESSION_HANDOFF_2026-05-08.md`.

## 2026-05-08 Daily Picks reliability addendum

Daily Picks now treats zero official picks as an explainable monitored event, not a silent success.

Reliability additions:
- No-pick reports classify the primary no-pick cause.
- Candidate rejection artifacts explain pre-hard-block and hard-blocked finalists.
- Failed-run recovery persists market-data health and hard-block evidence.
- Official Daily Picks reduces yfinance pressure by disabling heavy full-info calls in workflow context.
- `monster_data` enrichment is opt-in by default to prevent Monster Hunter research plumbing from destabilizing official Daily Picks.
- Stooq fallback rejects unsupported exchange-prefixed symbols conservatively instead of creating parser-error noise.

Product rule:
- The agent must not force a pick to look useful.
- The agent must clearly explain when it found candidates but rejected them.
- Trust is improved by explainable no-pick discipline, not by lowering standards.

## Active Product-Intelligence Repair Plan

The active product-intelligence repair roadmap is documented in:

- `docs/planning/PRODUCT_INTELLIGENCE_REPAIR_PLAN.md`

This plan prioritizes official no-pick explainability, watch-only outcome attribution, performance-source separation, late-news score calibration, opening-range quality evaluation, dynamic theme discovery, and observe-only theme-to-pick analysis before any paper trading, live trading, or production theme-aware scoring.

## Multi-lane product architecture checkpoint

The product is evolving into a monitoring-first, multi-lane stock intelligence system. The canonical architecture note is:

- `docs/strategy/MULTI_LANE_PRODUCT_ARCHITECTURE.md`

Key current interpretation:

- Lane 1 is the premarket official daily decision lane.
- Lane 1 accepts either a validated official pick or a validated official no-pick.
- Lane 1 is code-complete / pre-cert ready, but still awaiting Priority 19 real scheduled-run certification.
- Lane 2 should be introduced as a post-open watch-only opportunity lane, not as official after-open picks.
- Intraday/opening-range, Monster Hunter, compounder, long-term opportunity, and future learning systems must remain separate until independently validated.
- Paper trading and live trading remain forbidden until explicit readiness gates pass and founder approval is given.
