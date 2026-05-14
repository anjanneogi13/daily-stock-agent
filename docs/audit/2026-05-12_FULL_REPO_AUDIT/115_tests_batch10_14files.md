# Audit Batch 115 — tests/ files 136–149 (alphabetical) — TRUE line-by-line

**Pinned commit:** `3333e617`
**Files audited:** 149 of 178 (cumulative)
**Total lines audited in this batch:** ~1,200
**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

> Note: `test_premarket_decision_contract.py` (originally planned as batch entry 137) was already audited in batch 111 (file #97 / OPA). This batch covers 14 files, not 15.

---

# 136. `tests/test_position_monitor.py` (125 lines)

**Covers:** `src/position_monitor.py` (scan_open_positions, format_telegram_summary)

### ✅ GOOD-PM-1: 10 tests cover no-log, within-budget, swing-overdue, day-immediately-overdue, near-max, closed-ignored, unknown-trade-type-default, format-empty, format-mix, sort-most-overdue. **Complete behavior matrix.**
### ✅ GOOD-PM-2: `test_day_trade_overdue_immediately` (lines 54–62) — locks the **day-trade is overdue at T+1** contract. Critical for your day-pick failure mode.
### ✅ GOOD-PM-3: `test_unknown_trade_type_uses_default` (lines 86–95) — defensive against `trade_type=""`.
### ✅ GOOD-PM-4: All tests use `today=date(2026, 5, 2)` deterministic — **no `datetime.now()` flakiness**. Best time-handling pattern in batch.

### ⚠️ BUG-PM-1: `assert "POSITION MONITOR" in out` (line 108), `"1 OVERDUE" in out` (line 109), `"1 APPROACHING" in out` (line 110) — exact-label substring matches. Format-fragile.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 4

---

# 137. `tests/test_premarket_readiness_gate.py` (107 lines)

**Covers:** `src/premarket_readiness_gate.py::build_premarket_readiness_decision`

### ✅ GOOD-PRG-1: 6 tests cover sufficient-coverage, empty-universe, no-data-fetched, low-coverage, warns-on-errors-passes, fully-degraded-providers. **Complete state matrix for the gate that decides if premarket can ship picks.**
### ✅ GOOD-PRG-2: Each test asserts both `passed` AND `primary_no_pick_cause` fields. **Tests the AUDIT TRAIL, not just outcome.** Critical for downstream classification.
### ✅ GOOD-PRG-3: `test_readiness_warns_on_provider_errors_but_passes_when_coverage_is_enough` (lines 66–90) — locks the **graceful-degradation contract**: warns about provider issues but doesn't block. Conservative-but-not-paranoid.
### ✅ GOOD-PRG-4: Each scenario uses fully-realistic `market_data_health` shape with `providers`/`by_stage`/`attempts`/`successes`/`errors`/`empty`/`rate_limited`/`unauthorized` keys. Real production payload.

### ⚠️ BUG-PRG-1: `assert "provider_rate_limited" in result["warnings"]` (line 88) — locks an EXACT warning code. If renamed, breaks. Should reference a constant.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 4

---

# 138. `tests/test_premarket_sanity_gate.py` (109 lines)

**Covers:** `src/premarket_sanity_gate.py` (evaluate_premarket_sanity, apply_premarket_sanity_decisions, ACTION_*)

### ✅ GOOD-PSG-1: 7 tests cover safe-actionable, missing-price→watch-only, price-at-stop→skip, large-gap-up→half-size, market-skip-all-blocks, splits-official-and-blocked, half-size-reduces-qty.
### ✅ GOOD-PSG-2: Uses CONSTANTS `ACTION_SAFE`, `ACTION_HALF_SIZE`, `ACTION_WATCH_ONLY`, `ACTION_SKIP_TODAY` (lines 2–5) — **no string magic-values**. Best practice.
### ✅ GOOD-PSG-3: `test_half_size_reduces_quantity_before_official_logging` (lines 95–108) — verifies quantity actually drops from 20→10 AND the multiplier 0.5 is recorded in the plan. **Locks the audit trail.**
### ✅ GOOD-PSG-4: `test_market_skip_all_blocks_candidate` (lines 69–78) — locks the **broad-market kill-switch**. Critical safety: regardless of pick quality, market-level "skip_all" overrides.
### ✅ GOOD-PSG-5: `test_missing_fresh_price_is_watch_only` (lines 35–43) — **directly addresses the failure mode mentioned in test_premarket_watch_only.py**. Conservative when price unavailable.

### ⚠️ BUG-PSG-1: `assert result["reason"] == "broad market risk"` (line 78) — exact-string match on user-facing reason. Format-fragile.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 5

---

# 139. `tests/test_premarket_watch_only.py` (10 lines)

**Covers:** `scripts/premarket_check.py` — **100% SOURCE-GREP**

### 🚨 BUG-PWO-1: ENTIRE TEST FILE is 3 substring assertions on `scripts/premarket_check.py`:
- `'"👀 WATCH ONLY", "could not verify fresh price'` (line 7)
- `'"⚠️ HALF SIZE", "could not verify price"' not in text` (line 8)
- `'"actionable": tag not in ("👀 WATCH ONLY", "🚫 SKIP TODAY")'` (line 9)
- **Tests source text, not behavior.** A comment containing those strings would pass. A refactor to use constants would fail despite identical behavior.
- **Severity:** 🚨 100% source-grep test for safety-critical premarket behavior.
- **Right fix:** Test `scripts/premarket_check.py` as a function: feed in a missing-price candidate, assert the returned tag is "WATCH ONLY", not "HALF SIZE".

### ⚠️ BUG-PWO-2: This is the **ONLY test** for `premarket_check.py` (a critical module per filename). 10 lines for what looks like the safety entry-point.
- **Severity:** ⚠️ Coverage gap on a critical-path script.

**Per-file:** 🚨 1 · ⚠️ 1 · 🟡 0 · ✅ 0 (worst test in batch)

---

# 140. `tests/test_probability_engine.py` (296 lines)

**Covers:** `src/probability_engine.py` (compute_probabilistic_decision, SignalState, ProbabilisticDecision, _classify_news, _classify_catalyst, REGIME_ADJUSTMENTS, NEWS_ADJUSTMENTS, CATALYST_ADJUSTMENTS, DEFAULT_P_WIN_PRIOR)

### ✅ GOOD-PE-1: 31 tests grouped in 5 `Test*` classes covering classify-news (6), classify-catalyst (7), SignalState defaults (1), main decision logic (15), math sanity (2), config sanity (5). **Highest-density test file in batch.**
### ✅ GOOD-PE-2: Header docstring (lines 1–8) explicitly says "Probability engine is THE moat. Regressions here = catastrophic." **Best stakes-articulation in repo.**
### ✅ GOOD-PE-3: `test_pwin_clipped_to_sane_range` (lines 149–170) — tests EXTREME inputs (all-bullish AND all-bearish) and asserts `0.05 <= p_win <= 0.95`. **Critical safety: stack-overflow prevention.**
### ✅ GOOD-PE-4: `test_ev_calculation` (lines 188–195) — **derives expected EV from P(win)*TP - P(loss)*SL** and uses `< 0.01` tolerance. Tests math invariant, not magic number.
### ✅ GOOD-PE-5: `test_tp_at_least_minimum_rr` (lines 176–179) — locks the **R:R floor** safety contract.
### ✅ GOOD-PE-6: `test_price_levels_consistent` (lines 181–186) — tests **5 invariants** in one test (SL<entry, TP>entry, buy_zone brackets entry, trigger>entry).
### ✅ GOOD-PE-7: Configuration sanity tests (lines 274–296) verify the dict shape — **prevents typos in REGIME/NEWS/CATALYST adjustments dicts** that would silently fail at runtime.
### ✅ GOOD-PE-8: `test_confidence_low_when_no_stats_even_with_signals` (lines 233–242) — tests the **defensive default**: signals don't make up for absent base data. Conservative.
### ✅ GOOD-PE-9: `test_confidence_high_with_multiple_strong_signals` (lines 214–231) — graceful CI handling: if NVDA stats not available locally, accepts low/medium/high. Avoids false flakes in CI.

### ⚠️ BUG-PE-1: Tests private `_classify_news`, `_classify_catalyst` (lines 21–22). Same anti-pattern.
- **Severity:** 🟡

### ⚠️ BUG-PE-2: `test_no_signals_gives_default_pwin` (line 106) uses `< 0.05` magic tolerance. Should be a named constant.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 9 (highest GOOD count in batch — exemplary test file)

---

# 141. `tests/test_probability_engine_finding5.py` (36 lines)

**Covers:** `src/probability_engine.py::REGIME_ADJUSTMENTS["chop"]`

### ✅ GOOD-PE5-1: Header docstring (line 1) explicitly states "Finding #5: chop regime must produce defensive adjustments, not no-op." Concrete intent.
### ✅ GOOD-PE5-2: 3 tests cover key-exists, more-defensive-than-unknown, end-to-end-EV-differs.
### ✅ GOOD-PE5-3: `test_chop_regime_key_exists` (lines 9–12) — locks the **integration contract** between `regime.py` and `probability_engine.py`. **Bug-class regression: silently downgrading chop→unknown.**
### ✅ GOOD-PE5-4: `test_chop_decision_differs_from_unknown_decision` (lines 23–35) — END-TO-END asserts EV under chop < EV under unknown. Behavior, not just config.

### ⚠️ BUG-PE5-1: Could be merged into `test_probability_engine.py`. Separate file for one finding adds maintenance overhead.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 4

---

# 142. `tests/test_provider_failure_taxonomy.py` (86 lines)

**Covers:** `src/provider_failure_taxonomy.py` (classify_provider_failure, classify_legacy_provider_error, classify_provider_failure_detail, failure_type_for_legacy_error_bucket, legacy_error_bucket_for_failure_type, is_canonical_failure_type, CANONICAL_FAILURE_TYPES)

### ✅ GOOD-PFT-1: 4 parametrized tests with **22 input-output pairs** covering all 11 canonical failure types + 6 legacy bucket mappings + 6 reverse mappings. **Best parametrization density in batch.**
### ✅ GOOD-PFT-2: `test_unknown_provider_failure_is_captured` (lines 36–38) — defensive against `""` and `None`. **Catastrophic-failure handling.**
### ✅ GOOD-PFT-3: `test_classify_legacy_provider_error_preserves_existing_public_buckets` (lines 73–77) — locks the **backward-compat contract** for legacy callers.
### ✅ GOOD-PFT-4: Real provider error strings used as inputs (`"YFRateLimitError: Too Many Requests"`, `"HTTP Error 404: No data found, possibly delisted"` etc.) — production realism.
### ✅ GOOD-PFT-5: `test_classify_provider_failure_detail_returns_both_labels` (lines 80–86) — verifies bidirectional taxonomy mapping. Round-trip safety.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 0 · ✅ 5 (zero issues — exemplary file)

---

# 143. `tests/test_quarterly_report.py` (67 lines)

**Covers:** `src/quarterly_report.py` (_quarter_label, _summary_metrics, _top_movers, generate_report)

### ✅ GOOD-QR-1: 5 tests cover quarter-label, empty-metrics, with-data, top-movers-handles-few-rows, end-to-end smoke.
### ✅ GOOD-QR-2: `test_generate_report_smoke` (lines 56–66) — END-TO-END test. Asserts file exists AND key section headers present.

### 🚨 BUG-QR-1: `test_generate_report_smoke` runs against PRODUCTION data (no monkeypatching of `PICKS_LOG`). If production CSV is bad, this test breaks.
- **Severity:** 🚨 Same production-data-coupling pattern as batch 114 CN-1/SAFR-1.

### ⚠️ BUG-QR-2: 4 of 5 tests use private functions (`_quarter_label`, `_summary_metrics`, `_top_movers`). Same anti-pattern.
- **Severity:** 🟡

### ⚠️ BUG-QR-3: `assert m["win_rate"] == 0.5` (line 40), `m["total_r"] == 1.0` (line 41), `m["avg_alpha_spy"] == 0.5` (line 42), `m["avg_alpha_sec"] == 0.25` (line 43) — 4 exact-float assertions in one test.
- **Severity:** 🟡

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 2 · ✅ 2

---

# 144. `tests/test_regime_aware_sizing.py` (87 lines)

**Covers:** `src/risk_manager.py::atr_trade_plan, regime_risk_multiplier, REGIME_RISK_MULT`

### ✅ GOOD-RAS-1: 11 tests cover all 4 regimes (bull, transition, chop, bear) + unknown defensive default + ratio invariants + audit fields + backward-compat (no-regime arg).
### ✅ GOOD-RAS-2: `test_unknown_defaults_to_defensive` (lines 27–32) tests **4 garbage-input variants** (None, "", "garbage_value", "unknown") — all return 0.7 defensive default. **Best fuzz-style coverage in batch.**
### ✅ GOOD-RAS-3: `test_chop_qty_60pct_of_bull` (lines 55–60) and `test_bear_qty_40pct_of_bull` (lines 63–67) — use **bounded ratios** (0.55–0.65, 0.35–0.45) instead of exact equality. Tolerant of int rounding.
### ✅ GOOD-RAS-4: `test_backward_compat_no_regime_arg` (lines 81–86) — locks the **API stability contract**. Old callers without `regime=` param still get safe behavior.
### ✅ GOOD-RAS-5: `test_multiplier_dict_complete` (lines 35–38) — prevents accidentally dropping a regime from the dict.

### ⚠️ BUG-RAS-1: `assert regime_risk_multiplier("transition") == 0.8` (line 16), `chop == 0.6` (line 20), `bear == 0.4` (line 24) — **exact float equality** on hardcoded multipliers. If the constant 0.6 becomes 0.65 (legitimate tuning), test breaks even though `_plan` ratio test would still pass.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 5

---

# 145. `tests/test_regime_classification.py` (92 lines)

**Covers:** `src/regime.py::market_regime`

### ✅ GOOD-RC-1: 11 tests cover all 4 regimes (bull, transition, chop, bear) at multiple boundary points + distance_pct calculation + bullish-bool legacy compatibility.
### ✅ GOOD-RC-2: `_mock_spy_df` helper (lines 11–17) — **algorithmic synthetic data**: constructs a series whose 200d mean equals SMA but last close is the test parameter. **Mathematically clean fixture.**
### ✅ GOOD-RC-3: Boundary tests at +5%, +4%, 0%, -1.8%, -2%, -3%, -4.8%, -5%, -6%, -20% — **comprehensive boundary coverage** of the 4 regimes.
### ✅ GOOD-RC-4: `test_bullish_boolean_preserved_for_legacy_callers` (lines 84–91) — locks the **backward-compat for legacy `result['bullish']` consumers**. Critical for the dual-API surface.
### ✅ GOOD-RC-5: `_run_with_mocked_spy` patches both `_fetch_spy_with_retry` AND `_save_regime` — prevents real I/O. Hermetic.

### ⚠️ BUG-RC-1: Patches private `_fetch_spy_with_retry` and `_save_regime` (lines 24–25). Same anti-pattern.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 5

---

# 146. `tests/test_regime_finding4.py` (49 lines)

**Covers:** `src/regime.py::market_regime` (Finding #4: total fetch failure)

### ✅ GOOD-RF4-1: Header docstring (line 1) — "Total fetch failure + no cache must NOT default to bullish full-size trades." **Direct relevance to your "premarket failures" — captures a CATASTROPHIC failure mode.**
### ✅ GOOD-RF4-2: 3 tests cover defensive-default-on-failure, transition-fallback-specific, cache-still-used-when-available.
### ✅ GOOD-RF4-3: `test_total_failure_no_cache_returns_defensive` (lines 8–20) — **DOUBLE-asserts**: `regime != "bull"` AND `bullish is False`. Belt + suspenders.
### ✅ GOOD-RF4-4: `test_total_failure_falls_back_to_transition` (lines 23–33) — explicitly checks fallback is `"transition"` (allows trading at 0.8x sizing) NOT `"bull"` (full size disaster).
### ✅ GOOD-RF4-5: `test_cached_regime_still_used_when_available` (lines 36–48) — verifies graceful upgrade from defensive default to cached truth.

### ⚠️ BUG-RF4-1: Could be merged into `test_regime_classification.py`. Separate file pattern.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 5

---

# 147. `tests/test_risk_metrics.py` (131 lines)

**Covers:** `src/risk_metrics.py` (compute_risk_metrics, _sharpe, _sortino, _max_drawdown, format_risk_text)

### ✅ GOOD-RM-1: 11 tests cover no-log, pending-excluded, sharpe-edge-cases, sortino-only-downside, max-DD, max-DD-no-loss, full-metrics, chronological-order, format-empty, format-rendered, constant-returns-Sharpe-None.
### ✅ GOOD-RM-2: `test_chronological_order` (lines 89–99) — verifies **DD reflects time-order, not file-order**. Critical correctness invariant for time-series data.
### ✅ GOOD-RM-3: `test_constant_returns_sharpe_none` (lines 123–130) — defensive against zero-volatility edge case.
### ✅ GOOD-RM-4: `test_sortino_only_penalizes_downside` (lines 54–58) uses **mathematically-derived expected value** with `< 1e-6` tolerance. Best practice.
### ✅ GOOD-RM-5: `_pick` factory (lines 23–30) — clean parametric builder.

### ⚠️ BUG-RM-1: Tests private `_sharpe`, `_sortino`, `_max_drawdown` (lines 44–71). Same anti-pattern.
- **Severity:** 🟡

### ⚠️ BUG-RM-2: `assert m["max_drawdown_pct"] >= -5.1` (line 99) — magic number tolerance for floating-point. Why -5.1 not -5.05?
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 5

---

# 148. `tests/test_rules_violated.py` (48 lines)

**Covers:** `src/wisdom_base.py::add_lesson, LESSONS`, `src/weekly_review.py::rules_violated_on_losers`

### ✅ GOOD-RV-1: 4 tests cover fires-on-loser, skips-winners, handles-empty, handles-bad-data (NaN r_multiple).
### ✅ GOOD-RV-2: `isolated` fixture (lines 9–15) seeds a real lesson via `wb.add_lesson`. Realistic.
### ✅ GOOD-RV-3: `test_rules_violated_handles_bad_data` (lines 43–47) — defensive against `r_multiple="NaN"`. **Critical: real-world CSV data has these.**
### ✅ GOOD-RV-4: `test_rules_violated_handles_empty` (lines 38–40) covers BOTH `[]` and `None` inputs. Defensive.

### ⚠️ BUG-RV-1: `assert "average down" in out[0]` (line 28) — substring on lesson text. If lesson text changes, breaks.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 4

---

# 149. `tests/test_scoring_safety.py` (105 lines)

**Covers:** `src/scoring_safety.py` (assert_config_file_scoring_safety, assert_legacy_sector_boosts_disabled, assert_scoring_safety, scoring_safety_status), `config.yaml`

### ✅ GOOD-SS-1: 8 tests cover live-config-passes, parametrized-rejects-unsafe (5 cases), parametrized-accepts-safe (5 cases), parametrized-rejects-invalid (3 cases), combined-rejects-theme-enable, combined-rejects-sector-boost-before-theme, file-guard-rejects-temp, status-reports-disabled, config-yaml-documents.
### ✅ GOOD-SS-2: 3 parametrized tests with **13 total cases** — best multi-axis safety guard coverage.
### ✅ GOOD-SS-3: `test_current_config_yaml_passes_scoring_safety` (lines 14–15) — locks **THE LIVE CONFIG SHIPS WITH SAFETY ON**. Critical default-safety invariant.
### ✅ GOOD-SS-4: `test_combined_scoring_safety_rejects_theme_scoring_enablement` (lines 60–65) — locks the theme-scoring kill-switch. **Direct relevance to monitoring-only mode safety.**
### ✅ GOOD-SS-5: `test_legacy_sector_boost_guard_rejects_invalid_config` (lines 47–57) — defensive against `"sector": "bad"` AND non-numeric values. Type-fuzz.
### ✅ GOOD-SS-6: `pytest.raises(RuntimeError, match="Legacy blanket sector boosts are disabled")` (line 29) — uses regex match parameter. **Best exception-text checking pattern in batch.**

### 🚨 BUG-SS-1: `test_config_yaml_documents_legacy_boost_disablement` (lines 98–104) source-greps `config.yaml` for EXACT strings:
- `"DISABLED" in text`, `"semi_boost: 1.0" in text`, `"ai_boost: 0.0" in text`, `"Original: semi_boost 1.1, ai_boost 0.2" in text`
- These are HISTORICAL DOCUMENTATION strings. Tests that the comment is preserved. **Source-grep on YAML comments.**
- **Severity:** 🚨 Locks free-text comments as a hard contract.

### ⚠️ BUG-SS-2: `test_current_config_yaml_passes_scoring_safety` couples test to live `config.yaml`. If config legitimately changes, test breaks.
- **Severity:** 🟡 (mitigated by SS-3 being the intended invariant)

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 1 · ✅ 6

---

## 🎯 BATCH 115 grand totals

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 3 (PWO-1 100% source-grep, QR-1 production-data, SS-1 YAML-comment grep) |
| ⚠️ Data/safety risk | 1 |
| 🟡 Code smell | 18 |
| ✅ Good code | 64 |
| **Total findings** | **86 across 14 files / ~1,200 lines** |

### 🔥 ARCHITECTURE-RELEVANT FINDINGS THIS BATCH

1. **PWO-1 — `tests/test_premarket_watch_only.py` is 10 lines of pure source-grep on `scripts/premarket_check.py`.** This is **THE ONLY test for premarket_check.py**. Combined with the fact that you said "premarket picks are broken," this is the single highest-leverage finding of the audit. **Action:** Convert to a behavioral test that calls `premarket_check.main()` (or its decision function) with a mocked missing-price candidate, asserts the returned tag is "WATCH ONLY".

2. **PE-1..9 (probability_engine) — exemplary test file.** 31 tests, header docstring stating stakes, EV math derivation, p_win clipping, R:R floor, price-level invariants, configuration sanity, defensive low-confidence default, **and graceful CI handling for missing local data**. **Use this as the gold-standard template for testing safety-critical math.**

3. **PFT (provider_failure_taxonomy) — only ZERO-issue file in batch.** 22 parametrized cases, real production error strings, bidirectional mapping. **Use as parametrization template.**

4. **RF4 + PE5 (defensive-fallback tests) — directly address your premarket failure modes.** RF4 tests "total fetch failure + no cache must not default to bullish full-size trades." PE5 tests "chop regime must produce defensive adjustments, not silently downgrade to unknown." **These are exactly the failure modes that cause silent bad picks in production.** Both are well-tested.

5. **PSG (premarket_sanity_gate) — best safety-gate test pattern in batch.** Constants for actions, audit-trail assertions, broad-market kill-switch test, watch-only-when-price-missing. **Mirror this structure when adding tests for `premarket_check.py`.**

### 🆕 PATTERN: Source-grep on free-text COMMENTS

**SS-1** is a new sub-pattern: source-grep tests that lock historical documentation comments in config files. If you reorganize the comment, test breaks. **Worse than source-greppping code** because comments are FOR HUMANS — they should be free to evolve.

### Production code coverage from this batch

- `src/position_monitor.py` (10 tests, full coverage)
- `src/premarket_readiness_gate.py` (6 tests, full coverage)
- `src/premarket_sanity_gate.py` (7 tests, full coverage)
- `src/probability_engine.py` (31+3 = 34 tests across 2 files — most-tested module in batch)
- `src/provider_failure_taxonomy.py` (22 parametrized cases)
- `src/quarterly_report.py`, `src/regime.py`, `src/risk_manager.py`, `src/risk_metrics.py`, `src/wisdom_base.py`, `src/weekly_review.py`, `src/scoring_safety.py`
- `scripts/premarket_check.py` (only via 3-line source-grep — **CRITICAL COVERAGE GAP**)
- `config.yaml` (live-config safety + free-text comment grep)

### Next batch (116) — files 150–164 alphabetically (CONFIRMED FROM DIRECTORY LISTING):
`test_scripts_import.py`, `test_sector_alpha_backfill.py`, `test_sector_benchmark.py`, `test_sector_benchmark_subsectors.py`, `test_sector_benchmark_wiring.py`, `test_sector_breakdown.py`, `test_sector_pnl.py`, `test_sector_wisdom.py`, `test_self_awareness.py`, `test_send_late_daily_ideas_telegram.py`, `test_send_layman_daily_reliability.py`, `test_signal_journal_quality.py`, `test_smell_enforcement_readiness.py`, `test_smell_faculty.py`, `test_smell_faculty_finding2.py`
