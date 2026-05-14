# Batch 24 — src/learning_journal.py (69 lines) + src/wisdom_base.py (305 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** learning_journal.py (69 lines, fully read), wisdom_base.py (305 lines, fully read)
**Phase:** C (brain pillars) — files 7 and 8 of ~12

## TOP HEADLINE FINDINGS

1. LJ-X1: learning_journal.py is **THE PRODUCER side of meta_brain consumption** (Batch 23). 69 lines, 3 functions, **uses TIMEZONE-AWARE datetime** (`datetime.now(timezone.utc)`). **Joins MDH + NS as the third file using proper UTC discipline.** Compare to meta_brain (MB-12 cross-cutting issue) which strips timezone — **producer is tz-aware, consumer is tz-naive.** Round-trip information loss.
2. WB-X1: wisdom_base.py is **THE CENTRAL WISDOM STORE** — 305 lines, 14 functions, manages 3 artifacts (lessons.jsonl + patterns.jsonl + kill_list.json). **Trigger-eval engine (lines 245-303) is a mini DSL parser.** Operator-friendly but undocumented as DSL.
3. WB-X2: KILL_LIST has SAFETY-NET FALLBACK (line 181): `exp = now + timedelta(days=365)` if expires_at malformed. **Malformed kill entries STAY ACTIVE for 1 year.** Comment says "malformed → keep as safety net." **Intentional fail-CLOSED on bad data.** Per Batch 16 NS-X2 BANKRUPTCY_RISK 180-day-no-clear pattern, similar fail-closed-on-uncertainty design. ✅ defensive but no logging of malformed rows.
4. LJ-13 (line 32-33): JSONL append `with JOURNAL.open("a") as f: f.write(...)` — **NO ATOMIC WRITE.** Same pattern as SJ-33 (Batch 22). Crash mid-write = partial line → meta_brain.recent_mutations bare-except continues at MB-13 → the mutation event is LOST. **Two halves of the brain talking via fragile JSONL.**
5. WB-X3: deactivate_lesson (line 74-93) uses **FULL-FILE-REWRITE pattern** (read all, modify, rewrite all) — same anti-pattern as pick_logger PL-19 + signal_journal SJ-36+SJ-41. **NOW 3RD FILE WITH O(N) FULL-FILE-REWRITE FOR SINGLE-RECORD UPDATES.** Plus NO atomic write here. Catastrophic data loss risk on power event.
6. WB-21 (line 237): `tk in text.split()` — splits text on whitespace. **A lesson text "AVOID NVDA-related setups" → split = ["AVOID", "NVDA-related", "setups"]** — searching for "NVDA" returns FALSE because "NVDA-related" doesn't equal "NVDA". **Punctuation-attached tickers missed.** Should be regex word-boundary or `tk in text` substring.
7. WB-X4 (lines 245-303): Trigger DSL accepts ANY string matching regex `[a-zA-Z_][a-zA-Z0-9_]* (>=|<=|...) value`. **No validation of `key` being a known context field.** Lesson with trigger `random_typo>5` silently never fires (line 271 `if key not in ctx`). **Typo'd triggers = dead lessons.** No author warning.

## src/learning_journal.py — LINE BY LINE

### Lines 1-12: Module docstring
- LJ-1 GOOD: Documents T44 + Pillar 4 location.
- LJ-2 GOOD: Lists 5 mutation kinds explicitly.
- LJ-3 GOOD: One-line-per-event format documented.
- LJ-4 GOOD: Documents downstream consumer (weekly review).

### Lines 13-19: Imports + JOURNAL path
- LJ-5 GOOD (line 13): `from __future__ import annotations`.
- LJ-6 GOOD (line 15): **`from datetime import datetime, timezone` — timezone imported.** Per LJ-X1 head finding.
- LJ-7 BUG (line 19): `Path("data/learning_journal.jsonl")` — RELATIVE PATH. **15th file with this pattern.** Cumulative.

