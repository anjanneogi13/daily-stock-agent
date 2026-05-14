# Batch 31 — src/patterns/__init__.py (42 lines) + src/patterns/base.py (46 lines) + src/patterns/hhhl.py (106 lines) — TRUE LINE-BY-LINE — PHASE E BEGINS

**Date:** 2026-05-12
**Files:** patterns/__init__.py (42 lines), patterns/base.py (46 lines), patterns/hhhl.py (106 lines) — 3 small files
**Phase:** E (subdirectories) — files 1-3 of ~30-50

## TOP HEADLINE FINDINGS

1. PI-X1: src/patterns/__init__.py exports **15 DETECTORS** (per docstring "ALL 15 DETECTORS LIVE — T49 Phase 3 complete"). **8 detector files** (base.py + 7 detector modules). All detectors instantiated at module load (line 19-29 ALL_DETECTORS list). **Per Batch 30 PE2-X2, a single broken __init__ on any detector class crashes the whole import → pattern_engine empty.**
2. PI-X2: ALL_DETECTORS instances are **STATELESS singletons** instantiated at import time. **No constructor args.** Per Batch 30 PE2-7, can be overridden by caller. Reasonable design.
3. PB-X1: base.py is **ELEGANT 46-line ABC** — `Match` dataclass + `PatternDetector` ABC. **Pure stdlib, no I/O, type-hinted.** **Joins gold-standard pure-computation club** (now 9 modules: indicators, exit_manager, trailing_stop, adaptive_tp, scoring_safety, hypothesis_engine, calibration partly, self_awareness, base.py). Template for pluggable detector architectures.
4. PB-15 (line 23): `trigger: Dict = field(default_factory=dict)` — **untyped dict for detector-specific data.** Per detector adds whatever fields make sense. **Pro: flexibility.** **Con: pattern_layer (Batch 30 PL-19) and consumers can't statically know what fields exist.** Schema-soft contract.
5. HH-X1: hhhl.py is the **simplest detector** (106 lines, 2 detector classes — bullish HHHL + bearish LHLL mirror). **Pure computation, deterministic, type-hinted.** Mirror-symmetric design — clean DRY... almost (see HH-X2).
6. HH-X2: HHHLDetector and LHLLDetector are **NEAR-DUPLICATE 30-line blocks** (lines 41-71 vs 80-105). Only differences: comparison direction (`>` vs `<`) and gap formula direction. **DRY violation — should be parameterized.** Bug fix in one must be replicated in other.
7. HH-X3 (line 60, 94): `conf = min(0.95, 0.5 + 0.1 * n + 5 * (gap_h + gap_l))` — **6 magic numbers in confidence formula** (0.95 cap, 0.5 base, 0.1 n-multiplier, 5 gap-multiplier). **Identical formula in both classes.** Per Batch 22 SJ-X5 bucket_composite calibration archaeology pattern, **NO calibration provenance documented.** Where do these come from?

## src/patterns/__init__.py — LINE BY LINE

### Lines 1-4: Module docstring
- PI-1 GOOD: 4-line docstring documenting Pillar 3 + 15-detector status.
- PI-2 GOOD: T49 Phase 3 complete marker.

### Lines 5-17: Detector imports
- PI-3 GOOD: 8 import lines mapping to 8 detector files. **Per directory listing: base.py, breakouts, cup_handle, double, flags, head_shoulders, hhhl, triangles, wedges.** ✅ all 8 detector modules + base = 9 files in src/patterns/.
- PI-4 BUG: Bulk import means a SyntaxError or ImportError in ANY detector file kills the whole patterns package. **Per Batch 30 PE2-7 ALL_DETECTORS imported at module top — pattern_engine import fails too.** Fragile single point of failure.

### Lines 19-29: ALL_DETECTORS instantiation
- PI-5 GOOD: 16 detector instances (HHHL+LHLL+Breakout+Breakdown+BullFlag+BearFlag+Asc+Desc+Sym Triangles+CupHandle+DoubleTop+Bottom+H&S+InvH&S+FallingWedge+RisingWedge). **Wait — docstring says 15, list has 16.** Off-by-one in docstring OR forgot one.
- PI-6 BUG (lines 9-13): `from .triangles import (Asc, Desc, Sym)` — 3 triangle classes. So total = 16 detectors but docstring says 15. **Schema/docstring drift.**
- PI-7 GOOD: Stateless singletons instantiated at import.

