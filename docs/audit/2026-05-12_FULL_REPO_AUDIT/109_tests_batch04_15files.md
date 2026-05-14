# Audit Batch 109 — tests/ files 46–60 (alphabetical) — TRUE line-by-line

**Pinned commit:** `1f10a2e0`
**Files audited:** 60 of 178 (cumulative)
**Total lines audited in this batch:** ~1,350
**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

# 46. `tests/test_exclusions.py` (47 lines)

**Covers:** `config.yaml::universe.excluded_tickers`, `src/universe.py::get_universe`

### ✅ GOOD-EX-1: `BACKTESTER_LOSERS` constant (line 12) with documented source (lines 1–6). Locked-fact test.
### ✅ GOOD-EX-2: `try/except + pytest.skip` for network failure (lines 38–43) — graceful degradation.

### ⚠️ BUG-EX-1: `test_universe_loader_filters_losers` calls real `get_universe(cfg)` (line 39) — hits network
- **Severity:** ⚠️ Production-network dependency. Will skip (not fail) on CI without net, masking real bugs.

### ⚠️ BUG-EX-2: `BACKTESTER_LOSERS` is hardcoded — if backtester promotes one of these tickers back, test breaks even though config is correct.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 1 · ✅ 2

---

# 47. `tests/test_faculty_integration.py` (303 lines)

**Covers:** ALL 7 faculties — `data_fetcher`, `scorer`, `smell_faculty`, `_is_pick_sane`, `signal_journal`, `layman_translator`, `wisdom_consultant`

### ✅ GOOD-FI-1: **HEADLINE FILE OF THIS BATCH.** Header docstring (lines 1–21) is exemplary intent — explicitly documents which production failure (May 2-4 silent metadata) this regression-prevents. **This is what every test file should look like.**
### ✅ GOOD-FI-2: 17 tests organized by faculty with clear section dividers. End-to-end pipeline test (lines 235–303) exercises ALL 7 faculties together.
### ✅ GOOD-FI-3: `pytest.mark.xfail(strict=False)` (lines 30–41) on real-network test — explicitly documents acceptable flakiness AND points to the deterministic mocked equivalent. **Best xfail usage in repo.**

### 🚨 BUG-FI-1: `test_eyes_returns_required_fields` (lines 52–58) hits real `fetch_info("AAPL")` — **NOT marked xfail**
- This is a **production-network dependency that WILL FAIL** when yfinance is rate-limited. Breaks CI deterministically when production is healthy. **Same disease that caused the May 11 incident referenced in xfail comment above.**
- **Severity:** 🚨 Inconsistent with FI-1's stated philosophy.

### ⚠️ BUG-FI-2: `test_memory_journal_writes_and_reads` (lines 155–179) mutates module global `sj.JOURNAL` directly (line 166)
- Bypasses `monkeypatch`. Restored in `finally` BUT if test process is killed mid-flight, leak persists.
- **Severity:** ⚠️

### ⚠️ BUG-FI-3: `test_full_pipeline_end_to_end` (lines 235–289) mocks Finnhub but not yfinance, signal_journal, or wisdom calls
- Pipeline test is partly real, partly mocked. Inconsistent isolation = inconsistent failure modes.
- **Severity:** 🟡

### ⚠️ BUG-FI-4: `test_brain_composite_score_in_valid_range` (line 76) calls `composite_score` — `result.get("composite", 0) if isinstance(result, dict) else float(result)` (line 77). Defensive against TWO different return types means the contract is unclear.
- **Severity:** 🟡

**Per-file:** 🚨 1 · ⚠️ 1 · 🟡 2 · ✅ 3 (most ambitious file in batch — both best practice and worst risk)

---

# 48. `tests/test_full_repo_audit_accuracy.py` (49 lines)

**Covers:** `scripts/full_repo_audit.py` — **ALL VIA SOURCE-GREP**