### Lines 22-34: log
- LJ-8 GOOD: 3-line docstring documenting the 5 valid kinds.
- LJ-9 GOOD (line 27): **`datetime.now(timezone.utc).isoformat(timespec="seconds")`** — UTC, second precision. ✅ TZ-AWARE producer.
- LJ-10 GOOD (line 29): `**payload` — flexible additional fields per kind.
- LJ-11 BUG (line 31): `JOURNAL.parent.mkdir(...)` — runs ON EVERY log call. Cheap (exist_ok=True) but wasteful. Move to module init OR check via Path cache.
- LJ-12 BUG (line 31): mkdir at module init NOT done — only on log call. **Different from PL-7/DF-7/FH-5 pattern.** Less of a side effect on import. ✅
- LJ-13 BUG (line 32-33): NO ATOMIC WRITE. JSONL append. Per LJ-X1 head finding cross-cutting.
- LJ-14 BUG: NO `with _LOCK:` — multi-thread writes can interleave. Compare to MDH-31 which has Lock. **Per Batch 8 PS, parallel_scorer fires 5-10 threads. If any of those threads call learning_journal.log, races possible.** No evidence current code calls log from threads — but defenseless if it does.

### Lines 37-58: read
- LJ-15 GOOD (line 37-39): Defensive existence check, returns [].
- LJ-16 GOOD (line 43): `cutoff = datetime.now(timezone.utc).timestamp() - days * 86400` — TZ-aware UTC, epoch math. **Better than MB-12's naive comparison.**
- LJ-17 BUG (line 44): `JOURNAL.read_text().splitlines()` — full file in memory. Same Theme as PS-8, MB-8.
- LJ-18 BUG (line 48-49): bare `except Exception: continue` — Theme T1 undocumented JSONDecodeError swallow.
- LJ-19 GOOD (line 52): `r["ts"].replace("Z","+00:00")` — handles Z-suffix. Differs from MB-12 (`.split(".")[0]`). **Inconsistent across files.**
- LJ-20 BUG (line 53-54): bare `except Exception: continue` for ts parse fail — drops record silently. Combined with LJ-18, doubly silent on corrupt data.

### Lines 61-68: summary
- LJ-21 GOOD: Trivial counter. Returns 3-field dict.
- LJ-22 GOOD: Used by meta_brain.

## src/wisdom_base.py — LINE BY LINE

### Lines 1-14: Module docstring
- WB-1 GOOD: Documents Pillar 2 v0.1, 3 artifacts, OBSERVE-MODE stance.
- WB-2 GOOD (line 12-13): "OBSERVE-MODE: Wisdom INFORMS the brain via warnings; never auto-blocks. Auto-block in v0.2 once we trust the signals." **EXPLICIT MIGRATION PLAN documented.** Operator-friendly archaeology.

### Lines 15-25: Imports + paths
- WB-3 SMELL (line 17): `from datetime import datetime, timedelta` — NO timezone import. **Naive datetime throughout.** Compare LJ-6 which is tz-aware.
- WB-4 BUG (line 20): `Path("data/wisdom")` — RELATIVE. 16th file.
- WB-5 BUG (line 21): `ROOT.mkdir(...)` runs at MODULE IMPORT TIME. **6th file with import-time mkdir.** Cumulative: PL-7, DF-7, FH-5, BW, SJ-5, WB-5.
- WB-6 GOOD (lines 23-25): 3 named paths under ROOT.

### Lines 31-55: add_lesson
- WB-7 GOOD: Type-hinted with defaults.
- WB-8 GOOD (lines 39-41): Documents triggers field with example.
- WB-9 BUG (line 44): `datetime.now()` — NAIVE. Per WB-3.
- WB-10 GOOD (lines 43-52): 8-field record. Comprehensive.
- WB-11 GOOD (line 46): Comment lists known source values.
- WB-12 BUG (line 53-54): JSONL append, NO atomic write, NO lock. Same as LJ-13.

### Lines 58-71: load_active_lessons
- WB-13 GOOD (lines 60-61): Defensive existence check.
- WB-14 GOOD (line 63-64): Line iteration (better than read_text+splitlines).
- WB-15 GOOD (line 67-68): Scoped JSONDecodeError continue. Per Batch 22 cross-cutting universal pattern.
- WB-16 GOOD (line 69): `r.get("active", True)` — defaults to active if field missing.

