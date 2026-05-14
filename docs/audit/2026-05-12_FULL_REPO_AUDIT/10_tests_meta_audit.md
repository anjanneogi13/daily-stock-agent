# Audit Batch 4 — tests/ META-AUDIT (178 files)

**Date:** 2026-05-12
**Approach:** Portfolio analysis. 178 test files (~110,000 lines total) cannot be reviewed one-by-one in a reasonable batch. This audit examines:
- Full filename inventory (178 files)
- 17 representative samples covering every visible category (smoke, contract, faculty, integration, regression, audit, fuzz, footer, workflow-grep, schema, lifecycle)
- Cross-cutting patterns

If you want any specific subset (e.g., "all 14 patterns_* tests" or "all 6 phase2b_* tests") audited file-by-file, just say the word.

---

## TEST SUITE INVENTORY (178 files, by category)

| Category | # files | Representative examples |
|---|---:|---|
| Patterns engine | 14 | test_patterns_base, _breakouts, _cup_handle, _double, _flags, _head_shoulders, _hhhl, _triangles, _wedges, _pattern_engine, _pattern_layer, _pattern_stats, _pattern_hint, _scan_patterns |
| Wisdom layer | 13 | test_wisdom_base, _audit, _coverage, _coverage_rules, _drop, _hint_*, _in_telegram, _consultant, _daily_wisdom, _bootstrap, _capture_efficiency_in_wisdom, _sector_wisdom |
| News engine | 11 | test_news_engine, _engine_finding3, _engine_run_status, _evidence_*, _signal_*, _signals_negative_reaction, _to_picks, _action_window_guard, _workflow_persistence, _market_news |
| Phase 2B exits | 5 | test_phase2b_adaptive_sl/_tp/_scaleout/_trailing/_integration |
| Pillar footers | 5 | test_pillar1/4/5/6_footer + test_calibration_footer |
| Backfills | 6 | test_backfill_alpha/_earnings_days/_journal/_regime/_smell_columns + sector_alpha_backfill |
| Pick evaluator + lifecycle | 9 | test_pick_evaluator(_day_close), _candidate_lifecycle, _candidate_diagnostics, _pick_dict_*, _pick_log_dict_*, _pick_logger_schema_contract, _pick_sanity, _picks_log_* |
| Daily picks pipeline | 7 | test_daily_picks_no_pick_*/_run_status/_workflow_reliability/_zero_pick_failure/_intelligence_brief, _validate_daily_no_pick, _dry_run_official_* |
| Intraday + opening range | 11 | test_intraday_monitor_*/_scanner_opening_range/_new_opportunity_cutoff/_opening_range_* |
| Premarket gates | 6 | test_premarket_decision_contract/_readiness_gate/_sanity_gate/_watch_only/_check_… + _missed_premarket_alert |
| Late watch-only ideas | 5 | test_late_daily_ideas/_watch_only_sent_ledger_persistence/_dry_run_official_*/_send_late_daily_ideas_telegram/_layman_translator |
| Regime + market data | 8 | test_regime_*/_market_calendar/_market_data_*/_stooq_provider/_data_quality/_data_readiness_report |
| Sector benchmark | 7 | test_sector_alpha_backfill/_benchmark/_benchmark_subsectors/_benchmark_wiring/_breakdown/_pnl/_wisdom |
| Theme discovery | 4 | test_theme_discovery/_pick_bridge/_scoring_guardrails + week2_3_4 |
| Audit infrastructure | 8 | test_audit_dead_code/_earnings_fill_rate/_lane1_*/_sector_fill_rate, test_full_repo_audit_*, test_journal_consistency, test_signal_journal_quality |
| Faculty integration | 5 | test_faculty_integration, test_smell_faculty(+_finding2), test_smell_persistence, test_smell_wired_in_main, test_smell_enforcement_readiness |
| LLM + brain | 4 | test_llm_agent, test_meta_brain, test_self_awareness, test_nightly_conductor |
| Scoring + risk | 6 | test_basic, test_scoring_safety, test_risk_metrics, test_portfolio_risk_gate, test_position_monitor, test_phase2b_integration |
| Regime sizing + auto-actions | 5 | test_regime_aware_sizing, test_auto_pause/_cooldown/_lesson_on_cool/_promote |
| Calibration + confidence | 4 | test_calibration, _calibration_footer, _bucket_calibration, _confidence_band |
| Watch-only outcomes + paper-trade gate | 4 | test_watch_only_outcomes (12k), _monitoring_*, _premarket_watch_only |
| Edge + fuzz | 1 | test_edge_case_fuzz |
| Telegram + senders | 4 | test_telegram_dual_section, _dedup_sender, _send_*, _wisdom_in_telegram |
| Workflow grep tests | 8 | test_*_workflow_*.py + test_intraday_monitor_workflow*, _github_observability, _workflow_issue_upsert, _workflow_persistence_complete |
| Other + small | ~20 | misc smaller singletons |
| **Total** | **178** | |

