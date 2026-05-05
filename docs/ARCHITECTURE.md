# 🏛️ Daily Stock Agent — Architecture

**Last updated:** 2026-05-05
**Tests:** 1273 passed, 28 skipped · **Modules:** 80+ · **Workflows:** 14 · **Health:** monitoring-ready

---

## 0A. Monitoring-first launch status (2026-05-05)

**Monitoring-first launch** is the current product decision.

- The agent is approved for monitoring-only operation.
- real-money trading is forbidden.
- paper trading is deferred until two monitoring windows complete.
- Window 1: 2-week observation while issue cleanup and architecture work continue.
- Window 2: second 2-week validation after architecture stabilizes.
- Paper trading eligibility requires post-floor trade-type gates:
  - day trades >60% win rate plus positive expectancy
  - swing trades >66% win rate plus positive expectancy
  - monster / long holder picks >90% win rate plus positive expectancy

Decision record: `docs/decisions/2026-05-05-monitoring-first-no-paper-trading.md`

---

## 0. The 24-hour Rhythm (Singapore Time)

| When (SGT) | When (US ET) | What happens | Who reads it |
|---|---|---|---|
| **Mon-Fri 8:30 PM** | 8:30 AM ET | 🌅 Daily picks → Telegram (layman) | User |
| Mon-Fri 9:30 PM – 4 AM | 9:30 AM – 4 PM ET | 📊 Intraday monitor every 30 min | Files only |
| **Tue-Sat 6:00 AM** | 6:00 PM ET (prev day) | 🌆 Performance recap → Telegram (layman) | User |
| **Daily 7:00 AM** | 11:00 PM UTC | 🌙 Nightly Brain — 8-step self-improvement incl. memoir | Files (`learning_journal.jsonl`) |
| **Sat 9:00 AM** | 1:00 UTC Sat | 📅 Weekly recap → Telegram (layman) | User |
| **Mon 7:00 AM** | 11:00 PM UTC Sun | 🧠 Self-Improvement Report → Telegram | User |
| **1st of month 6:00 AM** | 22:00 UTC | 📆 Monthly recap → Telegram (layman) | User |
| **Jan 2 8:00 PM** | 12:00 UTC | 🎊 Year-in-Review → Telegram (layman) | User |

---

## 1. The 8 Pillars (all live)

| # | Pillar | Module | Status |
|---|---|---|---|
| 1 | **Context-aware scoring** | `parallel_scorer.py`, `scorer.py` | ✅ Live |
| 2 | **Wisdom base** (lessons learned) | `wisdom_base.py`, `wisdom_hint.py`, `wisdom_consultant.py` | ✅ Live |
| 3 | **Pattern engine** (16 chart patterns × regime) | `pattern_engine.py`, `pattern_layer.py`, `pattern_stats.py` | ✅ Live + WIRED into scoring |
| 4 | **Calibration loop** (per-factor accuracy → weight tweaks) | `calibration.py`, `weight_proposer.py`, `weight_applier.py` | ✅ Live (5%/wk safety cap) |
| 5 | **Auto-pause** (degraded health → pause) | `auto_pause.py`, `pause_state.py`, `self_awareness.py` | ✅ Live |
| 6 | **Hypothesis engine** (Wilson 95% CI tests) | `hypothesis_engine.py` | ✅ Live |
| 7 | **News & watchlist** | `news_engine.py`, `watchlist_manager.py`, `data/watchlist.json` | ✅ Live |
| 8 | **Auto-promote + lesson GC** | `auto_promote.py`, `lesson_gc.py` | ✅ Live |

---

## 2. The Self-Improvement Loop (NEW — May 3 2026)

┌─ EVERY NIGHT 11 PM UTC (Mon-Sun) ─────────────────────────┐ │ src/nightly_conductor.py — single orchestrator │ │ │ │ Step 1: pattern_scan (300 tickers on holidays) │ │ Step 2: pattern_stats (per-pattern × per-regime) │ │ Step 3: pattern_auto_e_d (kill losers, restore good) │ │ Step 4: calibration_propose (per-factor accuracy) │ │ Step 5: weight_apply (under 5%/wk safety cap) │ │ Step 6: auto_promote (winners → wisdom lessons) │ │ Step 7: lesson_gc (drop stale lessons) │ │ Step 8: agent_memoir (self-portrait + mission memory) │ │ │ │ Each step isolated in try/except — one failure can't │ │ break the chain. Single 'nightly_brain_run' event emitted │ │ to learning_journal.jsonl. │ └─────────────────────────────────────────────────────────────┘

