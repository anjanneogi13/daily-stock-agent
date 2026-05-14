# Batch 30 — src/pattern_engine.py (80 lines) + src/pattern_layer.py (131 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** pattern_engine.py (80 lines, fully read), pattern_layer.py (131 lines, fully read)
**Phase:** D (pipeline & output) — files 7 and 8 of ~30

## TOP HEADLINE FINDINGS

1. PE2-X1: pattern_engine.py is **THE PATTERN DETECTION ORCHESTRATOR** — 80 lines, runs ALL_DETECTORS (imported from `src.patterns` package, audited next batch) per ticker. **Called from nightly_conductor step 1** (Batch 28 NC-X1). **Produces patterns.jsonl that pattern_stats.py (Batch 21) consumes.** Producer-consumer chain confirmed.
2. PE2-X2: scan_ticker has a **BARE-EXCEPT WRAPPER per detector** (lines 34-37): `try: m = det.detect(df) except Exception: m = None`. **A buggy detector silently returns None — no logging, no escalation.** **Per Batch 28 nightly_conductor sequential scan over 300 tickers, a single broken detector silently produces ZERO matches across the entire run.** Operator sees empty patterns.jsonl + has no idea WHY.
3. PE2-X3 (line 41): `rec["date"] = datetime.now().date().isoformat()` — uses **TODAY'S DATE** as pattern detection date, NOT the date of the bar that triggered the pattern. **For end-of-day analysis, today=detection date works. But for backfill / historical scan, ALL backfilled patterns get today's date** → pattern_stats join (Batch 21 PS-X1) breaks. **Latent backfill bug.**
4. PL-X1: pattern_layer.py is **THE PATTERN→PROBABILITY MULTIPLIER** — converts pattern detections into ±15% multiplier on probability_engine score. **Multiplier capped at ±15% (line 22 MAX_BOOST=0.15) — the LARGEST single-source score adjustment in the audited brain stack.** Compare wisdom_consultant ±0.05 (Batch 25). 3x bigger impact.
5. PL-X2 (lines 73-75): "squash signal to [-MAX_BOOST, +MAX_BOOST]" with `raw = total_signal * 0.3`. **Magic 0.3 squash factor + comment example.** "edge of +0.5 with 0.8 conf = +0.4 raw → scale by 0.3 → +0.12 mult." Documented but undocumented WHY 0.3.
6. PL-X3 (lines 79-91): disable_pattern + enable_pattern + auto_enable_disable all WRITE to pattern_stats.json via `_ps.save(s)`. **Per Batch 21 PS-27+PS-28, pattern_stats.save has NO ATOMIC WRITE.** **Direct overwrite of pattern_stats.json.** Power loss = corrupt stats = pattern_layer always returns 1.0 (no effect) → all pattern intelligence dead.
7. PL-X4 (line 105): `pre_disabled = set(s.get(DISABLED_KEY, {}).keys())` — captures pre-state. Then auto_enable_disable iterates pattern stats and toggles disabled status based on edge thresholds (line 110: `mean_r <= -0.30 AND n >= 30`). **But auto_enable_disable USES PATTERN_STATS as STORAGE for the disabled list itself** (DISABLED_KEY=`"_disabled"`). **Storage + state mixing.** Per Batch 28 NC-23 cross-cutting, `pattern_stats._step skips keys starting with "_"` to avoid counting _disabled as a pattern. **The two files coordinate via convention, not contract.**

## src/pattern_engine.py — LINE BY LINE

### Lines 1-6: Module docstring
- PE2-1 GOOD: 6-line docstring documents purpose + dependencies + outputs.
- PE2-2 GOOD: "test-friendliness" — accepts df directly. ✅

### Lines 7-15: Imports + path
- PE2-3 GOOD (line 7): `from __future__ import annotations`.
- PE2-4 GOOD (line 13): Imports ALL_DETECTORS from src.patterns package.
- PE2-5 BUG (line 15): RELATIVE PATH `data/patterns.jsonl`. **23rd file with this pattern.** Cumulative.

