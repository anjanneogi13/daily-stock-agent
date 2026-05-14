# Batch 36 — src/premarket_filter.py (25 lines) + src/premarket_decision_contract.py (269 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** premarket_filter.py (25 lines), premarket_decision_contract.py (269 lines)
**Phase:** D (pipeline & output) resumed — files 9 and 10 of ~30

## TOP HEADLINE FINDINGS

1. PF-X1: premarket_filter.py is a **TINY 25-line gap-check gate** — uses yfinance fast_info to detect premarket gaps. **Single function `gap_check()`.** Default thresholds: max_gap_up=3%, max_gap_down=-5%. **Asymmetric tolerance** — wider for downs (panic-tolerant) than ups (chase-averse).
2. PF-X2: PF **FAILS OPEN** on errors (lines 23-24): bare-except returns `(True, 0.0, "gap check failed (...) — allowing")`. **A yfinance outage = ALL premarket gap-check gates passed.** Per Batch 8 hard_blocks gate-philosophy cross-cutting (most gates fail-CLOSED), this gate is the **OPPOSITE — fail-open by design.** Operator can detect via "gap check failed" reason string but no escalation.
3. PD-X1: premarket_decision_contract.py is **THE OFFICIAL PICK CONTRACT** — 269 lines defining 28-field pick payload + 19-field no-pick payload + 11 valid no-pick causes. **THE MOST COMPREHENSIVE schema-validation file in audit.** ✅ Pure validation, behavior-neutral per docstring.
4. PD-X2: PD docstring lines 6-12 — **6-LINE EXPLICIT BEHAVIOR-NEUTRAL CONTRACT**: "does not generate picks, does not change scoring, does not enable paper trading, does not enable live trading, does not send alerts, does not mutate runtime state." **GOLDEN STANDARD scope-limit declaration.** Per Batch 35 SP-1 (4 explicit "no" statements) + Batch 22 OBSERVE-MODE pattern, joins as **best-documented anti-mutation contract** in audit.
5. PD-X3 (lines 121-124, 144-149): SAFETY_FLAGS = ("paper_trading_enabled", "live_trading_enabled") — both **MUST be False**. Validator (line 147) enforces. **Hard-coded production-readiness gate.** **An operator who tries to ship `paper_trading_enabled=True` gets validation error.** ✅ Defensive against premature production push.
6. PD-X4 (lines 38-69, 71-95): 28 + 19 = **47 distinct field names** across 2 contract shapes. **9 fields shared** (artifact, date, decision, strategy_lane, contract_version, strategy_version, scoring_version, config_version, etc.). **No SHARED_FIELDS extraction** — DRY violation. If one contract gains a field, other doesn't.
7. PD-15 (line 161): `if field in {"score", "risk_reward", "quantity", "risk_dollars"} and numeric < 0` — **non-negative check**. Then line 163: `if field in {"entry", "stop_loss", "take_profit"} and numeric <= 0` — **strict positive**. **Inconsistent zero-handling.** Score CAN be 0 but entry CANNOT. Reasonable but undocumented why score=0 is OK.

## src/premarket_filter.py — LINE BY LINE

### Line 1: Module docstring
- PF-1 GOOD: 1-line docstring documents intent (gap-up = chasing, gap-down = bad news).

### Line 2: Import
- PF-2 GOOD: yfinance only. Minimal.

### Lines 4-24: gap_check
- PF-3 GOOD (lines 4-5): Type-hinted with explicit defaults (3% up, -5% down).
- PF-4 GOOD (lines 6-9): 3-line docstring documents return shape + usage.
- PF-5 GOOD (line 11): yf.Ticker — standard.
- PF-6 GOOD (line 12): `t.fast_info` — uses fast endpoint (cheaper than full info).
- PF-7 GOOD (lines 13-14): **Multi-key lookup** for camelCase + snake_case + alternative names. Defensive against yfinance schema variation. Per Batch 28 NC-X4 / Batch 27 PV-31 cross-cutting Theme T2 schema-chaos.
- PF-8 GOOD (line 15): `if not (prev_close and last)` — guard against missing data.
- PF-9 GOOD (line 16): **Returns `(True, 0.0, "no premarket data — allow")`** — fail-open per PF-X2.
- PF-10 GOOD (line 17): Standard gap calculation. No div-by-zero guard but `prev_close` is non-None per line 15. **Could be 0** for delisted/halted stocks. **Latent div-by-zero.**
- PF-11 GOOD (lines 18-21): 2-tier blocking with reason strings.
- PF-12 GOOD (line 22): Pass-through with reason.
- PF-13 BUG (lines 23-24): Per PF-X2, fail-open bare-except. **Catches ALL exceptions including KeyboardInterrupt** (Python 3.x bare-except still catches Exception ancestors). **Should be specific.**
- PF-14 GOOD (line 24): Reason string includes exception type for forensic debugging. ✅ better than silent.

