# 🧠 Daily Stock Agent — Architecture (Source of Truth)

> **Version:** v1.0 (May 3, 2026 — written after 8/8 pillars complete)
> **Purpose:** The single, honest map of how this agent works end-to-end.
> **Audience:** Future-you, future-AI sessions, future contributors.
> **Promise:** Every claim in this document has file:line evidence. No marketing.

---

## 0. TL;DR (read this first)

This is an AI agent that picks ~5-10 US stocks per trading day, sends them to Telegram with entry/SL/TP/quantity, then evaluates outcomes nightly and learns from them. It runs entirely on free GitHub Actions (no server). 8 brain "pillars" cooperate to make picks smarter over time.

EVERY MORNING (8:30 AM ET): Universe (~5000 tickers) → Filter (price/volume/fundamentals) → Score each candidate (composite_score) → Apply brain layers (regime / news / catalysts / wisdom) → Apply auto-pause guard (skip if rules currently broken) → Pick top N → write picks_log.csv → Send to Telegram with SL/TP/qty + wisdom hint

EVERY EVENING (6 PM ET): → Re-fetch each open pick → compute outcome → Append to signal_journal.jsonl → Send X-ray report + dashboard to Telegram → Append daily observation (learning)

EVERY WEEK (Sat 0:00 UTC): → Weekend reflection (LLM grades the week) → Weekly report card + Telegram summary → Hypothesis review (Sun 15:00 UTC)

EVERY MONTH (1st of month): → Monthly X-ray (deep dive)

Code

---

## 1. The 8 Brain Pillars (what each one does)

| # | Pillar | Status | Core modules | One-line role |
|---|---|---|---|---|
| 1 | Probability Engine | ✅ 100% | `probability_engine.py`, `scorer.py`, `parallel_scorer.py`, `stock_stats.py` | Scores each candidate stock with multi-layer signals |
| 2 | Wisdom Base | ✅ 100% | `wisdom_base.py`, `wisdom_hint.py`, `wisdom_consultant.py`, `wisdom_coverage.py` | Surfaces relevant trading lessons on each pick |
| 2.5 | Books-into-Brain | ✅ 100% | `book_ingest.py`, `wisdom_base.py` (extended) | Imports century-old book wisdom as context-triggered lessons |
| 3 | Pattern Recognition | ✅ 100% | `pattern_engine.py`, `pattern_layer.py`, `pattern_stats.py`, `patterns/*.py` | Detects 16 chart patterns + applies edge-weighted multiplier |
| 3.5 | Calibration Brain | ✅ 100% | `calibration.py`, `weight_proposer.py` | Analyzes per-factor accuracy and proposes weight tweaks |
| 4 | Feedback Loop | ✅ 100% | `weight_applier.py`, `auto_promote.py`, `hypothesis_engine.py`, `learning_journal.py`, `lesson_gc.py` | Applies brain mutations safely (5%/wk cap) + logs every change |
| 5 | Self-Awareness | ✅ 100% | `auto_pause.py`, `pause_state.py`, `self_awareness.py` | Pauses bad strategies + computes Wilson 30d CIs |
| 6 | P&L + Reporting | ✅ 100% | `weekly_review.py`, `quarterly_report.py`, `yearly_report.py`, `wow_trend.py`, `sector_pnl.py`, `risk_metrics.py` | Honest performance reporting (daily → yearly) |

---

## 2. Module → Pillar Map (every src/ file accounted for)

### Pillar 1 — Probability Engine
- `src/scorer.py` — composite_score() weighted sum of 7 components
- `src/parallel_scorer.py` — ThreadPool runner, calls composite_score per ticker
- `src/probability_engine.py` — v0.1 multi-layer combiner (regime/news/catalyst)
- `src/stock_stats.py` — per-ticker historical SL/TP base rates
- `src/indicators.py` — RSI, MACD, EMA, ATR, Bollinger
- `src/fundamentals.py` — score_fundamentals(), passes_filters()
- `src/news_sentiment.py` — news → sentiment score
- `src/news_classifier.py` — news → tradeable/noise classifier
- `src/news_signals.py` — bull/bear news event detection
- `src/news_engine.py` — orchestrates news fetch every 30 min
- `src/market_news.py` — macro/market news
- `src/regime.py` — bull/bear/transition/unknown classification
- `src/earnings.py` — days_to_earnings(), upcoming_earnings()
- `src/earnings_analyzer.py` — earnings beat/miss analysis
- `src/data_fetcher.py` — yfinance + Finnhub OHLCV/info loader
- `src/finnhub_data.py` — Finnhub API wrapper
- `src/cape_ratio.py` — Shiller CAPE (manually maintained monthly)
- `src/sector_benchmark.py` — SPY α, sector ETF α
- `src/semiconductors.py` — sector-specific scoring boost
- `src/monster_hunt.py` — short-squeeze/momentum monster detection
- `src/monster_data.py` — short-float, float-shares fetch
- `src/day_trading_scorer.py` — separate day-trade score
- `src/market_guard.py` — DAY/SWING classifier + sanity gates
- `src/hard_blocks.py` — penny stock / data-quality vetoes