### 🚨 BUG-FRA-1: ALL 5 tests are source-grep on `scripts/full_repo_audit.py`
- Tests assert `"MONITORING READINESS" in src`, `"EARNINGS FILL-RATE" in src`, etc.
- Same anti-pattern as DPW-1, CEW-1, DPZ-1. **Tests structure not behavior.** If you rename a section header, tests break but the audit still works.
- **Severity:** 🚨

### ⚠️ BUG-FRA-2: `test_audit_removes_stale_smell_not_persisted_pending_check` (lines 30–34) — asserts ABSENCE of strings. Even more brittle.
- **Severity:** ⚠️

**Per-file:** 🚨 1 · ⚠️ 1 · 🟡 0 · ✅ 0

---

# 49. `tests/test_full_repo_audit_drift.py` (65 lines)

**Covers:** `scripts/full_repo_audit.py::classify_docs_drift`

### ✅ GOOD-FRD-1: 3 behavioral tests for `classify_docs_drift` (lines 8–57) — not source-grep, real function calls.
### ✅ GOOD-FRD-2: Tests cover ghost-ref, planned-NOT-YET-BUILT, real-missing branches. State coverage.

### 🚨 BUG-FRD-1: `test_architecture_no_longer_mentions_watchlist_py` (lines 60–64) is source-grep on `docs/PROJECT_BLUEPRINT.md`
- One source-grep contaminates an otherwise good behavioral file.
- **Severity:** 🚨

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 0 · ✅ 2

---

# 50. `tests/test_full_repo_audit_import_safe.py` (25 lines)

**Covers:** `scripts/full_repo_audit.py` (import-time safety)

### ✅ GOOD-FRI-1: Header docstring (lines 1–11) documents the bug history (~180s import time). Exemplary intent.
### ✅ GOOD-FRI-2: `contextlib.redirect_stdout(buf)` (line 19) — clean stdout capture.
### ✅ GOOD-FRI-3: Tests BEHAVIOR (does importing produce side-effects?) not source text. **Best practice — should be model for refactoring source-grep tests.**

### ⚠️ BUG-FRI-1: Asserts `"REPO META" not in buf.getvalue()` — string-literal-based detection (line 23)
- If audit renames the section header, test passes silently even if side-effect persists.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 3

---

# 51. `tests/test_full_repo_audit_regime_counts.py` (42 lines)

**Covers:** `scripts/full_repo_audit.py::format_regime_counts, recent_regime_counts`

### ✅ GOOD-FRR-1: `test_recent_regime_counts_handles_quoted_company_commas` (lines 8–33) — explicit CSV-parsing edge case (commas in company names like "Agilent Technologies, Inc."). **CRITICAL.** This is the kind of test that catches subtle production bugs.
### ✅ GOOD-FRR-2: 3 distinct tests, all behavioral. No source-grep.

### ⚠️ BUG-FRR-1: `assert format_regime_counts({"bull": 10}) == "    10 bull"` (line 37) — exact whitespace string equality. If output gets a tab or different spacing for alignment, breaks.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 2

---

# 52. `tests/test_github_observability.py` (46 lines)

**Covers:** `src/github_observability.py::github_run_url, github_commit_url, github_artifact_bundle_name, github_observability_metadata`

### ✅ GOOD-GO-1: 4 tests pass `env=` dict directly (lines 10, 20, 33) — no env mutation, no monkeypatch. **Best env-dependency pattern.**
### ✅ GOOD-GO-2: Explicit format-string assertions (lines 16, 26) — locks URL contract.

### ⚠️ BUG-GO-1: No test for missing env keys. What if `GITHUB_RUN_ID` absent? Behavior undefined.
- **Severity:** 🟡

### ⚠️ BUG-GO-2: `test_github_metadata_is_empty_for_local_context` (lines 33–46) uses `"local"` literal. What if env var is just empty string `""`? Different code path untested.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 2

---

# 53. `tests/test_hard_blocks.py` (179 lines)

**Covers:** `src/hard_blocks.py` — penny-stock, SL-buffer, recent-pick, weak-sector, catastrophic-news gates + `apply_hard_blocks`

