# Batch 47 — src/agent_memoir.py (194 lines) + src/book_ingest.py (194 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** agent_memoir.py (194 lines), book_ingest.py (194 lines)
**Phase:** E (subdirectory & ancillary) — Phase E resumes after gate-layer completion. Files 13 and 14 of ~50.

## TOP HEADLINE FINDINGS

1. AM-X1: agent_memoir.py is **THE PERSISTENT IDENTITY NARRATIVE** rewritten nightly. Per docstring lines 4-6: "founder insight: 'Agent should not forget its mistakes and learnings, the wins, and what its task is supposed to be.'" **READ-ONLY input + JSON output.** **A UNIQUE module — no peer in audit.** Joins gold-standard OBSERVE-MODE pattern but with NARRATIVE output rather than data.
2. AM-X2 (lines 24-29): **MISSION_STATEMENT module-level constant** — 5-line agent identity declaration. **Hardcoded.** Operator-friendly but a brain-pillar artifact in source code (not in config). Per Batch 23 SA-X1 brain-pillar architecture cross-cutting, the agent's "identity" lives in source rather than a data file.
3. AM-X3 (lines 140-160): **4-TIER ADAPTIVE NARRATIVE based on win_rate + sample size:**
   - n<30 → OBSERVATION MODE (matches Batch 22 SJ-X3 / Batch 44 CA-X4 statistical-validity cross-cutting)
   - win_rate<40% → study losses
   - win_rate≥50% → improve R-multiple
   - else → refine per-pattern stats
   **First-class operator narrative.** ✅
4. AM-X4 (line 187): **NO ATOMIC WRITE** for agent_memoir.json. Power loss mid-write = corrupt identity narrative. Per Batch 37 OPA-X5 cross-cutting. **Per cross-cutting tally now 4 of 20 audited writers safe.**
5. BI-X1: book_ingest.py is **THE T35 BOOKS-INTO-BRAIN LOADER** — reads `data/books/seed.yaml` and inserts each rule into wisdom_base.LESSONS with `source="book:<slug>"`. **Per Batch 25 wisdom_consultant cross-cutting**, this is the IDENTITY of the BookLessons referenced. **Idempotent** by (source, text) tuple — line 83.
6. BI-X2 (line 21): **`import yaml` at module level** — hard dependency. Per Batch 39 MN-X3 cross-cutting, NOT lazy. **A PyYAML install failure = import error at any caller of wisdom-base.** Should be lazy-imported inside load_seed_file.
7. BI-X3 (lines 152-189): **3-SUBCOMMAND CLI** (load-seed/list-books/stats) with --dry-run flag. **Joins gold-standard CLI club** (Batch 44 CA-X2, Batch 43 PE3-X2). **`load-seed --dry-run` is the OPERATOR-SAFETY flag** — allows operator to verify before mutating LESSONS. ✅

## src/agent_memoir.py — LINE BY LINE

### Lines 1-12: Module docstring
- AM-1 GOOD: 12-line docstring with **dated founder-quote archaeology** (2026-05-04). Per Batch 27 PV-X3 / Batch 38 DS-X3 cross-cutting bug-archaeology gold standard. **7th module with this discipline.**
- AM-2 GOOD (line 8-9): "NARRATED self-portrait the agent rewrites every night" — clear purpose.

### Lines 13-18: Imports
- AM-3 GOOD: Pure stdlib including TZ-aware datetime imports. ✅

### Lines 20-22: Path constants
- AM-4 BUG: 3 relative paths. **30th, 31st, 32nd files with this pattern** per cross-cutting tally.

### Lines 24-29: MISSION_STATEMENT
- AM-5 GOOD: Per AM-X2, 5-line mission statement. Operator-readable.
- AM-6 BUG: Hardcoded in source. **A founder rebrand would require code change + commit, not config edit.** Should be `data/mission.txt` loaded by write_memoir.

