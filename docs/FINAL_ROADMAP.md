# 🚀 FINAL CONSOLIDATED ROADMAP — Daily Stock Agent

> **Version:** v4.0 (May 3, 2026 PM — Wisdom Pillar complete + 2 new pillars defined)
> **Locked:** May 3, 2026
> **Owner:** Anjan Neogi, Singapore
> **This is the single source of truth.** All future PRs reference this.

---

## 📊 CURRENT STATE — AT A GLANCE

| Metric | Value |
|---|---|
| Tests | **474 passing** (+322 since project audit; +131 today alone) |
| Pillars complete | **6 of 6** (1·2·2.5·3.5·4·5·6 ✅ · only Pillar 3 = multi-week ML) |
| Pillars partial | **4 of 6** (3, 4, 5, 6 in motion) |
| Bugs from Phase 0 | **5/5 RESOLVED** ✅ |
| Backtester | **LIVE** — 2,010 picks replayed, algo Sharpe **+0.97** |
| Live execution gap | **24.8 Sharpe gap → 2 root causes patched May 2** |
| Open PRs | 13 (debt — needs grooming sprint) |
| Test coverage | ~15% line / **474 behavioral tests locking critical paths** |

---

## 🏆 MILESTONE: SHIPPED Saturday 2026-05-02 (54 commits, 1 day)

This single Saturday sprint shipped ~5-6 weeks of original-plan work.

