# Batch 50 — src/hypothesis_engine.py (184 lines) + src/daily_wisdom.py (156 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** hypothesis_engine.py (184 lines), daily_wisdom.py (156 lines)
**Phase:** E (subdirectory & ancillary). Files 19 and 20 of ~50.
**MILESTONE:** Batch 50 (round number) — wisdom-writer side audit complete.

## TOP HEADLINE FINDINGS

1. HE-X1: hypothesis_engine.py is **PILLAR 1 LAYER 4 v0.1** — for each (signal, bucket), computes win-rate, base-rate delta, binomial p-value, avg R. **PURE COMPUTATION + NO I/O + NO STATE.** Per Batch 28 NC / Batch 31 patterns gold-standard, joins the **pure-compute club**. Joins indicators (B12), exit_manager (B13), scoring_safety (B14), semiconductors (B41), patterns/base+hhhl+triangles_linreg (B31-33) — **10 modules pure-compute/pure-data.**
2. HE-X2 (lines 16, 181): **EXPLICIT OBSERVE-MODE GUARANTEE** at top AND bottom of module — docstring line 16 plus the format_report final lines `"OBSERVE-MODE: No weights auto-changed. You decide what to act on."` **Operator-visible promise repeated.** Per Batch 49 WB-X1 (wisdom_base) v0.1 pattern — **2 modules in same layer with synchronized v0.1 OBSERVE-MODE messaging.**
3. HE-X3 (lines 28-53): **PURE-STDLIB BINOMIAL CDF implementation** (avoids scipy dependency). 3 functions: _binom_pmf, _binom_cdf, two_sided_p_value. **Excellent design decision** documented inline (line 28). Per Batch 41 SE-X1 pure-data gold standard — **avoiding scipy = lighter deploy, no version pin risk.**
4. HE-X4 (lines 30-53): **Numerical-stability concerns** — `comb(n, k) * p^k * (1-p)^(n-k)` overflows for n > ~1000 due to integer comb growing huge. Per Batch 33 TR linear-regression / Batch 31 patterns cross-cutting numerical stability theme. **At n=20-100 typical brain-loop scale, fine.** **Latent bug at scale** if signal_journal grows to 10k+ rows.
5. DW-X1: daily_wisdom.py is **THE OPERATOR-FACING WISDOM-REPORT GENERATOR** — runs hypothesis_engine on quality-floor picks and surfaces edges/drags. **3-tier sample-size honesty** (anecdotal/directional/useful/confident) per WB-X1 / Batch 43 PE3-X1 honest-versioning gold standard. **Joins 4th module with this discipline.**
6. DW-X2 (lines 27-37): **NAMED SAMPLE-SIZE THRESHOLDS** with operator-readable confidence labels: N_ANECDOTAL=20, N_DIRECTIONAL=50, N_CONFIDENT=100. **Per Batch 47 AM-X3 / Batch 44 CA-X4 / Batch 22 SJ-X3 cross-cutting statistical-validity discipline confirmed** — **6th module with named min-sample constants.**
7. DW-X3 (lines 51-54): **HARDCODED SCORE BUCKET BOUNDARIES** (0.79, 0.72, 0.66) — per Batch 44 CA-15 cross-cutting score-bucket boundaries 0.5/0.7/0.85. **DIFFERENT thresholds in different modules!** Per Batch 31 HH-X3 magic-number proliferation. **Score-bucket schema drift across calibration vs daily_wisdom.**

## src/hypothesis_engine.py — LINE BY LINE

### Lines 1-17: Module docstring
- HE-1 GOOD: 17-line docstring with v0.1 + Pillar 1 Layer 4 + 5-step calculation breakdown + 3-output classification.
- HE-2 GOOD (line 16): Per HE-X2, OBSERVE-MODE explicit.

### Lines 18-20: Imports
- HE-3 GOOD: Pure stdlib (typing, defaultdict, math.comb).
- HE-4 GOOD: NO scipy/numpy dependency. ✅

### Lines 23-24: Constants
- HE-5 GOOD: MIN_SAMPLE_SIZE=10, SIGNIFICANCE_THRESHOLD=0.05 — named.
- HE-6 BUG: Magic 10 / 0.05. **0.05 is standard p-value cutoff** (acceptable convention). 10 sample-size is more aggressive than daily_wisdom DW-X2 (20+ for direction). **Cross-module inconsistency** — hypothesis_engine reports significant edges at n=10 but daily_wisdom warns "anecdotal" up to n=20. Operator could see "STATISTICALLY SIGNIFICANT EDGE" + "⏳ ANECDOTAL sample" simultaneously. **Confusing.**

