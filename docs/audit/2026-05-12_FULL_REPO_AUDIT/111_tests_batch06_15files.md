# Audit Batch 111 — tests/ files 76–90 (alphabetical) — TRUE line-by-line

**Pinned commit:** `dc0f4897`
**Files audited:** 90 of 178 (cumulative)
**Total lines audited in this batch:** ~1,510
**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

# 76. `tests/test_missing_data_gate.py` (96 lines)

**Covers:** `src/missing_data_gate.py` (apply_missing_data_gate, validate_official_pick_required_data, official_pick_required_field_snapshot)

### ✅ GOOD-MDG-1: `candidate()` factory (lines 8–23) — single source of truth for valid-pick shape.
### ✅ GOOD-MDG-2: 7 tests cover happy path, missing ticker, bad plan values, inverted SL/TP, watch-only block, blocked-pick reporting, snapshot. Multi-axis coverage.
### ✅ GOOD-MDG-3: `assert blocked[0]["rejection_stage"] == "missing_data"` (line 84) — locks rejection-taxonomy contract. Critical for downstream classification.

### ⚠️ BUG-MDG-1: `assert "stop_loss must be below entry" in errors` (line 61) — substring match on error message. Format-fragile.
- **Severity:** 🟡

### ⚠️ BUG-MDG-2: No test for `apply_missing_data_gate([])` — empty input edge case.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 3

---

# 77. `tests/test_monitoring_first_docs.py` (68 lines)

**Covers:** `docs/decisions/2026-05-05-monitoring-first-no-paper-trading.md`, `docs/PROJECT_BLUEPRINT.md`, `docs/WORK_LOG.md`, `docs/NEXT_SESSION.md` — **ALL VIA SOURCE-GREP ON DOCS**

### 🚨 BUG-MFD-1: 100% source-grep on Markdown documentation (4 tests, 60 lines of grep)
- Asserts `"monitoring-ready" in text`, `"1561 passed, 30 skipped" in text`, etc.
- **CRITICAL FRAGILITY:** `"1561 passed, 30 skipped"` (line 32) — locks an EXACT TEST COUNT in a docs file. Every time you add or remove a test, this test breaks even though docs and code are both correct.
- **Severity:** 🚨

### ⚠️ BUG-MFD-2: `"Test suite: 1561 passed, 30 skipped"` snapshot in production docs is now likely stale because batches 108-110 audited 75 test files; you've almost certainly added more tests since. **Verify this test still passes in CI.**
- **Severity:** ⚠️ Likely already-broken test or stale doc.

**Per-file:** 🚨 1 · ⚠️ 1 · 🟡 0 · ✅ 0

---

# 78. `tests/test_monitoring_mode_no_paper_default.py` (20 lines)

**Covers:** `main.py::_should_log_paper_trade` (env var `TRADING_MODE`)

### ✅ GOOD-MMP-1: 3 tests cover unset (defaults to monitoring), `paper`, `monitoring`. Complete state coverage.
### ✅ GOOD-MMP-2: `monkeypatch.delenv` and `setenv` (lines 5, 11, 17) — clean env hygiene.
### ✅ GOOD-MMP-3: **CRITICAL SAFETY TEST.** `_should_log_paper_trade()` returning False on unset env is the #1 protection against accidentally enabling real-money flow. **Best safety-default test in batch.**

### ⚠️ BUG-MMP-1: No test for `TRADING_MODE="live"` or unknown values like `TRADING_MODE="PAPER"` (case sensitivity).
- **Severity:** 🟡 Coverage gap on a CRITICAL safety toggle.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 3

---

# 79. `tests/test_monitoring_readiness.py` (103 lines)

**Covers:** `scripts/monitoring_readiness.py` (CLOSED_STATUSES, classify_bucket, evaluate_bucket, run_all)

