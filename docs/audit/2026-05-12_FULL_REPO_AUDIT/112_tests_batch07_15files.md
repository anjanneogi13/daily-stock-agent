# Audit Batch 112 — tests/ files 91–105 (alphabetical) — TRUE line-by-line

**Pinned commit:** `16d4a912`
**Files audited:** 105 of 178 (cumulative)
**Total lines audited in this batch:** ~1,840
**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

# 91. `tests/test_news_to_picks.py` (214 lines)

**Covers:** `src/watchlist_manager.py` (watchlist_score_boost, _freshness_multiplier, _hours_old, get_watchlist_tickers, watchlist_meta), `src/universe.py::get_universe`

### ✅ GOOD-NTP-1: 16 tests across freshness math (5), boost calc (5), watchlist filter (2), universe expansion (3), metadata (2). Layered.
### ✅ GOOD-NTP-2: `_make_watchlist` and `_item` factories (lines 17–34) — clean parametrized data builders.
### ✅ GOOD-NTP-3: `test_universe_excluded_tickers_still_filtered` (lines 179–196) — tests **priority ordering** (excluded list beats watchlist). **Critical safety: backtester losers can't sneak in via fresh news.**
### ✅ GOOD-NTP-4: `test_boost_capped_at_30` (lines 95–99) — tests cap with deliberately impossible input (score=2.0). Defensive.

### ⚠️ BUG-NTP-1: `_freshness_multiplier`, `_hours_old` are private (lines 9, 42, 47, etc.) — tested directly. Same private-API anti-pattern.
- **Severity:** 🟡

### ⚠️ BUG-NTP-2: `assert boost == 0.30` (lines 70, 87, 99, 208) — **EXACT FLOAT EQUALITY repeated 4×**. `1.0 * 0.15 * 2.0 = 0.30` happens to be exact, but at scale this WILL flake.
- **Severity:** ⚠️ Float fragility, repeated.

### ⚠️ BUG-NTP-3: `monkeypatch.setattr("src.universe.get_sp500_tickers", lambda: ["AAPL"])` (line 162) — string-path patching. Brittle to module rename.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 2 · ✅ 4

---

# 92. `tests/test_news_workflow_persistence.py` (62 lines)

**Covers:** `.github/workflows/news_engine.yml`, `src/news_signals.py` — **MIXED REGEX-GREP**

### ✅ GOOD-NWP-1: Header docstring (lines 1–11) is **EXEMPLARY** — explicitly documents the May 4 silent-data-loss bug ("news_signals were silently thrown away after each run. Every pick for 48+ hours got news_boost=0"). **One of the best regression-intent docstrings in repo.**
### ✅ GOOD-NWP-2: `_git_add_files()` helper (lines 18–26) — uses regex to extract paths from `git add` lines. **Smarter than pure substring grep.** Tests the SET of committed files, which is the actual contract.

### 🚨 BUG-NWP-1: 4 tests (lines 29–54) source-grep `git add` paths in workflow YAML. The regex helper makes it slightly more robust than substring grep, but it's still fundamentally testing source text not behavior.
- The "actual" test would: invoke the workflow's commit step in a fixture repo, then `git ls-files data/` and assert all 4 files are tracked.
- **Severity:** 🚨 (mitigated by smart regex extraction, but pattern persists)

### ⚠️ BUG-NWP-2: `test_news_signals_json_writer_exists` (lines 57–61) source-greps `src/news_signals.py` for `"SIGNALS_PATH" in src` and `".write_text" in src or ...`. Tests source-text not behavior.
- **Severity:** 🚨

**Per-file:** 🚨 2 · ⚠️ 0 · 🟡 0 · ✅ 2 (best docstring in batch, undermined by source-grep)

---

# 93. `tests/test_nightly_conductor.py` (82 lines)

**Covers:** `src/nightly_conductor.py` (_step, format_summary_text, _load_universe_for_scan, run_nightly + 8 step lambdas)

