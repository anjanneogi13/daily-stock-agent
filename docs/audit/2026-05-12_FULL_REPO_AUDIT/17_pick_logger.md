# Batch 11 — src/pick_logger.py (179 lines) — TRUE LINE-BY-LINE — PHASE A FINALE

**Date:** 2026-05-12
**Files:** pick_logger.py (179 lines, fully read)
**Phase:** A (safety/gates) — file 8 of 8 — PHASE A NOW COMPLETE

## TOP HEADLINE FINDINGS

1. PL-X1: This file is THE PRODUCER OF picks_log.csv that 5+ downstream files (hard_blocks, portfolio_risk_gate, evaluators, dashboards) ALL silently fail-open against (per Batch 9 PRG-21 / HB-11). So pick_logger.py is the upstream of a fragile downstream chain. Quality here matters disproportionately.
2. PL-X2: 56 fields in FIELDS tuple — the LARGEST schema in the codebase. Every pick row has 56 columns. Compared to MDG's CRITICAL_OFFICIAL_PICK_FIELDS (8 fields), pick_logger writes 7x more data. **This file IS the de-facto schema definition.** It should be the source-of-truth, but currently MDG and PL define different things.
3. PL-7: `LOG_PATH.parent.mkdir(parents=True, exist_ok=True)` runs at MODULE IMPORT TIME (line 12). Same pattern as Batch 6 M-IO1 (subprocess.run at module top). **Side effect on import.** Tests that import pick_logger create data/ directory unconditionally. Same anti-pattern as bootstrap_wisdom.
4. PL-12: Header migration logic (lines 44-71) compares lists with `==` on line 55. **Adding a new field to the END of FIELDS forces a full file rewrite.** For a 5-year picks_log.csv with thousands of rows, this is an O(n) operation triggered by a one-line edit to FIELDS. No incremental migration. Theme T6.
5. PL-22 (line 77): `csv.DictWriter(f, fieldnames=FIELDS).writeheader()` — but ON SUBSEQUENT writes (line 98), DictWriter is created with `extrasaction='ignore'`. **First-write doesn't have extrasaction='ignore', subsequent writes do.** Inconsistent. If first write ever sees extra keys, raises ValueError. Subsequent writes silently drop. Asymmetric error-handling.
6. PL-25 (line 100): `if p["ticker"] in existing_today: continue` — **`p["ticker"]` raises KeyError if pick has no ticker.** Crashes the whole batch. Other code defensively uses `.get("ticker")`. Single inconsistency. Bug.
7. PL-30 (line 116): `round(p.get("score", 0), 3)` — but `p.get("score")` could return None (composite is sometimes None per Batch 9 PRG-12). `round(None, 3)` raises TypeError. **Crash bug.** Should be `round(p.get("score") or 0, 3)`.
8. PL-X3: NO try/except anywhere in log_picks. If ANY pick is malformed, the whole batch dies (and the WHOLE file write is rolled back since "a" mode buffers internally for csv module). **Single bad pick = no logging at all = brain operates blind tomorrow.** Same disease pattern as Batch 6 M-WR12.

## src/pick_logger.py — LINE BY LINE

### Lines 1-5: Module docstring
- PL-1 GOOD: References Phase 2B.1 history. Documents header migration intent.
- PL-2 SMELL: "old rows get blanks" — sounds harmless but means migration is LOSSY for column renames (e.g., if "qty" became "quantity", old qty data is silently dropped because old "qty" column matches new "qty"... actually wait, this is APPEND-NEW only, not rename. OK as designed but undocumented edge case.)

### Lines 6-9: Imports
- PL-3 GOOD: Just stdlib. csv, datetime, Path, typing.
- PL-4 SMELL: No `from __future__ import annotations` like other files. Inconsistent style.

### Lines 11-12: LOG_PATH + mkdir
- PL-5 BUG (line 11): Path("data/picks_log.csv") — RELATIVE PATH. Same M-CFG1 / HB-10 / PRG-3 bug. Same hardcoded relative path now in 4 audited files.
- PL-6 GOOD (line 12): mkdir with parents=True, exist_ok=True — defensive.
- PL-7 BUG (line 12): **Runs at MODULE IMPORT TIME.** Same pattern as Batch 6 M-IO1 (bootstrap_wisdom subprocess at import). Side effect on import. Tests, linting, type-checking, anything that imports this module creates `data/` dir. Should be inside _ensure_header() or log_picks().

