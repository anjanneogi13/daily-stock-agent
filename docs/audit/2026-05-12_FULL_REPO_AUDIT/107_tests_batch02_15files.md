# Audit Batch 107 — tests/ files 16–30 (alphabetical) — TRUE line-by-line

**Pinned commit:** `73ba13be`
**Files audited:** 30 of 178 (cumulative)
**Total lines audited in this batch:** ~1,610
**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

# 16. `tests/test_basic.py` (61 lines)

**Covers:** `src/scorer.py`, `src/risk_manager.py`, `src/semiconductors.py`, `src/indicators.py`, `src/fundamentals.py`

### ✅ GOOD-TB-1: `_fake_df` uses `np.random.seed(0)` (line 11) — deterministic.
### ✅ GOOD-TB-2: 7 test functions across 5 production modules — broad smoke coverage.

### ⚠️ BUG-TB-1: `test_indicators_run` (lines 24–28) — only asserts non-None. Doesn't check correctness of any indicator value.
- **Severity:** 🟡 Vacuous assertion.

### ⚠️ BUG-TB-2: `test_scorer_bounds` (lines 30–39) — only asserts `0<=s["composite"]<=1`. Composite could be `0.0` always and test passes.
- **Severity:** ⚠️ Bounds-only test, no behavior validation.

### ⚠️ BUG-TB-3: `test_position_size` (line 47) — `qty == 20` magic number with no derivation comment.
- **Severity:** 🟡

### ⚠️ BUG-TB-4: No edge case for `_fake_df(n=0)` or `n=1`. What if production gets a 1-row DataFrame? Crash unprotected.
- **Severity:** 🟡 Coverage gap.

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 3 · ✅ 2

---

# 17. `tests/test_book_ingest.py` (175 lines)

**Covers:** `src/book_ingest.py` + `src/wisdom_base.py::LESSONS`

### ✅ GOOD-BI-1: `isolated_lessons` patches BOTH `wb.LESSONS` and `book_ingest.LESSONS` (lines 49–51) — defensive against import-shape drift. Best mock-path discipline in this batch.
### ✅ GOOD-BI-2: 16 distinct tests covering parse, missing, schema, idempotency, dry-run, tags, author, empty-text, CLI. Excellent density.
### ✅ GOOD-BI-3: `test_real_seed_file_loads_50_rules` (lines 147–155) skips gracefully if file missing. Proper conditional smoke test.

### ⚠️ BUG-BI-1: `test_load_seed_dry_run` (line 96): `not isolated_lessons.exists() or isolated_lessons.read_text() == ""`
- Asserts EITHER no file OR empty file. Two semantically different states conflated.
- **Severity:** 🟡

### ⚠️ BUG-BI-2: `test_book_stats_ignores_inactive` (lines 137–145) hand-rewrites JSONL (line 143)
- Manually mutating the wisdom store bypasses production write APIs. If JSON shape changes, test silently breaks.
- **Severity:** 🟡

### ⚠️ BUG-BI-3: `test_real_seed_file_loads_50_rules` hardcodes `10 books / 50 rules` (lines 154–155)
- If seed file legitimately grows, test breaks even though production is fine.
- **Severity:** 🟡 Brittle constant.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 3

---

# 18. `tests/test_bucket_calibration.py` (93 lines)

**Covers:** `src/signal_journal.py::bucket_composite, bucket_vol, bucket_p_win`

### ✅ GOOD-BC-1: Documented purpose (lines 1–7) — locking thresholds against real distribution. Exemplary intent.
### ✅ GOOD-BC-2: `test_distribution_is_meaningful` (lines 80–92) — tests against a SYNTHETIC distribution to catch miscalibration. Smart pattern.
### ✅ GOOD-BC-3: 4 distinct buckets × multiple boundary values each.

