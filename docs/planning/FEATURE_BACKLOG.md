# Feature Backlog and Future Implementation Plan

## Purpose

This document captures future product, model, data, architecture, and notification improvements for Daily Stock Agent.

The goal is to document what we plan to build before coding, so future implementation can follow a clear plan instead of re-thinking everything from scratch.

This document should answer:

- what already exists
- what is partially implemented
- what is missing
- what should be built next
- why each feature matters
- how each feature should be approached
- what files may be affected
- what data artifacts should be added
- what tests should be added
- what risks exist
- when a feature can be promoted

## Current Product Philosophy

The agent should remain monitoring-only until readiness gates are proven.

The product should prioritize:

- trust over excitement
- evidence over hype
- clarity over aggressive alerts
- watch-only validation before official promotion
- explainable decisions
- clean separation between product lanes

The agent may:

- recommend
- monitor
- explain
- evaluate
- report
- learn
- propose improvements

The agent must not yet:

- execute real-money trades
- enable paper trading by default
- convert watch-only ideas into official picks
- mix intraday ideas with swing picks ambiguously
- treat speculative news spikes as long-term compounders
- force picks just to look useful

## Existing Canonical Documentation

The repo already has important documentation. This backlog should complement those docs, not replace them.

Important existing docs:

- `docs/PROJECT_BLUEPRINT.md`
- `docs/strategy/AGENT_MATURITY_TRACKER.md`
- `docs/strategy/MONSTER_HUNTER_DESIGN.md`
- `docs/strategy/PRODUCT_FAILURE_AND_WIN_STRATEGY.md`
- `docs/reference/intraday_model_strategy.md`
- `docs/reference/intraday_technical_indicators.md`
- `docs/WORK_LOG.md`
- `docs/NEXT_SESSION.md`

Documentation rule:

- Use `docs/PROJECT_BLUEPRINT.md` for canonical current state and architecture summary.
- Use this file for detailed future feature planning and implementation approach.
- Update `docs/WORK_LOG.md` after meaningful documentation or code changes.
- Update `docs/NEXT_SESSION.md` at the end of a work session.

## Current Major Product Lanes

The agent should be understood as multiple separate product lanes.

### Lane 1: Daily / Swing Picks

Purpose:

- official premarket model picks
- multi-day swing opportunities
- clear entry, stop-loss, take-profit, and risk/reward
- evaluation through `data/picks_log.csv`

Current status:

- implemented
- monitoring-only
- official pick generation exists
- paper/live trading disabled

### Lane 2: Intraday Opportunities

Purpose:

- same-day market monitoring
- existing pick status updates
- watch-only new intraday ideas
- opening-range and momentum observations
- future self-learning intraday model

Current status:

- partially implemented
- watch-only only
- not official intraday picks yet

### Lane 3: News Engine

Purpose:

- classify market/news catalysts
- maintain watchlist
- boost/penalize relevant tickers
- track news signal evidence and outcomes

Current status:

- implemented with evidence artifacts
- still monitoring-only

### Lane 4: Monster Hunter / Long-Term Compounders

Purpose:

- research long-term potential compounders
- understand fundamentals, themes, moat, institutional ownership, and thesis health
- separate long-term thesis tracking from day/swing trading

Current status:

- planned and partially scaffolded
- research-only
- not official picks
- not paper/live trades

### Lane 5: Learning / Wisdom / Calibration

Purpose:

- learn from outcomes
- maintain signal journals
- propose weight changes
- build wisdom rules
- improve safely through evidence

Current status:

- partially implemented
- needs unified lifecycle and promotion gates

## Current Implemented Inventory

This section summarizes what already exists in the repo.

### Daily Picks Engine

Likely files:

- `main.py`
- `config.yaml`
- `.github/workflows/daily-picks.yml`
- `src/scorer.py`
- `src/parallel_scorer.py`
- `src/risk_manager.py`
- `src/hard_blocks.py`
- `src/pick_logger.py`
- `src/picks_csv.py`
- `src/probability_engine.py`

Implemented capabilities:

- universe selection
- market data fetch
- technical indicator scoring
- fundamental scoring
- sentiment/news enrichment
- regime checks
- sector caps
- tag caps
- hard blocks
- probability engine observe-mode output
- smell faculty observe/enforce capability
- pick logging to CSV
- no-pick diagnostics
- candidate rejection reports
- market-data health summaries
- Telegram daily pick flow

Current product rule:

- official daily picks must not be forced
- no-pick days must be explainable
- monitoring-only remains default

### Pick Evaluation and Performance

Likely files:

- `evaluate_picks.py`
- `scripts/evaluate_picks.py`
- `.github/workflows/evaluate.yml`
- `src/pick_evaluator.py`
- `src/performance_tracker.py`
- `src/performance_stats.py`
- `src/exit_metrics.py`

Implemented capabilities:

- evaluate pending/open picks
- mark stop-loss hit
- mark take-profit hit
- mark day-close / expired style outcomes
- calculate actual return
- calculate R multiple
- support daily and longer review reports

Current gap:

- official picks have evaluation support
- watch-only intraday candidates do not yet have a complete equivalent outcome system

### Intraday Monitor

Likely files:

- `scripts/intraday_monitor.py`
- `scripts/intraday_scanner.py`
- `scripts/send_intraday_telegram.py`
- `.github/workflows/intraday_monitor.yml`
- `src/opening_range_scanner.py`
- `src/adaptive_sl.py`
- `src/adaptive_tp.py`
- `src/trailing_stop.py`

Implemented capabilities:

- monitor open/pending model picks
- detect near stop-loss
- detect stop-loss hit
- detect halfway to take-profit
- detect take-profit hit
- detect volume spike
- detect material news
- persist intraday SL/TP closes to CSV
- raise trailing stop
- raise adaptive take-profit
- tighten adaptive stop-loss
- scan for new watch-only intraday ideas
- opening-range breakout observations
- legacy momentum observations
- intraday Telegram alerts
- dedupe sent intraday alerts

Current gaps:

- message sections are not clear enough
- existing pick updates and new watch-only ideas can feel mixed
- scanner can skip when there are no active picks
- active pick loading falls back to most recent date instead of a clean active-position lifecycle

### Opening-Range Scanner

Likely files:

- `src/opening_range_scanner.py`
- `scripts/intraday_scanner.py`
- `scripts/backtest_opening_range_observations.py`
- `scripts/review_opening_range_observations.py`

Likely tests:

- `tests/test_opening_range_scanner.py`
- `tests/test_intraday_scanner_opening_range.py`
- `tests/test_opening_range_observation_backtest.py`
- `tests/test_opening_range_observation_review.py`

Implemented capabilities:

- opening-range breakout detection
- opening-range high/low calculation
- breakout percent
- opening-range width percent
- volume ratio
- gap guard
- extension/chase guard
- watch-only candidate output
- opening-range observation artifact
- opening-range bar artifact
- opening-range run-status artifact

Current artifacts:

- `data/opening_range_observations_YYYY-MM-DD.jsonl`
- `data/opening_range_bars/YYYY-MM-DD/TICKER.jsonl`
- `data/opening_range_run_status_YYYY-MM-DD.jsonl`

Current gaps:

- no unified intraday candidate artifact yet
- no full forward outcome tracking yet
- no daily intraday learning report yet
- no weekly recalibration report yet
- VWAP/EMA/RSI/MACD/ATR are not yet deeply used in opening-range selection

### Technical Indicators

Likely file:

- `src/indicators.py`

Already available:

- SMA
- EMA
- RSI
- MACD
- Bollinger Bands
- ATR
- Stochastic
- OBV
- Parabolic SAR
- VWAP
- ADX
- candlestick patterns
- Fibonacci levels
- support/resistance
- volume ratio

Important insight:

- the repo already has many indicators
- the missing part is not basic indicator implementation
- the missing part is using these indicators as intraday features and learning which ones actually improve outcomes

Future direction:

- create an intraday feature extractor
- reuse `src/indicators.py`
- avoid rewriting existing indicator logic
- feed features into candidate snapshots and scoring

### News Engine

Likely files:

- `src/news_engine.py`
- `src/news_signals.py`
- `src/news_classifier.py`
- `src/news_sentiment.py`
- `src/market_news.py`
- `scripts/run_news_engine.py`
- `scripts/news_signal_evidence_report.py`
- `scripts/news_signal_outcome_attribution.py`
- `.github/workflows/news_engine.yml`
- `.github/workflows/news_evidence.yml`

Implemented capabilities:

- fetch news
- classify headlines
- score tradeable impact
- dedupe seen news
- maintain watchlist
- create active news signals
- boost or penalize picks based on news
- record news engine run status
- create news signal evidence reports
- attribute future returns to news signals

Current artifacts:

- `data/news_log.jsonl`
- `data/news_seen.json`
- `data/news_signals.json`
- `data/watchlist.json`
- `data/news_engine_run_status_YYYY-MM-DD.jsonl`
- `data/news_signal_outcomes_YYYY-MM-DD.jsonl`
- `data/news_signal_evidence_report_YYYY-MM-DD.md`

Current gap:

- news evidence design is stronger than intraday evidence design
- intraday should copy the news evidence pattern

### Late Watch-Only Daily Ideas

Likely files:

- `scripts/generate_late_daily_ideas.py`
- `scripts/send_late_daily_ideas_telegram.py`
- `.github/workflows/late_watch_only.yml`

Implemented capabilities:

- generate watch-only fallback ideas after missed official premarket window
- avoid polluting official pick statistics
- send deduped Telegram fallback message
- preserve learning evidence even when official daily picks are missed
- avoid action-like BUY wording for unresolved watch-only ideas

Current artifacts:

- `data/late_daily_ideas_YYYY-MM-DD.jsonl`
- `data/late_daily_ideas_YYYY-MM-DD.md`
- `data/late_daily_ideas_sent_YYYY-MM-DD.json`

Current gap:

- late watch-only ideas are not yet connected to a unified watch-only candidate/outcome lifecycle

### Monster Hunter / Long-Term Compounder Lane

Likely docs:

- `docs/strategy/MONSTER_HUNTER_DESIGN.md`
- `docs/strategy/AGENT_MATURITY_TRACKER.md`

Likely files:

- `src/monster_hunt.py`
- `src/monster_data.py`

Likely tests:

- `tests/test_monster_hunt.py`
- `tests/test_monster_flag_persistence.py`
- `tests/test_parallel_scorer_monster_data.py`

Current status:

- planned architecture exists
- some scoring/treatment concepts exist
- `monster_score` exists in schema
- long-term research lane is documented
- should remain research-only / monitoring-only

Important product rule:

- Monster Hunter must not silently convert failed swing trades into long-term holds
- Monster Hunter must not contaminate official daily pick stats
- Monster Hunter must not create paper/live trades
- Monster Hunter must have separate thesis states and thesis-break rules

Current gap:

- no formal monster thesis state artifact yet
- no theme radar artifact yet
- no institutional/ETF ownership analyzer yet
- no deep quarterly/yearly fundamental thesis report yet
- no validated monster promotion gate yet

### Learning, Wisdom, Calibration, and Brain

Likely files:

- `src/learning_journal.py`
- `src/signal_journal.py`
- `src/calibration.py`
- `src/weight_proposer.py`
- `src/weight_applier.py`
- `src/wisdom_base.py`
- `src/wisdom_hint.py`
- `src/wisdom_consultant.py`
- `src/hypothesis_engine.py`
- `src/meta_brain.py`
- `src/agent_memoir.py`
- `scripts/run_nightly_brain.py`
- `scripts/run_hypothesis_review.py`
- `scripts/daily_watch_only_learning_report.py`
- `.github/workflows/nightly_brain.yml`
- `.github/workflows/hypothesis_weekly.yml`

Current artifacts:

- `data/learning_journal.jsonl`
- `data/signal_journal.jsonl`
- `data/weight_proposals.jsonl`
- `data/learning/`
- `data/wisdom/`

Implemented capabilities:

- signal journaling
- learning journal
- hypothesis review
- wisdom base
- weight proposals
- calibration concepts
- nightly brain workflow
- watch-only learning report v1

Current gap:

- learning is not yet organized around one unified lifecycle
- threshold changes should remain recommendations until approved
- model versioning is not yet strong enough for long-term attribution

## Feature Planning Template

Every future feature should be documented with this shape before implementation.

Template:

- Feature:
- Status:
- Priority:
- Why it matters:
- Current gap:
- Implementation approach:
- Likely files affected:
- Data artifacts:
- Tests:
- Product impact:
- Architecture impact:
- Risks:
- Promotion or validation gate:

## Phase 1: Product Clarity and Notification UX

### Feature: Separate Intraday Message Sections

Status:

- planned

Priority:

- very high

Why it matters:

- users may confuse existing model position updates with new intraday ideas
- trust depends on clear product language
- alerts like stop-loss updates must not look like new buy/sell instructions

Current gap:

- intraday Telegram messages currently use broad wording like `INTRADAY UPDATE`
- existing pick status and new opportunities can appear in one ambiguous flow
- a message about a model pick can feel like it is describing the user's actual position

Implementation approach:

- change intraday message structure into two explicit sections:
  - `MODEL POSITION UPDATES`
  - `WATCH-ONLY INTRADAY IDEAS`
- include pick date and trade type in model position updates
- use phrases like `model pick`, `model stop-loss`, `model take-profit`
- avoid phrases like `your position`, `you are down`, `you should sell`, `you should buy`
- keep watch-only ideas clearly labeled as not official picks

Likely files affected:

- `scripts/intraday_monitor.py`
- `scripts/send_intraday_telegram.py`
- `tests/test_telegram_dual_section.py`
- intraday monitor tests

Data artifacts:

- no new artifact required initially
- existing `data/intraday_alert_YYYY-MM-DD.md` may change format

Tests:

- verify both sections can appear independently
- verify empty sections are omitted
- verify watch-only disclaimer is present
- verify model position wording does not imply user ownership
- verify Telegram message stays under length limits

Product impact:

- reduces user confusion
- improves professionalism
- strengthens compliance posture
- makes alerts easier for busy users to understand

Architecture impact:

- short-term: improve existing formatter
- long-term: should move into unified notification renderer

Risks:

- Markdown formatting errors can break Telegram rendering
- too much wording can make messages long
- changing message format may require updating tests

Promotion or validation gate:

- CI green
- manual review of sample Telegram output

### Feature: Clean Active Pick Loading

Status:

- planned

Priority:

- very high

Why it matters:

- intraday monitor should monitor true active official model picks
- it should not indefinitely monitor stale old picks
- it should not monitor watch-only ideas as if they are official positions

Current gap:

- current loading logic focuses on today's picks and falls back to most recent pick date
- this can miss older still-active swing picks
- this can also create confusing fallback behavior
- pick date and trade type are not included in current intraday alert payload

