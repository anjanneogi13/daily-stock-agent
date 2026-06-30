# Data Contracts

## Purpose

This document defines important data artifacts used by Daily Stock Agent.

The goal is to make every artifact understandable, stable, and safe to use for reporting, learning, and future model improvements.

This document should answer:

- what each artifact represents
- whether it is official, watch-only, research-only, or operational
- which workflow or script owns it
- which fields are required
- which fields are optional
- whether the artifact may affect official pick statistics
- whether it may affect paper/live trading
- how it should be validated

## Data Contract Principles

### 1. Official and Watch-Only Data Must Stay Separate

Official picks may affect official pick statistics.

Watch-only ideas must not affect official pick statistics.

Research-only artifacts must not become official picks without explicit promotion and approval.

### 2. Monitoring-Only Is the Default

New artifacts should default to:

- `mode: monitoring_only`
- `watch_only: true`
- `paper_trading_enabled: false`
- `live_trading_enabled: false`

unless a readiness gate and founder approval explicitly say otherwise.

### 3. Every Artifact Should Be Explainable

A future reader should be able to answer:

- why was this row created?
- what script created it?
- what model/scanner created it?
- what timestamp does it represent?
- is it official or watch-only?
- did it send a Telegram alert?
- can it affect stats?

### 4. Prefer Append-Only JSONL for Evidence

For observation, learning, and audit evidence:

- prefer JSONL
- append rows instead of mutating rows
- include timestamps
- include source/scanner/model fields
- include GitHub workflow metadata when useful

CSV may remain appropriate for legacy official pick logs.

### 5. Schema Changes Must Be Backward-Compatible

When adding fields:

- prefer optional fields first
- preserve existing field names
- do not break old reports
- update tests if existing contracts change
- document meaning before relying on the field

### 6. Validation Should Start as Warning-Only

For new artifacts:

- validate required fields
- warn on malformed rows
- avoid crashing learning/reporting because of one bad row
- move to stricter validation only after stable

## Artifact Classification

Use these classifications:

### Official

Artifacts that represent official model picks and can affect official performance stats.

Example:

- `data/picks_log.csv`

### Watch-Only

Artifacts that represent monitored ideas that are not official picks.

Examples:

- `data/late_daily_ideas_YYYY-MM-DD.jsonl`
- `data/opening_range_observations_YYYY-MM-DD.jsonl`
- `data/intraday_momentum_observations_YYYY-MM-DD.jsonl`
- future `data/intraday_candidates_YYYY-MM-DD.jsonl`

### Research-Only

Artifacts used for research, thesis generation, backtesting, or model exploration.

Examples:

- future `data/monster_theses_YYYY-MM-DD.jsonl`
- future `data/fundamental_quality_YYYY-MM-DD.jsonl`
- backtest artifacts

### Operational

Artifacts that describe whether workflows ran, skipped, succeeded, failed, alerted, or wrote evidence.

Examples:

- `data/daily_picks_run_status_YYYY-MM-DD.jsonl`
- `data/opening_range_run_status_YYYY-MM-DD.jsonl`
- `data/news_engine_run_status_YYYY-MM-DD.jsonl`

## Contract: `data/picks_log.csv`

Classification:

- official

Purpose:

- source of truth for official model picks
- tracks entries, stop-losses, take-profits, statuses, outcomes, and learning fields
- used by monitoring, evaluation, reporting, readiness, and learning scripts

Primary owners:

- `main.py`
- `src/pick_logger.py`
- `src/picks_csv.py`
- `scripts/evaluate_picks.py`
- `scripts/intraday_monitor.py`

May affect official pick statistics:

- yes

May affect paper/live trading:

- not by default
- paper/live trading must remain disabled unless explicit readiness and founder approval exist

Required conceptual fields:

- `pick_date`
- `ticker`
- `company`
- `trade_type`
- `watch_only`
- `entry`
- `stop_loss`
- `take_profit`
- `risk_reward`
- `score`
- `evaluation_status`
- `evaluated_on`
- `exit_price`
- `actual_return_pct`
- `r_multiple`

Important optional or enrichment fields:

- `tag`
- `days_to_earnings`
- `news_action_window`
- `brain_p_win`
- `brain_ev_pct`
- `brain_sl`
- `brain_tp`
- `brain_confidence`
- `monster_score`
- `is_monster`
- `smell_codes`
- `smell_severities`
- `smell_messages`
- `sector_etf`
- `sector_close`
- `peak_price`
- `current_sl`
- `current_tp`
- `trail_active`
- `tp_raises`
- `sl_tightens`
- `peak_rsi`

