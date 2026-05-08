# Daily Stock Agent — Agent Maturity Tracker

**Created:** 2026-05-06
**Mode:** monitoring-only
**Purpose:** Track real-world trading lessons as the agent matures from signal generator into disciplined market assistant.

This document records observed behavior, founder/co-founder analysis, product lessons, and future intelligence upgrades.

It complements:

- `docs/PROJECT_BLUEPRINT.md` — canonical architecture and roadmap.
- `docs/WORK_LOG.md` — append-only implementation history.
- `docs/NEXT_SESSION.md` — near-term handoff.
- this file — trading intelligence maturity and daily lessons.

---

## Operating Principle

The agent is not allowed to trade real money or paper trade yet.

Current mission:

1. Recommend.
2. Monitor.
3. Explain.
4. Evaluate.
5. Learn.
6. Improve.

The agent becomes useful only if it learns from:

- real monitoring results,
- missed opportunities,
- bad timing,
- stale prices,
- wrong trade classification,
- historical market behavior,
- fundamental business quality,
- price/volume pattern history,
- regime changes.

---

## Trading Lanes

The agent must mature into three separate lanes. These lanes should not be mixed because each has different time horizon, entry logic, stop logic, target logic, and exit strategy.

### Lane 1 — Premarket Swing Picks

**Goal:** Find stocks worth holding for days/weeks with clear entry, stop-loss, target, and risk sizing.

**Current behavior:**

- Sends daily picks through Telegram.
- Logs picks to `data/picks_log.csv`.
- Tracks outcomes through evaluation scripts.

**Current weaknesses:**

- Daily picks can arrive after market open if GitHub Actions is delayed.
- Late picks can become live-market chase trades while still being labeled as normal daily picks.
- Premarket price verification can fail.
- Company/tag metadata may be blank.
- News catalysts marked as `intraday` can still become `swing` picks.

**Maturity target:**

- Official daily swing picks must be sent before market open only.
- If late, the agent should not send actionable swing picks.
- If price is stale or unverified, the agent should mark the idea as watch-only.
- Swing picks should require multi-day confirmation, not just urgent news.

---

### Lane 2 — Intraday Opportunities

**Goal:** Detect live market opportunities during the US session.

**Current behavior:**

- Intraday monitor sends status updates.
- It can detect new opportunities such as `NET`.

**Current weaknesses:**

- Scanner is reactive and may detect stocks after large moves are already obvious.
- It can miss ideal opening entries.
- It does not yet have mature opening-range / VWAP confirmation logic.

**Maturity target:**

- Add opening-range scans:
  - 09:35 ET early gap scan.
  - 09:45 ET opening-range scan.
  - 10:00 ET VWAP confirmation scan.
- Do not chase if a stock is already too extended.
- For news catalysts with `action_window=intraday`, use intraday-specific plans:
  - wait for first 5–15 minutes,
  - confirm VWAP/opening-range hold,
  - stop below intraday structure,
  - exit or reclassify before close.

---

### Lane 3 — Monster Hunt / Long-Term Compounders

Canonical design:

- `docs/MONSTER_HUNTER_DESIGN.md`

Monster Hunt is a dedicated long-term research lane, not an extension of swing trading.

It should mature into a serious compounder analyst that studies:

- 6-month to 5-year multi-bagger potential,
- quarterly and yearly P&L trends,
- revenue, EPS, margin, and free-cash-flow durability,
- management execution,
- moat and competitive positioning,
- secular 5-10 year themes,
- ETF, mutual fund, and institutional focus,
- sector rotation and long-term capital flows,
- valuation versus growth,
- thesis-break conditions.


**Goal:** Find fundamentally strong stocks that may compound over months/years and produce multi-fold returns.

Founder examples and thesis candidates include:

- AI / semiconductor / hardware / storage winners:
  - Sandisk-style multi-baggers,
  - Micron,
  - Seagate,
  - Western Digital,
  - TSMC,
  - Applied Materials,
  - Broadcom,
  - Marvell,
  - Nvidia,
  - AMD,
  - ASML,
  - and similar companies in other secular-growth industries.

**Current behavior:**

- Monster/long-holder concept exists in architecture and safety gates.
- `monster_score` exists in schema.
- Monster readiness gate exists conceptually: >90% win rate and positive expectancy.
- Active monster-hunt intelligence is not mature yet.

**Current weaknesses:**

- Agent is mostly optimized for daily/swing/news trades.
- It does not yet deeply analyze fundamentals, P&L history, secular themes, or multi-year chart structure.
- It may treat speculative news names too similarly to true compounders.
- It does not yet maintain a formal monster watchlist with thesis states.

**Maturity target:**

Monster-hunt should be a separate lane with its own outputs:

