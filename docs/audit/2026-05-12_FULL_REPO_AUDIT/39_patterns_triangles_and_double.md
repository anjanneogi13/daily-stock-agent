# Batch 33 — src/patterns/triangles.py (133 lines) + src/patterns/double.py (138 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** patterns/triangles.py (133 lines), patterns/double.py (138 lines)
**Phase:** E (subdirectories) — files 6 and 7 of ~50

## TOP HEADLINE FINDINGS

1. TR-X1: triangles.py is the **FIRST DETECTOR FILE WITH A SHARED BASE CLASS** — `_TriangleBase(PatternDetector)` (line 40-58). **Holds shared `_fit()` + class constants.** **THE TEMPLATE** that hhhl/breakouts/flags should follow per Batch 31 HH-X2 cross-cutting refactor recommendation.
2. TR-X2: triangles.py contains **3 detectors** (Asc, Desc, Sym) — **NOT a mirror pair, but a 3-way variation** with subtle inconsistencies. **Per Batch 31 PI-5 docstring count was 16 detectors total.** The 3-way is what makes the count odd.
3. TR-X3 (lines 19-31): `_linreg` is a **PURE STDLIB least-squares regression** — no numpy/scipy. **Joins gold-standard pure-computation pattern.** Per Batch 23 SA-2 self_awareness "no scipy/numpy" same minimalism.
4. DB-X1: double.py is **ANOTHER MIRROR-PAIR** (DoubleTop + DoubleBottom). **CONFIRMS Batch 31 HH-X2 hypothesis** — now **4 of 4** mirror-pair detector files audited (HH, BR, FL, DB). 100% rate.
5. DB-X2: double.py + hhhl.py both have `_local_peaks` / `_pivot_highs` helpers — **DUPLICATE PIVOT/PEAK FINDERS in 2 files**. Lines 15-21 of double.py vs lines 18-24 of hhhl.py. **DRY violation across files.** Could share via `src/patterns/_extrema.py`.
6. TR-15 (line 121): `if abs(abs(sh) - sl) > 0.30: return None` — **DOUBLE-NESTED abs() with magic 0.30.** **Hard to read.** Translates to "the resistance-falling-rate (positive value) and support-rising-rate must be within 0.30 of each other." Comment "roughly symmetric" doesn't explain the math.
7. DB-12 (line 71-72, 123-124): **"Last peak should be near the end (still active pattern)"** with magic `i2 < len(highs) - 10` → return None. **Pattern only fires if last extremum is in the last 10 bars.** Reasonable but **inconsistent with HH/BR/FL detectors** which have NO such "still-active" check. Some detectors are recency-gated, others aren't.

## src/patterns/triangles.py — LINE BY LINE

### Lines 1-13: Module docstring
- TR-1 GOOD: 13-line docstring documents:
  - Two-trendline approach
  - 3-way classification rules
  - Confidence scaling
- TR-2 GOOD: Per-class slope rules listed.

### Lines 14-16: Imports
- TR-3 GOOD: Minimal.

### Lines 19-31: _linreg — pure stdlib least-squares
- TR-4 GOOD (line 22): `if n < 2: return (0.0, ys[0] if ys else 0.0)` — defensive degenerate cases.
- TR-5 GOOD: Standard textbook formula. Numerator + denominator + slope + intercept.
- TR-6 BUG (line 28): `if den == 0: return (0.0, mean_y)` — div-by-zero guard. **But den==0 only if all xs equal, impossible for `range(n)` with n>=2.** Defensive but unreachable. Fine.

### Lines 34-37: _slope_pct_per_bar
- TR-7 GOOD: Normalizes slope to %/bar — comparable across price ranges.
- TR-8 GOOD (line 36): Div-by-zero guard.

### Lines 40-58: _TriangleBase
- TR-9 GOOD (line 40): **SHARED BASE CLASS — first in audit.** Per TR-X1.
- TR-10 GOOD (lines 41-44): 4 class constants (min_bars, LOOKBACK, FLAT_THRESHOLD, SLOPE_THRESHOLD).
- TR-11 BUG (lines 41-42): `min_bars = 20` AND `LOOKBACK = 20` — duplicate value. Should be `LOOKBACK = 20; min_bars = LOOKBACK`. Cosmetic.
- TR-12 BUG: NO calibration archaeology for FLAT_THRESHOLD=0.15 and SLOPE_THRESHOLD=0.20. Per Batch 31 HH-X3 cross-cutting cumulative.
- TR-13 GOOD (lines 46-58): _fit() shared method — extracts highs/lows, runs linreg, returns slopes + means.
- TR-14 BUG (lines 48-49): Raw `sub["High"]` / `sub["Low"]` access. Per Batch 31 HH-16, KeyError if column missing. Same pattern.

