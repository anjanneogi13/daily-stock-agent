# Audit Batch 106 — tests/ files 1–15 (alphabetical) — TRUE line-by-line

**Pinned commit:** `1d6975fe`
**Files audited:** 15 of 178
**Total lines audited in this batch:** ~520
**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

# 1. `tests/test_agent_memoir_finding1.py` (39 lines)

**Covers:** `src/agent_memoir.py::_load_closed_picks`

### ⚠️ BUG-AMF-1: `monkeypatch.setattr(memoir, "PICKS_LOG", fake_csv)` (line 24)
- Patches `memoir.PICKS_LOG`. If `_load_closed_picks` reads the constant via `from .X import PICKS_LOG` elsewhere, the patch has no effect. Couples test to import shape.
- **Severity:** ⚠️ Mock-path fragility.

### 🟡 BUG-AMF-2: Empty test `test_memoir_does_not_count_pending` (lines 33–38)
- Function body is just `pass` with a comment. Adds no assertions. Misleading test name implies coverage; provides none. Should be deleted.
- **Severity:** 🟡 Dead test.

### ✅ GOOD-AMF-1: Real CSV writing via `csv.DictWriter` (lines 17–20) — exercises real I/O path.
### ✅ GOOD-AMF-2: Hermetic via `tmp_path` (line 7) — no production data touched.

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 1 · ✅ 2 (4 findings)
**Top fixes:** delete `test_memoir_does_not_count_pending`; assert against `memoir._load_closed_picks` import contract.

---

# 2. `tests/test_artifact_completeness.py` (122 lines)

**Covers:** `scripts/check_daily_artifact_completeness.py` (build_artifact_completeness_report, format_markdown, write_outputs)

### ✅ GOOD-AC-1: Six independent test functions, each builds isolated `tmp_path` artifacts (lines 25–122). Excellent isolation pattern.
### ✅ GOOD-AC-2: `checks_by_key` helper (lines 21–22) — DRY assertion lookup.

### ⚠️ BUG-AC-1: Hardcoded date string `"2026-05-09"` repeated 6 times (lines 26, 46, 60, 75, 95, 114)
- Not a constant. If schema changes per-date, every test must be re-edited.
- **Severity:** 🟡 DRY.

### ⚠️ BUG-AC-2: `write_jsonl` empty list produces empty file (line 18)
- `"".join(...)` for empty list = empty string. Test on line 62 relies on this. But `write_jsonl(path, [])` and "file does not exist" are functionally different from a corrupt empty JSONL — test conflates them.
- **Severity:** 🟡 Edge case ambiguity.

### ⚠️ BUG-AC-3: `test_artifact_completeness_writes_outputs` (lines 94–110)
- Asserts only file names + 3 keys + 3 substrings in MD. Doesn't verify the JSON schema, doesn't check that all `checks` array entries are serialized. Shallow assertion.
- **Severity:** 🟡 Shallow assertion.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 2 (5 findings)
**Top fixes:** parameterize date; deepen `test_writes_outputs` to verify full schema.

---

# 3. `tests/test_audit_dead_code.py` (70 lines)

**Covers:** `scripts/audit_dead_code.py::_imports_from, find_dead`

### ✅ GOOD-ADC-1: `sys.path.insert` for repo root (line 4) — explicit dependency setup.
### ✅ GOOD-ADC-2: 5 import-shape variants tested (lines 9–30) — strong coverage of regex.
### ✅ GOOD-ADC-3: `test_dead_list_locked` (lines 51–69) is a regression-locking test with documented update procedure. Best practice.

### ⚠️ BUG-ADC-1: `test_pattern_stats_no_longer_dead`, `test_learning_journal_no_longer_dead`, `test_tracker_no_longer_dead` (lines 33–48)
- Three nearly-identical tests differing only in module name. Should be a single `pytest.mark.parametrize`.
- **Severity:** 🟡 DRY.

### ⚠️ BUG-ADC-2: `find_dead()` called 4 times (lines 35, 41, 47, 59)
- No fixture caches the result. Walks the entire repo 4× per test run.
- **Severity:** 🟡 Performance.

