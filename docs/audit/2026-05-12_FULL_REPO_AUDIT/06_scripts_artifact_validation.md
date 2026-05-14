# Audit Batch 3b — Scripts: Artifact + Validation Infrastructure (14 files)

**Date:** 2026-05-12
**Files (14):** build_candidate_lifecycle, build_daily_intelligence_brief, build_data_readiness_report, build_stock_stats, build_theme_pick_bridge, build_watch_only_outcomes, check_daily_artifact_completeness, check_enforcement_readiness, dry_run_official_no_pick, dry_run_official_premarket_pick, validate_daily_no_pick, validate_official_pick_artifacts, write_guard_no_pick_artifact, write_official_workflow_summary

**Total:** ~2,200 lines of Python

**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

## High-level summary in plain English

This batch implements the **Lane 1 official-decision discipline**: every morning, your system either produces a "pick" or a "no-pick", and BOTH outcomes must produce machine-verifiable artifacts. These 14 files are:

1. The artifact producers (build_*, write_*) — generate Markdown + JSON reports
2. The validators (validate_*, check_*) — confirm artifacts conform to a contract
3. The dry-runs (dry_run_*) — prove the artifact path works without calling real APIs
4. The completeness checker — confirms ALL expected daily artifacts were written

This is the most architecturally mature part of your repo. The contract pattern is well-developed.

Two families inside this batch:

Family A — Lane 1 Decision Contract (8 files):
- dry_run_official_premarket_pick.py, dry_run_official_no_pick.py
- validate_official_pick_artifacts.py, validate_daily_no_pick.py
- write_guard_no_pick_artifact.py, write_official_workflow_summary.py

Family B — Observe-Only Reports (6 files):
- build_data_readiness_report.py, build_candidate_lifecycle.py
- build_theme_pick_bridge.py, build_daily_intelligence_brief.py
- build_watch_only_outcomes.py, check_daily_artifact_completeness.py

Plus the misfits:
- build_stock_stats.py (data warming script)
- check_enforcement_readiness.py (separate gate-readiness audit)

---

## CROSS-CUTTING FINDINGS

### ✅ X-AV1: Excellent docstring discipline — safety constraints explicit
Every Family A file declares safety constraints in the docstring:
- dry_run_official_no_pick.py lines 9-14: "no live data calls / no real picks / no alerts / no paper-live trading / writes only to isolated dry-run directory"
- validate_daily_no_pick.py lines 6-8: "does not generate picks, enable paper trading, enable live trading, or send alerts"

Plain English: Each file SAYS what it WON'T do. If someone refactors and accidentally adds a Telegram call, the docstring lies — instant flag during review.
Severity: ✅ Propagate this to every script.

### ✅ X-AV2: Uniform safety_flags / SAFETY dict pattern
Every Family B builder embeds a SAFETY dict (e.g., build_candidate_lifecycle.py lines 25-32) with keys: observe_only=True, production_scoring_effect=False, official_score_boost_enabled=False, paper_trading_enabled=False, live_trading_enabled=False, buy_instructions_enabled=False. And every artifact INCLUDES it in output. Downstream consumers can trust the flags.
Severity: ✅ Exemplary defensive contract.

### ✅ X-AV3: Path templates centralized as helper functions
Each builder has candidate_lifecycle_json_path(), theme_pick_bridge_markdown_path(), etc. (e.g., lines 408-413 in build_candidate_lifecycle.py).
Plain English: Path conventions live in ONE place per file. If you ever rename candidate_lifecycle_YYYY-MM-DD.json to cand_lifecycle_YYYY-MM-DD.json, only one function changes.
Severity: ✅ Worth replicating.

### ⚠️ X-AV4: load_json / load_jsonl defined IDENTICALLY in 6+ files
build_candidate_lifecycle.py:46-69, build_daily_intelligence_brief.py:40-63, build_data_readiness_report.py:44-67, build_theme_pick_bridge.py:35-58, build_watch_only_outcomes.py:64-80, check_daily_artifact_completeness.py:108-130.

Same shape — load_json returns a "_parse_error" dict on failure, default if missing. load_jsonl also duplicated.

Plain English: Same code copy-pasted 6 times.
Why a problem: Bug fix to one (e.g., adding encoding parameter) won't propagate to others.
Fix: Extract to src/artifact_io.py. Import everywhere.
Severity: ⚠️ DRY violation × 6.

### ⚠️ X-AV5: Same _safe_float / _to_float helper duplicated
- build_watch_only_outcomes.py:41-47 (_safe_float)
- check_enforcement_readiness.py:50-54 (_to_float)
- audit_earnings_fill_rate.py (from Batch 3a)
Different default behaviors, different names.
Severity: ⚠️ DRY violation; behavior drift risk.

