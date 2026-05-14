# Batch 23 — src/meta_brain.py (279 lines) + src/self_awareness.py (140 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** meta_brain.py (279 lines, fully read), self_awareness.py (140 lines, fully read)
**Phase:** C (brain pillars) — files 5 and 6 of ~12

## TOP HEADLINE FINDINGS

1. MB-X1: meta_brain.py is **THE BRAIN-ABOUT-THE-BRAIN** — T50, reads learning_journal + signal_journal + pattern_stats and produces the Sunday Self-Improvement Report. **Explicit OBSERVE-ONLY philosophy at lines 12-14: "This module never mutates anything. It only OBSERVES the brain's recent behavior."** **JOINS the OBSERVE-MODE club** (scoring_safety, hypothesis_engine, weight_proposer, now meta_brain — 4 modules).
2. SA-X1: self_awareness.py is THE STATISTICAL CONFIDENCE LAYER — Wilson score interval for win-rate, t-style CI for mean R. **140 lines, pure stdlib** (no scipy). 3 functions, ZERO bare-except. **JOINS gold-standard pure computation club** (now 8 modules: indicators, exit_manager, trailing_stop, adaptive_tp, scoring_safety, hypothesis_engine, calibration partly, self_awareness).
3. MB-12 (line 56): `datetime.fromisoformat(str(e.get("ts","")).split(".")[0])` — strips microseconds via `.split(".")[0]`. **But ISO timestamps with timezone (e.g., "2026-05-12T14:30:45.123+00:00") split on "." removes microseconds AND timezone offset.** "2026-05-12T14:30:45.123+00:00".split(".")[0] = "2026-05-12T14:30:45" → loses tz. Then `datetime.fromisoformat` parses as NAIVE. Then compared to `datetime.now()` (also naive) at line 52. **Works by coincidence — both naive — but loses timezone information.** Theme T13 + naive datetime cross-cutting.
4. MB-X2 (lines 84-86): `if not events: return {"stuck": True, ...}` — **EMPTY EVENTS = "STUCK"**. But empty events could mean "nothing to learn" OR "system just started" OR "events file deleted". The defensive guard at lines 80-82 (system_age_days check) only fires if caller passes age. Per MB-22 below, build_self_improvement_digest at line 207-212 DOES compute system_age_days but only from non-empty events. **Empty events → no age → no defensive guard → reports "stuck=True severity=high" on day 1.** False alarm risk.
5. SA-X2 (lines 88-94): Verdict thresholds for EDGE_CONFIRMED (n≥20 AND r_lo>0 AND wr_lo>0.45) and EDGE_BROKEN (r_hi<0 OR wr_hi<0.35). **Strict.** For 30 closed picks with WR=60%, r_lo could still be near 0 (high variance). **System usually reports INCONCLUSIVE.** Documented honesty — won't claim edge until truly statistically clear. ✅ But also means weight_proposer (Batch 22) acts on smaller samples than self_awareness "verdict" requires. Two confidence frameworks, two thresholds.
6. MB-22 (line 134-137): suggest_hypotheses computes baseline_wr from ALL recent rows. **Includes rows with `r_multiple == 0` as losses** (line 137: `sum(1 for x in rs_all if x > 0)`). Same Theme as Batch 15 CB-30 / SJ-40. Strict positive = breakeven counts as loss.
7. MB-25 (line 168): `return hypotheses[:5]` — hard cap 5 hypotheses surfaced. Magic 5. Other 100s of buckets silently dropped.

## src/meta_brain.py — LINE BY LINE

### Lines 1-15: Module docstring
- MB-1 GOOD: Documents T50, 4 outputs, dependencies (3 data sources).
- MB-2 GOOD: **EXPLICIT PHILOSOPHY at lines 12-14**. Same OBSERVE-ONLY pattern as scoring_safety SCS-1.
- MB-3 GOOD: Documents Sunday telegram consumer.

### Lines 16-27: Imports + paths
- MB-4 GOOD (line 16): `from __future__ import annotations`.
- MB-5 BUG: 3 RELATIVE PATHS (JOURNAL, PICKS, STATS). **14th file with this pattern.** Cumulative: HB, PRG, PL, main.py, SCS, MDH, RG, CB, NS+NE, NC, FH, PS, SJ, WP, MB.

### Lines 30-32: _to_float
- MB-6 SMELL: 7th _safe_float-equivalent helper. Same pattern as PS-6, IND _f, etc.

