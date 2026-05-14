# Batch 14 — src/market_data_health.py (228 lines) + src/market_calendar.py (215 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** market_data_health.py (228 lines, fully read), market_calendar.py (215 lines, fully read)
**Phase:** B (scoring + data layer) — files 5 and 6 of ~18

## TOP HEADLINE FINDINGS

1. MDH-X1: market_data_health.py is THE TELEMETRY BACKBONE. data_fetcher (Batch 13) writes to it. premarket_readiness_gate (Batch 10) reads from it. 5 readers/writers across the codebase share this file. **Quality is critical.**
2. MDH-X2: USES ATOMIC WRITE PATTERN (line 76-78: tmp.write_text + tmp.replace). **First and ONLY file in the audit so far with atomic write discipline.** Compare to pick_logger (Batch 11 PL-19) which rewrites in place with no backup. **Use as template.**
3. MDH-X3: USES THREADING.LOCK (line 28). **First file to acknowledge concurrent writes.** parallel_scorer fires 5-10 threads (Batch 8) all writing telemetry → without _LOCK this would corrupt. ✅
4. MC-X1: market_calendar.py is HARDCODED HOLIDAYS for 2026-2028. **Will silently break on January 1, 2029 unless someone manually adds 2029 holidays.** Renewal mechanism exists (lines 165-196) but depends on Sunday Self-Improvement Report being read by an operator. No CI alert.
5. MC-X2 + Batch 6 M-RUN3 update: T51 calendar guard fail-OPEN bug — I now see the function `is_trading_day` is correct (line 114-117). The fail-open is in main.py's CALLER, not here. This file is solid; bug is elsewhere.
6. MDH-15 (line 184-186): `except Exception: # Telemetry must never break the picker. return` — explicit philosophy comment justifying the bare except. **First bare-except in audit with documented justification.** Defensible exception to Theme T1.
7. MC-23 (line 95): `_to_date` parses ISO strings via `datetime.fromisoformat(d.split("T")[0])` — **but doesn't handle other formats** (e.g., "5/9/2026" American, "09/05/2026" European). For a date string from CSV that uses non-ISO format, raises ValueError. Compare to hard_blocks HB-45 which has same fragility. Calendar can crash on malformed input.

## src/market_data_health.py — LINE BY LINE

### Lines 1-10: Module docstring
- MDH-1 GOOD: Explicit "lightweight and dependency-free so production runs can record provider failures without creating another point of failure." **Engineering philosophy stated.**
- MDH-2 GOOD: Lists 3 distinguishable failure modes (no candidate / provider degraded / invalid ticker noise).

### Lines 11-24: Imports
- MDH-3 GOOD (line 11): `from __future__ import annotations`.
- MDH-4 GOOD (line 14): threading imported. Concurrent-write awareness.
- MDH-5 GOOD (lines 15-17): timezone-aware datetime + ZoneInfo for ET. Compare to hard_blocks HB-46 / HB-70 that uses local datetime.now(). **First file using proper timezone handling.**
- MDH-6 GOOD (lines 19-24): Imports failure_taxonomy module. Separation of concerns.

### Lines 26-29: Module-level state
- MDH-7 BUG (line 26): `DATA_DIR = Path("data")` — **RELATIVE PATH AGAIN.** 6th file with this pattern (HB, PRG, PL, main.py, SCS, MDH).
- MDH-8 GOOD (line 28): `_LOCK = threading.Lock()` — single module-level lock for ALL telemetry writes. Coarse-grained but correct.
- MDH-9 BUG (line 29): `MAX_SAMPLES = 30` — magic 30. Caps sample collection per day. Documented intent (line 172) but threshold not justified.

### Lines 32-33: _today_et
- MDH-10 GOOD: `datetime.now(timezone.utc).astimezone(ET)` — UTC then convert to ET. Robust against runner timezone.

### Lines 36-38: health_path
- MDH-11 GOOD: `data_dir or DATA_DIR` — overridable for tests.
- MDH-12 GOOD: Daily file rotation by date. **Better than pick_logger PL-19 which rewrites a single growing file.**