### Lines 32-36: _safe_float
- AM-7 BUG: Per Batch 45 MD-8 cross-cutting, **7th duplicate `_safe_float` helper.** Should consolidate to `src/_safe.py`.
- AM-8 GOOD (line 34): Extra falsy-string set {"none", "null"} — handles CSV-stringified None. Per Batch 28 NC cross-cutting Theme T2 schema-chaos.

### Lines 39-47: _load_closed_picks
- AM-9 GOOD: Filter to 4 terminal statuses (tp_hit, sl_hit, expired, day_close).
- AM-10 BUG (line 43): Opens picks_log.csv with default text mode. Per Batch 28 NC cross-cutting, should use `newline=""` for csv reads.
- AM-11 BUG (line 45): No `evaluation_status` schema-stability check. Per Batch 11 PL cross-cutting pick_logger schema chaos. A schema change = silent zero-result.

### Lines 50-62: _load_learning_events
- AM-12 GOOD: JSONL reader with per-line defensive try/except.
- AM-13 BUG (line 60): bare except `pass`. **Theme T1 undocumented.** Should be `json.JSONDecodeError`.
- AM-14 GOOD (line 57): Empty-line skip.

### Lines 65-83: _biggest_win
- AM-15 GOOD: 2-stage filter (parse R, keep positive).
- AM-16 GOOD (line 70): max() picks best.
- AM-17 GOOD (lines 77-82): **6-line NARRATIVE template** — operator-friendly first-person prose. ✅
- AM-18 BUG (line 78): `f"On {best.get('pick_date')}, I picked {best.get('ticker')}"` — if pick_date is None, prints `"On None, I picked ..."`. Defensive failure. **Should fallback to "an undated trade"** etc.

### Lines 86-110: _biggest_loss
- AM-19 GOOD: Mirror of _biggest_win — min picks worst.
- AM-20 GOOD (lines 92-98): **Earnings-proximity diagnostic** — if loss happened ≤7 days from earnings, narrate it as possible cause. **Forensic insight in narrative.** ✅
- AM-21 GOOD (lines 97-98): scoped (ValueError, TypeError) catch.
- AM-22 BUG (line 95): Magic 7 days-to-earnings threshold. Per Batch 31 HH-X3 cross-cutting. **Same magic 7 in Batch 23 SA / Batch 37 OPA-29.** Should be EARNINGS_PROXIMITY_DAYS const shared.
- AM-23 GOOD (lines 105-108): 3-line lesson narrative.

### Lines 113-129: _summarize_recent_learning
- AM-24 GOOD (line 114): TZ-aware UTC cutoff. ✅ **Joins TZ-aware module count = 8.**
- AM-25 GOOD (line 119): `.replace("Z", "+00:00")` — ISO Z-suffix defensive. Per Batch 41 WM-14 cross-cutting same pattern.
- AM-26 BUG (line 122): bare except `pass`. Theme T1 second instance in this file.
- AM-27 GOOD (lines 124-129): 4-key summary with 3 event-type counts.
- AM-28 BUG: Hardcoded `kind` enum values (`weight_applied`, `lesson_promoted`, `nightly_brain_run`) — schema-coupled to whatever writes learning_journal.jsonl. Per Batch 24 LJ.

### Lines 132-188: write_memoir
- AM-29 GOOD (lines 133-138): Stats computation with defensive `_safe_float(...) or 0`.
- AM-30 BUG (lines 135-136): Same `r_multiple > 0` win definition as Batch 44 CA-21. **Cross-module consistency.** ✅ But duplicated logic — should import from calibration.
- AM-31 GOOD: Per AM-X3, 4-tier narrative.
- AM-32 BUG (line 146, 151): Magic 0.40 and 0.50 win-rate thresholds. Magic 30 sample size. Per Batch 22 SJ-X3 + Batch 31 HH-X3 cross-cutting.
- AM-33 GOOD (lines 162-184): 9-key memoir dict with TZ-aware last_updated.
- AM-34 GOOD (line 163): `datetime.now(timezone.utc).isoformat()` — TZ-aware. ✅
- AM-35 GOOD (lines 174-178): "what_im_proud_of" narrative — 3 self-described disciplines. **Operator-readable agent self-knowledge.**
- AM-36 GOOD (lines 180-183): "promise_to_anjan" — direct address to founder. **Unique in audit.**
- AM-37 BUG (line 186-187): Per AM-X4, **NO ATOMIC WRITE.** `MEMOIR_PATH.write_text(json.dumps(memoir, indent=2))` — power loss mid-write = corrupt narrative.