### ✅ GOOD-HB-1: 11 tests cover ALL 5 block types + apply_hard_blocks orchestration + check_sectors=False branch. **Complete state coverage.**
### ✅ GOOD-HB-2: `monkeypatch.setattr(hb, "_get_recent_pick_dates", ...)` (line 123) and `monkeypatch.setattr(hb, "get_weak_sectors", ...)` (line 122) — clean dependency injection.
### ✅ GOOD-HB-3: `test_apply_hard_blocks_can_disable_sector_check` uses `pytest.fail` inside a lambda (line 162) to assert "this should never be called". Smart pattern.
### ✅ GOOD-HB-4: `monkeypatch.chdir(tmp_path)` (line 121) — isolates the `data/hard_blocks_log.json` write.

### ⚠️ BUG-HB-1: 5 tests on private `_block_*` and `_get_*` functions. Same private-API anti-pattern.
- **Severity:** 🟡

### ⚠️ BUG-HB-2: `test_block_recent_pick_blocks_within_cooldown` uses `datetime.now()` (line 80) — time-dependent test
- **Severity:** 🟡

### ⚠️ BUG-HB-3: `assert blocked == [...]` (line 142) — exact equality on dict ORDER. If `apply_hard_blocks` reorders for any reason, breaks.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 4 (highest GOOD count, best gate-coverage in batch)

---

# 54. `tests/test_hypothesis_engine.py` (136 lines)

**Covers:** `src/signal_journal.py` (bucketing helpers), `src/hypothesis_engine.py::analyze, two_sided_p_value, format_report, MIN_SAMPLE_SIZE`

### ✅ GOOD-HE-1: 12 tests across bucketing + p-value math + analyze integration. Layered coverage.
### ✅ GOOD-HE-2: `test_pvalue_zero_n_safe` (line 81) — defensive math edge case.
### ✅ GOOD-HE-3: `test_analyze_finds_edge` (lines 94–117) — synthetic 30-pick dataset with KNOWN edge. Reproducible.

### ⚠️ BUG-HE-1: `MIN_SAMPLE_SIZE` imported (line 12) but never used in any test
- Dead import. Should test boundary against this constant.
- **Severity:** 🟡

### ⚠️ BUG-HE-2: `test_pvalue_huge_deviation_is_low` asserts `p < 0.001` (line 78) — magic threshold. Should reference a documented alpha.
- **Severity:** 🟡

### ⚠️ BUG-HE-3: `test_format_report_runs` (lines 129–135) only checks 2 substrings. Doesn't validate that report content matches analysis input.
- **Severity:** 🟡 Shallow.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 3

---

# 55. `tests/test_intraday_monitor_csv_close.py` (179 lines)

**Covers:** `scripts/intraday_monitor.py::load_todays_picks, monitor_existing_picks` (CSV-write behavior)

### ✅ GOOD-IMC-1: Header docstring (lines 1–6) **EXPLICITLY documents the production bug being regression-tested** — "Bug fixed 2026-05-05: monitor detected SL hits, alerted on Telegram, but NEVER wrote to picks_log.csv. So the same pick alerted 4× the same day". **EXEMPLARY** — this is the kind of test you need MORE of for your premarket/intraday issues.
### ✅ GOOD-IMC-2: 6 tests cover SL hit, TP hit, already-closed skip, near-SL no-close, required column presence, idempotency. **Best behavioral coverage in batch.**
### ✅ GOOD-IMC-3: `pytest.approx(-5.0, abs=0.1)` (line 158) — proper float comparison.
### ✅ GOOD-IMC-4: `test_idempotent_second_run_no_double_write` (lines 162–178) — explicit idempotency test.

### ⚠️ BUG-IMC-1: `_setup_module` reloads `intraday_monitor` (line 59) — module reload mid-test
- Reload + monkey-patch ordering is fragile. Comments (lines 53–58, 67–69) document the fragility itself. Sign of an architectural issue.
- **Severity:** ⚠️

### ⚠️ BUG-IMC-2: 27-column hardcoded CSV schema (lines 23–28) — if production schema changes, all 6 tests break.
- **Severity:** 🟡