Implementation approach:

- replace `load_todays_picks()` with a clearer `load_active_model_positions()`
- load all unresolved official picks from `data/picks_log.csv`
- exclude watch-only rows
- exclude closed terminal statuses
- respect trade type and age
- include metadata needed for clear message rendering

Suggested active rules:

- day trade: monitor same ET trading day only
- swing trade: monitor while pending/open, up to a defined max age
- monster research: exclude unless explicitly promoted to model position
- watch_only: exclude from position monitoring
- closed statuses: exclude

Closed statuses should include:

- `sl_hit`
- `tp_hit`
- `day_close`
- `closed`
- `expired`
- `unreachable_entry`
- any future terminal status

Likely files affected:

- `scripts/intraday_monitor.py`
- `src/picks_csv.py`
- `tests/test_intraday_monitor_csv_close.py`
- `tests/test_position_monitor.py`
- new or updated active-pick loading tests

Data artifacts:

- no new artifact required
- `data/picks_log.csv` remains source of truth for official model picks

Tests:

- day trade from today is included
- day trade from previous trading day is excluded
- swing trade still pending is included
- old stale swing beyond max age is excluded
- watch-only row is excluded
- closed statuses are excluded
- pick date and trade type are preserved in alert payload

Product impact:

- position updates become more accurate
- stale monitoring noise is reduced
- watch-only and official pick semantics remain separate

Architecture impact:

- moves system toward formal model-position lifecycle
- reduces date-fallback ambiguity

Risks:

- changing loading logic can accidentally stop monitoring valid swing picks
- max-age rule must be chosen carefully
- old CSV rows may have missing trade_type/status values

Promotion or validation gate:

- CI green
- inspect sample active pick list from current `data/picks_log.csv`

### Feature: Scanner Independence from Active Picks

Status:

- planned

Priority:

- very high

Why it matters:

- the intraday scanner should still find watch-only opportunities even when there are no active official picks
- no-pick days should not mean no intraday observation collection
- evidence collection should continue independently

Current gap:

- current intraday monitor exits early when no picks are loaded
- this can skip opening-range and momentum scans
- this can prevent watch-only evidence from being collected

Implementation approach:

- update intraday monitor flow:
  1. load active model positions
  2. monitor active positions if any
  3. run scanner if scanner window is open
  4. write observations
  5. send Telegram only if model updates or watch-only ideas exist
- do not require active picks to scan
- if no active picks and no scanner candidates, write run-status as completed/no_alerts

Likely files affected:

- `scripts/intraday_monitor.py`
- `scripts/intraday_scanner.py`
- `tests/test_intraday_monitor_workflow.py`
- `tests/test_intraday_monitor_workflow_observations.py`
- `tests/test_intraday_monitor_workflow_schedule.py`

Data artifacts:

- existing:
  - `data/opening_range_run_status_YYYY-MM-DD.jsonl`
  - `data/opening_range_observations_YYYY-MM-DD.jsonl`
  - `data/intraday_momentum_observations_YYYY-MM-DD.jsonl`

Tests:

- scanner runs when active pick list is empty
- scanner does not send Telegram when no candidates exist
- run-status records completed/no_alerts instead of skipped/no_picks
- existing-pick monitoring still works when picks exist

Product impact:

- intraday learning continues on days with no official picks
- better evidence collection
- fewer blind spots

Architecture impact:

- separates monitor and scanner responsibilities
- prepares for future independent scanner workflow if needed

Risks:

- more workflow runs may write more artifacts
- duplicate observations need dedupe rules
- Telegram must not send empty or noisy messages

Promotion or validation gate:

- CI green
- one trading-day observation review

## Phase 2: Unified Candidate and Outcome Lifecycle

### Feature: Unified Candidate Lifecycle

Status:

- planned

Priority:

- very high

Why it matters:

- the product currently has several related concepts: picks, candidates, observations, watch-only ideas, news signals, and model positions
- these concepts must not be mixed
- a unified lifecycle makes learning, reporting, promotion, and user messaging safer

Current gap:

- official picks live in `data/picks_log.csv`
- late watch-only ideas live in late daily artifacts
- opening-range observations live in opening-range artifacts
- intraday momentum observations live in momentum artifacts
- news signals live in news artifacts
- there is no single lifecycle definition connecting these states

Proposed lifecycle states:

1. `raw_signal`
2. `candidate`
3. `watch_only_candidate`
4. `paper_candidate`
5. `official_pick`
6. `active_model_position`
7. `closed_model_position`
8. `evaluated_outcome`
9. `learning_sample`
10. `recalibration_proposal`
11. `approved_model_change`

State definitions:

- `raw_signal`: an unverified signal from news, price action, pattern, or scanner
- `candidate`: a structured idea with enough fields for scoring
- `watch_only_candidate`: a monitored idea that is not an official pick
- `paper_candidate`: a candidate promoted to paper validation after evidence
- `official_pick`: a user-facing model pick
- `active_model_position`: an unresolved official pick being monitored
- `closed_model_position`: an official pick with terminal outcome
- `evaluated_outcome`: measured forward result
- `learning_sample`: outcome joined with original features
- `recalibration_proposal`: suggested model/config change
- `approved_model_change`: human-approved change to model behavior

Implementation approach:

- document lifecycle first
- add lifecycle fields to future artifacts
- do not migrate all historical data immediately
- start with intraday candidate and outcome artifacts
- later align late daily ideas, news signals, and official picks

Suggested common fields:

- `candidate_id`
- `date`
- `timestamp_et`
- `timestamp_utc`
- `lane`
- `source`
- `scanner`
- `ticker`
- `model_name`
- `model_version`
- `feature_set_version`
- `threshold_set_version`
- `state`
- `watch_only`
- `official_pick`
- `paper_trading_enabled`
- `live_trading_enabled`
- `score`
- `entry_reference`
- `stop_reference`
- `target_reference`
- `risk_reward`
- `features`
- `blockers`
- `reason`
- `disclaimer`

Likely files affected:

- future `src/model_lifecycle.py`
- future `src/candidate_schema.py`
- `scripts/intraday_scanner.py`
- `scripts/intraday_monitor.py`
- `scripts/generate_late_daily_ideas.py`
- `scripts/news_signal_outcome_attribution.py`
- `src/pick_logger.py`

Data artifacts:

- future `data/candidates_YYYY-MM-DD.jsonl`
- future `data/outcomes_YYYY-MM-DD.jsonl`
- or lane-specific artifacts such as:
  - `data/intraday_candidates_YYYY-MM-DD.jsonl`
  - `data/intraday_outcomes_YYYY-MM-DD.jsonl`

Tests:

- candidate schema required fields
- candidate ID is deterministic or traceable
- watch-only candidates cannot become official picks without promotion
- official picks must have clear model metadata
- paper/live flags default false

Product impact:

- clearer product semantics
- better trust
- easier reporting
- safer promotion from watch-only to official

Architecture impact:

- creates a shared backbone for future features
- reduces artifact fragmentation over time

Risks:

- over-designing too early
- breaking existing CSV/report assumptions
- duplicating data before migration plan is clear

Promotion or validation gate:

- docs approved first
- implement for intraday only first
- expand to other lanes after stable

### Feature: Intraday Candidate Snapshot

Status:

- planned

Priority:

- very high

Why it matters:

- the intraday system cannot learn unless every candidate is saved with full context
- Telegram alerts alone are not enough
- the model needs evidence for both alerted and non-alerted candidates

Current gap:

- opening-range observations exist
- intraday momentum observations exist
- but there is no unified intraday candidate artifact containing all features, blockers, model version, and references

Implementation approach:

- create a normalized intraday candidate builder
- write every scanner candidate to `data/intraday_candidates_YYYY-MM-DD.jsonl`
- include candidates even if they are blocked, if practical
- include model version and feature values
- keep watch-only flags explicit
- do not mutate official pick stats

Suggested fields:

- `candidate_id`
- `date`
- `timestamp_et`
- `timestamp_utc`
- `ticker`
- `scanner`
- `model_name`
- `model_version`
- `feature_set_version`
- `threshold_set_version`
- `watch_only`
- `mode`
- `price`
- `entry_reference`
- `stop_reference`
- `target_reference`
- `risk_reward`
- `score`
- `features`
- `blockers`
- `market_context`
- `reason`
- `alert_sent`
- `telegram_fingerprint`

Likely files affected:

- `scripts/intraday_scanner.py`
- `scripts/intraday_monitor.py`
- future `src/intraday_candidate_schema.py`
- future `src/model_version.py`

Data artifacts:

- `data/intraday_candidates_YYYY-MM-DD.jsonl`

Tests:

- candidate rows are valid JSONL
- required fields exist
- watch-only is always true until promotion
- blocked candidates can be recorded without alerting
- alert_sent is accurate
- candidate_id remains stable enough for outcome joins

Product impact:

- enables future learning
- makes intraday model auditable
- supports promotion gates
- improves trust by preserving evidence

Architecture impact:

- creates first step toward unified candidate lifecycle
- separates candidate recording from Telegram sending

Risks:

- artifact size may grow
- duplicate rows across workflow runs
- candidate ID design must support repeated scans
- noisy candidates may reduce report usefulness unless filtered

Promotion or validation gate:

- write artifact for at least several trading sessions
- manually inspect sample rows
- no official stats mutation

### Feature: Intraday Outcome Tracking

Status:

- planned

Priority:

- very high

Why it matters:

- a candidate snapshot is only useful if later joined with outcomes
- the model must learn whether candidates worked after 15, 30, 60 minutes and by end of day
- future promotion requires measured expectancy, not intuition

Current gap:

- official picks have evaluation
- news signal outcomes have a scaffold
- intraday watch-only candidates do not yet have complete forward outcome tracking

Implementation approach:

- create an evaluator for intraday candidates
- load `data/intraday_candidates_YYYY-MM-DD.jsonl`
- fetch forward intraday prices
- calculate horizon outcomes
- calculate whether target or stop was reached first where possible
- write results to JSONL
- keep this separate from official pick evaluation

Evaluation horizons:

- `15m`
- `30m`
- `60m`
- `eod`

Suggested fields:

- `candidate_id`
- `date`
- `ticker`
- `scanner`
- `candidate_timestamp_et`
- `evaluation_timestamp_et`
- `horizon`
- `entry_reference`
- `stop_reference`
- `target_reference`
- `price_at_horizon`
- `max_favorable_excursion`
- `max_adverse_excursion`
- `tp_before_sl`
- `sl_before_tp`
- `end_return_pct`
- `r_multiple`
- `data_quality`

Likely files affected:

- future `scripts/evaluate_intraday_candidates.py`
- future `src/intraday_outcomes.py`
- `scripts/daily_watch_only_learning_report.py`
- `.github/workflows/intraday_monitor.yml` or new workflow

Data artifacts:

- `data/intraday_outcomes_YYYY-MM-DD.jsonl`

Tests:

- outcome rows join to candidate IDs
- missing price data produces data_quality warning
- R multiple calculation is correct
- TP-before-SL and SL-before-TP logic is deterministic
- official pick stats are not modified

Product impact:

- enables real evidence-based intraday learning
- helps decide if WATCH ONLY can become paper-traded
- reveals best/worst scanners and time buckets

Architecture impact:

- creates reusable pattern for watch-only outcome evaluation

Risks:

- intraday historical data may be incomplete from free providers
- yfinance 5m data may be delayed or inconsistent
- path must avoid lookahead bias
- stop/target ordering can be ambiguous with 5-minute bars

Promotion or validation gate:

- collect at least 100 to 200 candidates before promotion decisions
- require positive expectancy before paper validation

### Feature: Daily Intraday Learning Report

Status:

- planned

Priority:

- high

Why it matters:

- raw candidate and outcome files are useful but hard to review manually
- the product needs a daily summary of what worked and what failed
- this report helps decide which scanner logic is improving

Current gap:

- watch-only learning report v1 exists
- but there is no dedicated intraday learning report with candidate/outcome metrics

Implementation approach:

- read intraday candidates and outcomes
- aggregate by scanner, time bucket, feature bucket, and ticker
- summarize hit rates and R multiples
- identify best and worst setups
- keep the report monitoring-only
- do not propose automatic threshold changes in the daily report

Suggested sections:

- candidate count
- alert count
- outcome coverage
- win rate
- average R
- median R
- profit factor
- best scanner
- worst scanner
- best time bucket
- worst time bucket
- best feature bucket
- worst feature bucket
- notable false positives
- notable missed opportunities
- data quality issues

Likely files affected:

- future `scripts/intraday_learning_report.py`
- future `src/intraday_learning.py`
- `scripts/daily_watch_only_learning_report.py`

Data artifacts:

- `data/intraday_learning_report_YYYY-MM-DD.json`
- optional `data/intraday_learning_report_YYYY-MM-DD.md`

Tests:

- report handles no candidates
- report handles candidates with missing outcomes
- metrics are calculated correctly
- monitoring-only flags are present
- official pick stats are not modified

Product impact:

- makes daily review faster
- improves founder/co-founder feedback loop
- supports evidence-based promotion

Architecture impact:

- creates reporting layer over candidate/outcome lifecycle

Risks:

- small daily sample sizes can mislead
- report should not overfit one day
- missing price data may distort metrics

Promotion or validation gate:

- produce reports for multiple trading sessions before using for decisions

### Feature: Weekly Intraday Recalibration Report

Status:

- planned

Priority:

- high

Why it matters:

- weekly aggregation is more useful than one-day noise
- the model needs structured recommendations for threshold changes
- human approval should remain required before changes affect production

Current gap:

- weight proposals exist in the repo
- but intraday-specific recalibration is not yet defined

Implementation approach:

- aggregate one or more weeks of intraday outcomes
- compare performance by scanner and feature bucket
- propose threshold adjustments
- mark recommendations as human-review-required
- do not auto-apply changes initially

Suggested recommendations:

- opening-range breakout threshold changes
- volume-ratio threshold changes
- gap guard changes
- VWAP distance guard changes
- time bucket suppression
- scanner promotion/demotion
- alert threshold adjustment
- watch-only to paper-trading readiness assessment

Likely files affected:

- future `scripts/intraday_recalibration_report.py`
- future `src/intraday_recalibration.py`
- future config model files

Data artifacts:

- `data/intraday_recalibration_report_YYYY-MM-DD.json`
- optional `data/intraday_recalibration_report_YYYY-MM-DD.md`

Tests:

- recommendations are generated only with enough sample size
- report does not auto-modify config
- low-confidence recommendations are labeled clearly
- human approval flag is required

Product impact:

- improves model safely
- creates disciplined learning cadence
- avoids emotional one-off changes