### 🚨 X-AV6: Family B builders have NO atomic write
- build_candidate_lifecycle.py:478-479: json_path.write_text(...), md_path.write_text(...) — direct overwrite.
- Same in build_daily_intelligence_brief.py:520-521, build_data_readiness_report.py:467-468, build_theme_pick_bridge.py:406-409, build_watch_only_outcomes.py:573-577, check_daily_artifact_completeness.py:335-336.
Plain English: If interrupted mid-write, downstream consumers (e.g., daily_intelligence_brief reads candidate_lifecycle.json) see corrupted JSON.
Severity: ⚠️ Inconsistent with backfills (Batch 3a) which DO atomic-write.

### ⚠️ X-AV7: from . import vs sys.path.insert inconsistency
Almost every script has sys.path.insert(0, str(Path(__file__).resolve().parent.parent)) then "from src.X import Y". Three patterns: parents[1], parent.parent, Path(__file__).resolve().parents[1]. All equivalent but inconsistent style.
Severity: 🟡 Style.

### 🟡 X-AV8: default=str and sort_keys=True for json.dumps inconsistent
- build_* files use sort_keys=True (good — deterministic output, helps git diff).
- check_enforcement_readiness.py:248 uses default=str but not sort_keys.
Severity: 🟡 Style; sort_keys=True is preferred.

### 🟡 X-AV9: Markdown writers do f.write_text(format_markdown(report) + "\n") — fine but no markdown linting
No automated check that the markdown is valid. If a typo in f-string produces malformed table syntax, it renders broken on GitHub but no test fails.
Severity: 🟡 Observability of report quality.

### ⚠️ X-AV10: Date defaults: UTC vs ET inconsistency
- build_candidate_lifecycle.py:485: datetime.now(timezone.utc).strftime("%Y-%m-%d") — UTC date
- dry_run_official_premarket_pick.py:48: datetime.now(ET).strftime("%Y-%m-%d") — ET date
- validate_official_pick_artifacts.py:32: ET date
- build_data_readiness_report.py:474: UTC date