┌─ EVERY SUNDAY 11 PM UTC ─────────────────────────────────────┐ │ src/meta_brain.py — reasons about the brain itself │ │ │ │ - recent_mutations(7d) │ │ - categorize by kind │ │ - detect_stuck_areas (no learning in 14d?) │ │ - suggest_hypotheses (outperforming buckets) │ │ - format_telegram_digest → plain English │ └──────────────────────────────────────────────────────────────┘

Code

---

## 3. Calendar Awareness (NEW — May 3 2026)

`src/market_calendar.py`

- Hardcoded NYSE holidays for **2026, 2027, 2028** (3-year buffer)
- Half-day awareness (Black Friday, Christmas Eve)
- Weekend skip everywhere (`main.py`, `intraday_monitor.py`)
- **Holidays = deep-learning days** (300 ticker scan vs 100)
- 3-layer renewal reminder system:
  1. Sunday Self-Improvement Report
  2. Monthly X-Ray Telegram
  3. GitHub Issue auto-opened Jan 1 + Jul 1 yearly
- Escalating tone: 📅 soft → ⚠️ urgent → 🚨 critical
- Annual user action: ~30 sec (~once every 2-3 years)

---

## 4. Dual-Channel Reporting (NEW — May 3 2026)

| Channel | Audience | Lives in | Telegram? |
|---|---|---|---|
| **Technical** | The AI agent (its own learning) | `signal_journal.jsonl`, `learning_journal.jsonl`, `exec_report_*.json`, `picks_log.csv` | ❌ No |
| **Layman** (NEW) | User + future amateurs | 5 `send_layman_*.py` scripts | ✅ Yes — only thing user sees |

`src/layman_translator.py` is the single source of truth for plain-English conversions:
- `score_to_words(0.92)` → `'excellent'`
- `pick_to_layman(pick)` → full plain-English with all prices
- `outcome_to_layman(out)` → `'✅ NVDA — hit profit target (+$120)'`
- `verdict_line(7,2,250)` → `'🎯 GREAT — agent crushed it today'`

---

## 5. Workflow Inventory (14 total)

| Workflow | Schedule (UTC) | Purpose |
|---|---|---|
| daily-picks.yml | 12:30 + 13:30 Mon-Fri | Pick stocks → layman Telegram |
| evaluate.yml | 22:00 Mon-Fri | Compute outcomes → layman recap |
| intraday_monitor.yml | every 30min during US hours | SL/TP proximity alerts |
| news_engine.yml | every 30min | News → watchlist boost |
| nightly_brain.yml | 23:00 daily | 8-step self-improvement incl. memoir |
| weekend_reflection.yml | 00:00 Sat | LLM-graded reflection |
| weekly_report.yml | 01:00 Sat | Weekly metrics + layman Telegram |
| hypothesis_weekly.yml | 15:00 Sun | Statistical edge tests |
| monthly_xray.yml | 22:00 1st of month | Monthly deep dive + layman Telegram |
| yearly_recap.yml | 12:00 Jan 2 | Year-in-Review layman Telegram |
| holiday_renewal_reminder.yml | 12:00 Jan 1 + Jul 1 | Auto-issue if calendar buffer low |
| backup.yml | 23:00 daily | Backup data/ |
| watchdog.yml | 13:35 + 14:35 Mon-Fri | Verify morning run happened |
| ci.yml | on push | Test gate |

---

## 6. Safety Mechanisms

| Risk | Defense |
|---|---|
| Weight changes too fast | 5%/factor/week cap in `weight_applier.py` |
| Promoting noise as wisdom | Wilson 95% CI required in `hypothesis_engine.py` |
| Killing patterns prematurely | Min 30 trades + mean_R < -0.30 |
| Bad strategy keeps running | Auto-pause when 14d health degrades |
| Forgetting old lessons too fast | Lesson GC requires 90+ days stale |
| Single bad day skews learning | Rolling 30d windows |
| US market closed → corrupted data | `is_trading_day()` check in main.py |
| Telegram message duplicates | `dedup_sender.py` with content-hash |
| Brain stuck without warning | Meta-Brain flags 14d-no-mutation as 'stuck' |