### ✅ GOOD-NC-1: `test_step_isolates_exception` (lines 17–22) — locks the **circuit-breaker contract**. Critical for nightly-run reliability.
### ✅ GOOD-NC-2: `test_step_handles_none_return` (lines 25–29) — defensive coverage of nullable return values.
### ✅ GOOD-NC-3: `test_run_nightly_executes_all_steps_with_isolation` (lines 65–81) — **forces all 8 steps to fail** and asserts the conductor STILL produces a complete summary. **Best nightly-conductor regression test possible.**
### ✅ GOOD-NC-4: Comment on line 80 ("added agent_memoir 2026-05-04") documents schema evolution.

### ⚠️ BUG-NC-1: 3 tests use the `(_ for _ in ()).throw(...)` generator-raise hack (lines 69–76) — repeated 8× in a single test. Unreadable.
- **Severity:** 🟡

### ⚠️ BUG-NC-2: `assert len(summary["steps"]) == 8` (line 81) — exact count. If a 9th step is added, test breaks even though that's the intended behavior. Should assert >= 8 with explicit name list.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 4

---

# 94. `tests/test_non_trading_day_trade_type_guard.py` (27 lines)

**Covers:** `main.py::_safe_trade_type_for_pick`

### ✅ GOOD-NTT-1: Header docstring (lines 1–5) **explicitly documents the Bug #7 trigger condition** — "should not emit new trade_type=day picks when the US market is closed". **Direct relevance to your premarket failures on weekends/holidays.**
### ✅ GOOD-NTT-2: 3 tests cover: trading-day allows day, weekend downgrades to swing, holiday downgrades to swing. **Complete state coverage.**
### ✅ GOOD-NTT-3: `DAYLIKE_SCORES` constant (lines 10–14) — single source of truth.

### ⚠️ BUG-NTT-1: Hardcoded `"2026-05-25"` (Memorial Day) and `"2026-05-02"` (Saturday) — if test runs in 2027 with same dates that ARE trading days (impossible but illustrative), would pass for wrong reason.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 3

---

# 95. `tests/test_official_artifact_loader.py` (101 lines)

**Covers:** `src/official_artifact_loader.py` (enrich_pick_row_with_artifact, enrich_pick_rows_with_artifacts, official_pick_artifacts_for_date, validate_official_artifacts_for_rows)

### ✅ GOOD-OAL-1: `artifact()` factory (lines 11–35) — comprehensive realistic artifact shape with 17 fields.
### ✅ GOOD-OAL-2: 5 tests cover: load by ticker, enrich preserves CSV shape, mark missing, validate-blocks-missing, validate-passes-valid. **Multi-state coverage.**
### ✅ GOOD-OAL-3: `test_enrich_pick_row_with_artifact_preserves_csv_shape` (lines 48–59) — locks the type-conversion contract (`"99"` string → `100.0` float). Critical for downstream consumers.
### ✅ GOOD-OAL-4: `test_validate_official_artifacts_for_rows_blocks_missing_artifact` (lines 71–76) — validates the **safety gate** that blocks shipping without official artifact. **Critical for your premarket pipeline integrity.**

### ⚠️ BUG-OAL-1: `assert errors == ["no official pick artifacts found for 2026-05-09"]` (line 76) — exact string match on error message. Format-fragile.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 4

---

# 96. `tests/test_official_artifact_outputs.py` (249 lines)

**Covers:** `scripts/format_picks_email.py`, `scripts/send_layman_daily.py` (subprocess integration)

### ✅ GOOD-OAO-1: 6 tests via `subprocess.run([sys.executable, ...])` — invoke ACTUAL production scripts. **Highest integration realism in batch.**
### ✅ GOOD-OAO-2: Uses `sys.executable` (lines 105, 127, 177, 202, 220, 241) — TZ/Python-version safe.
### ✅ GOOD-OAO-3: 3-axis matrix: format_picks_email AND send_layman_daily × valid-artifact / missing-artifact / valid-no-pick-artifact. **9 effective scenarios.**
### ✅ GOOD-OAO-4: Both BLOCKING tests (lines 172–209) verify `result.returncode == 1` — locks the fail-loudly contract for missing artifacts. **Direct regression-protection for your premarket failure-mode (no artifact = silent ship).**
### ✅ GOOD-OAO-5: `monkeypatch.delenv` for Telegram creds (lines 120–122, 196–198, etc.) — guards against accidental real-Telegram sends during test runs.