Plain English: Some builders default to UTC date, others to ET date. At 22:00 UTC = 18:00 ET, these are SAME day. At 02:00 UTC = 22:00 ET (previous day), they DIFFER by one.
Why a problem: build_candidate_lifecycle.py defaults to UTC date but build_data_readiness_report.py might be reading the wrong-dated artifacts.
Fix: Standardize on ET (the market's clock) for daily artifacts. Defensible to use UTC for nightly/weekly things.
Severity: ⚠️ Off-by-one-day bug latent.

---

## PER-FILE FINDINGS

### 1. build_candidate_lifecycle.py (508 lines)

What it does: Reconstructs every candidate's lifecycle for a date — selected/blocked/filtered/watched/missing — from multiple input artifacts. Outputs JSON + Markdown.

✅ GOOD-CL1: STATE_PRIORITY ordering (lines 34-43) — clear priority logic for which state "wins" when a ticker appears in multiple buckets.
✅ GOOD-CL2: Distinguishes "diagnostics_unavailable" vs "data_fetch_failed" vs "missing_from_universe" (lines 308-345) — granular failure attribution.
✅ GOOD-CL3: Excellent SAFETY dict (lines 25-32) and safety_flags array (397-404) — defensive contract.
✅ GOOD-CL4: _finalize_reason (lines 238-263) — human-readable explanations per state.

⚠️ BUG-CL1: Line 50 return json.loads(path.read_text()) — no encoding specified. Default is utf-8 on most systems but Windows defaults to cp1252. If artifact contains non-ASCII (theme names, company names with accents), can fail on Windows.
- Fix: path.read_text(encoding="utf-8").
- Severity: 🟡

🚨 BUG-CL2: Line 60 for line in path.read_text().splitlines() — reads ENTIRE JSONL into memory. For large files (e.g., intraday_momentum_observations_*.jsonl at high freq), this OOMs.
- Plain English: 50MB JSONL becomes a 50MB string then a list of millions of strings before parsing.
- Fix: stream line-by-line: for line in path.open(): ...
- Severity: ⚠️ Scaling cliff.

⚠️ BUG-CL3: Line 234 if STATE_PRIORITY.get(state, 0) >= STATE_PRIORITY.get(row["lifecycle_state"], 0):
- Plain English: Update lifecycle_state to new state IF new priority >= existing. The >= (not >) means later events of same priority overwrite earlier — but the row already has earlier event in row["events"]. The conflict-resolution comment is missing.
- Severity: 🟡 Documentation.

⚠️ BUG-CL4: Line 67 "_parse_error": str(exc) — silent. Caller may see a dict with _parse_error key and proceed as if it's normal data. Lines 277-279 do check if not isinstance(readiness, dict) but don't check for _parse_error key.
- Fix: explicit check if "_parse_error" in readiness: log_warning(...).
- Severity: ⚠️ Silent data corruption.

🟡 BUG-CL5: Line 348 row["themes"] = sorted(row.get("themes") or []) — alphabetic sort. If theme names are emoji-prefixed or non-ASCII, sort order is locale-dependent.
- Severity: 🟡

🟡 BUG-CL6: No --strict mode — can't gate CI on this.

### 2. build_daily_intelligence_brief.py (543 lines)

What it does: Synthesizes 6 other artifact files into a "founder-readable" operating report. Reads candidate_lifecycle, data_readiness, theme_discovery, theme_pick_bridge, no_pick_report, artifact_completeness. Outputs JSON + Markdown.

✅ GOOD-DB1: classify_daily_operating_status (lines 232-248) — clean decision tree for HUMAN status ("incomplete_pipeline" / "data_failed_or_degraded" / etc.)
✅ GOOD-DB2: _monitoring_priorities (lines 265-318) — generates actionable priorities for tomorrow.
✅ GOOD-DB3: Imports src.scoring_safety for safety status (lines 221-229) — confirms scoring boosts haven't accidentally been re-enabled.

🚨 BUG-DB1: Line 222-229 _scoring_safety_summary wraps the import in try/except and returns {"status": "failed", "error": str(exc)} on failure.
- Plain English: If src.scoring_safety import fails for ANY reason (typo in code, missing dep), the brief silently reports "scoring_safety failed" and proceeds.
- Why a problem: This is the ONE check that verifies legacy boosts are disabled. Silent failure here means you'd never know boosts came back on.
- Fix: log loudly, fail the report generation in strict mode, OR include the actual safety state directly (not via import).
- Severity: 🚨 Silent safety check.

🚨 BUG-DB2: Line 333-335 — fetches official_pick_count from data_readiness.json. If that file is missing/corrupted, defaults to 0, which triggers wrong classification.
- Plain English: missing input → assumes zero picks → reports "productive_no_official_picks" wrongly.
- Fix: when data_readiness is missing, set status = incomplete_pipeline, do NOT compute classifications from defaults.
- Severity: 🚨 Bad-default cascade.

⚠️ BUG-DB3: Line 343 _top_themes(theme_discovery) is called even if theme_discovery returned {} (file missing). Returns empty list — OK, but no signal that theme_discovery was MISSING vs EMPTY.
- Severity: ⚠️ Loss of "absent vs empty" distinction.

⚠️ BUG-DB4: Line 162-163 builds list of tickers, then later turned into a set (line 187). Wasteful work building a list when a set is the target.
- Severity: 🟡

⚠️ BUG-DB5: Line 365 data_readiness.get("official_pick_tickers", []) — same issue as BUG-DB2; relies on dependent artifact.
- Severity: ⚠️ Cascade failure.

### 3. build_data_readiness_report.py (490 lines)

What it does: The KEYSTONE classification artifact. Reads run_status, no_pick_report, rejections, watch-only lanes, theme_bridge, picks_log. Classifies the day as one of 6 outcomes (strategy_driven_no_qualified_candidates / data_provider_failure / pipeline_incomplete / diagnostics_missing / market_closed / mixed_or_uncertain).

✅ GOOD-DR1: Comprehensive classify_no_pick decision tree (lines 161-191) — handles ambiguity gracefully.
✅ GOOD-DR2: _contains_provider_failure_text heuristic (lines 93-111) — text-based fallback when structured data isn't available. Good defensive design.
✅ GOOD-DR3: Excellent _warnings (lines 208-236) — surfaces 8 distinct conditions independently.

⚠️ BUG-DR1: Line 94 text = json.dumps(obj, sort_keys=True, default=str).lower() — serializes the entire object, then substring-searches for tokens.
- Plain English: Re-serializing every input artifact to do a substring check is slow for large objects.
- More importantly: the tokens list (lines 96-110) is hardcoded English. If you ever localize error messages, fails silently.
- Severity: 🟡 Fragile heuristic.

🚨 BUG-DR2: Line 269-276 candidate_diagnostics_available logic checks rejection_path.exists() and bool(rejection_obj) and not isinstance(rejection_obj, list).
Plain English: "Available" if file exists AND has content AND not a list AND (either flag set OR any non-zero count OR has 'diagnostics' key).
Why suspect: The _parse_error payload returned by load_json IS a dict (passes not isinstance(..., list)) and contains _parse_error key — so this incorrectly reports diagnostics_available=True for corrupted files.
Severity: 🚨 False positive on corrupted artifact.

⚠️ BUG-DR3: Line 88-90 _latest_jsonl_record returns LAST record. But JSONL run-status files contain multiple events. The "latest" might be a routine status, missing the actual error event from earlier.
- Severity: ⚠️ Misleading sampling.

🟡 BUG-DR4: Line 35 NO_PICK_CLASSIFICATIONS set defined but never used in this file (only referenced for documentation). Dead-ish.

### 4. build_stock_stats.py (103 lines)

What it does: Fetches yfinance data for top 20 or top 100 tickers, computes per-stock stats (ATR, returns, volatility), saves to disk.

🚨 BUG-SS1: Line 20-58 TWO hardcoded ticker lists, with overlap. TOP_TICKERS (20) and TOP_100_TICKERS (100). Maintenance nightmare.
- Plain English: Adding NVDA to the list means updating BOTH places.
- Already drifting: TOP_TICKERS has RMBS, MRVL, NFLX, JPM mixed with mega-cap; TOP_100 includes ETFs SPY, QQQ, IWM, DIA (not stocks).
- Fix: single source. Universe should come from config or a discovery query.
- Severity: 🚨 Drift waiting to happen.

🚨 BUG-SS2: Line 94 time.sleep(0.5) — "be polite to yfinance" — but yfinance's actual rate limit isn't documented and isn't 2 req/sec. May be too fast (rate-limited) or too slow (~50 sec for 100 tickers).
- Severity: 🟡 Cargo-cult delay.

⚠️ BUG-SS3: Line 81 if profile is None: print("❌ FETCH FAILED"); failed.append(ticker); continue — silently appends to failed list. No retry, no Telegram alert. If 50 of 100 tickers fail, you just see ❌s scroll by.
- Severity: ⚠️ Silent partial failure.

🟡 BUG-SS4: Line 102 main() doesn't return exit code. If failed is non-empty, script exits 0 (success).
- Severity: 🟡

🟡 BUG-SS5: No docstring beyond top — no --help describes the --top100 / --all distinction.

### 5. build_theme_pick_bridge.py (437 lines)

What it does: Compares discovered themes against picks/rejections/watch-only to find theme-coverage gaps.

✅ GOOD-TB1: Sophisticated _gap_reasons (lines 174-201) — multi-cause attribution.
✅ GOOD-TB2: Coverage ratio (line 280): (len(leaders) - len(missing)) / len(leaders) — clean metric.

⚠️ BUG-TB1: Line 199 if leader_count and not reasons: reasons.append("no_bridge_gap_detected")
- Plain English: If there ARE leaders but no reasons accumulated, add "no_bridge_gap_detected". But if leader_count == 0, no entry added.
- Why a problem: empty-theme cases get NO reason. Downstream code may key on reasons and miss empty themes.
- Severity: 🟡 Edge case.

⚠️ BUG-TB2: Line 148 def _matches(theme_tickers: set[str], rows: Iterable[dict]) -> list[dict]:
- Iterates rows looking for ticker in theme_tickers. For each theme. With N themes × M rows = O(NM).
- For 12 themes × 1000 candidates = 12,000 comparisons. Fine. For 100 themes × 100k = problematic.
- Severity: 🟡 Scaling at extreme sizes.

🟡 BUG-TB3: Line 220 rejection_artifact_exists = rejection_path.exists() — used downstream but doesn't check whether JSON is PARSEABLE. Same bug class as BUG-DR2.

### 6. build_watch_only_outcomes.py (604 lines)

What it does: Evaluates watch-only ideas (late daily + opening range) for "did TP/SL hit, what was the quality, was breakout sustained?" Outputs JSONL + Markdown.

✅ GOOD-WO1: Best-in-batch safety preamble (lines 84-95): every outcome includes mode=monitoring_only, watch_only=True, official_pick_stats_mutated=False, etc.
✅ GOOD-WO2: evaluate_opening_range_quality (lines 198-346) — sophisticated breakout-quality scoring (sustained vs false vs overextended) with explicit flags.
✅ GOOD-WO3: Explicit data_sufficiency_status (line 120) distinguishes "range_only_no_intraday_sequence" — admits what it CAN'T determine.
✅ GOOD-WO4: Line 147-152: when both TP and SL hit same day from range-only data, status is "tp_and_sl_inside_range_order_unknown" — honest about uncertainty.

⚠️ BUG-WO1: Line 29-32 imports private functions from scripts.backtest_opening_range_observations (evaluate_observation_outcome, load_bars_for_observation).
- Plain English: This file's correctness depends on another script's internal functions.
- Why a problem: Same private-function-import coupling as BUG-BA1/BS1 in Batch 3a. If backtest_opening_range_observations is refactored, this breaks silently.
- Severity: ⚠️ Hidden coupling.

🚨 BUG-WO2: Line 256-260 overextended logic checks breakout_pct >= 2.0 OR breakout_pct >= or_width_pct.
- Plain English: Overextended IF breakout >= 2% OR (breakout >= range width).
- Why a problem: "2%" is a magic number with no explanation. Why 2 and not 1.5 or 3?
- Severity: 🟡 Magic threshold.

🟡 BUG-WO3: Line 295 avg_or_bar_volume = or_volume / 6.0 — comment says "Opening range is normally six 5-minute bars."
- Plain English: hardcoded "6 bars" assumption. If opening-range definition changes (e.g., 30-min vs 30-min × 5min bars), this breaks.
- Severity: 🟡

🚨 BUG-WO4: Line 307-322 score arithmetic: score = 50 then +20 / -25 / +20 / -20 / +5 / -5 / -10 based on flags, clamped 0-100.
- Plain English: Hardcoded score weights with no documented justification.
- Why a problem: This is exactly the kind of "magic ladder" that ages badly. After 6 months you won't remember why "confirmed volume = +5 but TP = +20." Brain-learning targets won't know what these mean either.
- Fix: move weights to config/watch_only_scoring.json, document.
- Severity: 🚨 Brain-irrelevant heuristic.

🟡 BUG-WO5: Line 573 jsonl_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in outcomes), encoding="utf-8") — builds entire JSONL in memory before writing.
- Fine for current sizes; bad for large batches.
- Severity: 🟡