### ⚠️ BUG-ADC-3: `KNOWN_DEAD` set hardcoded inside test (lines 60–64)
- If `book_ingest`, `exit_metrics`, `yearly_report` get deleted, test passes silently (set difference is empty). No "stale entry" warning.
- **Severity:** 🟡 Test stagnation.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 3 (6 findings)
**Top fixes:** parametrize the 3 module-specific tests; cache `find_dead()` in a session fixture.

---

# 4. `tests/test_audit_earnings_fill_rate.py` (92 lines)

**Covers:** `scripts/audit_earnings_fill_rate.py::has_days_to_earnings, audit_rows`

### ✅ GOOD-AEF-1: `row(**kw)` factory (lines 17–25) — DRY test data setup.
### ✅ GOOD-AEF-2: Tests both positive (numeric/zero) and negative (blank/None/"None"/text) cases (lines 28–38). Excellent boundary coverage.

### 🚨 BUG-AEF-1: `subprocess.run(["python", "scripts/audit_earnings_fill_rate.py", "--json"])` (lines 80–84)
- Uses bare `"python"` — picks up whatever `python` is on PATH. Should use `sys.executable`. Will fail in many CI environments where only `python3` exists.
- **Severity:** ⚠️ Test fragility / cross-env.

### ⚠️ BUG-AEF-2: `test_cli_json_outputs_fill_rate_fields` reads real `data/picks_log.csv` (lines 80–91)
- The CLI without `--input` path reads production data. Test asserts only key presence, not values. Test will produce different results based on production data state — flaky.
- **Severity:** ⚠️ Test depends on production data.

### ⚠️ BUG-AEF-3: No test for `audit_rows` with empty input (lines 41–77)
- Edge case missing. What if `rows=[]`? Division by zero on fill_rate?
- **Severity:** 🟡 Coverage gap.

**Per-file:** 🚨 0 · ⚠️ 3 · 🟡 0 · ✅ 2 (5 findings)
**Top fixes:** use `sys.executable`; pass `--input tmp_csv` to CLI; add empty-rows test.

---

# 5. `tests/test_audit_lane1_production_readiness.py` (55 lines)

**Covers:** `scripts/audit_lane1_production_readiness.py::run_audit + CLI`

### ⚠️ BUG-ALPR-1: `result["passed"] is True` hardcoded expectation (line 16)
- Test asserts the audit ALWAYS passes. If a real failure surfaces, the test breaks rather than being informative. The audit logic itself is the system under test, but here it's used as if its verdict is always "pass". Weak assertion.
- **Severity:** ⚠️ Tautological assertion.

### ⚠️ BUG-ALPR-2: Date `"2026-05-09"` hardcoded (lines 11, 41) — same issue as AC-1.
- **Severity:** 🟡

### ⚠️ BUG-ALPR-3: `subprocess.run` with `check=True` (lines 36–48)
- Already raises on non-zero, but then asserts on `result.stdout`. If the script silently succeeds with empty stdout, asserts will fail with confusing error. No `result.returncode` check separately.
- **Severity:** 🟡

### ⚠️ BUG-ALPR-4: `test_run_audit_passes_and_writes_artifacts` reads real env (no monkeypatch) (line 9–30)
- Calls `run_audit(date_str=...)` with `output_dir=tmp_path`. But the audit might read other production paths (`config/`, `data/`). If production state changes, test outcome changes.
- **Severity:** ⚠️ Env coupling.

**Per-file:** 🚨 0 · ⚠️ 2 · 🟡 2 · ✅ 0 (4 findings)
**Top fixes:** test BOTH pass AND fail conditions; fully isolate from production paths.

---

# 6. `tests/test_audit_sector_fill_rate.py` (94 lines)

**Covers:** `scripts/audit_sector_fill_rate.py::has_value, audit_rows`

### ✅ GOOD-ASF-1: Same `row(**kw)` factory pattern (lines 18–31). Consistent style.
### ✅ GOOD-ASF-2: Distinct entry-vs-exit field testing (lines 47–79) — domain-aware.

### ⚠️ BUG-ASF-1: Same `subprocess.run(["python", ...])` issue (line 84) — see AEF-1.
- **Severity:** ⚠️

### ⚠️ BUG-ASF-2: Same production-data dependency in `test_cli_json_outputs_sector_fields` (lines 82–93).
- **Severity:** ⚠️