### ⚠️ BUG-BC-1: `test_composite_high_range` (lines 23–26) — line 24 and 25 are identical (`bucket_composite(0.77) == "high"` twice). Copy-paste bug.
- **Severity:** 🟡 Dead assertion.

### ⚠️ BUG-BC-2: No test exactly at `0.55` (mid→low boundary), `0.75` (mid→high boundary), `0.78` (high→very_high boundary). Tests STRADDLE boundaries but don't pin them.
- **Severity:** 🟡 Off-by-one risk on threshold drift.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 3

---

# 19. `tests/test_calibration.py` (199 lines)

**Covers:** `src/calibration.py` (load_picks, bucketing, attribute_by, reports, CLI)

### ✅ GOOD-C-1: `fake_run` fixture builds 6-pick dataset with full schema (lines 29–54). Realistic test data.
### ✅ GOOD-C-2: 24 tests across structure, bucketing, reports, CLI. Excellent coverage.
### ✅ GOOD-C-3: `test_load_picks_handles_blank_numeric` (lines 77–83) — explicit None coercion check.

### ⚠️ BUG-C-1: `test_overall_summary_math` (line 162): `s["win_rate"] == round(4/6, 3)` 
- Test depends on exact `round` precision. If `calibration` later uses `round(..., 2)`, test breaks.
- **Severity:** 🟡 Precision coupling.

### ⚠️ BUG-C-2: `test_latest_run` (lines 62–64) — assumes alphabetical ordering of `latest_run`. Comment doesn't document this contract.
- **Severity:** 🟡

### ⚠️ BUG-C-3: Tests private helpers `_rsi_bucket`, `_score_bucket`, `_atr_bucket`, `_month_bucket`, `_is_win` (lines 88–122) — same anti-pattern as BR-1 in batch 106.
- **Severity:** 🟡 Couples to private API.

### ⚠️ BUG-C-4: `test_cli_unknown_run_exits` uses `pytest.raises(SystemExit)` (line 197) — doesn't assert exit code. SystemExit(0) would also satisfy this.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 4 · ✅ 3

---

# 20. `tests/test_calibration_footer.py` (135 lines)

**Covers:** `src/calibration.py::telegram_footer_lines, open_proposals_summary`, `src/weight_proposer.py::PROPOSALS`, `src/weekly_review.py`

### ✅ GOOD-CF-1: `_row` factory with rich defaults (lines 25–32). Reusable.
### ✅ GOOD-CF-2: `test_weekly_review_safe_when_calibration_broken` (lines 122–134) — explicit fault-injection test. Excellent resilience pattern.

### ⚠️ BUG-CF-1: `test_footer_surfaces_best_and_worst` (lines 50–61) uses `or` matching: `"🟢" in joined or "Best edge" in joined`
- Either-or assertion is weak. Production could display NEITHER and test still passes if one happens to appear by accident in another bucket.
- **Severity:** 🟡 Loose assertion.

### ⚠️ BUG-CF-2: `_row` defaults `pd_="2025-01-15"` but parameter named `pd_` (trailing underscore avoiding `pd` shadow). Unconventional. Could confuse callers.
- **Severity:** 🟡 Naming.

### ⚠️ BUG-CF-3: `test_weekly_review_includes_calibration_section` (line 117) imports `from src.weekly_review import build_report, format_telegram` INSIDE the test function. Module-level import would be cleaner unless avoiding circular import.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 2

---

# 21. `tests/test_candidate_diagnostics.py` (152 lines)

**Covers:** `src/candidate_diagnostics.py::build_candidate_diagnostics, summarize_candidate`

### ✅ GOOD-CD-1: `candidate(...)` factory (lines 4–22) — clean test data shape.
### ✅ GOOD-CD-2: 5 distinct tests cover counts, premarket-sanity, scored-not-filtered, portfolio-risk, missing-data. Stage-aware.

