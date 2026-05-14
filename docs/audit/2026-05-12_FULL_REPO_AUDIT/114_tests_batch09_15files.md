# Audit Batch 114 — tests/ files 121–135 (alphabetical) — TRUE line-by-line

**Pinned commit:** `2a153f45`
**Files audited:** 135 of 178 (cumulative)
**Total lines audited in this batch:** ~1,375
**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

# 121. `tests/test_phase2b_trailing.py` (91 lines)

**Covers:** `src/trailing_stop.py::compute_trailing_sl, trail_status`

### ✅ GOOD-PT-1: 9 tests cover no-activation-below-3pct, exact-3pct activation, never-moves-down, follows-new-highs, custom-thresholds, peak==entry, peak<entry, entry=0 safety, trail_status active+inactive. **Complete state-machine coverage.**
### ✅ GOOD-PT-2: `test_sl_only_moves_up_never_down` (lines 26–32) — locks the **monotonic-tighten safety invariant**. Critical for trailing-stop semantics.
### ✅ GOOD-PT-3: `test_invalid_entry_returns_unchanged` (lines 70–73) — defensive against entry=0 (data corruption).
### ✅ GOOD-PT-4: `test_trail_status_active_flag` (lines 78–83) — verifies derived booleans match underlying state.

### ⚠️ BUG-PT2-1: `assert new_sl == 100.94` (line 22), `== 102.9` (line 39), `== 107.8` (line 42), `== 102.82` (line 53) — **5 exact-float-equality assertions** on computed values. Same recurring fragility.
- **Severity:** ⚠️

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 0 · ✅ 4

---

# 122. `tests/test_pick_dict_none_coercion.py` (54 lines)