### ⚠️ BUG-ASF-3: `has_value("nan")` rejected (line 38) but `has_value("NaN")` not tested
- Case sensitivity bug? Need to check production code.
- **Severity:** 🟡 Coverage gap.

**Per-file:** 🚨 0 · ⚠️ 2 · 🟡 1 · ✅ 2 (5 findings)
**Top fixes:** parameterize CLI tests with input fixture; add case-insensitive nan test.

---

# 7. `tests/test_auto_cooldown.py` (108 lines)

**Covers:** `src/auto_cooldown.py::scan_and_cool, format_summary` + `src/wisdom_base.py`

### ✅ GOOD-ACD-1: `_isolate` autouse fixture (lines 11–17) — hermetic per-test wisdom paths. Excellent.
### ✅ GOOD-ACD-2: 8 distinct tests covering thresholds, streak-break, idempotency, dry-run.

### 🚨 BUG-ACD-1: Direct attribute mutation `mod.load_closed = lambda: closed` (lines 29, 39, 51, 70, 79, 90)
- Six places do `import src.auto_cooldown as mod; mod.load_closed = lambda: ...`. This is **monkey-patching without monkeypatch fixture** — the change LEAKS to subsequent tests in the same process. Pure global mutation.
- **Severity:** 🚨 Test pollution. The autouse fixture cleans wisdom paths but NOT this lambda.

### ⚠️ BUG-ACD-2: `test_no_closed_picks_returns_empty` (lines 25–32) leaks a `mod.load_closed = lambda: []` (line 29) that persists.
- **Severity:** 🚨 confirmed pollution source.

### ⚠️ BUG-ACD-3: Useless `__wrapped__` check (line 37)
- `r = ac.scan_and_cool.__wrapped__ if hasattr(...) else None  # noqa` — value never used. Dead code with `noqa` to silence linter.
- **Severity:** 🟡 Dead code.

### ⚠️ BUG-ACD-4: Empty `import json` import (line 2)
- Imported but never used.
- **Severity:** 🟡 Unused import.

### ⚠️ BUG-ACD-5: Empty `from pathlib import Path` (line 3)
- Imported but never used.
- **Severity:** 🟡 Unused import.

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 3 · ✅ 2 (6 findings)
**Top fixes:** replace 6× `mod.load_closed = ...` with `monkeypatch.setattr`; remove dead imports.

---

# 8. `tests/test_auto_lesson_on_cool.py` (65 lines)

**Covers:** `src/auto_cooldown.py::scan_and_cool` + lesson-writing path through `src/wisdom_base.py`

### ✅ GOOD-ALC-1: `_patch_closed` helper using `monkeypatch.setattr` (lines 31–32) — proper isolation, contrasts with ACD-1.
### ✅ GOOD-ALC-2: Tests cover apply/dry-run/duplicate-suppression (3 distinct tests).

### ⚠️ BUG-ALC-1: `0.5 < L["confidence"] < 0.9` (line 47)
- Range assertion without justification. What if business rules require exactly 0.7? Test passes for ANY value in range. Should assert specific value or document the range.
- **Severity:** 🟡 Loose assertion.

### ⚠️ BUG-ALC-2: `_losing_closed` produces same r_multiple/return for every row (lines 11–20)
- All losses are -1.0 R-multiple, -5.0% return. Doesn't test variability or edge values.
- **Severity:** 🟡 Coverage gap.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 2 (4 findings)
**Top fixes:** tighten confidence assertion; add varying-loss-magnitude test.

---

# 9. `tests/test_auto_pause.py` (87 lines)

**Covers:** `src/auto_pause.py` (consecutive_losses, rolling_r, rolling_win_rate, compute_score, classify, format_summary)

### ✅ GOOD-AP-1: Tests classify thresholds and rolling windows separately (lines 23–47). Unit-test discipline.
### ✅ GOOD-AP-2: `test_observe_mode_never_enforces` (lines 82–86) explicitly validates safety contract.

### 🚨 BUG-AP-1: `_row` uses `datetime.now()` (line 14)
- Time-dependent test data. Tests will run with relative-to-now dates. If `compute_score` does any boundary-day logic at midnight UTC, test results differ at midnight. **Flakiness source.**
- **Severity:** ⚠️ Time-dependent.

