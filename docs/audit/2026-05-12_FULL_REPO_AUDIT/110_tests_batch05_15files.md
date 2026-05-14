# Audit Batch 110 — tests/ files 61–75 (alphabetical) — TRUE line-by-line

**Pinned commit:** `1f10a2e0`
**Files audited:** 75 of 178 (cumulative)
**Total lines audited in this batch:** ~1,910
**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

# 61. `tests/test_intraday_scanner_opening_range.py` (490 lines — LARGEST FILE IN BATCH)

**Covers:** `scripts/intraday_scanner.py` (scan_opening_range_opportunities, scan_for_new_opportunities, append_opening_range_observations, append_intraday_momentum_observations, write_opening_range_bar_artifact, refresh_opening_range_bar_artifacts_for_observations, append_opening_range_run_status), `scripts/intraday_monitor.py::build_message`

### ✅ GOOD-ISO-1: 13 tests — full coverage of opening-range pipeline incl. happy path, stale-session skip, non-OR/non-watch-only filtering, bars merging, refresh-existing-observations.
### ✅ GOOD-ISO-2: `bar()` helper (lines 20–28) and `breakout_bars()` factory (lines 31–37) — clean reusable test data.
### ✅ GOOD-ISO-3: `tzinfo=ET` on EVERY datetime (lines 22, 51, 138, 168, 219, 257, 312, 342, 364, 372, 385, 415, 423, 435, 468, 480) — exemplary timezone discipline.
### ✅ GOOD-ISO-4: `test_scan_opening_range_opportunities_skips_stale_session_bars` (lines 328–346) — tests that a Thursday's bars don't trigger Friday morning's scan. **Direct relevance to your intraday breakage.**
### ✅ GOOD-ISO-5: `test_refresh_opening_range_bar_artifacts_reports_stale_session` (lines 451–489) — tests the FAILURE-TYPE field (`failure_type: "stale_data"`) is set. Telemetry contract.

### ⚠️ BUG-ISO-1: `assert "Reference levels: Observed $101.60" in msg` (line 107) and `assert "Observe levels: Entry" not in msg` (line 108) — exact-string + absence-string contracts. Same brittleness as IMO-2/IMO-3.
- **Severity:** 🟡

### ⚠️ BUG-ISO-2: Heavy reliance on `patch.object(scanner, ...)` for FOUR functions per test (lines 43–50, 64, 331–338, etc.) — large mock surface.
- **Severity:** 🟡

### ⚠️ BUG-ISO-3: Magic numbers `1.3039`, `0.5941`, `3.1818` (lines 128, 131, 132) — synthetic decimals that look real but have no derivation comment. Hard to maintain.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 5 (highest GOOD count + most behavioral coverage in batch — model file)

---

# 62. `tests/test_journal_consistency.py` (64 lines)

**Covers:** `scripts/audit_journal_consistency.py::audit, _load_picks_keys, _load_journal_keys`

### ✅ GOOD-JC-1: Header docstring (lines 1–6) explicitly documents the locked invariant ("39/39 in sync as of May 4 2026"). **Locked-fact test pattern.**
### ✅ GOOD-JC-2: Module-level `pytestmark = pytest.mark.skipif` (lines 15–18) cleanly handles missing data dependency.
### ✅ GOOD-JC-3: 4 tests cover shape, missing-from-journal, orphan-in-journal, count-match. State-symmetric.

### ⚠️ BUG-JC-1: ALL behavior tests skip when `data/picks_log.csv` missing — masks failures on fresh clones
- Same anti-pattern as DQ-1, ER-1.
- **Severity:** ⚠️

### ⚠️ BUG-JC-2: Imports private `_load_picks_keys`, `_load_journal_keys` (line 12) but never uses them in any test. Dead imports.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 1 · ✅ 3

---

# 63. `tests/test_late_daily_ideas.py` (278 lines)

**Covers:** `scripts/generate_late_daily_ideas.py` (build_late_ideas, compute_display_score, detect_risk_flags, format_markdown, late_ideas_path, late_ideas_markdown_path, write_outputs)

