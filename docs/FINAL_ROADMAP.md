# 🚀 FINAL CONSOLIDATED ROADMAP — Daily Stock Agent

> **Version:** FINAL v3.0 (consolidates v1, v2, brain architecture, EV/Monster/Position features)
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
- 🔴 BUG-3: Regime returning "unknown" frequently  
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
- 🔴 Per-strategy + per-regime tracking
- 🔴 Auto-pause triggers
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
- 🔴 Win rate by strategy (day/swing/multi)
- 🔴 Sharpe ratio calculation

**Monthly reports:** (partial done)
- ✅ Basic monthly X-ray
- 🔴 Per-strategy P&L breakdown
- 🔴 Per-sector P&L breakdown
- 🔴 Pattern performance summary
- 🔴 Wisdom rule violations summary

**Quarterly reports:** 🔴 NOT STARTED
- 🔴 90-day performance vs SPY/QQQ
- 🔴 Drawdown analysis
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
- 🔴 Annual Sharpe, Sortino, Calmar ratios
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
- 🔴 New positions.json tracks live trades
- 🔴 EOD job auto-flags positions past max_hold
- 🔴 Telegram alerts on max-hold breach
- 🔴 Updates picks_log.csv with actual_return

#### 🟢 PRIORITY 4 — Validation Infrastructure — 1 week

- 🔴 Alpaca PAPER TRADING integration (you have account)
- ✅ SPY benchmark column + alpha_pct in picks_log (May 2)
- 🔴 Sector benchmark per pick
- 🔴 Real fill tracking (slippage from Alpaca)
- 🔴 "No trade today" capability (high-bar threshold)
- 🔴 Ticker cooldown (BUG-4 fix — no TSM 3× in week)
- 🔴 SL min differentiation by stock type (BUG-5 fix)
- 🔴 Universe reduction (500 → top 100 by liquidity)

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