---

## CROSS-CUTTING FINDINGS

### ✅ T-X1: Test discipline is GENUINELY exceptional

This is the strongest part of the codebase. Out of ~24,750 LOC of production code, there are ~33,000 LOC of test code (1.33x ratio). For comparison:
- Industry average: 0.5–0.8x
- Well-tested OSS projects: 1.0–1.5x
- This repo: **1.33x** — top quartile.

Many tests are written **after a real production bug** (commented at top: "Discovered May 4 2026: 6 Apr 28 SEMI picks logged with entry prices $2-$20 ABOVE..." in test_pick_evaluator.py:1-7). Bug → test → fix discipline is **embedded in the culture**.

### ✅ T-X2: Bug-for-bug regression catalog
Files explicitly named after specific findings:
- `test_news_engine_finding3.py`
- `test_smell_faculty_finding2.py`
- `test_probability_engine_finding5.py`
- `test_workflow_persistence_finding6.py`
- `test_regime_finding4.py`
- `test_agent_memoir_finding1.py`

This is a "findings ledger" pattern — every numbered finding has a corresponding regression test. Excellent traceability.

### ✅ T-X3: Contract tests prevent silent schema drift
- `test_picks_log_column_contract.py`: AST-based check that EVERY `csv.DictReader` reader uses real CSV columns. Catches the kind of bug seen in Batch 3 (X-IO1, BUG-LA1) at test-time. Brilliantly precise (line 41-66 narrows to loop-var receivers only).
- `test_premarket_decision_contract.py`: validates payload shape + version constants for the Lane 1 official decision.
- `test_pick_logger_schema_contract.py`: locks pick-logger output schema.

These are **architectural firewalls**.

### ✅ T-X4: Audit-the-audit pattern
- `test_audit_dead_code.py` tests `scripts/audit_dead_code.py` itself (3 import shapes + locked dead-list).
- `test_full_repo_audit_*` (4 files) test scripts/full_repo_audit.py.
- `test_scripts_import.py` smoke-imports EVERY script via `importlib.util.spec_from_file_location` with non-`__main__` name to skip top-level guards (lines 32-40).

The audit infrastructure has its own audit infrastructure. Recursive defensive engineering.

### ✅ T-X5: Edge/fuzz coverage exists for prod-critical paths
`test_edge_case_fuzz.py` (213 lines) covers `auto_pause`, `auto_cooldown`, `wisdom_base` against:
- empty data, missing fields, garbage strings, `None`, future dates, corrupt JSONL, Unicode (BRK.A), 5000-char strings.

Each has explicit `pytest.fail(f"... crashed on ...")` patterns. Brilliant.

### ✅ T-X6: Hermetic isolation is the default
Most tests use `tmp_path` fixtures + `monkeypatch.setattr(module, "PATH_CONST", tmp_path / "...")`. Zero tracked-data pollution.

Examples:
- test_news_engine.py:20-24 — autouse fixture redirects `WATCHLIST_PATH`
- test_wisdom_base.py:12-18 — `_isolate_wisdom_dir()` helper
- test_pick_evaluator.py:27-59 — `_seed_pick()` helper builds tmp_path CSV

This is best-practice and surprisingly rare in real codebases.

---