Rules:

- rows with `watch_only=true` must not be treated as official actionable picks
- terminal statuses must not be monitored as active positions
- missing status should be interpreted carefully and only for backward compatibility
- intraday close writes should update the correct pick date
- official pick stats should be calculated only from official rows

Terminal statuses should include:

- `sl_hit`
- `tp_hit`
- `day_close`
- `closed`
- `expired`
- `unreachable_entry`

Future improvements:

- add model version fields if needed:
  - `model_name`
  - `model_version`
  - `feature_set_version`
  - `threshold_set_version`
  - `github_sha`
  - `github_run_id`

Validation ideas:

- required columns exist
- numeric fields parse safely
- watch-only field is normalized
- terminal statuses are recognized consistently
- no duplicate official pick row for same date/ticker unless intentionally allowed
- active-position loading excludes watch-only and terminal rows

## Contract: `data/daily_picks_run_status_YYYY-MM-DD.jsonl`

Classification:

- operational

Purpose:

- records Daily Picks workflow/watchdog run status
- helps explain whether official picks ran, skipped, failed, or were blocked
- supports operational learning and reliability review

Primary owners:

- `.github/workflows/daily-picks.yml`
- `scripts/record_daily_picks_run_status.py`
- related watchdog/recovery logic

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Suggested required fields:

- `date`
- `timestamp_utc`
- `workflow`
- `event`
- `result`
- `reason`
- `official_picks_generated`
- `telegram_sent`
- `mode`

Useful optional fields:

- `candidate_count`
- `final_pick_count`
- `no_pick_cause`
- `github`
- `run_id`
- `run_attempt`
- `sha`
- `ref`

Rules:

- operational status must never be counted as a pick
- skipped runs should include a reason
- failed runs should preserve enough evidence for diagnosis
- missing Telegram credentials should be recorded as skipped, not as model failure

Validation ideas:

- every row is valid JSON
- `result` is one of known values
- timestamp exists
- `mode` is monitoring-only unless explicitly changed

## Contract: `data/daily_picks_no_pick_report_YYYY-MM-DD.json`

Classification:

- operational
- diagnostic

Purpose:

- explains why official Daily Picks produced no final picks
- preserves evidence for no-pick days
- supports trust by making rejection explainable

Primary owners:

- `main.py`
- daily-picks failed-run recovery logic

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Suggested required fields:

- `artifact`
- `date`
- `timestamp_utc`
- `mode`
- `official_premarket_pick`
- `paper_trading_enabled`
- `live_trading_enabled`
- `ready_for_paper_trading`
- `reason`
- `primary_no_pick_cause`
- `secondary_causes`
- `human_readable_summary`
- `pipeline`
- `market_data_health`
- `next_action`

Rules:

- no-pick reports must not create picks
- no-pick reports should not be treated as failure if the model rejected candidates safely
- reports should explain whether the cause was data, filtering, hard blocks, runtime failure, or no candidates
- reports should preserve enough evidence to improve later

Validation ideas:

- required fields exist
- pipeline counters are numeric where possible
- paper/live flags remain false
- primary no-pick cause is present

## Contract: `data/daily_picks_candidate_rejections_YYYY-MM-DD.json`

Classification:

- operational
- diagnostic

Purpose:

- records candidates rejected during official Daily Picks
- explains hard-blocked finalists and candidate rejection context
- supports learning from rejected ideas

Primary owners:

- `main.py`

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Suggested required fields:

- `artifact`
- `date`
- `timestamp_utc`
- `mode`
- `official_premarket_pick`
- `paper_trading_enabled`
- `live_trading_enabled`
- `ready_for_paper_trading`
- `primary_no_pick_cause`
- `secondary_causes`
- `pipeline`
- `diagnostics`

Useful diagnostic sections:

- `pre_hard_block_candidates`
- `hard_blocked_candidates`
- `candidate`
- `block_type`
- `reason`

Rules:

- rejected candidates are not official picks
- rejected candidates must not be sent as actionable picks
- rejected candidates may be reviewed for model improvement
- hard-block evidence should be preserved for future analysis

Validation ideas:

- all rejected candidate rows have ticker if known
- block reason is present for hard-blocked candidates
- monitoring-only flags are false/true as expected

## Contract: `data/late_daily_ideas_YYYY-MM-DD.jsonl`

Classification:

- watch-only

Purpose:

- preserves watch-only ideas when official premarket daily-picks window is missed
- supports learning without polluting official statistics
- gives the user context while clearly avoiding official action language

Primary owners:

- `scripts/generate_late_daily_ideas.py`
- `scripts/send_late_daily_ideas_telegram.py`
- `.github/workflows/late_watch_only.yml`

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Suggested required fields:

- `date`
- `timestamp_utc`
- `ticker`
- `watch_only`
- `mode`
- `reason`
- `score`

Useful optional fields:

- `company`
- `entry_reference`
- `stop_reference`
- `target_reference`
- `risk_reward`
- `source`
- `price`
- `data_quality`
- `warning`

Rules:

- must remain watch-only
- must not use action-like BUY wording
- must not count as official pick
- must not be paper traded
- should preserve enough context for later outcome analysis

Validation ideas:

- every row is valid JSON
- `watch_only` is true
- `mode` is monitoring-only
- paper/live flags are false if present
- ticker is present and resolved

## Contract: `data/opening_range_observations_YYYY-MM-DD.jsonl`

Classification:

- watch-only
- evidence

Purpose:

- records opening-range breakout observations
- supports intraday learning and future promotion gates
- preserves scanner evidence even when no Telegram alert should be sent

Primary owners:

- `src/opening_range_scanner.py`
- `scripts/intraday_scanner.py`
- `scripts/intraday_monitor.py`

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Suggested required fields:

- `date`
- `timestamp_et`
- `ticker`
- `watch_only`
- `scanner`
- `price`
- `opening_range_high`
- `opening_range_low`
- `breakout_pct`
- `opening_range_width_pct`
- `volume_ratio`
- `result`
- `reason`

Useful optional fields:

- `timestamp_utc`
- `mode`
- `candidate_id`
- `score`
- `entry_reference`
- `stop_reference`
- `target_reference`
- `risk_reward`
- `gap_pct`
- `extension_pct`
- `market_context`
- `alert_sent`
- `blockers`

Rules:

- opening-range observations are not official picks
- must remain watch-only until promotion gates pass
- should be written even when candidates are rejected, if practical
- should include enough fields to evaluate future outcomes
- should avoid duplicate noisy rows for the same ticker/window

Validation ideas:

- every row is valid JSON
- `scanner` identifies opening-range logic
- `watch_only` is true
- price and opening-range fields parse as numbers where present
- result/reason fields explain inclusion or rejection

## Contract: `data/opening_range_bars/YYYY-MM-DD/TICKER.jsonl`

Classification:

- evidence
- diagnostic

Purpose:

- stores intraday bars used by opening-range scanner
- supports debugging and backtesting of scanner behavior
- allows reconstruction of opening-range calculations

Primary owners:

- `src/opening_range_scanner.py`
- `scripts/intraday_scanner.py`

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Suggested required fields:

- `timestamp_et`
- `open`
- `high`
- `low`
- `close`
- `volume`

Useful optional fields:

- `timestamp_utc`
- `source`
- `interval`
- `ticker`
- `data_quality`

Rules:

- bars are evidence, not signals
- missing bars should be flagged rather than silently ignored
- data source and interval should be explicit if available
- old bar artifacts may be large and should be managed carefully

Validation ideas:

- every row is valid JSON
- OHLC values parse as numbers
- volume parses as numeric
- timestamps are ordered or sortable
- interval/source are documented where present

## Contract: `data/opening_range_run_status_YYYY-MM-DD.jsonl`

Classification:

- operational

Purpose:

- records whether opening-range scanning ran, skipped, produced candidates, or failed
- helps distinguish no candidates from workflow failure
- supports operational debugging

Primary owners:

- `scripts/intraday_scanner.py`
- `scripts/intraday_monitor.py`

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Suggested required fields:

- `date`
- `timestamp_et`
- `timestamp_utc`
- `scanner`
- `status`
- `reason`
- `candidate_count`
- `alert_count`

Useful optional fields:

- `window`
- `mode`
- `workflow`
- `github_run_id`
- `github_sha`
- `data_quality`
- `tickers_scanned`

Rules:

- no-candidate runs should be recorded as completed/no_alerts, not failed
- market-closed or outside-window skips should include reason
- workflow errors should preserve error summary
- run status rows must not be interpreted as candidate rows

Validation ideas:

- every row is valid JSON
- `status` is one of known values
- candidate and alert counts are numeric
- skip/failure reasons are present

## Contract: `data/intraday_momentum_observations_YYYY-MM-DD.jsonl`

Classification:

- watch-only
- evidence

Purpose:

- records legacy intraday momentum observations
- preserves watch-only scanner evidence
- supports future comparison against opening-range and other scanners

Primary owners:

- `scripts/intraday_scanner.py`
- `scripts/intraday_monitor.py`

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Suggested required fields:

- `date`
- `timestamp_et`
- `ticker`
- `watch_only`
- `scanner`
- `price`
- `score`
- `reason`

Useful optional fields:

- `timestamp_utc`
- `mode`
- `candidate_id`
- `change_pct`
- `volume_ratio`
- `relative_volume`
- `entry_reference`
- `stop_reference`
- `target_reference`
- `risk_reward`
- `alert_sent`
- `blockers`
- `market_context`

Rules:

- momentum observations are watch-only
- they must not become official picks without promotion gates
- they should be comparable to future intraday candidate rows
- duplicate alerts for the same ticker/day should be deduped

Validation ideas:

- every row is valid JSON
- `watch_only` is true
- `scanner` is present
- score parses as numeric where present
- action language is not persisted as official instruction

## Future Contract: `data/intraday_candidates_YYYY-MM-DD.jsonl`

Classification:

- watch-only
- evidence

Purpose:

- normalized artifact for all intraday scanner candidates
- joins scanner features, blockers, scores, alert status, and model metadata
- becomes the main input for intraday outcome evaluation and learning

Primary owners:

- future `src/intraday_candidate_schema.py`
- `scripts/intraday_scanner.py`
- `scripts/intraday_monitor.py`
- future `src/intraday_score.py`
- future `src/intraday_features.py`

May affect official pick statistics:

- no

May affect paper/live trading:

- no, until explicit readiness and founder approval

Suggested required fields:

- `candidate_id`
- `date`
- `timestamp_et`
- `timestamp_utc`
- `ticker`
- `lane`
- `source`
- `scanner`
- `state`
- `watch_only`
- `official_pick`
- `paper_trading_enabled`
- `live_trading_enabled`
- `model_name`
- `model_version`
- `feature_set_version`
- `threshold_set_version`
- `price`
- `entry_reference`
- `stop_reference`
- `target_reference`
- `risk_reward`
- `score`
- `features`
- `blockers`
- `reason`
- `alert_sent`

Useful optional fields:

- `telegram_fingerprint`
- `market_context`
- `sector_context`
- `news_context`
- `data_quality`
- `github_run_id`
- `github_sha`
- `code_ref`

Rules:

- every candidate defaults to watch-only
- `official_pick` must be false unless explicitly promoted by a separate gate
- `paper_trading_enabled` and `live_trading_enabled` must default false
- blocked candidates may be recorded, but must not alert
- candidate IDs should be stable enough to join with outcomes
- candidate rows must not update `data/picks_log.csv`

Validation ideas:

- required fields exist
- JSON is valid
- booleans are normalized
- score is bounded if present
- `features` and `blockers` are JSON-safe
- candidate ID is unique enough for same date/ticker/scanner/timestamp
- alert_sent is false when blockers are present

## Future Contract: `data/intraday_outcomes_YYYY-MM-DD.jsonl`

Classification:

- watch-only
- evidence
- learning

Purpose:

- records forward outcomes for intraday candidates
- supports learning, readiness gates, and future recalibration
- keeps watch-only outcome statistics separate from official pick statistics

Primary owners:

- future `scripts/evaluate_intraday_candidates.py`
- future `src/intraday_outcomes.py`
- future `scripts/intraday_learning_report.py`

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Suggested required fields:

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

Useful optional fields:

- `model_name`
- `model_version`
- `feature_set_version`
- `threshold_set_version`
- `bars_used`
- `provider`
- `warning`
- `error`

Rules:

- outcome rows must join to candidate IDs
- outcomes must not mutate official pick statistics
- missing data should produce a data-quality warning, not silent success
- stop/target ordering must be deterministic
- ambiguous 5-minute bar ordering should be flagged

Validation ideas:

- candidate_id is present
- horizon is one of known values such as `15m`, `30m`, `60m`, `eod`
- returns and R multiple parse as numeric when available
- data_quality is present
- official/paper/live flags remain false if included

## Contract: `data/news_log.jsonl`

Classification:

- evidence
- operational

Purpose:

- records fetched and processed news items
- supports dedupe, signal creation, and future attribution
- preserves raw-ish news evidence for audit and debugging

Primary owners:

- `src/news_engine.py`
- `src/news_signals.py`
- `scripts/run_news_engine.py`

May affect official pick statistics:

- indirectly only if news scoring is explicitly wired into official pick scoring

May affect paper/live trading:

- no

Suggested required fields:

- `timestamp_utc`
- `ticker`
- `headline`
- `source`
- `url`
- `published_at`
- `classification`
- `impact_score`