Architecture impact:

- bridges learning evidence and config-driven thresholds

Risks:

- overfitting
- changing too many thresholds at once
- sample size bias
- regime-specific false conclusions

Promotion or validation gate:

- require minimum sample size
- require human approval
- require forward validation after any threshold change

## Phase 3: Intraday Feature Extraction and Scoring

### Feature: Intraday Feature Extractor

Status:

- planned

Priority:

- high

Why it matters:

- the repo already has many indicators, but intraday scanner does not yet use them deeply
- feature extraction should be centralized so candidates, scoring, reports, and learning use the same definitions

Current gap:

- `src/indicators.py` has useful indicators
- opening-range and momentum scanner use simpler rules
- no dedicated intraday feature object exists

Implementation approach:

- create `src/intraday_features.py`
- reuse `src/indicators.py`
- compute features from 5-minute bars and daily context
- output a JSON-safe feature dictionary
- include feature dictionary in intraday candidate snapshots
- use explainable features before complex ML

Initial feature groups:

- price action
- opening range
- VWAP
- EMA trend
- RSI
- MACD
- ATR / volatility
- volume / liquidity
- support / resistance
- candlestick / wick quality
- market alignment
- sector alignment
- time of day

Likely files affected:

- future `src/intraday_features.py`
- `scripts/intraday_scanner.py`
- `src/opening_range_scanner.py`
- `src/indicators.py`

Data artifacts:

- features embedded in `data/intraday_candidates_YYYY-MM-DD.jsonl`

Tests:

- feature extractor handles empty bars
- feature extractor handles missing volume
- output is JSON-serializable
- VWAP distance is calculated correctly
- RSI/MACD/ATR fields exist when enough bars exist
- no exception from short histories

Product impact:

- scanner becomes more chart-aware
- candidate explanations improve
- future learning becomes feature-based

Architecture impact:

- creates reusable feature layer
- reduces duplicated indicator logic

Risks:

- indicator soup
- too many low-quality features
- false precision from short intraday histories
- free data limitations

Promotion or validation gate:

- feature values logged first
- scoring weights changed only after evidence

### Feature: Explainable Intraday Scoring Model

Status:

- planned

Priority:

- high

Why it matters:

- the scanner should not just alert because a stock is moving
- it should rank candidates by evidence quality
- explainable scoring is safer than complex ML before enough data exists

Current gap:

- legacy momentum score is simple
- opening-range score is basic
- no full feature-weighted intraday scoring model exists yet

Implementation approach:

- create an explainable score out of 100
- start with conservative weights
- log all sub-scores
- do not auto-promote to official picks
- use outcomes to adjust weights later

Suggested initial score:

- price action / structure: 25
- volume / liquidity: 20
- VWAP / trend alignment: 15
- relative strength / market alignment: 15
- technical momentum indicators: 10
- risk/reward quality: 10
- catalyst / time quality: 5

Suggested hard blockers:

- spread too wide
- dollar volume too low
- price below VWAP unless reclaim setup
- distance above VWAP too extended
- gap too large
- opening-range extension too large
- risk/reward too poor
- stop distance too wide
- stop distance too tight
- market strongly against candidate
- sector strongly against candidate
- same ticker already alerted today
- known halt or extreme liquidity risk

Likely files affected:

- future `src/intraday_score.py`
- future `src/intraday_features.py`
- `scripts/intraday_scanner.py`
- future config files

Data artifacts:

- score and sub-scores embedded in `data/intraday_candidates_YYYY-MM-DD.jsonl`

Tests:

- score is bounded 0 to 100
- hard blockers are recorded
- blocked candidate does not alert
- scoring handles missing features
- score explanation is JSON-safe

Product impact:

- better candidate quality
- fewer low-quality alerts
- easier user trust
- future paper-trading gate becomes measurable

Architecture impact:

- separates scanning from scoring
- scoring can be versioned and recalibrated

Risks:

- arbitrary initial weights
- overconfidence before outcome data
- feature correlations can double-count signals

Promotion or validation gate:

- score only controls watch-only ranking initially
- no official promotion until outcome metrics pass

### Feature: Intraday Promotion Gates

Status:

- planned

Priority:

- very high

Why it matters:

- WATCH ONLY ideas must not become official intraday picks without evidence
- promotion gates protect users and product trust
- clear gates prevent emotional decisions after one good day

Current gap:

- intraday ideas are watch-only
- promotion criteria are discussed but not implemented as a formal gate

Implementation approach:

- define maturity levels
- calculate readiness from tracked outcomes
- keep gates conservative
- require human approval before promotion

Suggested maturity levels:

- Level 0: internal observation only
- Level 1: Telegram watch-only ideas
- Level 2: paper-traded intraday model
- Level 3: official intraday model picks
- Level 4: possible automation research only, not active

Promotion from Level 1 to Level 2 requires:

- at least 100 to 200 tracked candidates
- at least several trading weeks
- win rate at or above 60%
- positive average R
- profit factor above 1.3
- acceptable max drawdown
- stable performance across more than one market regime
- no major data-quality issue
- founder approval

Promotion from Level 2 to Level 3 requires:

- successful paper validation
- stable forward performance
- no severe Telegram/product confusion
- documented risk controls
- documented user-facing language
- founder approval

Likely files affected:

- future `scripts/intraday_readiness.py`
- future `src/intraday_readiness.py`
- future learning/recalibration reports
- `docs/reference/intraday_model_strategy.md`

Data artifacts:

- `data/intraday_readiness_YYYY-MM-DD.json`
- optional readiness Markdown report

Tests:

- readiness fails with insufficient sample size
- readiness fails with negative expectancy
- readiness fails with poor data quality
- readiness requires explicit approval flag for promotion

Product impact:

- protects trust
- creates a disciplined path from observation to official product
- avoids premature intraday alerting

Architecture impact:

- formalizes validation before promotion
- aligns with existing monitoring/paper/live safety gates

Risks:

- thresholds may be too strict or too loose
- small sample outperformance may not persist
- regime changes can invalidate prior performance

Promotion or validation gate:

- this feature itself is a gate
- should be implemented before any official intraday pick promotion

## Phase 4: Shared Architecture Improvements

### Feature: Unified Notification Renderer

Status:

- planned

Priority:

- high

Why it matters:

- the repo has many Telegram sender scripts
- inconsistent wording can confuse users
- disclaimers, watch-only labels, and message structure should be centralized

Current gap:

- Telegram formatting is spread across many scripts
- different senders can use different language and safety wording
- dedupe behavior is not fully centralized

Examples of sender scripts:

- `scripts/send_telegram.py`
- `scripts/send_intraday_telegram.py`
- `scripts/send_late_daily_ideas_telegram.py`
- `scripts/send_dashboard_telegram.py`
- `scripts/send_exec_telegram.py`
- `scripts/send_layman_daily.py`
- `scripts/send_layman_evening.py`
- `scripts/send_layman_weekly.py`
- `scripts/send_layman_monthly.py`
- `scripts/send_layman_yearly.py`
- `scripts/send_meta_brain_telegram.py`
- `scripts/send_position_alerts.py`
- `scripts/send_weekend_telegram.py`
- `scripts/send_weekly_review.py`

Implementation approach:

- create a shared notification package
- keep scripts as workflow entrypoints
- move message rendering into shared functions
- move Telegram send logic into one client
- standardize disclaimers and watch-only language
- standardize Markdown escaping and length truncation

Suggested package:

- `src/notifications/__init__.py`
- `src/notifications/telegram_client.py`
- `src/notifications/renderer.py`
- `src/notifications/templates.py`
- `src/notifications/dedupe.py`

Suggested message types:

- `daily_official_picks`
- `daily_no_pick_report`
- `late_watch_only_ideas`
- `model_position_update`
- `watch_only_intraday_ideas`
- `news_alert`
- `daily_execution_report`
- `weekly_review`
- `monthly_report`
- `monster_research_report`

Tests:

- each message type renders without error
- Telegram Markdown is safe
- messages include required disclaimer
- watch-only messages include watch-only wording
- official pick messages include model-pick wording
- long messages are truncated safely
- missing optional fields do not crash rendering

Product impact:

- clearer user experience
- safer language
- less duplicate code
- easier future UI changes

Architecture impact:

- reduces sender script sprawl
- creates one notification layer
- makes tests easier

Risks:

- refactor can accidentally change live message behavior
- Markdown parse errors can prevent Telegram delivery
- migration should be incremental

Promotion or validation gate:

- implement one sender first
- compare old and new sample output
- migrate other senders gradually

### Feature: Data Contracts

Status:

- planned

Priority:

- high

Why it matters:

- many artifacts exist across `data/`
- future learning depends on stable schemas
- schema drift can silently break reports and evaluations

Current gap:

- some tests check CSV columns
- some artifacts are documented in separate places
- there is no central data contract document for all important artifacts

Implementation approach:

- create a data contract document first
- later add lightweight schema validation helpers
- define required and optional fields
- define ownership for each artifact
- define whether artifact is official, watch-only, research-only, or operational

Suggested doc:

- `docs/planning/DATA_CONTRACTS.md`

Important artifacts to document:

- `data/picks_log.csv`
- `data/daily_picks_run_status_YYYY-MM-DD.jsonl`
- `data/daily_picks_no_pick_report_YYYY-MM-DD.json`
- `data/daily_picks_candidate_rejections_YYYY-MM-DD.json`
- `data/late_daily_ideas_YYYY-MM-DD.jsonl`
- `data/opening_range_observations_YYYY-MM-DD.jsonl`
- `data/opening_range_bars/YYYY-MM-DD/TICKER.jsonl`
- `data/opening_range_run_status_YYYY-MM-DD.jsonl`
- `data/intraday_momentum_observations_YYYY-MM-DD.jsonl`
- future `data/intraday_candidates_YYYY-MM-DD.jsonl`
- future `data/intraday_outcomes_YYYY-MM-DD.jsonl`
- `data/news_log.jsonl`
- `data/news_signals.json`
- `data/news_signal_outcomes_YYYY-MM-DD.jsonl`
- `data/signal_journal.jsonl`
- `data/learning_journal.jsonl`
- `data/weight_proposals.jsonl`

Tests:

- schema doc references existing artifacts
- required fields are validated for new artifacts
- malformed rows produce warnings instead of silent failure
- official and watch-only artifacts remain separated

Product impact:

- fewer broken reports
- better trust in learning data
- easier onboarding for future development

Architecture impact:

- creates stable contracts between scripts
- reduces accidental coupling

Risks:

- too much schema rigidity can slow iteration
- old artifacts may not match new contracts
- validation should start as warning-only

Promotion or validation gate:

- document first
- validate new artifacts first
- migrate old artifacts only when needed

### Feature: Config-Driven Model Thresholds

Status:

- planned

Priority:

- high

Why it matters:

- many thresholds are currently embedded in code
- learning and recalibration should propose config changes, not require code edits
- versioned configs make experiments easier to audit

Current gap:

- `config.yaml` centralizes some daily/swing/monster settings
- intraday scanner thresholds are still partly hardcoded
- opening-range and momentum thresholds should become configurable

Examples of thresholds to externalize:

- opening-range length
- minimum breakout percent
- minimum volume ratio
- maximum gap percent
- maximum extension percent
- new opportunity cutoff time
- legacy momentum change percent
- legacy momentum volume ratio
- watch-only alert threshold
- paper-trading readiness threshold
- official promotion threshold
- VWAP distance guard
- risk/reward minimum

Implementation approach:

- start with intraday thresholds
- keep defaults equivalent to current behavior
- add config loader with safe fallbacks
- include threshold_set_version in candidate artifacts
- allow weekly recalibration reports to propose config changes
- do not auto-apply threshold changes initially

Possible structure:

- `config.yaml` with a new `intraday:` section
- or future split files:
  - `config/models/daily_swing.yml`
  - `config/models/intraday.yml`
  - `config/models/monster.yml`

Likely files affected:

- `config.yaml`
- `scripts/intraday_scanner.py`
- future `src/config_loader.py`
- future `src/intraday_score.py`
- future `src/intraday_features.py`

Tests:

- config defaults match current behavior
- missing config falls back safely
- invalid threshold values are rejected or warned
- candidate artifact records threshold_set_version
- recalibration report does not mutate config automatically

Product impact:

- safer tuning
- easier experimentation
- better auditability

Architecture impact:

- separates policy from code
- supports model versioning and recalibration

Risks:

- too many config knobs can create confusion
- misconfigured thresholds can suppress useful alerts or create noise
- config validation is important

Promotion or validation gate:

- introduce config in observe-compatible way
- verify current scanner behavior does not materially change

### Feature: Model Versioning

Status:

- planned

Priority:

- high

Why it matters:

- the agent needs to know which model version produced which candidate or pick
- without model versioning, learning can confuse old and new behavior
- versioning is required for reliable attribution

Current gap:

- some fields and reports imply model behavior
- but model_name, model_version, feature_set_version, and threshold_set_version are not consistently present everywhere

Implementation approach:

- define version metadata helper
- stamp all future candidate and outcome artifacts
- eventually stamp official picks and learning samples
- include Git commit SHA and workflow run metadata where useful
- update reports to group outcomes by model version

Suggested metadata:

- `model_name`
- `model_version`
- `feature_set_version`
- `threshold_set_version`
- `scorer_version`
- `created_by_workflow`
- `github_run_id`
- `github_sha`
- `code_ref`

Likely files affected:

- future `src/model_version.py`
- `main.py`
- `scripts/intraday_scanner.py`
- `scripts/intraday_monitor.py`
- `src/pick_logger.py`
- future candidate/outcome schema modules

Data artifacts:

- future candidate and outcome JSONL rows
- eventually `data/picks_log.csv` may add version fields if needed

Tests:

- version metadata exists in new artifacts
- missing GitHub env vars do not break local runs
- reports can group by model version
- version strings are stable and explicit

Product impact:

- better learning attribution
- easier debugging
- safer model evolution

Architecture impact:

- supports future experiment tracking
- supports rollback decisions

Risks:

- too much metadata can clutter artifacts
- changing CSV columns requires care
- versioning discipline must be maintained

Promotion or validation gate:

- implement first for new intraday artifacts
- expand to official picks later

## Phase 5: Monster Hunter and Fundamental Research

### Feature: Monster Hunter Thesis State Machine

Status:

- planned

Priority:

- medium-high

Why it matters:

- long-term compounder research must not be mixed with swing trades
- a failed swing trade must not silently become a long-term hold
- monster candidates need thesis states, not just entry/SL/TP

Current gap:

- `docs/strategy/MONSTER_HUNTER_DESIGN.md` defines the concept
- `monster_score` exists
- but no formal thesis state artifact exists yet

Implementation approach:

- create research-only monster thesis artifacts
- define allowed states
- update state only through explicit evidence
- include thesis-break conditions
- never mutate official pick stats
- never create paper/live trades from Monster Hunter output

Allowed states:

- `candidate`
- `researching`
- `watchlist`
- `starter_position_candidate`
- `confirmed_compounder`
- `core_hold`
- `add_on_zone`
- `trim_zone`
- `exit_watch`
- `thesis_broken`
- `rejected`

Likely files affected:

- future `src/monster_thesis.py`
- future `scripts/monster_research_report.py`
- `src/monster_hunt.py`
- `src/monster_data.py`

Data artifacts:

- `data/monster_themes_YYYY-MM-DD.jsonl`
- `data/monster_candidates_YYYY-MM-DD.jsonl`
- `data/monster_theses_YYYY-MM-DD.jsonl`
- `data/monster_state_transitions_YYYY-MM-DD.jsonl`
- `reports/monster_hunter_report_YYYY-MM-DD.md`

Tests:

- monster outputs are research-only
- monster artifacts do not write to `picks_log.csv`
- invalid state transitions are rejected
- thesis-break conditions are required
- no paper/live flags are enabled

Product impact:

- creates a serious long-term research product lane
- prevents confusion between trading and investing
- improves trust around long-term ideas

Architecture impact:

- separates long-term thesis lifecycle from trade lifecycle

Risks:

- data source limitations for fundamentals
- subjective thesis scoring
- overconfidence in long-term narratives
- accidental contamination of official picks

Promotion or validation gate:

- research-only first
- no official scoring influence without founder approval
- historical and forward validation required

### Feature: Fundamental Quality and Pump-Risk Smell

Status:

- planned

Priority:

- high

Why it matters:

- speculative news spikes can look attractive but fail as swing or monster candidates
- low-quality companies should not be treated the same as high-quality compounders
- the agent should identify pump-risk and long-term value destruction

Current gap:

- smell faculty exists
- fundamentals exist in some scoring paths
- but pump-risk / fundamental-quality smell is not yet strong enough

Signals to consider:

- huge drawdown from all-time high
- weak long-term trend
- low liquidity
- repeated dilution
- reverse-split history if available
- negative revenue growth
- negative margin trend
- poor free cash flow
- weak balance sheet
- contract-news spike from low-quality company
- sudden high-volume move after long-term decline
- excessive gap without institutional-quality catalyst

Implementation approach:

- start in observe mode
- add warnings before blockers
- preserve smell codes in artifacts
- measure outcomes before enforcement
- avoid unfairly blocking legitimate turnarounds too early

Likely files affected:

- `src/smell_faculty.py`
- `src/fundamentals.py`
- `src/monster_data.py`
- `src/hard_blocks.py`
- `main.py`
- future intraday feature/scoring modules

Data artifacts:

- smell fields in `data/picks_log.csv`
- smell fields in future candidate artifacts
- learning reports grouped by smell code

Tests:

- high-risk patterns generate warnings
- warnings do not block in observe mode
- blocker mode requires explicit enforcement flag
- smell fields are persisted
- missing fundamental data does not crash scoring

Product impact:

- improves quality control
- reduces speculative low-quality picks
- helps separate intraday tradeability from long-term investability

Architecture impact:

- strengthens shared risk layer across lanes

Risks:

- false positives can block turnaround winners
- fundamental data may be stale or incomplete
- overly strict rules can reduce pick count too much

Promotion or validation gate:

- observe-mode evidence first
- enforce only after measured benefit

### Feature: Quarterly and Yearly Fundamental Analyzer

Status:

- planned

Priority:

- medium-high

Why it matters:

- swing and monster candidates should understand business quality
- price/news alone is not enough for multi-day or long-term conviction
- fundamentals help avoid low-quality speculative names

Current gap:

- basic fundamentals and earnings analysis exist
- Monster Hunter design requires deeper business analysis
- no full quarterly/yearly P&L thesis report exists yet

Implementation approach:

- begin as research-only
- collect available public fundamentals
- compute multi-period trends
- summarize improvement or deterioration
- add warnings for weak quality
- keep output separate from official picks until validated

Metrics to analyze:

- revenue growth
- EPS growth
- gross margin trend
- operating margin trend
- net income trend
- free cash flow trend
- debt and liquidity
- share dilution
- guidance trend
- earnings surprise history
- valuation versus growth
- valuation versus peers
- sector and industry tailwind

Likely files affected:

- `src/fundamentals.py`
- `src/earnings_analyzer.py`
- `src/monster_data.py`
- future `src/fundamental_quality.py`
- future `scripts/fundamental_research_report.py`

Data artifacts:

- `data/fundamental_quality_YYYY-MM-DD.jsonl`
- `reports/fundamental_research_report_YYYY-MM-DD.md`
- future fields in monster thesis artifacts

Tests:

- handles missing financial statements
- handles negative or zero values safely
- outputs JSON-safe metrics
- does not affect official picks unless explicitly wired
- research-only flags are present

Product impact:

- improves swing quality
- supports Monster Hunter
- improves explainability
- helps users understand business quality

Architecture impact:

- adds research layer shared by swing and monster lanes

Risks:

- free data may be incomplete
- financial statement formats vary
- fundamental data can lag
- valuation comparisons may be noisy

Promotion or validation gate:

- research-only first
- observe impact before adding scoring influence

## Phase 6: Historical Learning and Backtesting

### Feature: Historical Intraday Replay

Status:

- planned

Priority:

- medium

Why it matters:

- live evidence collection is slow
- historical replay can accelerate learning
- intraday model should understand different market conditions before promotion

Current gap:

- backtesting exists
- opening-range observation backtest exists
- but full historical intraday replay is not mature

Implementation approach:

- replay historical 5-minute bars where available
- run current opening-range and intraday feature logic on old sessions
- calculate forward outcomes
- compare rules across time and regime
- avoid lookahead bias
- keep train/test time splits

Likely files affected:

- `scripts/backtest_opening_range_observations.py`
- future `scripts/backtest_intraday_candidates.py`
- future `src/intraday_backtester.py`
- `src/opening_range_scanner.py`
- future `src/intraday_features.py`
- future `src/intraday_score.py`

Data artifacts:

- `data/backtests/intraday_replay_YYYY-MM-DD.jsonl`
- `reports/intraday_backtest_report_YYYY-MM-DD.md`

Tests:

- no lookahead bias
- historical candidates match expected timestamps
- outcome calculation is deterministic
- train/test split is respected
- missing bars are handled safely

Product impact:

- faster model learning
- better confidence before paper validation
- ability to compare scanner versions

Architecture impact:

- connects scanner, feature extractor, scoring, and outcome engine

Risks:

- historical intraday data availability
- survivorship bias
- lookahead bias
- overfitting to old market conditions

Promotion or validation gate:

- use historical replay for evidence
- require forward live observation before promotion

### Feature: Historical Regime Learning

Status:

- planned

Priority:

- medium

Why it matters:

- the agent cannot wait years to experience every market regime
- strategies behave differently in bull, bear, sideways, high-volatility, and crisis markets
- risk controls should adapt to regime

Current gap:

- regime checks exist
- historical regime learning is documented as a roadmap item
- no full regime-tagged learning system exists yet

Implementation approach:

- define historical regime periods
- tag backtest and live outcomes by regime
- compare feature and strategy performance by regime
- propose regime-specific thresholds
- keep changes in observe/recommendation mode first