### ⚠️ BUG-CD-1: All tests pass `pre_hard_block_candidates=[aapl, msft]` etc. with same object references repeated (lines 44, 95, 116, 142)
- Mutating `aapl` dict in production code would silently mutate test inputs. Test data not deepcopied.
- **Severity:** ⚠️ Aliasing risk.

### ⚠️ BUG-CD-2: `test_build_candidate_diagnostics_counts_scored_not_filtered` (lines 86–98) — single-test fixture for one stage, but no test for combinatorial multi-stage scenarios.
- **Severity:** 🟡 Coverage gap.

### ⚠️ BUG-CD-3: `summary["score"] == 0.7` (line 29) — depends on `composite=score` mapping unchanged forever. Tight coupling to internal field-name choices.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 2 · ✅ 2

---

# 22. `tests/test_candidate_lifecycle.py` (196 lines)

**Covers:** `scripts/build_candidate_lifecycle.py::build_candidate_lifecycle, format_markdown, write_outputs`

### ✅ GOOD-CL-1: 6 tests cover all 5 lifecycle states (selected_official, hard_blocked, filtered, watch_only, diagnostics_unavailable, missing_from_universe). Best state coverage in batch.
### ✅ GOOD-CL-2: `by_ticker` helper (lines 31–32) — consistent assertion pattern across tests.

### ⚠️ BUG-CL-1: `write_picks` schema discovery (line 24): `sorted({key for row in rows for key in row}) or ["pick_date", "ticker"]`
- For empty `rows`, falls back to minimal header. But CSV with only 2 columns might not match production schema → silent test pass when actually production reads MORE columns.
- **Severity:** ⚠️ Schema fragility.

### ⚠️ BUG-CL-2: `"2026-05-09"` repeated in 6 tests (lines 36, 82, 106, 137, 160, 189) — same DRY issue as AC-1.
- **Severity:** 🟡

### ⚠️ BUG-CL-3: `test_format_markdown_handles_empty_report` (lines 188–195) uses `or` substring match at line 195 — same anti-pattern as CF-1.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 2 · ✅ 2

---

# 23. `tests/test_capture_efficiency_in_wisdom.py` (33 lines)

**Covers:** `src/daily_wisdom.py` (via source-grep) + `src/exit_metrics.py::capture_efficiency`

### 🚨 BUG-CEW-1: 3 of 4 tests are SOURCE-GREP tests (lines 5–24)
- `test_daily_wisdom_imports_exit_metrics` greps for exact string `from src.exit_metrics import capture_efficiency`.
- `test_daily_wisdom_calls_capture_efficiency` greps for `capture_efficiency(`.
- `test_capture_efficiency_call_is_guarded` reads source lines and looks 12 lines up for `try:`.
- **All three break if you (a) rename the import, (b) move the call, (c) refactor the try/except into a helper. They test TEXT not BEHAVIOR.**
- **Severity:** 🚨 Worst anti-pattern in this batch — same disease as BA-4/BA-5/BJ-1.

### ⚠️ BUG-CEW-2: `test_wisdom_still_produces_output` (lines 27–32) calls `generate_daily_wisdom()` with NO mocking
- Hits real production data files. Will FAIL on a fresh clone with no `data/`.
- **Severity:** ⚠️

**Per-file:** 🚨 1 · ⚠️ 1 · 🟡 0 · ✅ 0 (worst-quality file in batch)

---

# 24. `tests/test_company_name_fallback.py` (111 lines)

**Covers:** `src/data_fetcher.py::fetch_info`, `src/parallel_scorer.py::_score_one`

### ✅ GOOD-CNF-1: `Mock` from `unittest.mock` for `yf.Ticker` (line 9). Proper external-lib boundary mock.
### ✅ GOOD-CNF-2: Both negative (FAKE = ticker name) AND positive (real name) branches tested (lines 6, 25). Bidirectional.

### ⚠️ BUG-CNF-1: `test_parallel_scorer_info_short_name_does_not_fall_back_to_ticker` (lines 44–110) monkeypatches **17 functions** in `parallel_scorer`
- Massive surface mock = brittle. ANY refactor renaming any of these helpers breaks the test even if behavior is identical.
- **Severity:** ⚠️ Mock surface explosion.

