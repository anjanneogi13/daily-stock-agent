# 🗺️ Daily Stock Agent — Final Roadmap

**Last updated:** 2026-05-05 · monitoring-first update
**Status:** monitoring-ready · data-quality audits green · paper trading deferred

---

## 🟢 CURRENT — Phase 5: Monitoring & Stabilization

**Goal:** verify the agent in the real daily workflow before adding execution or paper trading.

This phase comes before new feature expansion.

### Monitoring plan

1. Run a **2-week observation** window in monitoring-only mode.
2. During the same period, fix remaining audit issues and complete architecture documentation.
3. Run a **second 2-week validation** window after the architecture stabilizes.
4. Only then evaluate **paper trading eligibility**.

### Paper trading eligibility

Paper trading remains deferred until post-floor data passes all gates:

| Trade type | Required success rate | Extra gate |
|---|---:|---|
| day trades | >60% | positive expectancy |
| swing trades | >66% | positive expectancy |
| monster / long holder picks | >90% | positive expectancy |

No real-money launch is planned. The agent recommends, monitors, explains, and learns.

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

### Historical May 3 stats
- Tests: 491 → 805 (+314, ZERO regressions)

### Current May 5 status
- Tests: 1245 passed, 28 skipped
- Earnings fill-rate audit: green
- Sector benchmark fill-rate audit: green
- Journal consistency: green
- Enforcement gates: waiting on post-floor sample size
- New modules: 9
- New workflows: 3 (`nightly_brain.yml`, `yearly_recap.yml`, `holiday_renewal_reminder.yml`)
- Lines of code: ~3,500 added, ~11,897 total in src/
- Health check: 10/10

---

## 🟡 NEXT — Phase 5: Observation & Polish

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

---

## 📚 PHASE 9.5 — Reader Engine (added 2026-05-04 evening)

**Vision:** Agent reads one trading/investing book per week. Extracts claims.
Tests them against own data. Promotes only what works.

### Why deferred

- Requires LLM API access (Phase 8 budget approval first)
- PDF parsing + claim extraction + classification = real engineering (2-3 weekends)
- Needs baseline performance data (4+ weeks production) to measure book impact
- Risk of poisoning codebase with bad claims if validation pipeline is rushed

### Architecture sketch

src/reader_engine.py

book_intake (PDF/EPUB/txt)
chunk_into_claims (~50-200 claims/book)
classify_claim (rule/anecdote/definition/opinion)
extract_testable_rules
submit_to_hypothesis_engine (NEVER auto-promote)
data/library/

books_read.json (consumed inventory)
claims_extracted.jsonl (every claim ever found)
claims_under_test.jsonl (validation in progress)
claims_promoted.jsonl (passed Wilson 95% CI → became wisdom)
claims_rejected.jsonl (failed validation — kept for transparency)
scripts/read_book.py BOOK.pdf .github/workflows/weekly_book_read.yml (every Sunday)

Code

### Initial reading queue (priority order)

1. **Reminiscences of a Stock Operator** (Lefèvre) — psychology baseline
2. **Trade Like a Stock Market Wizard** (Minervini) — testable entry rules
3. **Technical Analysis of the Financial Markets** (Murphy) — pattern definitions
4. **One Up On Wall Street** (Lynch) — fundamental scoring
5. **The Intelligent Investor** (Graham) — value framework (high-risk for outdated specifics)

### CRITICAL design rule

**Books PROPOSE. Data DISPOSES.**

A claim from a book is just a hypothesis. It enters `claims_under_test.jsonl`
and must pass the same Wilson 95% CI bar as any internal hypothesis before
being promoted to active wisdom. The agent does not believe Buffett, Lynch,
or Minervini — it believes its own backtested data.

### Trigger to start Phase 9.5

After Phase 9 (curiosity_engine) is live AND has run for 2+ weeks AND
LLM budget is approved (Phase 8).

---

## 🌍 PHASE 10 — Historical Regime Engine (added 2026-05-04 night)

**Vision:** The market is NEVER always in one phase. Crashes, bulls, and
stagnations alternate forever. An agent built for only one will eventually
break. Phase 10 makes the agent regime-prescient — it sees transitions
coming BEFORE they happen.

### Why this is the moat

Most trading agents fail catastrophically at regime transitions because they
were trained on one regime. 2008 was not in the 2003-2007 bull-trained models.
COVID March 2020 wiped out 70% of quant funds in 3 weeks. 1973-75 stagflation
broke every "buy the dip" model.

A regime-prescient agent flags **"today looks 78% like Sept 2007 — reducing
equity exposure, increasing defensives, will reassess in 7 days."**

This is what separated Bridgewater ($150B fund) from competitors. Ray Dalio
literally calls this *Principles of a Changing World Order* — pattern matching
500 years of empire/economic cycles to predict the next transition.