### Pillar 2 / 2.5 — Wisdom + Books
- `src/wisdom_base.py` — lessons + patterns + kill-list storage
- `src/wisdom_hint.py` — per-pick lesson lookup (sector/ticker match)
- `src/wisdom_consultant.py` — pre-pick "should I take this?" check
- `src/wisdom_coverage.py` — % of picks that got at least 1 lesson cited
- `src/book_ingest.py` — seed.yaml → wisdom_base records
- `src/lesson_gc.py` — garbage-collects stale lessons
- `config/seed.yaml` — 50 hand-curated book lessons (B1-B6)

### Pillar 3 — Pattern Recognition
- `src/patterns/base.py` — PatternDetector ABC + Match dataclass
- `src/patterns/hhhl.py` — Higher-Highs/Higher-Lows + LHLL
- `src/patterns/breakouts.py` — 20d Donchian breakout/breakdown
- `src/patterns/flags.py` — bull_flag / bear_flag
- `src/patterns/triangles.py` — ascending / descending / symmetric
- `src/patterns/cup_handle.py` — William O'Neil cup-and-handle
- `src/patterns/double.py` — double_top / double_bottom
- `src/patterns/head_shoulders.py` — head-and-shoulders + inverse
- `src/patterns/wedges.py` — rising_wedge / falling_wedge
- `src/pattern_engine.py` — orchestrator: scan_ticker(), persist()
- `src/pattern_stats.py` — per-pattern × per-regime aggregator
- `src/pattern_layer.py` — Layer 6 multiplier + auto_enable_disable
- `scripts/scan_patterns.py` — CLI for universe scan

### Pillar 3.5 — Calibration Brain
- `src/calibration.py` — per-factor accuracy table
- `src/weight_proposer.py` — proposes boost/penalize/kill per factor
- `data/weight_proposals.jsonl` — unapplied proposals queue

### Pillar 4 — Feedback Loop
- `src/weight_applier.py` — applies proposals under 5%/wk-per-factor cap
- `src/auto_promote.py` — promotes consistent patterns to lessons
- `src/hypothesis_engine.py` — binomial significance test on tagged picks
- `src/learning_journal.py` — append-only log of every brain mutation
- `data/weight_history.jsonl` — audit trail of all weight changes
- `data/learning_journal.jsonl` — every brain change in one place

### Pillar 5 — Self-Awareness
- `src/auto_pause.py` — rolling 14d/30d health checks
- `src/pause_state.py` — active pause state (paused tags/types/regimes)
- `src/self_awareness.py` — Wilson 95% CIs + monthly calibration
- `config/auto_pause.json` — thresholds + enforce flag
- `data/pause_state.json` — what's currently paused

### Pillar 6 — Reporting
- `src/weekly_review.py` — Saturday weekly grade + post-mortem
- `src/quarterly_report.py` — 90d benchmark + sector breakdown
- `src/yearly_report.py` — annual summary scaffold
- `src/wow_trend.py` — week-over-week deltas
- `src/sector_pnl.py` — per-sector profit/loss
- `src/sector_breakdown.py` — per-sector trade counts
- `src/strategy_breakdown.py` — per-strategy/tag breakdown
- `src/performance_stats.py` — sharpe/sortino/maxdd/calmar
- `src/risk_metrics.py` — annualized + per-trade variants
- `src/performance_tracker.py` — daily P&L tracking

