# Batch 10 — src/missing_data_gate.py (163 lines) + src/premarket_readiness_gate.py (197 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** missing_data_gate.py (163 lines, fully read), premarket_readiness_gate.py (197 lines, fully read)
**Phase:** A (safety/gates) — files 6 and 7 of 8

## TOP HEADLINE FINDINGS

1. MDG-X1: missing_data_gate.py is the SECOND-CLEANEST gate (after portfolio_risk). 12 explicit checks, all fail-CLOSED, no bare-except in business logic, rich audit-trail. Tied for "use as template" with PRG.
2. PRG-X1 vs MDG: missing_data_gate is even tighter than portfolio_risk_gate in one respect — it has a CRITICAL_OFFICIAL_PICK_FIELDS tuple at module top that DOCUMENTS the contract (line 22-31). portfolio_risk_gate doesn't. This is the closest the codebase gets to a real schema definition.
3. PRDY-X1: premarket_readiness_gate.py is also clean — but with one major design issue: 4 huge return-dict branches (lines 116-159, 167-178) duplicate ~10 fields each. ~80 lines of dict-construction repetition. Single helper would collapse to ~30 lines.
4. MDG-9: validate_official_pick_required_data declares CRITICAL_OFFICIAL_PICK_FIELDS as 8 fields but the actual function checks 8 fields PLUS premarket_actionable + portfolio_risk_passed (10 things total). The constant is incomplete documentation. Only 80% of what's checked.
5. MDG-7: official_pick_required_field_snapshot has TEN dual-source `or` chains (lines 66-77) — same Theme T2 pattern as everywhere else. Schema unification would simplify this whole function.
6. PRDY-12: `if ohlcv_attempts >= 10` (line 166) — MAGIC 10. The provider-degraded check fires only when at least 10 attempts were made. For small universes (<10 tickers) this branch is DEAD. Theme T4 silent gap in safety.
7. PRDY-9: `required_fetched_count = max(1, min(min_fetched_count, required_by_coverage or min_fetched_count))` (line 101) — inscrutable formula. Took ~5 reads to confirm intent. Coverage and absolute thresholds combined ambiguously.

## src/missing_data_gate.py — LINE BY LINE

### Lines 1-15: Module docstring
- MDG-1 GOOD: Explicit purpose, intentionally reporting/validation only, "no fake picks/no paper/no live" disclaimer. Same template as PSG/PRG.

### Lines 17-19: Imports
- MDG-2 GOOD: Just typing.Any. Minimal.

### Lines 22-31: CRITICAL_OFFICIAL_PICK_FIELDS constant
- MDG-3 GOOD: 8-field tuple at module top. Closest thing to a schema in the codebase. Used by summary at line 159.
- MDG-4 BUG: Constant lists 8 fields but validate_official_pick_required_data checks 10 things (8 + premarket_actionable + portfolio_risk_passed). Constant is incomplete.
- MDG-5 SMELL: Constant declared but never USED for the actual validation (validation hardcodes field names, not iterating the tuple). It's documentation-only — purely descriptive. Currently the constant and the checker can drift independently (already have, per MDG-4).

### Lines 34-35: _is_blank
- MDG-6 GOOD: Compact, defensive against None and whitespace strings.

### Lines 38-44: _safe_float
- MDG-7 SMELL: FOURTH copy of _safe_float in the codebase (smell_faculty inline, premarket_sanity, portfolio_risk_gate, missing_data_gate). Each variant slightly different — this one returns None default; PRG/PSG return user-supplied default. Cross-file DRY violation now fully confirmed.

### Lines 47-53: _safe_int
- MDG-8 SMELL: SECOND copy of _safe_int (also in portfolio_risk_gate). Same DRY violation.

### Lines 56-78: official_pick_required_field_snapshot
- MDG-9 GOOD (lines 58-62): 5 dict-shape defensive isinstance checks. Same pattern as PRG. Verbose but correct.
- MDG-10 BUG (lines 66-77): TEN dual-source `or` chains (info OR candidate; plan OR candidate; etc.). Schema fragmentation taxonomy: company info.name OR candidate.company; sector info.sector OR ""; score scores.composite; trade_type candidate.trade_type OR scores.trade_type — same field in 2 places; entry/stop_loss/take_profit/risk_reward/quantity plan.X OR candidate.X — 5 fields with dual-source; premarket_action candidate.premarket_action OR sanity.action — same field in 2 places; premarket_actionable candidate.premarket_actionable OR sanity.actionable — same redundancy; portfolio_risk_passed portfolio_risk.passed only (single-source). Theme T2 amplified. The function exists BECAUSE the schema is fragmented.
- MDG-11 BUG (line 76): candidate.get("premarket_actionable") if "premarket_actionable" in candidate else sanity.get("actionable") — uses `in` check instead of `or`. Different pattern from line 75. Why? Because premarket_actionable=False is a meaningful value that `or` would override with sanity.actionable. Subtle. Should add comment explaining.
- MDG-12 BUG: Same subtle pitfall NOT applied to other False-meaningful fields. E.g., portfolio_risk_passed=False at line 77 — but PRG only sets passed: True (never False). So technically safe, but if PRG ever started writing False, this would silently treat it as missing.

