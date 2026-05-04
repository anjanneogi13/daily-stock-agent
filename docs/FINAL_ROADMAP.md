# 🗺️ Daily Stock Agent — Final Roadmap

**Last updated:** 2026-05-03 · 17:30 SGT
**Status:** 100% of MVP shipped · 100% of "Big 4 Ideas" shipped

---

## ✅ DONE — Phases 1 to 4 (T01 → T52)

### Phase 1: Foundation (T01-T15) — ✅ COMPLETE
Universe, scoring, journaling, Telegram, evaluator, regime detection,
auto-pause, signal journal, learning journal, weekend reflection.

### Phase 2: Intelligence (T16-T33) — ✅ COMPLETE
Wisdom base, news engine, watchlist, hypothesis engine, pattern engine,
calibration, weight proposer, weight applier, monthly X-ray, intraday monitor.

### Phase 3: Maturity (T34-T49) — ✅ COMPLETE
Auto-promote, lesson GC, self-awareness, dedup sender, layman docs,
pause state machine, sector caps, news verifier.

### Phase 4: The Big 4 Ideas (T50-T52) — ✅ SHIPPED MAY 3 2026
| Idea | Status | Module(s) |
|---|---|---|
| **Idea 1 — Self-improving brain** | ✅ Live | `nightly_conductor.py`, `meta_brain.py` |
| **Idea 2 — Architecture doc** | ✅ Live | `docs/ARCHITECTURE.md` |
| **Idea 3 — Integration audit (8/8)** | ✅ Live | Pillar 3 wired into `parallel_scorer.py`; 8 cron jobs scheduled |
| **Idea 4 — Layman Telegram** | ✅ Live | `layman_translator.py` + 5 `send_layman_*.py` scripts |
| **Bonus — Calendar awareness** | ✅ Live | `market_calendar.py` + 3-layer renewal reminder |

### Today's stats
- Tests: 491 → 805 (+314, ZERO regressions)
- New modules: 9
- New workflows: 3 (`nightly_brain.yml`, `yearly_recap.yml`, `holiday_renewal_reminder.yml`)
- Lines of code: ~3,500 added, ~11,897 total in src/
- Health check: 10/10

---

## 🟡 NEXT — Phase 5: Observation & Polish (no work yet)

**Goal: Run for 1-2 weeks. Read the Telegram messages. Find what reads weird.**

| Task | Why | Effort |
|---|---|---|
| Observe 5 days of layman daily picks | Tone, length, info density check | 0 (just read) |
| Observe first Sunday Self-Improvement Report | Does it read like a friend? | 0 (just read) |
| Observe first monthly recap (June 1) | Does it summarize well? | 0 (just read) |
| Tune layman_translator wording based on feel | Adjust based on real reads | ~30 min |
| Add small layman flourishes (emoji, encouragement) | Make it feel warmer | ~30 min |

---

## 🟠 PHASE 6 — Power User Features (deferred, optional)

| Idea | Justification | Priority |
|---|---|---|
| Telegram inline buttons ("show me why" → details) | Drill-down on any pick | Medium |
| Sector rotation tracking + alerts | Identify regime shifts earlier | Medium |
| Earnings-week awareness (skip earnings ±2 days) | Reduce earnings-day surprises | High |
| Pre-market gap awareness | Avoid gap-and-fade traps | High |
| Adaptive trade sizing (Kelly Criterion light) | Compound winners faster | Medium |
| Backtest rerunner on rule changes | Validate weight tweaks didn't break edge | High |
| Web dashboard (read-only) | See journal data visually | Low |

---

## 🔴 PHASE 7 — Infrastructure Hardening (deferred)

| Idea | Justification | Priority |
|---|---|---|
| Dependency upgrades + security scan | Health hygiene | Low |
| Move to Postgres from CSV (10K+ trades) | Performance at scale | Low (years away) |
| Failover broker / data source | Resilience | Low |
| Rate-limit + retry decorator on yfinance | Reduce silent fetch failures | Medium |
| Test coverage for scripts/ (currently src/ only) | Catch CLI bugs earlier | Medium |

---

## 🚫 NEVER (intentional non-goals)

