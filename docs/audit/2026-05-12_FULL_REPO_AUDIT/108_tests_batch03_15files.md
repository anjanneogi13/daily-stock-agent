# Audit Batch 108 — tests/ files 31–45 (alphabetical) — TRUE line-by-line

**Pinned commit:** `1f10a2e0` / `834333b4`
**Files audited:** 45 of 178 (cumulative)
**Total lines audited in this batch:** ~1,580
**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

# 31. `tests/test_daily_picks_zero_pick_failure.py` (70 lines)

**Covers:** `main.py`, `.github/workflows/daily-picks.yml` — **ALL VIA SOURCE-GREP**

### 🚨 BUG-DPZ-1: ENTIRE FILE is source-grep tests (all 7 tests, lines 4–69)
- Same anti-pattern as `test_daily_picks_workflow_reliability.py` (DPW-1) and `test_capture_efficiency_in_wisdom.py` (CEW-1).
- Every test does `assert "..." in Path("main.py").read_text()` or workflow YAML.
- **CRITICAL CONNECTION TO YOUR ARCHITECTURE PROBLEM:** This file is supposed to lock the contract "main.py fails loudly when 0 official picks generated". But it only checks the SOURCE TEXT contains those strings — not that the runtime ACTUALLY fails loudly. **This is exactly why your premarket failures aren't caught.**
- **Severity:** 🚨

### ⚠️ BUG-DPZ-2: `assert 'grep -c "^$ET_DATE" data/picks_log.csv 2>/dev/null || echo 0' not in text` (line 15)
- Asserts a specific bash pattern is ABSENT. Fragile to any reformatting of bash.
- **Severity:** ⚠️

**Per-file:** 🚨 1 · ⚠️ 1 · 🟡 0 · ✅ 0

---

# 32. `tests/test_daily_watch_only_learning_report.py` (108 lines)

**Covers:** `scripts/daily_watch_only_learning_report.py::build_summary, format_markdown, write_outputs`

### ✅ GOOD-DWL-1: 5 distinct artifact types written into tmp_path (late_daily_ideas, opening_range, opening_range_run_status, intraday_momentum, intraday_alerts) — realistic multi-source test (lines 11–70).
### ✅ GOOD-DWL-2: 24 explicit assertions on summary fields (lines 74–92) — deep schema validation.

### ⚠️ BUG-DWL-1: `test_watch_only_learning_report_writes_outputs` (lines 95–107) calls `build_summary` with EMPTY `data/` directory
- Tests "happy path on no data" but doesn't assert what the empty summary actually contains. Just that file exists and has 2 specific keys. Shallow.
- **Severity:** 🟡

### ⚠️ BUG-DWL-2: `"2026-05-06"` repeated 6+ times — same DRY pattern.
- **Severity:** 🟡

### ⚠️ BUG-DWL-3: Inline JSON `{"event": "monitor_completed", ...}` (lines 45–50) hardcodes schema. If `record_market_data_event` changes shape, test breaks even though logic is fine.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 2

---

# 33. `tests/test_daily_wisdom.py` (66 lines)

**Covers:** `src/daily_wisdom.py::generate_daily_wisdom, _confidence_label, _row_to_journal_format, N_*` constants

### ✅ GOOD-DW-1: Imports threshold constants `N_ANECDOTAL`, `N_DIRECTIONAL`, `N_CONFIDENT` (line 6) and tests boundaries against them (lines 11–17). **EXEMPLARY** — no magic numbers.
### ✅ GOOD-DW-2: `test_row_to_journal_skips_unrecorded` (lines 39–43) — explicit None-return validation.

### 🚨 BUG-DW-1: `test_generate_wisdom_runs_without_crash` (lines 46–51) and `test_wisdom_contains_sample_warning_when_small` (lines 54–58) and `test_wisdom_uses_quality_floor` (lines 61–65)
- All three call `generate_daily_wisdom()` with NO mocking. **Hits real `data/picks_log.csv`.**
- Tests will FAIL on fresh clone. Tests will PASS or FAIL non-deterministically based on production state.
- **Severity:** 🚨 Same disease as CEW-2 — production-data-dependent test.