### ⚠️ BUG-IMC-3: Manual `patch.start()` / `patch.stop()` with try/finally (lines 81–86, 99–104, etc.) — should use `with patch(...)` context manager. More fragile if exception in start.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 2 · ✅ 4

---

# 56. `tests/test_intraday_monitor_opening_range_observations.py` (56 lines)

**Covers:** `scripts/intraday_monitor.py::main, append_opening_range_observations`

### ✅ GOOD-IMO-1: `monkeypatch.setattr(monitor, "scan_for_new_opportunities", ...)` (line 33) returns synthetic candidate. Clean.
### ✅ GOOD-IMO-2: Asserts both side-effects (`calls`, `status_calls`) AND output file content. Layered.

### ⚠️ BUG-IMO-1: 8 separate monkeypatches (lines 27, 28, 29, 30, 31, 36, 41, 42) — large mock surface
- Same anti-pattern as CNF-1 in batch 107.
- **Severity:** 🟡

### ⚠️ BUG-IMO-2: `assert "Reference levels: Observed $101.60" in body` (line 54) — exact decimal format coupling.
- **Severity:** 🟡

### ⚠️ BUG-IMO-3: `assert "Observe levels: Entry" not in body` (line 55) — asserts ABSENCE of an old format string. Brittle.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 2

---

# 57. `tests/test_intraday_monitor_workflow.py` (107 lines)

**Covers:** `.github/workflows/intraday_monitor.yml` (grep) + `scripts/send_intraday_telegram.py` (subprocess)

### ✅ GOOD-IMW-1: `test_intraday_telegram_sender_runs_from_actions_script_path` (lines 28–56) — actually invokes the script via subprocess, asserts return code AND side-effect file creation. **Behavioral.**
### ✅ GOOD-IMW-2: `test_intraday_telegram_sender_import_has_no_side_effects` (lines 59–84) — explicitly checks import-time purity. Locks the contract.
### ✅ GOOD-IMW-3: `subprocess.run([sys.executable, ...])` (line 46) — uses `sys.executable` (correctly, unlike batch 106 files).

### 🚨 BUG-IMW-1: First 2 tests (lines 11–25) are source-grep on workflow YAML
- Same anti-pattern. But contained — only 2 tests vs. the rest being behavioral. Mixed file.
- **Severity:** 🚨 (pattern), but isolated impact.

### ⚠️ BUG-IMW-2: `timeout=30` (line 51) on subprocess. If CI is slow, false negative.
- **Severity:** 🟡

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 1 · ✅ 3

---

# 58. `tests/test_intraday_monitor_workflow_observations.py` (16 lines)

**Covers:** `.github/workflows/intraday_monitor.yml` — **ALL VIA SOURCE-GREP**

### 🚨 BUG-IMWO-1: 100% source-grep, 2 tests, 16 lines.
- **Severity:** 🚨 Pure anti-pattern. Tiniest source-grep file in repo.

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 0 · ✅ 0

---

# 59. `tests/test_intraday_monitor_workflow_schedule.py` (26 lines)

**Covers:** `.github/workflows/intraday_monitor.yml` cron schedule — **ALL VIA SOURCE-GREP**

### 🚨 BUG-IMWS-1: 100% source-grep, 3 tests
- Asserts cron strings `"35,45 13-14 * * 1-5"` and `"0,30 13-21 * * 1-5"` are present in YAML.
- **CRITICAL TO YOUR INTRADAY FAILURE:** This file is supposed to lock the cron schedule. But if cron triggers ARE present in YAML and STILL not firing in production (GitHub Actions concurrency lock, schedule disable on inactivity, runner unavailable), the test passes but production fails. **Source-grep is structurally incapable of catching the actual failure modes you're hitting.**
- **Severity:** 🚨

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 0 · ✅ 0

---

# 60. `tests/test_intraday_new_opportunity_cutoff.py` (56 lines)

**Covers:** `scripts/intraday_scanner.py::new_opportunity_window_open, scan_for_new_opportunities`