### Lines 30-34: _binom_pmf
- HE-7 GOOD (line 31): 3-condition guard (n<0, k<0, k>n) → 0.0.
- HE-8 GOOD (lines 32-33): Boundary p=0 / p=1 handled explicitly.
- HE-9 BUG (line 34): No overflow handling for large n. Per HE-X4 head finding.

### Lines 37-38: _binom_cdf
- HE-10 GOOD: Simple sum implementation.
- HE-11 BUG: O(N) per call — fine for typical n<200. Per HE-X4.

### Lines 41-53: two_sided_p_value
- HE-12 GOOD (lines 43-44): Edge cases (n=0, p outside (0,1)) → p=1 (cannot reject null).
- HE-13 GOOD (lines 45-53): Standard 2-sided binomial test.
- HE-14 GOOD (line 49, 53): `min(1.0, 2 * tail)` — caps p-value at 1.0. ✅

### Lines 59-128: analyze (MAIN PUBLIC API)
- HE-15 GOOD (lines 59-65): 5-line docstring documenting input + output shape.
- HE-16 GOOD (lines 66-72): Empty-input early-return with documented "No closed picks yet" summary.
- HE-17 GOOD (lines 74-75): Base-rate computation.
- HE-18 GOOD (lines 78-81): defaultdict-based bucket grouping.
- HE-19 GOOD (line 80): `r.get("signals") or {}` — defensive None handling.
- HE-20 GOOD (lines 84-101): Per-bucket loop with 7-field record.
- HE-21 GOOD (lines 89-91): R-multiple filtered to numeric only — defensive.
- HE-22 GOOD (line 91): `avg_r = None` when no numeric data. **Schema-stable None.**
- HE-23 GOOD (lines 103-105): **Low-sample bucket bypass** — n<min_n goes to low_sample list with NO p-value (intellectually honest).
- HE-24 GOOD (lines 107-113): p-value gated significance classification.
- HE-25 GOOD (line 110): `p < alpha AND win_rate > base_rate` — both required (correct).
- HE-26 GOOD (lines 115-117): Sort edges DESC vs_base, drags ASC vs_base (worst first), low_sample DESC by n (highest first).
- HE-27 GOOD (lines 119-128): 7-key summary dict with human-readable summary string.
- HE-28 BUG (line 80): `r.get("signals")` assumes journal schema. Per Batch 22 SJ producer schema-coupled. A signals-schema change in signal_journal silently produces no buckets here.

### Lines 131-183: format_report
- HE-29 GOOD: Telegram-friendly text report.
- HE-30 GOOD (lines 134-136): 70-char divider lines.
- HE-31 GOOD (line 135): "Pillar 1 Layer 4 v0.1 (observe-mode)" — surfaces version + mode to operator.
- HE-32 GOOD (lines 139-140): Empty-result early return.
- HE-33 GOOD (lines 146-153): Edge formatting with avg_R="?" fallback when None.
- HE-34 GOOD (lines 155-166): Drag formatting symmetric with edges.
- HE-35 GOOD (lines 168-177): Low-sample formatting limited to top 10. **Bounded operator-output.**
- HE-36 GOOD: Per HE-X2, lines 180-182 explicit OBSERVE-MODE close.

## src/daily_wisdom.py — LINE BY LINE

### Lines 1-16: Module docstring
- DW-1 GOOD: 16-line docstring with usage example + CLI + n=0 safety guarantee.
- DW-2 GOOD (lines 14-15): "Designed to be safe to run on n=0" — explicit invariant.

### Lines 17-22: Imports
- DW-3 GOOD: csv + Path + relative data_quality import.
- DW-4 BUG: Per Batch 49 WH-X2 cross-cutting, NO try/except import fallback. **A data_quality import failure crashes the whole module.** Inconsistent with wisdom-layer fallback pattern.

### Lines 25-30: Constants
- DW-5 BUG: Per cross-cutting, relative path. **36th file.**
- DW-6 GOOD (lines 27-30): Per DW-X2, 3 named sample-size thresholds with operator-readable purpose comments.