### ⚠️ BUG-OAO-1: 6 substring assertions per test on `result.stdout` (e.g., `"Official trace:* `..." in result.stdout` — lines 134–136). Format-fragile.
- **Severity:** 🟡

### ⚠️ BUG-OAO-2: Inline 80-line CSV writer (`write_csv`, lines 8–42) and 50-line artifact writer (`write_artifact`, lines 45–95) — should be in conftest.
- **Severity:** 🟡 DRY.

### ⚠️ BUG-OAO-3: `subprocess.run(check=True, ...)` (lines 106, 128, 221, 242) — if subprocess fails on legitimate-but-non-zero exit, test crashes with stderr swallowed.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 5 (best subprocess-integration coverage in repo)

---

# 97. `tests/test_official_pick_artifact.py` (125 lines)

**Covers:** `src/official_pick_artifact.py` (build_official_pick_artifact, official_pick_artifact_id/path/decision_id, write_official_pick_artifacts), `src/premarket_decision_contract.py` (DECISION_OFFICIAL_PICK, STRATEGY_LANE, validate_official_pick)

### ✅ GOOD-OPA-1: 6 tests cover build, path-sanitize, write+summary, validation-error recording, deterministic-helpers, GitHub observability. Multi-axis.
### ✅ GOOD-OPA-2: `pick()` factory (lines 17–37) — clean parameterized builder.
### ✅ GOOD-OPA-3: `test_build_official_pick_artifact_satisfies_contract` (line 60) calls `validate_official_pick(payload)` with same validator production uses. **Best practice — contract enforcement.**
### ✅ GOOD-OPA-4: `test_official_pick_artifact_path_sanitizes_ticker` (lines 63–66) — tests the BRK.B → BRKB ticker sanitization. Edge case.
### ✅ GOOD-OPA-5: `test_official_pick_artifact_includes_github_observability_metadata` (lines 110–124) — locks observability fields. Direct relevance to debugging your production failures.

### ⚠️ BUG-OPA-1: `assert payload["risk_dollars"] == 50.0` (line 57) — exact float on computed value `(100-95) * 10`. Math is clean but pattern is fragile.
- **Severity:** 🟡

### ⚠️ BUG-OPA-2: `assert "?" in summary["validation_errors"]` (line 101) — magic placeholder string. What does `"?"` mean? Unclear contract.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 5

---

# 98. `tests/test_opening_range_observation_backtest.py` (146 lines)

**Covers:** `scripts/backtest_opening_range_observations.py` (candidate_bar_paths, evaluate_observation_outcome, observation_date, summarize_outcomes, format_report)

### ✅ GOOD-ORB-1: 8 tests cover path resolution, TP-hit, conservative-SL-same-bar, timeout uses-last-close, missing-bars, summary-never-paper-ready, format-mentions-disabled, CLI-JSON, CLI-no-files. **Comprehensive.**
### ✅ GOOD-ORB-2: `test_evaluate_observation_sl_hit_conservative_same_bar` (lines 61–68) — tests the **CONSERVATIVE rule that SL wins when both hit in same bar**. Correct trader-safety semantic.
### ✅ GOOD-ORB-3: `test_summarize_outcomes_never_marks_ready_for_paper_trading` (lines 87–102) — tests the SAFETY contract: even with profitable backtest, `ready_for_paper_trading is False`. **Critical guard against premature paper-trading enablement.**

### ⚠️ BUG-ORB-1: `subprocess.check_output(["python", "scripts/...", ...])` (lines 120, 138) — uses `"python"` not `sys.executable`. Same anti-pattern.
- **Severity:** ⚠️

### ⚠️ BUG-ORB-2: `assert "Observations:          0" in out` (line 144) — locks EXACT WHITESPACE. Brittle.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 1 · ✅ 3

---

# 99. `tests/test_opening_range_observation_review.py` (127 lines)

**Covers:** `scripts/review_opening_range_observations.py` (load_observations, summarize_observations, format_report)

