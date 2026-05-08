# Candidate Lifecycle

## Purpose

This document defines how Daily Stock Agent should treat market ideas across different lifecycle states.

The goal is to prevent confusion between:

- official model picks
- watch-only ideas
- research-only ideas
- rejected candidates
- backtest candidates
- paper-trading candidates
- future live-trading candidates

This document is planning-only for now. It should guide future implementation.

## Core Principle

An idea is not a pick.

A candidate should become more important only after it earns evidence.

Default state should be observation, not action.

## Lifecycle Summary

High-level lifecycle:

1. candidate discovered
2. candidate classified
3. blockers checked
4. candidate stored as evidence
5. optional watch-only alert sent
6. forward outcome measured
7. learning report generated
8. readiness gate reviewed
9. founder approval requested if needed
10. promoted only after evidence and approval

## Lifecycle States

### `discovered`

Meaning:

- scanner or model found a possible idea
- no validation has happened yet

Allowed actions:

- calculate features
- attach market context
- attach source/scanner metadata

Not allowed:

- Telegram action alert
- official pick creation
- paper trading
- live trading

### `rejected`

Meaning:

- candidate failed a hard block or quality check

Examples:

- insufficient data
- bad spread/liquidity
- excessive extension
- weak risk/reward
- pump-risk smell
- missing required context

Allowed actions:

- store rejection evidence
- include in diagnostic report
- use for future learning

Not allowed:

- official pick creation
- action-style Telegram alert
- paper trading
- live trading

### `watch_only`

Meaning:

- candidate is worth monitoring
- candidate is not an official pick
- candidate does not affect official statistics

Allowed actions:

- store candidate row
- send clearly labeled watch-only alert
- measure forward outcome
- include in learning reports

Not allowed:

- official stats mutation
- paper trading
- live trading
- buy/sell instruction wording

### `research_only`

Meaning:

- candidate exists for research, thesis, backtest, wisdom, or fundamental analysis
- candidate is not actionable

Allowed actions:

- store research evidence
- update thesis state
- include in research reports
- measure long-term outcomes

Not allowed:

- official pick creation
- trading language
- paper/live trading

### `paper_candidate`

Meaning:

- candidate is eligible for paper trading after readiness gates pass
- this is still not live trading

Allowed actions:

- simulated execution
- paper outcome tracking
- paper performance reporting

Required before entering state:

- enough forward evidence
- documented readiness gate
- founder approval
- tests for tracking and reporting

Not allowed:

- live trading
- official claim of real-money readiness

### `official_model_pick`

Meaning:

- candidate has become an official model pick
- may be written to `data/picks_log.csv`
- may affect official pick statistics

Allowed actions:

- official pick logging
- official monitoring
- official outcome evaluation
- official reporting

Required before entering state:

- explicit model logic
- valid data
- no hard blocks
- correct time window
- safe notification language

Not allowed:

- silent promotion from watch-only artifacts
- promotion from research-only artifacts without explicit logic

### `live_candidate`

Meaning:

- future theoretical state only
- real-money automation candidate

Current status:

- deferred
- not allowed

Required before any future consideration:

- separate risk review
- legal/product review
- technical safety review
- long paper-validation history
- explicit founder approval


## Allowed Transitions

### `discovered` -> `rejected`

Allowed when:

- candidate fails hard block
- candidate lacks required data
- candidate has unsafe risk/reward
- candidate is outside valid time window
- candidate is duplicate/noisy

Required evidence:

- rejection reason
- scanner/source
- timestamp
- ticker if known
- blocker details where available

### `discovered` -> `watch_only`

Allowed when:

- candidate passes minimum monitoring checks
- candidate is interesting enough to observe
- candidate is not official
- alert language can be made safe

Required evidence:

- candidate row
- watch-only flag
- scanner/source
- reference price levels if applicable
- reason for monitoring

### `discovered` -> `research_only`

Allowed when:

- idea belongs to long-term thesis research
- idea belongs to fundamental research
- idea belongs to backtest/replay
- idea belongs to wisdom/rule exploration

Required evidence:

- research source
- thesis or research reason
- research-only flag
- no paper/live flags

### `watch_only` -> `paper_candidate`

Allowed only after:

- enough forward outcome evidence exists
- learning reports show positive expectancy or useful behavior
- data-quality issues are understood
- readiness gate is documented
- founder approval is explicit

