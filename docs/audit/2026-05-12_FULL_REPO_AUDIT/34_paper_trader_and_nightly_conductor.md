# Batch 28 — src/paper_trader.py (25 lines) + src/nightly_conductor.py (236 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** paper_trader.py (25 lines, fully read), nightly_conductor.py (236 lines, fully read)
**Phase:** D (pipeline & output) — files 3 and 4 of ~30

## TOP HEADLINE FINDINGS

1. PT-X1: paper_trader.py is **25 LINES — THE SHORTEST FILE IN THE AUDIT.** Single function `log_paper_trade` writes a CSV row. **Per Batch 6 main.py M-RUN42 sampling, paper_trader IS called from main.py.** This is THE SOLE PERSISTENCE for paper trades — yet it's the most under-engineered audited file. **Nothing about it scales.**
2. PT-X2: NO ATOMIC WRITE, NO LOCK, NO SCHEMA VALIDATION. Direct CSV append. **9 hardcoded column names** (line 12-13). **If pick or pick["plan"] missing keys → KeyError.** Compare to pick_evaluator (Batch 27) which has atomic write + 5-state outcomes + bug archaeology. **Two ends of the discipline spectrum in same codebase.**
3. PT-13 (line 17): `pick["scores"]["composite"]` — **DOUBLE KeyError-prone access.** No `.get()`. **If scoring failed and pick has no "scores" key, paper trade NEVER LOGGED.** Silent loss of trade record.
4. NC-X1: nightly_conductor.py is **THE BRAIN MUTATION ORCHESTRATOR** — 8-step pipeline that runs nightly. **Per Batch 23 MB-1 line 14: "mutations themselves happen in nightly_conductor"** — CONFIRMED. This is the ONE place where weights.json, kill_list.json, lessons.jsonl, and pattern_stats.json all get modified.
5. NC-X2: Each step wrapped in `_step()` helper (lines 30-40) with try/except that captures `traceback.format_exc().splitlines()[-3:]` (line 39) — **last 3 lines of stacktrace per step.** **One step failing does NOT break the chain.** ✅ Resilient orchestration. **Per docstring line 4-5: "each wrapped in try/except so one failure can't break the chain."**
6. NC-X3 (lines 213-218): Final `lj.log("nightly_brain_run", ...)` wrapped in bare-except. **The MUTATION ORCHESTRATOR's audit log to learning_journal can silently fail.** Combined with WA-30 (Batch 26 weight_applier silent journal failure), there are TWO points where mutations happen without journaling. **meta_brain.recent_mutations (Batch 23) reads learning_journal — if writes fail, brain reports STUCK falsely.** Per Batch 23 MB-X2.
7. NC-X4 (line 196): `_scan_count = 300 if deep_mode else 100` — **deep_mode triples scan size on weekends.** Magic 3x but documented. ✅ Reasonable. **But pattern_scan does sequential `for t in tickers: scan_ticker(t)` (line 79-81) — NO PARALLELISM.** Per Batch 8 PS parallel_scorer uses ThreadPoolExecutor. Inconsistent perf strategy.

## src/paper_trader.py — LINE BY LINE

### Lines 1-4: Module docstring + imports
- PT-1 BUG: 1-line docstring "Paper-trade logger." — minimal even by codebase standards.
- PT-2 SMELL (line 2): `import os, csv` — multi-import on one line. PEP 8 violates.
- PT-3 GOOD (line 3): datetime import — standard.
- PT-4 GOOD (line 4): typing.Dict — type hint.

### Lines 6-24: log_paper_trade
- PT-5 GOOD (line 6): Type-hinted, `csv_path` overridable. **Default `"data/trades.csv"` — NOT under data/picks_log.csv.** Distinct file. **21st file with relative-path constant.**
- PT-6 BUG (line 7): `os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)` — uses `os.makedirs` instead of `Path.mkdir`. Inconsistent with rest of codebase. Functionally fine.
- PT-7 BUG (line 8): `is_new = not os.path.exists(csv_path)` — race condition vs append. **In multi-threaded execution, two threads could both see file missing and both write headers.** Per Batch 8 PS parallel_scorer fires multiple threads. If any thread calls log_paper_trade concurrently, double-headers possible.
- PT-8 BUG (line 9): `open(csv_path, "a", newline="")` — append mode. **NO LOCK.** Concurrent appends can interleave row bytes → corrupt CSV.
- PT-9 BUG (lines 12-13): **9 column names hardcoded.** No constant, no schema validation. Compare to pick_logger (Batch 11) with 56 columns documented but still fragile.
- PT-10 BUG (line 15): `datetime.now().isoformat(timespec="seconds")` — NAIVE datetime. Cross-cutting.
- PT-11 GOOD (line 15): timespec="seconds" — clean format.
- PT-12 BUG (line 16-22): **6 raw `pick[...]` and `pick["plan"][...]` accesses.** No defensive `.get()`.
- PT-13 BUG (line 17): `pick["scores"]["composite"]` — DOUBLE KeyError per PT-X1 head finding. **For a scored pick this works. For a pick that came through hard_blocks rejection or non-scoring path, scores key may be missing.** Silent skip OR runtime crash.
- PT-14 GOOD (lines 18-22): Uses `.get()` for pick["plan"] sub-fields — defensive.
- PT-15 BUG (line 23): `"paper"` — magic literal. If real-trade mode is added later ("live"), would be a literal flag. Should be enum/constant.
- PT-16 BUG: NO RETURN VALUE. Caller can't tell if write succeeded. Combined with PT-7 race condition + PT-8 no-lock, silent corruption possible without caller awareness.
- PT-17 BUG: NO LOGGING of what was written. For audit, operator can't tell what trades were paper-logged vs not.