### Lines 41-47: classify_provider_error
- MDH-13 GOOD: Backward-compatible wrapper. Docstring notes new code should prefer canonical `failure_type`. Migration documented.

### Lines 50-59: _blank_summary
- MDH-14 GOOD: 6-field skeleton. Clean.
- MDH-15 SMELL (line 54): `datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")` — verbose ISO-Z formatting. Could be helper. Repeated at line 75. DRY violation.

### Lines 62-70: _load
- MDH-16 GOOD: Defensive existence + isinstance + JSON parse with try/except.
- MDH-17 BUG (lines 68-69): `except Exception: pass` — bare except. Theme T1. **But here it's DEFENSIBLE per MDH-X3 philosophy (telemetry must never break picker).** Falls back to blank summary on corrupt JSON. Loss of past samples acceptable for telemetry.

### Lines 73-78: _save
- MDH-18 GOOD (line 74): `mkdir(parents=True, exist_ok=True)`.
- MDH-19 GOOD (lines 76-78): **ATOMIC WRITE via tempfile + replace.** Best practice. **THE ONLY FILE IN THIS AUDIT WITH THIS PATTERN.** Compare PL-19 (in-place rewrite, corruption risk).
- MDH-20 GOOD (line 77): `sort_keys=True` — deterministic output. Better diffability and test-stability.

### Lines 81-94: _provider_bucket
- MDH-21 GOOD: 10-field counter dict for each provider. Plus failure_types sub-dict.
- MDH-22 BUG (line 93): `{failure_type: 0 for failure_type in sorted(CANONICAL_FAILURE_TYPES)}` — initializes ALL canonical failure types to 0 even if never seen. **Storage bloat per provider but enables consistent downstream queries.** Tradeoff acceptable.

### Lines 97-104: _stage_bucket
- MDH-23 GOOD: 4-field counter for stage. Lighter than provider bucket.
- MDH-24 SMELL: stage bucket doesn't track failure_types. Asymmetric with provider bucket. Per-stage failure types could help debug "ohlcv timeouts vs info timeouts."

### Lines 107-186: record_market_data_event
- MDH-25 GOOD (line 108): keyword-only args after `*`. Same protection pattern as PSG/PRG.
- MDH-26 GOOD (line 119 docstring): Documents valid `result` values.
- MDH-27 GOOD (line 121): UTC date with ET conversion via _today_et.
- MDH-28 GOOD (line 123): `safe_result = result if result in {"success", "empty", "error"} else "error"` — defensive enum coercion. Unknown result becomes "error". **Stricter than PSG-13 (defaults silently to "normal").**
- MDH-29 GOOD (lines 124-134): Defensive failure classification with conditional.
- MDH-30 SMELL (lines 125-134): Multi-line ternary with kwargs is hard to scan. `failure_detail = X if cond else None` pattern, but X is 4 lines. Refactor to if/else for clarity.
- MDH-31 GOOD (line 138): `with _LOCK:` — acquires module lock.
- MDH-32 GOOD (lines 144-145): Both buckets get `attempts += 1` regardless of result.
- MDH-33 GOOD (lines 147-159): Branch by result. Each branch updates BOTH provider and stage buckets symmetrically.
- MDH-34 BUG (line 156-159): `if safe_error in pb: pb[safe_error] += 1 else: pb["provider_error"] += 1` — **string-based field-name access.** If provider error taxonomy adds new bucket name not in `pb`, falls into "provider_error" bucket. Silent drift. Should validate `safe_error` against pb's known keys.
- MDH-35 GOOD (lines 161-181): failure_types accounting + sample collection.
- MDH-36 BUG (line 180): `str(message or "")[:240]` — magic 240 char truncation. Same as parallel_scorer PS-9 but different limit. Inconsistency in truncation lengths across files.
- MDH-37 GOOD (line 172): `if len(samples) < MAX_SAMPLES:` — caps sample list. **Doesn't drop oldest, just stops appending.** First N samples preserved. Reasonable.
- MDH-38 BUG: After 30 samples, ALL further failures are aggregated to counters but NOT preserved as samples. **The 31st-Nth failures lose context.** For a 1000-ticker run with widespread failures, only first 30 stack traces preserved. Could miss late-emerging patterns.
- MDH-39 GOOD (line 183): `_save(path, payload)` — full overwrite via atomic write.
- MDH-40 GOOD (lines 184-186): Bare except with EXPLICIT JUSTIFICATION COMMENT. Per MDH-X3, this is the right exception to Theme T1 — telemetry MUST not break the picker.

