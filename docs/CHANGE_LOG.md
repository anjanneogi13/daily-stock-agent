# Change Log

Historical note:

This file is preserved as an older append-only timeline.

Active work history should now be recorded in:

- `docs/WORK_LOG.md`

Current handoff and next work should be recorded in:

- `docs/NEXT_SESSION.md`

Current architecture/status should be recorded in:

- `docs/PROJECT_BLUEPRINT.md`

Future planning should be recorded under:

- `docs/planning/`

---

## 📜 Original Change Log — Permanent Timeline

This file records every meaningful change to the agent.
**Append-only.** Newest entries on top. Never edit history.

Format:
YYYY-MM-DD — short title
WHAT: what changed
WHY: why we changed it
HOW: files touched, approach
IMPACT: measurable change observed
COMMIT: hash + branch
Code

---

## 2026-05-04 (night) — Historical Regime Engine vision documented (Phase 10)

- **WHAT:**
  1. NEXT_SESSION.md: full rewrite — recap of today 3 commits + Phase 9/9.5/10 deferred features + updated homework + new opener
  2. AGENT_PHILOSOPHY.md: 6th sense extended to include historical regime study (commit pending in this same session)
  3. ARCHITECTURE.md Section 8: regime-prescience added as endgame for the 6th sense (commit pending)
  4. FINAL_ROADMAP.md: Phase 10 (Historical Regime Engine) appended (commit pending)

- **WHY:**
  - Founder vision (2026-05-04 night): "Market is not always in one phase. Agent should learn why crashes happened (1929, 1987, 2000, 2008, 2020), why bulls happened (1982-87, 90s, 2009-20), why stagnations happened (1973-75, 2000-03, 2015-16) — then predict transitions."
  - Most agents fail catastrophically at regime transitions because they were trained on one regime.
  - A regime-prescient agent flags "today looks 78% like Sept 2007" and adjusts BEFORE the crash.
  - This is genuinely the holy grail — what separated Bridgewater from every other fund (Dalio Principles of a Changing World Order).

- **CRITICAL design principles:**
  - History PROPOSES. Data DISPOSES. (same rule as books: pattern-match candidates must be statistically validated, not blindly trusted)
  - Catalog must include ALL 3 regime types: crashes, bulls, stagnations (not just crashes)
  - Each event needs precursor indicators (yield curve, credit spreads, VIX, housing, etc) — not just "what happened"
  - Pattern-matching today vs history runs nightly as part of the 6th sense

- **NOT shipped today:**
  - historical_regime_engine.py — major effort (40-80 hours of event curation alone)
  - Event JSON catalog (data/historical_events/) — needs careful research, not Wikipedia copy
  - Phase 10 starts only after Phase 9 (curiosity) + Phase 9.5 (reader) prove the validation pipeline works

- **WHY DEFER:**
  - Cognitive load — 4 commits today is already a lot
  - Vision needs to settle in writing before implementation
  - Phase 10 depends on Phase 9.5 reader_engine to ingest historical books (Reminiscences, When Genius Failed, Big Short)
  - No baseline production data yet — wait 4 weeks before adding more vision modules

- **COMMIT:** see git log (this session = 81274d8 + several follow-ups)

---

## 2026-05-04 (evening) — Reader vision added (curiosity mode 10b)

- **WHAT:**
  1. AGENT_PHILOSOPHY.md: Curiosity faculty extended with TWO modes
     - 10a: inward curiosity (studies itself) — already planned
     - 10b: outward curiosity (READS BOOKS) — NEW vision
  2. FINAL_ROADMAP.md: Phase 9.5 (Reader Engine) appended

- **WHY:**
  - Founder vision: "Agent must be curious reader, learning from books on
    trading/investing/finance, adding learnings to codebase if they help."
  - Centuries of trading wisdom exists in books — humans can't read it all,
    but an agent can (1 book/week × forever).

- **CRITICAL design rule encoded:**
  - Books PROPOSE. Data DISPOSES.
  - No claim from any book auto-promotes to wisdom.
  - Every claim must pass Wilson 95% CI on OUR data first.
  - Prevents poisoning codebase with outdated/wrong rules.

- **NOT shipped today:**
  - reader_engine.py — needs LLM access + 2-3 weekends + baseline data
  - Phase 9.5 starts only after Phase 9 (curiosity_engine) + 2 weeks live