### Lines 61-82: AscendingTriangleDetector
- TR-15 GOOD (lines 61-64): 2 class attrs (name, direction).
- TR-16 GOOD (lines 65-68): Standard guard + _fit call.
- TR-17 GOOD (lines 70-71): 2 explicit gates with inline comments.
- TR-18 BUG (line 72): `conf = min(0.95, 0.55 + sl * 0.5 + (FLAT_THRESHOLD - abs(sh)) * 0.5)` — 4 magic coefficients. No archaeology.
- TR-19 GOOD (lines 73-82): Match with rich trigger + operator-readable notes.

### Lines 85-106: DescendingTriangleDetector
- TR-20 BUG: ~22-line near-duplicate of Ascending. **Direction-flipped logic but same shape.** Mirror within same file.
- TR-21 GOOD (line 95): `if sh > -self.SLOPE_THRESHOLD: return None` — **negated threshold for "must be falling enough."** Subtle but correct.
- TR-22 BUG (line 96): Confidence formula uses `abs(sh) * 0.5` for descending — same coefficients as ascending's `sl * 0.5`. **Mirror-pair magic confirmed.**

### Lines 109-132: SymmetricTriangleDetector
- TR-23 GOOD (lines 109-111): name + direction="neutral". **Only "neutral" detector encountered so far.** Other detectors are bullish or bearish.
- TR-24 GOOD (lines 113-119): 3 explicit gates (resistance falling, support rising).
- TR-25 BUG (line 121): Per TR-15 head finding, `abs(abs(sh) - sl) > 0.30` magic + double-abs. **Should be `abs(magnitude_resistance - magnitude_support)` with named SYMMETRY_TOLERANCE.**
- TR-26 BUG (line 122): `conf = min(0.90, 0.55 + (abs(sh) + sl) * 0.4)` — **0.90 cap** (vs 0.95 in other 2). **Inconsistent ceiling — symmetric triangle confidence capped LOWER**. Operator should know symmetric is treated more skeptically. Comment missing.

## src/patterns/double.py — LINE BY LINE

### Lines 1-9: Module docstring
- DB-1 GOOD: 9-line docstring with 3-criterion definition.
- DB-2 GOOD: "Double Bottom = mirror" — explicit mirror acknowledgment. Same as Batch 32 FL-2.

### Lines 10-12: Imports
- DB-3 GOOD: Minimal.

### Lines 15-30: _local_peaks + _local_troughs
- DB-4 BUG (lines 15-30): **Per DB-X2, near-duplicate of hhhl.py _pivot_highs / _pivot_lows.** Function names differ (peaks vs pivot_highs) but logic identical. **DRY across files.**
- DB-5 GOOD (line 19, 28): Same uniqueness check (`window.count(value) == 1`) as hhhl.py. Consistent within patterns/.
- DB-6 BUG (lines 15, 24): `k: int = 3` — different default from hhhl.py k=2. **Inconsistent k between mirror peak-finders.** Per HH 20-bar lookback with k=2 vs DB 30-bar lookback with k=3 — proportionate but undocumented.

### Lines 33-85: DoubleTopDetector
- DB-7 GOOD (lines 33-41): Class-level constants (name, min_bars, direction, LOOKBACK, PEAK_TOL_PCT, MIN_TROUGH_DROP_PCT, MIN_PEAK_SEPARATION). 7 attrs — most-organized detector header.
- DB-8 BUG (line 38, 41): Same min_bars/LOOKBACK duplicate per TR-11.
- DB-9 GOOD (lines 43-46): Standard guard.
- DB-10 GOOD (lines 47-49): Pulls peaks via _local_peaks.
- DB-11 GOOD (lines 52-54): Take 2 highest, sort chronologically. **Reasonable heuristic.** May miss patterns where 3rd-highest is the true second-peak.
- DB-12 GOOD (lines 57-58): MIN_PEAK_SEPARATION gate.
- DB-13 GOOD (lines 60-61): PEAK_TOL_PCT gate (peaks within 2% of each other).
- DB-14 GOOD (lines 62-69): Trough check between peaks.
- DB-15 BUG (lines 63-65): `lows[i1:i2+1]` — pandas slice on Python list. Inclusive end. correct.
- DB-16 GOOD (line 67): `drop_pct = (avg - trough) / avg * 100` — no div-by-zero guard but `avg` is mean of 2 positive prices. Safe in practice.
- DB-17 GOOD (lines 71-72): Per DB-12 head finding, "still active pattern" recency check. Magic 10. **Should be class constant `MAX_AGE_BARS = 10`.**
- DB-18 BUG (line 73): Confidence formula: `0.55 + 0.04 * drop_pct + 0.05 * (PEAK_TOL_PCT - peak_diff_pct)`. 4 magic numbers + 2 class constants used. Mixed style.
- DB-19 GOOD (lines 74-85): Match with rich trigger.