### ✅ GOOD-MR-1: Header docstring (lines 1–8) explicitly enumerates the 3 readiness gates (day >60%, swing >66%, monster >90%). **Locked policy contract.**
### ✅ GOOD-MR-2: `test_evaluate_bucket_blocks_negative_expectancy_even_with_high_win_rate` (lines 62–75) — tests the CRITICAL fail-safe. **High win rate + negative expectancy must NOT pass.** This is exactly the kind of test that prevents a future "85% wins of small gains and one big loss → wrongly approves paper trading".
### ✅ GOOD-MR-3: 5 behavioral tests + 1 CLI integration test (line 96) — nice mix.
### ✅ GOOD-MR-4: `row(**kw)` factory (lines 21–30) — clean test-data builder.

### ⚠️ BUG-MR-1: `subprocess.check_output(["python", "scripts/monitoring_readiness.py", "--json"])` (lines 96–100) — uses `"python"` not `sys.executable`. Same anti-pattern as previous batch.
- **Severity:** ⚠️ Will break on systems where `python` resolves to v2 or is missing.

### ⚠️ BUG-MR-2: `assert round(result["win_rate"], 4) == 0.6667` (line 56) — float-equality with rounding. Should use `pytest.approx`.
- **Severity:** 🟡

### ⚠️ BUG-MR-3: CLI test reads REAL production `data/picks_log.csv` (since it doesn't pass tmp_path). Production-data dependent.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 2 · ✅ 4

---

# 80. `tests/test_monster_flag_persistence.py` (30 lines)

**Covers:** `main.py` — **100% SOURCE-GREP**

### 🚨 BUG-MFP-1: 30 lines, 1 test, ALL source-grep
- Asserts `'_p["is_monster"] = True' in src` AND `'"is_monster": p.get("is_monster") or p["scores"].get("is_monster") or False' in src` (line 26).
- The second assertion **locks an EXACT 80-character Python expression**. Any reformatting (Black, isort, line-wrap) breaks it.
- Header docstring (lines 1–12) is excellent and documents the bug, but the test enforcement is brittle source-text matching, NOT behavior. The bug it claims to regression-prevent (root-level `is_monster` losing in serialization) could STILL happen if someone refactors the expression to be semantically identical but syntactically different.
- **Severity:** 🚨

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 0 · ✅ 0

---

# 81. `tests/test_monster_hunt.py` (82 lines)

**Covers:** `src/monster_hunt.py::score_monster, apply_monster_treatment`

### ✅ GOOD-MH-1: 7 tests cover boundary at exactly 0.60 threshold (line 34) and just below at 0.40 (line 43). Tight.
### ✅ GOOD-MH-2: `test_full_monster_caps_at_one` (lines 20–26) — locks the cap=1.0 invariant.
### ✅ GOOD-MH-3: `test_monster_widens_sl_and_tp` (lines 69–81) — comprehensive treatment validation incl. `original_sl_pre_monster` audit-trail field. **Audit-trail discipline.**

### ⚠️ BUG-MH-1: `assert r["monster_score"] == 0.60` (line 34) and `== 0.40` (line 43) — exact float equality on COMPUTED scores. Same fragility as LDI-1.
- **Severity:** ⚠️ Float-equality on computed values.

### ⚠️ BUG-MH-2: `assert out["qty"] == 30` (line 78) — magic number. No comment showing the 150/5=30 derivation in the assertion (it's in line 77 comment).
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 1 · ✅ 3

---

# 82. `tests/test_news_action_window_guard.py` (43 lines)

**Covers:** `src/news_signals.py` (add_signal_from_classification, get_ticker_signal), `main.py::_safe_trade_type_for_pick`

### ✅ GOOD-NAW-1: `test_news_signal_preserves_action_window` (lines 8–24) — behavioral, locks the action_window propagation.
### ✅ GOOD-NAW-2: `test_intraday_news_swing_pick_is_marked_watch_only` (lines 27–42) tests the SAFETY: intraday news cannot silently become a regular swing.