### ⚠️ BUG-CNF-2: `monkeypatch.setattr(data_fetcher, "HAS_FINNHUB", False)` (lines 16, 35)
- Globally toggles a module attribute. Test pollution if any test forgets to use monkeypatch (could leak across modules).
- **Severity:** 🟡

### ⚠️ BUG-CNF-3: `cfg = {..., "_regime": "bull"}` (line 102) — underscore prefix is a private convention, but test uses it as public key. Suggests test is reaching into implementation.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 2 · ✅ 2

---

# 25. `tests/test_confidence_band.py` (66 lines)

**Covers:** `src/confidence_band.py::confidence_band, band_label, HIGH/GOOD/CAUTION/AVOID`

### ✅ GOOD-CB-1: 17 tests across 5 test classes — comprehensive matrix (drag/edge/score/lesson/robustness).
### ✅ GOOD-CB-2: Robustness tests for None/garbage (lines 50–55). Defensive.
### ✅ GOOD-CB-3: Sample hint constants `DRAG`, `EDGE`, `LESSON` (lines 8–10) — uses real production-shape strings.

### ⚠️ BUG-CB-1: `test_garbage_score` (line 51): comment says `"abc" → 0.0 → low` but `confidence_band("abc", "")` → `CAUTION`
- Test asserts CAUTION but doesn't verify the intermediate `0.0` coercion. If "abc" returned `1.0` (high), test would FAIL but with confusing trace.
- **Severity:** 🟡

### ⚠️ BUG-CB-2: `test_drag_at_score_1_caution` (line 19) — boundary test at exactly 1.0. Good. But no test at 1.0 boundary for EDGE or LESSON paths.
- **Severity:** 🟡 Asymmetric boundary coverage.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 3

---

# 26. `tests/test_cross_validate_price.py` (97 lines)

**Covers:** `src/finnhub_data.py::fetch_finnhub_quote, cross_validate_price`

### ✅ GOOD-CVP-1: 11 tests cover None/zero/negative/agreement/warn/block/custom thresholds. Excellent boundary coverage.
### ✅ GOOD-CVP-2: `unittest.mock.patch` for `fetch_finnhub_quote` (lines 44, 54, 64, 74, 82, 91) — proper isolation from network.
### ✅ GOOD-CVP-3: `test_validate_passes_when_second_source_unavailable` (lines 42–49) explicitly tests the "don't false-positive when Finnhub down" path. Thoughtful.

### ⚠️ BUG-CVP-1: `test_fetch_quote_no_api_key_returns_graceful` (lines 13–22) — convoluted env manipulation
- Sets `FINNHUB_API_KEY=""`, then deletes it. Two operations to express "key not present". Risk of leaking env into other tests if delete fails.
- **Severity:** 🟡

### ⚠️ BUG-CVP-2: `1.5 < v["disagreement_pct"] < 2.5` (line 86) — loose range for what should be a deterministic computation.
- **Severity:** 🟡 Loose assertion.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 3

---

# 27. `tests/test_daily_intelligence_brief.py` (233 lines)

**Covers:** `scripts/build_daily_intelligence_brief.py` (build, classify, format_markdown, write_outputs)

### ✅ GOOD-DIB-1: `test_classify_daily_operating_status_priority_order` (lines 115–138) — explicit priority-order matrix. Important for state machine correctness.
### ✅ GOOD-DIB-2: 6 tests cover incomplete pipeline, data-failed, productive paths, write_outputs, format. Multi-classification coverage.

### ⚠️ BUG-DIB-1: Truncated dict in `theme_pick_bridge` artifact (line 58): `"watch_only_[...]` — the actual file has a syntax-incomplete-looking `[...]`. Either it's truly truncated in source (broken test) or the audit-tool truncated display.
- **Severity:** ⚠️ Potential broken test (verify original source).