- `Candidate`
- `Watchlist`
- `Confirmed`
- `Core Hold`
- `Add-on Zone`
- `Trim Zone`
- `Exit Watch`
- `Thesis Broken`

Monster entries should not use tight day/swing stops. They should use:

- staged entries,
- thesis invalidation,
- weekly/monthly trend breaks,
- earnings/fundamental deterioration,
- major moving-average/trendline exits,
- partial profit-taking rules.

---

## 2026-05-06 Paper Trading Activation Checklist

Paper trading remains disabled.

Before enabling `TRADING_MODE=paper`, future sessions must follow:

- `docs/decisions/2026-05-06-paper-trading-activation-checklist.md`

Key rule:

- opening-range scanner outputs are `WATCH ONLY` / `monitoring_only`.
- opening-range observations persist to `data/opening_range_observations_YYYY-MM-DD.jsonl`.
- watch-only observations must not become paper trades.
- paper trading requires explicit founder approval plus readiness gates.

---

## 2026-05-06 Audit Fixes Implemented

The comprehensive repo audit fixed the most important operational safety gaps before new feature work.

Implemented:

1. **Premarket timing hard gate**
   - Normal daily picks are blocked after 09:20 ET.
   - Manual dispatch cannot bypass the gate.
   - Late workflow runs send a missed-window alert.

2. **Price freshness / stale-entry protection**
   - Unverified prices become `WATCH ONLY`.
   - Telegram avoids actionable buy instructions for watch-only ideas.

3. **News action-window enforcement**
   - News signals preserve `action_window`.
   - Intraday-news swing candidates become watch-only instead of silent normal swing picks.

4. **Monitoring-only paper safety**
   - Local paper logging is disabled by default.
   - `TRADING_MODE=paper` is now required to write legacy paper-trade artifacts.

5. **Intraday monitor close persistence**
   - SL/TP hits detected intraday now update the correct `pick_date` in CSV.

Lower-severity hygiene completed before new features:

1. `data/learning_journal.jsonl` test side effects are isolated.
2. Remaining tracked data isolation audited clean for `data/picks_log.csv` and `data/signal_journal.jsonl`.
3. Closed-status logic is aligned between enforcement and monitoring readiness dashboards.

Next feature roadmap item:

1. Build opening-range intraday scanner.

---

## 2026-05-05 Trading Day Review

### Summary

The agent performed better than last week in idea generation. It found real catalysts and one strong older swing winner closed. However, the day exposed execution and classification weaknesses.

Important outcomes:

- `POWI` — earlier swing pick from 2026-04-28, hit take-profit on 2026-05-05.
- `EXPD` — valid earnings-beat catalyst, but stopped out before recovering later.
- `GILT` — valid contract-win catalyst, still pending, but speculative quality concern.
- `NET` — strong intraday opportunity detected too late.

---

### POWI — Strong Swing Win

**Picked:** 2026-04-28 16:28:59
**Closed:** 2026-05-05
**Result:** `tp_hit`
**Return:** `+16.76%`
**R multiple:** `+2.0R`
**Alpha vs SPY:** `+14.89%`
**Sector alpha vs SOXX:** `+6.73%`

Lesson:

- The swing system can produce strong winners.
- Founder missed it in memory because it was not a new 2026-05-05 pick; it was an older swing pick that matured.


---

### EXPD — Valid Catalyst, Poor Execution Classification

**Catalyst:** Q1 earnings double beat.

News classification:

- sentiment: bullish
- urgency: high
- category: earnings beat
- tradeable score: 0.88
- action window: intraday

Agent pick:

- trade type: swing
- entry: 149.14
- stop-loss: 146.60
- target: 153.37

Outcome:

- hit stop loss
- `-1.0R`
- `-1.70%`

Lesson:

- EXPD was not a nonsense pick.
- The catalyst was real.
- The issue was execution classification and timing.
- News said `intraday`, but the pick was sent as `swing`.
- It hit stop and later recovered, suggesting entry/stop handling was too fragile for a post-earnings intraday mover.

Follow-up:

- If news action window is `intraday`, do not silently log as normal swing.
- Require intraday plan or stronger multi-day confirmation.

---

### GILT — Real Catalyst, Speculative/Pump Risk

**Catalyst:** Multimillion order from Nelco.

News classification:

- sentiment: bullish
- urgency: high
- tradeable score: 0.72
- action window: intraday

Agent pick:

- trade type: swing
- status: pending

Founder concern:

- GILT has suffered major long-term value destruction from prior highs.
- It may be a speculative news-driven stock rather than a high-quality long-term compounder.
- It may be tradable, but should not automatically be considered a normal swing or monster candidate.

Lesson:

- The agent needs a fundamental-quality / pump-risk smell.
- Long-term drawdown, weak quality, small-cap news spikes, and sudden contract headlines should be treated carefully.
- A stock may be good for intraday momentum but bad for long-term holding.

