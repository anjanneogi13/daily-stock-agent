# Premarket Official Pick Production Plan

**Last updated:** 2026-05-09  
**Product lane:** Lane 1 — Premarket Official Daily Stock Pick  
**Current maturity:** alpha / monitoring-ready, not production-ready  
**Estimated readiness:** 4.5 / 10  
**Safety posture:** observe-only / monitoring-first until explicit production gates pass

---

## Purpose

This document is the canonical production-readiness plan for Lane 1: the premarket official daily stock pick.

The goal is to finish this lane completely before moving to the next product lane.

Lane 1 should eventually produce a trusted official premarket stock pick or a trusted official no-pick decision before market open.

The system must be safe, explainable, auditable, testable, and validated before being considered production-ready.

---

## Product Definition

Lane 1 is responsible for producing an official premarket decision before the market opens.

The decision can be:

- official pick available,
- official no-pick because conditions are unsafe,
- official no-pick because data readiness failed,
- official no-pick because no qualified candidate passed gates,
- official no-pick because the market is closed or the premarket window was missed.

Important principle:

A no-pick day can be correct. No-pick must be treated as a first-class decision, not as an absence of output.

---

## Current Readiness Summary

Current status:

- operationally runnable,
- scheduled through GitHub Actions,
- capable of generating and logging picks,
- capable of sending GitHub issue and Telegram output,
- has post-market evaluation,
- has some diagnostics,
- has improving provider/readiness artifacts,
- not yet production-ready.

Estimated readiness:

- 4.5 / 10,
- about 40–50 percent complete.

Current maturity:

- alpha,
- monitoring-ready,
- not production-ready,
- not paper-trading-ready,
- not live-trading-ready.

---

## What Is Already Implemented

### Scheduled premarket workflow

Implemented in:

- `.github/workflows/daily-picks.yml`

Current behavior:

- scheduled weekday attempts during the premarket window,
- official premarket timing guard,
- duplicate same-day run guard,
- test execution before running the agent,
- runs `main.py`,
- verifies `data/picks_log.csv`,
- commits artifacts,
- formats picks,
- creates GitHub issue,
- sends Telegram,
- records daily run-status events.

Strength:

- good operational foundation.

Limitation:

- zero picks are currently treated too much like failure instead of a possible valid no-pick decision.

---

### Candidate universe

Implemented in:

- `src/universe.py`
- `config.yaml`

Current universe sources:

- S&P 500,
- always-included semiconductor tickers,
- bullish watchlist additions,
- custom tickers,
- excluded tickers.

Strength:

- useful broad universe with configurable additions/exclusions.

Limitations:

- universe quality/readiness is not yet treated as a formal production gate,
- universe-source failure can fall back instead of clearly becoming a degraded-readiness condition.

---

### Market data fetching and provider tracking

Implemented in:

- `src/data_fetcher.py`
- `src/market_data_health.py`
- `scripts/build_data_readiness_report.py`

Current behavior:

- yfinance primary OHLCV provider,
- Stooq fallback for daily OHLCV,
- provider events recorded,
- market-data health summarized,
- data readiness report can classify provider/readiness status.

Strength:

- strong foundation for provider visibility.

Limitations:

- readiness and provider health are still mostly reporting/observability,
- official pick selection is not fully gated by readiness status.

---

### Scoring

Implemented across:

- `src/parallel_scorer.py`
- `src/scorer.py`
- `src/fundamentals.py`
- `src/news_sentiment.py`
- `src/market_guard.py`
- `src/day_trading_scorer.py`
- `src/monster_hunt.py`

Current scoring includes:

- trend,
- momentum,
- volatility,
- volume,
- fundamentals,
- sentiment,
- enhanced technical indicators,
- sector multiplier,
- watchlist boost,
- pattern multiplier,
- day-trading score,
- monster score,
- wisdom consultant adjustment.

Safety status:

- legacy AI boost appears disabled in `config.yaml`,
- `semi_boost` is 1.0,
- `ai_boost` is 0.0.

Strength:

- rich scoring foundation.

Limitations:

- too many lanes are mixed inside one official-pick path,
- production scoring contract is unclear,
- missing evidence can still become neutral instead of fail-closed,
- scoring has not passed a formal Lane 1 promotion gate.

---

### Hard blocks

Implemented in:

- `src/hard_blocks.py`

Current hard blocks include:

- catastrophic news,
- penny stock,
- stop-loss too tight,
- recent pick cooldown,
- weak sector / weak tag ETF.

Strength:

- important safety layer.

Limitations:

- hard blocks happen after candidate scoring,
- premarket sanity checks are separate and run after logging,
- blocked candidate diagnostics are partial.

---

### Trade plan and risk plan

Implemented in:

- `src/risk_manager.py`

Current trade plan includes:

- entry,
- stop-loss,
- take-profit,
- quantity,
- risk/reward,
- ATR-based stop/target,
- regime-aware position-size multiplier,
- scale-out tier fields.

Strength:

- good basic risk foundation.

Limitations:

- not yet portfolio-grade,
- max open positions are not fully enforced,
- sector/correlation exposure is not production-grade,
- daily/weekly loss lockouts are not integrated into official pick selection,
- execution slippage and spread assumptions are not production-grade.

---

### Pick logging

Implemented in:

- `src/pick_logger.py`

Current `data/picks_log.csv` persists:

- pick date/time,
- ticker,
- score,
- trade type,
- watch-only fields,
- entry,
- stop-loss,
- take-profit,
- quantity,
- regime,
- SPY benchmark fields,
- sector benchmark fields,
- evaluation status,
- monster fields,
- smell fields,
- tier/trailing-stop fields.

Strength:

- rich historical artifact.

Limitations:

- official pick vs watch-only vs skipped classification needs cleaner separation,
- no-pick decisions are not tracked with equal status to pick decisions.

---

### Post-market evaluation

Implemented in:

- `.github/workflows/evaluate.yml`
- `scripts/evaluate_picks.py`
- `src/pick_evaluator.py`
- `src/performance_stats.py`
- `scripts/daily_execution_report.py`
- `scripts/daily_observation.py`

Current behavior:

- evaluates pending picks after market close,
- marks TP, SL, expired, day-close, or unreachable-entry,
- computes return and R multiple,
- computes SPY alpha,
- computes sector alpha,
- produces dashboard and execution report,
- logs daily observations.

Strength:

- useful outcome tracking foundation.

Limitations:

- still approximate,
- daily OHLC is not true execution simulation,
- fill/slippage/spread modeling is incomplete,
- no-pick quality is not evaluated,
- missed-opportunity analysis is not complete,
- official skipped/watch-only outcomes need cleaner separation.

---

## Main Production Gaps

### Gap 1 — No-pick is not first-class

Current problem:

- zero picks can be treated as workflow failure,
- valid no-pick does not have the same product status as a pick,
- no-pick outcome is not evaluated as a decision.

Production requirement:

- zero picks plus valid no-pick artifact should be success,
- zero picks with missing diagnostics should be failure,
- no-pick must have a reason, evidence, and follow-up learning loop.

Priority:

- critical.

---

### Gap 2 — Data readiness does not fully gate official selection

Current problem:

- provider/data readiness is mostly downstream reporting,
- official selection can proceed without a hard pre-selection readiness gate.

Production requirement:

- official picks require provider and data readiness,
- poor readiness should produce official no-pick,
- readiness failure must be explicit and auditable.

Priority:

- critical.

---

### Gap 3 — Premarket sanity check happens after picks are logged

Current problem:

- `premarket_check.py` runs after picks are already in `picks_log.csv`,
- it can tag SKIP, HALF SIZE, or WATCH ONLY,
- but those picks may already be treated as official picks.

Production requirement:

- premarket sanity must happen before official status,
- SKIP/WATCH candidates must not be logged as normal official picks,
- sanity result must be part of official selection or official no-pick logic.

Priority:

- critical.

---

### Gap 4 — Official pick contract is unclear

Current problem:

- Lane 1 says daily stock pick, but config can output multiple picks,
- day, swing, monster, watch-only, and official pick semantics are mixed.

Production requirement:

- define one pick vs top N,
- define official pick schema,
- define official no-pick schema,
- define mandatory evidence fields,
- define allowed strategy types,
- define what counts as official vs watch-only.

Priority:

- high.

---

### Gap 5 — Strategy lanes are mixed

Current problem:

- premarket official pick path includes swing, day, monster, watchlist/news, wisdom, pattern, and other logic.

Production requirement:

- Lane 1 needs a clean production contract,
- other lanes should be separated or marked observe-only,
- official premarket pick must not accidentally become intraday, monster, or watch-only logic without explicit strategy governance.

Priority:

- high.

---

### Gap 6 — Risk management is not production-grade

Current problem:

- ATR sizing and regime multiplier exist,
- portfolio-level constraints are incomplete.

Production requirement:

- max open positions,
- max daily risk,
- max weekly risk,
- max sector exposure,
- max correlated exposure,
- recent ticker cooldown,
- liquidity check,
- minimum risk/reward,
- max gap risk,
- existing position awareness.

Priority:

- high.

---

### Gap 7 — Missing data can be too permissive

Current problem:

- missing fundamentals can default to neutral,
- missing news can default to neutral,
- market guard failures can default to safe values,
- provider failures are not always selection blockers.

Production requirement:

- missing critical evidence must be explicit,
- missing critical evidence should reduce confidence or block official selection,
- no silent safe defaults for production decisions.

Priority:

- high.

---

### Gap 8 — Execution modeling is approximate

Current problem:

- evaluation mostly uses daily OHLC,
- same-day TP/SL order is approximated,
- limit order fill, spread, slippage, and premarket/open price behavior are incomplete.

Production requirement:

- execution simulation must reflect realistic fill assumptions,
- unreachable entries must be handled,
- slippage/spread must be modeled,
- official picks, skipped picks, watch-only ideas, and no-pick decisions must be evaluated separately.

Priority:

- medium-high.

---

### Gap 9 — Learning loop is not production-controlled

Current problem:

- reports and observations exist,
- but promotion from learning to scoring changes is not fully formalized.

Production requirement:

- calibration ledger,
- experiment tracking,
- scoring version tracking,
- hypothesis validation,
- backtesting,
- walk-forward validation,
- promotion and rollback criteria.

Priority:

- medium-high.

---

## Production-Ready Definition

Lane 1 is production-ready only when all of these are true:

- official pick contract is documented and enforced,
- official no-pick is a first-class successful outcome,
- data readiness gate runs before official selection,
- premarket sanity runs before official status or reclassifies candidates before logging,
- all official picks have mandatory evidence fields,
- all official picks have mandatory risk fields,
- missing critical data fails closed,
- provider failures fail closed or downgrade to official no-pick,
- strategy lanes are cleanly separated,
- official pick output is explainable,
- candidate rejection diagnostics are complete,
- risk and portfolio gates are enforced,
- outcome evaluation is reliable enough for learning,
- no-pick decisions are evaluated,
- missed-opportunity analysis exists,
- performance reports are lane-specific,
- full test suite is green,
- promotion criteria are met,
- rollback criteria are defined,
- paper/live trading remain disabled until future gates pass.

---

## Ordered Lane 1 Completion Plan

### Priority 1 — Define official premarket pick contract

Deliverables:

- formal official pick schema,
- formal official no-pick schema,
- mandatory evidence fields,
- mandatory risk fields,
- official vs watch-only rules,
- one-pick vs top-N decision,
- strategy-lane boundaries,
- production acceptance criteria.

Suggested artifact:

- this document plus follow-up schema/tests.

Status:

- not implemented.

---

### Priority 2 — Make no-pick a successful official outcome

Goal:

- zero picks with valid no-pick diagnostics should pass,
- zero picks without diagnostics should fail.

Deliverables:

- official no-pick JSON artifact,
- official no-pick Markdown summary,
- Telegram/GitHub no-pick message,
- workflow verification logic that accepts valid no-pick,
- tests for no-pick success and failure.

Status:

- critical missing.

---

### Priority 3 — Add pre-selection data readiness gate

Goal:

- official selection cannot run unless readiness passes.

Gate should check:

- market date/session,
- provider health,
- universe fetch coverage,
- OHLCV freshness,
- benchmark availability,
- minimum scored candidate coverage,
- stale/corrupt data evidence.

Failure behavior:

- produce official no-pick with data-readiness reason.

Status:

- mostly reporting-only today.

---

### Priority 4 — Move/enforce premarket sanity before official status

Goal:

- premarket sanity must determine whether a candidate is official, half-size, watch-only, or skipped before normal official logging.

Deliverables:

- premarket sanity gate,
- official candidate reclassification,
- tests for SAFE, HALF SIZE, WATCH ONLY, SKIP TODAY,
- no normal official logging for SKIP/WATCH candidates.

Status:

- partially implemented in the wrong position.

---

### Priority 5 — Complete candidate rejection diagnostics

Every official run should persist:

- universe count,
- fetched count,
- scored count,
- below-threshold count,
- filtered count,
- capped count,
- hard-blocked count,
- premarket-sanity-blocked count,
- selected official picks,
- rejected candidates,
- hard-blocked candidates,
- final official count,
- no-pick reason.

Status:

- partially implemented.

---

### Priority 6 — Add risk and portfolio gate

Gate should enforce:

- max open positions,
- max daily risk,
- max weekly risk,
- max sector exposure,
- max correlated exposure,
- liquidity threshold,
- minimum risk/reward,
- max gap risk,
- existing position awareness.

Status:

- basic risk exists, portfolio gate missing.

---

### Priority 7 — Make missing-data behavior fail closed

Goal:

- no silent neutral defaults for production-critical evidence.

Deliverables:

- explicit missing fundamentals status,
- explicit missing news status,
- explicit missing market regime status,
- explicit missing provider status,
- confidence/risk flags,
- fail-closed behavior for critical missing evidence.

Status:

- partially missing.

---

### Priority 8 — Add official pick versioning

Every official pick/no-pick should include:

- strategy version,
- scoring version,
- config version or hash,
- data provider status,
- selection time ET,
- workflow run ID,
- code commit SHA,
- gate versions.

Status:

- missing/partial.

---

### Priority 9 — Upgrade evaluation and learning

Needed separation:

- official entered picks,
- official skipped picks,
- watch-only ideas,
- no-pick decisions,
- unreachable entries.

Needed reports:

- no-pick outcome review,
- missed-opportunity review,
- slippage/fill assumption report,
- performance by strategy version,
- performance by regime.

Status:

- partial.

---

### Priority 10 — Add promotion gate dashboard

Promotion gate should require:

- sufficient sample size,
- positive expectancy,
- acceptable drawdown,
- stable win rate,
- slippage tolerance,
- data readiness stability,
- no unresolved provider-gate failures,
- no missing diagnostics,
- no stale-data official picks,
- reproducible full test suite,
- backtest and walk-forward validation,
- human approval.

Status:

- missing.

---

## Priority 1 Implementation Status

Initial contract implementation added:

- `src/premarket_decision_contract.py`
- `tests/test_premarket_decision_contract.py`

This implementation defines:

- Lane 1 strategy-lane identifier,
- contract version,
- strategy version,
- scoring version,
- official pick decision type,
- official no-pick decision type,
- required official pick fields,
- required official no-pick fields,
- allowed no-pick primary causes,
- safety flags requiring paper/live trading to remain false,
- validation helpers for official pick and official no-pick payloads.

This phase is intentionally behavior-neutral. It does not wire the contract into `main.py` or the GitHub Actions workflow yet.

Runtime wiring belongs to later phases:

- Phase 2: first-class official no-pick outcome,
- Phase 3: pre-selection data readiness gate,
- Phase 4: premarket sanity as an official gate.


## Priority 2 Implementation Status

Initial first-class no-pick runtime support added:

- `scripts/validate_daily_no_pick.py`
- `tests/test_validate_daily_no_pick.py`
- updated `main.py`
- updated `.github/workflows/daily-picks.yml`
- updated `scripts/format_picks_email.py`
- updated `scripts/send_layman_daily.py`

Behavior change:

- `main.py` now writes an official no-pick artifact and exits successfully when no official candidates survive scoring/filtering/gating.
- The daily-picks workflow now treats zero CSV rows as success only when `scripts/validate_daily_no_pick.py` validates the official no-pick artifact.
- Zero CSV rows without a valid no-pick artifact still fail loudly.
- GitHub issue and Telegram formatting now surface official no-pick reasoning when a no-pick report exists.

Safety:

- No fake picks are created.
- Paper trading remains disabled.
- Live trading remains disabled.
- No buy instructions are emitted for official no-pick days.


## Priority 3 Implementation Status

Initial pre-selection data readiness gate added:

- `src/premarket_readiness_gate.py`
- `tests/test_premarket_readiness_gate.py`
- updated `main.py`

Behavior change:

- after universe and OHLCV fetch, `main.py` now runs a premarket data-readiness gate before scoring,
- if the gate passes, scoring proceeds normally,
- if the gate fails, the run writes a contract-compatible official no-pick artifact and exits successfully,
- no fake picks are created when data readiness is poor.

Current gate checks:

- non-empty candidate universe,
- at least some OHLCV data fetched,
- minimum fetched-data coverage,
- minimum fetched ticker count,
- severe OHLCV provider degradation,
- provider warnings such as rate limits, empty results, and OHLCV errors.

Configurable environment variables:

- `PREMARKET_MIN_FETCH_COVERAGE`, default `0.25`,
- `PREMARKET_MIN_FETCHED_COUNT`, default `25`.

Safety:

- Paper trading remains disabled.
- Live trading remains disabled.
- No buy instructions are emitted on readiness-gated no-pick days.

Follow-up needed:

- add freshness/staleness checks,
- add SPY/QQQ benchmark availability checks,
- add provider-specific confidence scoring,
- integrate readiness output into daily intelligence/reporting.


## Priority 4 Implementation Status

Initial premarket sanity gate before official status added:

- `src/premarket_sanity_gate.py`
- `tests/test_premarket_sanity_gate.py`
- updated `main.py`

Behavior change:

- `main.py` now applies premarket sanity after finalist selection and trade-type tagging but before official logging,
- candidates marked `SKIP_TODAY` or `WATCH_ONLY` are not logged as normal official picks,
- candidates marked `HALF_SIZE` remain official but have quantity reduced before logging,
- if all finalists are blocked by premarket sanity, the run writes a contract-compatible official no-pick artifact and exits successfully.

Current sanity outcomes:

- `SAFE`,
- `HALF_SIZE`,
- `SKIP_TODAY`,
- `WATCH_ONLY`.

Safety:

- No fake picks are created.
- Paper trading remains disabled.
- Live trading remains disabled.
- No buy instructions are emitted when all candidates are blocked.

Follow-up needed:

- migrate legacy `scripts/premarket_check.py` into the reusable gate or make it pure reporting,
- persist premarket sanity fields directly in `picks_log.csv`,
- add richer live quote/provider confidence checks,
- separate official skipped candidates from watch-only candidates in evaluation.


## Priority 5 Implementation Status

Initial complete candidate diagnostics added:

- `src/candidate_diagnostics.py`
- `tests/test_candidate_diagnostics.py`
- updated `main.py`

Behavior change:

- official successful runs now write `data/daily_picks_candidate_diagnostics_YYYY-MM-DD.json`,
- official successful runs also write `data/daily_picks_candidate_diagnostics_YYYY-MM-DD.md`,
- no-pick runs now also write the same candidate diagnostics artifact when diagnostics are available,
- hard-block no-pick diagnostics now include stage counts, selected count, rejected count, and rejection details,
- premarket-sanity no-pick diagnostics now include stage counts and sanity-blocked candidates,
- wisdom-kill and earnings-risk drops are captured as extra rejection diagnostics.

Current diagnostic categories:

- selected official picks,
- rejected candidates,
- hard-blocked candidates,
- premarket-sanity-blocked candidates,
- scored-not-filtered count,
- filtered-not-capped count,
- stage counts,
- pipeline counts.