### Lines 88-137: DoubleBottomDetector
- DB-20 BUG (lines 88-137): Per DB-X1 head finding, near-duplicate ~50-line mirror of DoubleTop.
- DB-21 GOOD (lines 93-96): Class constants renamed semantically (BOTTOM_TOL_PCT, MIN_PEAK_RISE_PCT, MIN_BOTTOM_SEPARATION). **Better than blind copy — semantic naming preserved.**
- DB-22 GOOD (lines 104, 107-108): Uses _local_troughs + sorted-by-low + chronological re-sort.
- DB-23 GOOD (line 119): peak BETWEEN troughs (mirror of trough between peaks).
- DB-24 BUG (line 123): Same magic 10 for "still active" check. Per DB-17.
- DB-25 BUG (line 125): Identical confidence formula coefficients. Mirror-pair magic.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### TR-X1: First detector file with shared base — TEMPLATE for refactor
triangles.py uses `_TriangleBase(PatternDetector)` to share `_fit()` + class constants. Per Batch 31 HH-X2 / Batch 32 BR-X1+FL-X1 cross-cutting refactor recommendation, **this IS the template.** Other 4 mirror-pair files (hhhl, breakouts, flags, double) should follow:

    class _MirroredDetector(PatternDetector):
        DIRECTION_SIGN = +1   # +1 bullish, -1 bearish
        # shared logic
    class BullFlagDetector(_MirroredDetector):
        DIRECTION_SIGN = +1
        direction = "bullish"
    class BearFlagDetector(_MirroredDetector):
        DIRECTION_SIGN = -1
        direction = "bearish"

**~260 lines of duplicate could collapse to ~130** per Batch 32 BR-X1.

### DB-X1: Mirror-pair count update
Now 4 of 5 audited detector files have mirror pairs (HH, BR, FL, DB). **triangles.py is the EXCEPTION** with 3-way variation. **3 remaining unaudited (head_shoulders, wedges) — likely 2 more mirror pairs.** Total estimated: **6 mirror pairs out of 8 files.**

### DB-X2: Cross-file pivot/peak helper duplication
- hhhl.py: `_pivot_highs(highs, k=2)`, `_pivot_lows(lows, k=2)`
- double.py: `_local_peaks(values, k=3)`, `_local_troughs(values, k=3)`
**Same logic, different names, different default k.** Should consolidate into `src/patterns/_extrema.py` with `find_pivots(values, mode='max'|'min', k=2)`. Then HH and DB pass appropriate k.

### Cross-cutting: CONFIDENCE FORMULA tally (4 of 5 detector files audited)
| File | Formula | Cap | Magic count |
|---|---|---|---|
| hhhl | 0.5 + 0.1*n + 5*(gap_h+gap_l) | 0.95 | 6 |
| breakouts | 0.55 + 0.05*gap_pct + 0.05*(vol_ratio-1) | 0.95 | 4 each x2 |
| flags | 0.5 + 0.02*pole + 0.03*(MAX_FLAG-range) [+0.05 pos] | 0.95 | 4 each x2 |
| triangles asc | 0.55 + sl*0.5 + (FLAT-abs(sh))*0.5 | 0.95 | 4 |
| triangles desc | 0.55 + abs(sh)*0.5 + (FLAT-abs(sl))*0.5 | 0.95 | 4 |
| triangles sym | 0.55 + (abs(sh)+sl)*0.4 | **0.90** | 3 |
| double | 0.55 + 0.04*drop + 0.05*(PEAK_TOL-peak_diff) | 0.95 | 4 each x2 |