Regimes to study:

- bull markets
- bear markets
- sideways markets
- high VIX periods
- inflation shock periods
- rate-hike cycles
- COVID crash/recovery
- global financial crisis
- dot-com bubble
- sector bubbles and rotations

Likely files affected:

- `src/regime.py`
- `src/market_guard.py`
- future `src/historical_regimes.py`
- future backtest scripts
- future recalibration reports

Data artifacts:

- `data/regime_labels.json`
- `reports/regime_learning_report_YYYY-MM-DD.md`

Tests:

- regime labels are deterministic
- unknown dates handled safely
- outcome reports can group by regime
- recommendations do not auto-apply

Product impact:

- better risk management
- fewer bad-regime false positives
- more mature model behavior

Architecture impact:

- adds context layer for learning and scoring

Risks:

- regime definitions can be subjective
- too many regime buckets reduce sample size
- history may not repeat exactly

Promotion or validation gate:

- use as reporting first
- enforce regime-specific changes only after evidence

### Feature: Reader / Wisdom Ingestion

Status:

- planned

Priority:

- medium

Why it matters:

- the agent should improve from high-quality trading, investing, risk, and market-history knowledge
- lessons from books or research should become testable rules, not vague memory
- rules should remain observe-only until validated

Current gap:

- wisdom base exists
- wisdom hints and consultant concepts exist
- but a full reader/curiosity pipeline is not mature yet

Implementation approach:

- use only legal, allowed, public-domain, licensed, or founder-provided material
- extract lessons into structured rule candidates
- store source metadata
- map lessons to lanes:
  - daily/swing
  - intraday
  - monster
  - risk
  - psychology
  - regime
- keep new rules observe-only
- measure outcomes before enforcement

Suggested wisdom rule fields:

- `rule_id`
- `source_type`
- `source_name`
- `lesson`
- `applies_to_lane`
- `signal`
- `suggested_action`
- `risk`
- `status`
- `evidence_count`
- `promoted`
- `approved_by_founder`

Likely files affected:

- `src/wisdom_base.py`
- `src/wisdom_hint.py`
- `src/wisdom_consultant.py`
- `src/book_ingest.py`
- future `src/reader_engine.py`
- future `scripts/reader_ingest.py`

Data artifacts:

- `data/wisdom/rules.jsonl`
- `data/wisdom/sources.jsonl`
- `data/wisdom/evidence.jsonl`

Tests:

- source metadata is required
- unsupported source types are rejected
- new rules default to observe-only
- no wisdom rule can enforce without approval
- duplicate lessons are deduped

Product impact:

- makes the agent smarter over time
- creates long-term product moat
- improves explainability

Architecture impact:

- turns market knowledge into structured, testable rules

Risks:

- copyright/licensing issues
- low-quality sources can pollute wisdom
- untested rules can overfit or mislead
- source attribution must be handled carefully

Promotion or validation gate:

- founder approval required for any non-observe rule
- evidence required before scoring influence

## Deferred or Not-Yet Features

These features may be valuable later, but should not be implemented now.

### Deferred: Fully Automatic Threshold Mutation

Reason to defer:

- intraday data is noisy
- one unusual day can distort learning
- automatic threshold changes can overfit quickly
- human approval should remain required

Allowed near-term version:

- weekly recalibration recommendations
- no automatic config mutation
- founder-approved changes only

### Deferred: Complex Machine Learning Model

Reason to defer:

- clean candidate and outcome data is not mature enough yet
- explainable weighted scoring is safer initially
- ML without clean labels can learn noise

Allowed near-term version:

- feature logging
- simple explainable scoring
- historical and forward validation

### Deferred: Options Alerts

Reason to defer:

- options add implied volatility, Greeks, expiration, spread, liquidity, and assignment risk
- product and risk complexity increases significantly
- current equity signal quality must mature first

Allowed near-term version:

- no options alerts
- maybe research-only options notes later

### Deferred: Live Trading Automation

Reason to defer:

- legal, financial, product, and technical risk are too high
- readiness gates are not passed
- paper trading itself is still disabled

Allowed near-term version:

- monitoring-only
- paper trading only after explicit readiness and founder approval

### Deferred: Official Monster Hunter Picks

Reason to defer:

- Monster Hunter must first become a research thesis system
- long-term outcomes need more time and evidence
- no speculative news spike should become a monster candidate without fundamentals

Allowed near-term version:

- research-only reports
- watchlist/thesis states
- no official picks
- no paper/live trades

## Recommended Implementation Order

This order should be followed unless a production bug requires urgent attention.

### Documentation First

1. Keep this feature backlog updated.
2. Add or update data contracts.
3. Add or update notification design.
4. Add or update lifecycle documentation.
5. Update `docs/PROJECT_BLUEPRINT.md` with major architectural decisions.
6. Update `docs/NEXT_SESSION.md` at the end of each session.
7. Update `docs/WORK_LOG.md` after meaningful changes.

### Near-Term Build Order

1. Improve intraday Telegram UX.
2. Clean active model-position loading.
3. Let intraday scanner run without active picks.
4. Add intraday candidate snapshots.
5. Add intraday outcome tracking.
6. Add daily intraday learning report.
7. Add intraday feature extractor.
8. Add explainable intraday scoring.
9. Add weekly intraday recalibration report.
10. Add config-driven intraday thresholds.
11. Add model version metadata.
12. Add intraday readiness gate.

### Medium-Term Build Order

1. Unified notification renderer.
2. Data contract validation.
3. Fundamental-quality / pump-risk smell.
4. Quarterly/yearly fundamental analyzer.
5. Monster Hunter thesis state machine.
6. Historical intraday replay.
7. Historical regime learning.
8. Reader / wisdom ingestion.

### Long-Term Build Order

1. Paper-traded intraday model after readiness gates.
2. Official intraday model only after successful paper validation.
3. Monster Hunter research reports and thesis tracking.
4. Possible premium read-only dashboard.
5. Possible portfolio/watchlist intelligence.
6. Automation research only after strong evidence and separate risk review.

## Architecture Principles

Future implementation should follow these principles:

- separate official picks from watch-only ideas
- separate trading lanes by time horizon
- keep monitoring-only as default
- do not mutate official stats from watch-only artifacts
- prefer explicit model state over ambiguous status fields
- write evidence before changing behavior
- make every model change attributable to versioned config/code
- keep Telegram language clear and safe
- make no-pick and rejected-candidate events explainable
- add tests before relying on new behavior
- promote features only after evidence
- avoid overfitting
- avoid indicator complexity without outcome improvement
- keep founder approval for promotion gates

## Product Language Principles

Use language like:

- model pick
- model position update
- watch-only idea
- reference level
- observed price
- monitoring-only
- educational only
- not financial advice

Avoid language like:

- your position
- you should buy
- you should sell
- guaranteed
- safe trade
- sure winner
- official intraday pick before validation
- monster hold without thesis evidence

## Evidence Principles

Every important future feature should answer:

- What evidence did it use?
- What decision did it make?
- What was blocked?
- What was alerted?
- What happened afterward?
- Did the outcome improve?
- Should the rule remain, be down-weighted, or be removed?

## Final Rule

Every feature must earn its place.

A feature should be implemented only if it improves at least one of:

- trust
- clarity
- safety
- evidence collection
- outcome quality
- learning quality
- architectural maintainability

If a feature does not improve the product after evidence is collected, it should be revised, down-weighted, disabled, or removed.