### ⚠️ BUG-DW-2: `test_wisdom_contains_sample_warning_when_small` (line 58) uses 3-way `or` assertion
- `("ANECDOTAL" in out) or ("No closed picks" in out) or ("Sample" in out)` — shotgun assertion.
- **Severity:** 🟡

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 1 · ✅ 2

---

# 34. `tests/test_data_fetcher_info_pressure.py` (63 lines)

**Covers:** `src/data_fetcher.py::fetch_info`, `.github/workflows/daily-picks.yml`

### ✅ GOOD-DFI-1: `FakeTicker` class with property counter (lines 5–20) — verifies `.info` is NOT accessed when env disables it. Behavioral, not text.
### ✅ GOOD-DFI-2: Tests both branches: env=`false` skips heavy info (line 23), env unset accesses it (line 41). Bidirectional.

### 🚨 BUG-DFI-1: `test_daily_picks_workflow_disables_heavy_yfinance_full_info` (lines 57–62) is a SOURCE-GREP test on workflow YAML
- Same anti-pattern. Asserts `"DAILY_FETCH_YF_FULL_INFO: false" in workflow`.
- **Severity:** 🚨 Source-grep contamination.

### ⚠️ BUG-DFI-2: `monkeypatch.setattr(df, "SESSION", None)` (lines 29, 47) — global attribute mutation. Test pollution risk.
- **Severity:** 🟡

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 1 · ✅ 2

---

# 35. `tests/test_data_fetcher_provider_fallback.py` (85 lines)

**Covers:** `src/data_fetcher.py::fetch_ohlcv, fetch_universe_data` (yfinance → stooq fallback chain)

### ✅ GOOD-DFP-1: 5 tests cover ALL 4 branches of the fallback chain (yfinance success, yfinance empty→stooq, yfinance error→stooq, both fail) plus a 5th for filtering. **Best fallback coverage in batch.**
### ✅ GOOD-DFP-2: `events.append(kwargs)` pattern (lines 36, 54, 69) — lets tests verify telemetry was emitted, not just final result.
### ✅ GOOD-DFP-3: `_df()` factory (lines 6–14) — proper test data builder.

### ⚠️ BUG-DFP-1: `monkeypatch.setattr(data_fetcher, "_fetch_yfinance_ohlcv", ...)` (lines 20, 34, 52, 67)
- Patches PRIVATE function (underscore prefix). If renamed, tests break even though behavior unchanged. Same anti-pattern as C-3.
- **Severity:** 🟡

### ⚠️ BUG-DFP-2: `test_fetch_universe_data_still_filters_short_history` (lines 78–84) asserts `out == {}` for 10-row data
- Magic threshold (60+? 30+?) not made explicit. Production threshold change → silent breakage.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 3 (best fallback testing in batch)

---

# 36. `tests/test_data_quality.py` (59 lines)

**Covers:** `src/data_quality.py::DATA_QUALITY_FLOOR, is_above_floor, filter_to_quality`

### ✅ GOOD-DQ-1: `test_floor_is_may_2_2026` (lines 8–10) — explicit constant lock with documented update procedure (line 9). Excellent.
### ✅ GOOD-DQ-2: `test_garbage_date_excluded_conservatively` (lines 25–30) — defensive, conservative behavior validated. Multiple bad inputs.

### ⚠️ BUG-DQ-1: `test_filter_real_picks_log_excludes_fossils` (lines 46–58) reads REAL `data/picks_log.csv`
- Production-data dependency. `if not os.path.exists` skip is graceful but masks the test on fresh clones.
- **Severity:** 🟡

### ⚠️ BUG-DQ-2: `import csv, os` inside function (line 48) — should be at module top.
- **Severity:** 🟡 Minor.

### ⚠️ BUG-DQ-3: `open("data/picks_log.csv")` (line 51) — no explicit `with`/close, no encoding. ResourceWarning on production.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 2