### Cross-cutting / Infrastructure
- `src/signal_journal.py` — every pick → outcome (Pillar 1+4 backbone)
- `src/pick_logger.py` — picks_log.csv writer
- `src/picks_csv.py` — CSV schema helpers
- `src/pick_evaluator.py` — end-of-day outcome computation
- `src/risk_manager.py` — position sizing, ATR-based plans
- `src/adaptive_sl.py` — adaptive stop-loss
- `src/adaptive_tp.py` — adaptive take-profit
- `src/exit_manager.py` — EOD/max-hold force exits
- `src/exit_metrics.py` — slippage / spread analysis
- `src/trailing_stop.py` — trail-stop logic for runners
- `src/position_monitor.py` — SL/TP proximity alerts
- `src/dedup_sender.py` — prevents duplicate Telegram messages
- `src/auto_cooldown.py` — cooldowns after losers
- `src/llm_agent.py` — Gemini/Claude wrapper
- `src/paper_trader.py` — paper-trade tracking
- `src/tracker.py` — simple position tracker
- `src/backtester.py` — historical replay engine
- `src/universe.py` — ticker universe builder
- `src/watchlist_manager.py` — bullish-news watchlist
- `src/premarket_filter.py` — premarket sanity check
- `src/confidence_band.py` — LOW/MED/HIGH confidence label

---

## 3. The Cron Calendar — When the Brain Wakes Up

| Workflow | Cron (UTC) | What it does | Telegram output |
|---|---|---|---|
| `daily-picks.yml` | 12:30 & 13:30 Mon-Fri | Run main.py → score universe → write picks → Telegram | 📲 Daily picks |
| `evaluate.yml` | 22:00 Mon-Fri | Evaluate outcomes → dashboard + X-ray | 📲 Dashboard + X-ray + position alerts |
| `intraday_monitor.yml` | every 30 min, 13-21 Mon-Fri | Live SL/TP proximity check on open picks | 📲 Position alerts (only when triggered) |
| `news_engine.yml` | every 30 min, 8-23 Mon-Fri | Fetch + classify news → update watchlist | (silent — feeds picks/intraday) |
| `weekend_reflection.yml` | Sat 00:00 | LLM-graded weekly review | 📲 Weekend report |
| `weekly_report.yml` | Sat 01:00 | Quantitative weekly report card | (issue only) |
| `hypothesis_weekly.yml` | Sun 15:00 | Hypothesis-engine significance tests | 📲 Hypothesis findings |
| `monthly_xray.yml` | 1st of month, 22:00 | Deep monthly X-ray | 📲 Monthly summary |
| `backup.yml` | daily 23:00 | GitHub release backup of `data/` | (silent) |
| `watchdog.yml` | 13:35 & 14:35 Mon-Fri | Alert if morning picks didn't run | 📲 Watchdog alert (only on failure) |
| `ci.yml` | every push | pytest + smoke tests | (PR status only) |

---

## 4. The 4 Live Pipelines

### Pipeline A — Daily Picks (the morning run)

12:30 UTC trigger ↓ .github/workflows/daily-picks.yml ├─ DST + dedup guard ├─ pip install ├─ pytest (gate: tests must pass) ├─ scripts/build_stock_stats.py [Pillar 1 brain coverage] ├─ main.py [THE PICK ENGINE] │ └─ src/parallel_scorer.py │ ├─ data_fetcher.fetch_ohlcv() │ ├─ indicators.add_indicators() │ ├─ fundamentals.score_fundamentals() │ ├─ news_sentiment.score_sentiment() │ ├─ scorer.composite_score() ← weights from config │ ├─ watchlist_manager.watchlist_score_boost() │ ├─ day_trading_scorer.day_trading_score() │ ├─ market_guard.classify_with_day_score() │ ├─ risk_manager.atr_trade_plan() │ ├─ monster_hunt.score_monster() │ ├─ wisdom_consultant.consult_before_pick() [Pillar 2] │ ├─ signal_journal.build_signals() │ └─ writes picks_log.csv ├─ scripts/premarket_check.py [Pillar 5 sanity gate] ├─ scripts/format_picks_email.py └─ scripts/send_telegram.py [→ user via Telegram]

Code

### Pipeline B — Evening Evaluation

22:00 UTC trigger ↓ .github/workflows/evaluate.yml ├─ scripts/evaluate_picks.py │ ├─ pick_evaluator.evaluate() │ │ └─ data_fetcher.fetch_ohlcv() [intraday bars] │ └─ writes outcome columns to picks_log.csv │ └─ signal_journal.attach_outcome() ├─ scripts/performance_dashboard.py → /tmp/dashboard.txt ├─ scripts/send_dashboard_telegram.py 📲 ├─ scripts/daily_execution_report.py [the 'X-ray'] ├─ scripts/send_exec_telegram.py 📲 ├─ scripts/send_position_alerts.py 📲 └─ scripts/daily_observation.py → observations.jsonl