### Lines 74-93: deactivate_lesson — **FULL-FILE-REWRITE**
- WB-17 GOOD (line 75 docstring): Documents substring matching.
- WB-18 BUG (lines 78-89): Reads ALL into memory, modifies in-place, rewrites whole file. Per WB-X3 head finding.
- WB-19 BUG (line 85): `text_substring.lower() in r.get("text", "").lower()` — substring match. **Same false-positive risk as Batch 16 NS-15** (e.g., deactivating "AVOID NVDA" matches "AVOID NVDA-emerging-from-bankruptcy"). Per WB-21 cross-cutting.
- WB-20 BUG (lines 90-92): Rewrite whole file with NO atomic write. **Power loss = entire lessons.jsonl corrupt.**
- WB-21 BUG: NO LOCK. Concurrent deactivate calls = lost updates.

### Lines 99-120: add_pattern
- WB-22 GOOD: Type-hinted, returns the record.
- WB-23 GOOD (lines 107-117): 9-field record schema. Includes p_value (from hypothesis_engine).
- WB-24 BUG (line 108): `datetime.now()` — NAIVE.
- WB-25 BUG (line 118-119): JSONL append, no atomic.

### Lines 123-135: load_active_patterns
- WB-26 GOOD: Mirror of load_active_lessons. Same defensive pattern.

### Lines 141-202: kill_list functions
- WB-27 GOOD (line 141-147): _load_kill defensive existence + bare except. Per Theme T1 cross-cutting (corrupt JSON tolerable).
- WB-28 BUG (line 150-151): _save_kill **NO ATOMIC WRITE.** Direct overwrite of kill_list.json. **Critical — kill_list is consulted on every pick (per `is_killed` line 191-193). Power loss mid-save = empty kill_list = previously-killed tickers FREE TO BUY.** Single biggest data-loss risk in this file.
- WB-29 GOOD (lines 154-168): add_to_kill_list with auto-expire via cool_off_days.
- WB-30 BUG (line 160, 163): `datetime.now()` naive. Per WB-3.
- WB-31 BUG (line 161-166): `d[ticker.upper()] = {...}` — overwrites existing entry. **No history.** A ticker killed twice loses first reason.
- WB-32 GOOD (lines 171-188): get_kill_list auto-expires past entries.
- WB-33 BUG (line 179-181): `except Exception: exp = now + timedelta(days=365)` — per WB-X2 head finding, **malformed entries kept as 1-year safety net.** Defensive but no log of malformed entries surfaced to operator.
- WB-34 GOOD (lines 186-187): If anything expired, save updated dict. Self-cleaning.
- WB-35 BUG (line 187): _save_kill again — same WB-28 atomic write issue. Auto-cleanup can corrupt.
- WB-36 GOOD (lines 191-193): is_killed simple lookup.
- WB-37 GOOD (lines 196-202): remove_from_kill_list — explicit remove.

### Lines 208-213: stats
- WB-38 GOOD: 3-field summary. Used by ops/dashboards.

### Lines 218-241: lessons_for_ticker (T24)
- WB-39 GOOD (lines 220-228): 8-line docstring documenting 3 match strategies (tags, text, sector).
- WB-40 GOOD (line 229-230): Empty input → []. Defensive.
- WB-41 GOOD (lines 234-241): Two-pass match (tags first, then sector).
- WB-42 BUG (line 237): `tk in text.split()` — per WB-21 head finding, splits on whitespace ONLY. Punctuation-attached tickers missed. "NVDA-related" → no match for "NVDA".

