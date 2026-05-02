# 🗺️ Daily Stock Agent — Living Roadmap

> **Last updated:** 2026-05-02 (Saturday)
> **Update cadence:** Every coding session — co-founder reviews + amends
> **North Star:** Build the world's first self-improving retail trading AI with provable edge

---

## 🎯 NORTH STAR (don't change without serious thought)

A retail-priced trading AI that:
1. **Has a proven track record** (verifiable, public)
2. **Self-improves** from its own outcomes (not just static rules)
3. **Reads markets like a top trader** (patterns + catalysts + regime)
4. **Knows when not to trade** (confidence thresholds, not forced picks)
5. **Sells as SaaS** ($30-100/month tier, eventually)

---

## 📊 CURRENT STATE (Snapshot 2026-05-02)

**Codebase:** 81 Python files, 10,095 lines, 12 test files, 86 PRs merged
**Workflows:** 9 GitHub Actions (daily picks, news, eval, weekend, monthly, intraday, watchdog, backup)
**Data:**
- 38 picks logged (9 days, ~4/day)
- 811 KB news log (active classification)
- 102 KB news signals (266 active)
- 749 total data files

**What works:**
- Pick generation pipeline
- News classification + storage
- Daily Telegram delivery
- Backup system (just shipped)
- Hard enforcement layer (just shipped)