Follow-up:

- Add smell or scoring penalty for:
  - huge all-time-high drawdown,
  - weak long-term trend,
  - small-cap news spikes,
  - poor fundamentals,
  - dilution/reverse-split history if available,
  - low liquidity.

---

### NET — Good Opportunity Detected Late

Observed founder point:

- NET opened around 231.06 and closed around 244.43.
- Agent detected it later around 247.90 / 244.42 with strong volume.

Lesson:

- Intraday scanner is currently reactive.
- It identifies momentum after the move is already obvious.
- It needs opening-range logic to catch earlier high-quality moves.

Follow-up:

- Add 09:35 / 09:45 / 10:00 ET scans.
- Use gap, volume, VWAP, opening range, and news context.
- Avoid late chase when most of the move already happened.

---

## 2026-05-05 Operational Lessons

### Daily Picks Timing Failure

Problem:

- Founder did not receive official Telegram picks before market automatically.
- Manual run produced only `GILT` around 9:13 PM Singapore time.
- Later automatic run produced `EXPD` and `GILT` around 10:33 PM Singapore time, after US market open.

Likely root causes:

- GitHub Actions cron delays.
- `daily-picks.yml` allows runs until 11:00 ET.
- Manual dispatch bypasses time guard.
- Data/news/price inputs changed between manual and automatic runs.

Required behavior:

- Official premarket picks must not be sent after market open.
- If workflow is late, send a missed-window alert instead of normal picks.
- Manual run must not bypass price freshness and stale-entry checks.

Proposed rule:

- Before 09:20 ET: send official daily picks.
- After 09:20 ET: do not send normal daily picks.
- If missed, send a premarket-window-missed alert.
- Allow only intraday monitor alerts after the cutoff.

---

### Price Freshness / Buy Price Problem

Problem:

- Manual GILT pick showed buy around 18.34.
- Later automatic GILT pick showed buy around 19.98.
- Founder could not have bought at the stale/manual price.

Required behavior:

- The agent must not send actionable buy prices from stale or unverified data.
- If price cannot be verified, mark as watch-only.
- Telegram should clearly say when a pick is not actionable.

Proposed rule:

- If live price is unavailable or stale, do not show actionable entry.
- Mark the idea as WATCH ONLY.
- Require fresh quote before entry.

---

## Fundamental Analysis Roadmap

Founder thesis:

- To reduce risk and improve quality, the agent should evaluate company fundamentals before picks, especially for swing and monster-hunt lanes.
- Day trading can rely more on price, volume, and news, but swing and monster picks should understand business quality.

Required fundamental analysis:

1. Quarterly P&L review.
2. Yearly P&L review.
3. Revenue growth trend.
4. EPS growth trend.
5. Gross margin and operating margin trend.
6. Net income trend.
7. Free cash flow trend.
8. Debt and liquidity.
9. Guidance and management commentary.
10. Earnings surprise history.
11. Valuation context.
12. Sector and industry tailwinds.
13. Quality vs speculative classification.

For swing trades:

- Fundamentals should act as quality filter and fallback context.
- If a fundamentally strong swing temporarily fails to hit TP, agent may consider extended hold only if thesis remains valid.
- This must be explicit; a failed swing must not silently become a long-term baghold.

For monster-hunt:

- Fundamentals are mandatory.
- Agent should plan a greater-than-one-year thesis.
- Agent should monitor thesis health, add zones, trim zones, and exit conditions.


---

## Reader / Wisdom Learning Roadmap

Founder thesis:

- The agent should learn from the best available books and materials on trading, chart reading, fundamental analysis, market psychology, risk management, historical bubbles/crashes, long-term investing, and sector cycles.

This idea aligns with existing architecture concepts:

- Wisdom base.
- Reader engine.
- Curiosity engine.
- Historical regime engine.

Implementation principle:

- Use only legally accessible sources, public-domain materials, licensed notes, or founder-provided excerpts.
- Convert lessons into structured wisdom rules.
- Rules must remain in observe mode until tested.
- No book rule should bypass data-quality or readiness gates.

Example rule candidate:

- Lesson: Do not average down into deteriorating fundamentals.
- Source type: book, research note, or founder-provided excerpt.
- Applies to: swing and monster.
- Rule candidate: penalize stocks with falling revenue and falling margins despite bullish news.
- Status: observe.

---

## Historical Regime Learning Roadmap

Founder thesis:

The agent cannot wait years to experience every market regime. It should learn from historical market events and understand how stock picking must change across regimes.

Regimes/events to study:

- bull markets,
- bear markets,
- sideways/stagnant markets,
- recessions,
- inflation shocks,
- rate-hike cycles,
- COVID-19 crash/recovery,
- Lehman / Global Financial Crisis,
- dot-com bubble,
- Great Depression,
- black swan events,
- sector bubbles and rotations.

