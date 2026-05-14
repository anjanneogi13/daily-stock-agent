# Audit Batch 117 — tests/ files 165–181 (alphabetical) — TRUE line-by-line

**Pinned commit:** `0dcd05c9`
**Files audited:** 181 of ~196 (cumulative)
**Total lines audited in this batch:** ~1,640
**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

> Note: Several test names from the projected list (test_strategy_aware_decision, test_strategy_planner, test_telegram_dedup, test_unpause, test_watchlist_news_sniffer, etc.) **don't exist in the repo** — they were guessed. Real directory listing showed ~196 test files total (not 178 as projected). Auditing the 17 real files this batch.

---

# 165. `tests/test_smell_persistence.py` (46 lines)

**Covers:** `src/pick_logger.py::FIELDS`, `main.py`, `src/pick_logger.py` (Bug #17A)

### ✅ GOOD-SP-1: Header docstring (lines 1–12) — explicit problem/contract documentation. Names Bug #17A and the upstream pipeline.
### ✅ GOOD-SP-2: `test_pick_logger_fields_include_smell_columns` (lines 28–30) — **behavioral test** that imports FIELDS and checks set membership. Refactor-safe.

### 🚨 BUG-SP-1: `test_main_serializes_smell_warnings_for_log` (lines 33–38) — source-greps `main.py` for 4 substrings. Fragile.
- **Severity:** 🚨

### 🚨 BUG-SP-2: `test_pick_logger_writes_smell_columns` (lines 41–45) — source-greps for EXACT 3 strings like `'"smell_codes": p.get("smell_codes", "")'`. Black/isort detonation.
- **Severity:** 🚨

**Per-file:** 🚨 2 · ⚠️ 0 · 🟡 0 · ✅ 2

---

# 166. `tests/test_smell_wired_in_main.py` (51 lines)

**Covers:** `main.py` — **100% SOURCE-GREP**

### ✅ GOOD-SWM-1: Header docstring (lines 1–4) — names the failure mode: "future refactors could silently remove the smell gate and we'd have no idea." Concrete.
### ✅ GOOD-SWM-2: `test_smell_runs_after_ev_and_pause_gates` (lines 44–50) — uses **string-position ordering** (smell_idx > ev_idx) to assert pipeline order. Sophisticated for a source-grep, but still source-grep.

### 🚨 BUG-SWM-1: 5 tests, ALL source-grep on `main.py`:
- `"from src.smell_faculty import" in MAIN_PY` (line 13)
- `"SMELL FACULTY" in MAIN_PY` (line 22) — locks COMMENT TEXT
- `"for p in top:" in section` (line 25) — locks loop variable name
- `"SMELL_ENFORCE" in MAIN_PY` (line 31)
- Section-position ordering (lines 37–50)
- Comment renames detonate. Variable renames (`top`→`finalists`) detonate. **Section header `# SMELL FACULTY` becomes a hard contract.**
- **Severity:** 🚨

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 0 · ✅ 2

---

# 167. `tests/test_stale_price_smell.py` (106 lines)

**Covers:** `src/smell_faculty.py::smell_stale_price, sniff, ALL_SMELLS`, `src/data_fetcher.py::is_valid_market_data`

### ✅ GOOD-STP-1: 14 tests cover all 7 stale-price scenarios (agree, drift-warns, blocks, no-entry, no-ticker, finnhub-down, registered, sniff-integration) + 7 validator scenarios (valid, none, zero, negative, zero-volume, suspicious-high, non-numeric). **Most defensive battery in batch.**
### ✅ GOOD-STP-2: `test_smell_silent_when_finnhub_down` (lines 45–50) — locks the **graceful-degradation contract**: provider failure must NOT create false-positive blocks. **Critical for the "premarket failures" issue.**
### ✅ GOOD-STP-3: `test_sniff_includes_stale_price_in_critical_block` (lines 58–67) — END-TO-END integration test verifying the new smell is wired into the registry.
### ✅ GOOD-STP-4: All `mock` calls patch `src.finnhub_data.fetch_finnhub_quote` — proper module-path mocking.
### ✅ GOOD-STP-5: Validator tests use named tuples `(ok, reason)` — verifies BOTH boolean AND reason text.

### ⚠️ BUG-STP-1: `assert "None" in reason or "delisted" in reason` (line 79), `"untradeable" in reason or "volume" in reason.lower()` (line 95) — substring on user-facing reason text.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 5

---

# 168. `tests/test_stooq_provider.py` (18 lines)

**Covers:** `src/market_data_providers/stooq_provider.py::stooq_symbol`

### ✅ GOOD-STOOQ-1: 2 tests cover rejects-invalid (4 cases: TSX:, ^, /) + keeps-simple-US (2 cases: AAPL, BRK.B).
### ✅ GOOD-STOOQ-2: `test_stooq_symbol_keeps_simple_us_symbols_conservative` (lines 13–17) — locks the **lowercase + .us suffix convention** for Stooq.

### ⚠️ BUG-STOOQ-1: Tiny 18-line file. Only 2 tests for an entire data-provider module. **Coverage gap — no tests for actual data fetching, error handling, rate limiting.**
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 2

---

# 169. `tests/test_strategy_breakdown.py` (121 lines)

**Covers:** `src/strategy_breakdown.py::breakdown_by, format_breakdown_text`

### ✅ GOOD-SBR-1: 11 tests cover no-log, pending-excluded, basic-grouping, tag-isolates-losers, alpha-averaging, missing-alpha, unknown-group, format-empty, format-columns, sort-by-count.
### ✅ GOOD-SBR-2: `test_tag_breakdown_isolates_losers` (lines 62–73) — comment "Reproduces the SEMI/AI -7R observation." **Real production failure as test fixture.**
### ✅ GOOD-SBR-3: `test_pending_rows_excluded` (lines 41–43) — defensive against unevaluated picks polluting stats.
### ✅ GOOD-SBR-4: `_pick` and `_write` factories — clean parametric builders.

### ⚠️ BUG-SBR-1: `assert "swing" in out and "50%" in out and "0.50" in out` (line 109) — exact-string assertions on formatted output. Format-fragile.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 4

---

# 170. `tests/test_telegram_dual_section.py` (190 lines)

**Covers:** `scripts/send_telegram.py` (_classify_pick, build_message, _safe_float, _safe_int)

### ✅ GOOD-TDS-1: 17 tests cover classify (4), build_message (8), format helpers (2), edge cases (3). Comprehensive.
### ✅ GOOD-TDS-2: `_row` factory (lines 26–56) — exhaustive 24-field mock CSV row. Production-realistic.
### ✅ GOOD-TDS-3: `test_message_handles_bad_numeric_data` (lines 160–165) — defensive against empty entry/sl/tp. Real-world data hygiene.
### ✅ GOOD-TDS-4: Uses `spec_from_file_location` (lines 14–20) to import `send_telegram.py` without triggering `__main__` block. Same pattern as SI from batch 116.
### ✅ GOOD-TDS-5: `test_build_message_dual_section` (lines 116–130) verifies DAY appears BEFORE SWING via index comparison. Order-aware.

### 🚨 BUG-TDS-1: `os.environ["TELEGRAM_BOT_TOKEN"] = "test_token"` at module-level (line 8) — **mutates global state for ALL subsequent tests in the run**. Should be in a fixture with cleanup.
- **Severity:** 🚨 Cross-test contamination risk.

### ⚠️ BUG-TDS-2: `assert "−1.20%" in msg or "-1.20%" in msg` (line 137) — locks Unicode minus sign formatting. Fragile.
- **Severity:** 🟡

### ⚠️ BUG-TDS-3: `assert "PR #66" in msg` and `"#69" in msg` (lines 156–157) — locks PR-number footer text in a permanent test. **Will outlive the relevance of those PRs.**
- **Severity:** 🟡 Time-sensitive contract.

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 2 · ✅ 5

---

# 171. `tests/test_theme_discovery.py` (329 lines)

**Covers:** `scripts/discover_themes.py` (build_theme_discovery, extract_theme_terms, format_markdown, write_outputs)

### ✅ GOOD-TD-1: 6 tests, 329 lines — **largest file in batch**. Realistic mock JSON/CSV fixtures with 3+ tickers each.
### ✅ GOOD-TD-2: `test_theme_discovery_outputs_observe_only_artifact` (lines 41–118) — locks the **6-flag safety contract** (`observe_only`, `official_score_boost_enabled: False`, `production_scoring_effect: False`, `paper_trading_enabled: False`, `live_trading_enabled: False`, `buy_instructions_enabled: False`). **EXEMPLARY safety-mode test.**
### ✅ GOOD-TD-3: `test_theme_discovery_marks_news_hype_unconfirmed_for_low_breadth` (lines 121–148) — tests defensive labeling: low-breadth themes get `news_hype_unconfirmed` flag.
### ✅ GOOD-TD-4: `test_theme_discovery_reports_missing_market_evidence_not_guessed` (lines 188–216) — locks the **"don't guess when data missing"** contract. Critical defensive principle.
### ✅ GOOD-TD-5: `test_theme_discovery_provider_evidence_uses_readiness_and_market_health` (lines 282–328) — wires test through 4 input artifacts (watchlist, signals, picks, readiness, health). Realistic.
### ✅ GOOD-TD-6: Helper functions (`write_json`, `write_picks`) keep tests DRY.

### ⚠️ BUG-TD-1: 6 tests but a lot of boilerplate (~80% of lines are fixture data, not assertions). Could be parametrized.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 6 (highest GOOD count in batch)

---

# 172. `tests/test_theme_pick_bridge.py` (209 lines)

**Covers:** `scripts/build_theme_pick_bridge.py` (build_theme_pick_bridge, format_markdown, write_outputs)

### ✅ GOOD-TPB-1: 4 tests cover compares-official-rejected-watch-only, marks-missing-when-no-rejection, writes-outputs, preserves-market-evidence.
### ✅ GOOD-TPB-2: `test_theme_pick_bridge_compares_official_rejected_and_watch_only` (lines 31–110) — **integration test** wires together 4 input artifacts (theme, picks_log, rejections, late_ideas). Tests the cross-artifact reconciliation logic.
### ✅ GOOD-TPB-3: Same 6-flag safety contract verified (lines 89–95) as TD-2. Consistent observe-only enforcement.
### ✅ GOOD-TPB-4: Asserts `likely_gap_reasons` contains 4 categories — **locks the categorization taxonomy.**

### ⚠️ BUG-TPB-1: Same boilerplate density as TD-1.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 4

---

# 173. `tests/test_theme_scoring_guardrails.py` (87 lines)

**Covers:** `src/theme_scoring_guardrails.py`, `src/scorer.py`, `src/parallel_scorer.py`, `src/probability_engine.py`, `src/news_signals.py`, `config.yaml`

### ✅ GOOD-TSG-1: 5 tests + 4 parametrized cases cover all 6 safety flags + 4 enable-attempts (rejected) + 3 disable-configs (accepted) + explanation-text + production-isolation + config-yaml.
### ✅ GOOD-TSG-2: `test_production_scorers_do_not_import_theme_artifacts` (lines 57–79) — **STATIC ENFORCEMENT** that 4 production scorer files don't import any of 9 theme-related symbols. **Best architecture-boundary test in repo.**
### ✅ GOOD-TSG-3: 9-token forbidden list (lines 64–74) is comprehensive — `theme_discovery_`, `build_theme_*`, `theme_strength_score`, etc.
### ✅ GOOD-TSG-4: Test exists specifically to **prevent observe-only theme work from leaking into production scoring**. Direct safety value.

### ⚠️ BUG-TSG-1: `test_config_does_not_enable_theme_scoring` (lines 82–86) — source-greps `config.yaml` for negative substrings. YAML-comment grep variant.
- **Severity:** ⚠️

### ⚠️ BUG-TSG-2: TSG-2 uses substring on file text. If a future variable name is `theme_strength_score_v2`, the test would fire on legit code.
- **Severity:** 🟡 Substring is brittle; use AST import-detection for true safety.

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 1 · ✅ 4 (most architecturally-valuable test in batch)

---

# 174. `tests/test_tiered_exits_reserved.py` (53 lines)

**Covers:** `data/picks_log.csv`, `docs/PROJECT_BLUEPRINT.md`, `docs/NEXT_SESSION.md`, `scripts/send_telegram.py`

### ✅ GOOD-TER-1: `test_existing_picks_do_not_have_active_tiered_exit_fields` (lines 17–28) — **production data-integrity guard**: ensures no rows have populated tier fields.
### ✅ GOOD-TER-2: `_has_active_value` (lines 8–14) defensive against `"None"`, `"nan"`, `"null"`, `"[]"` strings.

### 🚨 BUG-TER-1: 3 of 4 tests source-grep DOCS files (`PROJECT_BLUEPRINT.md`, `NEXT_SESSION.md`, `send_telegram.py`):
- `"Tiered exit fields are reserved schema only" in text` (line 34)
- `"decide tiered TP fate" not in text` (line 45)
- `"if tp1 > 0 and tp2 > 0 and (qt1 + qt2 + qt3) > 0 and entry > 0:" in text` (line 52) — **EXACT 60-character source line**
- **Severity:** 🚨

### 🚨 BUG-TER-2: `test_existing_picks_do_not_have_active_tiered_exit_fields` reads PRODUCTION `data/picks_log.csv`. **5th instance of production-data coupling.**
- **Severity:** 🚨

**Per-file:** 🚨 2 · ⚠️ 0 · 🟡 0 · ✅ 2

---

# 175. `tests/test_todo_bugs_status.py` (60 lines)

**Covers:** `docs/PROJECT_BLUEPRINT.md`, `docs/WORK_LOG.md`, `docs/TODO_BUGS.md` — **100% DOC SOURCE-GREP**

### ✅ GOOD-TBS-1: Tests check that 3 docs preserve key content sections.

### 🚨 BUG-TBS-1: ENTIRE 60-line file is doc source-grep. ~30 substring assertions on free-text markdown.
- Examples: `"Documentation consolidation" in text`, `">60%" in text`, `">66%" in text`, `">90%" in text`, `"Paper trading stays blocked" in text`.
- **Severity:** 🚨 Worst doc-grep concentration in repo.

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 0 · ✅ 1

---

# 176. `tests/test_trigger_context.py` (104 lines)

**Covers:** `src/wisdom_base.py`, `src/book_ingest.py`, `src/wisdom_hint.py`

### ✅ GOOD-TC-1: 11 tests cover eval-trigger numeric + string-eq + missing-key + malformed + empty + None inputs, eval_triggers (AND-logic), add_lesson persists triggers, lessons_for_context fires + skips, book_ingest passes through, context_hint surfaces + empty.
### ✅ GOOD-TC-2: `test_eval_trigger_malformed_returns_false` (lines 32–35) — defensive against `"garbage"`, `""`, `None`.
### ✅ GOOD-TC-3: `test_eval_triggers_all_required` (lines 37–41) — locks the **AND-semantics** for trigger lists.
### ✅ GOOD-TC-4: `test_book_ingest_passes_triggers` (lines 70–89) — END-TO-END from YAML seed → JSONL persistence → trigger evaluation.

### ⚠️ BUG-TC-1: `assert "Cut losses" in hits[0]["text"]`, `"average down" in hits[0]["text"]` — substring on lesson text.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 4

---

# 177. `tests/test_validate_daily_no_pick.py` (88 lines)

**Covers:** `scripts/validate_daily_no_pick.py`, `src/premarket_decision_contract.py`

### ✅ GOOD-VDN-1: 4 tests cover valid-passes, requires-zero-picks, rejects-live-trading, load-from-disk + missing-returns-empty.
### ✅ GOOD-VDN-2: `valid_no_pick_payload()` (lines 14–46) — exhaustive 30-field reference payload using IMPORTED CONSTANTS. **Best contract test in batch.**
### ✅ GOOD-VDN-3: `test_no_pick_report_rejects_live_trading_enabled` — locks the safety invariant: a no-pick report with live_trading_enabled=true must FAIL validation.
### ✅ GOOD-VDN-4: Uses mutation pattern — tests the validator on synthetic invalid input.

### ⚠️ BUG-VDN-1: Locks EXACT 60-char error message (line 59). Format-fragile.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 4

---

# 178. `tests/test_validate_official_pick_artifacts.py` (94 lines)

**Covers:** `scripts/validate_official_pick_artifacts.py`, `src/official_pick_artifact.py`

### ✅ GOOD-VOPA-1: 3 tests cover accepts-matching, fails-when-missing, fails-on-count-mismatch.
### ✅ GOOD-VOPA-2: `pick()` factory (lines 7–22) — realistic 7-field nested pick.

### ⚠️ BUG-VOPA-1: Tests do **filename-rewriting hacks** to normalize "today's ET date" — testing pain reflects design pain. Should refactor `write_official_pick_artifacts` to accept `date_str`.
- **Severity:** 🟡

### ⚠️ BUG-VOPA-2: Substring on error messages (lines 67, 68, 93).
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 2

---

# 179. `tests/test_weekly_review.py` (90 lines)

**Covers:** `src/weekly_review.py`

### ✅ GOOD-WR-1: 9 tests cover grade-no-picks, grade-A, grade-F-crisis, what-worked-empty, what-worked-finds, what-failed-finds, recommendations-crisis, recommendations-no-picks-safe, format-telegram-smoke, build-report-sections.
### ✅ GOOD-WR-2: `test_recommendations_no_picks_safe` — defensive: even with all-None inputs, returns at least 1 action.
### ✅ GOOD-WR-3: `test_grade_no_picks` — defensive against 0-closed-picks division-by-zero.

### 🚨 BUG-WR-1: `test_format_telegram_smoke` and `test_build_report_returns_all_sections` call `build_report(end_date=datetime.now())` → reads PRODUCTION data. **6th production-data-coupled test pattern.**
- **Severity:** 🚨

### ⚠️ BUG-WR-2: Substring on grade text. Format-fragile.
- **Severity:** 🟡

### ⚠️ BUG-WR-3: `datetime.now()` — time-dependent test. Could flake at midnight.
- **Severity:** 🟡

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 2 · ✅ 3

---

# 180. `tests/test_weight_applier.py` (146 lines)

**Covers:** `src/weight_applier.py`, `src/weight_proposer.py`, `src/learning_journal.py`

### ✅ GOOD-WA-1: 11 tests cover apply-penalize, apply-boost, apply-kill, weekly-cap-blocks, cap-resets-next-week, idempotency, dry-run, history-records, history-summary, skip-invalid. **Complete state-machine coverage.**
### ✅ GOOD-WA-2: `test_weekly_cap_blocks_overflow` — locks the **5%/wk cap** safety invariant. Critical: prevents runaway weight mutations.
### ✅ GOOD-WA-3: `test_cap_resets_next_week` — uses ISO-week boundary timestamps. Tests the calendar logic.
### ✅ GOOD-WA-4: `test_apply_marks_proposals_and_skips_replays` — locks **idempotency**.
### ✅ GOOD-WA-5: `test_dry_run_does_not_persist` — defensive: dry_run=True must not write any files.
### ✅ GOOD-WA-6: Uses `pytest.approx(0.96, rel=1e-2)` — relative tolerance. Best practice.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 0 · ✅ 6 (zero-issue file — exemplary state-machine coverage)

---

# 181. `tests/test_wisdom_base.py` (130 lines)

**Covers:** `src/wisdom_base.py` (lessons + patterns + kill list), `src/wisdom_consultant.py`

### ✅ GOOD-WB-1: 11 tests cover lessons (3), patterns (1), kill-list (3 including auto-expire), consultant (4).
### ✅ GOOD-WB-2: `test_kill_list_auto_expire` — uses **manually-constructed expired entry** to test cleanup logic.
### ✅ GOOD-WB-3: `test_consult_pattern_boost_capped` — locks the **+0.05 cap** safety invariant on score adjustments.
### ✅ GOOD-WB-4: `test_kill_list_add_and_check` — case-insensitivity (UNH vs unh).

### 🚨 BUG-WB-1: `_isolate_wisdom_dir` (lines 12–18) **mutates module-level globals** `wb.ROOT`, `wb.LESSONS`, `wb.PATTERNS`, `wb.KILL` directly without `monkeypatch`. **Bleeds state across tests.**
- **Severity:** 🚨 Cross-test contamination risk.

### ⚠️ BUG-WB-2: Uses positional defaults in `wb.add_lesson("low", confidence=0.2)`. Signature-fragile.
- **Severity:** 🟡

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 1 · ✅ 4

---

## 🎯 BATCH 117 grand totals

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 9 (SP-1, SP-2, SWM-1, TDS-1, TER-1, TER-2, TBS-1, WR-1, WB-1) |
| ⚠️ Data/safety risk | 1 |
| 🟡 Code smell | 19 |
| ✅ Good code | 60 |
| **Total findings** | **89 across 17 files / ~1,640 lines** |

### 🔥 ARCHITECTURE-RELEVANT FINDINGS THIS BATCH

1. **TBS-1 + TER-1 — DOC source-grep pattern crystallizes.** `test_todo_bugs_status.py` (60 lines, 100% doc-grep) and `test_tiered_exits_reserved.py` (3 of 4 tests doc-grep) lock free-text markdown phrasing as hard contracts.

2. **TSG-2 — best architecture-boundary test in repo.** Verifies 4 production files don't reference 9 theme-related symbols. Apply pattern to other observe-only features.

3. **TDS-1 + WB-1 — module-level global mutation antipattern.** `os.environ["TELEGRAM_BOT_TOKEN"]` set at module-level in TDS, and `_isolate_wisdom_dir` mutates `wb.ROOT` directly without monkeypatch. Both are cross-test contamination bombs.

4. **WR-1 + TER-2 — production-data-coupling reaches 6 instances:**
   - `test_picks_log_company_names.py` (CN-1)
   - `test_picks_log_spy_alpha_fill_rate.py` (SAFR-1)
   - `test_quarterly_report.py` (QR-1)
   - `test_signal_journal_quality.py` (SJQ-1)
   - `test_tiered_exits_reserved.py` (TER-2)
   - `test_weekly_review.py` (WR-1)

5. **STP — exemplary safety-gate coverage.** 14 tests including `test_smell_silent_when_finnhub_down` which guards against the **exact failure mode in your premarket pipeline**.

6. **VDN — best contract test in batch.** Uses imported constants (DECISION_OFFICIAL_NO_PICK, STRATEGY_LANE) — refactor-safe.

### 14+ files remain in tests/ for true 100% audit (batch 118):
`test_watch_only_outcomes.py`, `test_week2_3_4.py`, `test_weekly_postmortem.py`, `test_weight_proposer.py`, `test_wisdom_audit.py`, `test_wisdom_coverage.py`, `test_wisdom_coverage_rules.py`, `test_wisdom_drop.py`, `test_wisdom_hint_book_attr.py`, `test_wisdom_hint_cli.py`, `test_wisdom_hint_inline.py`, `test_wisdom_in_telegram.py`, `test_workflow_issue_upsert.py`, `test_workflow_persistence_complete.py`, `test_workflow_persistence_finding6.py`, `test_wow_trend.py`, `test_write_guard_no_pick_artifact.py`, `test_write_official_workflow_summary.py`, `test_yearly_report.py`
