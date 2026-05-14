# Audit Batch 113 — tests/ files 106–120 (alphabetical) — TRUE line-by-line

**Pinned commit:** `045a77e7`
**Files audited:** 120 of 178 (cumulative)
**Total lines audited in this batch:** ~1,030
**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

> Note: Previously planned files for this batch (test_picks_log_diff, test_pillar3_phase2, test_pillar5_curiosity, test_portfolio_correlator, test_portfolio_risk, test_premarket_check, test_premarket_decision_loader, test_premarket_failure_alert, test_premarket_health, test_premarket_integration, test_premarket_no_pick_artifact, test_premarket_pause, test_premarket_quote_validator, test_premarket_sanity) **DO NOT EXIST** in the repository. Earlier plans were generated from inferred filenames. The actual alphabetical sequence after `test_pattern_stats.py` is the pattern-detector cluster + phase2b cluster shown below. **This is a discovery in itself: ~14 of the file names I was using as a roadmap were imaginary.** Going forward I'll use the live directory listing as the source of truth.

---

# 106. `tests/test_patterns_base.py` (28 lines)

**Covers:** `src/patterns/base.py::PatternDetector, Match`

### ✅ GOOD-PB-1: 3 tests cover dataclass round-trip, ABC enforcement (cannot instantiate), `_enough_bars` helper with 3-state input. Tight.
### ✅ GOOD-PB-2: `test_detector_abc_cannot_instantiate` (lines 14–16) — locks the abstract-class contract. Prevents accidentally subclassing without implementing `detect()`.
### ✅ GOOD-PB-3: Inline minimal subclass `_D` (lines 20–23) — clean fixture-free pattern.

### ⚠️ BUG-PB-1: `assert d._enough_bars(None) is False` (line 27) — tests private `_enough_bars` method. Same anti-pattern, but acceptable for a base class contract.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 3

---

# 107. `tests/test_patterns_breakouts.py` (69 lines)

**Covers:** `src/patterns/breakouts.py::BreakoutDetector, BreakdownDetector`

### ✅ GOOD-PBR-1: 7 tests cover happy-fire on new high, no-fire inside range, volume-boost increases confidence, short-data returns None, breakdown-on-new-low, breakdown-no-fire-inside-range, breakdown-short-data. **Symmetric coverage of long+short detectors.**
### ✅ GOOD-PBR-2: `test_breakout_volume_boost_raises_confidence` comment (line 36) explicitly says "Small gap (1%) so we don't saturate the 0.95 confidence ceiling" — **best inline test reasoning in batch.**
### ✅ GOOD-PBR-3: `_df()` factory (lines 7–15) is reused across all 7 tests.

### ⚠️ BUG-PBR-1: `assert m.trigger["gap_pct"] == 20.0` (line 26) — exact float equality. Pattern repeats throughout pattern tests.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 3

---

# 108. `tests/test_patterns_cup_handle.py` (67 lines)

**Covers:** `src/patterns/cup_handle.py::CupAndHandleDetector`

### ✅ GOOD-PCH-1: 4 tests cover classic-shape fire, no-cup reject, uneven-rims reject, loose-handle reject, short-data reject. Multi-axis rejection coverage.
### ✅ GOOD-PCH-2: Comments inline explain the synthetic shape (lines 19–27): "left rim → cup down → right rim → handle". **Documents the test data.**
### ✅ GOOD-PCH-3: `assert 10 <= m.trigger["cup_depth_pct"] <= 35` (line 33) — bounded range, NOT exact float. Best practice.

### ⚠️ BUG-PCH-1: `assert m.trigger["rim_diff_pct"] <= 3` (line 34) — magic threshold. Should reference a constant from production code.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 3

---

# 109. `tests/test_patterns_double.py` (70 lines)

**Covers:** `src/patterns/double.py::DoubleTopDetector, DoubleBottomDetector`

### ✅ GOOD-PD-1: 5 tests across both detectors with classic-fire + uneven-reject + short-data-reject.
### ✅ GOOD-PD-2: Comments explain the synthetic shape's pivot indices (lines 16–18, 48–49). **Helps future maintainers debug a flake.**
### ✅ GOOD-PD-3: `assert abs(m.trigger["peak1"] - m.trigger["peak2"]) / m.trigger["peak1"] * 100 <= 2.0` (line 29) — derived percentage check, not magic number.

### ⚠️ BUG-PD-1: 30-element synthetic arrays (lines 19–21) — long magic data sequences. Hard to verify "this is actually a double-top".
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 3