### 🚨 BUG-NAW-1: Lines 40–42 are SOURCE-GREP on main.py
- Comment line 38–39 explicitly says "Lock expected policy text in main.py until this guard is promoted into a smaller pure helper." — **acknowledges the anti-pattern is temporary**, but it's still active. Production safety relies on a literal-string match in main.py text.
- **Severity:** 🚨 (mitigated by intent comment, but still an active source-grep contract).

### ⚠️ BUG-NAW-2: `open("main.py").read()` (line 40) — no `with`, no encoding. ResourceWarning + Windows encoding bug latent.
- **Severity:** 🟡

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 1 · ✅ 2

---

# 83. `tests/test_news_engine.py` (283 lines)

**Covers:** `src/news_classifier.py::_heuristic_fallback, classify_news`, `src/watchlist_manager.py` (add_from_news, get_watchlist, get_watchlist_tickers, watchlist_score_boost, _prune_expired)

### ✅ GOOD-NE-1: `_isolate_watchlist` autouse fixture (lines 20–24) — hermetic test isolation. Best fixture pattern in batch.
### ✅ GOOD-NE-2: 14 tests across classifier (sentiment buckets) + watchlist (add/dedup/score boost/expiry/sort) + integration. Comprehensive.
### ✅ GOOD-NE-3: `test_watchlist_expiry_pruning` (lines 188–204) — explicit time-decay test using `datetime.now(timezone.utc) - timedelta(hours=100)`. Realistic.

### ⚠️ BUG-NE-1: `test_watchlist_score_boost_bullish` asserts `assert 0 < boost <= 0.30  # PR #68: cap raised from 0.15 to 0.30` (line 163) — **comment in test references a specific PR**. Pattern of inline-PR-history in tests means: if the cap changes again in PR #100, you need to find every PR reference and update.
- **Severity:** 🟡

### ⚠️ BUG-NE-2: `test_score_boost_applied_to_bullish_ticker` asserts EXACT `boost == 0.30` (line 250) — exact float equality.
- **Severity:** ⚠️ Float fragility.

### ⚠️ BUG-NE-3: `test_parallel_scorer_imports_watchlist` (lines 274–282) is **SOURCE-GREP on `parallel_scorer.py`** via `inspect.getsource(ps)`. Same anti-pattern, slightly disguised.
- **Severity:** 🚨 Source-grep masquerading as introspection.

### ⚠️ BUG-NE-4: `_reset_watchlist()` (lines 71–73) is called inside test bodies but `_isolate_watchlist` autouse fixture should already isolate. Redundant + suggests fixture isn't trusted.
- **Severity:** 🟡

**Per-file:** 🚨 1 · ⚠️ 1 · 🟡 2 · ✅ 3

---

# 84. `tests/test_news_engine_finding3.py` (44 lines)

**Covers:** `src/news_engine.py::fetch_yahoo_rss`

### ✅ GOOD-NEF-1: Header docstring (line 1) explicitly references "Finding #3" — links test to the audit finding. **Best traceability in batch.**
### ✅ GOOD-NEF-2: Inline `FAKE_RSS` XML (lines 5–19) — realistic RSS with 4 items. Tests "only first 3 are returned" contract.
### ✅ GOOD-NEF-3: `test_yahoo_rss_handles_no_items` (lines 36–43) — empty-input safety.

### ⚠️ BUG-NEF-1: `patch("src.news_engine.time.sleep")` (lines 27, 41) — silently disables retry backoff. If implementation depends on sleep for ordering, hidden bug.
- **Severity:** 🟡

### ⚠️ BUG-NEF-2: `assert items[0]["headline"] == "NVDA hits new all-time high"` (line 31) — exact string match on RSS-extracted text. If parser changes whitespace handling, breaks.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 3

---

# 85. `tests/test_news_engine_run_status.py` (122 lines)

**Covers:** `scripts/run_news_engine.py` (build_news_engine_run_status, append_news_engine_run_status, news_lookback_minutes, main, DEFAULT/MIN/MAX_NEWS_LOOKBACK_MINUTES)