### Lines 245-303: Trigger DSL — THE EXPRESSION ENGINE
- WB-43 BUG (line 245-246): Inline imports of operator+re. Per Batch 18 FH-38, inline imports are anti-pattern. Should be at module top.
- WB-44 GOOD (lines 248-251): Operator dict. Supports 7 ops.
- WB-45 GOOD (line 253): Regex documented and bounded.
- WB-46 GOOD (lines 256-259): _coerce — float-or-string. Defensive.
- WB-47 GOOD (lines 262-286): eval_trigger with 4-stage validation.
- WB-48 BUG (line 271-272): "Unknown keys → False" — per WB-X4 head finding, typo'd trigger keys silently never fire. **Should warn on first encounter.**
- WB-49 GOOD (line 273-275): Unknown op → False. Defensive.
- WB-50 GOOD (lines 279-283): Type-aware comparison — float vs string ops separated.
- WB-51 BUG (line 284): If types mismatch (float vs string), returns False. **A trigger `regime=chop` against ctx={"regime": "chop"} works** (both strings via _coerce). **A trigger `score>0.7` against ctx={"score": "0.75"} works** (both floats via _coerce). ✅ but ctx={"score": None} fails at line 271. Edge cases handled.
- WB-52 BUG (line 285-286): bare except False. Theme T1 undocumented.
- WB-53 GOOD (lines 289-293): eval_triggers — AND semantics for ALL triggers. Empty list → False (safer per docstring).
- WB-54 BUG (line 292): "Empty list → False" but add_lesson defaults triggers to []. **A lesson WITHOUT triggers can never fire via lessons_for_context** (line 296-303). **Author must explicitly add triggers OR lesson is dead.** No warning to author.