Code

### Pipeline C — Weekend Sweep

Sat 00:00 UTC — weekend_reflection.yml ├─ scripts/weekend_reflection.py (Gemini-graded) └─ scripts/send_weekend_telegram.py 📲

Sat 01:00 UTC — weekly_report.yml └─ scripts/weekly_report_card.py (issue only — currently NOT sent to Telegram)

Sun 15:00 UTC — hypothesis_weekly.yml └─ scripts/run_hypothesis_review.py --send └─ hypothesis_engine.analyze() + format_report()

Code

### Pipeline D — Monthly

1st of month 22:00 UTC — monthly_xray.yml └─ scripts/monthly_xray.py ├─ self_awareness.monthly_calibration() [30/60/90d] └─ reports/monthly_xray_<date>.md └─ scripts/send_monthly_telegram.py 📲

Code

---

## 5. Integration Truth Table

This is the **honest** view of what's actually running in production vs what's just code on disk. Status legend:
- ✅ wired-in-prod
- ⚠ built-but-orphaned
- 🔴 missing entirely

| Pillar | Component | Status | Evidence / Gap |
|---|---|---|---|
| 1 | composite_score in parallel_scorer | ✅ | `parallel_scorer.py:35` |
| 1 | Probability engine v0.1 layers | ⚠ | Module exists; not called in `parallel_scorer._score_one()` directly |
| 1 | stock_stats nightly build | ✅ | `daily-picks.yml` "Build per-stock statistics" step |
| 1 | regime conditioning | ⚠ | `regime.market_regime()` exists, not always passed to scorer |
| 2 | wisdom_consultant pre-pick | ✅ | `parallel_scorer.py:18` import + call |
| 2 | wisdom_hint in Telegram | ✅ | `send_telegram.py` lines 32-33 |
| 2 | wisdom_coverage footer | ✅ | imported in `send_telegram.py:34` |
| 2.5 | book_ingest seeded lessons | ✅ | seed.yaml exists; lessons in wisdom_base |
| 2.5 | trigger_context (B4) on hints | ✅ | shipped T43 |
| **3** | **pattern_engine called nightly** | **🔴** | `scan_patterns.py` exists as CLI only — NO workflow runs it |
| **3** | **pattern_layer.pattern_multiplier in scoring** | **🔴** | Defined but **zero callers** in src/scripts |
| **3** | **auto_enable_disable scheduled** | **🔴** | Function exists, not invoked anywhere |
| 3 | pattern_stats aggregator scheduled | 🔴 | Function exists, no nightly job |
| 3.5 | weight_proposer scheduled | ⚠ | Only referenced in `weekend_reflection.py:94` (LLM prompt) — proposals never auto-generated |
| 4 | weight_applier scheduled | ⚠ | Only referenced in `weekly_review.py:273` (footer summary). Apply step not in any workflow |
| 4 | auto_promote scheduled | 🔴 | Module exists, no workflow runs it |
| 4 | hypothesis_engine | ✅ | `hypothesis_weekly.yml` runs `scripts/run_hypothesis_review.py --send` |
| 4 | learning_journal writes | ✅ | When called; but applier itself rarely called |
| 4 | lesson_gc scheduled | 🔴 | No workflow invokes it |
| 5 | auto_pause check before picks | ⚠ | `is_paused()` imported in `send_telegram.py` — but does it veto picks before they ship? Needs verification |
| 5 | self_awareness in weekly | ✅ | `weekly_review.py:299` |
| 5 | self_awareness in monthly_xray | ✅ | wired T45 |
| 6 | weekly_review formatted | ✅ | `weekly_report.yml` runs it |
| 6 | weekly_review SENT to Telegram | ⚠ | Workflow posts as issue only — no Telegram step |
| 6 | quarterly_report scheduled | 🔴 | Module exists, no cron job |
| 6 | yearly_report scheduled | 🔴 | Module exists, no cron job |
| 6 | WoW + per-sector P&L footers | ✅ | `weekly_review.py:310-317` |

### Honest summary