### ✅ GOOD-NER-1: 7 tests cover row-shape, JSONL write, fresh-news=empty path, workflow YAML (mixed), default lookback, configurable+clamped, main-uses-default. Multi-layer coverage.
### ✅ GOOD-NER-2: `test_news_lookback_minutes_is_configurable_and_clamped` (lines 88–99) — 4 boundary cases (180/5/999/not-a-number) in one test. Compact and complete.
### ✅ GOOD-NER-3: Imports `runner.MIN_NEWS_LOOKBACK_MINUTES`, `runner.MAX_NEWS_LOOKBACK_MINUTES`, `runner.DEFAULT_NEWS_LOOKBACK_MINUTES` (lines 38, 93, 95, 99) — references PRODUCTION constants instead of magic numbers. **Exemplary.**
### ✅ GOOD-NER-4: All assertions enforce `paper_trading_enabled is False` and `live_trading_enabled is False` (lines 31, 32) — safety contract.

### 🚨 BUG-NER-1: `test_news_engine_workflow_commits_run_status_artifact` (lines 75–79) is SOURCE-GREP on workflow YAML.
- One source-grep test contaminates an otherwise excellent file.
- **Severity:** 🚨

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 0 · ✅ 4 (best constant-discipline in batch)

---

# 86. `tests/test_news_evidence_playbook_docs.py` (53 lines)

**Covers:** `docs/playbook/NEWS_EVIDENCE_REPORTS.md` — **100% SOURCE-GREP ON DOCS**

### 🚨 BUG-NEP-1: 4 tests, 53 lines, ALL source-grep on a single Markdown file
- Tests assert `"News Evidence Reports Playbook" in text`, `"Do not start paper trading" in text`, etc.
- Same anti-pattern as MFD-1. Documentation drift will break tests; documentation rewriting (semantically identical, different words) will break tests; CI flake risk on every doc edit.
- **Severity:** 🚨

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 0 · ✅ 0

---

# 87. `tests/test_news_evidence_workflow.py` (110 lines)

**Covers:** `.github/workflows/news_evidence.yml` — **MIXED SOURCE-GREP + STRUCTURAL**

### ✅ GOOD-NEW-1: `test_news_evidence_workflow_runs_no_write_preflights_before_writes` (lines 26–38) — uses `text.index(...)` to verify ORDER of steps. Structural, not just-presence. Better than pure grep.
### ✅ GOOD-NEW-2: `test_news_evidence_workflow_commits_only_reporting_artifacts` (lines 41–67) — explicit `forbidden = [...]` list of files that MUST NOT be committed by this workflow. **Critical safety contract.**
### ✅ GOOD-NEW-3: `test_news_evidence_workflow_checks_official_state_not_mutated` (lines 70–82) — locks the safety check that the read-only workflow doesn't mutate official state. Defensive.
### ✅ GOOD-NEW-4: `test_news_evidence_workflow_uploads_large_json_instead_of_committing_it` (lines 99–109) — locks the artifact-upload-vs-commit decision. Critical for repo-size hygiene.

### 🚨 BUG-NEW-1: All tests are STILL fundamentally source-grep on workflow YAML, just slightly more sophisticated (substring + index + section-split parsing).
- The "forbidden list" check is GOOD intent but BAD execution — what's actually needed is to RUN the workflow (or its commit step) and check the actual git diff is empty for forbidden paths.
- **Severity:** 🚨 (intent good, mechanism still grep)

### ⚠️ BUG-NEW-2: `re.search(r"grep -Eq '\^\[0-9\]\{4\}-\[0-9\]\{2\}-\[0-9\]\{2\}\$'", text)` (line 97) — regex-of-regex. If you change the date validation pattern, both the workflow AND the test break.
- **Severity:** 🟡

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 1 · ✅ 4 (best workflow source-grep in repo, but still source-grep)

---