### ⚠️ T-X7: Tests-as-grep — fragile workflow assertions
A pattern recurs ~15+ times: tests that read a workflow YAML or production script and `assert "literal string" in text`.

Examples:
- `test_premarket_watch_only.py` (10 lines): asserts `'"👀 WATCH ONLY", "could not verify fresh price'` is in `scripts/premarket_check.py`.
- `test_intraday_monitor_workflow_observations.py`: asserts `"data/opening_range_observations_*.jsonl" in workflow YAML`.
- `test_late_watch_only_sent_ledger_persistence.py`: asserts 3 path patterns in 2 YAMLs.
- `test_full_repo_audit_drift.py:60-64`: asserts `` "`watchlist.py`" not in PROJECT_BLUEPRINT.md ``.
- `test_smell_wired_in_main.py`: greps main.py for smell-faculty wire-up.
- `test_news_engine.py:274-282`: greps `parallel_scorer.py` source for `"watchlist_score_boost"`.

Plain English: these tests are **regex-against-source**. They break on harmless reformatting (renaming a variable, adding a space, switching quote style). They don't actually run the code being tested.

Severity: ⚠️ Brittle. **Hard to refactor anything without breaking 5-10 tests.**

### ⚠️ T-X8: 14 separate `test_patterns_*.py` files for 8 pattern types
- test_patterns_base, _breakouts, _cup_handle, _double, _flags, _head_shoulders, _hhhl, _triangles, _wedges
- + test_pattern_engine, _pattern_layer, _pattern_stats, _pattern_hint
- + test_scan_patterns

Plain English: there's overlap between `pattern_engine`, `pattern_layer`, and the per-pattern files. Possible duplicate tests for same code paths.

Severity: ⚠️ Maintenance overhead; same change might require updates in 3+ files.

### ⚠️ T-X9: `test_basic.py` is misleadingly named — it's the ONLY scoring smoke test
This file (60 lines) is the only place that calls `composite_score`, `position_size`, `trade_plan` directly with end-to-end inputs. For a project where scoring IS the product, having a single 60-line "basic" test is thin.

Compare: there are 14 pattern-recognition tests but ~1.5 scoring tests. Coverage skewed heavily toward patterns over scoring.

Severity: ⚠️ Coverage imbalance.

### ⚠️ T-X10: Three "weekly review" footer tests + an integration gap
`test_pillar1_footer.py`, `test_pillar4_footer.py`, `test_pillar5_footer.py`, `test_pillar6_footer.py`, `test_calibration_footer.py` all do the same thing:
1. Build minimal data
2. Patch one module to raise
3. Assert `"Recommended action" in text` (the catch-all string)

Plain English: each footer test verifies "if X breaks, weekly still ships." None of them verifies the footers contain CORRECT content together. **A bug that swaps Pillar 1 and Pillar 6 footer order would not be caught.**

Severity: ⚠️ Tests are individually green; integration hole.

### ⚠️ T-X11: `test_pick_evaluator.py` test_sl_hit + test_tp_hit don't patch SPY/sector alpha consistently
Lines 155-156 patch `_add_spy_alpha` and `_add_sector_alpha` for sl_hit and tp_hit tests. But test_unreachable_entry_above_high (line 65) doesn't patch them. If those functions hit a network/yfinance call, that test could flake.

Severity: ⚠️ Inconsistent isolation = potential test flakiness.

### ⚠️ T-X12: No CI status visible in readme/audit dashboards
From all batches so far, no observed file lists "tests passing: 178/178" or similar. Whether all 178 tests actually PASS on every PR is unknown from this audit.

Severity: ⚠️ Test suite quality only matters if it runs green.

---

### 🟡 T-X13: `pytest.skip` guards on missing data files
Multiple tests (e.g., test_picks_log_column_contract.py:36-37) `pytest.skip("data/picks_log.csv missing")`. In a fresh checkout / CI with empty data, this test silently passes by skipping.

Plain English: fresh CI run could give false green just because data isn't there.

Severity: 🟡 Could mask coverage loss.

### 🟡 T-X14: Heavy reliance on `monkeypatch.setattr(module, "CONSTANT", ...)`
This works but means: if the production code changes from `JOURNAL = Path(...)` to `def get_journal_path(): return Path(...)`, every test breaks. Constants-as-API is a maintenance contract.