### 7. check_daily_artifact_completeness.py (358 lines)

What it does: For each expected daily artifact (10 of them, defined in ARTIFACTS list), check: exists? parseable? row count > 0? Severity?

✅ GOOD-CC1: Excellent ARTIFACTS manifest (lines 34-105) — declarative spec of what's expected. Easy to add/remove.
✅ GOOD-CC2: Multi-level severity logic (lines 201-210): critical / warning / ok based on existence × required.
✅ GOOD-CC3: Distinguishes present_parse_error vs present_empty vs missing vs present.

⚠️ BUG-CC1: Line 147 official_pick_count falls back to reading picks_log.csv if data_readiness.json missing.
- Plain English: Two sources of truth for "how many picks today?" — data_readiness.json AND picks_log.csv.
- Why a problem: if they disagree, downstream classification is wrong.
- Severity: ⚠️ Dual source.

🟡 BUG-CC2: Line 116-130 inspect_jsonl reads entire file to count rows. For large JSONL files, wasteful (could just count newlines).
- Severity: 🟡

🟡 BUG-CC3: No --strict flag — CI can read the report but can't gate on it directly. (Would need a wrapper.)

🟡 BUG-CC4: Line 34 ARTIFACTS list is hardcoded. New observability artifacts (e.g., watch_only_outcomes_*.jsonl) need to be added manually. Drift-prone — Batch 3b created watch_only_outcomes_*.jsonl but it's NOT in this list.
- Actually checking: watch_only_outcomes_*.jsonl is NOT in ARTIFACTS. So this completeness check doesn't validate that file's presence.
- Severity: ⚠️ Coverage gap.