### Lines 191-193: __main__
- AM-38 GOOD: Operator-runnable smoke test. Per Batch 41 WM-44 cross-cutting CLI pattern. **6th file with __main__.**

## src/book_ingest.py — LINE BY LINE

### Lines 1-14: Module docstring
- BI-1 GOOD: 14-line docstring with **T35 reference + CLI usage**. Per Batch 44 CA-1 + Batch 22 WP-1 dated/tagged-task documentation pattern.
- BI-2 GOOD (line 7-8): "Idempotent — won't double-insert" — operator-friendly invariant called out.

### Lines 15-23: Imports
- BI-3 BUG (line 21): Per BI-X2, `import yaml` at module level. Hard dependency.
- BI-4 GOOD (line 23): `from src.wisdom_base import add_lesson, LESSONS` — explicit named imports.

### Lines 28-37: load_seed_file
- BI-5 GOOD (line 31-32): Explicit FileNotFoundError.
- BI-6 GOOD (line 35-36): Explicit ValueError on missing 'books' key.
- BI-7 GOOD (line 34): `yaml.safe_load(f) or {}` — defensive None fallback.

### Lines 40-57: _existing_book_lessons
- BI-8 GOOD: Dedup-key set extraction.
- BI-9 GOOD (line 43): Missing LESSONS file → empty set.
- BI-10 GOOD (line 52): Scoped json.JSONDecodeError. ✅ NOT bare-except.
- BI-11 GOOD (line 55): Only book-sourced lessons in dedup set. **Other sources unaffected.** ✅
- BI-12 BUG: `LESSONS` is opened in default text mode without `newline=""`. Should match csv-style discipline.

### Lines 60-110: load_seed
- BI-13 GOOD (lines 60-65): Type-hinted with --dry-run support.
- BI-14 GOOD (lines 67): Idempotency via existing-set check.
- BI-15 GOOD (lines 73-77): 2-level nested iteration (books → rules).
- BI-16 GOOD (lines 79-82): Empty-text skip.
- BI-17 GOOD (lines 83-85): **Dedup-skip if (source, text) already present.** Per BI-X1 head finding.
- BI-18 GOOD (lines 86-90): Tag enrichment with `rule:<id>` for traceability.
- BI-19 GOOD (line 91): `float(rule.get("confidence", 0.85))` — magic 0.85 default but documented as wisdom-base norm.
- BI-20 BUG (line 91): Magic 0.85 default confidence. **Should reference wisdom_base const if exists.** Schema drift risk.
- BI-21 GOOD (lines 93-101): Dry-run skips actual add_lesson call but still counts as inserted. **Allows preview.** ✅
- BI-22 GOOD (lines 104-110): 5-key result dict with dry_run flag.

### Lines 113-124: list_books
- BI-23 GOOD: 5-field per-book summary for CLI display.
- BI-24 GOOD (line 121): `len(b.get("rules", []))` — defensive empty-list.

### Lines 127-147: book_stats
- BI-25 GOOD (line 130-131): Missing-LESSONS empty fallback.
- BI-26 GOOD (line 139): Scoped json.JSONDecodeError.
- BI-27 GOOD (line 141): **Filters `active=True`** — respects lesson deactivation. Per Batch 25 wisdom_consultant cross-cutting `active` semantics.
- BI-28 GOOD (line 145): `src.split(":", 1)[1]` — extracts slug safely with maxsplit=1.