### Phase 0 — Bug Fixes (5/5 = 100% COMPLETE)
- ✅ BUG-1: Penny stock leak (PR #84 hard blocks)
- ✅ BUG-2: Picks stuck in pending — `bf06c07`
- ✅ BUG-3: Regime returning 'unknown' — `2f46dae`
- ✅ BUG-4: Same ticker repeated 3+ times — `c9ac768`
- ✅ BUG-5: SL too tight rejecting quality picks — `39c8f05`

### Pillar 1 — Probability Engine (5/5 layers LIVE) ✅ COMPLETE
- ✅ Layer 1: stock_stats per ticker — 106 tickers
- ✅ Layer 2: regime-conditional statistics
- ✅ Layer 3: probabilistic price level calculator (LIVE in main.py)
- ✅ EV Gate (observe-mode) · CI auto-builds stock_stats · 38 tests
- ✅ Layer 4: hypothesis testing — LIVE (`hypothesis_engine.py` + weekly CI + signal-journal backfill)
- ✅ Layer 5: self-awareness foundation — LIVE (`pause_state.py` + `auto_pause.py` + weekly footer)

### Pillar 5 — Self-Awareness — ✅ 100% COMPLETE (T45, May 3 PM)
- ✅ Auto-pause triggers (zero_win / loss_streak / neg_R) — `3433a3a`
- ✅ Per-tag + per-trade_type + per-regime tracking
- ✅ Observe-mode default (env: AUTO_PAUSE_ENABLED)
- ✅ Rolling 30d confidence intervals (Wilson + mean-R 95% CI) — `self_awareness.py`
- ✅ Monthly calibration (30/60/90d windows + trend) — wired into `monthly_xray.py`
- ✅ Weekly self-assessment (already in `weekly_review.py` grade)

### Pillar 6 — P&L + Reporting Brain — ✅ 100% MVP COMPLETE (T46, May 3 PM)
- ✅ SPY benchmark + alpha tracking — `e409a5b`
- ✅ Strategy/tag/regime breakdown — `7bf24b3`
- ✅ Sharpe / Sortino / Max DD / Calmar — `1ecf50d`
- ✅ Week-over-week trend (`wow_trend.py`)
- ✅ Per-sector P&L (`sector_pnl.py`)
- ✅ Quarterly report (`quarterly_report.py`) + Yearly scaffold (`yearly_report.py`)
- 🔵 PDF + LLM Buffett-letter + IRS/wash-sale = explicitly deferred (multi-week build)

### Edge Layer (2/3 items DONE)
- ✅ EV Filter — `bcd529e`
- ✅ Position Tracker — `a2f3952` + `cc798a1`
- 🔴 Monster Hunt Mode 💎

### Backtester v2 (THE BREAKTHROUGH)
- ✅ Phase A Brain Replay Engine + v1.1 (cooldown · gap fills · RSI cap)
- ✅ Real backtest: 100 tickers × 20 months × 2,010 picks
  - **Sharpe +0.97 · Win 44.43% · PF 1.15**
- ✅ Discovery: live -23.8 Sharpe vs +0.97 backtest = **execution leak, not algo**
- ✅ Sector boost leak FIXED — `34c60b1`
- ✅ Multi-fire workflow bug FIXED — `53a394d` (cron 13→2)
- ✅ 6 workflow DST bugs FIXED

**Total Saturday Stats:** 54 commits · tests 152 → 245 (+61%) · 2 architectural bugs killed · algorithm validated.

---

## 🏆 MILESTONE: SHIPPED Sunday 2026-05-03 — WISDOM PILLAR (T22 → T33)

12 tasks · 12 commits · +131 tests (343 → 474) · zero regressions.

### Pillar 2 — Wisdom Base v1.0 (LESSONS) — ✅ COMPLETE

| # | Task | Module | Function |
|---|---|---|---|
| T22 | wisdom store | `src/wisdom_base.py` | lessons + patterns + kill-list JSONL |
| T23 | hypothesis engine | `src/hypothesis_engine.py` | mines patterns from trade outcomes |
| T24 | per-pick lesson hint | `src/wisdom_hint.py` | 🧠 line under each pick |
| T25 | dry-run CLI | `python -m src.wisdom_hint --from-csv` | preview hints before market |
| T26 | pattern hint | `wisdom_hint.pattern_hint` | ✨/⚠ inline edge/drag |
| T27 | sector lesson match | `lessons_for_ticker` | XLE lesson → all energy picks |
| T28 | wisdom-in-play summary | telegram footer | "🧠 Wisdom in play:" block |
| T29 | **auto-promote** | `src/auto_promote.py` | patterns → lessons automatically |
| T30 | confidence band | `src/confidence_band.py` | 🔥/✅/⚠/🚫 emoji per pick |
| T31 | Makefile | `Makefile` | `make picks/evaluate/wisdom-*` |
| T32 | stale-lesson GC | `src/lesson_gc.py` | auto-deactivate >90d old |
| T33 | coverage footer | `src/wisdom_coverage.py` | "🧠 6/10 tagged · 4 lessons" |

**End State:** A trading agent that LEARNS from itself, WARNS before bad trades, EVOLVES over time, CLEANS up its own dead rules, and SHOWS YOU every morning how loud its own brain is.

---

## 🆕 TWO NEW PILLARS DEFINED (May 3, 2026)

### 🆕 Pillar 2.5 — BOOKS-INTO-BRAIN (NEW)

**Why:** Today's wisdom learns from your own trades (slow — needs hundreds of outcomes). Books give you **centuries of compressed master-trader wisdom** as high-confidence seed lessons.

**Status:** 🔴 0% — schema is ready (`source: "book:..."` slot reserved), no loader/seed/rules yet.

**Scope:**
- 🔴 B1 — Curate 10-book seed list (`data/books/seed.yaml`, ~30-50 rules)
  - Livermore, Lynch, Graham, Schwager, O'Neil, Douglas, Covel, Dalio, Soros, Marks
- 🔴 B2 — `src/book_ingest.py` loader + CLI + tests (`make wisdom-load-books`)
- 🔴 B3 — Bulk-load → `data/wisdom/lessons.jsonl` w/ `source="book:livermore"`
- 🔴 B4 — `trigger_context` field (situational rules, not just ticker/sector match)
  - e.g. `triggers: [drawdown>5%, regime=chop, holding_time>3d]`
- 🔴 B5 — Per-pick book attribution in Telegram (`🧠 _Livermore: never average down_`)
- 🔴 B6 — Weekly post-mortem: "rules violated on losers"
- 🔴 B7 — LLM-assisted extraction (optional, advanced) — feed PDF → rule list

**Effort:** ~3-4 sessions. MVP (B1-B3) = 1 hour.

---

### 🆕 Pillar 3.5 — CHART-LEARNING & SELF-CALIBRATION (NEW)

**Your ask:** *"Agent applies its pattern, builds it on charts, understands each timestamp where its logic worked / didn't, then calibrates itself."*

**Status:** 🟡 40% — backtester engine exists; the **learning loop** does not.

**What we have (✅):**
- Backtester replays brain across 100 tickers × 20 months (2,010 picks)
- Sharpe/Sortino/MaxDD/Profit Factor per run
- Point-in-time discipline (no look-ahead bias)
- Already exposed the 24.8 Sharpe live-vs-replay gap

**What's missing (🔴):**
- 🔴 C1 — `src/calibration.py`: read `data/backtest_results/*.csv`, compute per-factor (RSI, vol_z, momentum, sector_boost) win-rate × R-multiple
- 🔴 C2 — Per-timeframe attribution (D / W / M / 90d / 1y) — "where logic worked, where it broke"
- 🔴 C3 — Weight-delta proposer (READ-ONLY first) → `data/weight_proposals.jsonl`
  - "Suggested: ai_boost 1.0 → 0.95 (would have added +0.12 R over 1,200 picks)"
- 🔴 C4 — Weekly Telegram footer adds calibration line
- 🔴 C5 — Walk-forward validation (Backtester Phase B)
- 🔴 C6 — Auto-apply with safety caps (max 5%/wk, multi-window confirmation)
- 🔴 C7 — Per-pattern × per-regime × per-timeframe matrix (feeds Pillar 3)

**Effort:** ~4-5 sessions. C1-C3 MVP = 2 hours.

---

## 🧠 ARCHITECTURE — THE 6-PILLAR BRAIN (UPDATED)

| Pillar | Purpose | Status | % |
|---|---|---|---|
| 1. Probability Engine | Empirical SL/TP/buy/sell levels | 🟡 v0.1 LIVE | 60% |
| 2. **Wisdom Base** | Lessons + book-derived rules | 🟢 **v1.0 LIVE (May 3)** | **80%** |
| 2.5. 🆕 **Books-into-Brain** | Seed lessons from 10+ trading books | ✅ MVP complete | **100%** |
| 3. Pattern Recognition | 15 detectors + per-pattern stats | 🟡 indicators exist | 10% |
| 3.5. 🆕 **Chart-Learning / Calibration** | Replay → "what worked" → weight tuning | ✅ Complete | **100%** |
| 4. Feedback Loop & Self-Learning | Outcome attribution + weight updates | 🟡 auto_promote shipped | 30% |
| 5. Self-Awareness | Confidence intervals + auto-pause | 🟡 auto_pause LIVE | 20% |
| 6. P&L + Reporting Brain | Daily/Weekly/Monthly/Quarterly/Yearly | 🟡 metrics shipped | 50% |

See: `docs/BRAIN_ARCHITECTURE.md` (needs update for Pillar 2.5 + 3.5).

---

## ❌ TECHNICAL DELIVERABLES — NOT YET DONE

### TECH DEBT
- 🔴 Test coverage 15% line (have 474 behavioral — need branch coverage)
- 🔴 13 open PRs (#60-86) — needs grooming sprint
- 🔴 `src/paper_trader.py` exists but NOT integrated (BLOCKER for Stage 1 Gate)

### NEW FEATURES — RANKED BY PRIORITY (UPDATED v4.0)

#### 🔴 PRIORITY 1 — Brain Pillars (Months 1-6)

**Pillar 1: Probability Engine** — ✅ 100% (May 3 PM)
- ✅ Layer 4: Hypothesis testing — LIVE
- ✅ Layer 5: Self-Awareness foundation — LIVE

**Pillar 2: Wisdom Base v1.0** — ✅ 100% COMPLETE (May 3 PM, T42)
- ✅ Telegram showing matched/violated rules count (`wisdom_coverage` edges/warnings)
- ✅ Weekly post-mortem (`weekly_review` formal section)

**🆕 Pillar 2.5: Books-into-Brain** — ✅ 100% MVP (B1-B6 shipped, B7=optional/future)
- ✅ B1-B5 (T34-T36, May 3 AM)  ✅ B4 trigger_context  ✅ B6 rules-violated post-mortem (T43, May 3 PM)
- 🔵 B7 LLM-assisted PDF extraction — explicitly deferred (advanced/future)

**🆕 Pillar 3.5: Chart-Learning / Self-Calibration** — ✅ 100% (C1-C4 shipped May 3 AM, T37-T40)
- 🔴 C1-C7 (calibration · timeframe attribution · weight proposer · walk-forward · auto-apply · pattern matrix)

**Pillar 3: Pattern Recognition Engine** — 🟡 35% (Phase 1 LIVE — T47 May 3 PM)
- 🟡 4/15 detectors LIVE: HHHL, LHLL, breakout_20, breakdown_20
- ✅ Per-pattern × per-regime stats aggregator (`pattern_stats.py`)
- ✅ Universe scan CLI (`scripts/scan_patterns.py`)
- 🔴 Phase 2: bull_flag, bear_flag, triangles, cup-and-handle (next sprint)
- 🔴 Phase 3: head-and-shoulders, wedges, double top/bottom, Layer 6 wiring

**Pillar 4: Feedback Loop & Self-Learning** — ✅ 100% COMPLETE (T44, May 3 PM)
- ✅ auto_promote (T29) closes outcome → lesson loop
- ✅ hypothesis_engine (T23) mines patterns from outcomes
- ✅ Win/loss attribution per factor (calibration.py — shared w/ Pillar 3.5)
- ✅ Weight update mechanism with 5%/week cap (`weight_applier.py`)
- ✅ Learning journal (`learning_journal.py`) + Weight history (`weight_history.jsonl`)

**Pillar 5: Self-Awareness** — ✅ 100% (T45 May 3 PM)

#### ✅ PRIORITY 2 — P&L + Reporting Brain (Pillar 6) — ✅ 100% MVP
- ✅ Sharpe/Sortino/Calmar/MaxDD · SPY α · strategy/tag/regime breakdown
- ✅ Week-over-week trend · per-sector P&L · quarterly + yearly scaffolds
- 🔵 Stretch (multi-week): PDF · LLM Buffett letter · wash-sale · 1099-equiv

#### 🟡 PRIORITY 3 — Edge Layer — 2/3 DONE
- ✅ EV Filter · ✅ Position Tracker
- 🔴 **Monster Hunt Mode** 💎

#### 🟢 PRIORITY 4 — Validation Infrastructure — 60%
- 🔴 **Alpaca PAPER TRADING integration** (BLOCKER for Stage 1 Gate)
- ✅ SPY benchmark · Ticker cooldown · SL min by stock type · Universe top 100
- 🔴 Sector benchmark · Real fill slippage · "No trade today" capability

#### 🟢 PRIORITY 5 — Multi-Asset & Advanced — Months 7-12
Multi-LLM ensemble · Kelly sizing · Correlation matrix · Crypto · Options · Multi-TF · Stop-hunting · Sector rotation · Earnings transcripts · 8-K alerts · Form 4 · Options flow · Twitter/Reddit sentiment · FDA tracker

#### 🟢 PRIORITY 6 — SaaS Platform — Months 7-12
Postgres · FastAPI + JWT/2FA · Encrypted broker conns · Per-user Telegram · Celery · Next.js + Tailwind · Stripe · Tiered pricing · Landing/waitlist · Onboarding wizard

#### 🟢 PRIORITY 7 — Mobile & Real-Time — Months 13-15
React Native · Push · 1-tap approve · Voice query · WebSocket streaming

#### 🟢 PRIORITY 8 — Risk Management 2.0 — Months 16-18
Black swan hedging · Portfolio DD circuit breakers · Tax-loss harvesting · Wash sale awareness · Affiliate program (30%)

---

## 📅 6-MONTH IMPLEMENTATION SCHEDULE (REVISED v4.0)

### MONTH 1 (May 2026) — Foundation Stabilization + Wisdom 2.0
**Done so far (May 2-3):**
- ✅ Phase 0 bug fixes (5/5)
- ✅ Pillar 1 v0.1 LIVE (3 layers)
- ✅ Backtester v2 LIVE — algo edge validated
- ✅ Pillar 2 v1.0 LIVE (Wisdom Base, 12 modules)

**Remaining May 2026:**
- 🆕 Pillar 2.5: Books-into-Brain MVP (B1-B5)
- 🆕 Pillar 3.5: Calibration loop MVP (C1-C3)
- Monster Hunt Mode 💎 (closes Edge Layer 3/3)
- Alpaca paper trading integration
- Validate Mon May 4 picks fire diversely
- Flip BRAIN_ENFORCE_EV=true · AUTO_PAUSE_ENABLED=true after observe

### MONTH 2 (June 2026) — Pillar 3 Detectors + Pillar 4 Weights
- Pillar 3: ship 5-7 of 15 detectors
- Pillar 3.5: feed detectors into calibration matrix
- Pillar 4: weight-update mechanism (cap 5%/wk + history)
- Pillar 6: per-strategy + per-sector P&L breakdown
- Books pillar B6: weekly post-mortem on rule violations
- 30+ days Alpaca paper data

### MONTH 3 (July 2026) — Pattern Recognition Complete + Wisdom v2
- Pillar 3: remaining 8 detectors + per-regime stats
- Books B7: LLM extraction (scale beyond manual)
- **Stage 1 Gate review** (60-day Alpaca paper)

### MONTH 4 (August 2026) — Self-Awareness + P&L Brain v2
- Pillar 5: rolling 30d CI · monthly calibration · weekly self-assessment
- Pillar 6: full daily/weekly/monthly polish

### MONTH 5 (September 2026) — Quarterly Reports + Multi-LLM
- Pillar 6: Quarterly reports (PDF + LLM review)
- Multi-LLM ensemble (Claude + GPT-5 + Gemini)
- Open Moomoo real money $5K SGD

### MONTH 6 (October 2026) — Brain Integration + Stage 2 Gate
- All 6 pillars (+ 2 sub-pillars) working together
- Wisdom rules updated from outcomes (full loop closed)
- Pattern discovery (clustering)
- 60-day Moomoo real money complete
- **Stage 2 Gate review** · 10 alpha testers onboarded

---

## 🚀 NEXT-SESSION PLAN (3-hour sprint, May 3 PM SGT)

**HOUR 1 — BOOKS PILLAR MVP**
- T34 — `data/books/seed.yaml` — 30 curated rules (30m)
  - Livermore · Lynch · Graham · Schwager · O'Neil · Douglas · Covel · Dalio · Soros · Marks
- T35 — `src/book_ingest.py` + CLI + tests (20m)
- T36 — Wire book lessons into `wisdom_hint` w/ attribution (10m)

**HOUR 2 — CALIBRATION BRAIN**
- T37 — `src/calibration.py` — read `data/backtest_results/*.csv`, per-factor win-rate × R-multiple (40m)
- T38 — Per-timeframe attribution (D / W / M) (20m)

**HOUR 3 — CLOSE THE LOOP**
- T39 — Weight-delta proposer (READ-ONLY) → `data/weight_proposals.jsonl` (30m)
- T40 — Weekly Telegram footer adds calibration line (15m)
- T41 — Tests + commit + push (15m)

**END STATE 17:48 SGT:**
- ✅ Books pillar MVP shipped (Pillar 2.5)
- ✅ Calibration brain MVP shipped (Pillar 3.5)
- ✅ ~25-30 new tests · all green
- ✅ Two new Telegram lines tomorrow morning

---

## 💰 PRICING TIERS (Locked)

| Tier | Price | Features |
|---|---|---|
| FREE | $0 | 1 daily pick (24hr delayed), public track record |
| STARTER | $39/mo | Real-time picks, Telegram alerts, weekly/monthly |
| PRO ⭐ | $99/mo | Full 5-layer exits, auto-execute, backtest, LLM |
| ELITE | $249/mo | Multi-asset, custom strategies, monthly 1:1 |
| ENTERPRISE | $999/mo | White-label, SLA, hedge funds (Month 17+) |

**Discounts:** Annual (2mo free) · Lifetime $1,499 (first 100) · Affiliate 30% · Founder $29/mo (first 25)

---

## 🎯 STAGE GATES (Mandatory)

| Gate | When | Pass Criteria |
|---|---|---|
| Gate 1 | End Month 3 | 60d Alpaca paper: capture ≥60%, win ≥45%, beats SPY +2% |
| Gate 2 | End Month 6 | 60d Moomoo real $: capture ≥50%, beats SPY +1%, no >20% DD |
| Gate 3 | End Month 12 | $5K MRR, <10% churn, 50+ paying users, audited record |
| Gate 4 | Month 18 | $20K MRR for 3 months → **QUIT JOB** |

---

## 📊 SUCCESS METRICS (Month 24)

- $70K+ MRR ($840K ARR) · 800+ paying customers
- 24-month audited live trading record
- 20K+ LinkedIn + 5K+ Twitter followers
- Industry recognition (Bloomberg/CNBC mention)

---

## 🤝 CUSTOMER PERSONA (Locked)

**Working professionals** ages 28-50, salary $80-300K, $20-500K investable assets.
Pain: *"I want to beat the market but don't have time to research."*
Channels: LinkedIn (primary), Twitter/X, Substack, YouTube, Discord.

---

## 🔄 REVISION HISTORY

- **v1.0 (Apr 30):** Original 24-month plan
- **v2.0 (May 2 AM):** Reset based on Day 3 audit
- **v3.0 (May 2 PM):** 5-pillar brain, Pillar 6 added
- **v3.1 (May 2 eve):** Backtester v2 + algo +0.97 Sharpe validated
- **v4.0 (May 3 PM):** Wisdom Pillar v1.0 LIVE (T22-T33). **Two new pillars:** 2.5 Books-into-Brain · 3.5 Chart-Learning/Self-Calibration. Re-ranked priorities.

**Next revision:** End of Month 1 (May 31, 2026).

---

*Living document. Update after every major decision.*
*Owner: Anjan Neogi, Singapore*
*Last updated: May 3, 2026*