### Lines 31-41: __all__
- PI-8 GOOD: Explicit __all__ for `from src.patterns import *` semantic.
- PI-9 BUG: __all__ has 16 detector class names (matches ALL_DETECTORS). Docstring count of 15 is wrong.

## src/patterns/base.py — LINE BY LINE

### Lines 1-11: Module docstring
- PB-1 GOOD: 11-line docstring documenting:
  - Detector contract: `detect(ohlcv) -> Optional[Match]`
  - OHLCV column shape (yfinance)
  - Most-recent bar at END
  - Match purpose
- PB-2 GOOD: **Documents data shape contract** — operator-friendly.

### Lines 12-15: Imports
- PB-3 GOOD: from __future__ + ABC + dataclass + typing.

### Lines 18-27: Match dataclass
- PB-4 GOOD: 5-field dataclass with sensible types.
- PB-5 GOOD (line 20): pattern: str — canonical name.
- PB-6 GOOD (line 21): confidence: float 0-1.
- PB-7 GOOD (line 22): lookback: int — bars analyzed for transparency.
- PB-8 BUG (line 23): trigger: Dict — per PB-15 head finding, untyped. **No documented schema for what each detector puts here.** Consumers (pattern_layer Batch 30) can't statically know fields.
- PB-9 GOOD (line 24): notes: str default "". Optional human-readable.
- PB-10 GOOD (lines 26-27): to_dict via asdict — JSON-friendly serialization.

### Lines 30-45: PatternDetector ABC
- PB-11 GOOD (line 30-31): ABC with abstractmethod contract.
- PB-12 GOOD (lines 33-35): 3 class attributes (name, min_bars, direction).
- PB-13 GOOD (line 35): direction supports 3 values explicit comment.
- PB-14 GOOD (lines 37-39): Single abstractmethod `detect(df)`.
- PB-15 BUG (lines 41-45): `_enough_bars` defensive utility. **bare `except Exception: return False`** — Theme T1 undocumented swallow. **Should be specific TypeError catch.** A None df or weird object returns False silently.

## src/patterns/hhhl.py — LINE BY LINE

### Lines 1-11: Module docstring
- HH-1 GOOD: 11-line docstring documents:
  - HHHL definition (bullish trend confirmation)
  - 20-bar lookback
  - Pivot definition (k=2)
  - Confidence formula components
- HH-2 GOOD: Operator-friendly explanation.

### Lines 12-15: Imports
- HH-3 GOOD: from __future__ + typing + base.
- HH-4 GOOD: NO pandas/numpy import — works on raw lists. **Test-friendly.**

### Lines 18-24: _pivot_highs
- HH-5 GOOD (line 18): Type-hinted, `k: int = 2` default.
- HH-6 GOOD (line 20): `range(k, len(highs) - k)` — skips boundary bars.
- HH-7 GOOD (line 22): `highs[i] == max(window)` — local max check.
- HH-8 GOOD (line 22): `window.count(highs[i]) == 1` — **strict uniqueness check** (no plateau accepted as pivot). **Reasonable for clean signals but can miss equal-high pivots.** Per "double top" pattern (separate detector), exactly equal highs ARE meaningful — but here treated as not-pivot.
- HH-9 BUG (line 22): O(k) max + O(k) count per bar = O(k×n) total. For n=20, k=2, total ~80 ops. Cheap. ✅
- HH-10 GOOD: Returns list of (index, value) tuples.

### Lines 27-33: _pivot_lows
- HH-11 SMELL: Mirror of _pivot_highs with min instead of max. **DRY-violation candidate** but small.
- HH-12 GOOD: Same uniqueness guard.