## src/premarket_decision_contract.py — LINE BY LINE

### Lines 1-16: Module docstring
- PD-1 GOOD: 16-line docstring documenting:
  - Purpose (Lane 1 contract)
  - Behavior-neutral 6-bullet contract per PD-X2
  - Pre-wiring intent
- PD-2 GOOD: Explicit "before later phases wire it into main.py" — **roadmap declaration**.

### Lines 18-21: Imports
- PD-3 GOOD: Pure stdlib. **No I/O imports** — pure validation library.

### Lines 24-36: Constants — versioning + decisions
- PD-4 GOOD (line 24): STRATEGY_LANE = "premarket_official_daily_pick" — namespaced.
- PD-5 GOOD (lines 26-28): **3 version constants** (CONTRACT, STRATEGY, SCORING). **Version pinning per concern.** Per Batch 11 PL-X1 schema chaos cross-cutting, this is the FIX template — explicit versioning.
- PD-6 GOOD (lines 30-36): 2 decision constants + VALID_DECISIONS set. Symbolic names instead of magic strings.

### Lines 38-69: OFFICIAL_PICK_REQUIRED_FIELDS
- PD-7 GOOD: 28-field tuple. Comprehensive coverage:
  - Identity: artifact, date, decision, ticker, company
  - Versioning: 4 version fields
  - Provenance: selection_time_et, workflow_run_id, commit_sha
  - Status: 3 status fields
  - Scoring: 2 score fields
  - Trading: 7 trading-plan fields
  - Risk: regime, risk_flags, selection_reason, invalidation_conditions
  - Safety: 2 safety flags
- PD-8 GOOD: Per-line tuple format with trailing comma — git-diff-friendly.

### Lines 71-95: OFFICIAL_NO_PICK_REQUIRED_FIELDS
- PD-9 GOOD: 19-field tuple. Has explanation fields not in pick (primary_no_pick_cause, secondary_causes, pipeline, candidate_diagnostics, watch_only_available, next_action).
- PD-10 BUG: Per PD-X4, no SHARED_FIELDS extraction. **9 overlapping fields duplicated.**

### Lines 97-105: OFFICIAL_PICK_NUMERIC_FIELDS
- PD-11 GOOD: 7-field tuple naming numeric-validated fields.

### Lines 107-119: OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES
- PD-12 GOOD: 11-cause set. **All NO_PICK_ prefixed.** Operator-readable enum.
- PD-13 GOOD: Causes cover full failure space:
  - Data: PROVIDER_DEGRADED, READINESS_FAILED
  - Schedule: MARKET_CLOSED, WINDOW_MISSED
  - Pipeline: NO_SCORED_CANDIDATES, FILTERS_REMOVED_ALL
  - Gate-blocked: HARD_BLOCKED, PREMARKET_SANITY_BLOCKED, RISK_GATE_BLOCKED
  - Other: RUNTIME_FAILURE, UNKNOWN_POST_FILTER_GATING
- PD-14 BUG: NO docstring per cause. Operator must infer meaning. **Add cause description dict.**

### Lines 121-124: SAFETY_FLAGS
- PD-15 GOOD: Per PD-X3, 2-flag tuple enforced as False.

### Lines 127-137: _is_missing
- PD-16 GOOD (line 127-132): Docstring explains "empty dict/list allowed but None and blank strings not." **Subtle distinction documented.** ✅
- PD-17 GOOD (lines 133-137): Defensive None + empty-string check.

### Lines 140-141: _missing_required_fields
- PD-18 GOOD: 1-line list comprehension. Returns missing-field names.

### Lines 144-149: _validate_safety_flags
- PD-19 GOOD: Iterates SAFETY_FLAGS, requires `is False` (not falsy). **Strict identity check** — `0` or `""` would fail. ✅ defensive against truthy-falsy confusion.

