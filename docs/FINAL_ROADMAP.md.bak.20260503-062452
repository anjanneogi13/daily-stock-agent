# 🚀 FINAL CONSOLIDATED ROADMAP — Daily Stock Agent

## 🏆 MILESTONE: SHIPPED Saturday 2026-05-02 (54 commits, 1 day)

This single Saturday sprint shipped ~5-6 weeks of original-plan work.
All items below were 🔴 Not Started at the start of this day.

### Phase 0 — Bug Fixes (5/5 = 100% COMPLETE)
- ✅ BUG-1: Penny stock leak (PR #84 hard blocks) — pre-existing
- ✅ BUG-2: Picks stuck in pending — `bf06c07` (off-by-one in evaluator)
- ✅ BUG-3: Regime returning 'unknown' — `2f46dae` (retry+fallback+cache)
- ✅ BUG-4: Same ticker repeated 3+ times — `c9ac768` (ticker cooldown)
- ✅ BUG-5: SL too tight rejecting quality picks — `39c8f05` (tiered SL by price)

### Pillar 1 — Probability Engine (3/5 layers LIVE)
- ✅ Layer 1: stock_stats per ticker — `84f0d40`, expanded 20→106 tickers `860a134`
- ✅ Layer 2: regime-conditional statistics — `84f0d40`
- ✅ Layer 3: probabilistic price level calculator — `7c366df` (wired into main.py)
- ✅ EV Gate (Edge Layer + Pillar 1 integration) — `bcd529e` (observe-mode)
- ✅ CI auto-builds stock_stats every run — `11b6e36`
- ✅ 38 tests locking behavior — `5807c7d`
- 🔴 Layer 4: hypothesis testing engine — NEXT
- 🔴 Layer 5: self-awareness foundation

### Pillar 5 — Self-Awareness (FOUNDATION LIVE — 20%)
- ✅ Auto-pause triggers (zero_win / loss_streak / neg_R rules) — `3433a3a`
- ✅ Per-tag + per-trade_type + per-regime tracking — `3433a3a`
- ✅ Observe-mode default (env: AUTO_PAUSE_ENABLED) — mirror EV-gate pattern
- 🔴 Rolling 30d confidence intervals (groundwork done in risk_metrics)
- 🔴 Calibration check (monthly)
- 🔴 Telegram weekly self-assessment

### Pillar 6 — P&L + Reporting Brain (10% → 50%)
- ✅ SPY benchmark + alpha tracking on closed picks — `e409a5b`
- ✅ Strategy/tag/regime breakdown (win_rate, avg_R, total_R, alpha) — `7bf24b3`
- ✅ Sharpe ratio (per-trade + naive-annualized) — `1ecf50d`
- ✅ Sortino ratio (downside-only) — `1ecf50d`
- ✅ Max drawdown (chronological equity curve) — `1ecf50d`
- ✅ Calmar ratio (annualized return / |max DD|) — `1ecf50d`
- 🟡 Drawdown analysis — math shipped, needs 90d window for quarterly
- 🔴 Week-over-week trend
- 🔴 Per-sector P&L breakdown
- 🔴 Quarterly / Yearly reports

### Edge Layer (2/3 items DONE)
- ✅ EV Filter (was PR #70) — `bcd529e` (observe-mode)
- ✅ Position Tracker (was PR #72) — `a2f3952` + `cc798a1` (logic + Telegram + CI)
- 🔴 Monster Hunt Mode (was PR #71) — NEXT

### Validation Infrastructure (Priority 4)
- ✅ SPY benchmark column in picks_log — `e409a5b`
- ✅ Ticker cooldown (BUG-4 fix) — `c9ac768`
- ✅ SL min by stock type (BUG-5 fix) — `39c8f05`
- ✅ Universe top 100 — `860a134` (106 tickers, exceeds target)
- 🔴 Sector benchmark per pick
- 🔴 Alpaca paper trading integration

### Pillar 6 / Telegram Hardening
- ✅ Telegram MD→plain-text auto-fallback — `cd4d212`
- ✅ Telegram report dedup (no duplicate daily sends) — `5ebfde6` (PR #85)
- ✅ Position alerts dispatch + dedup (`scripts/send_position_alerts.py`)

### Live Diagnostics (DATA-VALIDATED on 9 closed picks)
| Metric | Value | Implication |
|---|---|---|
| Sharpe (annualized) | **-10.6** | Catastrophic — Wed EV flip is URGENT |
| Sortino (annualized) | **-6.02** | Downside dominant |
| Max drawdown | **-40.4%** | Capital protection critical |
| Calmar | **-6.84** | Risk/reward inverted |
| Win rate (swing) | **0/8** | All swing trades lost |
| Win rate (SEMI/AI tag) | **0/7** | Tag bleeding capital |
| Win rate (regime=unknown) | **0/6** | Validates BUG-3 fix urgency |

### Test Suite Growth
- Morning: 152 tests
- After BUG fixes & breakdown: 210 tests
- After Sharpe/Sortino: 221 tests
- After auto-pause: **232 tests** (+53% in one day)

### Documentation Infrastructure
- ✅ CONTEXT.md (single-source-of-truth) — `b754e2b`
- ✅ FINAL_ROADMAP.md v3.0 — `96b9693`
- ✅ 24-month master plan v2.0 — `0e8b841`
- ✅ ADR-001/002 (Probability Engine + brain architecture) — `b754e2b`
- ✅ Statistical Probability Engine design — `c9454e4`
- ✅ Daily backup system (749 files protected) — `77c4ab3` (PR #83)
- ✅ News intelligence engine — `036b23b` (PR #77)


### 🌙 EVENING SPRINT (16:00-22:30 UTC) — THE BREAKTHROUGH

After the afternoon's 44 commits, we kept going and discovered the live
performance gap was **not** an algo problem — it was a plumbing problem.

#### Backtester Build (Phases A + 1.1)
- ✅ **Backtester v2 Phase A** — Brain Replay Engine (10/10 tests pass) — `343b25c`
- ✅ **Backtester v1.1** — cooldown + gap fills + RSI cap (13 tests pass) — `a28fc61`
- ✅ **Real backtest validated** — 100 tickers × 20 months × 2,010 picks
  - Sharpe **+0.97** (annualized)
  - Win rate **44.43%**
  - Profit factor **1.15**
  - Sortino +1.24, Calmar workable

#### 🏆 THE BREAKTHROUGH DISCOVERY
| Metric | Backtest (algo) | Live (executed) | Gap |
|---|---|---|---|
| Win rate | **44.43%** | 11% | -33pp |
| Avg R | **+0.08** | -0.70 | -0.78R |
| Sharpe | **+0.97** | -23.8 | **-24.8** |
| Profit factor | **1.15** | 0.04 | -1.11 |

**Verdict:** The algorithm has real, validated edge. The 24.8 Sharpe gap
was caused by execution-layer bugs that bias picks toward losing clusters.

See: `docs/sessions/2026-05-02_BREAKTHROUGH.md`

#### Root-Cause Fixes Shipped Tonight
- ✅ **Sector boost leak FIXED** — `34c60b1`
  - `semi_boost: 1.1 → 1.0` and `ai_boost: 0.2 → 0.0`
  - Diagnostic proved 89.5%% of live picks were SEMI-tagged (100%% lost)
  - +30%% scoring head-start for SEMI/AI was forcing single-cluster bets
- ✅ **Multi-fire workflow bug FIXED** — `53a394d`
  - Cron entries reduced from 13 → 2 (primary EDT + primary EST)
  - Added early-exit guard in main.py (skip if today already logged)
  - Was firing 2-3x/day (Apr 28: 2 runs, May 1: 3 runs) → bypassing tag cap
  - Belt + suspenders defense in depth

#### Workflow Stability
- ✅ **6 workflow DST bugs FIXED** — daily-picks, weekly_report, weekend_reflection, +3 — `aa8685d`, `55c773f`

#### Test Suite
- Saturday morning: 152 tests
- Saturday afternoon: 232 tests
- Saturday evening: **245 tests** (+61%% in one day)

#### Data-Driven Insights from Backtester
**Top edges (universe focus):** PLTR +1.06R (88%% win), MDB +0.97R, NOW +0.87R, SNOW +0.83R, C +0.72R  
**Bottom losers (drop from universe):** UNH -1.35R, TEAM -1.0R, SMCI -0.94R, DIS -0.64R, SCHW -0.64R

#### Total Saturday Stats
- **54 commits** (44 afternoon + 10 evening)
- 2 architectural bugs killed (worth months of guess-work)
- 1 algorithm validated (changes everything about Phase 1 priorities)

---

### 🚨 IMMEDIATE NEXT-SESSION ACTIONS (UPDATED EVENING May 2)

**SUNDAY (May 3) — 15-min review only:**
1. Review Saturday's 54 commits (read-only, no changes)
2. Verify no overnight workflow failures

**MONDAY (May 4) — VALIDATION DAY (THE most important day):**
1. **8:30 AM ET** — Watch daily-picks fire ONCE (was 2-3x)
2. **9:00 AM ET** — Verify diverse picks in Telegram (NOT 5/5 SEMI)
3. If picks are diverse → tonight's fixes worked, proceed to Tue plan
4. If picks still concentrated → hunt 3rd bug before anything else

**TUE-THU (May 5-7) — IF MONDAY VALIDATES:**
5. Drop bottom-5 tickers from universe (UNH, TEAM, SMCI, DIS, SCHW)
6. Port cooldown logic from backtester to live system
7. **Wed May 6** — Flip `BRAIN_ENFORCE_EV=true` (data-justified)
8. **Wed May 6** — Flip `AUTO_PAUSE_ENABLED=true` after 2-3 days observe

**FRI-SAT (May 8-9) — Pillar 1 Layer 4:**
9. Pillar 1 Layer 4: hypothesis testing engine (now UNBLOCKED by backtester)
10. Backtester Phase B: walk-forward validation

**LATER:**
11. Monster Hunt Mode (closes Edge Layer 3/3)
12. Pillar 2 (Wisdom Base) — Week of May 10

---


> **Version:** FINAL v3.1 (May 2 evening: backtester v2 + breakthrough + 2 root-cause fixes)
> **Locked:** May 2, 2026
> **Owner:** Anjan Neogi, Singapore
> **This is the single source of truth.** All future PRs reference this.

---

## 🎯 NORTH STAR

**The world's only transparent, audited, AI-powered trading agent built for working professionals who want to invest in US stocks but lack time to research.**

Three differentiators no competitor has:
1. **5-Pillar Brain** (probability + wisdom + patterns + learning + self-awareness)
2. **Open source + audited public track record**
3. **Built BY a working professional FOR working professionals**

---

## 🧠 ARCHITECTURE — THE 5-PILLAR BRAIN

| Pillar | Purpose | Status |
|---|---|---|
| 1. Probability Engine | Empirical SL/TP/buy/sell levels | ✅ v0.1 LIVE (May 2) |
| 2. Wisdom Base | Encoded knowledge from 10+ trading books | 🔴 Not started |
| 3. Pattern Recognition | Numerical patterns scanned across universe | 🟡 Partial (indicators exist) |
| 4. Feedback Loop | Outcome-driven self-learning | 🔴 Not started |
| 5. Self-Awareness | Confidence intervals + auto-pause | 🔴 Not started |

**Plus a 6th supporting pillar (P&L Brain):**

| Pillar 6 | Purpose | Status |
|---|---|---|
| 6. P&L + Reporting Brain | Daily/Weekly/Monthly/Quarterly/Yearly performance analytics + tax reports | 🟡 Partial (basic logs exist) |

See: `docs/BRAIN_ARCHITECTURE.md` for full pillar 1-5 design.

---

## ✅ TECHNICAL DELIVERABLES — DONE

### Phase 1 — Foundation (DONE)
- ✅ Stock universe (S&P 500 + semis + custom)
- ✅ Multi-source data fetching (Yahoo, Alpaca News, Finnhub)
- ✅ Technical indicators (RSI, MACD, ATR, SMA, EMA, BB)
- ✅ Fundamental scoring
- ✅ Composite scoring (multi-factor weighted)
- ✅ Sector caps (max 2 picks per sector)
- ✅ DAY vs SWING classification
- ✅ ATR-based dynamic stops
- ✅ Position sizing by risk capital
- ✅ Picks logged to picks_log.csv

### Phase 2 — Intelligence (DONE)
- ✅ Market regime detection (bull/bear/transition)
- ✅ VIX-based position sizing
- ✅ SPY trend guards (50/200 DMA)
- ✅ Sector strength analysis
- ✅ Earnings calendar integration
- ✅ CAPE ratio macro filter
- ✅ Premarket gap check
- ✅ News engine (Alpaca + Yahoo RSS)
- ✅ Watchlist manager (3-day TTL)
- ✅ News classification (Claude Sonnet 4.5)
- ✅ Pick evaluation (next-day exit checking)
- ✅ R-multiple tracking
- ✅ 3-tier scale-out (TP1/TP2/TP3)
- ✅ Trailing stop engine
- ✅ Adaptive TP raise (RSI 70 + vol)
- ✅ Adaptive SL tighten (RSI fade)
- ✅ Capture efficiency metrics
- ✅ Telegram tier display

### Phase 3 — Reliability + Reports (DONE)
- ✅ 13 cron slots for morning runs (redundancy)
- ✅ External cron via cron-job.org (3 redundant triggers)
- ✅ Watchdog at 9:35 ET
- ✅ Backup system (daily, GitHub Releases, 30-day retention)
- ✅ Hard enforcement layer (penny stocks, SL min, sector caps)
- ✅ Telegram report dedup (no more 3-5x sends)
- ✅ Daily Telegram morning picks
- ✅ Daily exec X-ray report
- ✅ Weekly performance report card
- ✅ Monthly X-ray report
- ✅ Weekend reflection
- ✅ Intraday monitoring

### Phase 4 — Memory & Documentation (DONE TODAY)
- ✅ docs/CONTEXT.md (single source of truth)
- ✅ docs/ROADMAP.md (living doc)
- ✅ docs/MASTER_PLAN_24_MONTH_v2.md
- ✅ docs/BRAIN_ARCHITECTURE.md (5-pillar design)
- ✅ docs/PROBABILITY_ENGINE_DESIGN.md
- ✅ docs/decisions/ADR-001 (probability over rules)
- ✅ docs/decisions/ADR-002 (5-pillar brain)
- ✅ docs/playbook/CHAT_HANDOFF_PROTOCOL.md
- ✅ docs/SPRINT_2026-05-02_TO_MONDAY.md
- ✅ docs/sessions/2026-05-02-saturday-shipping.md
- ✅ docs/FINAL_ROADMAP.md (THIS FILE)

### Phase 5 — May 2 2026 Saturday Sprint (DONE TODAY)

**🧠 PILLAR 1 — Probability Engine v0.1 LIVE in PRODUCTION:**
- ✅ src/stock_stats.py (per-stock empirical statistics, 20 tickers)
- ✅ scripts/build_stock_stats.py (universe builder)
- ✅ src/probability_engine.py (multi-signal decision brain)
  - Layer 1: Empirical price-history base rates
  - Layer 2: Market regime conditioning
  - Layer 3: News + sentiment posteriors
  - Layer 4: Catalyst (earnings) conditioning
  - Layer 4b: Watchlist signal integration
  - Layer 5: Multi-signal combiner (heuristic v0.1)
  - Layer 6: SL/TP/buy/trigger price decisions
- ✅ tests/test_probability_engine.py — 38 tests
- ✅ Wired into main.py production pipeline (additive, zero risk)
- ✅ picks_log.csv now includes brain_p_win, brain_ev_pct, brain_sl, brain_tp, brain_confidence
- ✅ VERIFIED LIVE in production workflow run (cd4d212)

**Bug Fixes Shipped:**
- ✅ BUG-4: ticker cooldown (5 days, hard_blocks.py)
- ✅ BUG-5: tiered SL minimums by price ($100+: 1.5%, $30-99: 2%, etc.)

**Production Hardening:**
- ✅ Telegram Markdown→plain-text auto-fallback (HTTP 400 fix, cd4d212)
- ✅ Workflow now resilient to stock names with special chars

**Tests & Quality:**
- ✅ Test coverage: 152 → 190 tests (+25%)
- ✅ Zero regressions across 12 commits in single afternoon

**Honest v0.1 Limitations (next sprints):**
- 🟡 Stats only for 20 tickers (need top 100+) — Sunday task
- 🟡 Combiner heuristic, not full Bayesian — v0.2
- 🟡 EV calculated but NOT enforced as filter yet — Sunday task
- 🟡 Adjustment weights are PRIORS, not learned — needs Pillar 4
- 🟡 Brain output ADDITIVE — old SL/TP still primary in Telegram


---

## ❌ TECHNICAL DELIVERABLES — NOT YET DONE

### KNOWN BUGS (Phase 0 — Fix First)
- ✅ ~~BUG-1: Penny stock leak~~ → RESOLVED (PR #84 hard blocks working)
- ✅ BUG-2: Picks stuck in "pending" → RESOLVED (May 2, off-by-one in evaluator)
- ✅ BUG-3: Regime "unknown" → RESOLVED (May 2, retry+fallback+cache)  
- ✅ ~~BUG-4: Ticker cooldown~~ → RESOLVED (5-day cooldown in hard_blocks.py, May 2)
- ✅ ~~BUG-5: SL too tight rejection~~ → RESOLVED (tiered SL mins by price, May 2)

### TECH DEBT
- 🔴 Test coverage 15% (need 40%+)
- 🔴 13 open PRs (#60-86) creating merge debt
- 🔴 src/paper_trader.py exists but NOT integrated

### NEW FEATURES — RANKED BY PRIORITY

#### 🔴 PRIORITY 1 — Brain Pillars (Months 1-6)

**Pillar 1: Probability Engine** — 🟡 v0.1 LIVE in production (May 2 2026)
- ✅ Layer 1: stock_stats per ticker (20 tickers shipped, expand to 100+ Sunday)
- ✅ Layer 2: Regime-conditional statistics (heuristic in SignalState)
- ✅ Layer 3: Probabilistic price level calculator (LIVE in main.py)
- 🔴 Layer 4: Hypothesis testing engine (v0.2 — needs Pillar 4 outcomes)
- 🔴 Layer 5: Self-Awareness foundation (overlaps with Pillar 5)

**Pillar 2: Wisdom Base** (1-week build)
- 🔴 Curate 10-book list
- 🔴 LLM extraction script (~$10 one-time)
- 🔴 wisdom_base.json generation
- 🔴 Per-pick wisdom check integration
- 🔴 Telegram showing matched/violated rules
- 🔴 Weekly post-mortem (which rules violated on losses)

**Pillar 3: Pattern Recognition Engine** (2-week build)
- 🔴 15 pattern detectors (HHHL, bull flag, ascending triangle, etc.)
- 🔴 Per-pattern statistics tracking
- 🔴 Per-regime pattern performance
- 🔴 Hypothesis testing per pattern (auto-enable/disable)
- 🔴 Universe-wide daily scan

**Pillar 4: Feedback Loop & Self-Learning** (2-week build)
- 🔴 Win/loss attribution per factor
- 🔴 Weight update mechanism (max 5%/week)
- 🔴 Learning journal (data/learning_journal.jsonl)
- 🔴 Weight history tracking
- 🔴 Rule discovery from data
- 🔴 Wisdom base updated from outcomes

**Pillar 5: Self-Awareness** (1-week build)
- 🔴 Rolling 30-day confidence intervals
- ✅ Per-strategy + per-regime tracking — May 2 (auto_pause supports any dimension)
- ✅ Auto-pause triggers (foundation) — May 2 auto_pause.py
- 🔴 Calibration check (monthly)
- 🔴 Telegram weekly self-assessment

#### 🟡 PRIORITY 2 — P&L + Reporting Brain (Pillar 6) — 2 weeks

**Daily reports:**
- 🟡 Daily P&L (per pick + portfolio)
- 🟡 Daily slippage analysis
- 🟡 Daily vs SPY benchmark
- 🟡 Daily attribution (which factor drove gains/losses)

**Weekly reports:** (partial done)
- ✅ Basic weekly performance report card
- 🔴 Week-over-week trend
- ✅ Win rate by strategy (day/swing/multi) — May 2 strategy_breakdown.py
- ✅ Sharpe ratio calculation — May 2 risk_metrics.py

**Monthly reports:** (partial done)
- ✅ Basic monthly X-ray
- 🔴 Per-strategy P&L breakdown
- 🔴 Per-sector P&L breakdown
- 🔴 Pattern performance summary
- 🔴 Wisdom rule violations summary

**Quarterly reports:** 🔴 NOT STARTED
- 🔴 90-day performance vs SPY/QQQ
- 🟡 Drawdown analysis — math shipped May 2, needs 90d window for quarterly
- 🔴 Strategy attribution
- 🔴 Pattern win rate evolution
- 🔴 LLM-generated quarterly review
- 🔴 PDF generation for sharing
- 🔴 Tax-relevant: realized vs unrealized
- 🔴 IRS quarterly estimate suggestions (US users)

**Yearly reports:** 🔴 NOT STARTED
- 🔴 Annual P&L with full attribution
- 🔴 Tax-loss harvesting opportunities (US)
- 🔴 Wash sale rule compliance
- ✅ Sharpe, Sortino, Calmar formulas — May 2 (yearly window TBD)
- 🔴 Year-over-year comparison
- 🔴 Capital gains breakdown (short vs long-term)
- 🔴 1099-equivalent annual summary (PDF)
- 🔴 LLM-generated annual letter (like Buffett's)
- 🔴 Lessons learned (auto-generated from journal)

#### 🟡 PRIORITY 3 — Edge Layer (was old PR #70-72) — 1 week

**EV Filter** (formerly PR #70, ~45 min)
- 🔴 Estimate win probability per pick
- 🔴 Calculate EV = P(win) × TP - P(loss) × SL
- 🔴 Reject picks with EV < 0.3%
- 🔴 Telegram shows: "🧮 P(win)=42% · EV=+0.15% · ✅ EDGE"
- INTEGRATES WITH: Pillar 1 (Probability Engine) for win probability

**Monster Hunt Mode** 💎 (formerly PR #71, ~90 min) — MISSING from v2
- 🔴 New monster_score (0-1) per pick
- 🔴 Boost factors:
  - +0.20 if earnings within 7 days
  - +0.15 if float < 50M shares
  - +0.20 if short interest > 15%
  - +0.10 if multiple recent analyst upgrades
  - +0.15 if at 52-week breakout
  - +0.10 if RVOL > 1.5x for 3+ days
  - +0.10 if bullish news on watchlist
- 🔴 If monster_score > 0.6:
  - Wider SL (5%)
  - Aggressive TP (25-50%)
  - Trail stop after +20%
  - Smaller position (1-3% lottery sizing)
- 🔴 New 💎 MONSTER HUNTS section in Telegram

**Position Tracker** (formerly PR #72, ~60 min)
- ✅ position_monitor module reads picks_log (no separate file by design, May 2)
- ✅ EOD evaluator auto-flags positions past max_hold (May 2)
- ✅ Telegram alerts on max-hold breach (May 2, send_position_alerts.py)
- 🔴 Updates picks_log.csv with actual_return

#### 🟢 PRIORITY 4 — Validation Infrastructure — 1 week

- 🔴 Alpaca PAPER TRADING integration (you have account)
- ✅ SPY benchmark column + alpha_pct in picks_log (May 2)
- 🔴 Sector benchmark per pick
- 🔴 Real fill tracking (slippage from Alpaca)
- 🔴 "No trade today" capability (high-bar threshold)
- ✅ Ticker cooldown (May 2)
- ✅ SL min by stock type (May 2)
- ✅ Universe top 100 (106 tickers, May 2)

#### 🟢 PRIORITY 5 — Multi-Asset & Advanced — Months 7-12

- 🔴 Multi-LLM ensemble (Claude + GPT-5 + Gemini consensus)
- 🔴 Adaptive position sizing (Kelly criterion, capped)
- 🔴 Correlation matrix (avoid overlapping picks)
- 🔴 Crypto module (BTC/ETH/SOL)
- 🔴 Options scoring (long calls on conviction picks)
- 🔴 Multi-timeframe confirmation
- 🔴 Stop hunting detection
- 🔴 Sector rotation awareness
- 🔴 Earnings call transcript LLM analysis
- 🔴 SEC 8-K filing alerts
- 🔴 Insider trading signals (Form 4)
- 🔴 Options flow integration
- 🔴 Twitter/X sentiment integration
- 🔴 Discord/Reddit retail sentiment
- 🔴 FDA approval tracker (biotech alpha)

#### 🟢 PRIORITY 6 — SaaS Platform — Months 7-12

- 🔴 Multi-tenant Postgres backend
- 🔴 FastAPI + JWT auth + 2FA
- 🔴 Per-user broker connections (encrypted)
- 🔴 Per-user Telegram bot tokens
- 🔴 Background job scheduler (Celery)
- 🔴 Next.js + Tailwind frontend
- 🔴 Web dashboard (picks, performance, settings)
- 🔴 Stripe billing
- 🔴 Tiered pricing (Free/Starter/Pro/Elite/Enterprise)
- 🔴 Public landing page + waitlist
- 🔴 Onboarding wizard (5 steps)
- 🔴 Feature gates per tier

#### 🟢 PRIORITY 7 — Mobile & Real-Time — Months 13-15

- 🔴 React Native iOS/Android app
- 🔴 Push notifications
- 🔴 1-tap approve trades
- 🔴 Voice query ("Why did NVDA stop out?")
- 🔴 Real-time WebSocket streaming
- 🔴 Sub-second pick updates

#### 🟢 PRIORITY 8 — Risk Management 2.0 — Months 16-18

- 🔴 Black swan hedging suggestions
- 🔴 Drawdown circuit breakers (portfolio-level)
- 🔴 Tax-loss harvesting helper
- 🔴 Wash sale rule awareness
- 🔴 Affiliate program (30% recurring)

---

## 📅 6-MONTH IMPLEMENTATION SCHEDULE

### MONTH 1 (May 2026) — Foundation Stabilization
**This weekend (May 2-3):**
- Save all roadmap docs (DONE)
- Fix BUG-4 (ticker cooldown)
- Fix BUG-5 (SL min by stock type)
- Add SPY benchmark column

**Week 2-4 (May 5-31):**
- Pillar 1 Layer 1: stock_stats foundation
- Pillar 1 Layer 2: regime-conditional statistics
- Open Twitter/X + LinkedIn accounts
- First public posts (build in public)
- Alpaca paper integration start

### MONTH 2 (June 2026) — Probability Engine + EV Filter
- Pillar 1 Layer 3: probabilistic price levels
- Pillar 1 Layer 4: hypothesis testing
- Edge Layer: EV Filter (PR #70)
- Edge Layer: Position Tracker (PR #72)
- Alpaca paper integration complete
- 30 days paper trading data

### MONTH 3 (July 2026) — Pattern Recognition + Wisdom Base
- Pillar 3: 15 pattern detectors
- Pillar 3: per-pattern statistics
- Pillar 2: Wisdom Base v1 (10 books)
- Per-pick wisdom check
- Edge Layer: Monster Hunt Mode (PR #71) 💎
- Stage 1 Gate review (60-day Alpaca paper)

### MONTH 4 (August 2026) — Feedback Loop + Self-Awareness
- Pillar 4: outcome attribution
- Pillar 4: weight update mechanism
- Pillar 5: confidence tracking
- Pillar 5: auto-pause triggers
- Pillar 6: P&L Brain (daily + weekly enhanced)

### MONTH 5 (September 2026) — Quarterly Reports + Multi-LLM
- Pillar 6: Quarterly reports (full implementation)
- Multi-LLM ensemble (Claude + GPT-5 + Gemini)
- Disagreement detection
- Reasoning chain audit
- Open Moomoo real money $5K SGD

### MONTH 6 (October 2026) — Brain Integration + Stage 2 Gate
- All 5+1 pillars working together
- Wisdom rules updated from outcomes
- Pattern discovery (clustering)
- 60-day Moomoo real money complete
- Stage 2 Gate review
- 10 alpha testers onboarded

---

## 💰 PRICING TIERS (Locked)

| Tier | Price | Features |
|---|---|---|
| FREE | $0 | 1 daily pick (24hr delayed), public track record, open source |
| STARTER | $39/mo | Real-time picks, Telegram alerts, weekly/monthly reports |
| PRO ⭐ | $99/mo | Full 5-layer exits, auto-execute, backtest, LLM reasoning |
| ELITE | $249/mo | Multi-asset, custom strategies, monthly 1:1 review call |
| ENTERPRISE | $999/mo | White-label, SLA, for hedge funds (Month 17+) |

**Discounts:**
- Annual: 2 months free (16% off)
- Lifetime: $1,499 (first 100 users)
- Affiliate: 30% recurring commission
- Founder pricing: $29/mo locked for first 25 users

---

## 🎯 STAGE GATES (Mandatory)

| Gate | When | Pass Criteria |
|---|---|---|
| Gate 1 | End Month 3 | 60-day Alpaca paper: capture ≥60%, win ≥45%, beats SPY +2% |
| Gate 2 | End Month 6 | 60-day Moomoo real $: capture ≥50%, beats SPY +1%, no >20% DD |
| Gate 3 | End Month 12 | $5K MRR, <10% churn, 50+ paying users, audited record |
| Gate 4 | Month 18 | $20K MRR for 3 months → **QUIT JOB** |

---

## 📊 SUCCESS METRICS (Month 24)

- ✅ $70K+ MRR ($840K ARR)
- ✅ 800+ paying customers
- ✅ 24-month audited live trading record
- ✅ 20K+ LinkedIn + 5K+ Twitter followers
- ✅ Industry recognition (Bloomberg/CNBC mention)
- ✅ Acquisition or Series A optionality
- ✅ Best-in-market on 8 of 14 dimensions

---

## 🤝 CUSTOMER PERSONA (Locked)

**Working professionals** ages 28-50, salary $80-300K, $20-500K investable assets.

Pain: "I want to beat the market but don't have time to research."
Channels: LinkedIn (primary), Twitter/X, Substack, YouTube, Discord.

---

## 🔄 WHAT TO DO NOW (Saturday May 2, ~2:30 PM SGT)

### IMMEDIATE (next 2 hours):
1. ✅ Save FINAL_ROADMAP.md (this file)
2. ✅ Save BRAIN_ARCHITECTURE.md (from earlier message)
3. ✅ Save CONTEXT.md, ADR-001, ADR-002, CHAT_HANDOFF_PROTOCOL (from earlier)
4. ✅ Commit all docs + push
5. 🟡 Fix BUG-4 (ticker cooldown) — 45 min
6. 🟡 Fix BUG-5 (SL min by stock type) — 45 min

### SUNDAY (May 3) MORNING:
7. Probability Engine Phase 1 (stock_stats foundation) — 3 hours
8. Open Twitter/X account (reserve handle) — 15 min
9. Open Substack (reserve) — 15 min
10. Smoke test Monday's workflow — 30 min

### MONDAY (May 4):
11. Watch agent fire 8:30 PM SGT
12. Tweet/LinkedIn post the picks publicly
13. Day 1 of REAL track record begins

---

## 📚 DOCUMENT INDEX

| Doc | Purpose |
|---|---|
| `docs/CONTEXT.md` | Read first — project identity |
| `docs/FINAL_ROADMAP.md` | THIS FILE — single source of truth |
| `docs/MASTER_PLAN_24_MONTH_v2.md` | 24-month strategic plan |
| `docs/BRAIN_ARCHITECTURE.md` | 5-pillar intelligence design |
| `docs/PROBABILITY_ENGINE_DESIGN.md` | Pillar 1 deep dive |
| `docs/decisions/ADR-001` | Probability over rules |
| `docs/decisions/ADR-002` | 5-pillar brain architecture |
| `docs/playbook/CHAT_HANDOFF_PROTOCOL.md` | Session start/end protocol |
| `docs/SPRINT_2026-05-02_TO_MONDAY.md` | Current sprint |
| `docs/sessions/` | Chat session handoffs |
| `docs/learnings/` | Discoveries & lessons |

---

## 🔄 REVISION HISTORY

- **v1.0 (April 30):** Original 24-month plan (100 features)
- **v2.0 (May 2 AM):** Reset based on Day 3 audit, customer persona locked
- **v3.1 (May 2 evening):** Backtester v2 shipped, algo validated +0.97 Sharpe,
  2 root-cause execution leaks patched (sector boost + workflow multi-fire).
  Phase 0 stabilization week added (May 3-9).
- **v3.0 FINAL (May 2 PM):** Consolidates everything:
  - 5-pillar brain architecture (Pillars 1-5)
  - Pillar 6 (P&L + Reporting Brain) added
  - Monster Hunt Mode explicitly included
  - EV Filter explicitly included
  - Position Tracker explicitly included
  - Penny stock bug confirmed resolved
  - All other bugs catalogued

**Next revision:** End of Month 1 (May 31, 2026) after first month of execution.

---

*Living document. Update after every major decision or weekly review.*
*Owner: Anjan Neogi, Singapore*
*Last updated: May 2, 2026*