### 8. check_enforcement_readiness.py (256 lines)

What it does: Scores 3 OBSERVE-mode safety gates (SMELL_ENFORCE, BRAIN_ENFORCE_EV, AUTO_PAUSE_ENABLED) for readiness to flip ON. Plain-English: "do we have enough data to trust this gate?"

✅ GOOD-CE1: Excellent docstring (lines 1-23) explaining the problem and the data-driven approach.
✅ GOOD-CE2: Per-gate threshold defined inline with rationale (e.g., n>=30 picks-with-smell AND smell-FP-rate < 20%).
✅ GOOD-CE3: Pearson correlation (lines 148-158) computed inline — no scipy dep needed.

🚨 BUG-CE1: Line 38-40 graceful import fallback: if "from src.data_quality import filter_to_quality" fails, define filter_to_quality(rows): return rows.
- Plain English: If filter_to_quality can't be imported, fall back to no-op (return all rows).
- Why a problem: "Post-floor" data is the entire point of this audit. If filter_to_quality is broken, audit silently uses ALL rows (including pre-floor garbage) and reports false readiness.
- Fix: fail loudly. Module SHOULD be importable.
- Severity: 🚨 Silent corruption of audit signal.

⚠️ BUG-CE2: Line 87 if not rows or not any("smell_codes" in r for r in rows): — checks if ANY row HAS a smell_codes key.
- Plain English: If even ONE row has smell_codes column, audit proceeds.
- Why a problem: This is "schema present?" detection. But the schema column may exist with all empty values. Better check: at least N rows have NON-EMPTY smell_codes.
- Already partially handled by line 99 filter, but the early-exit on line 88 is too eager.
- Severity: 🟡