Required evidence:

- sample size
- performance summary
- failure modes
- proposed paper rules
- rollback/disable criteria

### `watch_only` -> `official_model_pick`

Generally not allowed directly.

Reason:

- watch-only artifacts should not silently become official picks
- official picks should come from explicit official model logic

Exception:

- future implementation may reuse watch-only evidence to design official model logic
- the official pick still must be created by explicit approved logic

### `research_only` -> `watch_only`

Allowed when:

- research insight becomes a monitored idea
- language remains watch-only
- source and rationale are preserved

Required evidence:

- source research artifact
- reason for monitoring
- watch-only classification

### `research_only` -> `official_model_pick`

Not allowed directly.

Research may inform future official model rules, but must not create official picks by itself.

### `paper_candidate` -> `official_model_pick`

Allowed only if:

- paper-trading period succeeds
- readiness criteria are met
- failures are understood
- model behavior is documented
- founder approval is explicit

### `paper_candidate` -> `live_candidate`

Currently not allowed.

Future consideration requires separate review.

### `official_model_pick` -> terminal state

Allowed terminal states include:

- `sl_hit`
- `tp_hit`
- `day_close`
- `closed`
- `expired`
- `unreachable_entry`

Rules:

- terminal rows should not be loaded as active positions
- terminal rows should preserve outcome evidence
- official stats should be updated only once

## Artifact Rules by Lifecycle State

### Discovered Candidates

Preferred future artifact:

- `data/intraday_candidates_YYYY-MM-DD.jsonl`

Required fields:

- `candidate_id`
- `date`
- `timestamp_et`
- `ticker`
- `scanner`
- `state`
- `source`
- `watch_only`
- `official_pick`
- `paper_trading_enabled`
- `live_trading_enabled`
- `reason`

Rules:

- discovered candidates default to watch-only or research-only
- discovered candidates must not mutate `data/picks_log.csv`
- discovered candidates must preserve scanner/source metadata

### Rejected Candidates

Current/future artifacts:

- `data/daily_picks_candidate_rejections_YYYY-MM-DD.json`
- future rejected rows in `data/intraday_candidates_YYYY-MM-DD.jsonl`

Required fields:

- `ticker`
- `state`
- `block_type`
- `reason`
- `scanner`
- `timestamp`
- `data_quality`

Rules:

- rejected candidates should be useful for learning
- rejected candidates should not be alerted as action ideas
- hard-block reasons should be explicit

### Watch-Only Candidates

Current/future artifacts:

- `data/late_daily_ideas_YYYY-MM-DD.jsonl`
- `data/opening_range_observations_YYYY-MM-DD.jsonl`
- `data/intraday_momentum_observations_YYYY-MM-DD.jsonl`
- future `data/intraday_candidates_YYYY-MM-DD.jsonl`

Required flags:

- `watch_only: true`
- `official_pick: false`
- `paper_trading_enabled: false`
- `live_trading_enabled: false`

Rules:

- watch-only candidates may be alerted only with clear watch-only language
- watch-only candidates must not affect official pick statistics
- watch-only candidates should be evaluated separately

### Research-Only Candidates

Current/future artifacts:

- future `data/monster_candidates_YYYY-MM-DD.jsonl`
- future `data/monster_theses_YYYY-MM-DD.jsonl`
- future `data/fundamental_quality_YYYY-MM-DD.jsonl`
- future `data/backtests/intraday_replay_YYYY-MM-DD.jsonl`
- `data/wisdom/rules.jsonl`

Required flags:

- `research_only: true`
- `official_pick: false`
- `paper_trading_enabled: false`
- `live_trading_enabled: false`

Rules:

- research-only candidates may inform future rules
- research-only candidates must not become official picks directly
- research reports should avoid trade instruction language

### Official Model Picks

Primary artifact:

- `data/picks_log.csv`

Required properties:

- official model pick source
- entry reference
- stop-loss reference
- take-profit reference
- evaluation status
- outcome fields after evaluation

Rules:

- official picks are the only ideas that may affect official pick statistics
- official picks must be created by explicit official model logic
- terminal statuses must prevent repeated active monitoring

## Readiness Gates

Readiness gates decide whether a monitored or research idea can move closer to official or paper behavior.