- **8+ confirmed integration gaps**, mostly in Pillar 3 (entire pattern engine is offline) and Pillar 4 (weight_applier + auto_promote + lesson_gc never auto-run).
- **Pillar 3 is the most painful gap:** we built 16 detectors + Layer 6 + auto-enable hook, all functional in tests, but in production the brain never sees their output. Picks don't currently benefit from pattern detection.
- **Pillar 4 is half-wired:** the proposer doesn't auto-generate proposals, and the applier doesn't auto-apply them. Today, both require manual CLI invocation.
- **Quarterly and yearly reports** are runnable but unscheduled.

---

## 6. Telegram Output Catalog (what users currently receive)

| When | Workflow | Script | Content |
|---|---|---|---|
| Mornings 8:30 AM ET | daily-picks | `send_telegram.py` | DAY trades + SWING trades sections, each with: ticker, score, day_score, entry/SL/TP, qty, R:R, hold horizon, wisdom hint, pattern hint, confidence band, watchlist 🔔 marker |
| Evenings 6 PM ET | evaluate | `send_dashboard_telegram.py` | Today's outcomes, win/loss tally, R-multiples |
| Evenings 6 PM ET | evaluate | `send_exec_telegram.py` | X-ray report: per-pick attribution, regime, sector, did-rules-match-or-violate |
| Every 30min | intraday | `send_intraday_telegram.py` | Position alerts: SL approach, TP approach |
| Every 30min | evaluate | `send_position_alerts.py` | Time-based reminders for open picks |
| Sat morning | weekend_reflection | `send_weekend_telegram.py` | LLM-graded weekend reflection |
| Sun afternoon | hypothesis_weekly | `run_hypothesis_review.py --send` | Statistical findings: which buckets are working / failing |
| 1st of month | monthly_xray | `send_monthly_telegram.py` | Deep monthly X-ray |

### What's MISSING from Telegram (Idea 4 prep)

- **No layman explanation.** Every message uses jargon: "score 0.74 | day_score 0.62 | R:R 2.5 | ATR-based SL". An amateur reads this as noise.
- **No "why this pick" plain-English summary.** Wisdom hint is one line; the user can't see *why* the brain liked it.
- **No daily P&L summary in plain English.** ("Today the agent went 3-2, made +$45 paper, vs SPY which was flat — slightly better than market.")
- **No weekly Telegram message that actually goes out** — `weekly_report_card.py` only posts as a GitHub issue, not Telegram.
- **No yearly Telegram report.**
- **No "what the brain learned this week" plain-English digest.**

---

## 7. Honest Gaps List (drives Idea 1 + Idea 4)

### Critical (block the brain from being self-improving)
1. 🔴 **Pillar 3 entirely offline in production** — 16 detectors + Layer 6 + stats aggregator + auto-enable hook all built, none scheduled or called by main.py
2. 🔴 **weight_applier never auto-runs** — proposals queue grows but is never applied
3. 🔴 **calibration / weight_proposer never auto-generates proposals**
4. 🔴 **auto_promote, lesson_gc, pattern_stats** — none scheduled
5. ⚠ **auto_pause may not veto picks** — needs verification in main.py

### Important (degrade output quality)
6. ⚠ **Probability engine v0.1 layers exist but inconsistently consumed** by parallel_scorer
7. 🔴 **No Telegram for weekly_report_card.py** (only GitHub issue)
8. 🔴 **Quarterly + yearly reports unscheduled**

### UX / amateur-user (drives Idea 4)
9. 🔴 No layman daily picks message
10. 🔴 No layman daily performance message
11. 🔴 No layman weekly report
12. 🔴 No layman monthly report
13. 🔴 No layman yearly report
14. 🔴 No "what the brain learned" plain-English digest

### Architecture / design
15. ⚠ Many modules carry implicit coupling via shared CSV columns — schema not formally documented
16. ⚠ No single config file enumerating which features are ON / OFF in production
17. ⚠ No central "nightly conductor" workflow that runs all the brain-maintenance tasks in correct order

---

## 8. Data Files & Their Roles