**What's broken / unused:**
- `src/paper_trader.py` exists but not integrated
- `src/performance_tracker.py` underused (most picks "pending")
- Regime detection often returns "unknown"
- Penny stock filter not enforcing (SLNH $1.66 logged May 1)
- Same ticker (TSM) picked 3+ times — no cooldown
- 13 open PRs (#60-86) creating merge debt

---

## 🚨 PHASE 0 — STABILIZE (NEXT 1-2 SESSIONS)

> Before adding anything new, fix what's broken. Pure debt reduction.

### Bugs to fix
- [ ] **BUG-1** Penny stock SLNH bypassed min_price filter — investigate enforcement chain
- [ ] **BUG-2** Picks stuck in "pending" — verify evaluate.yml is running + closing
- [ ] **BUG-3** Regime returning "unknown" — debug regime.py inputs
- [ ] **BUG-4** Same ticker picked multiple times in week — add cooldown logic
- [ ] **BUG-5** Decide fate of `src/paper_trader.py` — integrate OR delete

### Hygiene
- [ ] Close 13 open PRs (merge or close as obsolete)
- [ ] Test coverage from 15% → 40% (focus on hard_blocks, regime, scoring)
- [ ] Delete `TOMORROW_START_HERE.md` (replaced by this roadmap)

**Effort:** 4-6 hours
**Why FIRST:** Building on a broken foundation = wasted work.

---

## 🏗️ PHASE 1 — VALIDATION INFRASTRUCTURE (1-2 weeks)

> Without these, every "improvement" is unverifiable. Existential.

### Must-build
- [ ] **VAL-1** Alpaca paper trading integration (use existing `paper_trader.py`)
- [ ] **VAL-2** Benchmark column in picks_log (SPY return same period)
- [ ] **VAL-3** Sector benchmark (XLK, XLF, etc. matched to pick sector)
- [ ] **VAL-4** Real P&L attribution (slippage, fills, fees from Alpaca)
- [ ] **VAL-5** "No trade today" capability (skip when no edge clears threshold)

### Nice-to-have
- [ ] Walk-forward backtest framework (replay last 30 days)
- [ ] Pick uniqueness check (don't repeat same ticker within N days)

**Effort:** 12-15 hours
**Success criteria:** Every pick has REAL outcome + benchmark comparison + alpha calculation.

---

## 📚 PHASE 2 — WISDOM BASE (2-3 days, your unique idea!)

> The most differentiating feature. Almost nobody does this.

### Build steps
- [ ] **WIS-1** Curate book list (Lefèvre, O'Neil, Schwager, Lynch, Graham, etc.)
- [ ] **WIS-2** LLM-extract top rules per book (one-time ~$10)
- [ ] **WIS-3** Store in `data/wisdom_base.json` (rules, source, category)
- [ ] **WIS-4** Per-pick wisdom check (does pick violate any rule?)
- [ ] **WIS-5** Telegram shows: "✓ Matches O'Neil C+A+N" or "⚠ Violates Lefèvre rule X"
- [ ] **WIS-6** Weekly post-mortem: which wisdom rule was violated on losses?

**Effort:** 4-6 hours of code + content curation
**Cost:** ~$15-20/year in LLM calls
**Why this matters:** This is your moat. Competitors don't do this.

---

## 🧠 PHASE 3 — LEARNING LOOP (Month 2-3, after data accumulates)

> Cannot build until we have 100+ paper-traded picks with real outcomes.

### Level 0 (manual): Weekly review picks_log, hand-tune weights
### Level 1 (linear): Regression on outcomes → updated weights
### Level 2 (Bayesian): Online weight updates as new outcomes arrive
### Level 3 (ML): XGBoost/NN once 500+ outcomes — strict validation

**Pre-requisites:** Phase 1 (validation) + 30+ days of paper-traded data
**Effort:** 8-12 hours when ready
**DO NOT BUILD EARLY. Overfitting risk extreme.**

---

## 📈 PHASE 4 — STRATEGY DEPTH (Month 3-4)

> Once edge is proven on baseline, add specialized strategies.

### Day Trading (separate scoring track)
- [ ] Strict tech-only (no fundamentals/news in scoring)
- [ ] 5/10/20/30 MA stack as primary signal
- [ ] RVOL + ATR weighted heavier
- [ ] Mandatory EOD exit (max_hold_minutes already in config)

### Swing Trading
- [ ] Tech + fundamentals + news combined
- [ ] 2-10 day hold
- [ ] Wider stops, tiered targets

### Multi-bagger Hunt (small position sizing)
- [ ] Earnings-within-7-days boost
- [ ] Low float + high short interest filter
- [ ] Wide stop, asymmetric target (25-50%)
- [ ] Max 1-3% account per pick (lottery sizing)

**Pre-requisite:** Phase 3 learning loop showing which strategy has edge

---

## 🌐 PHASE 5 — UNIVERSE OPTIMIZATION (Ongoing)

> Quality > quantity. Depth > breadth.

- [ ] Reduce S&P 500 → top 100 by liquidity + fundamentals
- [ ] Add curated "wisdom-approved" list (CANSLIM screen?)
- [ ] Sector rotation tracking
- [ ] Earnings calendar integration (skip 3 days before earnings unless monster setup)

---

## 💼 PHASE 6 — PRODUCTIZATION (Month 4-6)

> Only after edge is proven. Otherwise selling snake oil.

### Tech
- [ ] Web dashboard (Streamlit on Render or similar)
- [ ] User accounts + onboarding
- [ ] Configurable risk profiles per user
- [ ] Mobile PWA

### Business
- [ ] Stripe billing
- [ ] ⚠️ **SEC compliance review** (advisor registration vs research framing)
- [ ] LLC formation
- [ ] Terms of Service + Privacy Policy
- [ ] Trademark filing

### Marketing
- [ ] Public verified track record
- [ ] Substack/newsletter
- [ ] YouTube weekly review
- [ ] Twitter/X presence

---

## 🚫 EXPLICITLY NOT BUILDING (and why)

| Idea | Why deferred |
|---|---|
| Vision LLM chart reading | Tech not ready (May 2026 vision LLMs ~60% accurate). Numerical pattern detection works better. Re-evaluate Q4 2026. |
| Brain v1 self-learning | Need 500+ real-outcome picks first. Currently have 38. Premature = overfitting. |
| Multi-bagger strategy | Until base strategy proves edge, this is fantasy. |
| Discord/Slack notifications | Telegram works. Don't fragment focus. |
| Brokerage live execution | Until 3+ months proven paper edge. Real money on unproven system = ruin. |
| Options flow | Tier 3 feature. After Phase 4. |

---

## 📅 SESSION LOG

| Date | Hours | What shipped | What we learned |
|---|---|---|---|
| 2026-05-02 | ~5 | PR #84/85/77/69.8/83 (safety/ops PRs) | Builder's trap diagnosed; pivoting to Phase 0 stabilization |

---

## 🎯 NEXT SESSION PRIORITIES

**Immediate (next session):**
1. Investigate BUG-1 (SLNH penny stock leak) — 30 min
2. Investigate BUG-2 (pending evaluations) — 30 min
3. Start VAL-1 (Alpaca paper integration) — 3 hr
4. Start WIS-1 (curate book list) — 1 hr

**This week:**
- Complete Phase 0 (stabilize)
- Begin Phase 1 (validation infra)

**This month:**
- Complete Phase 1 + Phase 2 (wisdom base)
- Accumulate 30+ paper-traded picks for Phase 3 prep

---

## 🔄 UPDATE PROTOCOL

After every coding session:
1. Update "Session Log" with what shipped
2. Tick boxes for completed items
3. Add new bugs discovered to Phase 0
4. Move items between phases if priorities shift
5. Update "Current State" snapshot at top
6. Commit with message: `docs: roadmap update YYYY-MM-DD`