### Gate 1: Data Quality

Questions:

- does the scanner have enough bars/prices?
- are timestamps reliable?
- is volume available?
- are prices stale?
- are stop/target levels valid?
- is provider data complete enough?

Pass criteria:

- data-quality warnings are rare or understood
- missing data does not create false positives
- degraded data blocks alerts where appropriate

### Gate 2: Outcome Evidence

Questions:

- what happened after watch-only alerts?
- did candidates hit target before stop?
- what was max favorable excursion?
- what was max adverse excursion?
- what was end-of-day return?
- did performance depend on one outlier?

Pass criteria:

- enough sample size for the lane
- outcome metrics are stable enough to trust
- failure modes are documented
- data-quality caveats are included

### Gate 3: Risk and Execution

Questions:

- is the spread acceptable?
- is volume/liquidity adequate?
- does the stop make sense?
- does the target make sense?
- is risk/reward acceptable?
- would execution assumptions be realistic?

Pass criteria:

- risk/reward is consistently valid
- illiquid names are blocked
- gap/extension risk is controlled
- stop/target logic is deterministic

### Gate 4: Notification Safety

Questions:

- does the message clearly say watch-only or official?
- could the user confuse it for a buy/sell instruction?
- are disclaimers present?
- is the source artifact clear?

Pass criteria:

- templates pass notification validation
- watch-only language is explicit
- official pick language appears only for official picks

### Gate 5: Operational Reliability

Questions:

- does the workflow run at the right time?
- does it skip safely outside windows?
- does it fail loudly enough?
- does it preserve evidence?
- does it avoid duplicate spam?

Pass criteria:

- run-status artifacts exist
- missing credentials are handled safely
- duplicate alerts are controlled
- failures preserve diagnostics

### Gate 6: Founder Approval

Required before:

- enabling paper trading for any lane
- promoting watch-only scanner behavior into official behavior
- applying learned weight changes
- enabling any real-money automation

Approval should include:

- what is being approved
- effective date
- lane/model/scanner
- evidence summary
- rollback criteria

## Outcome Evaluation Rules

Watch-only outcomes should be evaluated separately from official picks.

### Intraday Outcome Horizons

Suggested horizons:

- `15m`
- `30m`
- `60m`
- `eod`

Metrics:

- end return percent
- max favorable excursion
- max adverse excursion
- target before stop
- stop before target
- R multiple
- data quality

Rules:

- ambiguous bar ordering should be flagged
- missing bars should be explicit
- outcomes should join to candidate IDs
- outcome rows should not mutate candidate rows silently

### Official Pick Outcomes

Official outcomes belong in or derive from:

- `data/picks_log.csv`

Rules:

- only official rows affect official statistics
- watch-only rows must be excluded
- terminal statuses should be counted once
- active monitoring should exclude terminal rows

## Anti-Corruption Rules

Treat the following as serious bugs:

- a watch-only candidate written to `data/picks_log.csv`
- a research-only candidate written to `data/picks_log.csv`
- a backtest candidate mixed with live forward evidence without labeling
- a rejected candidate sent as an actionable Telegram alert
- a watch-only alert using BUY/SELL instruction language
- a paper-trading flag enabled by default
- a live-trading flag enabled by default
- an outcome row silently changing candidate classification
- a learned rule auto-promoting candidates without approval
- terminal official picks loaded as active positions

## Testing Ideas

Future tests should verify:

- default candidate flags are safe
- watch-only rows do not affect official statistics
- research-only rows cannot become official picks directly
- terminal statuses are excluded from active monitoring
- candidate IDs join to outcome rows
- paper/live flags default false
- notification language matches lifecycle state
- rejected candidates preserve reasons
- missing data produces warnings rather than silent success

## Implementation Order

Recommended order:

1. keep this document planning-only
2. define normalized candidate schema
3. write candidate records in warning-only mode
4. evaluate watch-only outcomes
5. create learning reports
6. add readiness gate report
7. only then discuss paper-trading promotion

## Final Candidate Lifecycle Rule

No candidate should gain authority by accident.

Every transition toward action must be:

- explicit
- evidenced
- logged
- reviewed
- reversible
- approved where required

If a future developer cannot tell whether something is official, watch-only, research-only, paper, or live, the lifecycle design has failed.