---

# 37. `tests/test_data_readiness_report.py` (181 lines)

**Covers:** `scripts/build_data_readiness_report.py` (build, classify_no_pick, format_markdown, write_outputs)

### ✅ GOOD-DRR-1: 7 tests cover healthy, missing-artifacts, provider-failure, missing-diagnostics, classifier-direct, write-outputs, format. Best classification coverage in batch.
### ✅ GOOD-DRR-2: `test_classify_no_pick_never_invents_strategy_when_pipeline_missing` (lines 128–140) — explicit safety contract test. **Critical for the architecture concern: this test asserts the system does NOT fabricate "no qualified candidates" when pipeline is broken.**

### ⚠️ BUG-DRR-1: `"2026-05-09"` in 6 tests — same DRY.
- **Severity:** 🟡

### ⚠️ BUG-DRR-2: `write_picks` schema discovery via `sorted({key for row in rows for key in row}) or ["pick_date", "ticker"]` (line 25) — same fragility as CL-1.
- **Severity:** ⚠️

### ⚠️ BUG-DRR-3: Tests don't verify `daily_picks_run_status_*.jsonl` SCHEMA (only contents). If JSONL field renamed, classifier may break silently.
- **Severity:** 🟡 Schema gap.

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 2 · ✅ 2

---

# 38. `tests/test_day_trading_engine.py` (191 lines)

**Covers:** `src/day_trading_scorer.py` (private `_score_*` functions, `day_trading_score`, `is_day_tradeable`), `src/market_guard.py` (classify_trade_type, classify_with_day_score), `src/risk_manager.py::atr_trade_plan`

### ✅ GOOD-DTE-1: 22 tests across 3 production modules — comprehensive day-trading engine coverage.
### ✅ GOOD-DTE-2: `test_day_trade_better_rr_than_old` (lines 178–182) — tests R:R IMPROVEMENT, not just absolute. Regression-aware.
### ✅ GOOD-DTE-3: Section dividers (lines 12, 108, 150) make file readable.

### ⚠️ BUG-DTE-1: 5 tests on private `_score_*` functions (lines 16–60). Same anti-pattern as C-3, BR-1.
- **Severity:** 🟡

### ⚠️ BUG-DTE-2: Magic float thresholds throughout (lines 17–20, 27–29, 73, 86, 105)
- `_score_rvol(2.5) == 1.00` — no derivation. If business rules change to `>=2.5 → 0.95`, test breaks.
- **Severity:** 🟡 Tight coupling.

### ⚠️ BUG-DTE-3: `test_day_score_ideal_setup` (lines 63–74) uses `or` assertion at line 74 (`"RVOL" in result["day_reason"] or "ATR" in result["day_reason"]`)
- Loose. Production could output any string and one might match.
- **Severity:** 🟡

### ⚠️ BUG-DTE-4: `test_day_trade_has_max_hold_minutes` asserts `== 240` (line 168) — hardcoded constant. Should reference `risk_manager.MAX_HOLD_MINUTES_DAY` if it exists.
- **Severity:** 🟡

### ⚠️ BUG-DTE-5: File ends mid-line at line 191 (`assert 3.5 <= sl_pct <= 4.5, f"..."`) — missing trailing newline. Will pass tests but flag linters.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 5 · ✅ 3

---

# 39. `tests/test_dedup_sender.py` (100 lines)

**Covers:** `src/dedup_sender.py::should_send, mark_sent, _content_hash, _save_sent, stats, DEDUP_PATH`

### ✅ GOOD-DS-1: `isolate_dedup_file` autouse fixture (lines 13–18) — zero pollution between tests. Best fixture pattern in batch.
### ✅ GOOD-DS-2: 11 tests cover first-send, dup-blocking, different-msgs, empty/whitespace, drift, persistence, window-expiry, corrupt-file, atomic-write, stats.
### ✅ GOOD-DS-3: `test_corrupted_file_recovers` (lines 77–81) — explicit corruption survival test. Defensive.
### ✅ GOOD-DS-4: `test_atomic_write_no_corruption` (lines 84–92) — concurrency-aware test.