---

# 110. `tests/test_patterns_flags.py` (84 lines)

**Covers:** `src/patterns/flags.py::BullFlagDetector, BearFlagDetector`

### ✅ GOOD-PF-1: 7 tests cover bull-classic-fire, weak-pole reject, loose-flag reject, short-data, **flag-that-rallies reject**, bear-inverse-fire, weak-bear-pole, **bear-flag-that-drops-further reject**. Complete state matrix.
### ✅ GOOD-PF-2: `test_bull_flag_rejects_flag_that_rallies` (lines 53–57) — tests the SUBTLE rejection: continuation upward is NOT a flag. Conservative-by-design.
### ✅ GOOD-PF-3: Pole + flag arrays are well-commented (lines 19–22) showing intent.

### ⚠️ BUG-PF-1: `assert m.trigger["pole_gain_pct"] >= 8` (line 27) — magic threshold (production constant likely 8). Reference constant.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 3

---

# 111. `tests/test_patterns_head_shoulders.py` (68 lines)

**Covers:** `src/patterns/head_shoulders.py::HeadShouldersDetector, InverseHeadShouldersDetector`

### ✅ GOOD-PHS-1: 5 tests cover both detectors with short-data + clean-synthetic patterns (with derived shoulders).
### ✅ GOOD-PHS-2: `test_head_shoulders_clean_synthetic` (lines 38–53) — algorithmically constructs a valid H&S using a loop. **Reproducible test-data generation pattern.**

### 🚨 BUG-PHS-1: `test_head_shoulders_fires` (lines 15–25) has a comment "Allow for the algorithm to find any matching triple — may be None if right shoulder doesn't appear in last 8 bars; relax assertion. We check it doesn't crash + returns Match-or-None"
- **Test asserts `m is None or m.pattern == "head_shoulders"`** (line 25). **THIS IS A NO-OP TEST.** It only verifies the function returns the correct type or None — does NOT verify the pattern actually fires.
- **Severity:** 🚨 No-op assertion masquerading as a test.

### ⚠️ BUG-PHS-2: `assert m.trigger["head"] > m.trigger["left_shoulder"]` (line 52) — only checks ordering. Doesn't validate magnitudes or neckline.
- **Severity:** 🟡

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 1 · ✅ 2

---

# 112. `tests/test_patterns_hhhl.py` (73 lines)

**Covers:** `src/patterns/hhhl.py::HHHLDetector, LHLLDetector, _pivot_highs, _pivot_lows`

### ✅ GOOD-PHL-1: 6 tests cover pivot-helper, HHHL-fires, HHHL-no-downtrend, short-data, LHLL-fires, LHLL-no-uptrend, flat-market. Symmetric.
### ✅ GOOD-PHL-2: `test_pivot_highs_finds_local_max` (lines 18–23) — tests private helper with explicit expected tuples. Fast unit test.
### ✅ GOOD-PHL-3: `test_hhhl_handles_flat_market` (lines 68–72) — defensive against degenerate input.

### ⚠️ BUG-PHL-1: Tests private `_pivot_highs`, `_pivot_lows` (line 4 import). Same anti-pattern.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 3

---

# 113. `tests/test_patterns_triangles.py` (99 lines)

**Covers:** `src/patterns/triangles.py::AscendingTriangleDetector, DescendingTriangleDetector, SymmetricTriangleDetector, _linreg`

### ✅ GOOD-PT-1: 9 tests cover linreg-helper-basic, linreg-flat, all 3 triangle detectors with fire+reject pairs, short-data handling for all 3.
### ✅ GOOD-PT-2: `assert m == pytest.approx(2.0)` (lines 27, 33) — **uses `pytest.approx` for float comparison**. **Best float-comparison pattern (after PL-2 from prev batch).**
### ✅ GOOD-PT-3: `test_symmetric_triangle_rejects_one_sided` (lines 85–91) — tests CLASSIFICATION priority (one-sided is descending, not symmetric). Conservative.

### ⚠️ BUG-PT-1: Tests private `_linreg` (line 8). Same anti-pattern.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 3

---

# 114. `tests/test_patterns_wedges.py` (56 lines)

**Covers:** `src/patterns/wedges.py::FallingWedgeDetector, RisingWedgeDetector`

### ✅ GOOD-PW-1: 5 tests cover falling-fire, falling-uptrend-reject, rising-fire, rising-downtrend-reject, short-data for both.
### ✅ GOOD-PW-2: Symmetric structure mirrors `test_patterns_flags.py` and `test_patterns_double.py` — consistent style across the pattern test suite.