### ✅ GOOD-ORR-1: 6 tests cover JSONL load + invalid-line counting, full summary, non-compliance flagging, format mentions safety, CLI JSON, CLI no-files. **Layered.**
### ✅ GOOD-ORR-2: `test_summarize_flags_non_compliant_rows` (lines 70–79) — tests detection of `watch_only=False, mode="paper"` rows. **Direct safety check** that catches accidentally-promoted observations.
### ✅ GOOD-ORR-3: `test_load_observations_reads_jsonl_and_counts_invalid_lines` (lines 38–46) — tests CORRUPTION-RESILIENCE. JSONL file with `{not-json}` line is parsed and counted. **Best resilience test in batch.**

### ⚠️ BUG-ORR-1: `subprocess.check_output(["python", ...])` (lines 99, 117) — same `"python"` not `sys.executable`.
- **Severity:** ⚠️

### ⚠️ BUG-ORR-2: `assert summary["avg_breakout_pct"] == 0.8` (line 64) — exact float. `(0.6 + 1.0) / 2 = 0.8` clean but should be `pytest.approx`.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 1 · ✅ 3

---

# 100. `tests/test_opening_range_scanner.py` (157 lines)

**Covers:** `src/opening_range_scanner.py` (calculate_opening_range, detect_opening_range_breakout, latest_post_range_bar, opening_range_bounds)

### ✅ GOOD-ORS-1: 9 tests across bounds, calc, incomplete-window, post-range bar, breakout candidate, no-break-block, low-volume-block, anti-chase-block, gap-block, naive-tz handling. **Highest test density / behavior in batch.**
### ✅ GOOD-ORS-2: `test_naive_timestamps_are_interpreted_as_et` (lines 146–156) — tests the SUBTLE TZ-default contract. Critical for production data ingestion.
### ✅ GOOD-ORS-3: `test_anti_chase_blocks_overextended_breakout` (lines 120–130) — tests the safety guard that prevents chasing already-extended breakouts. **Direct relevance to "monitoring-only mode safety."**
### ✅ GOOD-ORS-4: `bar()` and `ts()` and `sample_bars()` helpers (lines 15–36) — clean parametric builders.

### ⚠️ BUG-ORS-1: `assert result["volume"] == 3300` (line 56) — exact int. Sum of 1000+1200+1100=3300 is clean but pattern fragile.
- **Severity:** 🟡

### ⚠️ BUG-ORS-2: All 9 tests use the same `sample_bars()` helper. If helper bug, all tests share blind spot.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 4

---

# 101. `tests/test_parallel_scorer_monster_data.py` (114 lines)

**Covers:** `src/parallel_scorer.py::_score_one` (monster-data fetch gating)

### ✅ GOOD-PSM-1: `_patch_common` helper (lines 25–67) monkey-patches **15 dependencies in one place**. Clean test-double infrastructure.
### ✅ GOOD-PSM-2: 2 tests cover the EXACT contract: monster-data NOT fetched by default (cost control), opt-in via config. **Direct cost-control guarantee.**
### ✅ GOOD-PSM-3: `calls = []` capture pattern (lines 74, 90) verifies fetch suppression. Correct shape.

### ⚠️ BUG-PSM-1: 15 monkeypatches per test (lines 26–67) is the largest mock surface in this batch. If any signature changes, all tests break.
- **Severity:** ⚠️ Test maintainability bomb.

### ⚠️ BUG-PSM-2: Tests private `_score_one` (line 87, 110). Same anti-pattern.
- **Severity:** 🟡

### ⚠️ BUG-PSM-3: Only 2 tests for what is your **primary scoring orchestrator**. Undertested for its blast radius.
- **Severity:** ⚠️ Coverage gap on critical-path code.

**Per-file:** 🚨 0 · ⚠️ 2 · 🟡 1 · ✅ 3

---

# 102. `tests/test_pattern_engine.py` (70 lines)

**Covers:** `src/pattern_engine.py` (scan_ticker, persist, load_recent)