🚨 BUG-CE3: Line 178 def check_auto_pause(rows): ... bad_groups = [...] if wr < 0.30 ...
- Plain English: "Auto-pause is ready if there's a tag-group with WR < 30%."
- Why a problem: Optimizing FOR finding bad groups means the gate becomes auto-ready as soon as any segment performs poorly — even due to sampling noise. WR=0/5=0% with n=5 is a "ready" trigger.
- Fix: add statistical significance test (e.g., Wilson lower bound).
- Severity: 🚨 False-positive readiness on small n.

⚠️ BUG-CE4: Line 57-62 yet another CLOSED_STATUSES definition — see Batch 3a X-AB5.
- Severity: ⚠️ Schema drift × 6 files now.

🟡 BUG-CE5: Line 84 threshold_n = 30 and max_fp_rate = 0.20 are hardcoded inside the function. Other gates have their thresholds documented in docstring but not single-sourced.

### 9. dry_run_official_no_pick.py (317 lines)

What it does: Builds SYNTHETIC no-pick fixtures for every allowed OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES. Validates each through validate_no_pick_report. Used by audit_lane1_production_readiness AND by daily-picks workflow.

✅ GOOD-DN1: Cause-by-cause customization (lines 113-159) — different pipeline + diagnostics shapes per cause. Realistic test data.
✅ GOOD-DN2: Per-cause friendly summary (lines 70-84) — humanizes synthetic data.
✅ GOOD-DN3: keep + --output-dir semantics consistent with sibling dry-run.

⚠️ BUG-DN1: Line 284-288 same "if args.output_dir: keep = True" silent override as BUG-AL5.

🟡 BUG-DN2: Lines 71-84 summaries dict has 11 entries but OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES may not have exactly these. If a new cause is added to the contract, this dict needs updating.
- Fix: assert that summaries keys == ALLOWED_PRIMARY_CAUSES at module load.
- Severity: ⚠️ Manifest drift.

⚠️ BUG-DN3: Line 165 raise ValueError(f"unsupported no-pick cause: {cause}") — raised but run_dry_run doesn't catch and convert to validation_errors. Crashes the dry-run with stack trace instead of returning structured failure.
- Severity: 🟡

### 10. dry_run_official_premarket_pick.py (312 lines)

What it does: Full pipeline dry-run for one synthetic pick. Exercises: candidate_diagnostics → portfolio_risk_gate → missing_data_gate → write_official_pick_artifacts → validate_artifacts → validate_official_pick. End-to-end test of the production path.

✅ GOOD-DP1: Calls SAME production code paths as real picks (imports from src.*). Validates the full chain.
✅ GOOD-DP2: build_candidate_diagnostics is called TWICE (lines 159-171 and 191-209) — once before risk/missing-data gate, once after — to test the layered diagnostics shape.
✅ GOOD-DP3: Line 178-179 fails LOUDLY if synthetic candidate gets blocked unexpectedly (raise RuntimeError).

⚠️ BUG-DP1: Line 159-171 calls build_candidate_diagnostics first with selected_picks=[candidate], but then re-calls (line 191) with selected_picks=complete (which is the result of missing_data_gate). Two diagnostics built, only second is saved to file.
- Plain English: minor wasted work + slightly confusing.
- Severity: 🟡

⚠️ BUG-DP2: Line 213 _write_minimal_csv writes a 12-field CSV but production picks_log.csv has many more columns. Validators (line 229 validate_artifacts) read this minimal CSV.
- Plain English: dry-run CSV ≠ production CSV schema.
- Why a problem: passes contract validation but doesn't exercise full schema. If you add a new production column, validator may pass on minimal CSV but fail on real one.
- Severity: ⚠️ Schema-mismatch in fixture.