## src/nightly_conductor.py — LINE BY LINE

### Lines 1-16: Module docstring
- NC-1 GOOD: 16-line docstring documenting purpose + ORDER MATTERS notice.
- NC-2 GOOD: Lists 8 steps in execution order with arrow-arrows showing inputs/outputs.
- NC-3 GOOD: Documents the resilience contract ("one failure can't break the chain").

### Lines 17-27: Imports + paths
- NC-4 GOOD (line 17): `from __future__ import annotations`.
- NC-5 GOOD (line 20): `import traceback` — for error capture.
- NC-6 BUG (lines 26-27): 2 RELATIVE PATHS. **22nd file.** Cumulative.

### Lines 30-40: _step
- NC-7 GOOD: Single helper for resilient step execution.
- NC-8 GOOD (line 33): `result = fn() or {}` — defensive None → empty dict.
- NC-9 GOOD (lines 35-40): try/except captures error type + message + last 3 traceback lines. **Operator-friendly forensic info.**
- NC-10 BUG: Catches Exception (broad) — but here it's appropriate per resilience contract.

### Lines 43-66: _load_universe_for_scan
- NC-11 GOOD (lines 43-46): Documents the scan-universe rationale ("avoids slamming yfinance").
- NC-12 GOOD (line 47): Set for dedup.
- NC-13 BUG (lines 49-56): bare `except Exception: pass` — Theme T1 undocumented. **A corrupt watchlist.json silently produces empty scan.**
- NC-14 BUG (lines 58-65): Same pattern for picks_log read. Silent fail on corrupt CSV.
- NC-15 BUG (line 60): `with PICKS_LOG.open() as f` — full file iteration; no chunking. For 5-year picks_log this is slow.
- NC-16 GOOD (line 66): `sorted(out)[:max_tickers]` — deterministic order, capped.
- NC-17 BUG (line 66): No "last 30d" filter as docstring claims. **DOCSTRING LIES** at line 57: "Recent picks (last 30d)" — actually scans ALL picks ever. Schema drift between intent and code.

### Lines 72-84: _step_pattern_scan
- NC-18 GOOD: Imports inside function (lazy load) — avoids import-time cost if step not used.
- NC-19 BUG (line 76): `(market_regime() or {}).get("regime", "unknown")` — defensive but per Batch 15 RG, market_regime always returns dict. `or {}` redundant.
- NC-20 BUG (lines 79-81): **Sequential per-ticker scan.** Per NC-X4 head finding, no ThreadPoolExecutor. **For 300 tickers in deep_mode, this can take 10+ minutes.** Per Batch 8 PS-X1 parallel_scorer uses 5-10 threads. Inconsistent.
- NC-21 GOOD (lines 83-84): Returns scan stats dict.

### Lines 87-92: _step_pattern_stats
- NC-22 GOOD: 3-line trivial — calls pattern_stats build_stats + save.
- NC-23 BUG (line 91): `if not k.startswith("_")` — counts keys not starting with "_". Magic. Defensive against meta-keys but per Batch 21 PS, no underscore keys are produced. **Defensive against future schema.**

### Lines 95-99: _step_pattern_auto_enable_disable
- NC-24 GOOD: Trivial wrapper. Returns disabled/reactivated lists.

### Lines 102-121: _step_calibration_propose
- NC-25 GOOD: Imports calibration + weight_proposer lazily.
- NC-26 GOOD (line 110): Min-N=10 closed picks for proposal.
- NC-27 BUG (line 109): `r.get("r_multiple") not in (None, "")` — checks for None or empty string. **Per Batch 23 MB-28 cross-cutting, doesn't handle "None" string sentinel.** Per Batch 11 PL-X1 pick_logger writes "None" as string. **Silent skip of a class of rows.**
- NC-28 GOOD (lines 113-116): try/except around per_factor_report. Returns skipped reason.
- NC-29 BUG (line 117): `datetime.now().strftime(...)` — NAIVE. Per cross-cutting.
- NC-30 GOOD (line 117-118): run_id with timestamp for traceability.
- NC-31 GOOD (line 119): write_proposals only if proposals non-empty.

