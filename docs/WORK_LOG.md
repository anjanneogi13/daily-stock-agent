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