### Lines 14-41: FIELDS tuple (56 fields)
- PL-8 GOOD: Comprehensive schema. Best-documented in codebase.
- PL-9 GOOD: Inline comments group fields by phase ("Phase 2B.1 scale-out fields", "PILLAR 1 brain audit (E2b — May 4 2026)", etc.). Excellent archaeology.
- PL-10 BUG: 56 fields and NOT A SINGLE TYPE ANNOTATION. Each field is a string in CSV. No way to tell which fields are numeric, datetime, JSON-encoded, or freeform. Compare to MDG's CRITICAL_OFFICIAL_PICK_FIELDS (also untyped, but only 8 fields).
- PL-11 BUG: Field name `qty` here vs `quantity` in main.py / portfolio_risk_gate (PRG-71). **Schema drift across producer/consumer.** Confirmed cross-file: PRG line 71 reads `quantity` from candidate but pick_logger writes column `qty`. Then evaluators reading picks_log.csv get `qty`. Mismatch in either direction breaks one consumer.
- PL-12 BUG: Field name `score` here vs `composite` in PRG-58/parallel_scorer/scorer. **Same field, three names**: `composite` in scoring, `score` in pick_logger column. Theme T2.
- PL-13 BUG: Some fields have JSON-encoded values stored as strings (`tp_raises = "[]"` line 146, `sl_tightens = "[]"` line 148, smell_codes/severities/messages). **Mixing primitive and JSON-encoded columns in one CSV with no documentation of which is which.** Downstream parsers must know per-column.
- PL-14 BUG: 56 fields — but NO `notes`, `error`, `data_provider`, `provider_health` audit fields. The downstream debug story is poor.

### Lines 44-71: _migrate_header_if_needed
- PL-15 GOOD (lines 47-48): Empty/missing file early return.
- PL-16 BUG (line 49): `with LOG_PATH.open() as f:` — opens then reads then SEEKS BACK (line 58) AFTER closing the reader iterator. Inside `with` block. Works but unusual. line 58 `f.seek(0)` re-reads. Then `csv.DictReader(f)` re-iterates. Reads file TWICE.
- PL-17 BUG (line 55): `if existing_header == FIELDS: return` — **list-equality compare**. Works only if EXACT field order matches. Field reorder = full migration. May be intentional (forcing column-order consistency) but undocumented.
- PL-18 BUG (line 58-59): `f.seek(0); old_rows = list(csv.DictReader(f))` — loads ENTIRE picks_log.csv into memory. For 5-year log of 10k rows × 56 fields, ~5MB. Tolerable but unbounded.
- PL-19 BUG (lines 62-70): **REWRITES THE WHOLE FILE.** Single column added → entire file rewrite. No backup. **If the rewrite fails partway (disk full, permission, kill signal during write), picks_log.csv is corrupted/empty.** No atomic write (write-temp-then-rename). Single biggest data-loss risk in the codebase.
- PL-20 BUG (line 63): `extrasaction='ignore'` — old rows with EXTRA columns (deleted in new FIELDS) silently lose data. Could be intentional but undocumented.
- PL-21 BUG (lines 67-69): For loop fills missing new fields with empty string. Verbose but correct.
- PL-22 GOOD (line 71): print log of column count change.
- PL-23 BUG (line 71): `f"+{len(FIELDS) - len(existing_header)} new columns"` — assumes FIELDS is LARGER. For a column DELETION migration, prints negative number which reads weirdly (`+-2 new columns`). Edge case.

### Lines 74-79: _ensure_header
- PL-24 GOOD: Clear two-branch logic.
- PL-25 BUG (line 77): First-write uses `csv.DictWriter(f, fieldnames=FIELDS)` — NO `extrasaction='ignore'`. Subsequent writes (line 98) DO use it. **Asymmetric.** First write would CRASH on extra keys; subsequent silently drop. Should be consistent.