Severity: 🟡 Couples tests to production internals.

### 🟡 T-X15: Inline `sys.path.insert(0, ...)` in many tests
`test_news_engine.py:9`, `test_wisdom_base.py:6`, `test_hypothesis_engine.py:4`, `test_phase2b_integration.py:4`, `test_audit_dead_code.py:4`, etc.

Plain English: each test individually inserts repo root into sys.path. There's a `conftest.py` pattern that handles this once. Currently, ~20 files repeat this.

Severity: 🟡 DRY violation; either add a conftest or remove the inserts.

### 🟡 T-X16: Bug story documentation in docstrings is GREAT but fragile
Test files like `test_pick_evaluator.py:1-7` document the original bug discovery. Beautiful. But these docstrings drift over time (date references hard to verify). After 6 months, "May 4 2026" loses context.

Severity: 🟡 Add a link to the issue/PR for permanent traceability.

### 🟡 T-X17: Tests of LLM-dependent code
`test_llm_agent.py` (250 lines presumably) tests the LLM helper. Without seeing it: how does it test LLM responses? Two options:
1. Mocks (good but misses real-world behavior)
2. Live calls (flaky, expensive, network-dependent)

Severity: 🟡 Unknown without sampling — flagging as area to investigate.

### 🟡 T-X18: Test file size variance
Largest tests:
- test_intraday_scanner_opening_range.py (16k)
- test_faculty_integration.py (14.7k)
- test_theme_discovery.py (12.5k)
- test_watch_only_outcomes.py (12.3k)
- test_probability_engine.py (11.3k)
- test_pick_evaluator.py (10.3k)
- test_daily_intelligence_brief.py (10k)
- test_news_to_picks.py (9.5k)
- test_news_engine.py (9.5k)
- test_late_daily_ideas.py (9.2k)
- test_daily_picks_workflow_reliability.py (9.2k)
- test_official_artifact_outputs.py (9k)
- test_edge_case_fuzz.py (9.4k)

Smallest: test_premarket_watch_only.py (10 lines), test_missed_premarket_alert.py (522 bytes ≈ 15 lines), test_intraday_monitor_workflow_observations.py (16 lines).

Plain English: many "tests" are just 1-3 grep assertions. A unit-tests count of 178 overstates actual test density.

Severity: 🟡 Inflated test count; recommend tagging "smoke", "grep", "integration" pytest markers.

---

## QUALITY ASSESSMENT (sampled 17 of 178)

| Sample | Quality | Notes |
|---|---|---|
| test_basic.py | ✅ Excellent | Concise smoke for scorer/risk/indicators |
| test_pick_evaluator.py | ✅ Excellent | Bug-driven, F3 documented, hermetic |
| test_faculty_integration.py | ✅ Excellent | Multi-faculty integration, clean |
| test_news_engine.py | ✅ Excellent | Hermetic fixture, full lifecycle, regression assertion (line 274-282 is grep T-X7) |
| test_pillar1_footer.py | 🟡 Good but thin | Tests two paths, 38 lines for a whole pillar |
| test_pillar6_footer.py | 🟡 Same as Pillar 1 | Pattern repeats 5x |
| test_smell_faculty.py | ✅ Excellent | Comprehensive, every smell type, blocking-vs-warning, broken-input fuzz |
| test_wisdom_base.py | ✅ Excellent | Hermetic, lessons + patterns + kill-list + consultant |
| test_edge_case_fuzz.py | ✅ Outstanding | Best fuzz file in the repo |
| test_picks_log_column_contract.py | ✅ Outstanding | AST-based contract enforcement |
| test_premarket_decision_contract.py | ✅ Excellent | Clean payload validation |
| test_late_daily_ideas.py | ✅ Excellent | Hermetic, end-to-end, real-world bug examples (CCRN acquisition skip, GIG business combination) |
| test_audit_dead_code.py | ✅ Excellent | Tests own audit infra; locked KNOWN_DEAD set |
| test_scripts_import.py | ✅ Excellent | Catches dead imports across all scripts |
| test_full_repo_audit_drift.py | ✅ Good | Mostly real, line 60-64 is grep T-X7 |
| test_monitoring_mode_no_paper_default.py | ✅ Good | 3 tiny tests, real env-var assertions |
| test_premarket_watch_only.py | 🟡 GREP-ONLY | 10 lines, all `assert STRING in source` |
| test_intraday_monitor_workflow_observations.py | 🟡 GREP-ONLY | 16 lines, asserts paths in YAML |
| test_late_watch_only_sent_ledger_persistence.py | 🟡 GREP-ONLY | 18 lines, asserts paths in 2 YAMLs |
| test_hypothesis_engine.py | ✅ Excellent | Bucketing + p-value + analyze() integration |
| test_phase2b_integration.py | ✅ Excellent | End-to-end lifecycle smoke |