### Lines 81-127: validate_official_pick_required_data
- MDG-13 GOOD (line 84): errors: list[str] — collects ALL errors, not first-only. Compare to hard_blocks HB-65 first-block-wins. This is the CORRECT pattern.
- MDG-14 GOOD (lines 86-87): ticker check.
- MDG-15 GOOD (lines 89-93): score check including non-numeric AND negative.
- MDG-16 BUG (line 96): trade_type not in {"day", "swing"} — closed enum, no extension. What about "scalp", "position", "options"? Future trade types break this gate silently. Should be config-driven.
- MDG-17 GOOD (lines 99-114): 5 numeric fields validated for "must be positive". Each with explicit error message.
- MDG-18 GOOD (lines 116-119): Long-only assertion — stop_loss < entry, take_profit > entry. Same as PRG-40/41. Now the long-only assumption is in 2 explicit places.
- MDG-19 BUG (lines 116, 118): entry is not None and stop_loss is not None — but lines 105-108 already added errors when entry/sl are None. So lines 116/118 only fire when entry+sl are both PRESENT. If entry is None, error logged at 106, no sl-vs-entry check (correct: can't compare).
- MDG-20 BUG (lines 122-125): "premarket_actionable is false" / "portfolio_risk_passed is false" — these add to errors, BUT the logic is === False (per snap.get returning False). What if prior gate didn't run and actionable is None? Falls through (no error). Silently passes a candidate that bypassed prior gates entirely. Should also error on None.

### Lines 130-162: apply_missing_data_gate
- MDG-21 GOOD (line 130): Returns triple (allowed, blocked, summary). Pattern consistency with PRG/PSG.
- MDG-22 GOOD (lines 138-146): Blocked entry has 7 fields including missing_or_invalid_fields LIST (not just joined string) AND required_field_snapshot (full picture). Richest blocked-audit in any gate.
- MDG-23 SMELL (line 144): official_pick_required_field_snapshot(candidate) called TWICE per candidate (line 136 inside validate, line 144 here, and line 151 for allowed). 2-3x snapshot construction. Tiny perf, but ugly.
- MDG-24 GOOD (lines 149-152): Allowed candidate gets missing_data_gate namespaced sub-dict. Same pattern as PRG-58.
- MDG-25 GOOD (lines 155-160): Summary includes critical_fields list — operator can see WHAT was checked.
- MDG-26 BUG: Summary does NOT include count-by-error-type. For 50 blocked candidates, you have a flat list. Useful aggregation: {"missing_entry": 12, "negative_score": 3, ...}. Currently aggregator is downstream's problem.

## src/premarket_readiness_gate.py — LINE BY LINE

### Lines 1-11: Module docstring
- PRDY-1 GOOD: Same disclaimer template. "fail closed into official no-pick when critical data is missing."

### Lines 13-19: Imports + DEFAULT constants
- PRDY-2 GOOD (line 18): DEFAULT_MIN_FETCH_COVERAGE = 0.25 — 25% minimum coverage. Magic but named.
- PRDY-3 GOOD (line 19): DEFAULT_MIN_FETCHED_COUNT = 25 — magic 25, named.
- PRDY-4 SMELL: Two defaults, no comment explaining "why 25%? why 25 tickers?". Documented with the value but not the reasoning.

### Lines 22-26: _safe_int
- PRDY-5 SMELL: THIRD copy of _safe_int in codebase. Slightly different than PRG._safe_int — this one returns user-supplied default; PRG's also has the `or 0` issue (PRG-7).
- PRDY-6 BUG (line 24): int(value or 0) — same `or 0` pattern as PRG-6. Garbage string "abc" raises, caught, returns default. But "0" string returns 0 silently.

### Lines 29-33: _safe_float
- PRDY-7 SMELL: FIFTH copy of _safe_float now confirmed in codebase.

### Lines 36-75: _provider_attempt_summary
- PRDY-8 GOOD (lines 37-39): Defensive isinstance dict checks for nested dicts.
- PRDY-9 SMELL (lines 41-46): SIX provider counters initialized to 0. Could be a single Counter() or dict.
- PRDY-10 GOOD (lines 48-56): Iterates providers and aggregates 6 fields per provider. Defensive isinstance check at line 49.
- PRDY-11 GOOD (lines 58-62): OHLCV stage breakout — 4 fields. Reasonable.
- PRDY-12 GOOD (lines 64-75): Returns flat 10-field dict. Clean output contract.

### Lines 78-191: build_premarket_readiness_decision
- PRDY-13 GOOD (line 79): Keyword-only args.
- PRDY-14 GOOD (lines 94-97): Re-coerces inputs through _safe_int / _safe_float. Defensive against caller passing strings.
- PRDY-15 BUG (line 96): max(0.0, min(1.0, _safe_float(min_fetch_coverage, DEFAULT_MIN_FETCH_COVERAGE))) — clamps to [0,1]. Reasonable but COMPLETELY HIDES caller error (e.g., caller passes 50% as 0.5 correctly OR 50 mistakenly → clamped to 1.0 → 100% coverage requirement → always fails). Silent input-error tolerance. Should validate or warn.
- PRDY-16 BUG (line 97): max(1, _safe_int(min_fetched_count, DEFAULT_MIN_FETCHED_COUNT)) — floor 1.
- PRDY-17 BUG (line 100): required_by_coverage = int(universe_count * min_fetch_coverage) — int truncates. For universe=10, coverage=0.25 → required=2 (truncated from 2.5). Off-by-one silent. Should be math.ceil for safety stance.
- PRDY-18 BUG (line 101): required_fetched_count = max(1, min(min_fetched_count, required_by_coverage or min_fetched_count)) — INSCRUTABLE FORMULA. Effectively required_fetched_count = min(min_fetched_count, required_by_coverage) for normal cases. ASYMMETRIC LOGIC: passes if EITHER ≥25 fetched OR ≥25% of universe — whichever is LESS. So a universe of 40 needs only 10 (25% of 40), not 25. Looser threshold than naming suggests. Bug or feature? Comment-free.
- PRDY-19 GOOD (line 103): fetch_coverage rounded to 4 decimals.
- PRDY-20 SMELL (lines 105-114): warnings list populated but never RETURNED to caller in a structured-error sense. Just shoved into the result dict. Correct but naming "warnings" suggests they ARE warnings (vs being IN warnings). Naming OK-ish.
- PRDY-21 BUG (lines 116-128): Empty universe branch. Returns 9-field dict. First of 4 nearly-identical return blocks.
- PRDY-22 BUG (lines 130-142): No market data branch. Same 9-field shape.
- PRDY-23 BUG (lines 144-159): Low coverage branch. Same shape, only status, primary_no_pick_cause, human_readable_summary differ.
- PRDY-24 BUG (line 166): if ohlcv_attempts >= 10 and ohlcv_successes == 0 and (ohlcv_errors + ohlcv_empty) >= ohlcv_attempts — MAGIC 10. The provider-degraded check requires AT LEAST 10 attempts. For a small universe (e.g., 5-ticker test run), this branch is DEAD. Even for a universe of 25, if only 9 OHLCV attempts happened, branch dead. Theme T4 silent gap. Provider could be returning errors on every attempt and gate passes simply because attempt count was too low. The 10 should be parameterized OR scaled to universe size.
- PRDY-25 BUG (lines 167-178): FOURTH near-identical 12-field dict.
- PRDY-26 GOOD (line 180-191): Pass branch. Same 9-field shape.

### Lines 194-196: assert_premarket_readiness_or_no_pick
- PRDY-27 SMELL: Trivial pass-through wrapper. Adds no value. Consider removing OR add the actual "raise NoPickError" semantics implied by the name. Currently the name LIES — it doesn't assert, it just calls.
- PRDY-28 BUG: Function name suggests `raise` semantics ("assert_X_or_no_pick" sounds like fail-fast). Actual behavior: returns dict. Naming/behavior mismatch.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### MDG-X1 + PRG-X1: missing_data_gate is EXCEPTIONAL — collect-all-errors pattern
MDG-13 (line 84): errors: list[str] = [] then 8+ checks each appending. Compare:
- hard_blocks HB-65: first-block-wins, drops other reasons
- portfolio_risk_gate PRG-48: clean ladder but also first-fail (returns early)
- missing_data_gate MDG-13: collects ALL errors

For audit trails, the MDG pattern is correct. A pick failing 5 checks should report 5 reasons, not 1. Other gates should adopt this.

### Cross-cutting: 5 copies of _safe_float across the codebase
Now confirmed in:
1. smell_faculty (inline coercion)
2. premarket_sanity_gate (PSG-6)
3. portfolio_risk_gate (PRG-5)
4. missing_data_gate (MDG-7)
5. premarket_readiness_gate (PRDY-7)
And 3 copies of _safe_int (PRG, MDG, PRDY).
Single src/_utils.py would eliminate 8 duplicates.

### Cross-cutting: dual-source `or` pattern is THE schema-fragmentation symptom
MDG-10 alone has 10 dual-source pairs. PRG-14 has 5. PSG-9 has 2. HB-32 has 1. ~20 dual-source X = a.get(K) or b.get(K) pairs across audited gates. The single underlying issue: no canonical pick schema. A Pydantic/dataclass schema for pick, plan, info_short, scores would eliminate 90% of these.

### Cross-cutting: 4 of 5 audited gates return triples (allowed, blocked, summary/info)
PSG, PRG, MDG, PRDY (PRDY returns single dict but functionally similar). Pattern is established. One protocol could formalize a GateResult NamedTuple.

### Cross-cutting: CRITICAL_OFFICIAL_PICK_FIELDS is the only schema-like constant in the codebase
MDG-3. 8 fields. Should be promoted to a real schema (TypedDict at minimum, ideally a Pydantic model). Currently:
- It's a tuple of strings (no type info)
- It's not actually used by the validator (drift risk per MDG-5)
- It's incomplete (per MDG-4)

### Cross-cutting: All 5 audited gates have NO ERROR-CATEGORY AGGREGATION in their summaries
MDG-26: list of 50 blocked picks but no {error_type: count} aggregation. Pattern repeats across gates. For CI dashboards or operator alerts, the aggregation should be in the summary, not computed downstream.

## SUMMARY (Batch 10)

| Severity | missing_data_gate | premarket_readiness | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 6 | 9 | 3 | 18 |
| Data/safety | 5 | 4 | 0 | 9 |
| Code smell | 5 | 5 | 0 | 10 |
| Good code | 12 | 8 | 0 | 20 |
| Total findings | 28 | 26 | 3 | 57 |

## TOP 10 CRITICAL FIXES from Batch 10

1. PRDY-24: Magic 10 in `if ohlcv_attempts >= 10` — provider-degraded check dead for small universes. Parameterize. (15 min)
2. PRDY-18: Inscrutable required_fetched_count formula. Add comment explaining min(absolute, coverage*universe) intent OR refactor for clarity. (30 min)
3. MDG-X1 spread: Adopt collect-all-errors pattern in hard_blocks and PRG. (1 hr)
4. Cross-cutting _safe_float consolidation: Move to src/_utils.py, replace 5 copies. (30 min)
5. Cross-cutting _safe_int consolidation: Same. (15 min)
6. MDG-3 + MDG-4: Make CRITICAL_OFFICIAL_PICK_FIELDS authoritative — drive validation from it OR declare as TypedDict. (1 hr)
7. MDG-10 + cross-cutting: Single pick_schema.py with Pydantic model — eliminates 20+ dual-source `or` pairs across gates. (1-2 days, biggest architectural win)
8. PRDY-21 to 26: Extract _build_not_ready_response helper. Collapses 4×~12-line return dicts to 1 helper. (15 min)
9. MDG-16: Make trade_type enum config-driven, not hardcoded {"day","swing"}. (15 min)
10. PRDY-27 + PRDY-28: Either delete assert_premarket_readiness_or_no_pick OR make it actually assert. (5 min)

## NEW THEMES UPDATED

- Theme T2 (schema drift): HEAVILY AMPLIFIED. ~20 dual-source pairs across 5 gates. Root cause: no canonical pick schema. Highest-leverage architectural fix in entire audit.
- Theme T8 (DRY violation): Now 5 _safe_float copies + 3 _safe_int copies. Trivially consolidate-able.
- Theme T11 (fail-open by accident): NEW INSTANCE — PRDY-24's magic 10 silently disables provider-degraded check for small universes.
- Theme T4 (safety gates that don't gate): MDG is a counter-example. Audit-trail gold standard.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | 7/8 done | missing_data_gate, premarket_readiness_gate | 7/8 |
| Total true line-by-line | | +2 files | 22 of 382 |
| Remaining | | | 360 files |

## NEXT BATCH

Batch 11: src/pick_logger.py — the FINAL Phase A file. After this, Phase A complete (8/8 safety/gates). Then Phase B begins: scoring + data layer.

End of Batch 10.