Useful optional fields:

- `summary`
- `sentiment`
- `dedupe_key`
- `provider`
- `raw_payload`
- `reason`
- `data_quality`

Rules:

- news log rows are evidence, not official picks
- duplicate headlines should be deduped consistently
- source and URL should be preserved where available
- missing ticker should be handled explicitly

Validation ideas:

- every row is valid JSON
- headline or summary is present
- source is present when available
- impact_score parses as numeric where present

## Contract: `data/news_seen.json`

Classification:

- operational

Purpose:

- stores dedupe state for news processing
- prevents repeated alerts or repeated signal creation for the same news item

Primary owners:

- `src/news_engine.py`
- `scripts/run_news_engine.py`

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Suggested shape:

- mapping of dedupe keys to metadata
- metadata may include first_seen timestamp, ticker, headline, source, and URL

Rules:

- dedupe state must not be treated as signal evidence by itself
- corrupt dedupe state should fail safely
- dedupe keys should be stable enough to prevent spam

Validation ideas:

- file is valid JSON
- top-level value is object/dict
- keys are strings
- timestamps parse where present

## Contract: `data/news_signals.json`

Classification:

- evidence
- watch-only unless explicitly used by official scorer

Purpose:

- stores active or recent news signals
- supports pick enrichment, watchlist updates, and future outcome attribution

Primary owners:

- `src/news_signals.py`
- `src/news_engine.py`
- `scripts/run_news_engine.py`

May affect official pick statistics:

- indirectly only when official scoring consumes news signals

May affect paper/live trading:

- no

Suggested required fields per signal:

- `signal_id`
- `ticker`
- `headline`
- `source`
- `timestamp_utc`
- `classification`
- `impact_score`
- `direction`
- `status`

Useful optional fields:

- `url`
- `summary`
- `sentiment`
- `confidence`
- `expires_at`
- `reason`
- `related_symbols`
- `watchlist_action`

Rules:

- signals are not official picks
- signals should have expiry or status to avoid stale influence
- status should distinguish active, expired, ignored, and attributed
- if used by official scoring, the influence should be logged

Validation ideas:

- signal IDs are present
- active signals have ticker and timestamp
- impact score parses as numeric
- status is one of known values

## Contract: `data/news_signal_outcomes_YYYY-MM-DD.jsonl`

Classification:

- evidence
- learning

Purpose:

- records future return/outcome attribution for news signals
- helps determine whether news classifications and impact scores are useful

Primary owners:

- `scripts/news_signal_outcome_attribution.py`

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Suggested required fields:

- `signal_id`
- `date`
- `ticker`
- `headline`
- `classification`
- `impact_score`
- `horizon`
- `start_price`
- `end_price`
- `return_pct`
- `data_quality`

Useful optional fields:

- `max_favorable_excursion`
- `max_adverse_excursion`
- `provider`
- `warning`
- `error`

Rules:

- outcomes must not create or mutate picks
- missing data should be explicit
- attribution windows should be documented
- outcome records should join back to news signal IDs when possible

Validation ideas:

- every row is valid JSON
- signal_id or equivalent trace key exists
- horizon is present
- return_pct parses as numeric where available
- data_quality is present

## Contract: `data/news_signal_evidence_report_YYYY-MM-DD.md`

Classification:

- report
- learning

Purpose:

- summarizes news signal evidence and outcome attribution
- helps review whether news signals deserve more or less model influence

Primary owners:

- `scripts/news_signal_evidence_report.py`

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Rules:

- report is human-readable only
- report must not be parsed as source of truth when JSONL artifacts exist
- recommendations should remain observe/review unless explicitly approved

Validation ideas:

- report exists when workflow completes
- report includes date
- report references source artifacts
- report distinguishes evidence from recommendation

## Contract: `data/signal_journal.jsonl`

Classification:

- evidence
- learning

Purpose:

- records structured signal evidence for later learning
- helps connect observed signals to outcomes, hypotheses, and calibration

Primary owners:

- `src/signal_journal.py`
- learning and hypothesis scripts

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Suggested required fields:

- `timestamp_utc`
- `date`
- `ticker`
- `signal_type`
- `source`
- `value`
- `reason`

Useful optional fields:

- `lane`
- `model_name`
- `model_version`
- `features`
- `outcome_ref`
- `confidence`
- `data_quality`

Rules:

- signal journal rows are evidence, not picks
- rows should be append-only
- source and signal type should be explicit
- missing outcomes should not invalidate the signal record

Validation ideas:

- every row is valid JSON
- ticker exists when signal is ticker-specific
- signal_type is present
- timestamp is present