🟡 BUG-DP3: Line 220-227 hardcoded synthetic context: data_readiness_status="ready_dry_run", provider_status="healthy_dry_run", market_session_status="premarket_dry_run".
These status values are NEVER produced by real production. If contract validation is strict on these values, the dry-run might pass but real run fail.
- Severity: 🟡

### 11. validate_daily_no_pick.py (101 lines)

What it does: Loads daily_picks_no_pick_report_YYYY-MM-DD.json, validates against contract, prints errors. Exit code 1 on any failure.

✅ GOOD-VN1: Tightest file in batch. Single responsibility, clear error reporting.
✅ GOOD-VN2: Belt-and-suspenders: contract validation PLUS explicit checks (paper_trading=false, live_trading=false, decision=official_no_pick, final_pick_count=0). Defense in depth.
✅ GOOD-VN3: list(dict.fromkeys(errors)) (line 65) — dedupes errors while preserving order.

🟡 BUG-VN1: Line 44 return {"_parse_error": str(exc)}, path — same pattern as builders. Caller does check for _parse_error (line 79) — OK here, but inconsistent with other consumers.

🟡 BUG-VN2: No --data-dir validation — if user passes nonexistent dir, error is "missing file" not "bad dir."

### 12. validate_official_pick_artifacts.py (163 lines)

What it does: Validates ALL official pick artifacts for a date. Checks counts match picks_log.csv. Checks contract per artifact. Checks summary artifact agrees with count.

✅ GOOD-VO1: Counts BOTH directions: too few artifacts (line 82) AND too many (line 84). Catches both kinds of drift.
✅ GOOD-VO2: Duplicate ticker detection (line 101-104).
✅ GOOD-VO3: Summary artifact cross-checked against actual artifact count (lines 114-128).

🚨 BUG-VO1: Line 47-57 _count_csv_rows_for_date uses if line.startswith(f"{date_str},"): count += 1.
- Plain English: Counts CSV rows where line starts with date_str followed by comma.
- Why a problem: Assumes pick_date is the FIRST column. If column order is rearranged (e.g., ticker first), validation silently returns 0.
- Fix: use csv.DictReader and check row["pick_date"] == date_str.
- Severity: 🚨 Brittle parsing on production CSV.

⚠️ BUG-VO2: Line 74-77: returns an "error" when zero picks were expected. But callers may want "0 picks is valid no-pick day" semantics.
- Actually checking call site in daily-picks.yml: this validator IS called only when picks > 0 expected. So error is appropriate guard.
- Severity: 📝 OK behavior; doc could be clearer.

🟡 BUG-VO3: Line 116 if official_count != len(paths) — compares to artifact file count. But summary says "official_pick_count" might mean "logged picks" not "artifacts written." Disambiguate.

### 13. write_guard_no_pick_artifact.py (256 lines)

What it does: Writes no-pick artifacts BEFORE main.py runs, when workflow guard skips (market closed, window missed). Validates self-produced artifact against contract.

✅ GOOD-WG1: Self-validates via validate_no_pick_report(payload) (line 184) — refuses to write invalid artifact. Belt-and-suspenders.
✅ GOOD-WG2: _trace_ids (lines 63-73) generates deterministic decision_id + artifact_id for traceability.
✅ GOOD-WG3: Restricted to 2 specific causes (lines 48-51 SUPPORTED_GUARD_CAUSES). Defensive; prevents misuse.
✅ GOOD-WG4: argparse.choices=sorted(SUPPORTED_GUARD_CAUSES) (line 227) — CLI rejects bad causes at parse-time.

🟡 BUG-WG1: Line 67 short_sha = str(commit_sha or "local")[:12] — when running outside GitHub Actions, commit_sha is "local". Two simultaneous local runs at same time get IDENTICAL decision_id. Should add nanoseconds or PID.
- Severity: 🟡 Local collision (edge case).

🟡 BUG-WG2: Line 87-94 _default_reason for NO_PICK_MARKET_CLOSED — calls next_trading_day(date_str).isoformat() inside try/except, returns "unknown" on error. Silent fallback hides calendar bug.
- Severity: 🟡

### 14. write_official_workflow_summary.py (273 lines)

What it does: Writes Markdown to GitHub Step Summary at end of workflow. Includes both dry-run results AND production artifact summaries.

✅ GOOD-WS1: Reads from /tmp/lane1-*-dry-run dirs to surface dry-run pass/fail. Good observability.
✅ GOOD-WS2: Markdown tables (lines 69-83, 203-211) render well in GitHub UI.
✅ GOOD-WS3: Includes workflow_run_url + commit_url (lines 232-237) — clickable observability.