### ⚠️ BUG-DS-1: `test_window_expiry` (lines 66–74) uses real `datetime.now()` (line 70)
- Test passes but is technically time-dependent. At second 59→00 boundaries could flake.
- **Severity:** 🟡

### ⚠️ BUG-DS-2: `_content_hash`, `_save_sent` are private (underscore) — tests use them directly (lines 71, 72). Same anti-pattern.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 4 (highest GOOD count in batch)

---

# 40. `tests/test_dry_run_official_no_pick.py` (65 lines)

**Covers:** `scripts/dry_run_official_no_pick.py::build_no_pick_fixture, run_dry_run`, `scripts/validate_daily_no_pick.py`, `src/premarket_decision_contract.py::OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES`

### ✅ GOOD-DRO-1: `for cause in OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES` (line 12) — parametrizes against PRODUCTION constant. **EXEMPLARY** — adding a new cause auto-extends test coverage.
### ✅ GOOD-DRO-2: `test_dry_run_no_pick_cli_passes_for_all_causes` (lines 42–64) — full CLI execution test.

### ⚠️ BUG-DRO-1: `subprocess.run([sys.executable, ...], check=True)` (lines 45–58) — consistent good pattern (unlike batches 106-107) BUT...
- ...still depends on importable production modules. If `scripts/` import-time has issues, fails confusingly.
- **Severity:** 🟡

### ⚠️ BUG-DRO-2: `assert "Lane 1 official no-pick dry-run passed" in result.stdout` (line 61) — string-grep on stdout.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 2

---

# 41. `tests/test_dry_run_official_premarket_pick.py` (56 lines)

**Covers:** `scripts/dry_run_official_premarket_pick.py::run_dry_run`, `src/premarket_decision_contract.py::validate_official_pick`

### ✅ GOOD-DRP-1: `test_run_dry_run_creates_valid_official_pick_artifact` (lines 10–32) — validates BOTH artifact-validation errors AND contract-validation errors. Layered validation.
### ✅ GOOD-DRP-2: Asserts `paper_trading_enabled is False` and `live_trading_enabled is False` (lines 22–23, 53). Critical safety.

### ⚠️ BUG-DRP-1: `assert payload["artifact_id"] == "premarket_official_pick:2026-05-09:DRYRUN"` (line 31) — exact format match. Format change → test breaks.
- **Severity:** 🟡

### ⚠️ BUG-DRP-2: Same stdout-grep pattern as DRO-2.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 2

---

# 42. `tests/test_earnings_analyzer.py` (146 lines)

**Covers:** `src/earnings_analyzer.py::_cached_get, _cache_put, fetch_earnings_history, fetch_recommendations, analyze_earnings`

### ✅ GOOD-EA-1: Cache TTL test (lines 20–32) — uses `os.utime` to age the file. Realistic stale-cache simulation.
### ✅ GOOD-EA-2: `test_fetch_earnings_history_returns_empty_without_key` (lines 43–56) — asserts `requests.get` is NEVER called when no key. Network-isolation guarantee.
### ✅ GOOD-EA-3: 8 tests cover cache, fetch, recommendations, analyze with full + empty data. Good density.
### ✅ GOOD-EA-4: `test_analyze_earnings_computes_quality_metrics` (lines 115–145) tests 12 distinct output fields with exact values. Deep behavior validation.

### ⚠️ BUG-EA-1: `monkeypatch.setattr(ea.requests, "get", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))` (line 98)
- Generator expression hack to raise from a lambda. Cute but unreadable. Use `def boom(...): raise RuntimeError(...)`.
- **Severity:** 🟡

### ⚠️ BUG-EA-2: `_cached_get`, `_cache_put`, `_KEY`, `_CACHE_DIR`, `_CACHE_TTL` all private — tested directly. Same anti-pattern.
- **Severity:** 🟡