### ✅ GOOD-INO-1: Explicit `datetime` with `tzinfo=ET` (lines 17, 23, 51) — timezone-correct.
### ✅ GOOD-INO-2: Boundary tests at exactly cutoff (line 23, `15:15`) and just before (line 18, `15:14`). Tight.
### ✅ GOOD-INO-3: `calls = []` capture pattern (line 28, 31) verifies suppression — function NOT called when window closed.

### ⚠️ BUG-INO-1: Cutoff time `15:15` ET hardcoded — should reference `intraday_scanner.NEW_OPPORTUNITY_CUTOFF` constant if exists.
- **Severity:** 🟡

### ⚠️ BUG-INO-2: Only 3 tests. Missing: weekend, market holiday, after-hours.
- **Severity:** 🟡 Coverage gap.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 3

---

## 🎯 BATCH 109 grand totals

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 6 (FI-1, FRA-1, FRD-1, IMW-1, IMWO-1, IMWS-1) |
| ⚠️ Data/safety risk | 4 |
| 🟡 Code smell | 24 |
| ✅ Good code | 33 |
| **Total findings** | **67 across 15 files / ~1,350 lines** |

### 🔥 ARCHITECTURE-RELEVANT FINDINGS THIS BATCH (you cited intraday breakage)

1. **IMWS-1** — `test_intraday_monitor_workflow_schedule.py` is **100% source-grep on cron strings**. **This is the smoking gun for your intraday failures.** If the cron exists in YAML but GitHub Actions is silently disabling it (60-day inactivity rule, concurrency lock, repository archival, schedule throttling), this test passes while production stops running. **Suggestion: replace with a workflow-run-history check** that asserts at least N successful runs in the past 7 days via the GitHub Actions API.

2. **IMC-1** — `test_intraday_monitor_csv_close.py` is the **best regression test in your repo**. Header literally says "Bug fixed 2026-05-05: monitor detected SL hits, alerted on Telegram, but NEVER wrote to picks_log.csv." **This is what every test for your premarket/intraday flows should look like.** Use it as the template.

3. **FI-1** — `test_faculty_integration.py` is the **most ambitious test in your repo** (303 lines testing all 7 faculties end-to-end). This is GREAT, but FI-1 has one real-network test (`test_eyes_returns_required_fields`) that wasn't marked xfail — this WILL flake when yfinance is rate-limited, exactly like the May 11 incident the file's xfail comment references.

### 🚨 THE PATTERN IS NOW UNDENIABLE

After 60 test files audited, the **#1 systemic test debt** is:
- **24 of 60 audited test files (40%)** use source-grep against either `.py`, `.md`, or `.yml` files instead of testing behavior.
- This means **40% of your "test coverage" is structurally unable to catch production failures** — it only catches code-text changes.
- Your premarket and intraday picks failures are almost certainly in this gap.

### Production code coverage from this batch

- `config.yaml`, `src/universe.py`, `src/data_fetcher.py`, `src/scorer.py`, `src/smell_faculty.py`, `src/signal_journal.py`, `src/layman_translator.py`, `src/wisdom_consultant.py`, `src/github_observability.py`, `src/hard_blocks.py`, `src/news_signals.py`, `src/hypothesis_engine.py`
- `scripts/send_layman_daily.py`, `scripts/full_repo_audit.py`, `scripts/intraday_monitor.py`, `scripts/intraday_scanner.py`, `scripts/send_intraday_telegram.py`
- `.github/workflows/intraday_monitor.yml` (grep only)

### Next batch (110) — files 61–75 alphabetically:
`test_intraday_scanner_opening_range.py`, `test_journal_consistency.py`, `test_late_daily_ideas.py`, `test_late_watch_only_sent_ledger_persistence.py`, `test_layman_translator.py`, `test_learning_journal.py`, `test_lesson_gc.py`, `test_llm_agent.py`, `test_main_t51_guard_no_pick_artifact.py`, `test_market_calendar.py`, `test_market_data_health.py`, `test_market_data_provider_stooq.py`, `test_market_news.py`, `test_meta_brain.py`, `test_missed_premarket_alert.py`