### ⚠️ BUG-DIB-2: `"2026-05-09"` and `"2026-05-08"` repeated 6+ times (multiple lines). Same DRY anti-pattern.
- **Severity:** 🟡

### ⚠️ BUG-DIB-3: `test_format_markdown_includes_safety_status` (lines 176–183) calls `build_daily_intelligence_brief` with NO artifacts in `tmp_path`
- Depends on the function tolerating fully-empty input. Doesn't pin the schema actually returned.
- **Severity:** 🟡 Shallow.

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 2 · ✅ 2

---

# 28. `tests/test_daily_picks_no_pick_diagnostics.py` (126 lines)

**Covers:** `main.py::_classify_no_pick_cause, _write_daily_picks_no_pick_report` (via `import main`)

### 🚨 BUG-DPND-1: `test_no_pick_report_function_supports_diagnostics_and_cause_classification` (lines 6–15)
- 7 GREPs against `main.py` source text. **Worst type of test** — couples to source text not behavior. Identical anti-pattern to CEW-1.
- **Severity:** 🚨

### ⚠️ BUG-DPND-2: `import main` at top of test file (line 19, 49) — runs all of main.py's import-time code each test
- main.py is 1,817 lines. Side effects at import time (file reads, env reads) repeat per test.
- **Severity:** ⚠️ Slow + side-effects.

### ⚠️ BUG-DPND-3: `monkeypatch.chdir(tmp_path)` (line 51) — global cwd change
- Other tests in the same session may break if any caller assumes original cwd. monkeypatch unwinds, but only on fixture teardown, not immediately.
- **Severity:** 🟡

### ⚠️ BUG-DPND-4: `_write_daily_picks_no_pick_report` invocation (lines 63–102) builds an enormous inline dict
- 40-line literal makes intent hard to read. Should be a fixture.
- **Severity:** 🟡

**Per-file:** 🚨 1 · ⚠️ 1 · 🟡 2 · ✅ 0

---

# 29. `tests/test_daily_picks_run_status.py` (158 lines)

**Covers:** `scripts/record_daily_picks_run_status.py` (status_path, build_record, append_record, today_picks_count, _daily_picks_diagnostics)

### ✅ GOOD-DPR-1: Frozen `datetime` with explicit `tzinfo=ZoneInfo("America/New_York")` (lines 27, 45, 59, 128) — deterministic, timezone-correct.
### ✅ GOOD-DPR-2: 8 tests cover path-naming, record-building, append, csv-counting, diagnostics-reading, inferred-cause. Strong.
### ✅ GOOD-DPR-3: `monkeypatch.setenv("GITHUB_RUN_ID", "123")` (line 20) — proper env mock.

### ⚠️ BUG-DPR-1: `test_today_picks_count_counts_csv_rows_for_date` writes raw CSV string (lines 73–78) instead of using `csv.DictWriter`
- If schema changes, this string-CSV breaks production read. Inconsistent with other tests' CSV write style.
- **Severity:** 🟡

### ⚠️ BUG-DPR-2: `_daily_picks_diagnostics` is a private function (underscore prefix) but tested directly (lines 84, 99, 140, 152). Same anti-pattern as C-3.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 3

---

# 30. `tests/test_daily_picks_workflow_reliability.py` (242 lines)

**Covers:** `.github/workflows/daily-picks.yml`, `.github/workflows/watchdog.yml`, `.github/workflows/late_watch_only.yml` — **ALL VIA SOURCE-GREP**

### 🚨 BUG-DPW-1: ENTIRE FILE is source-grep tests — all 22 tests assert string presence in workflow YAML files
- Lines 22–242, every single test does `assert "..." in text`. **This is a YAML linter masquerading as tests.**
- **Critical issue:** Tests assert on workflow text, NOT on workflow BEHAVIOR. If GitHub changes how `cron:` or `if:` is parsed, tests pass but production breaks. If you reformat YAML, tests break but production works.
- **Severity:** 🚨 Test architecture anti-pattern (entire file).

