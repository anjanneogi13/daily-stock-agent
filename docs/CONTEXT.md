# 🧠 Project Context — Read This First

## 🚀 LAST UPDATED: 2026-05-02 Saturday Sprint (33+ commits, 5/5 BUGS DONE, SPY alpha live)

### TL;DR FOR NEXT CHAT SESSION
- 🧠 **Pillar 1 Probability Engine v0.1 LIVE in production** (5 weeks ahead of plan!)
- 🎯 Brain coverage: **20 → 106 tickers** (5.3x expansion)
- 🧮 EV gate added in **OBSERVE-MODE** (logs vetoes, doesn't filter — flip Wednesday after Mon/Tue observation)
- 🐛 **PHASE 0 COMPLETE — ALL 5/5 BUGS RESOLVED** 🎉
📊 **SPY benchmark + alpha tracking LIVE** (Priority 4 item shipped 5 weeks early)
- 📲 Telegram MD→plain-text auto-fallback shipped (HTTP 400 fix)
- 📊 CI now auto-builds stock_stats every run (fresh data, never stale)
- 📚 5-pillar brain architecture locked (ADR-001, ADR-002, BRAIN_ARCHITECTURE.md)
- ✅ 190 tests passing (+25% from morning's 152)

### 🎯 NEXT SESSION'S TOP-3 PRIORITIES
1. **Position Tracker** (positions.json + max_hold flagging, ~60 min) — Edge Layer
2. ~~SPY benchmark column~~ ✅ DONE today (e409a5b)
3. **Wednesday May 6**: review Mon/Tue EV gate logs → flip `BRAIN_ENFORCE_EV=true`
   (with 11.1% win rate proven, EV gate is HIGH priority)

### 🚨 DO NOT TOUCH (working in production)
- `main.py` brain block (lines 213-260) — additive, zero-risk
- `.github/workflows/daily-picks.yml` stats build step — `continue-on-error: true`
- `TOP_100_TICKERS` list in `scripts/build_stock_stats.py` — just expanded, no churn
- Brain output is ADDITIVE only — old SL/TP still primary in Telegram

### 🔄 OPT-IN SWITCHES (env vars to flip later)
- `BRAIN_ENFORCE_EV=true` → activates EV-based pick filtering
- `BRAIN_EV_MIN_PCT=-1.0` → threshold for veto (default generous, tighten over time)

### 📊 PROGRESS METRICS (DELTA TODAY)
| Metric | This Morning | Now |
|---|---|---|
| 24-month plan complete | ~8% | **~14%** |
| Known bugs fixed | 1/5 | **4/5** |
| Brain pillars LIVE | 0/5 | **1/5** |
| Test count | 152 | **190** (+25%) |
| Brain ticker coverage | 20 | **106** |
| Open PRs (debt) | 13 | 13 (unchanged) |

### 📋 SCHEDULE COMPARISON: Plan vs Reality
- **Saturday May 2** plan: roadmap docs + BUG-4 + BUG-5 + SPY col → **3/4 DONE** (SPY pending)
- **Week 2-4 May** plan: Pillar 1 Layer 1 + Layer 2 → **DONE TODAY (3 weeks early)**
- **Month 2 June** plan: Pillar 1 Layer 3 + EV Filter → **Layer 3 DONE + EV in observe-mode (5 weeks early)**

### 🐛 STILL OPEN BUGS
✅ NONE — Phase 0 complete as of 2f46dae

### 📈 FIRST REAL PERFORMANCE NUMBERS (post-BUG-2 fix + SPY alpha)
**Returns:**
- 9/38 picks closed (29 still mid-flight)
- Win rate: 11.1% (1 TP, 8 SL)
- Expectancy: -0.70R per trade
- SEMI/AI tag: 0% win rate, -7R total — needs scrutiny
- Best: AAPL +2.18% (1.66R)
- Worst: ARM -8.83%
- **Implication**: Pillar 1 EV gate even MORE necessary than thought.

**Alpha vs SPY (NEW):**
- 1/9 picks beat SPY (only AAPL +1.9% alpha)
- Avg alpha: **-5.70%** (worse than raw return → genuine alpha destruction)
- Worst: SLNH -9.92%, ARM -8.83%, RMBS -9.22%
- **Implication**: Losses aren't "market down" — losses are losing TO the market.
  SEMI/AI tag is systematically alpha-negative.

### 📝 KEY COMMITS TODAY (chronological)
- `cd4d212` Pillar 1 brain wired into main.py + Telegram fallback fix
- `42570ea` docs: roadmap reality check — Phase 5 + Pillar 1 LIVE
- `860a134` feat(brain): expand stats coverage 20 → 106 tickers
- `11b6e36` ci(brain): auto-build stats before every daily picks run
- `bcd529e` feat(brain): EV gate (observe-mode, opt-in enforcement)
- `2eab633` docs(context): May 2 sprint summary
- `bf06c07` fix(BUG-2): evaluator off-by-one — first real win-rate numbers
- `d54666f` docs(context): mark BUG-2 closed + record real win/loss numbers
- `e409a5b` feat(eval): SPY benchmark + alpha tracking — 1/9 beat SPY
- `58f9595` docs: mark SPY benchmark + 4/5 bugs done in roadmap
- `d2925e4` docs(sessions): Saturday May 2 sprint log
- `2f46dae` fix(BUG-3): eliminate regime='unknown' — PHASE 0 100% DONE 🎉

---


> **Purpose:** This file is the SINGLE SOURCE OF TRUTH for any new chat session, any future contributor, or any future "you" picking this up after a break. Read this completely before doing anything.

> **Last updated:** 2026-05-02 by Anjan
> **Update protocol:** After EVERY significant decision or session

---

## 🎯 PROJECT IDENTITY

- **Name:** Daily Stock Agent
- **Owner:** Anjan Neogi (Singapore)
- **Started:** April 30, 2026
- **Mission:** Build the world's first transparent, audited, AI-powered trading agent that beats every retail product
- **24-month plan:** See `docs/MASTER_PLAN_24_MONTH.md`
- **Goal:** $20K+ MRR by Month 18 (quit job), $70K+ MRR by Month 24

---

## 🏛️ FOUR PILLARS

1. **Technical Excellence** — Be objectively better
2. **Trust & Transparency** — Be the only honest player (open source, audited)
3. **Community & Education** — Build in public
4. **Sustainable Business** — $1M+ ARR by Month 24

---

## 🧠 ARCHITECTURE NORTH STAR

**Statistical Probability Engine** (locked May 2, 2026)

Every price decision (SL, TP, buy, sell, trigger) MUST be PROBABILITY-BASED, not rule-based. The agent must know its own probability of working at all times.

See: `docs/PROBABILITY_ENGINE_DESIGN.md`

This replaces all arbitrary thresholds (1.5×ATR, RSI 30, 3% SL) with empirically-derived probabilistic decisions.

---

## ✅ WHAT'S BUILT (Audit Reference)

- 81 Python files, 10,095 lines of code
- 9 GitHub Actions workflows (daily picks, news, eval, weekend, monthly, intraday, watchdog, backup)
- 12 test files (LOW coverage — gap)
- 86 PRs merged
- 38 picks logged in 9 days
- 749 data files
- News pipeline working (266 active signals)
- Backup system live
- Hard enforcement layer live

For complete inventory, run:
```bash
python scripts/code_inspector.py
```

---

## 🚨 KNOWN BUGS / TECHNICAL DEBT

1. **BUG-2:** Many picks stuck in "pending" evaluation status
2. **BUG-3:** Regime returning "unknown" frequently
3. **BUG-4:** Same ticker (TSM) picked 3+ times in 9 days — no cooldown
4. **TECH DEBT:** `src/paper_trader.py` exists but not integrated
5. **TECH DEBT:** Test coverage ~15% (need 40%+)
6. **TECH DEBT:** 13 open PRs creating merge debt

---

## 🚫 WHAT WE EXPLICITLY ARE NOT BUILDING (Yet)

- LLM vision chart reading → tech immature in 2026
- Deep learning models → need 10K+ trades
- High-frequency strategies → unrealistic for retail
- Live brokerage execution → after 3 months proven paper edge
- Discord/Slack notifications → don't fragment focus
- Multi-asset (crypto, options) → after Phase T7 (Month 8)

For each, see `docs/decisions/` for the WHY.

---

## 📜 OPERATING PRINCIPLES

1. **Decisions live in the repo, not in chat sessions**
   - Chat sessions reset; the repo doesn't
   - Every architectural decision → `docs/decisions/ADR-NNN.md`

2. **Probability over rules**
   - Replace arbitrary thresholds with empirical probabilities
   - Every pattern must pass hypothesis test (p < 0.05) to deploy

3. **Anti-overfitting discipline**
   - Train/test split mandatory
   - Walk-forward validation (no lookahead)
   - 95% CIs for go/no-go decisions
   - Pre-register hypotheses BEFORE testing

4. **Build in public**
   - LinkedIn (M/W/F), Twitter (daily)
   - Open source from Day 1
   - Honest about losses

5. **Stage gates discipline**
   - Stage 1: 60-day Alpaca paper validation (no real money before)
   - Stage 2: 60-day Moomoo real $5K (no SaaS build before)
   - Stage 3: 3-month soft launch (no public launch before)

6. **Sustainable pace**
   - Weekly rest day (Sunday afternoon off)
   - Quarterly 2-week vacation
   - 8 hours sleep non-negotiable

---

## 🔄 SESSION START PROTOCOL (For Future "You" or AI)

When starting a new chat session, paste this prompt:

> "Resuming work on daily-stock-agent. Read these files in order:
> 1. `docs/CONTEXT.md` (this file)
> 2. `docs/ROADMAP.md` (current state + plan)
> 3. `docs/PROBABILITY_ENGINE_DESIGN.md` (architecture)
> 4. `docs/sessions/` (most recent file — last session handoff)
> 5. `docs/decisions/` (recent ADRs)
>
> Then summarize: where we are, what's next, any open questions."

---

## 📂 KEY DOC LOCATIONS

| Doc | Purpose |
|---|---|
| `docs/CONTEXT.md` | THIS FILE — read first |
| `docs/ROADMAP.md` | Current phased roadmap, updated weekly |
| `docs/MASTER_PLAN_24_MONTH.md` | 24-month strategic plan |
| `docs/PROBABILITY_ENGINE_DESIGN.md` | Statistical engine architecture |
| `docs/decisions/` | Architecture Decision Records |
| `docs/sessions/` | Chat session handoffs |
| `docs/playbook/` | How we work |
| `docs/learnings/` | What we discovered |

---

## 🔧 KEY COMMANDS

```bash
# See current pipeline status
python main.py --status

# Run full pick generation (manual)
python main.py

# Generate evaluation report
python evaluate_picks.py

# Trigger backup
python scripts/backup_data.py

# View recent picks
tail -10 data/picks_log.csv

# Check workflow status  
gh run list --limit 10
```

---

## 🤝 WORKING AGREEMENT

**Founder commits:**
- Update this file after every major decision
- Tweet/post weekly minimum (build in public)
- Respect stage gates (don't skip)
- Take rest (no burnout)

**AI co-pilot commits:**
- Read this file at start of every session
- Push back on bad ideas (honest co-founder voice)
- Document everything in repo (memory > chat)
- Reference architecture decisions before coding

---

*This is your single source of truth. Treat it as sacred.*