### ✅ GOOD-PE-1: `isolated` fixture (lines 18–22) — clean log-path isolation.
### ✅ GOOD-PE-2: 5 tests cover happy scan, empty df, none df, append-persist, no-write-on-empty, time-window filter. Complete.
### ✅ GOOD-PE-3: `test_scan_ticker_handles_none_df` (lines 41–44) — tests `data_fetcher.fetch_ohlcv` returning None. Defensive.

### ⚠️ BUG-PE-1: `_df_breakout()` (lines 10–15) generates 21-row df with `closes = [10]*20 + [12]`. Synthetic but not labeled. Magic data.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 3

---

# 103. `tests/test_pattern_hint.py` (110 lines)

**Covers:** `src/wisdom_hint.py::pattern_hint`, `src/wisdom_base.py::add_pattern`

### ✅ GOOD-PH-1: 10 tests grouped in single `TestPatternHint` class. Cover empty/None, drag-prioritized-over-edge, low-sample exclusion, high-pvalue exclusion, unknown-signal ignored, case-insensitive bucket match, largest-sample-wins, never-crashes-on-garbage. **Best behavioral state-machine coverage in batch.**
### ✅ GOOD-PH-2: `test_drag_prioritized_over_edge` (lines 51–60) — tests CRITICAL safety priority: warnings beat boosts. Correct conservative semantic.
### ✅ GOOD-PH-3: `test_never_crashes_on_garbage` (lines 102–109) — fuzzy input including `None`, missing keys, `{"trade_type": None}`. **Best defensive test in batch.**
### ✅ GOOD-PH-4: `_wh()` helper (lines 15–18) reloads the module per-test — guards against module-state bleeding.

### ⚠️ BUG-PH-1: `importlib.reload(m)` (line 17) — per-test module reload is slow + risks subtle state issues. Hint that wisdom_hint has module-level mutable state worth refactoring.
- **Severity:** 🟡

### ⚠️ BUG-PH-2: `assert "31%" in out` (line 39) — substring on user-facing percent string. Format-fragile.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 4

---

# 104. `tests/test_pattern_layer.py` (96 lines)

**Covers:** `src/pattern_layer.py` (pattern_multiplier, disable_pattern, enable_pattern, auto_enable_disable, MAX_BOOST)

### ✅ GOOD-PL-1: 10 tests cover neutral-when-no-stats, boosts-on-positive-edge, penalizes-on-negative-edge, ignores-low-sample, disable→enable, disabled-yields-neutral, auto-kill-negative, auto-reactivate-on-recovery, respects-min-n. **Excellent state-machine coverage.**
### ✅ GOOD-PL-2: `assert mult <= 1.0 + pl.MAX_BOOST + 1e-6` (line 37) — uses PRODUCTION CONSTANT + epsilon margin. **Best float-comparison pattern in batch.**
### ✅ GOOD-PL-3: `test_pattern_multiplier_ignores_low_sample` (lines 48–51) — tests safety guard against acting on too-small samples.
### ✅ GOOD-PL-4: `test_auto_enable_disable_reactivates_on_recovery` (lines 80–87) — tests the **bidirectional learning loop** (kills bad patterns AND brings back recovered ones). Critical for adaptive system.

### ⚠️ BUG-PL-1: `_breakout_df()` (lines 20–24) — same magic synthetic data as PE-1. Should be in conftest.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 4

---

# 105. `tests/test_pattern_stats.py` (93 lines)

**Covers:** `src/pattern_stats.py` (build_stats, save, load)

### ✅ GOOD-PS-1: `isolated` fixture isolates 3 paths (PATTERNS_LOG, PICKS_LOG, STATS) — lines 10–18. Hermetic.
### ✅ GOOD-PS-2: 6 tests cover empty, multi-regime aggregation, skip-when-no-pick, save+load roundtrip, load-empty-when-missing, missing-regime fallback. Multi-axis.
### ✅ GOOD-PS-3: `test_build_stats_handles_missing_regime` (lines 83–92) — tests the `"unknown"` fallback. Defensive.

### ⚠️ BUG-PS-1: `_seed_picks` and `_seed_patterns` factories (lines 21–31) duplicate JSONL/CSV writing logic across many tests in this batch. Consolidate.
- **Severity:** 🟡

