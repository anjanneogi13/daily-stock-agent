# Intraday Model Strategy

## Goal

Build the intraday system as a serious product-ready model internally, but keep all new intraday opportunities user-facing as WATCH ONLY until performance is proven.

Internal goal:

- serious intraday model
- candidate tracking
- outcome tracking
- daily performance reports
- weekly recalibration reports
- model versioning
- self-learning over time

External/user-facing status for now:

- WATCH ONLY
- not official picks
- not buy instructions
- educational only
- under validation

## Promotion Criteria

The intraday model should only become official after evidence proves it works.

Suggested gate:

- 100–200+ tracked intraday candidates
- win rate >= 60%
- positive average R
- profit factor > 1.3
- stable performance across multiple weeks
- acceptable max drawdown
- no single ticker/sector/day explains most gains

Win rate alone is not enough.

Example:

60% wins at +1.5R and 40% losses at -1R = strong.
60% wins at +0.5R and 40% losses at -1R = bad.

So promotion requires both win rate and positive expectancy.

## Current System

The intraday workflow currently does two things:

1. Monitors existing model picks
2. Scans for new watch-only intraday opportunities

Workflow:

- `.github/workflows/intraday_monitor.yml`

Main scripts:

- `scripts/intraday_monitor.py`
- `scripts/send_intraday_telegram.py`
- `scripts/intraday_scanner.py`
- `src/opening_range_scanner.py`

## Existing Pick Monitoring

The monitor checks open/pending model picks from:

- `data/picks_log.csv`

It can alert on:

- near stop-loss
- hit stop-loss
- halfway to take-profit
- hit take-profit
- volume spike
- material news
- trailing stop raise
- adaptive TP raise
- adaptive SL tighten

This is useful because target users may not have time to monitor charts all day.

But the message must be clearly framed as a model position update, not a new intraday pick.

## Product Messaging Problem

A message like this can confuse users:

- `INTRADAY UPDATE`
- `Pick Status`
- `DOWN GILT...`

Better framing:

- `MODEL POSITION UPDATE — 10:30 ET`
- `GILT — swing model pick from 2026-05-05`
- `Current: $19.35`
- `Model entry: $19.98`
- `Model SL: $19.42`
- `Status: Hit model stop-loss`
- `Only relevant if you entered or are tracking this model pick.`
- `Educational only. Not financial advice.`

Telegram messages should separate:

- `MODEL POSITION UPDATES`
- `WATCH-ONLY INTRADAY IDEAS`

They should not be mixed ambiguously.

## Current Intraday Opportunity Logic

There are two opportunity paths:

1. Opening-range breakout scanner
2. Legacy momentum scanner

### Opening-range scanner

Current parameters:

- 15-minute opening range
- minimum 3 opening-range bars
- breakout above opening-range high
- minimum breakout: 0.10%
- minimum volume ratio: 1.5x
- max extension: 3.0%
- max gap: 8.0%
- stop reference: opening-range low
- take-profit reference: entry + 1.5R

### Legacy momentum scanner

Current parameters:

- intraday move > +1.5%
- volume ratio >= 1.5x
- score >= 70
- optional catalyst/news boost

Current scoring:

- base score = 50
- plus momentum boost
- plus volume boost
- plus catalyst boost

## Current Strengths

The current model has a useful foundation:

- opening-range breakout logic
- volume confirmation
- anti-chase guard
- gap guard
- watch-only labeling
- dedupe
- evidence logging

## Current Weaknesses

The current model is not yet a powerful intraday picking model.

Missing or underdeveloped:

- VWAP
- RSI for candidate selection
- MACD
- moving averages
- stochastic oscillator
- divergence detection
- Bollinger Bands
- ATR/volatility-adjusted stops
- support/resistance
- premarket high/low
- prior day high/low
- spread/liquidity filters
- dollar volume filters
- SPY/QQQ/sector alignment
- relative strength
- time-of-day learning
- post-alert outcome tracking
- self-learning recalibration

## Target Product Design

### Daily Picks

Official morning picks.

### Model Position Monitor

Monitors already-issued official model picks.

Should alert on:

- near SL
- hit SL
- near TP
- hit TP
- SL raised
- TP raised
- material news
- momentum fading

Must use language like:

- model pick
- model stop-loss
- model take-profit
- if you entered or are tracking this model pick

Must not imply the app knows the user actually entered the trade.

Avoid language like:

- your position
- you are down
- you should sell
- you should buy

### Intraday Watchlist Scanner

Finds new same-day watch-only opportunities.

Must clearly say:

- WATCH ONLY
- not an official pick
- not a buy instruction
- under validation

## Active Pick Loading Rules

Current active-pick loading should be improved.

Target behavior:

- monitor all active unresolved official picks
- respect trade type
- exclude watch-only ideas from position monitoring
- avoid stale indefinite monitoring

Suggested rules:

- day trade: monitor same ET trading day only
- swing trade: monitor while pending/open, max defined age
- watch_only: exclude from position monitoring
- closed/sl_hit/tp_hit/day_close/unreachable_entry: exclude

## Scanner Independence

The scanner should run even if there are no active picks.

Target flow:

1. Monitor existing active picks if any
2. Scan for new watch-only intraday ideas if scanner window is open
3. Send a message only if either section has content

## Self-Learning Loop

The intraday system should learn from every candidate.

### Candidate snapshot

Write every candidate to:

- `data/intraday_candidates_YYYY-MM-DD.jsonl`

Include:

- ticker
- timestamp
- scanner type
- model version
- score
- entry reference
- stop reference
- target reference
- all feature values
- all blockers
- market context
- watch_only flag

### Outcome tracking

Evaluate candidates at:

- +15 minutes
- +30 minutes
- +60 minutes
- end of day

Track:

- price at horizon
- max favorable excursion
- max adverse excursion
- TP before SL
- SL before TP
- end-of-day return
- R multiple

Write outcomes to:

- `data/intraday_outcomes_YYYY-MM-DD.jsonl`

### Daily learning report

Write:

- `data/intraday_learning_report_YYYY-MM-DD.json`

Include:

- candidate count
- win rate
- average R
- profit factor
- best setup
- worst setup
- best time bucket
- worst time bucket
- feature bucket performance

### Weekly recalibration report

Write:

- `data/intraday_recalibration_report_YYYY-MM-DD.json`

Suggest:

- threshold changes
- volume-ratio changes
- gap guard changes
- VWAP distance changes
- time bucket suppression
- scanner promotion/demotion

Initial recalibration should require human approval.

## Maturity Ladder

- Level 0: Logs only
- Level 1: Watch-only observations
- Level 2: Telegram watchlist ideas
- Level 3: Paper-traded intraday model
- Level 4: Official intraday picks after proven performance

Current state:

- between Level 1 and Level 2

Target next state:

- Level 2 with Level 3 evidence collection

## Immediate Priorities

1. Fix Telegram UX and separate message sections
2. Add pick_date and trade_type to position alerts
3. Improve active pick loading
4. Let scanner run independently
5. Add candidate snapshot file
6. Add outcome tracking
7. Add daily learning report
8. Add weekly recalibration report

## Principle

The goal is not to send more intraday alerts.

The goal is to send fewer, clearer, better-supported signals.

Trust is more important than excitement.