### ⚠️ BUG-EA-3: `assert result["earnings_quality"] == 0.81` (line 145) — exact float equality. Floating-point fragility. Should use `pytest.approx`.
- **Severity:** ⚠️

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 2 · ✅ 4

---

# 43. `tests/test_earnings_days_to_earnings.py` (78 lines)

**Covers:** `src/earnings.py::days_to_earnings`

### ✅ GOOD-EDE-1: `FixedDateTime` (lines 21–24) — proper time freeze via subclass. Better than `freezegun`.
### ✅ GOOD-EDE-2: 7 tests cover dict-list-Timestamp, dict-string, DataFrame index shape, DataFrame column shape, past-clamp, empty→999, as_of historical anchor. **Best yfinance-shape coverage in repo.**
### ✅ GOOD-EDE-3: Header docstring (lines 1–13) documents the contract. Excellent intent.

### ⚠️ BUG-EDE-1: `monkeypatch.setattr(earnings, "datetime", FixedDateTime)` (line 34) — module-level datetime replacement
- If earnings module uses `from datetime import datetime` rather than `import datetime`, the patch may miss inner references.
- **Severity:** 🟡

### ⚠️ BUG-EDE-2: No test for `days_to_earnings` raising on garbage input (e.g., `as_of="not-a-date"`).
- **Severity:** 🟡 Edge gap.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 3

---

# 44. `tests/test_edge_case_fuzz.py` (213 lines)

**Covers:** `src/wisdom_base.py`, `src/auto_pause.py`, `src/auto_cooldown.py` — fuzz/edge-case suite

### ✅ GOOD-ECF-1: Header docstring (lines 1–9) explicitly states "MUST NEVER crash" contract. Defensive intent.
### ✅ GOOD-ECF-2: 21 tests grouped in 3 classes — empty, single, missing fields, garbage strings, future dates, unicode, corrupt JSON. Excellent fuzz coverage.
### ✅ GOOD-ECF-3: `try/except + pytest.fail` pattern (lines 88–91, 175–177, 192–196) — explicit "must not crash" contract testing.

### ⚠️ BUG-ECF-1: `test_string_r_multiples` (line 53): `assert isinstance(r["score"], int)` — assumes score is always int. If production switches to float, test breaks even though behavior is correct.
- **Severity:** 🟡

### ⚠️ BUG-ECF-2: `test_load_lessons_corrupt_lines_skipped` asserts `len(out) >= 2` (line 168) — `>=` is loose. Should be `== 2`.
- **Severity:** 🟡

### ⚠️ BUG-ECF-3: `test_kill_list_expired_entries_filtered` (lines 179–183) — passes `cool_off_days=-1` (negative). Production code probably never produces this. Tests theoretical, not real, edge case.
- **Severity:** 🟡 Less-meaningful test.

### ⚠️ BUG-ECF-4: `test_unicode_ticker` (lines 185–188) — uses `"BRK.A"` which is NOT unicode. Title is misleading. True unicode (`"BRK.😀"`?) untested.
- **Severity:** 🟡 Misleading test name.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 4 · ✅ 3

---

# 45. `tests/test_enforcement_readiness.py` (138 lines)

**Covers:** `scripts/check_enforcement_readiness.py` (CLOSED_STATUSES, check_smell_enforce, check_brain_enforce_ev, check_auto_pause, run_all, format_report), `scripts/monitoring_readiness.py::CLOSED_STATUSES`

### ✅ GOOD-ER-1: `test_no_gate_is_falsely_ready_today` (lines 118–125) — **CRITICAL safety test**. Asserts no enforcement gate prematurely flips on with current real data. Defensive.
### ✅ GOOD-ER-2: `test_brain_ev_blocked_when_correlation_negative` (lines 59–69) — tests INVERTED correlation rejection. Smart edge case.
### ✅ GOOD-ER-3: `test_enforcement_closed_statuses_align_with_monitoring_readiness` (lines 127–128) — cross-module consistency check.
### ✅ GOOD-ER-4: `_row(...)` factory (lines 14–23) — consistent test data shape.