---

## 7. What's NEXT (deferred to future sessions)

See `docs/FINAL_ROADMAP.md` and `docs/NEXT_SESSION.md` for the prioritized backlog.

---

## 8. The 7-Faculty Agent Model (added 2026-05-04)

Anjan's design vision: build the agent like an advanced human — with all the
faculties of a person, plus a 6th sense for prediction, plus curiosity that
never stops. But CRITICALLY: zero emotion. All decisions driven by data and
what works, not fear or greed.

### The 7 faculties

| # | Faculty | Purpose | Current module(s) | Maturity |
|---|---|---|---|---|
| 1 | 🧠 **Brain** | Decision-making | `parallel_scorer.py`, `probability_engine.py` | Strong |
| 2 | ❤️ **Heart** | Risk tolerance, conviction (NO emotion) | `weight_applier.py` (5%/wk cap), `auto_pause.py` | Strong |
| 3 | 🌟 **Soul** | Identity, mission, narrative memory | `agent_memoir.py` | Strong (NEW May 4) |
| 4 | 👁 **Sight** | Reads price/volume charts | `pattern_engine.py` (16 patterns) | Strong |
| 5 | 👂 **Hearing** | Listens to news + sentiment | `news_engine.py` | Basic (regex) |
| 6 | 👅 **Taste** | Discerns quality (good vs bad setups) | `monster_score`, `composite_score` | Strong |
| 7 | 👃 **Smell** | Detects danger early | `auto_pause.py`, `hard_blocks` | Reactive only |
| 8 | ✋ **Touch** | Feels market temperature (regime) | `regime.py` (bull/bear/chop) | Strong |
| 9a | 🔮 **6th sense (tactical)** | Predicts edges per pattern × regime | `hypothesis_engine.py` (Wilson 95% CI) | Just started |
| 9b | 🌍 **6th sense (strategic regime)** | Pattern-matches today vs historical events; predicts regime transitions | `historical_regime_engine.py` (Phase 10) | NOT YET BUILT |
| 10a | 🦉 **Curiosity (inward)** | Uses idle time to study itself | `curiosity_engine.py` (Phase 9) | NOT YET BUILT |
| 10b | 📚 **Curiosity (outward)** | Reads books, extracts claims, validates against own data | `reader_engine.py` (Phase 9.5) | NOT YET BUILT |

(Now 12 module slots but still only 7 marketing faculties — sight/hearing/taste/smell/touch
collectively are "the 5 senses" + brain + heart + soul + 6th sense (tactical+strategic) + curiosity (inward+outward).
Going with 7 in marketing language: brain, heart, soul, 5 senses, 6th sense, curiosity.
The 6th sense and curiosity each have 2 horizons — see rows 9a/9b and 10a/10b above.)

### What makes this different from a human trader

**Humans:** brain × 5 senses × emotional bias = often bad decisions
**Our agent:** brain × 5 senses × 6th sense × curiosity − emotional bias = consistently better decisions

Future tagline (per BUSINESS_PLAN):
> *"A trading agent built like a human — but with one critical upgrade:
>  it can't feel fear or greed."*

### How faculties collaborate (the rhythm)

Daily picks workflow: Sight (patterns) + Hearing (news) + Taste (monster_score) + Touch (regime) → Brain (parallel_scorer) consults Heart (risk caps) → Soul (memoir) provides historical context → Picks emitted to user

Nightly brain workflow: Curiosity (idle exploration) → 6th sense (hypothesis testing, Wilson 95% CI) → Brain learns (calibration_propose) → Heart enforces safety (5%/wk cap) → Soul updates memoir

Code

### Maturity targets (from BUSINESS_PLAN.md)

| Faculty | Today | Month 3 target | Month 12 target |
|---|---|---|---|
| Hearing | regex | LLM news comprehension | multi-source consensus |
| Smell | reactive | proactive danger sniffing | predicts danger 2-3 days early |
| 6th sense (tactical) | starting | 50+ tested hypotheses | regime-specific edge maps |
| 6th sense (strategic regime) | not built | catalog research started | 13-event catalog live, nightly pattern-match running |
| Curiosity (inward) | not built | runs hourly, 100 questions answered | self-generates new questions |
| Curiosity (outward / books) | not built | first book ingested + validated | 12+ books ingested, 30+ promoted claims |