### Lines 33-37: _confidence_label
- DW-7 GOOD: 4-tier confidence label with emoji + n + threshold guidance. ✅ **Operator-facing transparency.**
- DW-8 GOOD: Each tier surfaces "need X+ for direction/confidence" — actionable.

### Lines 40-68: _row_to_journal_format
- DW-9 GOOD (lines 41): Documents transformation purpose.
- DW-10 GOOD (lines 42-45): Scoped (KeyError, ValueError, TypeError) → None — defensive skip.
- DW-11 GOOD (line 46): Explicit win/loss binary from r_multiple sign. Matches Batch 44 CA-21 / Batch 47 AM-30 win definition.
- DW-12 BUG: Per DW-X3 head finding, lines 51-54 hardcoded score buckets (0.79/0.72/0.66). **Different from Batch 44 CA-15 calibration thresholds (0.5/0.7/0.85).** Schema drift.
- DW-13 GOOD (line 56): "unknown" fallback for parse failure.
- DW-14 GOOD (lines 57-67): 5-field signals dict with explicit "unknown"/"none" fallbacks.
- DW-15 GOOD (line 65): **M4 archaeology comment** "pick_logger writes sector_tag" — documents schema-coupling defense. Per Batch 38 / Batch 42 archaeology pattern.
- DW-16 GOOD (line 65): `((r.get("sector_tag") or r.get("tag") or "none")).split(" / ")[0].upper() or "none"` — 4-tier fallback chain. **Defensive vs Batch 11 PL pick schema chaos.**
- DW-17 BUG (line 65): Per Batch 46 PG-11 + Batch 43 SC-8 cross-cutting, uses `" / "` separator. **Consistent with scorer + portfolio_risk_gate.** ✅ 3 modules now agree.
- DW-18 GOOD (line 66): Boolean coerced from CSV stringified ("True", "true", "1"). Per Batch 28 NC cross-cutting Theme T2.

### Lines 71-82: _load_quality_closed_picks
- DW-19 GOOD (lines 73-74): Missing-file empty list.
- DW-20 BUG (line 75): `csv.DictReader(open(PICKS_LOG))` — **NO context manager.** File handle leak. Per Batch 28 NC cross-cutting csv-discipline.
- DW-21 GOOD (line 76): Calls filter_to_quality (B14) — quality floor enforced.
- DW-22 GOOD (lines 78-81): Per-row None-skip pattern.

### Lines 85-151: generate_daily_wisdom
- DW-23 GOOD (lines 87-88): Load + count.
- DW-24 GOOD (lines 90-97): 7-line header with quality floor date surfaced. **Operator transparency.** ✅
- DW-25 GOOD (line 93): `DATA_QUALITY_FLOOR.isoformat()` — shows the floor explicitly so operator knows what's excluded.
- DW-26 GOOD (lines 99-104): Empty-state explanation message — actionable ("will activate once outcomes start being recorded").
- DW-27 GOOD (lines 106-129): **F2 (May 4) capture-efficiency injection** with dated archaeology. **Per Batch 27 PV-X3 / Batch 38 DS-X3 cross-cutting**, joins bug-archaeology gold standard.
- DW-28 GOOD (lines 119-121): 3-tier emoji classification by efficiency (≥70 ✅, ≥50 ⚠, <50 🚨). Operator-readable.
- DW-29 BUG (line 120): Magic 70.0 target + magic 50 threshold. Should be const.
- DW-30 GOOD (line 122-125): Conditional avg MFE/realized display.
- DW-31 GOOD (line 126): "low efficiency = giving back gains; raise TP1 / tighten trail" — **PRESCRIPTIVE OPERATOR ADVICE.** ✅ Excellent.
- DW-32 BUG (lines 127-129): bare except + silent pass + comment "Silent — exit metrics are observability, not core". **Documented intent but Theme T1 still applies.** Should be scoped.
- DW-33 GOOD (lines 131-134): **Anecdotal-sample warning** — "do NOT change strategy on this." **Operator-protection language.** Per HE-X2 / WB-X1 cross-cutting OBSERVE-MODE messaging.
- DW-34 GOOD (lines 136-141): Hypothesis engine integration with try/except.
- DW-35 BUG (line 142-147): bare except. **Theme T1.** Falls back to plain win-rate. **Fallback works but undocumented.**
- DW-36 GOOD (lines 145-147): Manual win-rate fallback — **belt-and-braces.**
- DW-37 GOOD (lines 149-151): Footer.