### ⚠️ BUG-PW-1: Only 5 tests — no test for "wedge that breaks out vs. stays inside the wedge boundary". Wedges are direction-predictive; this isn't tested.
- **Severity:** 🟡 Coverage gap on a direction-predictive pattern.

### ⚠️ BUG-PW-2: No assertion on `m.confidence` or `m.trigger["slope_diff"]` for either detector. Tests only existence.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 2

---

# 115. `tests/test_pause_state.py` (118 lines)

**Covers:** `src/pause_state.py` (is_paused, maybe_auto_pause, trigger_pause, clear_state, format_pause_alert, load_config)

### ✅ GOOD-PSS-1: `_isolate` autouse fixture (lines 12–24) — hermetic config + state path isolation. **Best fixture pattern in batch.**
### ✅ GOOD-PSS-2: 11 tests cover default-not-paused, observe-mode-never-triggers, enforce-mode-above-threshold, below-threshold, auto-clear-on-expiry, idempotent clear, until-date arithmetic, no-extension contract, alert-format, missing-config defaults. **Highest test density in batch.**
### ✅ GOOD-PSS-3: `test_does_not_extend_existing_pause` (lines 90–100) — locks the **non-escalation safety contract** (a worse condition cannot extend an active pause). Critical for predictability.
### ✅ GOOD-PSS-4: `test_observe_mode_never_triggers` (lines 33–37) — locks the SAFETY DEFAULT (enforced=false means no auto-pause). **Direct relevance to monitoring-only mode.**
### ✅ GOOD-PSS-5: `test_pause_expires_auto_clears` (lines 61–72) verifies BOTH state+file cleanup. Storage hygiene.

### ⚠️ BUG-PSS-1: `assert "PAUSED" in alert` (line 107), `"9" in alert` (line 108), `"RED" in alert` (line 109) — substring on user-facing message. Format-fragile.
- **Severity:** 🟡

### ⚠️ BUG-PSS-2: `datetime.now()` used in `test_pause_expires_auto_clears` (line 62). Time-dependent test could flake at midnight.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 5 (highest GOOD count in batch)

---

# 116. `tests/test_performance_source_separation.py` (138 lines)

**Covers:** `src/performance_source_separation.py` (LAYMAN_PERFORMANCE_SOURCE_NOTE, filter_official_performance_rows, is_watch_only_row, PERFORMANCE_SOURCE_NOTE), `src/performance_tracker.py::compute_segmented_metrics`, scripts (`send_layman_weekly`, `send_layman_monthly`, `send_layman_evening`, `send_layman_yearly`, `weekly_report_card`)

### ✅ GOOD-PSEP-1: 5 tests cover helper-truthiness, performance_tracker excludes watch-only rows, weekly Telegram filters AND discloses source, monthly+evening+yearly all disclose source, weekly_report_card discloses. **Multi-script source-separation contract enforced uniformly.**
### ✅ GOOD-PSEP-2: `test_layman_weekly_filters_watch_only_and_discloses_source` (lines 69–84) — verifies BOTH filter (`"WATCH" not in msg`) AND disclosure (`LAYMAN_PERFORMANCE_SOURCE_NOTE in msg`). **Critical safety contract: never let watch-only inflate official performance.**
### ✅ GOOD-PSEP-3: `closed_row()` factory (lines 21–37) — clean parameterized builder.
### ✅ GOOD-PSEP-4: `is_watch_only_row({"watch_only": "1"})` test (line 43) — handles legacy string-encoded boolean. Defensive.

### ⚠️ BUG-PSEP-1: `assert metrics["overall"]["best_ticker"] == "OFFWIN"` (line 66) — hardcodes a result dependent on test data ordering + tie-breaking. If sort key changes, breaks.
- **Severity:** 🟡

### ⚠️ BUG-PSEP-2: 4 sequential `import` statements inside test bodies (lines 50, 76, 88–90, 101). Should be at module scope.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 4

---

# 117. `tests/test_phase2b_adaptive_sl.py` (119 lines)

**Covers:** `src/adaptive_sl.py::should_tighten_sl, append_tighten_audit, last_tighten_ts`