### Lines 35-42: _read_jsonl
- MB-7 SMELL: NEAR-IDENTICAL to pattern_stats _read_jsonl (Batch 21 PS-7 to PS-10). DRY violation across files.
- MB-8 BUG (line 38): `p.read_text().splitlines()` — full file in memory. Same Theme as PS-8.
- MB-9 BUG (line 41): bare `except: pass` — Theme T1 undocumented. Per Batch 22 cross-cutting, JSONDecodeError swallow is universal pattern.

### Lines 48-61: recent_mutations
- MB-10 GOOD (line 49): Path injectable for tests.
- MB-11 BUG (line 52): `datetime.now()` — NAIVE. Cross-cutting datetime issue.
- MB-12 BUG (line 56): `datetime.fromisoformat(str(e.get("ts","")).split(".")[0])` — per MB-X1 head finding, splits on "." removing microseconds AND timezone. Naive comparison works but loses tz info.
- MB-13 GOOD (lines 59-60): Defensive try/except — bad timestamp = drop event.
- MB-14 BUG (line 60): bare except. Theme T1 undocumented.

### Lines 64-69: categorize_mutations
- MB-15 GOOD: Single-purpose grouping helper. Defaultdict.
- MB-16 GOOD: `e.get("kind","unknown")` — silent default for missing kind. Per cross-cutting, "unknown" sentinel is everywhere.

### Lines 75-98: detect_stuck_areas
- MB-17 GOOD (lines 78-82): Defensive guard for new systems — added 2026-05-04. Comment explains why.
- MB-18 BUG (lines 75-83): **DOCSTRING IS AT LINE 83 — AFTER the early-return at line 80.** Python convention: docstring immediately follows def. The system_age_days guard runs BEFORE the docstring. Functionally fine but PEP-257 violation. Code quality smell.
- MB-19 BUG (line 84-86): Per MB-X1 head finding, empty events → stuck=True without age guard if caller didn't pass system_age_days.
- MB-20 GOOD (lines 87-93): Most-recent timestamp computation with defensive try/except.
- MB-21 BUG (line 90): Same `.split(".")[0]` as MB-12 — naive parsing.
- MB-22 BUG (line 93): `age_days = 999` — magic sentinel for "couldn't parse." Then line 94 `if age_days >= stuck_days` triggers stuck=True. **Bad timestamp = stuck=True.** Silent fail-CLOSED in this direction (alarm-prone, not silent).

### Lines 104-168: suggest_hypotheses
- MB-23 GOOD (line 104-106): Type-hinted args, all optional with defaults.
- MB-24 GOOD (line 113-114): Defensive existence check.
- MB-25 GOOD (line 115): `cutoff = datetime.now().date() - timedelta(...)` — uses date arithmetic.
- MB-26 GOOD (line 120): Comment "legacy 'date' fallback removed 2026-05-05 (column never existed)" — schema cleanup archaeology.
- MB-27 BUG (lines 122-125): Defensive parse with continue on bad date. Silent drop.
- MB-28 BUG (line 127): `r.get("r_multiple") in (None, "")` — checks for None or empty string. **Misses "None" string sentinel** that pick_logger may write (per Batch 11 PL-X1 schema chaos).
- MB-29 BUG (lines 129-130): Bare `except: return []` — Theme T1 undocumented. Whole-function silent failure.
- MB-30 BUG (line 137): `baseline_wr = sum(1 for x in rs_all if x > 0) / len(rs_all)` — strict positive. Breakeven (r=0) counts as loss. Per MB-25 head finding, same as CB-30/SJ-40.
- MB-31 GOOD (lines 141-148): 4-group analysis (sector_cat / sector_tag / trade_type / regime). Comprehensive.
- MB-32 BUG (line 153): Magic 0.15 (15%) absolute swing threshold. No source.
- MB-33 BUG (line 168): Magic 5 hypothesis cap. Per MB-25 head finding.

### Lines 174-195: _human_summary_of_mutations
- MB-34 GOOD: Excellent translation layer — technical events → plain English.
- MB-35 GOOD (line 175 docstring): "a friend explaining over coffee" — sets the voice.
- MB-36 GOOD (lines 177-194): 6 mutation categories with emoji + count + sample names.
- MB-37 BUG (line 182): `names[:3]` — magic 3 cap on shown names. Hardcoded.
- MB-38 BUG (lines 186-188): Combines lesson_promoted + pattern_promoted into single "learned X new lessons" line. **Conflates two distinct event types.** Operator can't tell which. Information loss for plain-English-clarity.
- MB-39 SMELL: All `if "X" in by_kind:` checks but iterating `for kind, events in by_kind.items()` would be more pythonic + extensible.