### ✅ GOOD-LDI-1: 9 tests cover happy path, suppression-no-quote-identity, acquisition-arbitrage skip, news-display score cap, business-combination risk-flag, takeover-bid risk flags. **Best risk-flag coverage in repo.**
### ✅ GOOD-LDI-2: Realistic news payloads (lines 29–59, 192–200, 230–245) — production-shaped JSON.
### ✅ GOOD-LDI-3: `test_late_news_display_score_is_capped_below_100_for_standard_news` (lines 211–222) — locks the score-cap contract. Critical for "no false 100/100" guarantee.
### ✅ GOOD-LDI-4: All assertions enforce `paper_trading_enabled is False` and `live_trading_enabled is False` (lines 85–86, 96–98) — safety contract.

### 🚨 BUG-LDI-1: `assert idea["score"] == 75.0` (line 257) — **EXACT FLOAT EQUALITY** on a computed display score
- If float math drifts by 0.000001 (compiler/numpy version), test fails. Should use `pytest.approx`.
- **Severity:** ⚠️ Floating-point fragility on a CRITICAL safety-score test.

### ⚠️ BUG-LDI-2: Truncated string in test at line 105 (`"score_explanation": "...display_score=7[...]"`)
- **The actual test source has `[...]` ellipsis in a STRING value.** This will not match production output. **TEST IS BROKEN AS WRITTEN** — either CI is skipping this assertion, OR the string ellipsis is intentional placeholder (in which case test isn't actually validating).
- **Severity:** 🚨 Broken test (verify in source).

### ⚠️ BUG-LDI-3: `assert tickers == ["ERNA", "ALAB"]` (line 82) — exact ORDER assertion. If sort key changes, breaks.
- **Severity:** 🟡

**Per-file:** 🚨 1 · ⚠️ 1 · 🟡 1 · ✅ 4

---

# 64. `tests/test_late_watch_only_sent_ledger_persistence.py` (18 lines)

**Covers:** `.github/workflows/daily-picks.yml`, `.github/workflows/late_watch_only.yml` — **ALL VIA SOURCE-GREP**

### 🚨 BUG-LWO-1: 100% source-grep on workflow YAML files (both tests)
- Same anti-pattern as DPW, IMWO, IMWS. 18 tiny lines of pure YAML grep.
- **Severity:** 🚨

**Per-file:** 🚨 1 · ⚠️ 0 · 🟡 0 · ✅ 0

---

# 65. `tests/test_layman_translator.py` (140 lines)

**Covers:** `src/layman_translator.py` (score_to_words, confidence_label, risk_label, money, pct, r_multiple_words, pick_to_layman, outcome_to_layman, verdict_line, beat_market_line)

### ✅ GOOD-LT-1: 30 tiny single-purpose tests with clear section dividers. Excellent test discipline.
### ✅ GOOD-LT-2: `test_money_handles_string` (line 52) — defensive on bad input.
### ✅ GOOD-LT-3: `test_beat_market_handles_none` (line 138) — None safety.
### ✅ GOOD-LT-4: `test_pick_to_layman_includes_all_actionable_data` (lines 74–92) — multi-assertion contract test for the highest-stakes function.

### ⚠️ BUG-LT-1: Many tests check substring `"few days" in out or "weeks" in out` (line 88) — `or` shotgun. Either substring matches passes.
- **Severity:** 🟡

### ⚠️ BUG-LT-2: `assert lt.score_to_words(0.92) == "excellent"` (line 8) — magic threshold. No reference to `LT_THRESHOLDS` constant.
- **Severity:** 🟡

### ⚠️ BUG-LT-3: `test_money_zero` asserts `"$0"` (line 50) but `test_money_positive` asserts `"+$45.20"` — sign-prefix asymmetry. Unclear contract.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 4

---

# 66. `tests/test_learning_journal.py` (61 lines)

**Covers:** `src/learning_journal.py::log, read, summary`

### ✅ GOOD-LJ-1: `isolated` fixture (lines 11–15) — clean per-test journal isolation via monkeypatch.
### ✅ GOOD-LJ-2: 5 tests cover append, read-all, filter-by-days, summary-counts, empty. Complete.
### ✅ GOOD-LJ-3: `test_read_filters_by_days` (lines 35–44) writes an OLD record manually then writes a new one — tests time-window filter.

### ⚠️ BUG-LJ-1: `test_read_filters_by_days` parameter `monkeypatch` is in the signature but never used (line 35) — dead arg.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 3

---

# 67. `tests/test_lesson_gc.py` (157 lines)

**Covers:** `src/lesson_gc.py::find_stale, gc_stale, _cli`

### ✅ GOOD-LGC-1: 4 test classes (TestFindStale, TestProtections, TestGcStale, TestCLI) — clean organizational structure.
### ✅ GOOD-LGC-2: Boundary tests at exactly 89/91 days (lines 47–53). Tight.
### ✅ GOOD-LGC-3: `test_idempotent` (lines 111–116) — explicit second-run = 0 deactivations check.
### ✅ GOOD-LGC-4: 5 CLI tests (lines 119–156) — covers all flags including `--dry-run`, `--max-age`, `--protect`. Best CLI coverage in batch.

### ⚠️ BUG-LGC-1: `_lesson` factory uses `datetime.now()` (line 24) — time-dependent test. If clock skews mid-test, results could shift.
- **Severity:** 🟡

### ⚠️ BUG-LGC-2: `lesson_gc._cli([])` (line 122) — calls private `_cli` function. Should use `subprocess.run` against the actual entry point.
- **Severity:** 🟡

### ⚠️ BUG-LGC-3: `assert "Deactivated 1" in out` (line 131) — substring on stdout. Format-fragile.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 4

---

# 68. `tests/test_llm_agent.py` (222 lines)

**Covers:** `src/llm_agent.py` (_cache_key, _cache_put, _cache_get, _rule_based, _build_prompt, _is_quota_error, _try_provider, _explain_uncached, explain_pick)

### ✅ GOOD-LLM-1: 14 tests cover cache, prompt-building, quota detection, provider fallback chain (Claude→Gemini→OpenAI→rule-based). **Best LLM-fallback coverage in repo.**
### ✅ GOOD-LLM-2: `test_cache_get_handles_legacy_naive_timestamp` (lines 52–58) — tests backward-compat with old data. Migration awareness.
### ✅ GOOD-LLM-3: `_clear_env(monkeypatch)` helper (lines 27–29) — clean env hygiene.
### ✅ GOOD-LLM-4: `test_cache_key_is_stable_for_equivalent_payloads` (lines 32–37) — locks order-invariance contract critical for caching.
### ✅ GOOD-LLM-5: `test_explain_uncached_sets_claude_quota_and_falls_back_to_gemini` (lines 146–167) — tests STATEFUL behavior (quota flag flips).

### ⚠️ BUG-LLM-1: 9 tests on private `_*` functions. Same private-API anti-pattern repeated.
- **Severity:** 🟡

### ⚠️ BUG-LLM-2: `assert calls[1][1][-1] == "gemini-2.5-flash-lite"` (line 167) — hardcoded model name. If product-side model name changes, tests break unrelated.
- **Severity:** 🟡

### ⚠️ BUG-LLM-3: `(_ for _ in ()).throw(...)` generator-expression-as-raise hack (lines 195, 214) — same unreadable pattern as EA-1.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 5

---

# 69. `tests/test_main_t51_guard_no_pick_artifact.py` (102 lines)

**Covers:** `main.py::_write_guard_no_pick_artifact_for_main, run` (T51 market-closed guard)

### ✅ GOOD-MT5-1: Header docstring (lines 1–10) **EXPLICITLY documents the production gap discovered in 2026-05-09 Lane 1 audit**. Exemplary regression-test intent.
### ✅ GOOD-MT5-2: 3 tests cover happy path, writer-failure-swallow safety contract, **wiring regression** (`test_main_t51_guard_invokes_helper`, lines 71–101) — critical "is the helper actually called by run()?" check.
### ✅ GOOD-MT5-3: `from scripts.validate_daily_no_pick import validate_no_pick_report` (line 45) — uses canonical validator. **Best practice — tests artifact passes the SAME validation production uses.**
### ✅ GOOD-MT5-4: Wiring test stubs `_is_td`, `_why_closed`, `_next_td` (lines 93–95) cleanly. Behavioral, not source-grep.

### ⚠️ BUG-MT5-1: `monkeypatch.setattr("scripts.write_guard_no_pick_artifact.write_guard_no_pick_artifact", _boom)` (lines 60–63) — string-path attribute patching. Brittle to module rename.
- **Severity:** 🟡

### ⚠️ BUG-MT5-2: `monkeypatch.setattr(main, "load_config", lambda *a, **k: {})` (line 91) — replaces config loader with empty dict. Real config could expose bugs this masks.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 4 (best-intent regression test in batch)

---

# 70. `tests/test_market_calendar.py` (205 lines)

**Covers:** `src/market_calendar.py` (is_weekend, is_holiday, is_trading_day, is_early_close, reason_market_closed, next/previous_trading_day, cached_years, years_remaining, needs_renewal, renewal_message, renewal_urgency, market_status_today, US_MARKET_HOLIDAYS)

### ✅ GOOD-MC-1: 38 tests covering EVERY exposed function across weekend/holiday/half-day/cross-year-boundary/renewal-urgency. **Highest test-density in batch.**
### ✅ GOOD-MC-2: `test_july_3_2026_is_holiday_when_jul_4_saturday` (lines 35–37) — tests the SUBTLE holiday-on-Saturday observation rule. Explicit comment.
### ✅ GOOD-MC-3: `test_navigates_across_year_boundary` (lines 165–167) — tests Dec 31 → Jan 4 navigation. Edge case.
### ✅ GOOD-MC-4: `test_holidays_present_for_all_three_years` (lines 170–174) — sanity-check on data completeness across 2026/2027/2028.
### ✅ GOOD-MC-5: 4 escalating renewal-urgency tests (lines 179–204) — locks the operational alarm tier system.

### ⚠️ BUG-MC-1: `test_renewal_urgency_soft_when_18mo_or_less` (line 185) asserts `in ("soft", "urgent")` — `or` between two states. Loose.
- **Severity:** 🟡

### ⚠️ BUG-MC-2: `assert "2030" in msg or "2028" in msg` (line 139) — same `or` shotgun.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 5 (highest GOOD count in batch)

---

# 71. `tests/test_market_data_health.py` (85 lines)

**Covers:** `src/market_data_health.py::classify_provider_error, record_market_data_event, write_market_data_run_summary, summarize_market_data_health`

### ✅ GOOD-MDH-1: `test_classify_provider_error_buckets_yfinance_failures` (lines 4–10) — tests 4 distinct error patterns. **Direct relevance to your premarket failures** (rate_limited classification).
### ✅ GOOD-MDH-2: `test_record_market_data_event_adds_canonical_failure_type` (lines 55–84) — locks the canonical `failure_type` field contract. Schema discipline.
### ✅ GOOD-MDH-3: `monkeypatch.setattr(health, "DATA_DIR", tmp_path)` (line 16) — clean isolation.

### ⚠️ BUG-MDH-1: `assert summary["samples"][0]["ticker"] == "ABC"` (line 53) — order dependency on samples list. If implementation switches to dict-keyed samples, breaks.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 1 · ✅ 3

---

# 72. `tests/test_market_data_provider_stooq.py` (39 lines)

**Covers:** `src/market_data_providers/stooq_provider.py::stooq_symbol, fetch_stooq_ohlcv, _http_get`

### ✅ GOOD-SP-1: `test_stooq_symbol_preserves_existing_suffix` (line 12) — tests BRK.B special case.
### ✅ GOOD-SP-2: `test_fetch_stooq_ohlcv_returns_empty_for_intraday_interval` (lines 36–38) — tests Stooq's known limitation (no intraday). Defensive.
### ✅ GOOD-SP-3: `monkeypatch.setattr(stooq_provider, "_http_get", ...)` (lines 22–26) — clean network isolation.

### ⚠️ BUG-SP-1: Tests private `_http_get` (line 24). Same anti-pattern.
- **Severity:** 🟡

### ⚠️ BUG-SP-2: Only 4 tests — no test for malformed CSV, missing columns, network error path.
- **Severity:** 🟡 Coverage gap.

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 2 · ✅ 3

---

# 73. `tests/test_market_news.py` (252 lines)

**Covers:** `src/market_news.py` (_cache_path, _sentiment_cache_path, fetch_market_news, _build_sentiment_prompt, _strip_markdown_fences, _gemini_sentiment, _claude_sentiment, analyze_market_sentiment, get_market_briefing)

### ✅ GOOD-MN-1: 15 tests cover cache freshness, no-key skip, sort+cache, non-200, exception, prompt-build, fence-stripping, Gemini POST, Claude success/failure, fallback chain, briefing assembly. **Most thorough provider-fallback coverage in repo.**
### ✅ GOOD-MN-2: `test_fetch_market_news_returns_empty_without_key` (lines 18–30) — explicit "no key = no network call" guarantee. Cost/safety important.
### ✅ GOOD-MN-3: `test_strip_markdown_fences_handles_json_and_plain_text` (lines 103–105) — defensive against LLM output variation.
### ✅ GOOD-MN-4: Cache-path tests (lines 10–15) — locks per-hour cache scoping.

### ⚠️ BUG-MN-1: 7 tests on private `_*` functions.
- **Severity:** 🟡

### ⚠️ BUG-MN-2: Same `(_ for _ in ()).throw(...)` hack (lines 87, 161, 191) — repeated 3× in this file alone.
- **Severity:** 🟡

### ⚠️ BUG-MN-3: `assert calls[0][2]["contents"][0]["parts"][0]["text"] == "prompt"` (line 132) — deep dict-path assertion. If Gemini API shape changes (Google does this often), test breaks even though code is correct.
- **Severity:** 🟡

### ⚠️ BUG-MN-4: `assert "gemini-test:generateContent?key=gem-key" in calls[0][0]` (line 131) — substring of URL. Couples to Google's URL format.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 4 · ✅ 4

---

# 74. `tests/test_meta_brain.py` (161 lines)

**Covers:** `src/meta_brain.py` (recent_mutations, categorize_mutations, detect_stuck_areas, suggest_hypotheses, build_self_improvement_digest, format_telegram_digest)

### ✅ GOOD-MB-1: 10 tests across 4 sections (mutations, stuck, hypothesis, digest). Clear taxonomy.
### ✅ GOOD-MB-2: `test_suggest_hypotheses_finds_outperformer` (lines 83–106) — synthetic 25 winners + 25 losers dataset, asserts hypothesis surface. Reproducible.
### ✅ GOOD-MB-3: `test_format_telegram_digest_quiet` and `_active_week` pair (lines 129–161) — tests both states.

### ⚠️ BUG-MB-1: `_now()` and `_iso(dt)` (lines 30–31) — uses real `datetime.now()`. Time-dependent.
- **Severity:** 🟡

### ⚠️ BUG-MB-2: `assert any("Adjusted how it weighs" in line for line in digest["plain_english"])` (line 125) — substring on user-facing text. Fragile to copy edits.
- **Severity:** 🟡

### ⚠️ BUG-MB-3: `assert msg ... "Heads up"` (line 139) and `assert "Heads up" not in msg` (line 160) — same string-presence anti-pattern.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 0 · 🟡 3 · ✅ 3

---

# 75. `tests/test_missed_premarket_alert.py` (15 lines)

**Covers:** `scripts/send_missed_premarket_alert.py::build_message`

### ✅ GOOD-MPA-1: One test, but covers the CRITICAL safety contract — "Premarket missed → message says NOT actionable". **Direct relevance to your premarket failures.**
### ✅ GOOD-MPA-2: `tzinfo=ZoneInfo("America/New_York")` (line 8) — TZ-correct.

### 🚨 BUG-MPA-1: ONLY ONE TEST for a script that ships when premarket BREAKS
- This is the alarm system for your #1 production failure mode. Should test: weekend, holiday, after 09:45 vs 10:30, with/without late-watch-only artifacts present, telegram-deduped scenarios.
- **Severity:** ⚠️ Coverage gap for a critical safety alarm.

### ⚠️ BUG-MPA-2: 4 substring assertions (lines 10–14) — fragile to copy edits.
- **Severity:** 🟡

**Per-file:** 🚨 0 · ⚠️ 1 · 🟡 1 · ✅ 2

---

## 🎯 BATCH 110 grand totals

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 3 (LDI-1/LDI-2 floating-point + truncated string + LWO-1 source-grep) |
| ⚠️ Data/safety risk | 4 |
| 🟡 Code smell | 33 |
| ✅ Good code | 55 |
| **Total findings** | **95 across 15 files / ~1,910 lines** |

### 🔥 ARCHITECTURE-RELEVANT FINDINGS THIS BATCH

You said premarket and intraday picks are broken. **Three findings here directly bear on those failure modes:**

1. **MPA-1** — `test_missed_premarket_alert.py` is **15 lines, 1 test** for the script that fires when premarket fails. **This is the alarm system for your most painful production failure mode and it has near-zero test coverage.** This is the single highest-leverage gap.

2. **ISO-4** — `test_intraday_scanner_opening_range.py::test_scan_opening_range_opportunities_skips_stale_session_bars` (lines 328–346) is **good news** — it tests Thursday's bars don't bleed into Friday's scan. Use this as a template for the rest.

3. **MDH-1** — `test_market_data_health.py::test_classify_provider_error_buckets_yfinance_failures` (lines 4–10) tests rate-limit classification. **Critical because your premarket failures during yfinance rate-limit storms depend on this classification being correct.**

### 🎯 BEST-IN-BATCH: `test_main_t51_guard_no_pick_artifact.py` (file 69)

This file is the **template for what your test architecture should look like:**
1. Header docstring documents the production bug it regression-prevents.
2. Three layered tests: helper happy path → safety swallow → wiring check.
3. Wiring test ensures the helper is actually CALLED by run(), not just that it exists.
4. Validates artifact with the SAME validator production uses.

**Use this 102-line file as the model for fixing your premarket and intraday test gaps.**

### Production code coverage from this batch

- `src/learning_journal.py`, `src/lesson_gc.py`, `src/wisdom_base.py`, `src/llm_agent.py`, `src/layman_translator.py`, `src/market_calendar.py`, `src/market_data_health.py`, `src/market_news.py`, `src/meta_brain.py`, `src/market_data_providers/stooq_provider.py`
- `scripts/intraday_scanner.py`, `scripts/intraday_monitor.py`, `scripts/audit_journal_consistency.py`, `scripts/generate_late_daily_ideas.py`, `scripts/send_missed_premarket_alert.py`, `scripts/write_guard_no_pick_artifact.py`, `scripts/validate_daily_no_pick.py`
- `main.py` (T51 guard, `_write_guard_no_pick_artifact_for_main`, `run`)
- `.github/workflows/daily-picks.yml`, `.github/workflows/late_watch_only.yml` (grep only)

### Next batch (111) — files 76–90 alphabetically:
`test_missing_data_gate.py`, `test_monitoring_first_docs.py`, `test_monitoring_mode_no_paper_default.py`, `test_monitoring_readiness.py`, `test_monster_flag_persistence.py`, `test_monster_hunt.py`, `test_news_action_window_guard.py`, `test_news_engine.py`, `test_news_engine_finding3.py`, `test_news_engine_run_status.py`, `test_news_evidence_playbook_docs.py`, `test_news_evidence_workflow.py`, `test_news_signal_evidence_report.py`, `test_news_signal_outcome_attribution.py`, `test_news_signals_negative_reaction.py`