- **COMMIT:** docs only

---

## 2026-05-04 (afternoon) — 7-Faculty Agent Vision documented

- **WHAT:**
  1. NEW DOC: `docs/AGENT_PHILOSOPHY.md` — canonical vision (7 faculties + zero emotion)
  2. ARCHITECTURE.md: added Section 8 (7-Faculty Agent Model with module mapping)
  3. FINAL_ROADMAP.md: appended Phase 9 (build curiosity_engine + sharpen weak faculties)

- **WHY:**
  - Founder vision: "Build agent like advanced human — brain, heart, soul, 5 senses,
    6th sense, curiosity. But zero emotion. Decisions from data only."
  - Project needed ONE canonical doc explaining what makes this agent different
  - Roadmap needed reframing around the 7 faculties so weak ones get prioritized

- **HOW (docs only — no code):**
  - Mapped existing 78 modules onto the 7-faculty model
  - Identified 3 weakest faculties: hearing (regex), smell (reactive), curiosity (missing)
  - Encoded the 7 design rules (no emotion, glass box, honest, curiosity > reactivity, etc)

- **IMPACT:**
  - Future-Claude has clear vision doc to read
  - Future-Anjan has tagline material ("7 faculties. 1 mission. Zero emotion.")
  - Phase 9 roadmap = build curiosity_engine.py first (highest leverage)

- **NOT shipped today (intentional):**
  - curiosity_engine.py itself — wait until 4 weeks of obs data to know what to be curious about
  - Hearing/smell improvements — Phase 8/9, not today

- **COMMIT:** see git log

---

## 2026-05-04 — Metadata tagging fix + agent memoir + stuck-warning fix

- **WHAT:**
  1. `src/signal_journal.build_signals()` now defensive across field-naming conventions
  2. `src/meta_brain.detect_stuck_areas()` now requires system age ≥ stuck_days
  3. NEW MODULE: `src/agent_memoir.py` — agent's persistent self-portrait
  4. Memoir wired into `nightly_conductor.py` as Step 8
  5. Test `test_run_nightly_executes_all_steps_with_isolation` updated 7 → 8 steps

- **WHY:**
  - First weekly hypothesis report (2026-05-03) showed 100% of buckets = "unknown"
  - Brain literally couldn't learn — every signal looked identical to it
  - Stuck-warning fired on day 1 (false alarm — system too young to be stuck)
  - Founder insight: "Agent should not forget its mistakes, learnings, or task"

- **HOW:**
  - `build_signals` tries multiple field-name aliases for each signal
    (composite/composite_score/score, vol_ratio top-level + scores, etc)
  - `detect_stuck_areas` accepts `system_age_days`; returns not-stuck early if too young
  - `agent_memoir` reads picks_log + learning_journal, writes narrated JSON memoir
  - Memoir runs as final step of every nightly brain cycle

- **IMPACT (verified before commit):**
  - Smoke test: `build_signals` now produces real buckets, not "unknown"
  - Smoke test: nightly conductor 8/8 steps green
  - Test suite: 805 passing (was 805, +1 new test path covered)
  - Memoir file: `data/agent_memoir.json` writes successfully

- **EXPECTED IMPACT (next 7 days):**
  - Sunday May 10 hypothesis report: real bucket distinctions, not all "unknown"
  - Monday May 11 Self-Improvement Report: no false stuck warning
  - Agent gains persistent identity via nightly-rewritten memoir

- **COMMIT:** see `git log` for hash on `main`

---

## 2026-05-03 — The Big Sunday Sprint (Ideas 1-4 + calendar + bonus)

- **WHAT:** Shipped 20 features (T34 → T52 + T51b)
  - Self-improving brain (`nightly_conductor.py`, `meta_brain.py`)
  - Architecture doc, integration audit (8/8 gaps closed)
  - Layman Telegram (5 send_layman_*.py scripts)
  - Calendar awareness with 3-year buffer + 3-layer renewal reminder
- **WHY:** Foundation week — agent needed to be self-improving and human-readable before going live
- **HOW:** ~3,500 lines added across 9 new modules + 3 new workflows
- **IMPACT:** Tests 491 → 805 (+314, ZERO regressions). Health 10/10.
- **COMMIT:** Multiple commits Sunday May 3 (a32f71d → 1fade14)

---

*Older history lives in git log + `docs/sessions/` chat handoffs.*