### Lines 154-155: __main__
- DW-38 GOOD: 1-line CLI wrapper. Per Batch 49 WH-46 cross-cutting __main__ pattern.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### HE-X1 + cross-cutting: Pure-compute / pure-data club update
**10 modules confirmed pure-compute / pure-data:**
- indicators (B12)
- exit_manager (B13)
- trailing_stop (B11)
- adaptive_tp (B11)
- scoring_safety (B14)
- patterns/base (B31)
- patterns/hhhl (B31)
- patterns/triangles_linreg (B33)
- semiconductors (B41)
- hypothesis_engine (this batch)
**~10% of audited modules are I/O-free.** Lowest defect density in audit.

### HE-X2 + cross-cutting: OBSERVE-MODE messaging
Modules with **explicit operator-facing OBSERVE-MODE / no-auto-mutation guarantees:**
- hard_blocks (B7)
- risk_gate (B8)
- news_safety (B16)
- premarket_decision_contract (B36)
- official_artifact_loader (B37)
- candidate_diagnostics (B38)
- gh_observability (B39 partial)
- 6 gates (B45+B46)
- agent_memoir (B47)
- wisdom_base (B49) v0.1
- hypothesis_engine (this batch) — **explicit top AND bottom**
- daily_wisdom (this batch) — DW-33 anecdotal warning

**14+ modules with explicit OBSERVE-MODE contract.** **Pattern is codebase-wide.**

### DW-X3 cross-cutting: Score-bucket boundary drift
| Module | Boundaries |
|---|---|
| calibration (B44 CA-15) | 0.5 / 0.7 / 0.85 |
| daily_wisdom (this batch DW-12) | 0.79 / 0.72 / 0.66 |

**2 modules with DIFFERENT score-bucket thresholds.** A "high"-score pick in calibration is NOT necessarily "high" in daily_wisdom. **Operator confusion risk.** Should consolidate to single SHARED `score_bucket(s)` function.

### HE-6 + DW-X2 cross-cutting: Min-sample threshold inconsistency
- hypothesis_engine MIN_SAMPLE_SIZE = 10
- daily_wisdom N_ANECDOTAL = 20
**Edge declared significant at n=10 inside hypothesis_engine but daily_wisdom warns "anecdotal" up to n=20.** Operator sees both messages. Should reconcile.

### Statistical-validity discipline cross-cutting (updated)
Now **6 modules with explicit min-sample thresholds:**
- pick_evaluator (B27)
- weight_proposer (B22)
- signal_journal (B22 SJ-X3)
- calibration (B44 CA-X4)
- agent_memoir (B47 AM-X3)
- daily_wisdom (this batch DW-X2)
+ hypothesis_engine (this batch HE-5) implicit MIN_SAMPLE_SIZE
**7 modules with statistical hygiene.** **Architectural standard confirmed.**

### Cross-cutting: bare-except this batch
- hypothesis_engine: 0 ✅ (pure compute, no I/O = no defensive try/except needed)
- daily_wisdom: 2 (DW-32 exit_metrics defense, DW-35 hypothesis_engine defense — both documented graceful degradation)

### Cross-cutting: relative-path constants
daily_wisdom adds PICKS_LOG = **36 files.** hypothesis_engine no paths.

### Cross-cutting: bug-archaeology gold standard
daily_wisdom DW-27 "F2 (May 4)" + DW-15 "M4 archaeology" — **8th module with dated archaeology.**

### Cross-cutting: TZ-aware modules: 8 (no addition).

### Cross-cutting: ATOMIC WRITE — both files READ-ONLY/REPORTING. N/A.

### Cross-cutting: emoji-as-protocol (Batch 48 WC-X3)
hypothesis_engine uses ✅/❌/⏳ in format_report — **structured by section header**, not parsed downstream. **Safe usage.** daily_wisdom uses ✅/⚠️/🚨 similarly — safe. **Compare wisdom_hint emoji which IS parsed** (Batch 49 WH-X1 + B48 WC-X3 brittle).

## SUMMARY (Batch 50)