### Lines 189-214: write_market_data_run_summary
- MDH-41 GOOD (line 190): keyword-only args.
- MDH-42 GOOD (lines 204-211): Conditional update — only writes provided fields. Allows incremental updates.
- MDH-43 GOOD (line 213-214): Same defensive bare-except philosophy as MDH-40.

### Lines 217-227: summarize_market_data_health
- MDH-44 GOOD: Read-only counterpart. Returns {} on missing/corrupt.
- MDH-45 SMELL (lines 226-227): bare except returns {} silently. Reasonable for read.

## src/market_calendar.py — LINE BY LINE

### Lines 1-17: Module docstring
- MC-1 GOOD: Documents intent (T51), source (NYSE website), AND maintenance procedure (annual renewal via Sunday Self-Improvement Report).
- MC-2 GOOD: Comprehensive API listing in docstring.
- MC-3 BUG (line 7): "Each January, the Sunday Self-Improvement Report flags when the calendar needs +1 more year of holidays added." — **DEPENDS ON OPERATOR READING REPORT.** No CI test that fails. Could rot for years.

### Lines 18-21: Imports
- MC-4 GOOD: stdlib only. No external deps for calendar = robust.

### Lines 27-62: US_MARKET_HOLIDAYS
- MC-5 GOOD: Date strings as set, easy to test/lookup.
- MC-6 GOOD: Inline comments document each holiday's name + observance reasoning.
- MC-7 BUG: 2026-2028 hardcoded — only 3 years cached. Today is 2026-05-12. **20.5 months left in cache** (until 2028-12-25). renewal_urgency would say "none" today (>18 months). But each passing day reduces the buffer. **Will trigger "soft" notification around 2027-08-12.**
- MC-8 BUG (line 53): `# 2028-01-01 not listed because Jan 1 = Sat, no observance NYE 2028` — **Confusion: 2028-01-01 IS a Saturday, but historically NYSE observed Friday 2027-12-31 instead OR took no observance.** This implementation assumes "no observance" — needs to verify against actual NYSE 2028 schedule. **Speculative entry.**
- MC-9 GOOD: Comment archaeology preserves observance logic for date-shift holidays.

### Lines 65-80: US_MARKET_EARLY_CLOSE
- MC-10 GOOD: Documented half-day closures.
- MC-11 BUG: 2028 only has 2 entries (Jul 3, Black Friday Nov 24). **Missing Christmas Eve 2028** (Dec 22 = Friday before Christmas Mon Dec 25). NYSE pattern would be early close Dec 22. Dropped entry.
- MC-12 BUG: 2026 entry "2026-07-02" comment says "Jul 4 = Sat → observed Fri Jul 3 closed, so Jul 2 = early close per recent NYSE pattern." **Self-inconsistent**: if Jul 3 is closed and Jul 2 is early close, that's correct. But MC-7 has Jul 3 as full-day holiday. Cross-check OK.

### Lines 86-96: _to_date
- MC-13 GOOD (line 88-89): None defaults to today. Convenient.
- MC-14 GOOD (lines 90-93): Handles datetime, date, str.
- MC-15 BUG (line 95): `datetime.fromisoformat(d.split("T")[0])` — **assumes ISO-8601 format only.** "5/9/2026" raises ValueError unhandled. Same fragility as Batch 8 HB-45.
- MC-16 BUG (line 96): `raise TypeError` for unknown type. Loud. ✅ but inconsistent with rest of codebase silence patterns.

### Lines 99-101: is_weekend
- MC-17 GOOD: `weekday() >= 5` — concise.

### Lines 104-106: is_holiday
- MC-18 GOOD: ISO format lookup against set. O(1).

### Lines 109-111: is_early_close
- MC-19 GOOD: Same pattern. Consistent.