**Covers:** `main.py` (lines documenting Bug #8b) — **MIXED PURE-PYTHON + SOURCE-GREP**

### ✅ GOOD-DNC-1: Header docstring (lines 1–7) is **EXEMPLARY** — explicitly documents the Python gotcha (`dict.get(key, default)` returns None when key exists with None) AND the production bug it caused (sector cache → empty CSV column).
### ✅ GOOD-DNC-2: 3 pure-Python tests (lines 10–30) document the gotcha generically. **Self-contained, no source dependency.** Best Python-idiom regression doc in repo.
### ✅ GOOD-DNC-3: `test_dict_get_or_pattern_preserves_truthy_values` (lines 26–30) — REGRESSION GUARD: prevents over-correction (the `or default` pattern must not clobber valid 0.5, "SPY", 144.73). Defensive of the fix itself.

### 🚨 BUG-DNC-1: `test_main_py_sclose_assignment_uses_or_idiom` (lines 33–43) source-greps `main.py` for an EXACT 36-character string `'_sclose = p.get("_sector_close") or ""'`.
- Black/isort would break this. Refactoring the variable name from `_sclose` to `sector_close_str` would break this. **Source-grep with character-level fragility.**
- **Severity:** 🚨

### 🚨 BUG-DNC-2: `test_main_py_setf_assignment_uses_or_idiom` (lines 46–53) — same pattern, second exact-string source-grep on main.py.
- **Severity:** 🚨

**Per-file:** 🚨 2 · ⚠️ 0 · 🟡 0 · ✅ 3 (best Python-idiom doc + worst source-grep specificity in batch)

---

# 123. `tests/test_pick_evaluator.py` (236 lines)

**Covers:** `src/pick_evaluator.py` (evaluate_pending, _fetch_ohlc, unreachable_entry detection, SL/TP/tie-break/still-open logic)

### ✅ GOOD-PE-1: Header docstring (lines 1–7) — **6 SEMI picks with entry $2-$20 ABOVE that day's high were marked sl_hit**. Concrete production-failure regression doc. **Best regression-intent docstring of batch.**
### ✅ GOOD-PE-2: 9 tests cover unreachable-above-high, unreachable-below-low, within-range-proceeds, 0.5pct-tolerance, sl_hit, tp_hit, tie-break-near-tp, tie-break-near-sl, still-open. **Complete behavior matrix for the broken function.**
### ✅ GOOD-PE-3: `_seed_pick` (lines 27–59) factory writes a 24-field CSV row. Realistic.
### ✅ GOOD-PE-4: `test_unreachable_entry_above_high_marked` asserts `counts["sl_hits"] == 0` (line 81) — **explicit negative assertion** ensures the bug is NOT silently re-introduced. Critical pattern.
### ✅ GOOD-PE-5: `test_05pct_tolerance_for_rounding` (lines 122–137) — tests the exact tolerance threshold. Catches over-strict OR over-lax tolerance regressions.

### ⚠️ BUG-PE-1: 9 tests each duplicate the `monkeypatch.setattr(pick_evaluator, "_fetch_ohlc", ...)` boilerplate. Should be a fixture.
- **Severity:** 🟡

### ⚠️ BUG-PE-2: `from src import pick_evaluator` inside each test body (lines 67, 89, 106, etc.) — should be top-of-file.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 5 (best regression docstring in batch)

---

# 124. `tests/test_pick_evaluator_day_close.py` (162 lines)

**Covers:** `src/pick_evaluator.py::evaluate_pending` (day-trade force-close logic)

### ✅ GOOD-DC-1: Header docstring (lines 1–11) — **explicitly documents MPWR 2026-05-02 victim**. Names the actual ticker that triggered the bug. **Best concrete regression doc in batch.**
### ✅ GOOD-DC-2: 7 tests cover day-close-on-close, sl-still-wins, tp-still-wins, swing-NOT-affected, all-cols-populated, counts-include-day_close, **WEEKEND day-pick uses next trading bar**. Edge cases comprehensive.
### ✅ GOOD-DC-3: `_FrozenDT` subclass (lines 66–69) for deterministic time. **Best frozen-time pattern in batch.** Subclassing instead of patching `now` directly preserves `strptime` and arithmetic.
### ✅ GOOD-DC-4: `test_swing_pick_no_hit_is_NOT_day_closed` (lines 108–116) — REGRESSION GUARD that the day-trade fix doesn't accidentally apply to swing trades. Critical.
### ✅ GOOD-DC-5: `test_day_pick_on_weekend_uses_next_trading_bar` (lines 144–161) — tests **the failure mode you're hitting in production** (weekend picks). Comment explicitly notes "the upstream bug (picking on weekends) is filed separately."
### ✅ GOOD-DC-6: `pytest.approx(1.04, abs=0.05)` and `pytest.approx(0.43, abs=0.05)` (lines 129, 131) — **uses bounded tolerance** for floats. Best practice.

### ⚠️ BUG-DC-1: `_run_evaluator` (lines 49–72) uses 6 patches simultaneously. If any signature changes, all tests break.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 6 (highest GOOD count in batch)

---

# 125. `tests/test_pick_log_dict_defensive_defaults.py` (65 lines)

**Covers:** `main.py` — **100% SOURCE-GREP via regex extraction**

### ✅ GOOD-DEF-1: Header docstring (lines 1–11) — explains the SEMANTIC distinction: fields with semantic-default get `or default`, fields without (entry, brain_*) stay `dict.get()`. **Most nuanced design rationale in batch.**
### ✅ GOOD-DEF-2: `_block()` helper (lines 18–22) uses regex to extract the `picks_for_log.append({...})` block — limits the scope of the source-grep. Smarter than full-file substring.

### 🚨 BUG-DEF-1: 8 tests, all source-grep. Each asserts an EXACT 30-character substring like `'p.get("trade_type") or "swing"'` (line 26). **8 brittle exact-string contracts.**
- Black/isort/manual-refactor would break these immediately.
- The intent is good (catching the gotcha class) but the mechanism is the wrong layer.
- **Right fix:** Test `picks_for_log` OUTPUT for a fabricated input where every field is None, assert all defaults applied. Behavior, not source.
- **Severity:** 🚨

### 🚨 BUG-DEF-2: `test_no_data_fields_left_alone` (lines 55–64) source-greps for `'p["plan"].get("entry")'` etc. Same issue.
- **Severity:** 🚨

**Per-file:** 🚨 2 · ⚠️ 0 · 🟡 0 · ✅ 2

---

# 126. `tests/test_pick_logger_schema_contract.py` (97 lines)

**Covers:** `src/pick_logger.py::FIELDS, log_picks, LOG_PATH`, `data/picks_log.csv` (live header)

### ✅ GOOD-PLS-1: Header docstring (lines 1–16) — **explicitly documents Bug #15** (FIELDS missing live CSV columns → silent data loss). Concrete and actionable.
### ✅ GOOD-PLS-2: `test_pick_logger_fields_preserve_existing_csv_header_columns` (lines 40–50) — **reads PRODUCTION CSV header** and asserts no missing columns. **Best contract test in batch — actually tests the live invariant.**
### ✅ GOOD-PLS-3: 2 separate contract tests for SPY-alpha + sector-alpha field sets (lines 25–37, 53–62). Domain-grouped contracts.
### ✅ GOOD-PLS-4: `test_pick_logger_persists_watch_only_news_action_fields` (lines 65–96) — round-trip test (write → read) verifying `watch_only`, `watch_only_reason`, `news_action_window` survive. **Critical for monitoring-mode auditability.**

### ⚠️ BUG-PLS-1: Test imports `from src.pick_logger import FIELDS` (line 20) at module scope BUT also `import src.pick_logger as pl` inside test body (line 67). Inconsistent.
- **Severity:** 🟡

### ⚠️ BUG-PLS-2: Reads PRODUCTION `data/picks_log.csv` (line 23) — couples the test to live state. If you delete the file the test breaks.
- **Severity:** 🟡 Test should be skip-on-missing OR use a versioned fixture.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 4

---

# 127. `tests/test_pick_sanity.py` (97 lines)

**Covers:** `scripts/send_layman_daily.py::_is_pick_sane`, `src/layman_translator.py::pick_to_layman, _company_suffix`

### ✅ GOOD-PS-1: 14 tests cover 8 sanity-gate cases (zero-tp, zero-entry, tp-below-entry, sl-above-entry, low-rr, good-pick, 3 field-name aliases) + 6 company-suffix cases.
### ✅ GOOD-PS-2: `test_field_name_take_profit_works`, `_tp_works`, `_target_price_works` (lines 46–62) — locks the **3 accepted alias contract**. Critical for backward compatibility with various pick-source scripts.
### ✅ GOOD-PS-3: Header docstring (line 1) — "MUST pass forever or no pick ships to user". Clear stakes.
### ✅ GOOD-PS-4: `test_company_suffix_hides_when_equals_ticker` (lines 71–73) — locks the data-fallback fix (don't display `(A)` for ticker `A`). Real production polish.

### ⚠️ BUG-PSAN-1: Tests private `_is_pick_sane` (line 6) and `_company_suffix` (line 68). Same anti-pattern.
- **Severity:** 🟡

### ⚠️ BUG-PSAN-2: `assert "Inc." not in _company_suffix(...)` (line 87), `"Corp." not in ...` (line 88) — substring-NOT checks. If "Inc." appears in unexpected context, false-pass.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 4

---

# 128. `tests/test_picks_log_column_contract.py` (134 lines)

**Covers:** `src/**/*.py` and `scripts/**/*.py` (via AST walk) vs. `data/picks_log.csv` header

### ✅ GOOD-CON-1: **AST-based static analysis** (lines 42–89) — finds `for r in csv.DictReader(...)` loops, then traces all `r.get('column_name')` calls within their scope. **By far the most sophisticated test mechanism in the entire repo.**
### ✅ GOOD-CON-2: `_find_csv_row_vars` precisely scopes to DictReader iteration (lines 42–66). **Avoids false positives on JSON `.get()` calls** — the docstring explicitly mentions this design choice.
### ✅ GOOD-CON-3: `SYNTHETIC_FIELDS` allowlist (lines 24–32) for legitimate aliases (pnl, status, buy_price, etc.) — handles real-world flex.
### ✅ GOOD-CON-4: Parameterized over ALL `*.py` files (line 108) — **catches the bug class repo-wide** automatically. Bug #4 (`status` instead of `evaluation_status`) caught for any file added in future.
### ✅ GOOD-CON-5: Header docstring (lines 1–12) names 2 specific bugs caught (`send_layman_evening` reading `'status'`, `layman_translator` reading `'pnl_dollar'`). Concrete.

### ⚠️ BUG-CCC-1: `pytest.skip` on missing CSV (line 37). If `data/picks_log.csv` is missing in CI, this test silently passes. Should be hard-fail.
- **Severity:** ⚠️ Silent-pass on missing data is worse than fail.

### ⚠️ BUG-CCC-2: AST detection only catches `for r in csv.DictReader(...)`. If someone uses `rows = list(csv.DictReader(...))` then `for r in rows:`, the test misses it.
- **Severity:** 🟡 Coverage gap on a common Python idiom.

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 1 · ✅ 5 (most sophisticated test in repo)

---

# 129. `tests/test_picks_log_company_names.py` (18 lines)

**Covers:** `data/picks_log.csv` (Bug #6: ticker stored as company name)

### ✅ GOOD-CN-1: 1 test, 17 lines — minimal, focused. Reads PRODUCTION CSV, checks no `ticker == company` rows. **Lock-in test for cleaned data.**

### 🚨 BUG-CN-1: Tests run against PRODUCTION `data/picks_log.csv`. If a single bad row sneaks in, **the failure blocks ALL CI runs**. No skip on missing file.
- This is a **data-integrity test masquerading as a unit test**. Should be in a separate "data-integrity" CI job, not in the unit suite.
- **Severity:** 🚨 Production-data-coupled test in unit suite.

### ⚠️ BUG-CN-2: No fixture/synthetic test for the underlying `is_company_equal_to_ticker` logic. If logic changes, only production data is checked.
- **Severity:** 🟡

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 1 · ✅ 1

---

# 130. `tests/test_picks_log_spy_alpha_fill_rate.py` (53 lines)

**Covers:** `data/picks_log.csv` (Bug #9: SPY-alpha fill-rate)

### ✅ GOOD-SA-1: 2 tests with explicit `CLOSED_STATUSES` and `SPY_ALPHA_FIELDS` sets (lines 6–7).
### ✅ GOOD-SA-2: `_has_value` helper (lines 10–15) — defensive against `"None"`, `"nan"`, `"null"` strings (legacy data quirks). Realistic.
### ✅ GOOD-SA-3: `test_post_floor_closed_tracked_picks_have_spy_alpha_fields` (lines 36–52) — uses `pick_date >= "2026-05-02"` floor to allow legacy data to remain unfilled while enforcing the contract going forward. **Best historical-data-handling pattern in batch.**

### 🚨 BUG-SAFR-1: Same as CN-1 — runs against PRODUCTION CSV. Single bad row blocks CI.
- **Severity:** 🚨

### ⚠️ BUG-SAFR-2: `pick_date >= "2026-05-02"` (line 42) — **string-compares ISO dates**. Works because of ISO ordering, but fragile if date format changes.
- **Severity:** 🟡

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 1 · ✅ 3

---

# 131. `tests/test_pillar1_footer.py` (38 lines)

**Covers:** `src/weekly_review.py` (build_report, format_telegram), `src/signal_journal.py`, `src/auto_pause.py`

### ✅ GOOD-PF1-1: 2 tests cover happy-path render + RuntimeError-resilience.
### ✅ GOOD-PF1-2: `test_weekly_safe_when_pillar1_modules_break` (lines 28–37) — verifies "if auto_pause raises, weekly still ships." **Critical resilience pattern for downstream safety.**

### ⚠️ BUG-PF1-1: `assert "Probability engine (Pillar 1)" in text` (line 24) — locks an EXACT user-facing label. Format-fragile. If you re-name to "Probability Engine (Pillar 1)" capitalization changes break.
- **Severity:** 🟡

### ⚠️ BUG-PF1-2: `assert "Hypothesis journal" in text` (line 25) — same.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 2

---

# 132. `tests/test_pillar4_footer.py` (27 lines)

**Covers:** `src/weekly_review.py`, `src/learning_journal.py`, `src/weight_applier.py`

### ✅ GOOD-PF4-1: 2 tests with same pattern as PF1 — happy + resilience.
### ✅ GOOD-PF4-2: Resilience test mirrors PF1 — when `wa.history_summary` raises, weekly still produces a report.

### ⚠️ BUG-PF4-1: `assert "Brain learned this week" in text` (line 16) — exact-label substring. Same fragility as PF1-1.
- **Severity:** 🟡

### ⚠️ BUG-PF4-2: Trivially short test file. 27 lines for an entire pillar. Coverage gap.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 2

---

# 133. `tests/test_pillar5_footer.py` (33 lines)

**Covers:** `src/weekly_review.py`, `src/signal_journal.py`, `src/self_awareness.py`

### ✅ GOOD-PF5-1: 2 tests, same pattern as PF1/PF4.
### ✅ GOOD-PF5-2: `test_weekly_renders_pillar5_block` (lines 9–23) seeds 5 synthetic outcomes with realistic signal-journal entries.

### ⚠️ BUG-PF5-1: `today = datetime.now().date().isoformat()` (line 12) — **time-dependent test**. Could flake at midnight. Same as ASL-2.
- **Severity:** 🟡

### ⚠️ BUG-PF5-2: `assert "Self-awareness (Pillar 5)" in text` (line 22) and `"30d edge" in text` (line 23) — exact-label substrings.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 2

---

# 134. `tests/test_pillar6_footer.py` (45 lines)

**Covers:** `src/weekly_review.py`, `src/wow_trend.py`

### ✅ GOOD-PF6-1: Resilience test pattern continues from PF1/4/5.

### 🚨 BUG-PF6-1: `test_weekly_renders_pillar6_blocks` (lines 8–35) — **only assertion is `"Recommended action" in text` (line 35)**. The test sets up a 30-line CSV fixture but **never verifies any pillar-6-specific content**. Comment line 34 even says "Just check Pillar 6 footers attempted to render (or weekly stable)" — **same no-op pattern as PHS-1 from previous batch.**
- The test name says "renders pillar6 blocks" but the assertion proves nothing about pillar 6 content.
- **Severity:** 🚨 No-op test masquerading as content verification.

### ⚠️ BUG-PF6-2: `test_weekly_safe_when_pillar6_breaks` (lines 38–44) only checks "Recommended action" in text. Same generic assertion.
- **Severity:** 🟡

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 1 · ✅ 1

---

# 135. `tests/test_portfolio_risk_gate.py` (123 lines)

**Covers:** `src/portfolio_risk_gate.py` (apply_portfolio_risk_gate, build_portfolio_risk_config, evaluate_candidate_portfolio_risk)

### ✅ GOOD-PRG-1: 6 tests cover config-defaults, allow-valid, block-too-much-risk, max-positions cap, sector-AND-tag caps, allow-different-sectors-up-to-max.
### ✅ GOOD-PRG-2: `cfg()` and `candidate()` factories (lines 8–33) — clean parametric builders.
### ✅ GOOD-PRG-3: `test_apply_portfolio_gate_enforces_sector_and_tag_caps` (lines 91–105) — tests the SUBTLE interaction (single AAPL pick fills both sector AND tag cap, blocking MSFT). Multi-axis exposure logic.
### ✅ GOOD-PRG-4: All blocked rows assert `rejection_stage == "portfolio_risk"` (line 103) — locks the rejection-taxonomy contract for downstream classification.
### ✅ GOOD-PRG-5: `assert detail["risk_profile"]["risk_dollars"] == 50.0` and `risk_pct == 0.5` (lines 58–59) — verifies derived risk math from config.

### ⚠️ BUG-PRG-1: `assert "exceeds limit" in reason` (line 73), `"sector exposure cap" in reason or "tag exposure cap" in reason` (line 104) — substring on user-facing reason text.
- **Severity:** 🟡

### ⚠️ BUG-PRG-2: 6 tests — no test for `existing_positions=[]` AND `max_positions=0` edge case (zero-allocation mode).
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 5

---

## 🎯 BATCH 114 grand totals

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 7 (DNC-1, DNC-2, DEF-1, DEF-2, CN-1, SAFR-1, PF6-1) |
| ⚠️ Data/safety risk | 2 |
| 🟡 Code smell | 21 |
| ✅ Good code | 51 |
| **Total findings** | **81 across 15 files / ~1,375 lines** |

### 🔥 ARCHITECTURE-RELEVANT FINDINGS THIS BATCH

1. **DNC-1/DNC-2 + DEF-1/DEF-2 — 4 source-grep tests on main.py for EXACT `or "default"` idioms.** This is a **new sub-pattern** of source-grep: tests that lock specific Python idioms via character-perfect substring match. **Total source-grep contracts on `main.py` discovered so far: 14+.** Refactoring `main.py` will detonate a small minefield. **Strongest signal yet that `main.py` needs to be broken into pure-function modules** so behavior can be tested directly.

2. **DC-3 (frozen-time pattern) — `_FrozenDT` subclass approach.** This is the **best frozen-time pattern in the entire repo**. Subclasses `datetime` so `strptime` and arithmetic still work. **Use this as the template** for fixing the ~12 time-dependent tests across the suite (instead of `datetime.now()`).

3. **CN-1 + SAFR-1 — Production-data-coupled tests in unit suite.** `tests/test_picks_log_company_names.py` and `tests/test_picks_log_spy_alpha_fill_rate.py` read live `data/picks_log.csv`. **One bad production row blocks ALL CI.** These belong in a separate "data integrity" CI job, NOT mixed with unit tests. **Direct relevance to your "premarket failures" — if production data has a bad row, your test suite stops running, hiding genuine code regressions.**

4. **CCC (test_picks_log_column_contract.py) — best test mechanism in repo.** AST walk that finds DictReader loops and validates `.get()` calls against the live CSV header. **This is the right way to enforce a contract** instead of source-grep. Use this as the template for replacing the 14+ source-grep tests on main.py.

5. **PF6-1 — second instance of no-op test.** `test_weekly_renders_pillar6_blocks` only asserts a generic phrase that appears in EVERY weekly report. **Together with PHS-1 from batch 113, this confirms a repo-wide pattern.** Search regex: `assert "Recommended action" in text` for more.

### 🆕 REPO-WIDE PATTERN CRYSTALLIZING

**The "production data coupling" pattern.** Several tests read `data/picks_log.csv` directly (CN-1, SAFR-1, PLS-2, CCC). When live data is bad, CI breaks. When live data is missing, tests silently skip. This is the wrong architecture for unit tests. **Consider:**
- Move data-integrity tests to a separate `tests/integrity/` directory with its own CI job
- Add versioned CSV fixtures under `tests/fixtures/picks_log_*.csv`
- Make data-integrity job NON-blocking for code PRs

### Production code coverage from this batch

- `src/trailing_stop.py`, `src/pick_evaluator.py` (force-close + unreachable_entry), `src/pick_logger.py` (FIELDS contract)
- `src/portfolio_risk_gate.py` (full coverage)
- `src/layman_translator.py::pick_to_layman, _company_suffix`
- `src/weekly_review.py`, `src/signal_journal.py`, `src/learning_journal.py`, `src/wow_trend.py`, `src/self_awareness.py`, `src/auto_pause.py`, `src/weight_applier.py`
- `scripts/send_layman_daily.py::_is_pick_sane`
- `main.py` (4× source-grep on `or default` idioms)
- `data/picks_log.csv` (4× direct production-data tests)

### Next batch (115) — files 136–150 alphabetically (CONFIRMED FROM DIRECTORY LISTING):
`test_position_monitor.py`, `test_premarket_decision_contract.py`, `test_premarket_readiness_gate.py`, `test_premarket_sanity_gate.py`, `test_premarket_watch_only.py`, `test_probability_engine.py`, `test_probability_engine_finding5.py`, `test_provider_failure_taxonomy.py`, `test_quarterly_report.py`, `test_regime_aware_sizing.py`, `test_regime_classification.py`, `test_regime_finding4.py`, `test_risk_metrics.py`, `test_rules_violated.py`, `test_scoring_safety.py`
