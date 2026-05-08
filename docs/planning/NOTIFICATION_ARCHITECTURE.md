# Notification Architecture

## Purpose

This document defines how Daily Stock Agent should render and send user-facing notifications.

The goal is to make every message:

- clear
- safe
- consistent
- auditable
- easy to test
- explicit about whether something is official, watch-only, research-only, or operational

This document is planning-only for now. It should guide future refactors.

## Core Principle

Notification wording is product behavior.

A confusing Telegram message can make a watch-only idea look like an official pick.

A future notification layer must prevent that.

## Notification Classifications

### Official Model Pick

Meaning:

- a model-generated official pick
- may be tracked in `data/picks_log.csv`
- may affect official pick statistics

Required language:

- "model pick"
- "official model pick"
- "entry reference"
- "stop-loss reference"
- "take-profit reference"
- "not financial advice"

Avoid language:

- "you should buy"
- "your position"
- "guaranteed"
- "safe trade"

### Model Position Update

Meaning:

- update about an existing official model pick or model position
- may mention SL/TP, day close, status, or evaluation

Required language:

- "model position update"
- "tracked model pick"
- "reference level"

Avoid language:

- "your position"
- "sell now"
- "buy more"

### Watch-Only Idea

Meaning:

- monitored idea
- not an official pick
- does not affect official pick statistics
- does not imply action

Required language:

- "WATCH ONLY"
- "monitoring-only"
- "not an official model pick"
- "do not treat this as a buy/sell instruction"

Avoid language:

- "BUY"
- "SELL"
- "official pick"
- "entry signal"
- "trade this"

### Research-Only Note

Meaning:

- long-term research, Monster Hunter thesis, fundamental research, backtest, or wisdom note
- not actionable
- not official

Required language:

- "research-only"
- "thesis candidate"
- "not an official model pick"
- "requires further validation"

Avoid language:

- "official long-term pick"
- "core hold"
- "buy and hold" unless explicitly approved and validated

### Operational Alert

Meaning:

- workflow ran, skipped, failed, or recovered
- status/debugging message, not a trade idea

Required language:

- "workflow status"
- "run status"
- "skipped"
- "failed"
- "recovered"
- "no official pick generated"

Avoid language:

- any trade instruction

## Current Sender Scripts

Known sender/notification scripts include:

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

Future refactor should keep these scripts as workflow entrypoints where useful, but move rendering and Telegram delivery into shared modules.

## Proposed Package Structure

Future package:

- `src/notifications/__init__.py`
- `src/notifications/telegram_client.py`
- `src/notifications/renderer.py`
- `src/notifications/templates.py`
- `src/notifications/dedupe.py`

### `telegram_client.py`

Responsibilities:

- send messages to Telegram
- handle missing credentials safely
- handle API errors
- handle retries if appropriate
- return structured send result
- avoid duplicating token/chat-id logic across scripts

### `renderer.py`

Responsibilities:

- render typed notification payloads into message text
- enforce classification-specific wording
- ensure disclaimers exist
- truncate long messages safely
- escape Telegram Markdown safely

### `templates.py`

Responsibilities:

- store canonical message templates
- define section ordering
- centralize disclaimers
- keep message format consistent across workflows

### `dedupe.py`

Responsibilities:

- generate notification fingerprints
- avoid repeated intraday alerts
- avoid repeated news alerts
- preserve dedupe state separately from candidate/evidence artifacts

## Message Types

Suggested message type names:

- `daily_official_picks`
- `daily_no_pick_report`
- `late_watch_only_ideas`
- `watch_only_intraday_ideas`
- `model_position_update`
- `news_alert`
- `daily_execution_report`
- `weekly_review`
- `monthly_report`
- `monster_research_report`
- `workflow_status`
- `data_quality_warning`

## Required Message Metadata

Every rendered notification should ideally know:

- `message_type`
- `classification`
- `date`
- `timestamp_utc`
- `source_script`
- `source_artifact`
- `ticker_count`
- `official_pick`
- `watch_only`
- `research_only`
- `paper_trading_enabled`
- `live_trading_enabled`

## Safety Defaults

Unless explicitly overridden by approved model state:

- `official_pick: false`
- `watch_only: true`
- `research_only: false`
- `paper_trading_enabled: false`
- `live_trading_enabled: false`

For research reports:

- `official_pick: false`
- `watch_only: false`
- `research_only: true`
- `paper_trading_enabled: false`
- `live_trading_enabled: false`

## Standard Disclaimers

### Official Pick Disclaimer

Suggested text:

- Educational model output only. Not financial advice. Use your own judgment and risk controls.

### Watch-Only Disclaimer

Suggested text:

- WATCH ONLY / monitoring-only. This is not an official model pick and not a buy/sell instruction.

### Research-Only Disclaimer

Suggested text:

- Research-only note. This is not an official model pick and not a trading instruction.

### Operational Disclaimer

Suggested text:

- Workflow status message only. No trading action is implied.

## Validation Rules

Notification tests should verify:

- official pick messages include official/model-pick wording
- watch-only messages include WATCH ONLY wording
- research-only messages include research-only wording
- paper/live flags do not appear enabled by default
- no watch-only template uses BUY or SELL as instruction language
- Markdown rendering does not break Telegram parsing
- long messages truncate safely
- missing optional fields do not crash rendering
- message classification is explicit

## Migration Strategy

### Phase 1: Document Only

Status:

- current

Rules:

- no runtime behavior changes
- document desired structure
- keep existing sender scripts working

### Phase 2: Shared Renderer for One Low-Risk Sender

Start with one sender, likely:

- `scripts/send_late_daily_ideas_telegram.py`

Why:

- watch-only language matters
- lower risk than official pick sender
- easy to compare old and new output

### Phase 3: Shared Telegram Client

Move token/chat-id/API send logic into:

- `src/notifications/telegram_client.py`

Keep script entrypoints.

### Phase 4: Migrate Intraday Alerts

Move intraday watch-only rendering into shared renderer.

Ensure:

- WATCH ONLY label
- no official-pick wording
- dedupe preserved
- candidate artifact references preserved

### Phase 5: Migrate Official Pick Messages

Only after watch-only and intraday rendering is stable.

Compare old/new output carefully.

### Phase 6: Migrate Reports

Migrate weekly/monthly/meta-brain/monster/research reports gradually.

## Anti-Patterns

Avoid:

- each script inventing its own disclaimer
- watch-only alerts saying BUY
- research reports sounding like official picks
- Telegram send code copied into many scripts
- Markdown escaping implemented differently per sender
- notification delivery mutating model artifacts
- dedupe state being treated as evidence
- missing Telegram credentials being treated as model failure

## Final Notification Rule

Every user-facing message must make clear:

- what it is
- whether it is official
- whether it is watch-only
- whether it is research-only
- whether action is implied
- what artifact or workflow produced it

If a message could confuse a user into thinking a watch-only idea is an official pick, the message is wrong.