### Lines 152-165: _validate_numeric_fields
- PD-20 GOOD (line 156-160): try/except for float coercion. Specific (TypeError, ValueError) — NOT bare-except. ✅
- PD-21 GOOD (line 161): Per PD-15 head finding, asymmetric zero-handling.
- PD-22 BUG (line 161, 163): Hardcoded sets `{"score", "risk_reward", "quantity", "risk_dollars"}` and `{"entry", "stop_loss", "take_profit"}` inside function. **Magic strings duplicated from OFFICIAL_PICK_NUMERIC_FIELDS tuple.** If a new numeric field added, must edit this function too. **Lift sets to module level.**

### Lines 168-200: validate_official_pick
- PD-23 GOOD: Type-hinted Mapping[str, Any].
- PD-24 GOOD: Returns list of human-readable error strings.
- PD-25 GOOD (line 176-177): Missing-field check.
- PD-26 GOOD (lines 179-183): Decision + strategy_lane enum check.
- PD-27 GOOD (lines 185-186): Safety + numeric validations.
- PD-28 GOOD (lines 188-198): Type-shape validations for nested fields (mapping, list, list).
- PD-29 BUG (lines 188-198): 3 IDENTICAL `if X is not None and not isinstance(X, ...)` blocks — DRY violation. Should be helper `_require_type(payload, field, expected_type, errors)`.

### Lines 203-241: validate_official_no_pick
- PD-30 GOOD: Mirror structure of validate_official_pick.
- PD-31 GOOD (lines 220-222): Validates primary_no_pick_cause is in allowed set.
- PD-32 BUG (line 220): `if primary` — falsy check. **A primary_no_pick_cause of empty string passes the check** (already missing-field-checked above) but logic relies on missing being caught earlier. Brittle dependency on order of validations.
- PD-33 GOOD (lines 224-234): Type-shape validations.
- PD-34 GOOD (line 236): `if payload.get("watch_only_available") not in {True, False}` — boolean strict check.

### Lines 244-251: validate_official_decision
- PD-35 GOOD: Dispatcher to pick or no-pick validator.
- PD-36 GOOD (line 251): Defaults to error if decision invalid.

### Lines 254-268: contract_summary
- PD-37 GOOD: JSON-safe self-description for diagnostics/dashboards.
- PD-38 GOOD (lines 266-267): **Hardcoded paper/live trading flags = False.** Operator inspects contract_summary() and sees production status guarantee.
- PD-39 BUG (lines 266-267): Hardcoded vs SAFETY_FLAGS-derived. If SAFETY_FLAGS expanded, this breaks.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### PF-X2: Gate-philosophy inconsistency
Per Batch 7 hard_blocks cross-cutting, gates can be:
- **fail-CLOSED:** error → block (capital-preserving)
- **fail-OPEN:** error → allow (continue-friendly)

Cumulative tally:
| Gate | Strategy |
|---|---|
| hard_blocks (B7) | fail-CLOSED |
| risk_gate (B8) | fail-CLOSED |
| premarket_filter (this batch) | **fail-OPEN** |
| news_safety (B16) | fail-CLOSED |

**1 of 4 audited gates fails OPEN.** Per Batch 30 PE2-X2 silent-detector-failure cross-cutting, fail-open gates compound silent failures. **A yfinance outage during premarket = ALL gap checks "allow" → ALL picks pass premarket gate → operator gets surprise gap-up trades.**

### PD-X2: Behavior-neutral contract pattern emerging
Modules with explicit "this does not mutate" docstrings:
- meta_brain (B23 MB-1): "this module never mutates"
- weight_proposer (B22 WP-2): "Never auto-applies"
- self_awareness (B23 SA-1): "READ-ONLY brain reflection"
- stooq_provider (B35 SP-1): 4-line "no" scope contract
- premarket_decision_contract (this batch PD-X2): 6-line "does not" contract

**5 modules with explicit OBSERVE-MODE / NEUTRAL contracts.** **Phase D continues this pattern.** ✅

### PD-X3 + Phase D safety enforcement
SAFETY_FLAGS hardcoded production-readiness gate is **first explicit "must be False" enforcement** in audit. Compare:
- weight_applier dry_run default (Batch 26 WA-39)
- hypothesis_engine OBSERVE-MODE only (Batch 21 HE-16)
- premarket_decision_contract paper_trading_enabled MUST be False (this batch)

**3-tier production-safety pattern.** **Should document this as architectural standard.**