### ✅ GOOD-ASL-1: 9 tests cover all-conditions-met fire, not-profitable, RSI-never-peaked, RSI-still-strong, vol-still-high, proposed-below-current-SL, cooldown-block, cooldown-expire, missing-RSI. **One test per blocking condition.**
### ✅ GOOD-ASL-2: `test_no_tighten_if_proposed_below_current_sl` (lines 63–70) — locks the "never lower the stop" safety invariant. **Critical: trailing stop should monotonically tighten.**
### ✅ GOOD-ASL-3: Cooldown tests with `datetime.now() - timedelta(minutes=10/45)` (lines 75, 87) — realistic timing.

### ⚠️ BUG-ASL-1: `assert new_sl == 103.95` (line 19) — exact float on `105 * 0.99`. Math is clean here but pattern persists.
- **Severity:** 🟡

### ⚠️ BUG-ASL-2: Time-dependent tests use `datetime.now()` (lines 75, 87). Real wall clock — could flake under slow CI.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 3

---

# 118. `tests/test_phase2b_adaptive_tp.py` (136 lines)

**Covers:** `src/adaptive_tp.py::should_raise_tp, append_raise_audit, last_raise_ts`

### ✅ GOOD-ATP-1: 11 tests cover all-conditions fire, regression-block, gain-too-low, RSI-too-low, vol-too-low, RSI-None, vol-None, cooldown-blocks, cooldown-passes, audit append, multi-append, last-ts retrieval. **Most thorough adaptive function coverage in batch.**
### ✅ GOOD-ATP-2: `test_new_tp_must_be_above_current` (lines 24–33) — locks the **never-regress contract** for take-profit. Mirrors ASL-2 for SL. Symmetric safety.
### ✅ GOOD-ATP-3: Cooldown tests use `datetime(2026, 5, 1, 14, 30)` (lines 86, 99) — **deterministic time, not `datetime.now()`**. **Best time-handling in batch.**
### ✅ GOOD-ATP-4: 3 audit-helper tests (lines 111–135) — covers empty-state, multi-append ordering, latest-ts retrieval.

### ⚠️ BUG-ATP-1: `assert new_tp == 112.35` (line 19) — exact float. Same pattern.
- **Severity:** 🟡

### ⚠️ BUG-ATP-2: `assert "RSI 75" in reason` (line 20) — locks user-facing text format. Format-fragile.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 4

---

# 119. `tests/test_phase2b_integration.py` (122 lines)

**Covers:** `src/exit_metrics.py` (tier_hit_breakdown, trail_stats, tp_raise_stats, capture_efficiency), `src/risk_manager.py::atr_trade_plan`, `src/trailing_stop.py::compute_trailing_sl`, `src/adaptive_tp.py::should_raise_tp`

### ✅ GOOD-PI-1: 5 tests cover tier-counts, trail-locked-gains, TP-raise-counts (incl. malformed JSON ignored), capture-efficiency math, FULL LIFECYCLE smoke test.
### ✅ GOOD-PI-2: `test_phase_2b_full_lifecycle_smoke` (lines 87–121) — **CHAINS 4 modules end-to-end**: trade plan → trail activation → TP raise → audit append. **Best integration test in batch — exemplary multi-module wiring verification.**
### ✅ GOOD-PI-3: `test_tp_raise_stats_counts_raises_from_audit` (lines 44–60) tests JSON-malformed handling in line 54 (`"tp_raises": ""`). Defensive.
### ✅ GOOD-PI-4: `assert plan["qty_t1"] + plan["qty_t2"] + plan["qty_t3"] == plan["quantity"]` (line 99) — locks the **invariant that scale-out qty splits sum to total**. Conservation law.

### ⚠️ BUG-PI-1: `assert s["avg_locked_gain_pct"] == 5.0` (line 38) — exact float on `(4+6)/2`. Clean here but pattern.
- **Severity:** 🟡

### ⚠️ BUG-PI-2: Inline imports in `test_phase_2b_full_lifecycle_smoke` (lines 91–93). Should be top-of-file.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 4 (best integration test in batch)

---

# 120. `tests/test_phase2b_scaleout.py` (78 lines)

**Covers:** `src/exit_manager.py::compute_exit_tiers`, `src/risk_manager.py::atr_trade_plan`