Safety:

- Reporting-only change.
- No scoring behavior changes.
- No pick creation behavior changes.
- Paper trading remains disabled.
- Live trading remains disabled.

Follow-up needed:

- add lower-level score-threshold rejection reasons from the scorer,
- persist diagnostics for every intermediate candidate if artifact size remains manageable,
- connect diagnostics into daily intelligence brief and readiness reports.


## Priority 6 Implementation Status

Initial portfolio risk gate added:

- `src/portfolio_risk_gate.py`
- `tests/test_portfolio_risk_gate.py`
- updated `src/candidate_diagnostics.py`
- updated `main.py`

Behavior change:

- `main.py` now applies a portfolio risk gate after premarket sanity and before official logging,
- candidates that exceed risk constraints are blocked from normal official logging,
- if all finalists are blocked by portfolio risk, the run writes a contract-compatible official no-pick artifact and exits successfully,
- successful runs include portfolio-risk diagnostics.

Current gate checks:

- max open positions,
- available new-pick slots,
- malformed entry/stop/target/quantity,
- per-trade risk percent,
- minimum risk/reward,
- sector exposure cap,
- tag exposure cap.

Current config sources:

- `risk.account_size`,
- `risk.risk_per_trade_pct`,
- `risk.max_positions`,
- optional `risk.max_per_sector`,
- optional `risk.max_per_tag`,
- optional `risk.min_risk_reward`.

Safety:

- No fake picks are created.
- Paper trading remains disabled.
- Live trading remains disabled.
- No buy instructions are emitted when all candidates are risk-blocked.

Follow-up needed:

- add correlation-aware exposure,
- add daily/weekly loss lockout,
- add existing-position sector metadata backfill,
- run monster-treatment sizing before final risk gate or add post-monster risk validation.


## Priority 7 Implementation Status

Initial missing-data fail-closed behavior added:

- `src/missing_data_gate.py`
- `tests/test_missing_data_gate.py`
- updated `src/candidate_diagnostics.py`
- updated `main.py`

Behavior change:

- `main.py` now applies a final missing-data gate after portfolio risk and before official logging,
- candidates with missing/malformed critical official-pick fields are blocked from normal official logging,
- if all finalists are blocked by missing data, the run writes a contract-compatible official no-pick artifact and exits successfully,
- successful and no-pick candidate diagnostics now include missing-data blocks.

Current required official-pick data checks:

- ticker present,
- numeric non-negative score,
- trade type is `day` or `swing`,
- positive entry,
- positive stop loss,
- positive take profit,
- positive quantity,
- positive risk/reward,
- stop loss below entry,
- take profit above entry,
- prior premarket sanity did not mark candidate non-actionable,
- prior portfolio risk did not mark candidate failed.

Safety:

- No fake picks are created.
- No scoring behavior changes.
- Paper trading remains disabled.
- Live trading remains disabled.
- No buy instructions are emitted when all candidates are missing-data blocked.

Follow-up needed:

- decide whether company/sector should be hard-required or warning-only,
- add provider freshness timestamps to required field snapshot,
- validate final logged row against the full official decision contract when Priority 8 wires the official decision artifact.


## Priority 8 Implementation Status

Initial official pick artifact generation added:

- `src/official_pick_artifact.py`
- `tests/test_official_pick_artifact.py`
- updated `main.py`

Behavior change:

- after all gates pass and before CSV logging, `main.py` writes one contract-compatible official pick artifact per final official pick,
- `main.py` also writes a daily official pick summary artifact,
- official pick artifacts are validated against `src.premarket_decision_contract.validate_official_pick`,
- if artifact validation fails, the run writes a valid official no-pick artifact and exits successfully instead of logging invalid official picks.

New artifacts:

- `data/premarket_official_pick_YYYY-MM-DD_TICKER.json`
- `data/premarket_official_pick_summary_YYYY-MM-DD.json`

Safety:

- No fake picks are created.
- No scoring behavior changes.
- Paper trading remains disabled.
- Live trading remains disabled.
- Artifact validation failure prevents invalid official logging.

Follow-up needed:

- publish artifact path in GitHub workflow summary,
- include artifact metadata in Telegram/GitHub issue output,
- persist artifact path or decision ID in `picks_log.csv`.


## Priority 9 Implementation Status

Initial workflow official artifact validation/upload integration added:

- `scripts/validate_official_pick_artifacts.py`
- `tests/test_validate_official_pick_artifacts.py`
- updated `.github/workflows/daily-picks.yml`

Behavior change:

- after CSV/no-pick verification, the workflow validates official decision artifacts,
- pick days require valid contract-compatible official pick artifacts matching the logged row count,
- no-pick days require a valid official no-pick artifact,
- official decision artifacts are uploaded with `actions/upload-artifact`,
- official pick, no-pick, diagnostics, and rejection artifacts are included in commit staging.

Safety:

- Validation-only workflow change.
- No fake picks are created.
- No scoring behavior changes.
- Paper trading remains disabled.
- Live trading remains disabled.