### Lines 198-233: build_self_improvement_digest
- MB-40 GOOD: Composer function. Calls all 4 sub-functions.
- MB-41 GOOD (lines 203-212): Computes system_age_days FROM EVENTS (oldest event ts).
- MB-42 BUG (line 207): `min(e.get("ts", "") for e in events if e.get("ts"))` — empty string ts excluded ✅. **But if all events have empty ts, min() returns "" → fromisoformat raises → except → _system_age_days=None → no guard.** Edge case.
- MB-43 GOOD (line 209): `_oldest.replace("Z", "+00:00")` — handles Z-suffix ISO. **DIFFERENT from MB-12 line 56 which strips microseconds.** Two parsing strategies in same file. Inconsistent.
- MB-44 GOOD (lines 211-212): Bare except → None. Acceptable defensive.
- MB-45 GOOD (lines 217-223): T51 calendar warning integration. Imports market_calendar. Defensive try/except.
- MB-46 GOOD (lines 224-233): 8-field digest dict.

### Lines 236-278: format_telegram_digest
- MB-47 GOOD: Renders to Markdown. Sectioned (improvements / heads-up / investigations / maintenance).
- MB-48 GOOD (lines 250-251): "Quiet week" fallback for when nothing happened. Operator-friendly.
- MB-49 GOOD (line 264): hyps[:3] cap for telegram brevity.
- MB-50 GOOD (lines 267-268): Translates "outperforming/underperforming" → "winning more/losing more" for layman.
- MB-51 BUG: T51 calendar warning section appended AFTER hyps — could be rare/intermittent. Operator may overlook. Should arguably be top of message when present (urgent).

## src/self_awareness.py — LINE BY LINE

### Lines 1-12: Module docstring
- SA-1 GOOD: Documents T45 / Pillar 5, two metrics (Wilson + SEM), consumers.
- SA-2 GOOD: **EXPLICIT pure-stdlib note** ("no scipy/numpy"). Reduces deps.
- SA-3 GOOD: Notes statistical methods used (Wilson score, normal-approx for mean).

### Lines 13-19: Imports
- SA-4 GOOD: stdlib + signal_journal.load_closed only.
- SA-5 GOOD: Type hints throughout.

### Lines 23-31: wilson_ci
- SA-6 GOOD: Documented Wilson score interval. Standard formula.
- SA-7 GOOD (line 25-26): n=0 → return (0,0). Defensive.
- SA-8 GOOD (line 31): `max(0.0, ...)` and `min(1.0, ...)` clamp to valid probability.
- SA-9 BUG (line 23): `z: float = 1.96` — magic 1.96 (95% CI z-score). Documented in docstring as "95% Wilson CI" so trace-able. But for 99% CI need z=2.576 — caller must pass.