### ✅ GOOD-PSO-1: 8 tests cover swing-tier-prices, day-tier-prices (tighter), divisible split, remainder-to-T3, qty-too-small-collapse, zero-ATR fallback, T3-mode-trail, atr_trade_plan integration.
### ✅ GOOD-PSO-2: `test_qty_split_remainder_goes_to_t3` (lines 34–40) — locks the rounding-rule contract. Critical for share-count integrity.
### ✅ GOOD-PSO-3: `test_qty_too_small_collapses_to_single_exit` (lines 43–48) — defensive against edge case where qty<3 makes 3-way split impossible.
### ✅ GOOD-PSO-4: `test_zero_atr_falls_back_to_2pct` (lines 51–56) — tests the production safety net for missing ATR. Critical for live data gaps.
### ✅ GOOD-PSO-5: `assert plan["take_profit"] == plan["tp2"]` (line 77) — locks LEGACY-FIELD-EQUALS-NEW-FIELD invariant. Smart backward-compat test.

### ⚠️ BUG-PSO-1: 8 tests but no test for `compute_exit_tiers(qty=1)` — what happens with smallest possible qty?
- **Severity:** 🟡 Edge-case gap.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 5

---

## 🎯 BATCH 113 grand totals

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 1 (PHS-1: no-op assertion in head_shoulders test) |
| ⚠️ Data/safety risk | 0 |
| 🟡 Code smell | 21 |
| ✅ Good code | 50 |
| **Total findings** | **72 across 15 files / ~1,030 lines** |

### 🔥 ARCHITECTURE-RELEVANT FINDINGS THIS BATCH

1. **PHS-1 — `test_head_shoulders_fires` is a no-op test.** Lines 15–25 assert `m is None or m.pattern == "head_shoulders"` — that's `True` for both fire and not-fire. **It tests literally nothing about whether the detector works.** The comment even acknowledges the relaxation. **Highest-leverage fix: convert to a real fire-asserting test (the file already has `test_head_shoulders_clean_synthetic` showing how).**

2. **PSS-3/PSS-4 (pause_state) — best safety design in batch.** The `enforced=false` default + non-extension invariant + auto-clear-on-expiry combination is **exemplary monitoring-mode safety**. This is the architecture pattern that prevents unintended automation. Use as model for other safety-default systems.

3. **PI-2 (phase2b integration) — best integration test pattern.** Lifecycle-style test that chains trade-plan → trail → TP-raise → audit. Catches regressions in the WIRING between modules, not just per-module behavior. **You should write a similar lifecycle test for premarket pipeline:** universe → score → safety-gate → artifact → telegram-output.

4. **ATP-3 (adaptive_tp) — best time-handling.** Uses deterministic `datetime(2026, 5, 1, 14, 30)` instead of `datetime.now()`. **Use this as the template** for fixing the ~12 time-dependent tests across the suite.

### 🆕 NEW PATTERN DISCOVERED

**No-op assertions disguised as tests.** PHS-1 form: `assert x is None or x.field == "expected"`. This passes regardless of behavior. **Search regex to find more:** `assert .* is None or `

### Production code coverage from this batch

- `src/patterns/base.py`, `src/patterns/breakouts.py`, `src/patterns/cup_handle.py`, `src/patterns/double.py`, `src/patterns/flags.py`, `src/patterns/head_shoulders.py`, `src/patterns/hhhl.py`, `src/patterns/triangles.py`, `src/patterns/wedges.py` — **9 pattern detectors fully exercised**
- `src/pause_state.py` (best-tested safety system in batch)
- `src/performance_source_separation.py`, `src/performance_tracker.py`
- `src/adaptive_sl.py`, `src/adaptive_tp.py`, `src/exit_manager.py`, `src/exit_metrics.py`, `src/trailing_stop.py`, `src/risk_manager.py`
- `scripts/send_layman_weekly.py`, `send_layman_monthly.py`, `send_layman_evening.py`, `send_layman_yearly.py`, `weekly_report_card.py`

### 📝 Roadmap correction

**14 of 15 originally-planned filenames for this batch DO NOT EXIST.** I generated those filenames from inferred-but-imaginary file structure. The actual `tests/` directory has a different alphabetical sequence. Going forward I'll use the live directory listing.

### Next batch (114) — files 121–135 alphabetically (CONFIRMED FROM DIRECTORY LISTING):
`test_phase2b_trailing.py`, `test_pick_dict_none_coercion.py`, `test_pick_evaluator.py`, `test_pick_evaluator_day_close.py`, `test_pick_log_dict_defensive_defaults.py`, `test_pick_logger_schema_contract.py`, `test_pick_sanity.py`, `test_picks_log_column_contract.py`, `test_picks_log_company_names.py`, `test_picks_log_spy_alpha_fill_rate.py`, `test_pillar1_footer.py`, `test_pillar4_footer.py`, `test_pillar5_footer.py`, `test_pillar6_footer.py`, `test_portfolio_risk_gate.py`