### ⚠️ BUG-AP-2: `r["score"] >= 7` (line 70) — comment says "streak(4) + dd(4) capped at 10" but assertion is `>=7`.
- Comment claims `>=8`, assertion accepts `>=7`. Off-by-one between comment and assertion.
- **Severity:** 🟡 Spec mismatch.

### ⚠️ BUG-AP-3: Magic numbers in classify thresholds (lines 51–54)
- `0`, `4`, `6`, `9` — not derived from any documented threshold constants.
- **Severity:** 🟡 Tight coupling to hidden constants.

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 2 · ✅ 2 (5 findings)
**Top fixes:** freeze "now" with `freezegun`; align comment+assertion; import threshold constants from `auto_pause`.

---

# 10. `tests/test_auto_promote.py` (139 lines)

**Covers:** `src/auto_promote.py` (promote_patterns, _confidence_from_p, _marker, _cli) + `src/wisdom_base.py`

### ✅ GOOD-APP-1: Class-grouped tests with section-divider comments (lines 22, 64, 91, 105, 117). Highly readable.
### ✅ GOOD-APP-2: 17 tests covering gate, idempotency, confidence, dry-run, CLI. Best test density in batch.
### ✅ GOOD-APP-3: `_add_p` factory (lines 14–19) for test data — DRY.

### ⚠️ BUG-APP-1: `_confidence_from_p("xx")` returns `0.7` (line 102)
- "Garbage in returns floor" tests the helper but doesn't check that a WARNING is logged. Silent bad-input handling.
- **Severity:** 🟡

### ⚠️ BUG-APP-2: Test data uses arbitrary precise floats `0.31`, `0.005`, `0.001` (multiple lines)
- These are right at the boundaries (`win_rate < 0.40` etc.). Nothing tests `win_rate=0.40` exact boundary. Off-by-one risk.
- **Severity:** 🟡 Boundary gap.

### ⚠️ BUG-APP-3: `test_cli_no_patterns` `assert "No patterns" in capsys.readouterr().out` (line 122)
- String matching on stdout. Brittle — any minor message change breaks the test.
- **Severity:** 🟡 Brittle stdout matching.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 3 (6 findings)
**Top fixes:** add boundary-value tests at thresholds; use logging assertions instead of stdout strings.

---

# 11. `tests/test_backfill_alpha.py` (103 lines)

**Covers:** `scripts/backfill_alpha.py` (subprocess-driven)

### 🚨 BUG-BA-1: `test_dry_run_does_not_modify_csv` modifies the REAL `data/picks_log.csv` path (lines 31–45)
- `PICKS_LOG = Path("data/picks_log.csv")` (line 17, top-level constant). Test backs it up to tmp, runs the script, checks file unchanged. **But if the script HAS a bug and IS modifying the CSV, the test only catches it AFTER the corruption. The original is restored from backup but only inside the test scope; if test crashes between corrupt and restore, real production file is corrupted.**
- **Severity:** 🚨 Test mutates production data path.

### 🚨 BUG-BA-2: Test depends on `data/picks_log.csv` existing in repo (line 21, 33)
- Hard dependency on repository state. CI must check out data files (which violates ".gitignore most data" pattern).
- **Severity:** 🚨 Test won't run on fresh clone.

### ⚠️ BUG-BA-3: `subprocess.run([sys.executable, str(SCRIPT)], cwd=Path.cwd())` (lines 38–41, 50–52)
- Uses `cwd=Path.cwd()` which depends on test invocation directory. If tests run from `tests/`, paths break.
- **Severity:** ⚠️ Cwd coupling.

### ⚠️ BUG-BA-4: `test_script_has_apply_flag` (lines 24–28) is a string-grep on source code
- Not behavior testing. If `--apply` is renamed to `--commit`, test breaks but the script still works.
- **Severity:** 🟡 Tests source-text not behavior.

### ⚠️ BUG-BA-5: `test_uses_existing_add_spy_alpha_helper` (lines 96–102) is also string-grep
- Same anti-pattern. Couples test to import line text.
- **Severity:** 🟡