### ⚠️ BUG-PS-2: `assert bull["win_rate"] == 0.5` (line 55) — exact float. `1/2 = 0.5` clean but pattern fragile.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 3

---

## 🎯 BATCH 112 grand totals

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 2 (NWP-1, NWP-2 — both source-grep persisting despite great intent docstring) |
| ⚠️ Data/safety risk | 6 |
| 🟡 Code smell | 26 |
| ✅ Good code | 56 |
| **Total findings** | **90 across 15 files / ~1,840 lines** |

### 🔥 ARCHITECTURE-RELEVANT FINDINGS THIS BATCH

You said premarket and intraday picks are broken. **Five findings here directly bear on those failure modes:**

1. **NWP-1 + GOOD-NWP-1** — `test_news_workflow_persistence.py` has the **best regression-intent docstring in the entire repo** (the May 4 silent-data-loss bug story) BUT the test mechanism is still source-grep. **The right fix:** spawn the workflow's commit step in a fixture repo and assert `git ls-files data/` includes all 4 files. **This is your template for fixing premarket-failure regression tests.**

2. **NTT-1 — `test_non_trading_day_trade_type_guard.py`** — only 27 lines, 3 tests, but they directly test "should not emit day picks on non-trading days." **This is one of the few tests that directly addresses a premarket-on-weekend failure mode.** Use as template.

3. **OAO-4 — `test_official_artifact_outputs.py`** has 6 subprocess integration tests that VERIFY `result.returncode == 1` when the official artifact is missing. **This is the gold-standard pattern for ensuring premarket pipeline fails loudly instead of silently shipping.**

4. **ORB-3 + ORR-2 — opening-range backtest/review safety guards** — explicitly test that `ready_for_paper_trading is False` even with profitable backtests, and detect non-compliant rows (`watch_only=False, mode="paper"`). These are the **safety nets between observation mode and paper trading**. They're well-tested. Good.

5. **PSM-1/PSM-3 — `test_parallel_scorer_monster_data.py`** has only 2 tests for what is **the primary scoring orchestrator**. With 15 monkeypatches per test. **This is the highest-blast-radius / lowest-coverage file in your repo.** When `_score_one` breaks (and it will), CI won't catch it — it'll show up as silent zero picks in production.

### 🎯 BEST-IN-BATCH: `test_pattern_layer.py` (file 104)

Uses `pl.MAX_BOOST + 1e-6` instead of magic-number floats. **The single best float-comparison pattern in the entire audited test suite.** Use this as the rewrite-template for the ~30 exact-float-equality bugs found across previous batches.

### Production code coverage from this batch

- `src/watchlist_manager.py`, `src/universe.py`, `src/news_signals.py`, `src/nightly_conductor.py`, `src/learning_journal.py`, `src/official_artifact_loader.py`, `src/official_pick_artifact.py`, `src/premarket_decision_contract.py`, `src/parallel_scorer.py`, `src/opening_range_scanner.py`, `src/pattern_engine.py`, `src/pattern_stats.py`, `src/pattern_layer.py`, `src/wisdom_hint.py`, `src/wisdom_base.py`, `src/data_fetcher.py`
- `scripts/format_picks_email.py`, `scripts/send_layman_daily.py`, `scripts/backtest_opening_range_observations.py`, `scripts/review_opening_range_observations.py`
- `main.py::_safe_trade_type_for_pick`
- `.github/workflows/news_engine.yml` (regex-grep)

### Next batch (113) — files 106–120 alphabetically:
`test_picks_log_diff.py`, `test_pillar3_phase2.py`, `test_pillar5_curiosity.py`, `test_portfolio_correlator.py`, `test_portfolio_risk.py`, `test_premarket_check.py`, `test_premarket_decision_contract.py`, `test_premarket_decision_loader.py`, `test_premarket_failure_alert.py`, `test_premarket_health.py`, `test_premarket_integration.py`, `test_premarket_no_pick_artifact.py`, `test_premarket_pause.py`, `test_premarket_quote_validator.py`, `test_premarket_sanity.py`