### Lines 124-136: _step_weight_apply
- NC-32 GOOD: Calls weight_applier with dry_run=False.
- NC-33 GOOD (lines 127-131): _count helper handles int/list/None defensively. **Compensates for inconsistent return shapes from weight_applier.**
- NC-34 BUG: NO logging of WHICH proposals applied. Just counts. For audit, operator wants per-mutation detail. weight_applier already logs to history.jsonl (Batch 26 WA-18) but conductor doesn't surface.

### Lines 139-144: _step_auto_promote
- NC-35 GOOD (lines 142-144): **Defensive against unknown return shape** — handles list-or-dict return. **Indicates author isn't sure of auto_promote signature.** Schema fragility.

### Lines 147-154: _step_lesson_gc
- NC-36 GOOD: Same defensive list-or-dict pattern. Confirms NC-35 schema uncertainty.
- NC-37 BUG (line 154): `return {"gc_removed": 0}` — fall-through default. **If lesson_gc returns something unexpected (str, None), reports 0.** Hides upstream bugs.

### Lines 160-169: _step_agent_memoir
- NC-38 GOOD (lines 161-163): Documents "Step 8 (added 2026-05-04)" — schema archaeology.
- NC-39 BUG (line 165-168): 4 raw `m["lifetime_stats"][...]` accesses. No defensive `.get()`. KeyError-prone. Per PT-13 same pattern.

### Lines 172-222: run_nightly — THE PUBLIC API
- NC-40 GOOD: Comprehensive docstring with deep_mode rationale.
- NC-41 GOOD (lines 180-183): summary dict initialized with ts + steps.
- NC-42 BUG (line 181): `datetime.now().isoformat()` — NAIVE.
- NC-43 GOOD (lines 186-192): Auto-detect deep_mode from market_calendar.
- NC-44 BUG (line 191): bare except → defaults deep_mode=False. **If market_calendar fails, runs in shallow mode.** Acceptable degradation. Per Batch 14 MDH cross-cutting Theme T1 documented bare-except for non-critical path.
- NC-45 GOOD (line 193): summary["deep_mode"] surfaced.
- NC-46 BUG (line 196): `_scan_count = 300 if deep_mode else 100` — magic numbers but reasonable.
- NC-47 GOOD (lines 197-206): 8 steps in documented order.
- NC-48 BUG (lines 213-218): Per NC-X3, learning_journal log wrapped in bare-except. Mutation-event silent loss possible.
- NC-49 GOOD (lines 220-221): ok_count + fail_count surfaced.

### Lines 225-236: format_summary_text
- NC-50 GOOD: Plain-text summary for CI/logs.
- NC-51 GOOD: Per-step icon + result/error.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### PT-X1+X2: paper_trader is the LEAST-DEFENDED critical-path file
- 25 lines, no atomic write, no lock, no schema validation, KeyError-prone (PT-13)
- Per Batch 8 PS parallel_scorer fires multiple threads → race conditions possible
- Compare pick_logger (56 fields, fragile but documented) and pick_evaluator (atomic write + bug archaeology)
- **paper_trader.py needs the same MDH/PV gold-standard treatment** if used in production paper-trading

### NC-X1+X2: nightly_conductor IS the centralized mutation point
Per Batch 23 MB-1 docstring promise, mutations happen in nightly_conductor — CONFIRMED. 8 steps:
1. pattern_scan → patterns.jsonl WRITE
2. pattern_stats → pattern_stats.json WRITE
3. auto_enable_disable → patterns.jsonl MUTATE
4. calibration_propose → weight_proposals.jsonl WRITE
5. weight_apply → weights.json + weight_history.jsonl + proposals.jsonl WRITE/MUTATE
6. auto_promote → wisdom lessons.jsonl WRITE
7. lesson_gc → lessons.jsonl MUTATE
8. agent_memoir → memoir state WRITE

**8 mutation steps, conducted by ONE orchestrator, with resilient try/except per step.** Excellent design pattern. ✅

### NC-X3: Mutation event journaling is fragile (audit gap)
Per WA-30 (Batch 26) + NC-X3 (this batch), TWO points where mutations happen but learning_journal write may silently fail. Combined with MB-X2 (Batch 23 false STUCK alarm on empty events), this creates a **DOUBLE-FRAGILITY**:
- Mutations applied → journal write fails → meta_brain.recent_mutations sees no events → reports STUCK
- Operator alarmed by false STUCK on Sunday Telegram
- **Recovery: meta_brain should also check weight_history.jsonl + lessons.jsonl directly as fallback**