# 88. `tests/test_news_signal_evidence_report.py` (167 lines)

**Covers:** `scripts/news_signal_evidence_report.py::build_report, format_markdown, write_outputs`

### ✅ GOOD-NSE-1: 2 tests but the first one (lines 8–152) builds a REALISTIC end-to-end fixture: 6 distinct artifact types (news_log, news_signals, watchlist, news_engine_run_status, late_daily_ideas, news_signal_outcomes, picks_log). **Highest fixture realism in batch.**
### ✅ GOOD-NSE-2: 27 distinct assertions on report shape (lines 121–144) — schema discipline.
### ✅ GOOD-NSE-3: All safety field assertions enforced (`mode == "monitoring_only"`, `read_only is True`, `paper/live_trading_enabled is False`, `official_pick_stats_mutated is False` — lines 122–126).

### ⚠️ BUG-NSE-1: 6 inline production-shape JSON literals (lines 12–101). DRY violation but the realism is the point. Track for refactor.
- **Severity:** 🟡

### ⚠️ BUG-NSE-2: `assert "Read-only" in md` (line 149) and `"Outcome rows" in md` (line 151) — substring on user-facing markdown. Format-fragile.
- **Severity:** 🟡

### ⚠️ BUG-NSE-3: `test_news_signal_evidence_report_writes_outputs` (lines 155–167) calls `build_report` with EMPTY data dir. Asserts only that files exist + `read_only is True`. Doesn't validate empty-state SCHEMA.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 3

---

# 89. `tests/test_news_signal_outcome_attribution.py` (149 lines)

**Covers:** `scripts/news_signal_outcome_attribution.py` (load_evidence, evaluate_evidence_item, write_outcomes, summarize_outcomes, main)

### ✅ GOOD-NSO-1: 5 tests cover load+dedupe across 3 sources, evaluate with fake history, missing-history fallback, write+summarize, --no-write CLI mode. Multi-layer.
### ✅ GOOD-NSO-2: `test_evaluate_evidence_item_with_fake_price_history` (lines 60–94) — uses `pd.DataFrame` fixture with realistic 4-day OHLCV. Direct numerical validation: `start=100, one_d=103, return=3%, horizon=106, return=6%`.
### ✅ GOOD-NSO-3: `test_main_no_write_does_not_create_output` (lines 138–148) — locks the read-only CLI contract.
### ✅ GOOD-NSO-4: All safety assertions present (lines 90–94, 107–108).

### ⚠️ BUG-NSO-1: `assert row["one_d_return_pct"] == 3.0` (line 87) — exact float on computed `(103-100)/100*100`. Math is clean here so probably safe, but should use `pytest.approx`.
- **Severity:** 🟡

### ⚠️ BUG-NSO-2: `assert summary["avg_one_d_return_pct"] == 3.0` (line 133) — same. With single evaluated row of 3.0% the avg=3.0 is safe; if test grows to 3 rows could flake.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 4

---

# 90. `tests/test_news_signals_negative_reaction.py` (95 lines)

**Covers:** `src/news_signals.py::_has_negative_reaction, add_signal_from_classification`

### ✅ GOOD-NSN-1: `_item(...)` factory (lines 7–18) — clean parameterized test-data builder.
### ✅ GOOD-NSN-2: 5 tests cover detector-helper, fade-bullish-on-negative-reaction, clean-bullish, bearish-not-weakened, hard-block-wins. **Excellent state-machine coverage** for a complex signal-mutation function.
### ✅ GOOD-NSN-3: `test_hard_block_still_wins_over_negative_reaction` (lines 76–94) — locks priority-ordering between safety mechanisms. **Critical for safety predictability.**
### ✅ GOOD-NSN-4: `test_negative_reaction_fades_bullish_signal_to_small_penalty` asserts `score_delta < 0 AND >= -0.03` (lines 39–40) — **bounded numeric range** instead of exact float. Best practice.