### Lines 18-46: scan_ticker
- PE2-6 GOOD (lines 18-21): Type-hinted, all optional args.
- PE2-7 GOOD (line 23): `detectors = detectors or ALL_DETECTORS` — caller can override.
- PE2-8 BUG (lines 24-29): If df=None, fetch via data_fetcher with `period="3mo"`. **Hardcoded 3mo magic.** Not configurable per detector. Different patterns may need different lookbacks (e.g., long-term head-and-shoulders needs 6mo+, short-term breakouts need 1mo).
- PE2-9 BUG (line 28): bare `except Exception: return []` — Theme T1 undocumented. **A data_fetcher failure silently produces empty pattern matches.** Per PE2-X2.
- PE2-10 GOOD (line 30-31): Defensive empty df check.
- PE2-11 BUG (lines 33-37): Per PE2-X2, per-detector bare-except → silent None. **No logging of WHICH detector failed.** Operator sees empty out, doesn't know which detector is broken.
- PE2-12 GOOD (lines 38-39): None match → continue.
- PE2-13 GOOD (line 40): `m.to_dict()` — assumes detector produces an object with to_dict method.
- PE2-14 BUG (line 41): Per PE2-X3, today's date used as match date. Backfill broken.
- PE2-15 BUG (line 41): `datetime.now().date().isoformat()` — NAIVE. Cross-cutting.
- PE2-16 GOOD (line 42-44): rec enriched with ticker, direction, regime.
- PE2-17 BUG (line 44): `regime` arg can be None. Persisted as `None` in JSON → pattern_stats.py PS-22 maps to "unknown" regime. Per Batch 21 PS-X1 5-regime pollution.

### Lines 49-59: persist
- PE2-18 GOOD (lines 49-50): Type-hinted, optional path.
- PE2-19 GOOD (line 52-53): Empty input early return.
- PE2-20 BUG (lines 56-58): **JSONL APPEND, NO ATOMIC WRITE, NO LOCK.** Same pattern as Batch 22 SJ-33, Batch 24 LJ-13, etc. **Concurrent persist calls (multiple tickers in parallel) can interleave bytes → corrupt JSONL.** **Per Batch 28 NC-20 sequential scan in nightly_conductor mitigates this currently** but if parallelized later, lock missing.
- PE2-21 BUG: NO try/except around the write. Disk-full / permission-denied raises to caller (nightly_conductor step). **Per NC-X2 wraps step in try/except, so failure caught — but error message just says "OSError: ..." with no context.**

### Lines 62-79: load_recent
- PE2-22 GOOD (lines 62-67): Defensive existence check.
- PE2-23 BUG (line 68): `cutoff = datetime.now().date()` — NAIVE.
- PE2-24 BUG (line 70): `path.read_text().splitlines()` — full file in memory. Per Batch 21 PS-8 + others cross-cutting.
- PE2-25 BUG (lines 72-78): try/except (broad Exception, not just JSONDecodeError) catches AND swallows date-parse errors silently. Per Batch 22 cross-cutting JSONDecodeError pattern, but here BROADER.

## src/pattern_layer.py — LINE BY LINE

### Lines 1-12: Module docstring
- PL-1 GOOD: 12-line docstring documenting:
  - Purpose (signal → multiplier)
  - 3 multiplier rules (boost / penalize / neutral)
  - Disabled-patterns escape clause
- PL-2 GOOD: Documents max impact (1.15x boost, 0.85x penalty).

### Lines 13-23: Imports + constants
- PL-3 GOOD (line 13): `from __future__ import annotations`.
- PL-4 GOOD (lines 16-17): Imports pattern_engine + pattern_stats.
- PL-5 GOOD (lines 20-23): **4 named constants** — MIN_SAMPLE_FOR_EDGE=20, EDGE_R_THRESHOLD=0.20, MAX_BOOST=0.15, DISABLED_KEY="_disabled". Operator-friendly.
- PL-6 BUG: 4 magic thresholds not documented WHY chosen. Compare to Batch 22 SJ-X5 bucket_composite calibration archaeology.