## Contract: `data/learning_journal.jsonl`

Classification:

- learning

Purpose:

- records model lessons, observations, performance notes, and learning events
- supports the agent's long-term improvement loop

Primary owners:

- `src/learning_journal.py`
- `scripts/run_nightly_brain.py`
- `scripts/run_hypothesis_review.py`
- learning/report scripts

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Suggested required fields:

- `timestamp_utc`
- `date`
- `lesson_type`
- `summary`
- `evidence`
- `status`

Useful optional fields:

- `lane`
- `ticker`
- `hypothesis_id`
- `model_version`
- `recommendation`
- `confidence`
- `approved`
- `applied`

Rules:

- lessons must not auto-change production behavior
- recommendations require approval before applying
- learning entries should reference evidence where possible
- low-confidence lessons should be labeled clearly

Validation ideas:

- every row is valid JSON
- summary exists
- status is present
- applied changes require explicit approval metadata

## Contract: `data/weight_proposals.jsonl`

Classification:

- learning
- recommendation

Purpose:

- records proposed model weight or threshold changes
- creates an audit trail for calibration recommendations

Primary owners:

- `src/weight_proposer.py`
- `src/weight_applier.py`
- `src/calibration.py`
- learning/recalibration scripts

May affect official pick statistics:

- not directly

May affect paper/live trading:

- no direct effect unless separately approved and applied

Suggested required fields:

- `timestamp_utc`
- `proposal_id`
- `model_area`
- `parameter`
- `current_value`
- `proposed_value`
- `reason`
- `evidence_summary`
- `status`

Useful optional fields:

- `lane`
- `sample_size`
- `expected_impact`
- `confidence`
- `approved_by`
- `approved_at`
- `applied_at`
- `rollback_plan`

Rules:

- proposals must not auto-apply by default
- approval must be explicit
- applied changes should be traceable to config/code version
- rejected proposals should remain auditable

Validation ideas:

- proposal_id exists
- current and proposed values are present
- status is one of known values
- applied proposals include approval metadata

## Contract: `data/wisdom/rules.jsonl`

Classification:

- research-only
- learning

Purpose:

- stores structured lessons from books, research, founder notes, or other approved sources
- converts market wisdom into testable rule candidates

Primary owners:

- `src/wisdom_base.py`
- `src/wisdom_hint.py`
- `src/wisdom_consultant.py`
- future reader ingestion scripts

May affect official pick statistics:

- no, unless a rule is later validated, approved, and explicitly wired into scoring

May affect paper/live trading:

- no

Suggested required fields:

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

Useful optional fields:

- `source_url`
- `source_author`
- `created_at`
- `updated_at`
- `evidence_refs`
- `notes`

Rules:

- new wisdom rules default to observe-only
- unsupported or unlicensed sources should be rejected
- no rule may enforce behavior without approval
- source metadata must be preserved

Validation ideas:

- source metadata exists
- status is present
- promoted defaults false
- approved_by_founder is required before enforcement

## Contract: `data/wisdom/sources.jsonl`

Classification:

- research-only
- operational

Purpose:

- records metadata for wisdom sources
- supports source attribution and licensing discipline

Primary owners:

- future reader ingestion scripts
- wisdom modules

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Suggested required fields:

- `source_id`
- `source_type`
- `source_name`
- `allowed_use`
- `ingested_at`
- `notes`

Useful optional fields:

- `author`
- `url`
- `license`
- `provided_by`
- `content_hash`
- `status`

Rules:

- source licensing/use status must be explicit
- unsupported sources should not be ingested
- source records do not create trading rules by themselves

Validation ideas:

- source_id exists
- allowed_use is present
- status is known if present

## Future Contract: `data/monster_candidates_YYYY-MM-DD.jsonl`

Classification:

- research-only
- evidence

Purpose:

- records Monster Hunter / long-term compounder candidates
- keeps long-term thesis research separate from swing trades and intraday ideas
- supports future thesis tracking without creating official picks

Primary owners:

- `src/monster_hunt.py`
- `src/monster_data.py`
- future `scripts/monster_research_report.py`

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Suggested required fields:

- `date`
- `timestamp_utc`
- `ticker`
- `company`
- `research_only`
- `lane`
- `monster_score`
- `thesis_state`
- `reason`
- `fundamental_summary`
- `risk_summary`

Useful optional fields:

- `candidate_id`
- `sector`
- `industry`
- `market_cap`
- `revenue_growth`
- `margin_trend`
- `free_cash_flow_trend`
- `balance_sheet_quality`
- `moat_notes`
- `thesis_break_conditions`
- `data_quality`