### Lines 152-189: main (CLI)
- BI-29 GOOD: argparse with 3 subcommands.
- BI-30 GOOD (lines 168-170): **DRY-RUN prefix in output** — operator visibility. ✅
- BI-31 GOOD (line 175): Per-book column formatting.
- BI-32 GOOD (line 181-182): "no book-sourced lessons loaded yet — run `load-seed`" — operator-friendly empty-state hint.
- BI-33 GOOD (line 184): Sorted by count DESC.

### Lines 192-193: __main__
- BI-34 GOOD: `raise SystemExit(main())` — proper exit code propagation. Per Batch 44 CA-42 same pattern.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### AM-X3 + statistical-validity cross-cutting
4 modules with explicit min-sample-size guards now:
- pick_evaluator (Batch 27)
- weight_proposer (Batch 22)
- signal_journal (Batch 22 SJ-X3)
- calibration (Batch 44 CA-X4)
- agent_memoir (this batch AM-X3) — narrative-tier version of same threshold
**5 modules now share statistical hygiene.** **AM-X3 is the OPERATOR-FACING surface.**

### AM-X4 + Cross-cutting atomic-write tally update
Now **4 of 20 audited state-writers safe** (down from 4/19). agent_memoir adds 21st audited writer (UNSAFE).
**Tally:** 4 safe / 16 unsafe / 20 total = **80% UNSAFE writers.** Same gross figure but doc count keeps climbing.

### AM-7 + cross-cutting: `_safe_float` duplicate count update
Now **7 modules** with near-identical `_safe_float` helpers:
1. premarket_decision_contract (B36)
2. official_pick_artifact (B37)
3. missing_data_gate (B45)
4. premarket_readiness_gate (B45)
5. premarket_sanity_gate (B46)
6. portfolio_risk_gate (B46)
7. agent_memoir (this batch)

**7-file DRY violation.** Cumulative refactor saves ~80 lines.

### AM-22 + Cross-cutting: 7-day earnings threshold
- agent_memoir (this batch line 95): `int(d2e) <= 7`
- official_pick_artifact (B37 OPA-29): `EARNINGS_WITHIN_10_DAYS` flag at days < 10
- probability_engine (B43 PE3-22): `near` bucket = 4-7 days
**3 modules with 7-10 day earnings windows.** Slightly inconsistent. Should be shared `EARNINGS_PROXIMITY_NEAR_DAYS` const.

### AM-30 + cross-cutting: r_multiple > 0 win definition
Modules with explicit win-definition logic:
- calibration (B44 CA-21): `_is_win` function
- agent_memoir (this batch lines 135-136): inline `r_multiple > 0`
**2 modules with identical logic.** Should import `_is_win` from calibration.

### BI-X1 + Cross-cutting: 3-subcommand CLI pattern
Modules with mature argparse CLIs:
- weight_proposer (B22) — 4 subcommands
- calibration (B44 CA-X2) — 5 subcommands
- book_ingest (this batch) — 3 subcommands
- pattern_engine (B26 PE-X2) — 1 subcommand
**4 modules with operator CLIs.** Pattern emerging.

### BI-X2: yaml import dependency depth
PyYAML is required by:
- book_ingest (this batch)
- config loader (likely Batch 0 / main.py — not yet audited at this layer)
**Hard dependency confirmed.** Should document in requirements.txt rationale.

### Cross-cutting: bare-except this batch
- agent_memoir: 2 (AM-13, AM-26) — JSONL/datetime defenses
- book_ingest: 0 ✅ (uses scoped json.JSONDecodeError)

**Phase E resumed: 2 bare-excepts in 1 file, 0 in the other.**

### Cross-cutting: relative-path constants
- agent_memoir adds 3 (MEMOIR_PATH, PICKS_LOG, LEARNING_JOURNAL)
- book_ingest adds 1 (DEFAULT_SEED via Path)
**Now 33 files with relative-path constants.** Per cross-cutting tally cumulative.

### Cross-cutting: TZ-aware modules
agent_memoir adds 8th TZ-aware module. **8/95 audited = ~8.4%.**