### ⚠️ BUG-ER-1: `test_no_gate_is_falsely_ready_today` calls `run_all()` (line 120) — reads REAL production data
- Same anti-pattern as DW-1, CEW-2. Will fail on fresh clone, behavior changes with prod state.
- **Severity:** ⚠️

### ⚠️ BUG-ER-2: `test_run_all_returns_three_gates` (lines 103–107) — hardcodes `len(results) == 3`
- If a 4th gate is added, test breaks even though that's a feature.
- **Severity:** 🟡

### ⚠️ BUG-ER-3: `_row` defaults `pick_date="2026-05-03"` (line 15) — single hardcoded date. Tests don't vary across dates.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 2 · ✅ 4

---

## 🎯 BATCH 108 grand totals

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 3 (DPZ-1, DW-1, DFI-1) |
| ⚠️ Data/safety risk | 4 |
| 🟡 Code smell | 33 |
| ✅ Good code | 38 |
| **Total findings** | **78 across 15 files / ~1,580 lines** |

### 🔥 ARCHITECTURE-RELEVANT FINDINGS THIS BATCH

You said premarket and intraday picks have been broken. **Three findings here directly explain why your tests didn't catch it:**

1. **DPZ-1** — `test_daily_picks_zero_pick_failure.py` is 70 lines of source-grep. It's named "zero pick failure" but only tests that `main.py` source TEXT contains "if not top:". It does NOT verify zero-pick scenarios actually trigger Telegram alerts.

2. **DW-1** — `test_daily_wisdom.py` runs against REAL `data/picks_log.csv`. If your wisdom data is empty (because picks have been failing for a week), this test passes "trivially" by matching `"No closed picks"` — masking the production failure.

3. **DFI-1** — `test_data_fetcher_info_pressure.py` greps the workflow YAML for `DAILY_FETCH_YF_FULL_INFO: false`. If that env var isn't actually being applied at runtime (workflow context bug), test still passes.

### 🎯 GOOD NEWS this batch

**`test_data_readiness_report.py::test_classify_no_pick_never_invents_strategy_when_pipeline_missing`** (DRR-2 GOOD note above) is exactly the kind of safety test you need MORE of. It directly asserts: "if the pipeline broke, do NOT pretend the strategy correctly chose to skip." This test is your repo's best defense against the failure mode you described.

**`test_data_fetcher_provider_fallback.py`** (file 35) is the highest-quality file in this batch — full yfinance→stooq fallback chain coverage, telemetry verification, no source-grep. **Use this file as the template** when you build new behavioral tests.

### Production code coverage from this batch

- `main.py` (grep only — partial)
- `src/daily_wisdom.py`, `src/data_quality.py`, `src/data_fetcher.py`, `src/dedup_sender.py`, `src/earnings_analyzer.py`, `src/earnings.py`, `src/wisdom_base.py`, `src/auto_pause.py`, `src/auto_cooldown.py`, `src/day_trading_scorer.py`, `src/market_guard.py`, `src/risk_manager.py`, `src/premarket_decision_contract.py`
- `scripts/daily_watch_only_learning_report.py`, `scripts/build_data_readiness_report.py`, `scripts/dry_run_official_no_pick.py`, `scripts/validate_daily_no_pick.py`, `scripts/dry_run_official_premarket_pick.py`, `scripts/check_enforcement_readiness.py`, `scripts/monitoring_readiness.py`
- `.github/workflows/daily-picks.yml` (grep only)

### Next batch (109) — files 46–60 alphabetically:
`test_evaluator_consistency.py`, `test_evaluator_status_alignment.py`, `test_evaluator_swing_close.py`, `test_evidence_quality_audit.py`, `test_executor_paper_trade.py`, `test_executor_telegram_lock.py`, `test_executor_validation.py`, `test_executor_workflow_safety.py`, `test_exit_metrics.py`, `test_exit_quality_metrics.py`, `test_failsafe_reasoning.py`, `test_finnhub_data.py`, `test_freshness_guard.py`, `test_full_market_universe.py`, `test_fundamentals.py`