Required learning:

1. What worked in each regime?
2. What failed?
3. Which indicators gave early warnings?
4. How should position sizing change?
5. When should swing/day trades be reduced?
6. When should cash be preferred?
7. When should monster stocks be accumulated vs avoided?
8. How do correlations change in crisis?

Implementation target:

- Historical regime simulator.
- Regime-tagged backtests.
- Scenario playbooks.
- Regime-specific scoring weights.
- Crisis-mode hard blocks and risk reductions.


---

## Historical Chart and Pattern Learning Roadmap

Founder thesis:

The agent should not wait years to learn patterns from live picks. It should learn from historical charts and recalibrate itself by replaying past market data.

Required capabilities:

1. Replay historical daily/intraday charts.
2. Apply current pattern engine to old data.
3. Measure whether patterns predicted future returns.
4. Recalibrate thresholds.
5. Learn from failed historical setups.
6. Learn from monster-stock early bases and breakouts.
7. Learn day/swing timing from opening gaps, VWAP, and volume.
8. Compare pattern performance by regime.

Implementation target:

- Historical chart reader.
- Pattern replay engine.
- Walk-forward backtester.
- Opening-range backtester.
- Monster-base detector.
- Parameter recalibration loop.

Important constraint:

- Avoid overfitting.
- Use train/test time splits.
- Keep all promoted rules in observe mode until forward validation passes.

---

## Agent Maturity Scorecard

Track these over time:

| Area | Current maturity | Target |
|---|---:|---|
| Catalyst discovery | medium | high |
| Premarket timing | weak | high |
| Price freshness | weak | high |
| Swing classification | medium-low | high |
| Intraday timing | weak | high |
| Fundamental analysis | immature | high |
| Monster hunt | immature | high |
| Historical regime learning | planned | high |
| Historical chart learning | planned | high |
| Smell/pump-risk detection | immature | high |
| P&L / earnings analysis | planned | high |
| Risk sizing | medium | high |
| Outcome journaling | improving | high |
| Documentation memory | strong | high |

---

## Near-Term Implementation Priorities

1. **Premarket timing hard gate** — implemented 2026-05-06
   - no normal daily picks after 09:20 ET.
   - send missed-window alert instead.

2. **Price freshness and stale-entry protection** — implemented 2026-05-06
   - no actionable buy price if quote unavailable/stale.

3. **News action-window enforcement** — implemented 2026-05-06
   - `intraday` news must not silently become `swing`.

4. **Opening-range intraday scanner**
   - detect NET-like opportunities earlier.

5. **Fundamental-quality / pump-risk smell**
   - protect swing/monster lanes from speculative low-quality names.

6. **Monster-hunt foundation**
   - separate watchlist, thesis states, and long-term exit logic,
   - dedicated Monster Hunter design in `docs/MONSTER_HUNTER_DESIGN.md`,
   - long-term theme radar,
   - full fundamental and P&L analysis,
   - ETF/mutual fund/institutional focus analysis,
   - research-only reports before any scoring influence.

7. **P&L / earnings analyzer**
   - quarterly/yearly fundamentals for swing and monster picks.

8. **Historical regime and chart learning**
   - learn from past bull/bear/sideways/crisis markets.

9. **Reader / wisdom ingestion**
   - transform legal market wisdom sources into testable observe-mode rules.

---

## Non-Negotiables

- Monitoring-only until readiness gates pass.
- No real-money trading.
- No paper trading yet.
- Do not manually enable enforcement flags.
- Do not convert failed swings into long-term holds without explicit thesis validation.
- Do not classify speculative news spikes as monster candidates without fundamentals.
- Do not let Monster Hunter outputs become official picks, paper trades, or live trades without explicit validation and founder approval.
- Do not promote any Monster Hunter rule beyond observe mode until historical and forward evidence support it.
- Do not send stale/unverified prices as actionable entries.

## 2026-05-08 — Lesson: no-pick explainability is part of intelligence

Observation:
- Three straight days had zero official Daily Picks rows.
- May 8 proved the agent did find finalists but hard-blocked both.
- Therefore the key intelligence gap was not only pick selection; it was explainability of rejection.

Maturity upgrade:
- No-pick cause classification added.
- Candidate rejection diagnostics added.
- Hard-blocked finalist context is now preserved for review.
- Provider-health evidence is now persisted on failed Daily Picks recovery.
- yfinance pressure reduced in official scoring paths.

Lesson:
- A mature agent must explain what it rejected, not only what it selected.
- "No pick" is acceptable only when supported by evidence.
- The next intelligence milestone is not more aggression; it is better attribution of rejection, data quality, and opportunity quality.