### Cross-cutting: bug-archaeology gold standard
agent_memoir AM-1 "founder insight 2026-05-04" archaeology joins:
- pick_evaluator (B27)
- dedup_sender (B38)
- market_guard (B40)
- universe (B40)
- sector_benchmark (B42)
- data_fetcher (B42)
- agent_memoir (this batch)
**Now 7 modules with dated/quantified archaeology.**

## SUMMARY (Batch 47)

| Severity | agent_memoir | book_ingest | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 7 | 4 | 4 | 15 |
| Data/safety | 4 | 1 | 0 | 5 |
| Code smell | 1 | 0 | 0 | 1 |
| Good code | 25 | 30 | 0 | 55 |
| Total findings | 37 | 35 | 4 | 76 |

## TOP 10 CRITICAL FIXES from Batch 47

1. AM-X4 / AM-37: Add atomic write to write_memoir. (5 min)
2. AM-7 + cross-cutting: Extract `_safe_float` to `src/_safe.py`. Apply to 7 modules. (30 min — bundled with prior cross-cutting refactor.)
3. AM-6: Move MISSION_STATEMENT to `data/mission.txt` loaded by write_memoir. (10 min)
4. AM-13 + AM-26: Replace 2 bare-excepts with scoped exceptions. (5 min)
5. BI-3 / BI-X2: Lazy-import yaml inside load_seed_file. (3 min)
6. AM-22 + cross-cutting: Define `EARNINGS_PROXIMITY_NEAR_DAYS` const shared across 3 modules. (10 min)
7. AM-30 + cross-cutting: Import `_is_win` from calibration into agent_memoir. (5 min)
8. AM-32 + AM-11: Document magic 0.40/0.50/30 win-rate thresholds with archaeology. (5 min)
9. BI-20: Reference wisdom_base default-confidence const instead of hardcoding 0.85. (5 min)
10. AM-18: Fallback narrative when pick_date is None ("an undated trade"). (3 min)

## NEW THEMES UPDATED

- **Theme T1 (bare except):** agent_memoir 2 (data-defense intent, undocumented). book_ingest 0 ✅. **Phase E resumed clean-ish.**
- **Theme T2 (schema drift):** AM-11 evaluation_status enum coupling. AM-28 kind enum coupling. BI-20 confidence default coupling.
- **Theme T6 (atomic writes):** AM-X4 adds 21st unsafe writer. **80% UNSAFE confirmed.**
- **Theme T8 (DRY):** `_safe_float` now in 7 modules. **80-line refactor opportunity.**
- **Theme T11 (fail-open by accident):** N/A this batch (pure reporting).
- **Theme T13 (silent-default-fills):** AM-9 4-status filter — what if a new terminal status added?
- **Theme T14 (gold-standard patterns):** agent_memoir AM-X1 narrative identity + AM-X3 4-tier adaptive narrative + AM-1 founder-quote archaeology. book_ingest BI-X3 3-subcommand CLI with --dry-run + BI-X1 idempotent dedup. **Both files = templates for self-aware brain modules.**

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A | 8/8 COMPLETE | (none) | 8/8 |
| Phase B | 18/18 COMPLETE | (none) | 18/18 |
| Phase C | 12/12 COMPLETE | (none) | 12/12 |
| Phase D | 30/~30 COMPLETE | (none) | 30/~30 |
| Phase E | 14/~50 done | agent_memoir, book_ingest | 14/~50 |
| Total true line-by-line | | +2 files | **97 of ~382 (~25.4%)** |
| Remaining | | | **~285 files** |

**25% milestone confirmed. Phase E in progress.**

## NEXT BATCH

Batch 48 (doc #54): Continue Phase E. Two strong candidates clustered around brain layer:
- **`src/lesson_gc.py` (4.9KB)** — wisdom_base garbage collector (consumes Batch 25 wisdom_consultant lesson schema)
- **`src/hypothesis_engine.py` (6.9KB)** — observe-mode hypothesis engine, brain-adjacent
Will pick `lesson_gc.py + hypothesis_engine.py` to close out the wisdom-layer audit.

End of Batch 47. Phase E in progress (14/50). **25.4% audit milestone.**