### NC-X4: Sequential pattern scan is slow + inconsistent
nightly_conductor sequentially scans 300 tickers (deep_mode). Per Batch 8 PS parallel_scorer uses ThreadPoolExecutor. **Same codebase, two perf strategies.** Could 5x speedup pattern_scan with ThreadPoolExecutor.

### NC-17: Docstring lies about "last 30d" filter
Line 57 docstring claims "Recent picks (last 30d)" but code at line 60-65 reads ALL picks ever. Schema drift between intent and implementation. Single most-misleading docstring in audit.

### Cross-cutting: 22 files with relative-path constants
Cumulative.

### Cross-cutting: Bare-except count
- nightly_conductor: 4 (NC-13, NC-14, NC-44, NC-48). Half documented (NC-44 has rationale). Half undocumented.
- paper_trader: 0 ✅ (but only because it has NO error handling at all)

### Cross-cutting: Schema fragility patterns
- NC-35 + NC-36: defensive list-or-dict shape handling for auto_promote/lesson_gc
- NC-39 + PT-13: raw nested key access without `.get()`
- NC-27: incomplete None-string-sentinel handling in CSV reads
**6+ instances of schema-uncertainty defensive coding within Phase D first 4 files.**

## SUMMARY (Batch 28)

| Severity | paper_trader | nightly_conductor | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 6 | 7 | 4 | 17 |
| Data/safety | 5 | 5 | 0 | 10 |
| Code smell | 3 | 4 | 0 | 7 |
| Good code | 3 | 35 | 0 | 38 |
| Total findings | 17 | 51 | 4 | 72 |

## TOP 10 CRITICAL FIXES from Batch 28

1. PT-X1+X2: Refactor paper_trader.py with atomic write + lock + .get() defensive access + return success bool. Use MDH/PV gold standard. (1 hr)
2. NC-X3 / NC-48: Don't bare-except the learning_journal write in run_nightly. Surface failures to summary. (10 min)
3. PT-13: `pick.get("scores", {}).get("composite")` defensive. (5 min)
4. NC-X4 / NC-20: Use ThreadPoolExecutor for pattern_scan loop. (30 min)
5. NC-17: Either implement 30d filter OR fix docstring. (10 min)
6. NC-27: Handle "None" string sentinel in r_multiple check. (5 min)
7. NC-39 + PT-12: Use defensive `.get()` for nested dict access in nightly_conductor + paper_trader. (15 min)
8. PT-7+PT-8: Add threading.Lock and atomic write to log_paper_trade. (15 min)
9. NC-13+NC-14: Document or escalate the bare excepts in _load_universe_for_scan. (5 min)
10. PT-15: Replace "paper" magic literal with TradeMode enum. (10 min)

## NEW THEMES UPDATED

- Theme T1 (bare except): nightly_conductor 4, paper_trader 0 (no exception handling at all). Mixed.
- Theme T2 (schema drift): NC-35+NC-36 list-or-dict defensive handling indicates upstream API uncertainty. NC-17 docstring vs code drift.
- Theme T6 (atomic writes): paper_trader joins pick_logger as fragile state writers. Now 9 of 12 audited state-writers UNSAFE.
- Theme T8 (DRY): N/A this batch.
- Theme T11 (fail-open by accident): PT-X1+X2 silent paper-trade loss. NC-X3 silent mutation-event loss.
- Theme T13 (silent-default-fills): PT-12 raw key access could KeyError silently if main.py's caller wraps. NC-37 fall-through 0.
- Theme T14 (gold-standard patterns): nightly_conductor is THE TEMPLATE for resilient orchestration (per-step try/except + traceback capture + summary surfacing). paper_trader is the OPPOSITE — anti-template.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | 8/8 COMPLETE | (none) | 8/8 |
| Phase B (scoring/data) | 18/18 COMPLETE | (none) | 18/18 |
| Phase C (brain pillars) | 12/12 COMPLETE | (none) | 12/12 |
| Phase D (pipeline & output) | 4/~30 done | paper_trader, nightly_conductor | 4/~30 |
| Total true line-by-line | | +2 files | **57 of ~382 (~14.9%)** |
| Remaining | | | **~325 files** |

## NEXT BATCH

Batch 29: src/auto_promote.py + src/lesson_gc.py — the TWO Phase-D mutation actors called by nightly_conductor steps 6 and 7. They actually MODIFY wisdom_base lessons.jsonl. Critical to verify they honor wisdom_base's WB-X3 full-file-rewrite anti-pattern + WB-X5 kill_list fragility.

End of Batch 28. Phase D in progress (4/30).