### Lines 82-178: log_picks
- PL-26 SMELL (line 82): `cape: Dict = None` — mutable default would be a bug. None default is OK but type-hinted as Dict (should be Optional[Dict]).
- PL-27 BUG (line 84): `_ensure_header()` called every log call. For each call, file is opened/checked. Tolerable but if migration is needed, it runs on EVERY call to log_picks (until the migration completes — which it does on first call). Wasteful but bounded.
- PL-28 GOOD (lines 85-87): timestamp captured ONCE at start.
- PL-29 BUG (lines 89-94): Read-existing-today loop scans the ENTIRE picks_log.csv to find today's tickers. **O(n) read for every log_picks call.** For 5-year log this is 10k row scan. Should be reverse-scan (start from end) and break on first non-today row, OR maintain a separate today-index.
- PL-30 BUG (line 91): `with LOG_PATH.open() as f:` — opens file. THEN line 97 opens for append. **File opened TWICE per call.**
- PL-31 BUG (line 93): `row["pick_date"]` — **KeyError if any row missing pick_date column.** A migration mid-flight or corrupted row crashes. Should be `row.get("pick_date")`.
- PL-32 BUG (line 100): `if p["ticker"] in existing_today: continue` — **KeyError if pick missing ticker.** Should be `p.get("ticker")`.
- PL-33 BUG (line 102-173): **MASSIVE 70-LINE DICT LITERAL** for w.writerow. No try/except. **One bad pick crashes the loop.** Picks AFTER the bad one are not written. CSV file is left in an INDETERMINATE STATE (some new rows written, some not, no header issues but mid-file truncation if buffering hadn't flushed). This is THE MOST FRAGILE WRITE PATH IN THE CODEBASE.
- PL-34 BUG (line 116): `round(p.get("score", 0), 3)` — `p.get("score")` could be None. `round(None, 3)` → TypeError. CRASH.
- PL-35 BUG (lines 105-173): SCORES of dual-source `or` would be needed. Currently only handles `score` (line 116) and `multiplier` (line 117) with defaults. Other fields (`entry`, `stop_loss`, `take_profit`) come through as p.get(X) — could be None. CSV writes None as empty string (works), but downstream readers comparing `float(row["entry"])` will crash on empty.
- PL-36 BUG (lines 109, 158, 143): `"true" if p.get(K) else "false"` — converts bool to string in 3 different places. Inconsistent with other bool-storage patterns elsewhere in codebase.
- PL-37 BUG (line 121): `risk_reward: p.get("risk_reward", 2.0)` — DEFAULTS TO 2.0! If pick has no R:R, log records 2.0 as if it were specified. **Audit trail lies** about what the pick actually claimed.
- PL-38 BUG (line 124): `regime: (regime or {}).get("regime") or "unknown"` — defensive double-fallback. ✅ pattern but `unknown` is Theme T11 (silent failure looks like data).
- PL-39 BUG (line 138): `tier_status: "none"` — magic string. Comment lists 5 valid values (none|tp1_hit|tp2_hit|trailing|closed). Should be ENUM, not string.
- PL-40 BUG (lines 140-142): `original_sl/current_sl/peak_price` initialized from p["stop_loss"]/p["entry"] — **but p["stop_loss"] is `p.get("stop_loss")` so could be None.** If None, original_sl/current_sl/peak_price are all None → CSV writes empty → downstream trailing-stop tracker (Phase 2B.2) reads empty → likely crashes.
- PL-41 BUG (line 143): `trail_active: "false"` — string, not bool. Inconsistent with Python bool semantics. Downstream check `if row["trail_active"]:` is True for both "true" AND "false" (non-empty string). Common bug.
- PL-42 BUG (line 146): `tp_raises: "[]"` — JSON-encoded list as string. Inconsistent with other columns. Downstream MUST know to json.loads.
- PL-43 BUG (line 148): `sl_tightens: "[]"` — same JSON-as-string. Two columns now do this.
- PL-44 BUG (lines 149-154): brain_* fields — comment "fixes silent extrasaction='ignore' drop". This means PRIOR to E2b, these fields existed in pick dict but were SILENTLY DROPPED by the writer because they weren't in FIELDS. **Confirms a class of bugs: any pick field added but not added to FIELDS is silently dropped on persistence.** Ongoing risk.
- PL-45 BUG (line 158): `is_monster: "true" if p.get("is_monster") else "false"` — same string-bool issue.
- PL-46 BUG (lines 160-162): smell_codes/severities/messages stored as STRINGS. Probably comma-joined upstream. NOT json-encoded like tp_raises/sl_tightens. **Two different serialization conventions in same CSV.** Inconsistent.
- PL-47 BUG (lines 164-166, 170-172): spy_close_at_exit, spy_return_pct, alpha_pct, sector_close_at_exit, sector_return_pct, sector_alpha_pct — all initialized to "" (empty). These are MEANT to be filled in later by the evaluator. **No marker distinguishes "not yet evaluated" from "evaluated but no data".** evaluation_status = "pending" handles this for top-level state but per-field state is ambiguous.
- PL-48 GOOD (lines 175-178): print summary of saved/skipped. Operator-friendly.
- PL-49 BUG: NO try/except around the whole log_picks. If ANY pick raises (PL-32, PL-34, PL-40), saved count is LIES — printed value is wrong, file may be truncated. Should at minimum wrap each pick's writerow in try/except with traceback log.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### PL-X1: pick_logger writes the data 5+ files silently fail-open against
Quality of pick_logger writes is THE upstream-quality-gate for:
- hard_blocks._get_recent_pick_dates (HB-11/HB-17)
- portfolio_risk_gate.load_open_positions_from_picks_log (PRG-21/PRG-25)
- evaluate_picks (root) reading picks_log
- app.py (Streamlit dashboard)
- Tests verifying contract

If pick_logger crashes mid-write OR migrates corruptly, all 5 silently degrade. **Single highest-impact fragility in the codebase.**

### PL-X2: 56-field FIELDS is the de-facto schema
But:
- Not type-annotated (PL-10)
- Field names diverge from producers (qty vs quantity PL-11; score vs composite PL-12)
- Some fields are JSON strings (PL-13)
- Some fields are bool-as-string (PL-36, PL-41, PL-45)
- Adding a field elsewhere in the code without updating FIELDS = silent drop (PL-44 confirmed bug pattern)

**This SHOULD be the canonical pick schema. It nearly is. Promote to TypedDict or Pydantic with field type info, then drive both writers AND readers from it.**

### PL-X3: No try/except in log_picks = single-bad-pick-takes-down-batch
Combined with main.py:1761-1789 lesson ("Brain operated blind 2026-05-02 to 2026-05-04"), the failure mode is exactly the one the author already identified and fixed in main.py but didn't propagate here. **Same Theme T1 as Batch 6.**

### PL-X4: File-rewrite migration without atomic write = data loss risk
Lines 62-70 rewrite picks_log.csv in place. No backup, no temp-and-rename. Single power loss / kill / disk-full mid-write = corrupted or empty file. **Recommend tempfile + os.replace pattern.**

### Cross-cutting confirmed: relative path bug now in 4 files
- src/hard_blocks PICKS_LOG_PATH (HB-10)
- src/portfolio_risk_gate PICKS_LOG_PATH (PRG-3)
- src/pick_logger LOG_PATH (PL-5)
- main.py M-CFG1 (Batch 6)
**Recommend src/_paths.py with module-relative resolution OR cwd-validation at startup.**

## SUMMARY (Batch 11)

| Severity | Count |
|---|---:|
| Show-stopper | 18 |
| Data/safety | 11 |
| Code smell | 7 |
| Good code | 9 |
| Total findings | 45 |

## TOP 10 CRITICAL FIXES from Batch 11

1. PL-33+49: Wrap each pick's writerow in try/except with traceback log. Single bad pick should not kill batch. (15 min, biggest reliability win)
2. PL-19: Atomic write via tempfile + os.replace for migration. (30 min)
3. PL-32+34+40: Replace `p["ticker"]` with `p.get("ticker") or "?"` and add None-guards on all numeric reads. (15 min)
4. PL-X2: Promote FIELDS to TypedDict / Pydantic with types; drive both writers and readers from it. (1-2 days, biggest architectural win this batch)
5. PL-7: Move `mkdir` from module top into _ensure_header(). (5 min)
6. PL-29: Reverse-scan today's tickers OR maintain index. O(n) → O(today's count). (30 min)
7. PL-37: Stop defaulting risk_reward to 2.0. Empty if missing — preserve audit trail integrity. (5 min)
8. PL-25: Make first-write and subsequent-write CONSISTENT in extrasaction handling. (5 min)
9. PL-44 ongoing: Add a CI test that asserts `set(pick.keys()) ⊆ FIELDS` for every pick produced — catches silent drops. (1 hr)
10. Cross-cutting: src/_paths.py for repo-relative path resolution. Eliminates 4 separate relative-path bugs. (15 min)