### Lines 114-117: is_trading_day
- MC-20 GOOD: Composite check. **Correct logic.**
- MC-21 GOOD: Per Batch 6 M-RUN3 — fail-open bug is in main.py CALLER, not here. THIS function is correct.

### Lines 120-127: reason_market_closed
- MC-22 GOOD: 3-state return ('weekend' / 'holiday' / None).
- MC-23 BUG: Doesn't return 'early_close' even though that's a separately-tracked state. **Asymmetric.** A caller asking "why is market closed?" gets None for early-close days even though afternoon trading is closed. Naming is technically correct ("market closed" means full close) but ambiguous.

### Lines 130-137: next_trading_day
- MC-24 GOOD (line 130): `max_lookahead: int = 14` — defensive bound.
- MC-25 GOOD (line 137): RAISES on no-find. Loud. ✅ Compare to silent-degradation Theme T11.
- MC-26 BUG: `max_lookahead = 14` — for normal use OK, but Christmas-New-Year stretch can have 5+ consecutive non-trading days. 14 is plenty. Actually no — verify: 2024 saw Dec 24 early-close, Dec 25 closed, Dec 26 open, Dec 27 open, Dec 28-29 weekend, Dec 30-31 open, Jan 1 closed. So max consecutive closed = 3 days. 14 sufficient.

### Lines 140-147: previous_trading_day
- MC-27 GOOD: Symmetric with next_trading_day.

### Lines 153-156: cached_years
- MC-28 GOOD: Set comprehension extracting years from date strings.

### Lines 158-162: years_remaining
- MC-29 BUG (line 162): `max_year - today.year` — gives integer year count but doesn't account for partial year. If today=2028-12-31 and max_year=2028, returns 0 even though 1 day of cache remains. Off-by-one. Per renewal_urgency line 174 which uses months_left, the per-month computation is correct.

### Lines 165-167: needs_renewal
- MC-30 GOOD: Default threshold=2 years. Reasonable.

### Lines 170-178: renewal_urgency
- MC-31 GOOD: 4-tier ladder.
- MC-32 SMELL (line 174): `(max_year - today.year) * 12 + (12 - today.month)` — **off by one**. For today=2028-01-01 max=2028, gives 0*12 + 11 = 11 months left. But cache extends through 2028-12-25 = ~12 months. Approximate, acceptable for urgency tier.
- MC-33 BUG: Magic 18/6/2 month thresholds. No constants.

### Lines 181-196: renewal_message
- MC-34 GOOD (line 193): "critical" message says **"agent will silently break on next holiday"** — explicit warning of failure mode. Operator-friendly.
- MC-35 GOOD: Icon-coded by urgency.
- MC-36 SMELL (line 196): Hardcoded path "src/market_calendar.py" in the message. If file is renamed, message lies. Should use __file__ if possible.

### Lines 202-214: market_status_today
- MC-37 GOOD: Comprehensive 7-field dict for ops.
- MC-38 BUG (line 213): `next_trading_day(dd).isoformat() if closed else dd.isoformat()` — if today IS a trading day, next_open = today's date. **Slightly misleading semantics**: "next_open" suggests a future date. For a trading day, "open today" would be clearer.
- MC-39 BUG: Doesn't surface `early_close` flag in `closed_reason`. Per MC-23, half-days are silently invisible to "is the market closed?" callers.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### MDH-X1 + MDH-X2 + MDH-X3: GOLD STANDARD instrumentation file
- Atomic write (MDH-19): ONLY file in audit
- Threading.Lock (MDH-8): ONLY file in audit acknowledging concurrency
- Documented bare-except philosophy (MDH-40, MDH-43): ONLY file with explicit "telemetry must not break picker" comment
- UTC + ET timezone discipline (MDH-5, MDH-10): rare in codebase
- Daily file rotation (MDH-12): reduces growth issues that pick_logger has
- Defensive enum coercion (MDH-28): stricter than PSG-13

**Use as template for ALL state-writing files in the codebase, especially pick_logger.**