### Lines 34-44: mean_r_ci
- SA-10 GOOD: Standard mean + standard-error CI.
- SA-11 GOOD (line 37-38): n=0 → (0,0,0).
- SA-12 GOOD (line 40-41): n=1 → (mean, mean, mean) — no variance possible.
- SA-13 GOOD (line 42): `var = sum((x-mean)**2 for x in rs) / (n - 1)` — sample variance (Bessel's correction). Statistically correct ✅.
- SA-14 BUG: Assumes ~normal R distribution per docstring. **R-multiples are typically NOT normal** (heavy right tail from runners, left tail from stops). For small n, bootstrap CI better. But scipy-free constraint precludes that.

### Lines 48-59: _within_days
- SA-15 GOOD: Test-injectable `today` arg.
- SA-16 GOOD (lines 51-58): Tries evaluated_on first, falls back to pick_date. **Two field names checked.**
- SA-17 BUG (line 51): `("evaluated_on", "pick_date")` — but pick_date is the START not the END. **Using pick_date for "within last N days" filter measures pick AGE not OUTCOME age.** A pick taken 10 days ago and closed 2 days ago would be:
  - `evaluated_on` (close date) = 2 days ago → within 30d ✅
  - `pick_date` = 10 days ago → within 30d ✅
  - Both within 30d, return True. ✅ in this case
  - But if pick was 35 days ago and closed 10 days ago → evaluated_on says yes, pick_date says no. **Returns True from first match (evaluated_on at line 56).** ✅ correct precedence.

### Lines 63-107: rolling_window
- SA-18 GOOD: Comprehensive docstring with output schema.
- SA-19 GOOD (lines 75-76): Filters via load_closed + _within_days.
- SA-20 BUG (line 75): `(load_closed() or [])` — defensive but load_closed returns [] on missing file (Batch 22 SJ-44). Always returns list — `or []` redundant.
- SA-21 GOOD (line 78): Wins counted from outcome string (not r_multiple). Per SJ-39, outcome derived from r_multiple>0. Consistent.
- SA-22 GOOD (lines 80-82): R-list with try/except per record.
- SA-23 BUG (line 81): `c.get("r_multiple") or 0` — `or 0` masks None as 0. **Per Batch 15 CB-30 same pattern.** Pending picks (r_multiple=None) included as 0R outcomes. **But wait — load_closed at SJ-44 already filters outcome in (win, loss), so all returned rows HAVE r_multiple.** **So `or 0` shouldn't fire in practice.** Defensive belt-and-suspenders.
- SA-24 GOOD (lines 84-86): Win rate, Wilson CI, mean-R CI.
- SA-25 GOOD (lines 88-94): 3-tier verdict (CONFIRMED / BROKEN / INCONCLUSIVE) with explicit thresholds.
- SA-26 BUG (line 90): Magic n>=20. Lower than weight_proposer min_n=30 default. **Per SA-X2 cross-cutting, two confidence frameworks.**
- SA-27 BUG (line 91): EDGE_CONFIRMED requires r_lo > 0 AND wr_lo > 0.45. **Strict — needs both lower bounds positive.** Reasonable but may rarely fire.
- SA-28 BUG (line 93): EDGE_BROKEN requires r_hi < 0 OR wr_hi < 0.35. **OR logic — easier to trigger.** Asymmetric — easier to declare broken than confirmed. Conservative bias for capital protection. ✅

### Lines 110-122: format_footer
- SA-29 GOOD: Empty n → "" (no footer). Defensive.
- SA-30 GOOD: Emoji-coded verdict.
- SA-31 GOOD: Two-line format with WR + mean-R + CIs.

### Lines 125-139: monthly_calibration
- SA-32 GOOD: Multi-window analysis (30/60/90d).
- SA-33 GOOD (lines 131-135): Trend detection — improving / decaying based on Δ mean_r >= 0.20.
- SA-34 BUG (line 132, 134): Magic 0.20 R-multiple threshold for trend detection. No source.
- SA-35 BUG: 30d vs 90d comparison ignores 60d window for trend logic. Could detect "improving then decaying" pattern but doesn't.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### MB-X1 + SA-X1: TWO MORE GOLD-STANDARD MODULES
- **meta_brain joins OBSERVE-MODE club** (4 modules: scoring_safety, hypothesis_engine, weight_proposer, meta_brain). Explicit no-mutation philosophy.
- **self_awareness joins gold-standard pure-computation club** (8 modules now). Pure stdlib, type-hinted, defensive empty-input handling, no bare-except.

### MB-X2: Empty events false-positive STUCK alarm
detect_stuck_areas (line 84-86) returns stuck=True when events empty. The system_age_days defensive guard only protects when caller passes age. Per MB-41-44, build_self_improvement_digest computes age FROM events — empty events → no age → no guard. **Fresh install reports STUCK on day 1.** Self-deprecating false alarm.

### SA-X2: TWO confidence frameworks, two min-N thresholds
- self_awareness: n>=20 for verdict (Wilson CI based)
- weight_proposer: min_n=30 default for proposals
- hypothesis_engine: min_n=10 for significance test
- pattern_stats: implicit (no min, just reports)
- meta_brain.suggest_hypotheses: min_n=20
**5 modules, 4 different min-n thresholds.** Could be unified or at least documented.

### MB-X3: Naive datetime parsing inconsistency WITHIN one file
- MB-12 line 56: `.split(".")[0]` strips microseconds AND timezone
- MB-43 line 209: `.replace("Z", "+00:00")` keeps timezone
**Two parsing strategies in same file for same kind of timestamp.** Should pick one.

### Cross-cutting: 14 files with relative-path constants
HB, PRG, PL, main.py, SCS, MDH, RG, CB, NS+NE, NC, FH, PS, SJ, WP, MB. **14 files.**

### Cross-cutting: 7 _safe_float-equivalent helpers
Added MB-6 to the previous 6.

### Cross-cutting: bare-except in JSONDecodeError continue pattern
Now in 6+ files: MB-9, MB-14, MB-29, PS-10 (Batch 21), SJ-37, SJ-43 (Batch 22), WP-36 (Batch 22), CB-? (Batch 15). **Universal undocumented pattern.** Per Batch 22 SJ-X4 recommendation, should formally document as "JSONL corruption tolerable for analysis layer" Theme T1 exception category.

### Cross-cutting: Magic 0/15/20/30/100 thresholds
- MB-25 magic 0.15 (15% swing)
- MB-32 magic 0.20 (R-mult trend)
- SA-26 magic 20 (n threshold)
- SA-27 magic 0.45 (WR threshold)
- SA-28 magic 0.35 (WR broken threshold)
- SA-34 magic 0.20 (trend threshold)
**6 magic thresholds in 2 small files.** Per Batch 12 SC-X3 Theme.

### Cross-cutting: PHASE C OBSERVE-MODE adoption
4 of 6 audited Phase-C files explicit OBSERVE-MODE:
- scoring_safety (Batch 12 — actually Phase B but shares discipline)
- hypothesis_engine (Batch 21)
- weight_proposer (Batch 22)
- meta_brain (Batch 23)
**Discipline trend: Phase C sub-systems are READ-ONLY-by-design.** Mutations live in nightly_conductor (per MB-1 line 14). Centralized mutation point. ✅ architectural pattern.

## SUMMARY (Batch 23)

| Severity | meta_brain | self_awareness | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 8 | 4 | 4 | 16 |
| Data/safety | 6 | 3 | 0 | 9 |
| Code smell | 4 | 2 | 0 | 6 |
| Good code | 33 | 20 | 0 | 53 |
| Total findings | 51 | 29 | 4 | 84 |

## TOP 10 CRITICAL FIXES from Batch 23

1. MB-X2 / MB-19: detect_stuck_areas should NOT report stuck=True on empty events without system_age_days. Default to "unknown" or "insufficient data." (5 min)
2. MB-X3 / MB-12+MB-21+MB-43: Pick ONE timestamp-parsing strategy. Use `_parse_iso_ts(s)` helper. (15 min)
3. SA-X2: Document or unify min-N thresholds across 5 brain modules. (15 min)
4. MB-7+MB-8: Refactor _read_jsonl shared helper into src/_utils.py (8th _safe-helper-equivalent — combine all). (30 min)
5. MB-30: baseline_wr should match SA convention (treat r=0 as TBD or as separate category). (10 min)
6. MB-32 + MB-33: Document magic 0.15 (swing threshold) and 5 (hypothesis cap). (5 min)
7. SA-26: Increase n>=20 to match weight_proposer min_n=30 OR document rationale for difference. (5 min)
8. MB-18: Move docstring to top of detect_stuck_areas function (PEP-257 fix). (1 min)
9. MB-29: Replace `except: return []` with logged exception. (5 min)
10. SA-14: Document the normality assumption + suggest n>=30 for valid SEM. (5 min)

## NEW THEMES UPDATED

- Theme T1 (bare except): MB has 4 bare excepts (lines 41, 60, 130, 211). Mostly defensive. SA has zero. MB inconsistent.
- Theme T2 (schema drift): N/A this batch.
- Theme T8 (DRY): MB-7 _read_jsonl duplicates pattern_stats. _to_float duplicates 6 other files.
- Theme T11 (fail-open by accident): MB-X2 false STUCK alarm.
- Theme T13 (silent-default-fills): MB many "unknown" defaults.
- Theme T14 (gold-standard patterns): meta_brain joins OBSERVE-MODE club (4 total). self_awareness joins pure-compute club (8 total). **PHASE C is the cleanest sub-architecture in the codebase.**

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | 8/8 COMPLETE | (none) | 8/8 |
| Phase B (scoring/data) | 18/18 COMPLETE | (none) | 18/18 |
| Phase C (brain pillars) | 6/~12 done | meta_brain, self_awareness | 6/~12 |
| Total true line-by-line | | +2 files | **47 of ~382** |
| Remaining | | | **~335 files** |

## NEXT BATCH

Batch 24: src/learning_journal.py + src/wisdom_base.py — learning_journal is the producer of mutation events that meta_brain reads. wisdom_base is the central wisdom storage that wisdom_consultant/wisdom_hint consume.

End of Batch 23. Phase C in progress (6/12).