| File | Producer | Consumer | Purpose |
|---|---|---|---|
| `data/picks_log.csv` | main.py | almost everyone | Source of truth for picks + outcomes |
| `data/signal_journal.jsonl` | main.py + evaluator | weekly/hypothesis | Per-pick signal snapshot + outcome |
| `data/weight_proposals.jsonl` | weight_proposer | weight_applier | Queue of proposed weight changes |
| `data/weight_history.jsonl` | weight_applier | weekly footer | Audit trail of applied changes |
| `data/learning_journal.jsonl` | weight_applier + auto_promote | weekly footer | Every brain mutation in one log |
| `data/pause_state.json` | auto_pause | scoring + telegram | What's currently paused |
| `data/exec_report_<date>.json` | daily_execution_report | observation logger | Per-day X-ray |
| `data/pattern_stats.json` | pattern_stats (would-be) | pattern_layer | Pattern × regime edge table |
| `data/patterns.jsonl` | pattern_engine (would-be) | pattern_stats | Detected patterns log |
| `data/watchlist.json` | news_engine | scoring + telegram | Bullish-news watchlist |
| `data/news_log.jsonl` | news_engine | news_signals | Raw news capture |
| `data/metrics_history.jsonl` | tracker | reports | Daily metric snapshots |
| `config/seed.yaml` | hand-curated | book_ingest | 50 book lessons (B1-B6) |
| `config/weights.json` | weight_applier | scorer | Brain-controlled multipliers |
| `config/auto_pause.json` | hand-curated | auto_pause | Pause thresholds + enforce flag |

---

## 9. The Master Pick Decision (how a stock gets picked, in 13 steps)

parallel_scorer iterates universe
fetch_ohlcv() loads price history
add_indicators() computes RSI/MACD/EMA/ATR/Bollinger
passes_filters() vetoes if penny stock / low volume / bad fundamentals
score_fundamentals() → fund_score (P/E, growth, margins)
fetch_news() + score_sentiment() → sent_score
composite_score() weighted sum of: trend, momentum, volatility, volume, fundamentals, sentiment, indicators
watchlist_score_boost() adds bullish-news bonus
day_trading_score() computed separately
classify_with_day_score() decides DAY vs SWING
atr_trade_plan() sets entry/SL/TP/qty by ATR
monster_hunt scoring (additive, optional)
wisdom_consultant.consult_before_pick() — final sanity check (lessons that say "don't take this" can veto)
THEN top picks ranked → top N selected → written to picks_log.csv

⚠ Pillar 3 (pattern_layer) currently NOT applied here — should be step 7.5 ⚠ Pillar 5 (auto_pause) check happens in send_telegram, not in scorer

Code

---

## 10. What's Next

**Stage A — Close integration gaps (makes brain actually self-improving):**
1. Wire `pattern_layer.pattern_multiplier()` into `parallel_scorer._score_one()`
2. Build a single nightly conductor workflow that runs in order:
   - calibration → weight_proposer → weight_applier
   - auto_promote → lesson_gc
   - pattern_engine universe scan → pattern_stats → auto_enable_disable
3. Verify auto_pause vetoes picks before they reach Telegram

**Stage B — Layman Telegram messages (Idea 4):**
4. New `scripts/send_layman_daily.py` — plain English daily picks
5. New `scripts/send_layman_evening.py` — plain English performance recap
6. Layman version of weekly/monthly/yearly summaries
7. New Telegram message: "what the brain learned this week"

**Stage C — Self-Improvement Loop "Meta-Brain" (Idea 1):**
8. New `src/meta_brain.py` that:
   - Reads recent journal events
   - Summarizes self-improvements made
   - Flags areas where the brain is stuck
   - Suggests new hypotheses to test
   - Sends weekly "self-improvement digest" to Telegram

---

## 11. Glossary (for amateur readers)

- **R-multiple:** Profit/loss expressed as multiples of risk. +2R = won 2× what was risked.
- **ATR:** Average True Range — volatility measure used to set SL/TP.
- **Composite score:** 0.0-1.0 quality score combining 7 signals.
- **DAY trade:** Entered + exited same day (≤4h hold).
- **SWING trade:** Held overnight, days to weeks.
- **Regime:** Market state (bull/bear/transition/unknown).
- **Wisdom lesson:** A trading rule promoted from book or backtest evidence.
- **Kill list:** Patterns/setups proven to lose money (auto-vetoed).
- **Auto-pause:** Freezes a tag/regime when its rolling stats degrade.
- **Calibration:** Comparing forecast probability to actual win rate.
- **Hypothesis test:** Statistical check for "is this edge real or noise?"

---

_Last updated: 2026-05-03. Verified by recon evidence in `docs/SPRINT_2026-05-03.md`._