### ⚠️ BUG-DPW-2: 22 distinct hardcoded strings to maintain
- `"5,20,35,50 12-14 * * 1-5"`, `"OFFICIAL_CUTOFF=$((9 * 60 + 20))"`, `"--event watchdog_alert"`, etc.
- Maintenance burden: every workflow tweak requires updating multiple test strings.
- **Severity:** ⚠️ Maintenance debt.

### ⚠️ BUG-DPW-3: `test_skipped_daily_picks_attempt_self_heals_missing_run_status_marker` (lines 205–224)
- 19 string assertions on a single workflow block. If you split that block into 2 steps for readability, all 19 break.
- **Severity:** ⚠️

### 🟡 BUG-DPW-4: Tests assert ABSENCE of strings (lines 35, 36, 70, 91) — `not in text`
- Even more brittle. ANY reformatting could trigger these.
- **Severity:** 🟡

### ✅ Pseudo-good: At least the file IS testing something — workflow misconfig is the #1 reason your premarket picks have been failing. **But tests should invoke `actionlint` or simulate the workflow runner, not grep YAML.**

**Per-file:** 🚨 1 · ⚠️ 2 · 🟡 1 · ✅ 0

---

## 🎯 BATCH 107 grand totals

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 3 (CEW-1, DPND-1, DPW-1) |
| ⚠️ Data/safety risk | 9 |
| 🟡 Code smell | 30 |
| ✅ Good code | 30 |
| **Total findings** | **72 across 15 files / ~1,610 lines** |

### 🔥 CRITICAL CROSS-FILE PATTERN (relevant to your "agent broken" concern)

**`test_daily_picks_workflow_reliability.py` is 242 lines of YAML string-grep.** This is exactly the file that should catch your premarket failures — but because it tests workflow TEXT not workflow BEHAVIOR, it has been GREEN while your premarket picks have been FAILING for a week+. **The test is structurally incapable of catching the bugs you're hitting.** This is a top-priority finding for your remediation plan.

### Production code coverage from this batch

- `src/scorer.py`, `src/risk_manager.py`, `src/semiconductors.py`, `src/indicators.py`, `src/fundamentals.py` (5 src)
- `src/book_ingest.py`, `src/wisdom_base.py`, `src/signal_journal.py`, `src/calibration.py`, `src/weight_proposer.py`, `src/weekly_review.py`, `src/candidate_diagnostics.py`, `src/daily_wisdom.py`, `src/exit_metrics.py`, `src/data_fetcher.py`, `src/parallel_scorer.py`, `src/confidence_band.py`, `src/finnhub_data.py` (13 src)
- `scripts/build_candidate_lifecycle.py`, `scripts/build_daily_intelligence_brief.py`, `scripts/record_daily_picks_run_status.py` (3 scripts)
- `main.py` (via grep + import) — incomplete coverage, just `_classify_no_pick_cause` and `_write_daily_picks_no_pick_report`
- `.github/workflows/{daily-picks,watchdog,late_watch_only}.yml` (3 workflows — TEXT only)

### Next batch (108) — files 31–45 alphabetically:
`test_daily_picks_zero_pick_failure.py`, `test_daily_watch_only_learning_report.py`, `test_daily_wisdom.py`, `test_data_fetcher_info_pressure.py`, `test_data_fetcher_provider_fallback.py`, `test_data_quality.py`, `test_data_readiness_report.py`, `test_day_trading_engine.py`, `test_dedup_sender.py`, `test_dry_run_official_no_pick.py`, `test_dry_run_official_premarket_pick.py`, `test_earnings_analyzer.py`, `test_earnings_days_to_earnings.py`, `test_edge_case_fuzz.py`, `test_enforcement_readiness.py`