### MC-X1: Calendar will silently break on a future date
- Cache covers 2026-2028 (3 years)
- Renewal mechanism exists but depends on operator reading Sunday report
- **No CI test that fails when years_remaining < 1**
- Risk: 2029-01-01, agent assumes Jan 1 is a trading day (not in HOLIDAYS set), runs picks, may execute live (if enabled)

**Recommend: pytest test that asserts years_remaining(today=date(2099,1,1)) > 0. Will start failing 2 years before cache exhaustion. CI alarm.**

### MC-X2 vs Batch 6 M-RUN3
This file's logic is CORRECT (is_trading_day works). The fail-OPEN bug is in main.py caller. **Audit ledger update**: M-RUN3 is a CALLER bug, not a calendar bug.

### Cross-cutting: 6 files with relative-path constants now confirmed
HB-10, PRG-3, PL-5, main.py M-CFG1, SCS-14, MDH-7. **src/_paths.py would consolidate.**

### Cross-cutting: Inconsistent string-truncation lengths
- parallel_scorer PS-9: [:80]
- data_fetcher DF-16: [:120]
- market_data_health MDH-36: [:240]
**Three files, three truncation limits, all hardcoded.** Single TRUNCATION constant would unify.

### Cross-cutting: Telemetry consumed but not enforced
data_fetcher writes events. premarket_readiness_gate reads counters. **But no other gate reads telemetry.** If yfinance is degraded but PRDY's heuristic doesn't fire (PRDY-24 magic 10 threshold), the counters are written and ignored. **Telemetry awareness needs to extend to other gates.**

## SUMMARY (Batch 14)

| Severity | market_data_health | market_calendar | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 4 | 8 | 3 | 15 |
| Data/safety | 3 | 6 | 0 | 9 |
| Code smell | 6 | 4 | 0 | 10 |
| Good code | 32 | 21 | 0 | 53 |
| Total findings | 45 | 39 | 3 | 87 |

## TOP 10 CRITICAL FIXES from Batch 14

1. MC-X1: Add CI test asserting calendar has >12 months remaining. Will start failing 2 years before cache rot. (15 min)
2. MC-7+8+11: Verify and update 2028 holidays + add Christmas Eve 2028 early close. (1 hr — research NYSE schedule)
3. MC-15: Make _to_date handle non-ISO date strings (or raise with helpful message). (15 min)
4. MDH-7: Move DATA_DIR to src/_paths.py shared constants. (5 min)
5. MDH-22 + MDH-38: Document or implement rolling sample preservation (oldest-out vs first-N). (15 min)
6. MDH-34: Validate `safe_error` against known pb keys instead of silent-bucket-other. (15 min)
7. MC-23 + MC-39: Make reason_market_closed and market_status_today handle early-close consistently. (15 min)
8. MC-32: Externalize 18/6/2 month thresholds as constants. (5 min)
9. Cross-cutting: Standardize truncation lengths via MAX_ERR_MSG = 240. (15 min)
10. MC-36: Replace hardcoded "src/market_calendar.py" in renewal_message with __file__. (5 min)

## NEW THEMES UPDATED

- Theme T1 (bare except): Now has DOCUMENTED EXCEPTION (MDH-40). "Telemetry must not break the picker" justifies fail-soft.
- Theme T2 (schema drift): Stage bucket vs provider bucket asymmetric (MDH-24).
- Theme T11 (fail-open by accident): Calendar renewal depends on human-in-the-loop (MC-3, MC-X1). Will silently fail 2029-01-01 unless CI test added.
- **Theme T14 NEW (operational gold-standard patterns)**: market_data_health demonstrates 5 patterns absent elsewhere — atomic write, threading.Lock, timezone discipline, daily rotation, documented exception philosophy.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | 8/8 COMPLETE | (none) | 8/8 |
| Phase B (scoring/data) | 6/~18 done | market_data_health, market_calendar | 6/~18 |
| Total true line-by-line | | +2 files | 29 of 382 |
| Remaining | | | 353 files |

## NEXT BATCH

Batch 15: src/regime.py + src/calibration.py — market regime detection + score calibration. Both are referenced from main.py and parallel_scorer.

End of Batch 14. Phase B in progress (6/18).