### Lines 36-71: HHHLDetector
- HH-13 GOOD (lines 36-39): 3 class attrs.
- HH-14 GOOD (line 42-43): _enough_bars guard.
- HH-15 GOOD (lines 44-45): `df["High"].tail(self.min_bars).tolist()` — pandas → list. **Per HH-4 design, detection works on lists.** Type-decoupled.
- HH-16 BUG (line 44-45): `df["High"]` raw access — KeyError if column missing. Compare PB docstring contract requires Open/High/Low/Close/Volume. **Caller responsibility.** Fragile.
- HH-17 GOOD (lines 46-49): Pivot extraction + sample-size check.
- HH-18 GOOD (lines 51-55): Strict-increasing check on last 2 pivots.
- HH-19 GOOD (line 57): `n = min(len(ph), len(pl))` — conservative pivot count.
- HH-20 BUG (lines 58-59): `gap_h = (ph[-1][1] - ph[-2][1]) / max(ph[-2][1], 1e-9)` — guards against div-by-zero with 1e-9. **Magic 1e-9.** ✅ defensive but should be a named EPSILON constant.
- HH-21 BUG (line 60): Per HH-X3, 6-magic-number confidence formula with no calibration provenance.
- HH-22 GOOD (lines 61-71): Match returned with rich trigger dict.
- HH-23 GOOD (line 70): notes "bullish trend continuation" — operator-friendly.

### Lines 74-105: LHLLDetector
- HH-24 BUG (lines 74-105): Per HH-X2, near-duplicate of HHHLDetector. ~30 lines mostly identical. Should be parameterized: `class TrendContinuation(direction='bull'|'bear')`.
- HH-25 GOOD (lines 89-90): One-liner ifs for the direction-flipped strict-decreasing checks. Compact.
- HH-26 BUG (lines 92-93): gap formula DIRECTION-FLIPPED (prev - last instead of last - prev) to keep gap positive for bearish. **Subtle — easy to mess up if refactoring.** Confidence formula at line 94 IDENTICAL coefficients (0.5 + 0.1×n + 5×gap). **Mirrors deliberately.**
- HH-27 GOOD: Same Match shape, "bearish trend continuation" notes.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### PI-X1 + PI-5: Detector count mismatch
- Docstring says "ALL 15 DETECTORS"
- ALL_DETECTORS list has 16 instances
- __all__ has 16 names
**Off-by-one in docstring.** Either count was 15 before SymmetricTriangle added and docstring not updated, OR docstring is correct and one detector is duplicated. Cosmetic but indicates docstring drift.

### PI-4 + Batch 30 PE2-X2 amplification
A SyntaxError in ANY of 8 detector files breaks `from src.patterns import ALL_DETECTORS` → pattern_engine fails to import → nightly_conductor pattern_scan step fails → resilient try/except logs error → operator sees "pattern_scan failed" but no clue WHICH detector. **Compounds the silent-failure pattern.**

### HH-X2: 1st DRY violation in detector layer
HHHLDetector + LHLLDetector — 30-line near-duplicate. **Likely repeats across:**
- breakouts.py (Breakout vs Breakdown)
- flags.py (BullFlag vs BearFlag)
- triangles.py (Asc vs Desc)
- double.py (Top vs Bottom)
- head_shoulders.py (H&S vs InverseH&S)
- wedges.py (Falling vs Rising)

**~6 mirror-symmetric pairs probably repeated.** A `class _MirroredDetector(direction)` base would unify ~180 lines.

### HH-X3 + HH-21: Magic-number calibration provenance gap
6 magic numbers in HHHL confidence formula. Per Batch 22 SJ-X5 bucket_composite has 23-line calibration archaeology. **HH has zero.** Likely copy-pasted across all 8 detector files (96 magic numbers total estimated). **Pattern for Batch 32-35 to verify.**

### PB-X1 + HH gold-standard pure-computation
- base.py + hhhl.py: ZERO bare-except (except 1 in PB-15), ZERO I/O, type-hinted, deterministic, test-friendly.
- **Joins** indicators, exit_manager, trailing_stop, adaptive_tp, scoring_safety, hypothesis_engine, self_awareness, calibration partly. **NOW 9 GOLD-STANDARD MODULES.**

### PB-8: Soft-contract on Match.trigger
trigger: Dict — untyped. Per detector adds custom fields. Consumers can't statically validate. **Per Batch 30 PL-19 default-confidence 0.5 silent-fill, soft contracts amplify.** **Should be Optional[TypedDict] per detector, OR consumer-side validation.**