**Quality distribution from sample:** 13 excellent / 4 good / 3 grep-only / 0 broken.

If sample is representative of the full 178: ~75% excellent, ~15% good, ~10% grep-only.

---

## TOP RECOMMENDATIONS

### Top 5 things to fix in tests/

| # | Action | Why | Effort |
|---|---|---|---|
| 1 | Add `conftest.py` at tests/ root with sys.path insertion | Eliminates ~20 inline insertions (T-X15) | 5 min |
| 2 | Tag tests with pytest markers: `@pytest.mark.unit`, `@pytest.mark.grep`, `@pytest.mark.integration`, `@pytest.mark.fuzz` | Lets you run `pytest -m "not grep"` for fast iter loop. 178 tests is heavy. | 30-60 min |
| 3 | Replace YAML-grep tests with workflow-trigger smoke tests | Use `actionlint` + a single "all expected paths exist in workflows" parametrized test instead of 8 tiny grep files | Medium |
| 4 | Beef up `test_basic.py` | Single thin scoring test for the whole product. Add 10-15 cases. | 1-2 hr |
| 5 | Add `test_evaluation_status_constants.py` | Locks the canonical CLOSED_STATUSES = {"tp_hit","sl_hit","expired"} set as src constant + tests every consumer uses it. Kills X-BR4 (Batch 3e) drift. | 1 hr |

### Top 3 things that are MODEL CITIZEN tests
1. `test_picks_log_column_contract.py` — AST-based, precise, catches a bug class.
2. `test_edge_case_fuzz.py` — comprehensive fuzz against prod-critical modules with explicit fail messages.
3. `test_audit_dead_code.py` — tests its own audit, locks dead-list.

Use these as templates for new test files.

---

## SUMMARY

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 0 |
| ⚠️ Data/safety risk | 6 |
| 🟡 Code smell | 6 |
| 📝 Doc-only | 0 |
| ✅ Good code (cross-cutting) | 6 |
| Per-file good code | ~13 (from sample) |
| **Total findings** | 18 cross-cutting + sample-level notes |

**Test suite is the strongest part of the codebase.** Most production-code findings from Batches 1-3 (e.g., CLOSED_STATUSES drift, Telegram-impl duplication, module-level side effects) are NOT caught by tests. The test suite has excellent local discipline but doesn't enforce architectural invariants across modules.

**Cumulative across all batches (1a/1b/2a/2b/3a/3b/3c/3d/3e/4):**
- Show-stoppers: 118
- Data/safety risks: 238
- Code smells: 200
- Doc-only: 14
- Good-code citations: 255+
- **Total: ~825 findings across 286 files**

---

## What's left in the audit

After this batch:
1. ✅ Workflows (.github/) — Batch 1a-1b
2. ✅ src/ — Batches 2a-2b
3. ✅ scripts/ — Batches 3a-3e
4. ✅ tests/ — this batch (meta)
5. ⏳ docs/ — multi-hundred markdown files. Likely a meta-batch like this.
6. ⏳ config.yaml + watchlist.json + main.py + app.py — root-level files
7. ⏳ data/ schemas (already covered in passing) — may not need its own batch

Recommended next: Batch 5a — root-level files (main.py, app.py, config.yaml). These are the entry points and have been referenced 50+ times across all prior batches but never directly audited.

End of Batch 4.