- Real-money trading execution (agent recommends, user trades)
- Options / futures / crypto (US equities only by design)
- Auto-fetch holidays from internet (silent failure risk)
- Removing the technical channel (the agent learns from it)
- Sub-minute intraday trading (we're swing/day, not HFT)

---

## 🧠 PHASE 8 — Selective LLM Augmentation (PARKED — pending data)

**Added:** 2026-05-04 (founder idea: multi-agent clones)
**Status:** 🟡 PARKED — do not start until 4+ weeks of production data exist
**Why parked:** Need real failure-mode data to know where LLM augmentation actually helps

### Decision matrix

| Where | LLM ROI | Effort | Cost/mo | Priority |
|---|---|---|---|---|
| **News article interpretation** | 🟢 HIGH | 1 weekend | ~$5-15 | After Month 1 obs |
| **Weekend Reflection deepening** | 🟢 HIGH | 1 day | ~$2-5 | After Month 1 obs |
| **Earnings call transcripts (NEW)** | 🟢 HIGH | 1 week | ~$10-30 | Month 3+ |
| **Multi-LLM ensemble for hard picks** (Claude+GPT+Gemini vote) | 🟡 MEDIUM | 1 week | ~$30-80 | Month 5 (per BUSINESS_PLAN) |
| **Meta-Brain Sunday digest LLM-ified** | 🟡 MEDIUM | 1 day | ~$2 | Only if users say current is robotic |
| **Scoring / pattern detection / calibration** | 🔴 LOW | — | — | Never (math beats LLMs here) |

### Why NOT a full multi-agent clone architecture

The "5 LLM agents talking to a master" pattern was considered. Rejected because:
1. Multi-LLM ENSEMBLE (3 LLMs voting on 1 question) gives 80% of the benefit at 20% of the cost
2. Multi-AGENT (5 specialized LLMs) = ~$200-500/month + brittle coordination
3. Our existing modules already act like specialized "agents" — they just communicate via files (cheap, atomic) instead of LLM API calls (expensive, fragile)
4. The agent isn't bottlenecked on intelligence — it's bottlenecked on data quality. More LLMs won't fix bad yfinance data.

### Trigger to revisit Phase 8

Revisit after one of these signals appears in production:
- ✅ User reports >30% of picks lacked critical news context the agent missed
- ✅ Earnings surprises caused >10% of losing trades in a month
- ✅ Brain stuck (no learning) for >3 weeks despite enough trades
- ✅ Sunday digest feels robotic in user's actual reading

---

## 🦉 PHASE 9 — The 7-Faculty Agent Build-Out (added 2026-05-04)

**Vision:** Build the agent like an advanced human — brain, heart, soul,
5 senses, 6th sense, curiosity. Zero emotion. Decisions from data only.

### Priority order (build the weakest faculties first)

| Priority | Faculty | What's missing | Effort | When |
|---|---|---|---|---|
| **P0** | 🦉 **Curiosity** | Module doesn't exist; ~14hr/day idle compute wasted | 1 weekend | After 4 weeks of obs data |
| **P1** | 👂 **Hearing** | News engine is regex-only, misses semantic context | 1 weekend | Month 2-3 (Phase 8 LLM) |
| **P2** | 👃 **Smell** | Reactive only; should detect danger PROACTIVELY | 1 week | Month 3 |
| **P3** | 🔮 **6th sense** | Hypothesis engine just started; needs 100+ tests run | Time, not effort | Builds with data |

### Phase 9 ship sequence

**Step 1 — Curiosity Engine (highest leverage, lowest effort)**
- New module: `src/curiosity_engine.py`
- New workflow: `.github/workflows/curiosity_hourly.yml` (every hour during idle)
- Output: `data/curiosity_journal.jsonl` — agent's self-discovered insights
- Catalog of ~30 curiosity questions to start; agent generates more over time

**Step 2 — Proactive Smell**
- Refactor `auto_pause.py` to detect danger BEFORE health degrades
- Add early-warning signals: regime shift detection, vol spike forecasting

**Step 3 — Better Hearing (LLM news, see Phase 8)**
- Already designed in Phase 8 — just renamed faculty

**Step 4 — Sharper 6th sense**
- Just keep running. More data = sharper predictions. No code needed.

### Trigger to start Phase 9

After 4 weeks of production observation, IF curiosity gap is real (i.e.,
agent has answered fewer self-questions than there are open hypotheses),
start with curiosity_engine.

### Why curiosity is P0

Every other faculty IMPROVES via curiosity:
- Curiosity tests new hypotheses → 6th sense gets sharper
- Curiosity finds losing pattern clusters → smell becomes proactive
- Curiosity studies own losses → brain calibrates better
- Curiosity narrates findings → soul/memoir gets richer

**Without curiosity, the agent is reactive forever. With it, the agent compounds.**
