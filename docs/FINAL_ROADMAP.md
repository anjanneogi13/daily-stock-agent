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