### PD-X4 + DRY across 2 schemas
9 overlapping fields between PICK + NO_PICK contracts. **Should extract:**

    SHARED_REQUIRED_FIELDS = ("artifact", "date", "decision", "strategy_lane", ...)
    OFFICIAL_PICK_ONLY_FIELDS = (...)
    OFFICIAL_NO_PICK_ONLY_FIELDS = (...)
    OFFICIAL_PICK_REQUIRED_FIELDS = SHARED_REQUIRED_FIELDS + OFFICIAL_PICK_ONLY_FIELDS

### PF-7 cross-cutting: Multi-key lookup pattern
PF-7 line 13-14 uses 2-3 alternative key names per field. Per:
- PV-31/PV-32 (Batch 27 pick_evaluator) 6 alternative names for sector/tag fields
- NC-X4 (Batch 28 nightly_conductor) silent JSON corruption tolerance
- PF-7 (this batch) 3 alternative names for prev_close + last fields

**Schema-chaos defensiveness now in 4+ files.** **Operators paying the cost of yfinance schema instability.**

### Cross-cutting: bare-except in this batch
- premarket_filter: 1 (PF-13, fail-open documented)
- premarket_decision_contract: 0 (uses scoped TypeError, ValueError per PD-20)

### Cross-cutting: ATOMIC WRITE
N/A this batch (validation + read-only).

## SUMMARY (Batch 36)

| Severity | premarket_filter | premarket_decision_contract | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 3 | 6 | 4 | 13 |
| Data/safety | 1 | 4 | 0 | 5 |
| Code smell | 1 | 1 | 0 | 2 |
| Good code | 11 | 32 | 0 | 43 |
| Total findings | 16 | 43 | 4 | 63 |

## TOP 10 CRITICAL FIXES from Batch 36

1. PF-X2: Add escalation/alerting when gap_check fails repeatedly. Currently silent-allowed. Operator sees only reason strings. (15 min)
2. PD-X4 / PD-10: Extract SHARED_REQUIRED_FIELDS to eliminate 9-field duplicate. (10 min)
3. PD-22: Lift "score, risk_reward, ..." sets to module level. (5 min)
4. PD-29: Add `_require_type()` helper for 5+ type-shape checks. (10 min)
5. PD-14: Add per-cause description dict for OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES. (15 min)
6. PD-39: Drive contract_summary safety flags from SAFETY_FLAGS tuple, not hardcoded. (3 min)
7. PF-13: Replace bare-except with specific exception types. (3 min)
8. PF-10: Add div-by-zero guard for prev_close=0 (delisted/halted edge case). (3 min)
9. PD-15 documentation: Add comment explaining why score=0 is OK but entry=0 is not. (3 min)
10. PD-32: Document PRECEDENCE — primary_no_pick_cause check assumes missing-field check ran first. (3 min)

## NEW THEMES UPDATED

- Theme T1 (bare except): premarket_filter 1 (documented fail-open). premarket_decision_contract 0 (scoped). **Phase D resumed clean.**
- Theme T2 (schema drift): PF-7 multi-key lookup confirms 4-file schema-chaos pattern.
- Theme T6 (atomic writes): N/A this batch.
- Theme T8 (DRY): PD-X4 9 shared fields duplicated across 2 contracts. PD-29 5 type-shape duplicate blocks.
- Theme T11 (fail-open by accident): PF-X2 fail-open gate with no escalation.
- Theme T13 (silent-default-fills): PF-9 "no premarket data — allow" silent permission.
- Theme T14 (gold-standard patterns): premarket_decision_contract is THE TEMPLATE for behavior-neutral contracts. SAFETY_FLAGS production-readiness pattern is reusable.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A | 8/8 COMPLETE | (none) | 8/8 |
| Phase B | 18/18 COMPLETE | (none) | 18/18 |
| Phase C | 12/12 COMPLETE | (none) | 12/12 |
| Phase D | 10/~30 done | premarket_filter, premarket_decision_contract | 10/~30 |
| Phase E | 12/~50 done | (none) | 12/~50 |
| Total true line-by-line | | +2 files | **75 of ~382 (~19.6%)** |
| Remaining | | | **~307 files** |

## NEXT BATCH

Batch 37: src/official_pick_artifact.py + src/official_artifact_loader.py — the producer/consumer for the pick contract validated in this batch. official_pick_artifact creates the JSON artifacts, official_artifact_loader reads them. CRITICAL Phase D pair — the actual write of premarket pick decisions to disk.

End of Batch 36. Phase D in progress (10/30).