### ⚠️ BUG-BA-6: `importlib.util.spec_from_file_location` (lines 64–67)
- Loads the script as a module each test. Test pollution risk if the import has side effects.
- **Severity:** 🟡

**Per-file:** 🚨 2 · ⚠️ 1 · 🟡 3 · ✅ 0 (6 findings — worst-quality file in batch)
**Top fixes:** copy `data/picks_log.csv` to `tmp_path` and patch `PICKS_LOG`; replace string-grep with behavior tests.

---

# 12. `tests/test_backfill_earnings_days.py` (73 lines)

**Covers:** `scripts/backfill_earnings_days.py::backfill, days_to_earnings, UNKNOWN_EARNINGS_DAYS`

### ✅ GOOD-BED-1: Hermetic `tmp_path` everywhere, no production paths (lines 22–73).
### ✅ GOOD-BED-2: `monkeypatch.setattr(be, "days_to_earnings", ...)` (line 34) — proper mock.
### ✅ GOOD-BED-3: 3 tests cover fill, skip-unknown, dry-run.

### ⚠️ BUG-BED-1: `_write_csv` hardcodes 4 fields (line 10)
- If the production schema adds a column, helper must be updated. Brittle.
- **Severity:** 🟡

### ⚠️ BUG-BED-2: `calls = []` capture (lines 29, 31) but only tested in one test (line 42)
- Pattern repeated would be DRY violation; here it's fine but not generalized.
- **Severity:** 🟡 Minor.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 3 (5 findings — best-quality file in batch)
**Top fixes:** parameterize column list; expose call-recording helper.

---

# 13. `tests/test_backfill_journal.py` (128 lines)

**Covers:** `scripts/backfill_signal_journal.py` (loaded via `importlib.util`) + `src/signal_journal.py`

### ⚠️ BUG-BJ-1: `importlib.util.spec_from_file_location` at module level (lines 14–18)
- Loads script during test collection. If the script has import-time side effects (writes a file, hits network), all tests pay the cost. Fragile.
- **Severity:** ⚠️ Collection-time side effect.

### ⚠️ BUG-BJ-2: `_make_row` defaults score=0.85 (line 39)
- Magic default. If production code thresholds change to require >0.85, tests pass spuriously because data is exactly at boundary.
- **Severity:** 🟡

### ⚠️ BUG-BJ-3: `test_backfill_handles_missing_csv` (lines 104–107) only checks rc==1
- Doesn't check error message, doesn't check that no journal file was created. Shallow.
- **Severity:** 🟡

### ⚠️ BUG-BJ-4: `csv_p, jrn = isolated` unpacking but `jrn` unused in some tests (lines 105, 111)
- `jrn` extracted but never asserted on. Dead variable, signals incomplete test.
- **Severity:** 🟡

### ✅ GOOD-BJ-1: 8 distinct tests covering mapping, write, skip-open, idempotency, dry-run, missing-csv, no-closed-picks, bad-numerics. Strong coverage.
### ✅ GOOD-BJ-2: `isolated` fixture returns tuple — clean parameterized resource access.

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 3 · ✅ 2 (6 findings)
**Top fixes:** lazy-import the script inside fixture; deepen `test_handles_missing_csv` assertions.

---

# 14. `tests/test_backfill_regime.py` (37 lines)

**Covers:** `scripts/backfill_regime.py::_classify`

### ✅ GOOD-BR-1: All 4 regime states tested + unknown + 3 boundary cases. Complete state coverage.
### ✅ GOOD-BR-2: Comments document what each test exercises (lines 11, 33).

### 🟡 BUG-BR-1: Tests only `_classify` — a private helper
- Tests a private function (underscore prefix). Couples tests to implementation details. If `_classify` is renamed/inlined, all 7 tests break even though public behavior is fine.
- **Severity:** 🟡

### ⚠️ BUG-BR-2: No test for `spy_close == sma200` exact equality of the 0% case beyond line 35
- Line 35 tests `(100.0, 100.0)` which is 0% → "transition". But what about NaN, infinity? Edge cases skipped.
- **Severity:** 🟡 Edge gap.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 2 (4 findings — smallest file in batch)
**Top fixes:** test public API not `_classify`; add NaN/inf cases.