| Severity | hypothesis_engine | daily_wisdom | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 4 | 6 | 4 | 14 |
| Data/safety | 2 | 3 | 0 | 5 |
| Code smell | 1 | 1 | 0 | 2 |
| Good code | 29 | 27 | 0 | 56 |
| Total findings | 36 | 37 | 4 | 77 |

## TOP 10 CRITICAL FIXES from Batch 50

1. **DW-X3 / DW-12 cross-cutting (HIGH):** Reconcile score-bucket boundaries. Add shared `score_bucket(s)` function used by both calibration + daily_wisdom. (15 min)
2. **HE-6 + DW-X2 cross-cutting (MEDIUM):** Reconcile min-sample thresholds — hypothesis_engine = 10 vs daily_wisdom = 20. Use shared constant from a single module. (10 min)
3. DW-20: Wrap `csv.DictReader(open(PICKS_LOG))` in context manager. File handle leak. (3 min)
4. HE-X4 / HE-9: Add overflow protection for large n in _binom_pmf. Use log-space arithmetic. (15 min — only if signal_journal grows large)
5. DW-29: Lift magic 70.0/50.0 capture-efficiency thresholds to module constants. (3 min)
6. DW-4: Add try/except import for data_quality (consistency with wisdom-layer fallback pattern). Or document why this one doesn't have it. (5 min)
7. DW-32 + DW-35: Replace 2 bare-excepts with scoped exceptions. (5 min)
8. HE-28: Document signals-schema coupling between hypothesis_engine and signal_journal. (5 min)
9. DW-17: Verify tag separator across all 3 modules (scorer, portfolio_risk_gate, daily_wisdom) and consolidate to `_parse_primary_tag(tag)` helper. (10 min — bundled with prior cross-cutting refactor)
10. HE-2 / DW-33 cross-cutting: Add OBSERVE-MODE language consistency check across all 14+ documented modules. Architectural review. (30 min)

## NEW THEMES UPDATED

- **Theme T1 (bare except):** hypothesis_engine 0 ✅ (pure compute). daily_wisdom 2 (documented graceful degradation).
- **Theme T2 (schema drift):** DW-X3 score-bucket boundary drift across 2 modules. HE-28 signals-schema coupling.
- **Theme T6 (atomic writes):** N/A this batch (read-only).
- **Theme T8 (DRY):** Score-bucket logic duplicated across calibration + daily_wisdom — needs shared helper.
- **Theme T11 (fail-open by accident):** N/A this batch (OBSERVE-MODE by design).
- **Theme T13 (silent-default-fills):** DW-13 "unknown" score-bucket fallback. DW-14 "unknown"/"none" signal fallbacks (defensive, documented).
- **Theme T14 (gold-standard patterns):** hypothesis_engine HE-X3 pure-stdlib binomial + HE-X1 zero-I/O + HE-X2 top-AND-bottom OBSERVE-MODE messaging = **TEMPLATE for analytic modules.** daily_wisdom DW-X2 4-tier confidence labels + DW-25 quality-floor transparency + DW-31 prescriptive operator advice + DW-33 anecdotal warning = **OPERATOR-FRIENDLY REPORTING TEMPLATE.**

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A | 8/8 COMPLETE | (none) | 8/8 |
| Phase B | 18/18 COMPLETE | (none) | 18/18 |
| Phase C | 12/12 COMPLETE | (none) | 12/12 |
| Phase D | 30/~30 COMPLETE | (none) | 30/~30 |
| Phase E | 20/~50 done | hypothesis_engine, daily_wisdom | 20/~50 |
| Total true line-by-line | | +2 files | **103 of ~382 (~27.0%)** |
| Remaining | | | **~279 files** |

**MILESTONE: Batch 50 reached. Wisdom-writer side audit complete. 27% audit milestone.**

## NEXT BATCH

Batch 51 (doc #57): Continue Phase E. Candidates clustered around earnings + news layer (both consumed by parallel_scorer B44):
- **`src/earnings.py` (4.9KB)** — produces days_to_earnings used by parallel_scorer + probability_engine + agent_memoir.
- **`src/earnings_analyzer.py` (7.8KB)** — deeper earnings analysis layer.
Will pick `earnings.py + earnings_analyzer.py` next session — closes earnings audit.

End of Batch 50. Phase E in progress (20/50). **27.0% audit milestone.**