Follow-up needed:

- add workflow summary Markdown links to uploaded artifacts,
- include official artifact paths in Telegram/GitHub issue output,
- add retention policy if artifact volume becomes large.


## Priority 10 Implementation Status

Initial Telegram/GitHub issue official-artifact consumption added:

- `src/official_artifact_loader.py`
- `tests/test_official_artifact_loader.py`
- `tests/test_official_artifact_outputs.py`
- updated `scripts/format_picks_email.py`
- updated `scripts/send_layman_daily.py`

Behavior change:

- GitHub daily-picks issue output now enriches CSV rows from validated official pick artifacts,
- Telegram daily-picks output now enriches CSV rows from validated official pick artifacts,
- user-facing output now displays official artifact presence, contract version, official reason, and official risk flags when available,
- CSV remains a fallback source if artifacts are missing.

Safety:

- Reporting-only output change.
- No scoring behavior changes.
- No pick creation behavior changes.
- Paper trading remains disabled.
- Live trading remains disabled.

Follow-up needed:

- include direct GitHub artifact links once workflow run artifact URLs are available,
- add official decision IDs to `picks_log.csv`,
- make artifact absence fail user-facing sends once production readiness is declared.


## Priority 11 Implementation Status

Initial end-to-end dry-run validation added:

- `scripts/dry_run_official_premarket_pick.py`
- `tests/test_dry_run_official_premarket_pick.py`
- updated `.github/workflows/daily-picks.yml`

Behavior change:

- the daily-picks workflow now runs a Lane 1 synthetic official-pick dry-run before normal smoke tests,
- the dry-run validates the local official-pick chain without calling market data providers, LLMs, Telegram, or GitHub,
- the dry-run exercises candidate diagnostics, portfolio risk, missing-data validation, official artifact writing, contract validation, and artifact validation.

Safety:

- No real picks are generated by the dry-run.
- No live provider calls are made by the dry-run.
- No alerts are sent by the dry-run.
- Paper trading remains disabled.
- Live trading remains disabled.

Follow-up needed:

- add a synthetic official no-pick dry-run,
- add workflow summary output for dry-run status,
- add dry-run fixture variants for each no-pick cause.


## Priority 12 Implementation Status

Initial synthetic no-pick dry-run and cause fixture coverage added:

- `scripts/dry_run_official_no_pick.py`
- `tests/test_dry_run_official_no_pick.py`
- updated `.github/workflows/daily-picks.yml`

Behavior change:

- the daily-picks workflow now runs a Lane 1 synthetic official no-pick dry-run before normal smoke tests,
- the dry-run validates all allowed official no-pick causes from the decision contract,
- each synthetic no-pick artifact is validated with `scripts/validate_daily_no_pick.py` logic,
- the dry-run uses only local synthetic data and writes to an isolated output directory.

Safety:

- No real picks are generated by the dry-run.
- No live provider calls are made by the dry-run.
- No alerts are sent by the dry-run.
- Paper trading remains disabled.
- Live trading remains disabled.

Follow-up needed:

- add workflow summary output for both dry-run scripts,
- add fixture assertions for exact classifier diagnostics per cause,
- make production no-pick artifact builder share more code with this fixture builder.


## Implementation Playbook

This section translates the roadmap into concrete code work.

The work should be completed in small, testable commits. Each priority should leave the repository green and should not enable paper or live trading.

---

### Implementation Phase 1 — Official decision contract

Purpose:

Define the official output contract before changing behavior.

Likely files:

- `docs/planning/PREMARKET_OFFICIAL_PICK_PRODUCTION_PLAN.md`
- new tests under `tests/`
- possibly a new module such as `src/premarket_decision_contract.py`

Implementation tasks:

- define official pick schema,
- define official no-pick schema,
- define required safety flags,
- define required readiness fields,
- define required risk fields,
- define official vs watch-only vs skipped semantics,
- define whether Lane 1 emits one official pick or multiple official candidates.

Suggested official pick fields:

- `artifact`,
- `date`,
- `decision`,
- `ticker`,
- `company`,
- `strategy_lane`,
- `strategy_version`,
- `scoring_version`,
- `config_version`,
- `selection_time_et`,
- `workflow_run_id`,
- `commit_sha`,
- `data_readiness_status`,
- `provider_status`,
- `market_session_status`,
- `score`,
- `score_components`,
- `entry`,
- `stop_loss`,
- `take_profit`,
- `risk_reward`,
- `quantity`,
- `risk_dollars`,
- `regime`,
- `risk_flags`,
- `selection_reason`,
- `invalidation_conditions`,
- `paper_trading_enabled`,
- `live_trading_enabled`.

Suggested official no-pick fields:

- `artifact`,
- `date`,
- `decision`,
- `primary_no_pick_cause`,
- `secondary_causes`,
- `human_readable_summary`,
- `data_readiness_status`,
- `provider_status`,
- `market_session_status`,
- `pipeline`,
- `candidate_diagnostics`,
- `watch_only_available`,
- `next_action`,
- `paper_trading_enabled`,
- `live_trading_enabled`.

