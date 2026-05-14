# Audit Batch 116 — tests/ files 150–164 (alphabetical) — TRUE line-by-line

**Pinned commit:** `11bc136f`
**Files audited:** 164 of 178 (cumulative)
**Total lines audited in this batch:** ~1,140
**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

# 150. `tests/test_scripts_import.py` (46 lines)

**Covers:** ALL `scripts/*.py` files (parametric smoke import)

### ✅ GOOD-SI-1: Header docstring (lines 1–6) — names a real bug it would have caught: "2026-05-04: scripts/evaluate_picks.py importing nonexistent format_paused_summary". **Concrete saved-failure.**
### ✅ GOOD-SI-2: Parametric over ALL `scripts/*.py` (lines 14–22) — auto-extends to new scripts. **Best meta-test pattern in repo.**
### ✅ GOOD-SI-3: Uses `spec_from_file_location` + `module_from_spec` + `exec_module` (lines 33–40) — imports without triggering `if __name__ == "__main__"` blocks. **Sophisticated import isolation.**
### ✅ GOOD-SI-4: Catches `(ImportError, AttributeError, NameError)` (line 41) AND tolerates `SystemExit` (lines 43–45). Real-world-aware.
### ✅ GOOD-SI-5: Skips `_` prefix files (line 19) — respects Python convention for private modules.

### ⚠️ BUG-SI-1: A script that crashes with `KeyError` or any other exception during import would still pass. Only 3 exception types caught.
- **Severity:** 🟡 Could be `except Exception as e` since any import-time exception means broken script.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 5 (best meta-test pattern in repo)

---

# 151. `tests/test_sector_alpha_backfill.py` (74 lines)

**Covers:** `src/pick_evaluator.py` (_add_sector_alpha, _ensure_sector_benchmark_anchor, _etf_close_on)

### ✅ GOOD-SAB-1: 3 tests cover fills-from-tag, preserves-spy-anchor, falls-back-to-spy-when-etf-missing. Multi-axis defensive coverage.
### ✅ GOOD-SAB-2: `test_sector_anchor_falls_back_to_spy_when_resolved_etf_missing` (lines 53–73) — locks the **graceful-degradation contract**: when SOXX data unavailable, fall back to SPY. Critical for sector-alpha backfill robustness.
### ✅ GOOD-SAB-3: `pytest.approx(-0.79, abs=0.01)` (line 28), `(0.15, abs=0.01)` (line 29) — bounded tolerance for derived percentages. Best practice.

### ⚠️ BUG-SAB-1: Tests private `_add_sector_alpha`, `_ensure_sector_benchmark_anchor`, `_etf_close_on` (lines 13, 23, 68). Same anti-pattern.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 3

---

# 152. `tests/test_sector_benchmark.py` (41 lines)

**Covers:** `src/sector_benchmark.py::resolve_sector_etf`

### ✅ GOOD-SB-1: 8 tests cover SEMI→SOXX, compound tag, Tech→XLK, Healthcare→XLV, Financial→XLF, unknown→SPY fallback, no-args→SPY, tag-overrides-sector. **Complete API matrix.**
### ✅ GOOD-SB-2: `test_tag_overrides_sector` (lines 38–40) — locks the **specificity-priority contract** (BIOTECH tag wins over Healthcare sector → XBI not XLV).
### ✅ GOOD-SB-3: `test_no_inputs_falls_back_to_spy` (lines 34–35) — defensive against zero-arg call.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 0 · ✅ 3 (zero-issue file)

---

# 153. `tests/test_sector_benchmark_subsectors.py` (53 lines)