⚠️ BUG-WS1: Line 33-38 _load_json returns {} on failure. Then if not payload (line 60, 98) — sections silently show "not found." But {} (parse error) and missing file are different! Parse error means artifact was generated but corrupted — different action needed.
- Fix: distinguish parse_error from missing.
- Severity: ⚠️ Lost diagnostic distinction.

🟡 BUG-WS2: Line 165 f"- Result: **passed**" — hardcoded "passed" without verifying. If dry-run produced summary but content indicates failures, this still says "passed."
- Fix: check summary.get("validation_errors") == [] first.
- Severity: ⚠️ False reassurance.

---

## Summary of Batch 3b (14 files)

### By severity
| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 12 |
| ⚠️ Data/safety risk | 22 |
| 🟡 Code smell | 23 |
| 📝 Doc-only | 2 |
| ✅ Good code | 32 |
| Total | 91 findings |

### Top 10 things to fix in this batch (in order)

| # | Bug | Why first | Fix difficulty |
|---|---|---|---|
| 1 | BUG-DB1 (scoring_safety silent failure) | Hides the ONE safety check that verifies legacy boosts disabled | Easy: log + fail-loud |
| 2 | BUG-VO1 (CSV row count assumes column order) | Validation silently returns 0 if CSV reordered | Easy: use DictReader |
| 3 | BUG-DR2 (candidate_diagnostics_available false positive) | False "ready" status on corrupted artifacts | Medium: check _parse_error key |
| 4 | BUG-DB2 (data_readiness missing → wrong classification) | Cascade failure of operating status | Easy: fail-closed default |
| 5 | BUG-CE1 (graceful import fallback to no-op) | Audit silently uses pre-floor data; reports false readiness | Easy: remove the fallback |
| 6 | BUG-CE3 (auto-pause readiness on small-n bad group) | Gate flips ON due to sampling noise | Medium: add Wilson lower bound |
| 7 | BUG-WO4 (magic score weights hardcoded) | Brain-irrelevant heuristic ages badly | Medium: move to config |
| 8 | BUG-SS1 (two hardcoded ticker lists) | Drift-prone maintenance | Medium: single config source |
| 9 | X-AV6 (no atomic write in Family B builders) | Mid-write corruption breaks downstream readers | Easy: copy pattern from Batch 3a |
| 10 | X-AV4 (load_json/load_jsonl duplicated ×6) | DRY violation; fix won't propagate | Easy: extract to src/artifact_io.py |

### What this batch tells us about the project

- Lane 1 official-decision discipline is genuinely strong. The contract pattern, validators, dry-runs, and guard-no-pick paths are well-thought-out and defensive.
- The observe-only family (Family B) is well-designed but mechanically weaker. No atomic write, duplicated helpers, lost "parse_error vs missing" distinction.
- The cascade-failure risk is real. daily_intelligence_brief reads data_readiness, which reads other artifacts. If any LINK silently fails (e.g., BUG-DR2, BUG-DB2), the WHOLE chain reports wrong status. One missing artifact ⇒ wrong "operating status" ⇒ wrong "tomorrow priorities" ⇒ wrong manual response.
- check_enforcement_readiness.py is a critical audit but has 3 silent-failure modes. It's the gate-flip gate. If it lies (e.g., BUG-CE1, BUG-CE3), you flip on enforcement based on bad data. Triple-check this file.
- write_official_workflow_summary.py says "passed" too readily. This is the thing your eyes scan on every workflow run. False-reassurance bias.
- Atomic-write pattern from Batch 3a should propagate. Five Family B builders need it.

### Glossary additions

| Term | Plain English |
|---|---|
| Contract validation | A function that takes a JSON object and checks it has all required fields with right types. Like a customs form. |
| Decision artifact | A JSON file that records what the system decided today and WHY. Used for audit + replay. |
| Dry-run | Run the same code paths as production but with fake inputs, no API calls, no real artifacts. |
| Belt-and-suspenders | Two independent checks that BOTH must pass. Defense in depth. |
| Cascade failure | Error in one component silently propagates as defaults into downstream components, producing wrong-but-confident output. |
| Wilson lower bound | A statistical method to say "I'm 95% confident this proportion is at least X." Better than naive average for small n. |

---

End of Batch 3b.

Cumulative findings across batches 1a + 1b + 2a + 2b + 3a + 3b:
- Show-stoppers: 77
- Data/safety risks: 132
- Code smells: 111
- Doc-only: 11
- Good code: 124
- Total: 455 findings across 53 files (~16,200 lines)

Next: Batch 3c — Scripts: send_telegram + send_layman_* + send_*_telegram + Telegram infrastructure (~15 files, the user-facing channel).