### Architecture sketch (indented code, no fences)

    src/historical_regime_engine.py
      - load_event_catalog (data/historical_events/*.json)
      - extract_present_indicators (yield_curve, credit_spreads, vix, housing)
      - score_similarity (today vs each historical event)
      - flag_top_matches (ranked by similarity %)
      - submit_to_hypothesis_engine (NEVER auto-promote — must validate)

    data/historical_events/
      crashes/
        1929_great_depression.json
        1987_black_monday.json
        2000_dotcom.json
        2008_lehman.json
        2020_covid.json
      bulls/
        1982_1987_reagan_bull.json
        1990s_dotcom_runup.json
        2009_2020_qe_bull.json
      stagnations/
        1973_1975_stagflation.json
        2000_2003_post_dotcom.json
        2015_2016_china_scare.json
      precursor_indicators.json (canonical indicator definitions)

    .github/workflows/regime_match_nightly.yml (part of nightly_conductor)

### Each event JSON shape (indented)

    {
      "event": "2008 Lehman Brothers Collapse",
      "date": "2008-09-15",
      "type": "crash",
      "duration_days": 547,
      "spx_drawdown_pct": -56.8,
      "precursors_observed": [
        {"indicator": "yield_curve_inverted", "lead_days": 720},
        {"indicator": "housing_starts_declining_3mo", "lead_days": 540},
        {"indicator": "vix_above_30_persistent", "lead_days": 90},
        {"indicator": "credit_spreads_widening", "lead_days": 180}
      ],
      "what_worked": ["short positions", "treasuries", "gold"],
      "what_failed": ["buy the dip", "growth stocks", "leverage"],
      "lessons": [
        "Credit spreads widen + housing weakens = reduce equity exposure",
        "Financial sector breakdown precedes broad market by 6-9 months",
        "Buy-the-dip stops working when liquidity vanishes"
      ],
      "recovery_pattern": "U-shaped, 5 years to new highs",
      "sources": ["When Genius Failed", "Big Short", "Too Big to Fail"]
    }

### Initial event catalog (minimum to ship Phase 10)

#### Crashes (5 events)
1. **1929 Great Depression** — fundamental shift, ended Roaring 20s
2. **1987 Black Monday** — single-day -22% (algorithmic cascade)
3. **2000 Dotcom Bust** — sector bubble (testing what was overvalued)
4. **2008 Lehman Brothers** — credit/financial crisis
5. **2020 COVID Crash** — exogenous shock (pandemic)

#### Bull cycles (4 events)
1. **1982-1987 Reagan Bull** — secular bull start
2. **1990s Dotcom Runup** — productivity boom + irrational exuberance
3. **2009-2020 QE Bull** — central bank-driven, longest in history
4. **2020-2021 Post-COVID Bull** — stimulus + reopening

#### Stagnations (4 events)
1. **1973-1975 Stagflation** — oil shock + wage-price spiral
2. **2000-2003 Post-Dotcom** — tech rebuild, broad index sideways
3. **2015-2016 China Scare** — global growth fears
4. **2018 Q4 Pivot** — Fed reversal mid-cycle

**Curation effort:** 40-80 hours for the initial 13 events. Each event needs
careful research from multiple sources (not Wikipedia copy-paste).

### CRITICAL design rule (mirrors books)

**History PROPOSES. Data DISPOSES.**

A historical pattern match is just a hypothesis. The agent does NOT blindly
trust history any more than it blindly trusts books. Every "today looks like
X" claim must:
1. Pass minimum similarity threshold (e.g. 70%+ across precursor indicators)
2. Be statistically validated against present-day forward outcomes
3. Earn weight gradually (heart enforces 5%/wk cap — no panic re-allocations)

### Trigger conditions to start Phase 10

ALL of these must be true:
- Phase 9 (curiosity_engine) live AND running 2+ weeks
- Phase 9.5 (reader_engine) live AND has ingested at least 3 books successfully
- LLM API budget approved + flowing
- 4+ months of production data exists (so similarity scoring has something to validate against)
- Founder has time for the 40-80 hour event curation work (or budget to outsource)

### Future expansion (Phase 10.5+)

- **Global events:** Japan 1990 lost decade, China 2015, EU debt crisis 2011
- **Sector rotations:** energy boom/busts, tech cycles, biotech waves
- **Yield-driven regimes:** rising rates (1979-81), zero rates (2009-21), normalization
- **Geopolitical patterns:** wars, oil shocks, currency crises

### Vision quote (Anjan, 2026-05-04 night)

> *"Market is not always in one phase. Agent should learn why crashes happened,
> why bulls happened, why stagnations happened — then predict transitions.
> This will help agent in the picks in future."*

