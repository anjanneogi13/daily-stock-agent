# Daily Stock Agent — Work Log

Append-only history of every meaningful bug fix, feature, audit, and documentation change.

Rules:

1. Newest entries go first.
2. Include date, type, summary, tests, and follow-up.
3. Do not delete historical entries.
4. Update this file after every meaningful codebase move.
5. If architecture, roadmap, or product state changes, update `docs/PROJECT_BLUEPRINT.md`.
6. If next work changes, update `docs/NEXT_SESSION.md`.

---

## 2026-05-06 — Comprehensive audit fixes for monitoring safety

**Type:** audit / bug fix / workflow hardening / monitoring safety

**Summary:**

Performed comprehensive repo-health audit before new feature work and fixed the highest-severity issues first.

Fixed:

- Intraday monitor CSV close regression:
  - `scripts/intraday_monitor.py` now uses module `TODAY` when closing picks, so test/backfill/manual monitor runs update the same `pick_date` selected by `load_todays_picks()`.
  - Prevents repeated SL/TP alerts from leaving rows stuck as `pending`.

- Daily-picks timing hard gate:
  - `.github/workflows/daily-picks.yml` now blocks normal daily picks after 09:20 ET.
  - Manual dispatch no longer bypasses the official premarket timing gate.
  - Late runs send a missed-window Telegram alert instead of normal actionable picks.

- Stale/unverified price protection:
  - `scripts/premarket_check.py` now marks unverified prices as `👀 WATCH ONLY`.
  - Telegram daily sender does not show actionable buy instructions for watch-only picks.
  - GitHub issue formatter documents the watch-only state.

- Monitoring-only paper logging safety:
  - `main.py` no longer defaults to paper-trade logging when `TRADING_MODE` is unset.
  - Legacy local paper logging is now opt-in only with `TRADING_MODE=paper`.

- News action-window guard:
  - `src/news_signals.py` preserves `action_window`.
  - `main.py` marks intraday-news swing candidates as watch-only instead of silently presenting them as normal swing entries.
  - `src/pick_logger.py` persists `watch_only`, `watch_only_reason`, and `news_action_window`.

Added tests for:

- Missed premarket-window alert.
- Daily-picks 09:20 ET hard cutoff.
- Watch-only stale-price behavior.
- Monitoring mode paper-logging default.
- News action-window preservation and watch-only guard.
- Pick logger watch-only/news-action-window persistence.

**Tests:**

- `python3 -m pytest tests/ -q --tb=short --disable-warnings`
  - `1284 passed, 28 skipped`
- `python scripts/audit_journal_consistency.py --strict`
- `python scripts/check_enforcement_readiness.py`
- `python scripts/monitoring_readiness.py`
- `git diff --check`

**Follow-up:**

Highest-severity audit issues are fixed. Next lower-severity cleanup should address:

1. Test/data isolation for `data/learning_journal.jsonl` and related tracked data side effects.
2. Closed-status alignment between readiness scripts.
3. Documentation consistency cleanup.
4. Then resume feature roadmap with opening-range intraday scanner.

---

## 2026-05-06 — Created agent maturity tracker and intelligence roadmap

**Type:** documentation / product strategy

**Summary:**

Created `docs/AGENT_MATURITY_TRACKER.md` to preserve the May 5 trading-day analysis and track how the agent matures.

Documented:

- Premarket swing, intraday, and monster-hunt lanes.
- POWI as an older 2026-04-28 swing pick that hit `+2.0R` on 2026-05-05.
- EXPD as a valid earnings catalyst but poor intraday/swing classification case.
- GILT as a valid catalyst with speculative/pump-risk concerns.
- NET as a strong intraday opportunity detected too late.
- Daily Telegram timing and stale-price issues.
- Fundamental/P&L analysis roadmap.
- Reader/wisdom learning roadmap.
- Historical regime learning roadmap.
- Historical chart/pattern replay roadmap.
- Monster-hunt long-term compounder roadmap.

Updated:

- `docs/README.md`
- `docs/PROJECT_BLUEPRINT.md`
- `docs/NEXT_SESSION.md`

**Follow-up:**

Next implementation should start with daily-picks timing and stale-price protection before deeper intelligence features.

**Tests:**

Documentation-only change. Run markdown/file sanity and startup health before next coding task.

---

## 2026-05-06 — Reviewed 2026-05-05 pick outcomes

**Type:** monitoring / data evaluation

**Summary:**

Reviewed the 2026-05-05 agent picks and current evaluated outcomes:

- `EXPD` had a valid bullish earnings-beat catalyst but hit stop loss: `-1.0R`.
- `GILT` had a bullish contract-win catalyst and remains pending.
- `POWI` was evaluated as a strong take-profit win: `+2.0R`.

**Lesson:**

The agent is finding real catalysts, but news action windows are not yet fully connected to trade classification. Both `EXPD` and `GILT` had news classified as `intraday`, while the picks were logged as `swing`.

**Risks observed:**

- Missing company/tag metadata on 2026-05-05 picks.
- Premarket check could not verify prices and marked both picks half-size.
- Brain probability / EV fields were blank.
- Smell faculty did not flag missing verification or intraday/swing mismatch.

**Follow-up:**

Consider adding a guard or scoring adjustment so high-urgency news catalysts with `action_window=intraday` are either:

1. logged as day/intraday trades,
2. given tighter monitoring rules, or
3. penalized/blocked as swing picks unless confirmed by stronger multi-day setup.

**Tests:**

- `python scripts/audit_journal_consistency.py --strict`
- `python3 -m pytest tests/test_journal_consistency.py tests/test_signal_journal_quality.py -q --tb=short`

---

## 2026-05-05 — Signal journal quality repair

**Type:** data fix

**Summary:**

Set post-fix `vol_ratio_bucket` values for the newly repaired 2026-05-05 signal journal rows:

- `EXPD` -> `low`
- `GILT` -> `low`

Also reset full-suite evaluation side effects on those signal rows so they match the pending state in `data/picks_log.csv`.

**Tests:**

- `python3 -m pytest tests/test_signal_journal_quality.py tests/test_journal_consistency.py -q --tb=short`
- Full suite

---

## 2026-05-05 — Signal journal consistency repair

**Type:** data fix

**Summary:**

Added missing signal journal rows for post-send picks:

- `2026-05-05 EXPD`
- `2026-05-05 GILT`

**Reason:**

The post-send state commit added rows to `data/picks_log.csv` without matching rows in `data/signal_journal.jsonl`, breaking the journal consistency invariant.

**Tests:**

- `python3 -m pytest tests/test_journal_consistency.py -q --tb=short`
- Full suite

**Follow-up:**

Investigate and harden the post-send persistence path so picks cannot be persisted without matching signal journal entries.

---

## 2026-05-05 — Documentation consolidation

**Type:** docs / process

**Summary:**

Created canonical documentation structure:

- `docs/PROJECT_BLUEPRINT.md`
- `docs/WORK_LOG.md`
- `docs/NEXT_SESSION.md`
- `docs/README.md`

**Reason:**

Older docs repeated architecture, roadmap, current state, bug ledger, and next-session content.

**Follow-up:**

Keep this file updated after every bug fix, feature, audit, or process change.

---

## 2026-05-05 — LLM agent coverage and cache fix

**Commit:** `0deccc5`

**Type:** test / bug fix

**Summary:** Added `llm_agent` provider fallback/cache tests and fixed timezone-aware cache timestamps.

**Tests:** 1273 passed, 28 skipped

**CI:** green

---

## 2026-05-05 — Market news coverage

**Commit:** `5036ad0`

**Type:** test

**Summary:** Added tests for market news cache, Finnhub fetch fallbacks, Claude/Gemini parsing, and briefing assembly.

**CI:** green

---

## 2026-05-05 — Earnings analyzer coverage

**Commit:** `a1f2a70`

**Type:** test

**Summary:** Added tests for earnings cache, Finnhub fallbacks, recommendations, and composite score math.

**CI:** green

---

## 2026-05-05 — Hard blocks coverage

**Commit:** `6c4fc03`

**Type:** test

**Summary:** Added tests for hard-block gate logic and audit-log behavior.

**CI:** green

---

## 2026-05-05 — Tiered exits reserved schema

**Commit:** `c17d2dd`

**Type:** docs / product decision

**Summary:** Marked tiered TP columns as reserved schema in monitoring mode.

**CI:** green

---

## 2026-05-05 — Telegram delivery reliability

**Commit:** `aa9829f`

**Type:** bug fix

**Summary:** Daily sender marks dedup only after confirmed delivery.

**CI:** green

---

## 2026-05-05 — Daily picks persistence hardening

**Commit:** `caf5e9b`

**Type:** workflow fix

**Summary:** Daily picks workflow now recovers/persists state and fails if persistence cannot be pushed.

**CI:** green

---

## 2026-05-05 — CI audit syntax repair

**Commit:** `6dd5dd5`

**Type:** CI fix

**Summary:** Repaired full repo audit syntax/import-safety issues.

**CI:** green