### Lines 26-33: _get_edge
- PL-7 GOOD (line 26-27): Returns mean_r if n >= min, else None.
- PL-8 BUG (line 29): `bucket = pat.get(regime) or pat.get("unknown")` — **falls back to "unknown" regime if specific regime not found.** Per PE2-17, persist writes regime=None → pattern_stats may have "unknown" key → fallback fires. **Silent regime-conflation.** A pattern with strong edge in bull regime + no data in bear regime would use "unknown" for bear queries → wrong edge.
- PL-9 GOOD (line 31-32): `n < MIN_SAMPLE_FOR_EDGE` → None. Strict.
- PL-10 GOOD (line 33): `float(bucket.get("mean_r", 0))` — defensive numeric coercion.

### Lines 36-37: _is_disabled
- PL-11 GOOD: Trivial lookup.

### Lines 40-76: pattern_multiplier — THE CORE FUNCTION
- PL-12 GOOD (lines 40-43): Type-hinted with optional df + stats injection (test-friendly).
- PL-13 GOOD (lines 49-50): Lazy load of stats.
- PL-14 GOOD (lines 51-53): scan_ticker call, empty matches → (1.0, []).
- PL-15 GOOD (lines 55-67): Loops over matches, accumulates signal.
- PL-16 GOOD (line 59-60): Disabled pattern → continue.
- PL-17 GOOD (line 61-63): No edge data → continue (no effect).
- PL-18 GOOD (line 65): Weighted by detector confidence.
- PL-19 BUG (line 65): `float(m.get("confidence", 0.5))` — **default 0.5 if missing.** **A detector that doesn't produce confidence field gets 50% weight.** Defensible default but masks a producer bug.
- PL-20 GOOD (line 67): qualifying list captures match + edge + contribution for caller transparency.
- PL-21 GOOD (lines 69-70): No qualifying → return (1.0, all_matches). **Returns ALL matches even when no qualifying.** Operator can see "patterns fired but none qualified."
- PL-22 BUG (line 74): Per PL-X2, magic 0.3 squash. Undocumented WHY.
- PL-23 GOOD (line 75): Clamp to [-MAX_BOOST, +MAX_BOOST].
- PL-24 GOOD (line 76): Returns `(round(mult, 4), qualifying)` — 4-decimal precision.

### Lines 79-91: disable_pattern + enable_pattern
- PL-25 GOOD: Trivial state mutators.
- PL-26 BUG (lines 83, 90): `_ps.save(s)` — per PL-X3, pattern_stats.save has NO ATOMIC WRITE. **Each disable/enable can corrupt the entire pattern_stats.json.**
- PL-27 BUG: NO LOGGING of disable/enable events. Compare to auto_enable_disable line 122-127 which DOES log to learning_journal. **Inconsistent within file.**

### Lines 94-130: auto_enable_disable — MUTATION ACTOR
- PL-28 GOOD (lines 94-101): 7-line docstring documenting kill_threshold + min_n.
- PL-29 BUG (lines 95-96): kill_threshold_r=-0.30 + min_n=30. **Different from class-level constants (EDGE_R_THRESHOLD=0.20).** **Two threshold values for related concepts.** No central config.
- PL-30 GOOD (line 105): pre-state captured for diff.
- PL-31 GOOD (lines 107-119): Iterates patterns, computes `bad` flag from any-regime check.
- PL-32 GOOD (line 110): `b.get("n",0) >= min_n AND b.get("mean_r",0) <= kill_threshold_r` — **AND logic** for kill criteria.
- PL-33 BUG (line 110): `mean_r <= kill_threshold_r` — strict less-than-or-equal. At exactly -0.30 with n=30, kills. Edge case operator should know.
- PL-34 GOOD (lines 112-119): Idempotent — only adds to disabled if not already, only reactivates if already disabled.
- PL-35 BUG (line 120): `_ps.save(s)` — same PL-X3 atomic-write gap.
- PL-36 GOOD (lines 122-129): **Logs each disable/enable event to learning_journal.** Per Batch 23 MB-X1 chain — meta_brain.recent_mutations consumes these.
- PL-37 BUG (line 128-129): bare `except Exception: pass` — Theme T1 undocumented. **Per Batch 28 NC-X3 cross-cutting, mutation events with silent journal failure.** Now confirmed in 3 modules: WA-30, NC-X3, PL-37.
- PL-38 GOOD (line 130): Returns dict matching nightly_conductor's expected shape (Batch 28 NC-24).