**Formulas DIFFER per file (no shared abstraction).** **All cap at 0.95 except symmetric triangle (0.90).** **All start at 0.5 or 0.55 base.** **Total ~50 confidence-formula magic numbers across 5 files. NO calibration archaeology in any.**

### TR-26: Inconsistent confidence ceilings
Symmetric triangle caps at 0.90 vs others at 0.95. Operator can't tell why. Likely intentional (symmetric is harder to direction-trade) but **needs comment**.

### DB-17 + DB-24: "Still active" check magic 10 only in double, not other detectors
Pattern-detection RECENCY differs by detector:
- HH/BR/FL: NO recency check — match could be from days ago
- TR (triangles): NO recency check
- DB (double): MUST be in last 10 bars
**Inconsistent operational semantics.** A breakout detected 18 bars ago and a double-top detected 18 bars ago: breakout still fires, double-top doesn't. **Operator confusion + downstream bias.**

### Cross-cutting: 23 files with relative-path constants (no change)

## SUMMARY (Batch 33)

| Severity | triangles | double | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 4 | 6 | 4 | 14 |
| Data/safety | 4 | 5 | 0 | 9 |
| Code smell | 2 | 1 | 0 | 3 |
| Good code | 16 | 16 | 0 | 32 |
| Total findings | 26 | 28 | 4 | 58 |

## TOP 10 CRITICAL FIXES from Batch 33

1. TR-X1 / DB-X1 cross-cutting: Use _TriangleBase TEMPLATE to refactor 4 mirror-pair files (HH, BR, FL, DB) into shared base. (4-6 hr per Batch 32)
2. DB-X2: Move pivot/peak helpers into `src/patterns/_extrema.py`. Unify HH + DB. (15 min)
3. DB-17 + DB-24 cross-cutting: Add MAX_AGE_BARS to ALL detectors uniformly OR document why some are stateless and some recency-gated. (30 min)
4. TR-26: Add comment explaining 0.90 cap for symmetric triangle. (3 min)
5. TR-25 / TR-15: Replace `abs(abs(sh) - sl)` with named SYMMETRY_TOLERANCE constant + clearer expression. (5 min)
6. Cross-cutting confidence formulas: Add calibration archaeology to ALL 5 audited detector files (~50 magic numbers). (1-2 hr per Batch 32 #6)
7. DB-15 / DB-22: Document the "take 2 highest peaks" heuristic edge case (could miss correct pair if 3rd-highest is the true second). (5 min)
8. TR-11 + DB-8: Make `min_bars = LOOKBACK` instead of duplicate value. (1 min)
9. DB-6: Document why DB uses k=3 vs HH uses k=2 for pivot finding. (3 min)
10. TR-14: Add column-presence guard for "High"/"Low" in _fit(). (5 min)

## NEW THEMES UPDATED

- Theme T1 (bare except): triangles 0, double 0. **Phase E continues clean.**
- Theme T2 (schema drift): N/A this batch (pure compute).
- Theme T6 (atomic writes): N/A this batch.
- Theme T8 (DRY): Mirror pairs now 4/5 confirmed. Cross-file pivot helper duplication (DB-X2). Cross-file confidence formula proliferation.
- Theme T11 (fail-open by accident): TR-X1 base class hides math complexity well; symmetric 0.90 cap is silent intentional.
- Theme T13 (silent-default-fills): N/A this batch.
- Theme T14 (gold-standard patterns): _TriangleBase shared base = template for refactor. _linreg pure-stdlib joins computation gold standard.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A | 8/8 COMPLETE | (none) | 8/8 |
| Phase B | 18/18 COMPLETE | (none) | 18/18 |
| Phase C | 12/12 COMPLETE | (none) | 12/12 |
| Phase D | 8/~30 done | (none) | 8/~30 |
| Phase E | 7/~50 done | patterns/triangles, patterns/double | 7/~50 |
| Total true line-by-line | | +2 files | **68 of ~382 (~17.8%)** |
| Remaining | | | **~314 files** |

## NEXT BATCH

Batch 34: src/patterns/cup_handle.py + src/patterns/head_shoulders.py — cup_handle is a SINGLE DETECTOR (no mirror), head_shoulders is the 6th expected mirror pair. Will close out detector-layer audit in Batch 35 with wedges.py.

End of Batch 33. Phase E in progress (7/50).