Acceptance criteria:

- schemas are documented,
- tests assert required fields,
- no runtime behavior changes yet,
- full relevant tests pass.

---

### Implementation Phase 2 — First-class official no-pick outcome

Purpose:

Make no-pick a valid official premarket decision when evidence supports it.

Likely files:

- `.github/workflows/daily-picks.yml`
- `main.py`
- `scripts/record_daily_picks_run_status.py`
- `scripts/format_picks_email.py`
- `scripts/send_layman_daily.py`
- tests under `tests/`

Implementation tasks:

- create or standardize official no-pick artifact,
- ensure `main.py` writes complete diagnostics when no candidates qualify,
- change workflow verification so zero `picks_log.csv` rows is success if valid no-pick artifact exists,
- keep zero rows as failure if no no-pick artifact exists,
- send Telegram/GitHub no-pick summary,
- record run-status as official no-pick rather than generic failure.

Expected artifacts:

- `data/daily_picks_no_pick_report_YYYY-MM-DD.json`
- `data/daily_picks_no_pick_report_YYYY-MM-DD.md`
- `data/daily_picks_candidate_rejections_YYYY-MM-DD.json`
- `data/daily_picks_run_status_YYYY-MM-DD.jsonl`

Acceptance criteria:

- valid no-pick exits workflow successfully,
- invalid no-pick without diagnostics fails loudly,
- no-pick message is human-readable,
- no-pick does not create fake picks,
- paper/live trading remain false,
- tests cover success and failure paths.

---

### Implementation Phase 3 — Pre-selection data readiness gate

Purpose:

Prevent official selection from running on degraded or incomplete data.

Likely files:

- `main.py`
- `src/data_fetcher.py`
- `src/market_data_health.py`
- `scripts/build_data_readiness_report.py`
- possibly new module `src/premarket_readiness_gate.py`
- tests under `tests/`

Implementation tasks:

- compute readiness before candidate selection becomes official,
- check market/trading-day status,
- check provider error rates,
- check universe fetch coverage,
- check OHLCV freshness,
- check benchmark availability,
- check minimum candidate coverage,
- fail closed into official no-pick if readiness fails.

Possible gate inputs:

- universe count,
- fetched count,
- scored count,
- provider failure taxonomy,
- market data health summary,
- market calendar status,
- SPY/QQQ availability,
- stale data indicators.

Acceptance criteria:

- readiness failure produces official no-pick,
- provider outage does not generate official picks,
- readiness status is persisted,
- tests cover provider failure, low coverage, and healthy data paths.

---

### Implementation Phase 4 — Premarket sanity as an official gate

Purpose:

Ensure candidates are not logged as official picks before fresh premarket sanity is applied.

Likely files:

- `main.py`
- `scripts/premarket_check.py`
- `scripts/format_picks_email.py`
- `scripts/send_layman_daily.py`
- possibly new module `src/premarket_sanity_gate.py`
- tests under `tests/`

Implementation options:

Option A:

- move sanity logic into `main.py` before `log_picks`.

Option B:

- make `main.py` write candidate artifact first,
- run sanity gate,
- only then write official pick/no-pick artifact and `picks_log.csv`.

Preferred direction:

- Option B is cleaner because it separates candidate generation from official decision logging.

Expected artifact flow:

- candidate generation artifact,
- premarket sanity artifact,
- official decision artifact,
- `picks_log.csv` only for actionable official picks.

Acceptance criteria:

- SKIP TODAY candidates are not logged as normal official picks,
- WATCH ONLY candidates are not logged as normal official picks,
- HALF SIZE candidates carry explicit risk adjustment,
- if all candidates are skipped/watch-only, official no-pick is emitted,
- tests cover SAFE, HALF SIZE, WATCH ONLY, SKIP TODAY.

---

### Implementation Phase 5 — Complete rejection and selection diagnostics

Purpose:

Make every official decision explainable.

Likely files:

- `main.py`
- `scripts/build_candidate_lifecycle.py`
- `scripts/build_data_readiness_report.py`
- `scripts/build_daily_intelligence_brief.py`
- tests under `tests/`

Implementation tasks:

- persist full pipeline counts,
- persist selected official picks,
- persist rejected candidates,
- persist hard-blocked candidates,
- persist premarket-sanity-blocked candidates,
- persist below-threshold candidates or aggregate counts,
- include rejection reason categories.

Required counts:

- universe count,
- fetched count,
- scored count,
- below-score-threshold count,
- filtered count,
- capped count,
- hard-blocked count,
- premarket-sanity-blocked count,
- selected official count,
- watch-only count,
- final no-pick status.

Acceptance criteria:

- every no-pick has candidate diagnostics,
- every rejected finalist has a reason,
- daily intelligence brief can summarize the decision,
- tests cover diagnostic completeness.

---

### Implementation Phase 6 — Risk and portfolio gate

Purpose:

Prevent individually good picks from creating bad portfolio risk.

Likely files:

- `src/risk_manager.py`
- possible new module `src/portfolio_risk_gate.py`
- `main.py`
- `config.yaml`
- tests under `tests/`