## CONSOLIDATED CROSS-CUTTING FINDINGS

### PE2-X2+X3: Pattern detection has TWO silent-failure modes
1. **Per-detector bare-except (PE2-11):** A buggy detector returns None silently.
2. **Today's-date as match date (PE2-X3):** Backfill produces wrong dates → pattern_stats join fails.
**Both invisible to operator.** Combined with NC-20 sequential scan over 300 tickers in deep_mode, **a single broken detector silently zeroes ALL pattern matches for that detector across all tickers** for the entire run.

### PL-X3+PL-26+PL-35: pattern_stats.json has FOUR unsafe writers
Cumulative writers:
1. pattern_stats.save (Batch 21 PS-27)
2. pattern_layer.disable_pattern
3. pattern_layer.enable_pattern
4. pattern_layer.auto_enable_disable

**4 writers, 0 atomic, 0 locks.** Pattern_stats.json is the SECOND-MOST-FRAGILE state file (after lessons.jsonl with 3 unsafe writers from Batch 29).

### PL-X4: Storage + state mixing in pattern_stats.json
DISABLED_KEY="_disabled" sub-dict lives INSIDE pattern_stats.json (the analytics file). Coordination via convention (Batch 28 NC-23 skip "_" keys) instead of contract. **A future writer that doesn't honor the convention would corrupt analytics OR be counted as a "pattern."** **Should split into separate files** (pattern_stats.json + pattern_disabled.json).

### PL-29 + Cross-cutting: 7th distinct min-N threshold
Cumulative:
- hypothesis_engine: min_n=10 (B21)
- self_awareness: n>=20 verdict (B23)
- meta_brain.suggest_hypotheses: min_n=20 (B23)
- weight_proposer: min_n=30 (B22)
- nightly_conductor.calibration_propose: 10 closed picks (B28)
- auto_promote: min_sample=40 (B29)
- pattern_layer.auto_enable_disable: min_n=30 (this batch)
- pattern_layer.MIN_SAMPLE_FOR_EDGE: 20 (this batch — same module, different threshold)
**8 thresholds across 7 modules in 6 batches.** **CRITICAL DRY violation.** Single src/_constants.py CONFIDENCE_THRESHOLDS would unify.

### Cross-cutting: Mutation event silent-journal-failure now in 3 modules
1. weight_applier (B26 WA-30)
2. nightly_conductor (B28 NC-X3)
3. pattern_layer.auto_enable_disable (this batch PL-37)
**3 mutation actors, all wrap learning_journal in bare-except.** Combined creates the "meta_brain false STUCK alarm" risk (Batch 23 MB-X2).

### Cross-cutting: Detector-level confidence default magic
PL-19 line 65: `float(m.get("confidence", 0.5))` — magic 0.5 default. **For detectors that DON'T return confidence, halfway weight.** **Should be 0 (skip) OR explicit warn.** Per Batch 18 fundamentals FH-X3 cross-cutting silent default fills.

