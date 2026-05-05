# 🗺 FUTURE ROADMAP — Prioritized Backlog

> **As of:** 2026-05-05 (post data-quality/readiness fixes)
> **Status:** 1221 tests passing, 28 skipped. Core faculties are live; strategic regime, curiosity, and reader extensions remain planned.
> **Discipline:** One feature per week. Each PR <=1500 lines, fully tested.

---

## 6-Week Sequence

| Week | Phase | Feature | Effort | Unblocks |
|------|-------|---------|--------|----------|
| 1 | 5.5 | Backtester hardening | partial already exists | Phases 9, 9.5, 10 |
| 2 | — | Faculty integration test expansion | partial already exists | All future changes |
| 3 | — | Hearing LLM upgrade | 4-6 days | Better news scoring |
| 4 | 9 | Curiosity inward | 3-5 days | Self-debug loop |
| 5 | 9.5 | Reader engine | 5-7 days | Outward learning |
| 6 | 10 | Historical regime engine | 1.5-2 wks | Strategic 6th sense |

---

## Week 1 — Phase 5.5 BACKTESTER hardening (foundation exists)

**Why first:** 4 of next 5 features depend on replaying agent vs historical data. Without this, every new feature is unfalsifiable.

- Existing package: `src/backtester/` (`engine.py`, `metrics.py`, `outcome_simulator.py`, `pit_data.py`)
- Harden replay mode for `news_signals.py` + `parallel_scorer.py`
- CLI: python -m scripts.backtest --start 2025-08-01 --end 2026-04-30
- Output: data/backtests/<run_id>/ with picks, evals, equity curve
- Acceptance: reproduce last week's actual picks +/- 5%, runs <60s for 1mo, and is covered by tests

## Week 2 — Faculty integration test expansion

**Why second:** Locks in the 6 May 4 fixes + prevents same-pattern regressions.

- Existing: `tests/test_faculty_integration.py`
- Expand into one suite per faculty, especially undercovered risk/gate paths
- Bonus: scripts/audit_faculty_reachability.py = 5th audit dashboard
  Walk import graph, prove each faculty's output reaches a consumer.
  Would have caught 4 of 6 May 4 critical bugs automatically.

## Week 3 — Hearing LLM upgrade

- Route headlines through llm_agent.py for sentiment + materiality
- Cache in data/llm_cache/ (already gitignored)
- ~$0.001/headline gpt-4o-mini, ~$1.50/mo total
- Feature-flagged with keyword fallback

## Week 4 — Phase 9 CURIOSITY (inward)

- New: src/curiosity_engine.py
- Reads journals, asks "what surprised me?"
- Daily Telegram + data/curiosity_findings.jsonl
- Depends on backtester (validation harness)

## Week 5 — Phase 9.5 READER (outward)

- New: src/reader_engine.py
- Sources: SEC EDGAR (free), FRED, earnings calendar
- Validates hypothesis_engine claims against reality
- Risk: SEC rate limits, 10-K parsing — plan 1-2 day buffer

## Week 6 — Phase 10 Historical regime engine

- New: src/historical_regime_engine.py
- 13+ events: 2008 GFC, 2020 COVID, 2022 hikes, dot-com, etc.
- Per-event: SPY %, VIX, sector rotation, what worked/failed
- At pick-time: "current regime most similar to X" -> apply lessons

---

## After Week 6 (planned)

### 7. Two-repo split (1 day)
- daily-stock-agent-engine (public) = pure code, free CI
- daily-stock-agent (private) = data, docs, secrets, history
- Engine = git submodule of private repo
- Solves: cost vs alpha-leakage tradeoff

### 8. Competitive moat doc (2 hrs)
Honest answer: judgment + data + discipline. Not the code.

### 9. Cache llm_cache + stock_stats in workflows (2 hrs)
Currently regenerated every run. Easy fix.

---

## Discipline Rules

1. One PR per feature. Never bundle. <=1500 lines.
2. Tests before merge. New feature must add >=5 tests.
3. All audit dashboards stay green every PR.
4. No silent failure. Either work or raise loudly.
5. Document the why in CHANGES_<date>.md.

---

## Success in 6 weeks

- 1221 -> ~1500 tests
- 81 -> ~88 modules
- Backtester runs nightly, posts 30-day stats
- Curiosity surfaces 1-3 findings/day
- Hearing scores news with LLM (~$2/mo)
- Reader validates ~5 hypotheses/week
- 13-event regime catalog with similarity scoring

**Result:** an agent that doesn't just trade — it learns, self-debugs, asks questions.