## NEW THEMES UPDATED

- Theme T1 (silent failure): NEW INSTANCE — log_picks no try/except = batch crash on single bad pick.
- Theme T2 (schema drift): pick_logger FIELDS vs producer field names confirmed in 2 places (qty vs quantity, score vs composite). De-facto schema exists, just not unified.
- Theme T6 (artifact lifecycle): full file rewrite for column add. Atomic-write missing.
- Theme T7 (inconsistent imports/orchestration): 4 files with relative path constants. Single _paths.py would consolidate.
- Theme T8 (DRY): 56-field FIELDS is duplicated implicitly across all readers (each reader hardcodes column names).

## PHASE A COMPLETE — FINAL TALLY

| File | Lines | Findings | Critical | Use as template? |
|---|---:|---:|---:|---|
| smell_faculty.py (Batch 7) | 271 | 28 | 9 | NO — 5/7 smells dead |
| parallel_scorer.py (Batch 8) | 177 | 48 | 22 | NO — God-function |
| hard_blocks.py (Batch 8) | 329 | 50 | 18 | NO — fail-open epidemic |
| premarket_sanity_gate.py (Batch 9) | 301 | 57 | 14 | PARTIAL — fail-closed branches good |
| portfolio_risk_gate.py (Batch 9) | 279 | 47 | 6 | YES — gold standard |
| missing_data_gate.py (Batch 10) | 163 | 28 | 6 | YES — collect-all-errors champion |
| premarket_readiness_gate.py (Batch 10) | 197 | 26 | 9 | PARTIAL — clean but 4× dict repetition |
| pick_logger.py (Batch 11) | 179 | 45 | 18 | NO — fragile writes |
| **Phase A total** | **1,896** | **329** | **102** | |

