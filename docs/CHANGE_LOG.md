# 📜 Change Log — Permanent Timeline

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