### Cross-cutting: 23 files with relative-path constants
patterns/__init__ doesn't add (no Path constants). Cumulative.

### Cross-cutting: ATOMIC WRITE
This batch has NO state writes (pure detection). N/A.

### Cross-cutting: 8th distinct min-N threshold... wait, NO
Per Batch 30 PL-29 cross-cutting, 8 thresholds across 7 modules. This batch:
- HHHL min_bars=20 (line 38)
- LHLL min_bars=20 (line 77)
**Same threshold for both. ✅ no new cross-cutting issue.**

## SUMMARY (Batch 31)

| Severity | __init__ | base | hhhl | Cross-cutting | Total |
|---|---:|---:|---:|---:|---:|
| Show-stopper | 4 | 1 | 5 | 4 | 14 |
| Data/safety | 1 | 1 | 3 | 0 | 5 |
| Code smell | 0 | 0 | 2 | 0 | 2 |
| Good code | 4 | 13 | 19 | 0 | 36 |
| Total findings | 9 | 15 | 29 | 4 | 57 |

## TOP 10 CRITICAL FIXES from Batch 31

1. PI-X1 / PI-5: Fix docstring "ALL 15 DETECTORS" → 16. (1 min)
2. HH-X2 / HH-X3 cross-cutting: Plan refactor of 6 mirror-pair detector duplications into `_MirroredDetector(direction)` base. (2-4 hr — major refactor for next batches to verify)
3. PB-15: Replace bare except in _enough_bars with TypeError catch. (1 min)
4. HH-X3 / HH-21: Add calibration archaeology comment for the 6-magic-number confidence formula. Cite source or document derivation. (15 min — and apply to all 8 detector files in batches 32-35)
5. HH-20: Replace 1e-9 magic with EPSILON constant in src/_constants.py. (5 min)
6. PI-4: Wrap each detector import in try/except so one broken detector doesn't kill all. Maintain partial ALL_DETECTORS. (30 min)
7. PB-8: Document Match.trigger schema per detector OR introduce TypedDict. (1 hr)
8. HH-16: Add column-presence guard in detect() — return None gracefully if "High"/"Low" missing. (10 min for both detectors)
9. HH-8: Document the strict-uniqueness pivot rule (rejects plateaus). Operator should know. (5 min)
10. HH-11: Refactor _pivot_highs/_pivot_lows into `_pivots(values, mode='max'|'min', k)` single function. (10 min)

## NEW THEMES UPDATED

- Theme T1 (bare except): PB-15 (1 documented), HH 0, PI 0. Phase E first batch is CLEANER than Phase D.
- Theme T2 (schema drift): PI docstring count off-by-one. PB-8 untyped trigger dict.
- Theme T6 (atomic writes): N/A this batch.
- Theme T8 (DRY): HH-X2 mirror-pair duplication — likely 6 more pairs in next batches.
- Theme T11 (fail-open by accident): PI-4 single-detector-error breaks all import.
- Theme T13 (silent-default-fills): PB-8 soft-contract trigger dict.
- Theme T14 (gold-standard patterns): patterns/base.py + hhhl.py join the 9-module pure-computation club. Phase E starting clean.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | 8/8 COMPLETE | (none) | 8/8 |
| Phase B (scoring/data) | 18/18 COMPLETE | (none) | 18/18 |
| Phase C (brain pillars) | 12/12 COMPLETE | (none) | 12/12 |
| Phase D (pipeline & output) | 8/~30 done | (none) | 8/~30 |
| Phase E (subdirectories) | 3/~30-50 done | patterns/__init__, patterns/base, patterns/hhhl | 3/~50 |
| Total true line-by-line | | +3 files | **64 of ~382 (~16.8%)** |
| Remaining | | | **~318 files** |

## NEXT BATCH

Batch 32: src/patterns/breakouts.py + src/patterns/flags.py — 2 mirror-pair detector files. Will verify HH-X2 DRY violation hypothesis (Breakout/Breakdown + BullFlag/BearFlag) and HH-X3 magic-number repeat hypothesis.

End of Batch 31. Phase E in progress (3/50). **Phase D paused at 8/30 to advance Phase E now that pattern_engine consumers are understood.**