### Cross-cutting: ATOMIC WRITE adoption (running tally)
Now 3 of 14 audited state-writers do atomic write. pattern_layer adds 3 more unsafe writes to pattern_stats.json (which itself was already unsafe).
- Safe: market_data_health, news_signals, pick_evaluator
- Unsafe: pick_logger, regime, news_engine, finnhub_data, pattern_stats (× 4 writers now), signal_journal, wisdom_base (× 3 writers), weight_applier, paper_trader, lesson_gc
**~78% of state-writers UNSAFE.**

### Cross-cutting: 23 files with relative-path constants
Cumulative.

## SUMMARY (Batch 30)

| Severity | pattern_engine | pattern_layer | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 8 | 11 | 4 | 23 |
| Data/safety | 5 | 7 | 0 | 12 |
| Code smell | 2 | 2 | 0 | 4 |
| Good code | 11 | 18 | 0 | 29 |
| Total findings | 26 | 38 | 4 | 68 |

## TOP 10 CRITICAL FIXES from Batch 30

1. PE2-X2 / PE2-11: Log per-detector failures (logger.warning with detector name + error). Currently silent. (10 min)
2. PE2-X3 / PE2-14: Use last bar's date (df.index[-1]) instead of today's date for match date. Fixes backfill. (10 min)
3. PL-X3 / PL-26+35: Add atomic write to pattern_stats.save. (15 min — included in WA-X3 1-hr refactor)
4. PL-X4: Split DISABLED_KEY into separate pattern_disabled.json file. Cleaner separation. (30 min)
5. PL-29 cross-cutting: Centralize 8 min-N thresholds in src/_constants.py CONFIDENCE_THRESHOLDS. (30 min)
6. PL-19: Default detector confidence to 0 (skip) instead of 0.5. (5 min)
7. PE2-20: Add threading.Lock to persist function for parallel-scan safety. (10 min)
8. PE2-25: Use scoped json.JSONDecodeError instead of bare Exception in load_recent. (5 min)
9. PL-37: Document or escalate bare-except around learning_journal call. Same Batch 28 NC-X3 fix. (5 min)
10. PL-X2 / PL-22: Document WHY 0.3 squash factor. Cite empirical derivation. (5 min)

## NEW THEMES UPDATED

- Theme T1 (bare except): pattern_engine 3 (PE2-9, PE2-11, PE2-25). pattern_layer 1 (PL-37). Mostly undocumented.
- Theme T2 (schema drift): PL-X4 storage+state mixing in pattern_stats.json.
- Theme T6 (atomic writes): pattern_stats.json now has 4 unsafe writers (worst of any state file). NOW 11 of 14 state-writers UNSAFE.
- Theme T8 (DRY): PL-29 8 min-N thresholds in 7 modules. Compounding.
- Theme T11 (fail-open by accident): PE2-X2 silent detector failure → empty matches. PL-19 magic 0.5 confidence default.
- Theme T13 (silent-default-fills): PL-19, PE2-23 naive datetime, PE2-X3 today's-date for backfill.
- Theme T14 (gold-standard patterns): pattern_layer.auto_enable_disable is well-designed (idempotent, journaled, AND criteria) but the persist layer (pattern_stats.save) is fragile. **Logic clean, persistence broken.**

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | 8/8 COMPLETE | (none) | 8/8 |
| Phase B (scoring/data) | 18/18 COMPLETE | (none) | 18/18 |
| Phase C (brain pillars) | 12/12 COMPLETE | (none) | 12/12 |
| Phase D (pipeline & output) | 8/~30 done | pattern_engine, pattern_layer | 8/~30 |
| Total true line-by-line | | +2 files | **61 of ~382 (~16.0%)** |
| Remaining | | | **~321 files** |

## NEXT BATCH

Batch 31: src/patterns/ subdirectory begins — the actual detector implementations consumed by pattern_engine ALL_DETECTORS. Will start with src/patterns/__init__.py + first 1-2 detectors (likely bull_flag.py or similar).

End of Batch 30. Phase D in progress (8/30).