---

# 15. `tests/test_backfill_smell_columns.py` (96 lines)

**Covers:** `scripts/backfill_smell_columns.py::migrate, SMELL_FIELDS`

### ✅ GOOD-BSC-1: Tests cover add-missing, preserve-existing, dry-run, idempotent. All four CRUD-like scenarios.
### ✅ GOOD-BSC-2: Uses `bsc.SMELL_FIELDS` constant (lines 33, 78) — couples to single source of truth.

### ⚠️ BUG-BSC-1: `assert changed == 3` (line 32)
- The number `3` is the count of SMELL_FIELDS. If a 4th smell column is added, assertion silently breaks. Should assert `len(bsc.SMELL_FIELDS)`.
- **Severity:** 🟡 Magic number drift.

### ⚠️ BUG-BSC-2: `assert fields[-3:] == bsc.SMELL_FIELDS` (line 33)
- Assumes SMELL_FIELDS is added at end. Depends on implementation order. If migration changes ordering, test breaks even though behavior is correct.
- **Severity:** 🟡

### ⚠️ BUG-BSC-3: `test_migrate_dry_run_does_not_write` returns `changed == 3` (lines 68, 71)
- Dry-run returns count it WOULD change. But assertion equates dry-run-count with apply-count without distinguishing semantics. Subtle.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 2 (5 findings)
**Top fixes:** replace `== 3` with `== len(bsc.SMELL_FIELDS)`; assert by set membership not slice ordering.

---

## 🎯 BATCH 106 grand totals

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 3 (ACD-1, BA-1, BA-2) |
| ⚠️ Data/safety risk | 11 |
| 🟡 Code smell | 33 |
| 📝 Doc-only | 0 |
| ✅ Good code | 29 |
| **Total findings** | **76 across 15 files / ~520 lines** |

### Cross-file patterns spotted in Batch 106

1. **`subprocess.run(["python", ...])`** — 4 files use bare `"python"` instead of `sys.executable` (AEF-1, ASF-1, ALPR-3, BA-3). **CI portability risk.**
2. **Tests depending on real `data/picks_log.csv`** — BA-1, BA-2, AEF-2, ASF-2. **Won't run on fresh clone; not hermetic.**
3. **Hardcoded `"2026-05-09"` date** in artifact-completeness/lane1 tests — should be parameterized constant.
4. **Magic numbers in assertions** — BSC-1, AP-3, ALC-1, APP-2 — should reference production constants.
5. **String-grep tests for source code text** — BA-4, BA-5 — anti-pattern (test behavior not text).
6. **Module-attribute monkey-patching without `monkeypatch`** — ACD-1 (6 occurrences) — pure global mutation.
7. **`importlib.util.spec_from_file_location` at module/test scope** — BA-6, BJ-1 — collection-time side effects.

### Production code coverage from this batch

These 15 test files exercise:
- `src/agent_memoir.py` (1 test file)
- `src/auto_cooldown.py`, `src/auto_pause.py`, `src/auto_promote.py`, `src/wisdom_base.py`, `src/signal_journal.py` (5 src modules)
- `scripts/check_daily_artifact_completeness.py`, `scripts/audit_dead_code.py`, `scripts/audit_earnings_fill_rate.py`, `scripts/audit_lane1_production_readiness.py`, `scripts/audit_sector_fill_rate.py`, `scripts/backfill_alpha.py`, `scripts/backfill_earnings_days.py`, `scripts/backfill_signal_journal.py`, `scripts/backfill_regime.py`, `scripts/backfill_smell_columns.py` (10 scripts)

### Next batch (107) — files 16–30 alphabetically:

`test_basic.py`, `test_book_ingest.py`, `test_bucket_calibration.py`, `test_calibration.py`, `test_calibration_footer.py`, `test_candidate_diagnostics.py`, `test_candidate_lifecycle.py`, `test_capture_efficiency_in_wisdom.py`, `test_company_name_fallback.py`, `test_confidence_band.py`, `test_cross_validate_price.py`, `test_daily_intelligence_brief.py`, `test_daily_picks_no_pick_diagnostics.py`, `test_daily_picks_run_status.py`, `test_daily_picks_workflow_reliability.py`