Rules:

- monster candidates are research-only
- they must not write to `data/picks_log.csv`
- a swing trade must not silently become a monster thesis
- thesis-break conditions should be present before any serious tracking
- no paper/live flags may be enabled

Validation ideas:

- research_only is true
- thesis_state is present
- monster_score parses as numeric where present
- thesis-break conditions exist for promoted thesis states

## Future Contract: `data/monster_theses_YYYY-MM-DD.jsonl`

Classification:

- research-only
- thesis

Purpose:

- records long-term thesis state for Monster Hunter candidates
- tracks evidence, thesis changes, and state transitions over time
- separates investing thesis lifecycle from trading lifecycle

Primary owners:

- future `src/monster_thesis.py`
- future `scripts/monster_research_report.py`

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Suggested required fields:

- `thesis_id`
- `date`
- `timestamp_utc`
- `ticker`
- `company`
- `thesis_state`
- `research_only`
- `thesis_summary`
- `evidence`
- `thesis_break_conditions`
- `risks`

Allowed thesis states:

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

Rules:

- thesis state changes require explicit evidence
- invalid transitions should be rejected
- thesis artifacts must not create official picks
- thesis artifacts must not enable paper/live trading

Validation ideas:

- thesis_id exists
- thesis_state is allowed
- research_only is true
- thesis_break_conditions are present
- evidence is present for non-candidate states

## Future Contract: `data/fundamental_quality_YYYY-MM-DD.jsonl`

Classification:

- research-only
- evidence

Purpose:

- stores quarterly/yearly fundamental-quality analysis
- supports swing quality control and Monster Hunter research
- provides warnings for low-quality or pump-risk names

Primary owners:

- `src/fundamentals.py`
- `src/earnings_analyzer.py`
- `src/monster_data.py`
- future `src/fundamental_quality.py`
- future `scripts/fundamental_research_report.py`

May affect official pick statistics:

- no, unless explicitly wired after validation and approval

May affect paper/live trading:

- no

Suggested required fields:

- `date`
- `timestamp_utc`
- `ticker`
- `company`
- `research_only`
- `data_quality`
- `quality_score`
- `warnings`
- `summary`

Useful optional fields:

- `revenue_growth`
- `eps_growth`
- `gross_margin_trend`
- `operating_margin_trend`
- `net_income_trend`
- `free_cash_flow_trend`
- `debt_liquidity_summary`
- `dilution_summary`
- `guidance_trend`
- `valuation_summary`
- `sector_tailwind`

Rules:

- missing fundamentals should produce data-quality warnings
- fundamental research must not automatically block official picks initially
- warnings should be measured before enforcement
- research-only flag should remain true

Validation ideas:

- ticker exists
- quality_score parses as numeric where present
- warnings is list-like
- missing data is explicit

## Future Contract: `data/backtests/intraday_replay_YYYY-MM-DD.jsonl`

Classification:

- research-only
- backtest
- learning

Purpose:

- stores historical intraday replay candidates and outcomes
- accelerates scanner and scoring evaluation
- supports regime-aware learning before paper validation

Primary owners:

- future `scripts/backtest_intraday_candidates.py`
- future `src/intraday_backtester.py`
- `scripts/backtest_opening_range_observations.py`

May affect official pick statistics:

- no

May affect paper/live trading:

- no

Suggested required fields:

- `backtest_id`
- `historical_date`
- `generated_at_utc`
- `ticker`
- `scanner`
- `candidate_timestamp_et`
- `features`
- `score`
- `entry_reference`
- `stop_reference`
- `target_reference`
- `outcome`
- `data_quality`

Useful optional fields:

- `model_name`
- `model_version`
- `feature_set_version`
- `threshold_set_version`
- `regime`
- `train_test_split`
- `provider`
- `bars_used`

Rules:

- must avoid lookahead bias
- train/test split should be explicit where used
- historical replay must not be mixed with live forward evidence without labeling
- backtest results must not create picks

Validation ideas:

- historical timestamps are preserved
- no future data is used before candidate timestamp
- outcome is deterministic
- data_quality is present

## Validation Roadmap

Validation should be introduced gradually.

### Phase 1: Documentation Only

Status:

- current

Goals:

- document artifact purpose
- document classification
- document required conceptual fields
- document ownership
- document whether artifacts may affect official stats or paper/live trading

Rules:

- no runtime behavior changes
- no schema enforcement yet
- use this document as the source of planning truth

### Phase 2: Warning-Only Validators

Goals:

- add lightweight validators for new artifacts
- warn on missing fields
- warn on malformed JSONL rows
- warn on invalid booleans or statuses
- do not fail workflows unless artifact corruption would hide a production issue

Suggested validators:

- `src/data_contracts.py`
- `scripts/validate_data_contracts.py`

Initial validation targets:

- future `data/intraday_candidates_YYYY-MM-DD.jsonl`
- future `data/intraday_outcomes_YYYY-MM-DD.jsonl`
- `data/opening_range_run_status_YYYY-MM-DD.jsonl`
- `data/daily_picks_run_status_YYYY-MM-DD.jsonl`

### Phase 3: CI Checks for New Artifacts

Goals:

- validate schema for newly generated test artifacts
- keep old historical artifacts warning-only
- prevent accidental official/watch-only mixing

Suggested checks:

- JSONL validity
- required fields for new artifacts
- official/watch-only/paper/live flag consistency
- terminal status consistency
- no watch-only artifact mutates official pick stats

### Phase 4: Strict Contracts for Critical Artifacts

Potential strict targets:

- `data/picks_log.csv`
- future `data/intraday_candidates_YYYY-MM-DD.jsonl`
- future `data/intraday_outcomes_YYYY-MM-DD.jsonl`

Strict validation should happen only after:

- schema has stabilized
- tests cover common legacy cases
- migration plan exists
- warning-only validation has run successfully for a while

## Common Field Meanings

### `watch_only`

Meaning:

- true when the row is not an official actionable model pick

Rules:

- watch-only rows must not affect official stats
- watch-only rows must not imply buy/sell instruction
- watch-only rows require clear user-facing language if alerted

### `official_pick`

Meaning:

- true only when a row represents an official model pick

Rules:

- should be false for scanner candidates, watch-only ideas, research artifacts, and backtests
- should not become true without explicit promotion logic

### `paper_trading_enabled`

Meaning:

- true only when paper trading is explicitly enabled for that lane/model

Rules:

- default false
- requires readiness gate
- requires founder approval

### `live_trading_enabled`

Meaning:

- true only when live trading is explicitly enabled

Rules:

- default false
- should remain false for the foreseeable future
- requires separate risk/legal/product review before any activation

### `mode`

Suggested values:

- `monitoring_only`
- `research_only`
- `watch_only`
- `paper`
- `live`

Rules:

- default to monitoring-only or research-only
- paper/live values require explicit gates

### `data_quality`

Suggested values or components:

- `ok`
- `missing_price_data`
- `missing_volume`
- `partial_bars`
- `provider_error`
- `stale_data`
- `ambiguous_bar_order`
- `insufficient_history`

Rules:

- missing or degraded data should be explicit
- poor data should reduce confidence or block promotion

### `candidate_id`

Meaning:

- stable trace key for joining candidates to outcomes

Recommended ingredients:

- date
- ticker
- scanner
- timestamp bucket
- model/scorer version if needed

Rules:

- deterministic is preferred
- must be stable enough for outcome joins
- should avoid collisions across scanners

### `terminal status`

Meaning:

- a status that means an official model position is no longer active

Known terminal statuses:

- `sl_hit`
- `tp_hit`
- `day_close`
- `closed`
- `expired`
- `unreachable_entry`

Rules:

- terminal rows should not be monitored as active positions
- future terminal statuses should be added here and in tests

## Artifact Ownership Rules

Every artifact should have:

- a primary writer
- zero or more readers
- clear classification
- clear official-stat impact rule
- clear paper/live impact rule

If ownership is unclear:

- document the current behavior
- avoid adding new writers
- add tests before changing behavior

## Migration Rules

When changing an artifact schema:

1. Document the new field here.
2. Add the field as optional first.
3. Update readers to tolerate missing values.
4. Add tests with old and new shapes.
5. Start writing the new field.
6. Validate in warning-only mode.
7. Make the field required only after stable.

## Anti-Corruption Rules

The following should be treated as serious bugs:

- watch-only rows counted in official pick stats
- research-only rows written to `data/picks_log.csv`
- scanner candidates sent with official buy/sell language
- terminal official picks monitored as active positions
- paper/live flags enabled by default
- outcome rows mutating official pick rows
- backtest rows mixed with live forward evidence without labels
- recommendations auto-applied without approval

## Final Data Contract Rule

Data artifacts are product memory.

If an artifact is ambiguous, future learning will be ambiguous.

Every artifact should make clear:

- what it is
- where it came from
- whether it is official
- whether it is watch-only
- whether it can affect stats
- whether it can affect trading
- what evidence supports it
- what happened afterward