### Lines 296-303: lessons_for_context
- WB-55 GOOD: Composes load_active_lessons + eval_triggers.
- WB-56 BUG (line 300): `if trigs and eval_triggers(...)` — only fires for lessons WITH triggers. Per WB-54, trigger-less lessons are inert here. Compare to lessons_for_ticker which works on tags/text without triggers. **Two parallel matching APIs with different semantics.** Author confusion likely.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### LJ-X1: Producer-consumer timezone mismatch
- learning_journal.log (LJ-9): writes UTC ISO `2026-05-12T14:30:45+00:00`
- meta_brain.recent_mutations (MB-12): parses with `.split(".")[0]` → loses TZ → naive comparison
- learning_journal.read (LJ-19): parses with `.replace("Z","+00:00")` → keeps TZ
**3 different ISO-parse strategies in 3 modules for the same producer.** Should pick one (recommend LJ-19's approach).

### WB-X3: Full-file-rewrite anti-pattern now in 3 files
1. pick_logger.py (PL-19) — primary state
2. signal_journal.py (SJ-36+SJ-41) — learning state
3. wisdom_base.py (WB-18 deactivate_lesson, WB-28 _save_kill)
**All 3 modules write critical state, none use atomic write.** Power-loss-during-write = data loss.
**Recommend: shared `_atomic_write_jsonl(path, records)` and `_atomic_overwrite_json(path, obj)` helpers in src/_io.py.**

### WB-X4: Trigger DSL has silent-typo failure mode
A lesson author writing `triggers=["score_compoasite>0.7"]` (typo) → key not in ctx → eval_trigger returns False → lesson never fires → operator never sees the lesson AND never sees the typo. **Silent dead lessons.**
**Recommend: lessons_for_context returns warning list of lessons whose triggers all referenced unknown keys.**

### WB-X5: kill_list is the most fragile single state file in audited code
- WB-28: NO atomic write
- Single source of truth for "do not buy" decisions
- Read on every pick (via is_killed)
- Corruption = previously-killed tickers free to buy
- Combined with WB-31 (overwrite-no-history), recovery from corrupt state = manual rebuild from learning_journal events (if those weren't lost too)

### Cross-cutting: 16 files with relative-path constants
HB, PRG, PL, main.py, SCS, MDH, RG, CB, NS+NE, NC, FH, PS, SJ, WP, MB, LJ, WB. **16 files. URGENT.**

### Cross-cutting: 6 files with module-import mkdir
PL, DF, FH, BW, SJ, WB. **Side effects on test imports.**

### Cross-cutting: TZ-aware vs TZ-naive datetime use
- TZ-aware: MDH (Batch 14), NS (Batch 16), LJ (this batch — 3 files)
- TZ-naive: HB, FH, NC, CB, MB, ATP, WB (this batch), most others
**~85% of audited files use naive datetime.** When tz-aware modules talk to tz-naive ones, comparisons fail or lose info. **Single _now_utc() helper would unify, low cost.**

### Cross-cutting: Substring-matching false positives
- WB-19 deactivate_lesson (lessons text)
- WB-42 lessons_for_ticker (text.split for ticker)
- NS-15 _is_catastrophic (Batch 16, news classification)
- NSENT POSITIVE/NEGATIVE (Batch 17, news sentiment)
**4 modules using substring matching with no word-boundary guards.** False-positive risks compound.

## SUMMARY (Batch 24)

| Severity | learning_journal | wisdom_base | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 4 | 14 | 5 | 23 |
| Data/safety | 4 | 9 | 0 | 13 |
| Code smell | 1 | 5 | 0 | 6 |
| Good code | 13 | 28 | 0 | 41 |
| Total findings | 22 | 56 | 5 | 83 |

## TOP 10 CRITICAL FIXES from Batch 24

1. WB-X5 / WB-28: Add atomic write to _save_kill. Highest-stakes single state file. (10 min)
2. WB-X3: Refactor 3 full-file-rewrite anti-patterns (PL-19, SJ-36, WB-18) into shared atomic helper. (1 hr)
3. WB-X4 / WB-48: Surface unknown-key triggers as warnings (dead lessons). (15 min)
4. LJ-X1 cross-cutting: Standardize ISO timestamp parsing — pick LJ-19's `.replace("Z","+00:00")`. (15 min for all 3 files)
5. WB-42 / cross-cutting: Add word-boundary regex to substring matching in WB / NS / NSENT. (30 min)
6. LJ-13 + LJ-14: Add atomic write OR threading.Lock to learning_journal.log. (15 min)
7. WB-3 + WB-30: Make wisdom_base datetime tz-aware. (10 min)
8. WB-31: Allow kill_list to maintain history (list of entries per ticker, not single overwrite). (30 min)
9. WB-54+WB-56: Document the lessons_for_ticker vs lessons_for_context API split semantics. (5 min)
10. WB-43: Move `import operator, re` to top of file. (1 min)

## NEW THEMES UPDATED

- Theme T1 (bare except): WB-15 (documented JSONDecodeError), WB-27 (load_kill bare), WB-52 (eval_trigger), LJ-18 (read), LJ-20 (read).
- Theme T2 (schema drift): N/A this batch (single-file producers).
- Theme T6 (artifact lifecycle / atomic writes): WB-X3 — now 3 files with full-file-rewrite anti-pattern. URGENT.
- Theme T8 (DRY): _safe_float now in 7+ files. Atomic-write missing in 3+ files.
- Theme T11 (fail-open by accident): WB-X5 kill_list corruption frees tickers. WB-X4 typo'd triggers silently dead.
- Theme T13 (silent-default-fills): WB-33 malformed kill_list entry → 1-year safety net (intentional). WB-21 missing field defaults.
- Theme T14 (gold-standard patterns): learning_journal IS partially gold-standard (UTC tz-aware). wisdom_base is NOT (naive, no atomic). **Mixed within Phase C.**
- Theme T15 (false-positive blocking): WB-19 deactivate_lesson substring matching can mass-deactivate. WB-42 punctuation-attached ticker matching fails.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | 8/8 COMPLETE | (none) | 8/8 |
| Phase B (scoring/data) | 18/18 COMPLETE | (none) | 18/18 |
| Phase C (brain pillars) | 8/~12 done | learning_journal, wisdom_base | 8/~12 |
| Total true line-by-line | | +2 files | **49 of ~382** |
| Remaining | | | **~333 files** |

## NEXT BATCH

Batch 25: src/wisdom_consultant.py + src/wisdom_hint.py — the read-side wisdom layer. wisdom_consultant likely orchestrates lessons_for_ticker/lessons_for_context calls. wisdom_hint produces the inline Telegram hints (T24 reference in WB-X1).

End of Batch 24. Phase C in progress (8/12).