## PHASE A KEY INSIGHTS

1. **The codebase has THREE quality tiers:**
   - Gold (PRG, MDG): explicit fail-closed, named constants, audit-trail dicts, no bare-except
   - Silver (PSG, PRDY): mostly fail-closed but with magic numbers and dict-construction repetition
   - Lead (smell_faculty, parallel_scorer, hard_blocks, pick_logger): fail-open, schema drift, bare-except
   
2. **Quality correlates with HOW RECENTLY the file was authored.** PRG/MDG/PSG/PRDY all have `from __future__ import annotations` and consistent docstring template ("no fake picks, no paper trading, no live trading"). Older files (smell_faculty, hard_blocks, pick_logger) lack this discipline. **The author learned. Newer code is better. Older code needs back-porting.**

3. **The single highest-leverage architectural fix is a unified `pick` schema.**
   - Eliminates ~20 dual-source `or` chains across 5 gate files (Theme T2)
   - Eliminates 5 copies of _safe_float, 3 copies of _safe_int (Theme T8)
   - Promotes FIELDS to authoritative type-annotated definition
   - Catches silent field drops at producer time, not consumer time
   - Estimated effort: 1-2 days for Pydantic adoption

4. **The single highest-leverage operational fix is wrapping per-pick writes in try/except.** PL-33+49. 15 minutes. Eliminates entire class of "blind brain" outages.

5. **Phase A revealed 102 critical findings across 8 files.** Even at 30-min-per-fix average, that's ~50 hours of cleanup work just in safety/gates.

## COVERAGE TRACKER

| Phase | Status | Files in this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | **8/8 COMPLETE** | pick_logger | **8/8** |
| Total true line-by-line | | +1 file | **23 of 382** |
| Remaining | | | **359 files** |

## NEXT BATCH — PHASE B BEGINS

Batch 12: src/scorer.py + src/scoring_safety.py (composite scoring engine + safety wrappers around it). These are the most-referenced files from parallel_scorer (Batch 8 PS-16). After this:

- Batch 13: src/data_fetcher.py + src/indicators.py (data layer)
- Batch 14: src/market_data_health.py + src/market_calendar.py
- Batch 15: src/regime.py + src/calibration.py
- Batch 16: src/news_signals.py + src/news_engine.py + src/news_classifier.py
- Batch 17: Phase B remaining

End of Batch 11. Phase A complete.