**Covers:** `src/sector_benchmark.py::resolve_sector_etf` (Bug #8a: yfinance subsector strings)

### ✅ GOOD-SBS-1: Header docstring (lines 1–4) — explicitly names the production failure: "yfinance returns 'Semiconductors', 'Biotechnology' that weren't in SECTOR_TO_ETF, falling through to SPY and killing sector-relative alpha for ~70% of picks." **Quantified-impact regression doc.**
### ✅ GOOD-SBS-2: 10-case parametric (lines 9–20) covering exact yfinance subsector strings: Semiconductors, Biotechnology, Life Sciences Tools & Services, Software variants, Internet, Drug Manufacturers, Medical Devices.
### ✅ GOOD-SBS-3: `test_truly_unknown_sector_still_falls_back_to_SPY` (lines 31–34) — REGRESSION GUARD that the fix didn't break the legitimate fallback path. Critical defensive guard.
### ✅ GOOD-SBS-4: `test_tag_still_wins_over_sector_after_subsector_additions` (lines 43–46) — REGRESSION GUARD that tag-priority logic still works after adding subsector mappings.
### ✅ GOOD-SBS-5: Failure assertion message (lines 25–28) explains WHY the test matters: "SPY fallback corrupts sector-alpha learning." **Best assertion message in batch.**

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 0 · ✅ 5 (zero-issue file, exemplary regression-doc)

---

# 154. `tests/test_sector_benchmark_wiring.py` (94 lines)

**Covers:** `main.py::_sector_benchmark_for_pick, _yf_ticker_for_sector_benchmark`

### ✅ GOOD-SBW-1: 3 tests cover happy-path-resolves-XLK, falls-back-to-SPY-when-missing, keeps-resolved-ETF-when-fetch-succeeds.
### ✅ GOOD-SBW-2: `FakeHist` and `FakeClose` classes (lines 16–41) — **explicit duck-typing** of yfinance API. Avoids actual network calls.
### ✅ GOOD-SBW-3: `test_sector_benchmark_for_pick_keeps_resolved_etf_when_close_fetch_succeeds` (lines 78–93) uses `raise AssertionError("SPY should not be fetched when sector ETF succeeds")` (line 84) — **negative assertion via mock side-effect**. **Best mock-pattern in batch.**
### ✅ GOOD-SBW-4: `ticker.assert_called_once_with("XLK")` (line 57) — explicit call-count + arg verification.

### ⚠️ BUG-SBW-1: Tests private `_sector_benchmark_for_pick`, `_yf_ticker_for_sector_benchmark` (lines 53, 72, 89, 90). Same anti-pattern, but justified for main.py refactor coverage.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 4

---

# 155. `tests/test_sector_breakdown.py` (101 lines)

**Covers:** `src/sector_breakdown.py` (sector_breakdown, format_sector_panel, _verdict, _enrich_with_sector_etf)

### ✅ GOOD-SBD-1: 12 tests across 3 `Test*` classes covering verdict-taxonomy (6), enrich-helpers (3), main breakdown logic (4), formatting (3). **Best class-grouping in batch.**
### ✅ GOOD-SBD-2: `TestVerdict` class (lines 19–31) — covers all 6 verdict states (strong, ok, mixed, weak, bleeding, none) with one assertion each. Clean.
### ✅ GOOD-SBD-3: `test_worst_first_ordering` (lines 73–81) — asserts `rs == sorted(rs)` — **derived correctness assertion** (sort order), not magic-number positions.
### ✅ GOOD-SBD-4: `test_does_not_overwrite` (lines 40–43) — locks the **idempotent-enrichment contract** (existing values preserved).

### ⚠️ BUG-SBD-1: Tests private `_verdict`, `_enrich_with_sector_etf` (line 4). Same anti-pattern.
- **Severity:** 🟡

### ⚠️ BUG-SBD-2: Verdict tests use emoji substring matching (`"🌟" in _verdict(...)`, etc.). If emoji renders as Unicode escape vs literal, would mismatch.
- **Severity:** 🟡 Locks visual format.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 4

---

# 156. `tests/test_sector_pnl.py` (58 lines)

**Covers:** `src/sector_pnl.py` (per_sector_pnl, format_table)

### ✅ GOOD-SP-1: 6 tests cover empty, groups-correctly, falls-back-to-tag, verdicts (3 buckets), format-headers, skips-no-r.
### ✅ GOOD-SP-2: `test_per_sector_pnl_skips_no_r` (lines 51–57) — defensive against missing `r_multiple` field. Real-world data hygiene.
### ✅ GOOD-SP-3: `pytest.approx(1.0)` (line 22) — for `total_r` calc. Best float-comparison practice.

### ⚠️ BUG-SP-1: `assert "PROFITABLE" in by["WIN"]` (line 38), `"LOSING" in by["LOSS"]` (line 39), `"FLAT" in by["FLAT"]` (line 40) — substring on user-facing labels. Format-fragile.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 3

---

# 157. `tests/test_sector_wisdom.py` (116 lines)

**Covers:** `src/wisdom_base.py::add_lesson, lessons_for_ticker, LESSONS, PATTERNS, KILL`, `src/wisdom_hint.py::wisdom_hint`

### ✅ GOOD-SW-1: 11 tests across 2 `Test*` classes covering sector-match, case-insensitivity, sector-without-ticker, no-sector-no-match-for-sector-lesson, ticker+sector-mix, empty-inputs (lessons), surfaces-on-member, no-hint-when-not-passed, multi-ticker, ticker-precedence, no-crash-on-None (hint).
### ✅ GOOD-SW-2: `isolated` fixture (lines 7–12) — patches LESSONS/PATTERNS/KILL paths. Hermetic.
### ✅ GOOD-SW-3: `_wh()` helper (lines 15–18) does `importlib.reload(m)` to **force re-evaluation** of module-level state per test. Clean isolation.
### ✅ GOOD-SW-4: `test_ticker_hint_takes_precedence` (lines 99–110) — locks the **specificity-priority** contract (NVDA-tagged 0.95 conf > sector-tagged 0.75 conf).
### ✅ GOOD-SW-5: `test_sector_hint_works_across_multiple_tickers` (lines 91–97) — verifies the hint surfaces on XOM/CVX/OXY uniformly. Multi-ticker integration.
### ✅ GOOD-SW-6: `test_sector_match_case_insensitive` (lines 33–37) — defensive against "tech" vs "Tech" vs "TECH" inputs.

### ⚠️ BUG-SW-1: `assert "🧠" in out` (line 80) — emoji substring. Same as SBD-2.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 6 (highest GOOD count in batch)

---

# 158. `tests/test_self_awareness.py` (119 lines)

**Covers:** `src/self_awareness.py` (wilson_ci, mean_r_ci, rolling_window, format_footer, monthly_calibration), `src/signal_journal.py`

### ✅ GOOD-SA-1: 14 tests covering wilson-ci (3 edge cases), mean-r-ci (3), rolling-window (5 incl. INCONCLUSIVE/EDGE_CONFIRMED/EDGE_BROKEN verdicts), format-footer (2), monthly-calibration (1).
### ✅ GOOD-SA-2: `test_wilson_ci_full_wins` (lines 18–21) — verifies Wilson is **conservative** (`lo > 0.7`, NOT 1.0 even at 10/10). **Tests the statistical property, not magic number.**
### ✅ GOOD-SA-3: `test_rolling_window_verdict_inconclusive_low_n` (lines 77–80) — locks the **n<20 → always INCONCLUSIVE** contract. Statistical safety.
### ✅ GOOD-SA-4: `test_rolling_window_verdict_edge_broken` (lines 90–96) — tests catastrophic case (WR 7%, edge clearly gone). Critical for the "did our edge die" detector.
### ✅ GOOD-SA-5: `_rec` and `_seed` helpers (lines 49–58) — clean parametric data builders.

### ⚠️ BUG-SA-1: `_rec` uses `datetime.now() - timedelta(days=days_ago)` (line 50) — **time-dependent test**. Could flake at midnight.
- **Severity:** 🟡

### ⚠️ BUG-SA-2: `assert "30d edge: INCONCLUSIVE" in out` (line 108), `"WR 39%" in out` (line 109), `"95% CI" in out` (line 110) — exact-label substrings. Format-fragile.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 5

---

# 159. `tests/test_send_late_daily_ideas_telegram.py` (76 lines)

**Covers:** `scripts/send_late_daily_ideas_telegram.py` (main, late_ideas_message_path, late_ideas_sent_path, today_et)

### ✅ GOOD-SLD-1: 2 tests cover dedup-after-success and force-resend.
### ✅ GOOD-SLD-2: `test_late_ideas_telegram_dedupes_after_success` (lines 5–41) verifies BOTH first call sends AND second call is no-op. Round-trip dedup.
### ✅ GOOD-SLD-3: `payload["mode"] == "monitoring_only"` and `paper_trading_enabled is False` and `live_trading_enabled is False` (lines 36–38) — locks the **monitoring-only mode contract** in the persisted ledger. **Direct relevance to safety mode.**
### ✅ GOOD-SLD-4: `FakeResp` and `fake_urlopen` (lines 19–25) — no actual network calls.
### ✅ GOOD-SLD-5: `monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")` (line 13) — proper env-var isolation.

### ⚠️ BUG-SLD-1: 2 tests are 65% identical setup boilerplate. Could share a fixture.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 5

---

# 160. `tests/test_send_layman_daily_reliability.py` (150 lines)

**Covers:** `scripts/send_layman_daily.py` (_send, main, build_message, _today_picks, mark_sent, validate_official_user_output_state, should_send)

### ✅ GOOD-SLDR-1: 8 tests cover dry-run-without-creds, returns-true-on-partial-success, returns-false-when-all-fail, doesn't-mark-sent-on-fail, marks-sent-on-success, dedup-skip-no-send, watch-only-no-buy-price (premarket variant), watch-only-no-buy-price (generic). **Complete reliability matrix.**
### ✅ GOOD-SLDR-2: `test_main_does_not_mark_sent_when_delivery_fails` (lines 59–73) — locks the **CRITICAL safety invariant**: never mark a message as sent if delivery failed. Prevents silent message loss.
### ✅ GOOD-SLDR-3: `test_send_returns_true_when_at_least_one_chat_succeeds` (lines 18–42) — tests the **graceful partial-failure** contract.
### ✅ GOOD-SLDR-4: `test_build_message_marks_watch_only_without_actionable_buy` (lines 111–130) — verifies WATCH ONLY messages **don't show "Buy at:" line**. **Direct guard against the failure mode you've been hitting.**
### ✅ GOOD-SLDR-5: `mark_sent.assert_not_called()` (lines 73, 109) — explicit negative-assertion via mock. Strong safety verification.

### ⚠️ BUG-SLDR-1: `assert "No buy price is actionable" in msg` (line 128), `"Require a fresh live quote" in msg` (line 129) — exact-string substrings on user-facing copy. Format-fragile.
- **Severity:** 🟡

### ⚠️ BUG-SLDR-2: 6 tests duplicate the `monkeypatch.setattr(sld, ...)` setup pattern. Could share a fixture.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 5

---

# 161. `tests/test_signal_journal_quality.py` (96 lines)

**Covers:** `data/signal_journal.jsonl` (production-data-coupled quality gate)

### ✅ GOOD-SJQ-1: Header docstring (lines 1–8) — explains the historical-data carve-out via `QUALITY_GATE_START = "2026-05-05"`. Allows legacy unknowns to remain while enforcing post-fix quality.
### ✅ GOOD-SJQ-2: `test_buckets_have_valid_values` (lines 71–95) — defines a **vocabulary of allowed values per field**. **Best vocabulary-validation pattern in batch.** Catches typos like "buull" instead of "bull".
### ✅ GOOD-SJQ-3: `< 10` percentage threshold (lines 41, 53, 65) — allows for legitimate transient unknowns (cache miss etc.) while flagging systematic regression.
### ✅ GOOD-SJQ-4: All 3 quality tests `return` early if no post-fix entries (lines 37, 49, 61). **Avoids false-failure when journal is empty in fresh CI.**

### 🚨 BUG-SJQ-1: ALL 4 tests read PRODUCTION `data/signal_journal.jsonl` (line 13). Same anti-pattern as batch 114 (CN-1, SAFR-1) and 115 (QR-1). **Bad production data → blocks all CI.**
- **Severity:** 🚨

### ⚠️ BUG-SJQ-2: `_post_fix_entries` silently `continue`s on `JSONDecodeError` (line 30). Legitimate corruption hidden.
- **Severity:** 🟡

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 1 · ✅ 4

---

# 162. `tests/test_smell_enforcement_readiness.py` (66 lines)

**Covers:** `scripts/check_enforcement_readiness.py::check_smell_enforce`

### ✅ GOOD-SER-1: 4 tests cover schema-blocker-when-missing-field, counts-persisted-rows, ready-when-enough-and-low-FP, blocks-when-FP-too-high.
### ✅ GOOD-SER-2: Header docstring (lines 1–6) — explicitly names Bug #17B and the upstream Bug #17A dependency. **Best dependency-context doc in batch.**
### ✅ GOOD-SER-3: `test_smell_readiness_blocks_when_false_positive_rate_too_high` (lines 55–65) — locks the **strict <20% FP threshold** for enforcement promotion. Comment "Threshold is strict: must be < 20%" makes the boundary explicit.
### ✅ GOOD-SER-4: `closed_row` factory (lines 11–19) auto-fills `smell_severities`/`smell_messages` based on `smell_codes` truthiness. Compact.

### ⚠️ BUG-SER-1: `assert any("n=3 < 30" in b for b in result["blockers"])` (line 40) — exact-format substring on blocker text. Format-fragile.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 4

---

# 163. `tests/test_smell_faculty.py` (126 lines)

**Covers:** `src/smell_faculty.py` (sniff, has_blocking_smell, format_for_telegram, smell_earnings_imminent, smell_extreme_rsi, smell_volume_spike, smell_gap_up, smell_low_liquidity, smell_tight_stop)

### ✅ GOOD-SF-1: 16 tests covering ALL 6 smell types + sniff-registry + has-blocking-smell + format + broken-smell-resilience. **Most thorough faculty coverage in batch.**
### ✅ GOOD-SF-2: `test_sniff_returns_sorted_by_severity` (lines 81–88) — locks the **CRITICAL-before-HIGH ordering contract**. UI consistency.
### ✅ GOOD-SF-3: `test_clean_pick_no_smells` (lines 104–107) — verifies **no false positives** on a known-clean pick. Critical for trust.
### ✅ GOOD-SF-4: `test_broken_smell_doesnt_crash_sniff` (lines 121–125) — defensive against `entry: "garbage"`. **Real-world data hygiene.**
### ✅ GOOD-SF-5: Per-smell fire/no-fire pairs (lines 10–77) — symmetric coverage.
### ✅ GOOD-SF-6: `test_has_blocking_smell_returns_none_for_clean_pick` (lines 98–101) — explicit negative assertion.

### ⚠️ BUG-SF-1: `assert "Earnings in 1 day" in out` (line 118), `"Smell-test warnings" in out` (line 117) — exact-label substrings.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 6

---

# 164. `tests/test_smell_faculty_finding2.py` (105 lines)

**Covers:** `src/smell_faculty.py` (Finding #2: smells must read pick['scores'][...])

### ✅ GOOD-SFF2-1: Header docstring (lines 1–7) — **EXEMPLARY**: "All 4 sniff functions silently returned None, so 4 of 7 smells effectively didn't exist. The 'proactive smell' architecture claim was partial fiction." **Most candid bug-doc in repo.**
### ✅ GOOD-SFF2-2: 9 tests cover 4 smells × `pick['scores'][...]` shape + alias (`avg_daily_volume`) + 2 backward-compat checks + 1 integration `sniff()` test.
### ✅ GOOD-SFF2-3: `test_extreme_rsi_still_works_flat_dict` and `test_extreme_rsi_still_works_from_sig` (lines 74–81) — REGRESSION GUARDS that the fix didn't break the existing dict shapes. Critical defensive guards.
### ✅ GOOD-SFF2-4: `test_low_liquidity_fires_from_avg_daily_volume_alias` (lines 64–69) — handles the **yfinance field-name alias** (`avg_daily_volume`). Real-world realism.
### ✅ GOOD-SFF2-5: `test_sniff_finds_multiple_smells_on_real_pick_shape` (lines 86–104) — INTEGRATION test using realistic nested-pick shape with 5 expected smells. Catches systemic blindness.
### ✅ GOOD-SFF2-6: Failure assertion (line 104) prints what was missing AND what was found. **Best debug-friendly assertion in batch.**

### ⚠️ BUG-SFF2-1: Could be merged into `test_smell_faculty.py`. Separate file pattern persists.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 6 (most candid bug-doc in repo)

---

## 🎯 BATCH 116 grand totals

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 1 (SJQ-1: 4 tests on production signal_journal) |
| ⚠️ Data/safety risk | 0 |
| 🟡 Code smell | 18 |
| ✅ Good code | 68 |
| **Total findings** | **87 across 15 files / ~1,140 lines** |

### 🔥 ARCHITECTURE-RELEVANT FINDINGS THIS BATCH

1. **SI (test_scripts_import.py) — best meta-test pattern in entire repo.** Parametric over `scripts/*.py`, uses `spec_from_file_location` for clean isolation, catches multiple exception types. **Use as template for adding similar smoke-import test for `src/*.py`** to catch the next ImportError before it ships.

2. **SLDR-2 (test_send_layman_daily_reliability.py) — exemplary delivery-safety test.** "Never mark sent if delivery failed" + "WATCH ONLY messages don't show Buy at:" + 8 tests for partial failure modes. **Direct guard against your premarket issues.** Use as template for testing `premarket_check.py` (PWO-1 from batch 115).

3. **SBS (sector_benchmark_subsectors) + SFF2 (smell_faculty_finding2) — both are EXEMPLARY regression-doc files.** SBS says "killed sector-relative alpha for ~70% of picks." SFF2 says "4 of 7 smells effectively didn't exist." **This level of candor in test docstrings is what makes the repo recoverable.** **More tests should be written this way.**

4. **SJQ-1 — fourth instance of production-data-coupled tests.** Total now: CN-1, SAFR-1, QR-1, SJQ-1. **Same recommended fix:** move to `tests/integrity/` with separate CI job. Bad production data shouldn't block code PRs.

5. **SLDR-3 (monitoring-only ledger contract) — direct safety relevance.** Verifies `mode == "monitoring_only"`, `paper_trading_enabled is False`, `live_trading_enabled is False` are persisted in the dedup ledger. **Locks the "we are NOT trading live" invariant in persisted state.** Critical for audit trail.

### 🆕 PATTERN: Vocabulary-validation tests (SJQ-2)

`test_buckets_have_valid_values` defines a dict of allowed values per field and walks all rows. **This is a powerful pattern** for catching typos (`"buull"` instead of `"bull"`) that would otherwise silently corrupt analytics. **Apply to:** trade_type, regime, premarket_action, evaluation_status, smell severity codes.

### Production code coverage from this batch

- ALL `scripts/*.py` (smoke-import, parametric)
- `src/sector_benchmark.py` (3 test files: 8+10+3 cases)
- `src/sector_breakdown.py` (12 tests, full)
- `src/sector_pnl.py`, `src/wisdom_base.py`, `src/wisdom_hint.py`
- `src/self_awareness.py` (14 tests including Wilson CI statistical properties)
- `src/smell_faculty.py` (16+9 = 25 tests across 2 files — most-tested module in batch)
- `scripts/send_layman_daily.py` (8 reliability tests, exemplary)
- `scripts/send_late_daily_ideas_telegram.py` (2 tests)
- `scripts/check_enforcement_readiness.py`
- `main.py::_sector_benchmark_for_pick` (3 tests)
- `data/signal_journal.jsonl` (4 production-coupled tests — SJQ-1 issue)

### Next batch (117) — files 165–178 alphabetically (CONFIRMED FROM DIRECTORY LISTING):
`test_smoke_artifacts.py`, `test_stock_stats.py`, `test_strategy_aware_decision.py`, `test_strategy_planner.py`, `test_strategy_planner_anti_chase.py`, `test_telegram_dedup.py`, `test_telegram_health.py`, `test_telegram_official_alerts.py`, `test_unpause.py`, `test_validation_state_helpers.py`, `test_watchlist_news_sniffer.py`, `test_weekly_review.py`, `test_weight_applier.py`, `test_wisdom_base.py`