Implementation tasks:

- enforce max open positions,
- enforce max daily risk,
- enforce max weekly risk,
- enforce sector exposure,
- enforce correlation or tag exposure,
- enforce minimum risk/reward,
- enforce liquidity threshold,
- enforce existing position awareness.

Acceptance criteria:

- risk gate can block all candidates and produce official no-pick,
- blocked candidates have risk reasons,
- no pick exceeds configured risk,
- tests cover each risk rule.

---

### Implementation Phase 7 — Missing-data fail-closed behavior

Purpose:

Prevent missing critical evidence from silently becoming neutral.

Likely files:

- `src/data_fetcher.py`
- `src/fundamentals.py`
- `src/news_sentiment.py`
- `src/market_guard.py`
- `src/parallel_scorer.py`
- `main.py`
- tests under `tests/`

Implementation tasks:

- mark missing fundamentals explicitly,
- mark missing news explicitly,
- mark missing market regime explicitly,
- mark missing provider status explicitly,
- distinguish optional missing evidence from critical missing evidence,
- block or downgrade critical missing evidence.

Acceptance criteria:

- critical missing data cannot become a normal official pick silently,
- output contains missing-data flags,
- tests cover missing fundamentals/news/regime/provider paths.

---

### Implementation Phase 8 — Official pick versioning

Purpose:

Make every decision reproducible and auditable.

Likely files:

- `main.py`
- `src/pick_logger.py`
- possibly `src/versioning.py`
- tests under `tests/`

Implementation tasks:

- add strategy version,
- add scoring version,
- add config hash,
- add commit SHA,
- add workflow run ID,
- add selection timestamp,
- add gate versions.

Acceptance criteria:

- every official pick/no-pick has version metadata,
- `picks_log.csv` or official decision artifacts preserve version fields,
- tests assert metadata is present.

---

### Implementation Phase 9 — Evaluation and learning upgrade

Purpose:

Separate actual entered picks from skipped, watch-only, and no-pick decisions.

Likely files:

- `src/pick_evaluator.py`
- `src/performance_stats.py`
- `scripts/evaluate_picks.py`
- `scripts/daily_execution_report.py`
- `scripts/daily_observation.py`
- possible new scripts for no-pick and missed-opportunity review
- tests under `tests/`

Implementation tasks:

- evaluate official entered picks separately,
- evaluate skipped picks separately,
- evaluate watch-only candidates separately,
- evaluate no-pick days,
- add missed-opportunity report,
- add slippage/fill assumption report,
- report performance by strategy version and regime.

Acceptance criteria:

- no-pick decisions can be reviewed,
- missed opportunities are visible,
- watch-only performance is not mixed with official picks,
- official pick performance is lane-specific.

---

### Implementation Phase 10 — Promotion dashboard

Purpose:

Define and monitor whether Lane 1 can move from monitoring-ready to paper-trading-ready.

Likely files:

- new script such as `scripts/build_premarket_promotion_dashboard.py`
- docs under `docs/planning/`
- tests under `tests/`

Promotion criteria should include:

- sufficient sample size,
- positive expectancy,
- acceptable drawdown,
- stable win rate,
- slippage tolerance,
- data readiness stability,
- provider reliability,
- complete diagnostics,
- no stale-data official picks,
- green tests,
- historical backtest,
- walk-forward validation,
- human approval.

Acceptance criteria:

- dashboard states ready/not ready,
- dashboard explains blockers,
- paper/live trading remain disabled until explicitly promoted.

---

## Suggested Commit Sequence

Recommended small commits:

1. Document and test official decision schemas.
2. Add official no-pick artifact validation.
3. Update workflow to treat valid no-pick as success.
4. Add pre-selection readiness gate.
5. Move or refactor premarket sanity into official decision flow.
6. Expand rejection diagnostics.
7. Add portfolio risk gate.
8. Add fail-closed missing-data flags.
9. Add decision versioning.
10. Upgrade evaluation and no-pick/missed-opportunity learning.
11. Add promotion dashboard.

Each commit should include:

- tests,
- documentation update,
- no paper/live trading enablement,
- green targeted tests,
- green full suite when behavior changes are broad.

---

## Implementation Rule

Do not optimize scoring before decision correctness is fixed.

Order of work:

1. correctness,
2. safety,
3. observability,
4. diagnostics,
5. risk gates,
6. evaluation realism,
7. learning loop,
8. scoring optimization,
9. promotion gates.


## Immediate Recommendation

Do not start by tuning scoring.

Start with correctness, safety, and product contract.

Recommended first three work items:

1. define and enforce the official premarket pick contract,
2. make no-pick a first-class successful official outcome,
3. add a pre-selection data readiness gate.

Only after that should Lane 1 scoring and optimization be tuned.

---

## Safety Commitments

Until Lane 1 passes production gates:

- monitoring-first remains the default,
- paper trading remains disabled,
- live trading remains disabled,
- no buy instructions are emitted from observe-only reports,
- official scoring changes require tests,
- production behavior changes require documentation,
- no automatic self-modification of scoring logic is allowed.