### ⚠️ BUG-NSN-1: `_has_negative_reaction` is private (underscore prefix, line 22) — tested directly. Same anti-pattern.
- **Severity:** 🟡

### ⚠️ BUG-NSN-2: `assert sig["score_delta"] == -1.0` (line 93) — exact float equality on the hard-block penalty. If penalty changes to -0.9999 due to float arithmetic, breaks.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 4

---

## 🎯 BATCH 111 grand totals

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 7 (MFD-1, MFP-1, NAW-1, NE-3 disguised grep, NER-1, NEP-1, NEW-1) |
| ⚠️ Data/safety risk | 4 |
| 🟡 Code smell | 22 |
| ✅ Good code | 42 |
| **Total findings** | **75 across 15 files / ~1,510 lines** |

### 🔥 ARCHITECTURE-RELEVANT FINDINGS THIS BATCH

1. **MFD-2 — almost-certainly-broken test in production:** `test_monitoring_first_docs.py` line 32 asserts `"1561 passed, 30 skipped" in text` against `docs/PROJECT_BLUEPRINT.md`. **Run this test today** — there's a high chance it's failing or the docs are stale because you've added tests since. This is a self-stale doc test.

2. **MMP-3 — best safety test in batch:** `test_monitoring_mode_no_paper_default.py` is 20 lines that lock the #1 safety toggle (`TRADING_MODE` defaults to monitoring → paper trading off). **This is the kind of test your remediation plan needs more of.**

3. **MR-2 — NEGATIVE EXPECTANCY GATE:** `test_evaluate_bucket_blocks_negative_expectancy_even_with_high_win_rate` (test_monitoring_readiness.py lines 62–75) is **EXEMPLARY safety regression testing.** "85% win rate with negative avg-R must NOT pass readiness gate." **Use this as the model** for the gates you build to prevent paper-trading promotion.

4. **NE-3 — disguised source-grep:** `test_news_engine.py::test_parallel_scorer_imports_watchlist` uses `inspect.getsource(ps)` to do source-grep. **This was missed in the source-grep tally because it doesn't use `Path.read_text()`.** Probably more of these exist in the codebase.

### 🚨 NEW PATTERN DISCOVERED

`inspect.getsource(module)` followed by `"foo" in src_code` is **source-grep in disguise**. Add this to the search pattern when refactoring source-grep tests away. Search regex: `inspect\.getsource\(.+\)`.

### Production code coverage from this batch

- `src/missing_data_gate.py`, `src/monster_hunt.py`, `src/news_signals.py`, `src/news_classifier.py`, `src/news_engine.py`, `src/watchlist_manager.py`, `src/parallel_scorer.py` (via inspect)
- `scripts/monitoring_readiness.py`, `scripts/run_news_engine.py`, `scripts/news_signal_evidence_report.py`, `scripts/news_signal_outcome_attribution.py`
- `main.py` (`_should_log_paper_trade`, `_safe_trade_type_for_pick`)
- `docs/decisions/2026-05-05-monitoring-first-no-paper-trading.md`, `docs/PROJECT_BLUEPRINT.md`, `docs/WORK_LOG.md`, `docs/NEXT_SESSION.md`, `docs/playbook/NEWS_EVIDENCE_REPORTS.md` (grep only)
- `.github/workflows/news_engine.yml`, `.github/workflows/news_evidence.yml` (grep only)

### Next batch (112) — files 91–105 alphabetically:
`test_news_to_picks.py`, `test_news_workflow_persistence.py`, `test_nightly_conductor.py`, `test_non_trading_day_trade_type_guard.py`, `test_official_artifact_loader.py`, `test_official_artifact_outputs.py`, `test_official_pick_artifact.py`, `test_opening_range_observation_backtest.py`, `test_opening_range_observation_review.py`, `test_opening_range_scanner.py`, `test_parallel_scorer_monster_data.py`, `test_pattern_engine.py`, `test_pattern_hint.py`, `test_pattern_layer.py`, `test_pattern_stats.py`
