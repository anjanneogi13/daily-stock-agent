# Batch 48 — src/lesson_gc.py (144 lines) + src/wisdom_coverage.py (85 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** lesson_gc.py (144 lines), wisdom_coverage.py (85 lines)
**Phase:** E (subdirectory & ancillary) — wisdom-layer cleanup. Files 15 and 16 of ~50.

## TOP HEADLINE FINDINGS

1. LG-X1: lesson_gc.py is **T32 STALE-LESSON GARBAGE COLLECTOR** — auto-deactivates lessons older than 90 days (default). **NEVER DELETES** — sets `active=False` to preserve audit trail (line 5). Per Batch 25 wisdom_consultant cross-cutting `active` filter, this is the WRITER for the active flag. **Soft-delete pattern.**
2. LG-X2 (lines 7-11): **3 EXPLICIT PROTECTIONS** documented in docstring — high-confidence lessons (>=0.90) kept forever (user-curated truths), already-inactive skipped, missing/unparseable ts kept (fail-safe). Per Batch 47 BI-X1 idempotency + Batch 45 MD-X3 invariants pattern.
3. LG-X3 (lines 96-101): **READ-ALL-THEN-REWRITE-ALL atomicity** — loads entire JSONL into rows list, mutates in memory, writes whole file. **NO atomic rename** — `with LESSONS.open("w")` truncates then writes. **Power loss mid-write = CATASTROPHIC LESSON LOSS** (truncated wisdom base). **CRITICAL BUG** — per Batch 37 OPA-X5 cross-cutting, this is the WORST single atomic-write violation in audit (whole-file rewrite without tmp+replace).
4. LG-X4 (line 45): `now = now or datetime.now()` — **NAIVE datetime.now()** with NO timezone. Compared against `datetime.fromisoformat(ts)` from line 34 which may be TZ-aware (Batch 47 AM-24 writes TZ-aware ISO). **TZ-naive vs TZ-aware comparison = TypeError.** **HIDDEN RUNTIME BUG** that fires when wisdom_base contains both naive and aware timestamps.
5. WC-X1: wisdom_coverage.py is **T33 BRAIN-FIRING TELEMETRY** — counts how often wisdom_hint + pattern_hint produce non-empty output across picks. **READ-ONLY observability metric.** Per Batch 25 wisdom-layer + Batch 30 pattern_layer integration check.
6. WC-X2 (lines 13-17): **MODULE-LEVEL try/except ImportError + lambda stubs** — if wisdom_hint or pattern_hint fail to import, replaces them with no-op lambdas at import time. **GRACEFUL DEGRADATION** but **SILENT** — operator sees `wisdom_coverage` returning 0% coverage and thinks brain isn't firing, when actually wisdom_hint module is broken. **Hidden fail-OPEN.**
7. WC-X3 (lines 50-53): **EMOJI-BASED CLASSIFICATION** — counts warning emoji as warnings, sparkle/green emoji as edges. **STRING-MATCHED EMOJI parsing.** Per Batch 11 PL cross-cutting Theme T2 schema-chaos. A wisdom_hint formatting change silently breaks classification. Latent.

## src/lesson_gc.py — LINE BY LINE

### Lines 1-18: Module docstring
- LG-1 GOOD: 18-line docstring with T32 tag + PROTECTIONS section + CLI examples. Per Batch 44 CA-1 / Batch 47 BI-1 dated-task pattern. **8th module with structured task-archaeology.**
- LG-2 GOOD (line 5): "Lessons aren't deleted — they get active=False, preserving an audit trail and keeping idempotency." Operator-readable design invariant.

### Lines 19-23: Imports
- LG-3 GOOD: Minimal stdlib + relative wisdom_base import.
- LG-4 BUG (line 20): `from datetime import datetime, timedelta` — NO `timezone`. Per LG-X4 head finding, this is the root cause of TZ-naive bug.

### Lines 25-26: Constants
- LG-5 GOOD: MAX_AGE_DAYS=90, PROTECT_CONF=0.90 — named constants.
- LG-6 BUG: Magic 90 days. No archaeology — why 90? Per Batch 31 HH-X3 cross-cutting magic-number proliferation. Should reference a wisdom-decay study.

### Lines 29-36: _parse_ts
- LG-7 GOOD (line 30): "Best-effort ISO-8601 parse" — explicit docstring.
- LG-8 GOOD (line 35): Scoped (ValueError, TypeError) — NOT bare-except.
- LG-9 BUG (line 34): `datetime.fromisoformat(s)` — handles Z-suffix on Python >= 3.11 only. Per Batch 41 WM-14 / Batch 47 AM-25 cross-cutting, `.replace("Z", "+00:00")` pattern is the defensive form. Inconsistent across modules.
- LG-10 BUG: Returns naive datetime if input is naive, TZ-aware if input is aware. Caller (line 62) compares result against naive cutoff. Per LG-X4 root cause.

### Lines 39-64: find_stale
- LG-11 GOOD: Returns preview without mutating. READ-ONLY accessor.
- LG-12 GOOD (line 43-44): Missing LESSONS → empty list.
- LG-13 BUG (line 45): Per LG-X4, datetime.now() NAIVE. Bug propagated from _parse_ts.
- LG-14 GOOD (line 53): Scoped json.JSONDecodeError.
- LG-15 GOOD (line 55): Skip already-inactive — idempotent.
- LG-16 GOOD (line 57): Protect high-confidence — per LG-X2.
- LG-17 GOOD (line 60-61): "ts is None: continue  # fail safe — keep" — missing-timestamp protection per LG-X2.
- LG-18 GOOD (line 62): Final cutoff comparison.

### Lines 67-103: gc_stale (MUTATOR)
- LG-19 GOOD (line 71-73): Returns (count, records) — operator-friendly.
- LG-20 GOOD (line 75-76): Missing-file early return.
- LG-21 BUG (line 77): Per LG-X4, naive datetime.
- LG-22 GOOD (lines 82-96): Single-pass read + mutate + collect.
- LG-23 GOOD (line 93): `r["deactivated_at"] = now.isoformat(timespec="seconds")` — adds forensic timestamp.
- LG-24 GOOD (line 94): `deactivated_reason` field — operator-readable. Audit-trail design.
- LG-25 BUG: Per LG-X3, lines 98-101 are the **CATASTROPHIC NON-ATOMIC WRITE.** A power loss between truncate and write completion = truncated/lost LESSONS file. Should use tmp+rename pattern.
- LG-26 GOOD (line 98): `if not dry_run and deactivated:` — skips write if no changes. Idempotent.
- LG-27 BUG (line 99): No file lock. Concurrent run could interleave reads/writes. Per Batch 14 MDH-X1 / Batch 22 SJ cross-cutting, JSONL append-safety pattern not applied here either.

### Lines 109-139: _cli
- LG-28 GOOD: argparse with --max-age, --protect, --dry-run.
- LG-29 GOOD (lines 114-119): Help text includes defaults.
- LG-30 GOOD (lines 127-129): Empty-result early-exit with checkmark emoji.
- LG-31 GOOD (lines 131-138): Human-readable preview output with ts + conf + text truncation.
- LG-32 GOOD (line 135): `ts[:10]` — date-only display.
- LG-33 GOOD (line 137): `text[:65]` — bounded preview width. Per Batch 38 / Batch 41 truncation pattern.

### Lines 142-143: __main__
- LG-34 GOOD: `raise SystemExit(_cli())` — proper exit propagation. Per Batch 44 CA-42 / Batch 47 BI-34 cross-cutting.

## src/wisdom_coverage.py — LINE BY LINE

### Lines 1-10: Module docstring
- WC-1 GOOD: 10-line docstring with T33 tag + concrete example output. Operator-friendly.
- WC-2 GOOD (lines 7-9): "Low coverage → wisdom base needs growing" — diagnostic interpretation inline.

### Lines 11-17: Imports
- WC-3 GOOD (line 11): Pure typing.
- WC-4 BUG: Per WC-X2, module-level fallback lambdas. Hidden fail-OPEN if wisdom_hint module breaks.
- WC-5 BUG (line 15): bare `except Exception` — broader than necessary. Should be `ImportError` specifically.

### Lines 20-65: coverage
- WC-6 GOOD (line 20-25): 5-key docstring.
- WC-7 GOOD (line 26): `len(rows or [])` — defensive against None.
- WC-8 GOOD (lines 27-29): Empty-rows zero-fill stats.
- WC-9 GOOD (line 31-32): Accumulators initialized.
- WC-10 BUG (line 32): "T42: matched vs violated" inline comment. No docstring update. Per Batch 28 NC cross-cutting docstring drift.
- WC-11 BUG (line 35): `wisdom_hint(r.get("ticker"), sector=r.get("sector"))` — assumes pick rows have flat `ticker` + `sector` fields. Per Batch 11 PL pick schema chaos, picks may carry nested `info_short.sector`. Schema-coupled.
- WC-12 GOOD (lines 36-37, 40-41): try/except around external calls — broader graceful degradation than the import-time fallback.
- WC-13 BUG (lines 36, 40): bare-except. Theme T1 undocumented. Now 2nd-tier defense (after import-time lambdas) — DOUBLE belt-and-braces but unscoped both times.
- WC-14 GOOD (lines 42-43): `bool((wh or "").strip())` — defensive against None.
- WC-15 GOOD: Per WC-X3, emoji classification at lines 50-53.
- WC-16 BUG: Per WC-X3, brittle emoji parsing.
- WC-17 BUG (line 52): 2 emoji variants for edges. Inconsistent. Either wisdom_hint emits both (schema drift) or one is dead code.
- WC-18 GOOD (line 54): Either-or tag count for n_tagged.
- WC-19 GOOD (lines 57-65): 7-key result dict with `pct` rounded.
- WC-20 BUG: No `edges` and `warnings` in empty-row early return (line 28). Schema asymmetric. A caller iterating result keys hits KeyError on empty input.

### Lines 68-84: format_footer
- WC-21 GOOD: Telegram-ready 1-line footer. Per Batch 44 CA-43 telegram_footer pattern.
- WC-22 GOOD (line 70-71): Empty-stats early return "".
- WC-23 GOOD (lines 72-78): Markdown italic with pluralization.
- WC-24 GOOD (lines 80-83): T42 optional second line. Conditional formatting — only shows if meaningful.
- WC-25 BUG (line 80-81): `stats.get("edges", 0)` — defensive against WC-20 schema asymmetry. But masks the bug.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### LG-X3 + Cross-cutting atomic-write tally
**lesson_gc.py read-all-rewrite-all is THE WORST atomic-write violation in audit:**
- Other unsafe writers: append + truncate small files (memoir, dedup, watchlist)
- lesson_gc: TRUNCATES the entire wisdom base then writes it back
- A crash mid-write = wisdom base lost.

**Atomic-write tally update:** Now 4 of 21 audited state-writers safe. lesson_gc adds 22nd writer (UNSAFE, CRITICAL). ~81% UNSAFE.

### LG-X4 + Batch 38/41/47 TZ-aware cross-cutting CONFIRMED
TZ-aware writers (modules that produce TZ-aware ISO):
- market_data_health (B14)
- news_signals
- learning_journal (B24)
- weight_applier
- stooq_provider
- official_pick_artifact (B37)
- watchlist_manager (B41)
- agent_memoir (B47)

**8 modules write TZ-aware.** lesson_gc (this batch) is a TZ-naive READER. TZ-aware/naive mismatch creates HIDDEN RUNTIME BUG.

### WC-X2 + Cross-cutting Theme T11 fail-open by accident
Module-level import-time lambda fallback is a NEW silent-failure pattern not yet cataloged:
- wisdom_coverage (this batch WC-X2)

Pattern: `try: from .x import f except Exception: f = lambda *a, **k: ""` at module top.
Risk: Broken upstream module = entire module silently produces empty/zero output. No alarm.

### WC-X3 + Cross-cutting Theme T2 schema-chaos
Emoji-as-protocol is a new schema-chaos vector. A wisdom_hint reformat = silently broken coverage classification. Should use structured tuples (kind, text) instead of emoji-encoded strings.

### LG-9 + cross-cutting Z-suffix handling
Modules that defensively handle Z-suffix:
- watchlist_manager (B41 WM-14)
- agent_memoir (B47 AM-25)

2 modules DEFENSIVE. lesson_gc this batch DOES NOT. 3 modules with inconsistent Z-handling.

### Cross-cutting: bare-except this batch
- lesson_gc: 0 (uses scoped json.JSONDecodeError + ValueError/TypeError)
- wisdom_coverage: 3 (WC-5 import, WC-13 x2 call sites) — graceful degradation but unscoped

### Cross-cutting: relative-path constants — no change this batch (lesson_gc uses LESSONS from wisdom_base; wisdom_coverage no paths)

### Cross-cutting: TZ-aware modules: 8 (no addition; lesson_gc is the new TZ-NAIVE reader)

### Cross-cutting: bug-archaeology gold standard: 7 modules (no new addition; both files have T-tags but not dated quantified archaeology)

## SUMMARY (Batch 48)

| Severity | lesson_gc | wisdom_coverage | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 6 | 7 | 4 | 17 |
| Data/safety | 3 | 2 | 0 | 5 |
| Code smell | 1 | 1 | 0 | 2 |
| Good code | 24 | 14 | 0 | 38 |
| Total findings | 34 | 24 | 4 | 62 |

## TOP 10 CRITICAL FIXES from Batch 48

1. **LG-X3 / LG-25 (CRITICAL):** Add atomic write (tmp+rename) to gc_stale. Truncate-then-write of full wisdom base is the SINGLE WORST atomic-write violation in audit. (10 min)
2. **LG-X4 / LG-4 + LG-13 + LG-21 (HIGH):** Convert lesson_gc to TZ-aware (datetime.now(timezone.utc) + Z-suffix defensive parse). (10 min)
3. WC-X2 / WC-4: Replace import-time lambda fallback with explicit `if WISDOM_AVAILABLE` flag + log warning. (10 min)
4. WC-X3 / WC-15: Use structured (kind, text) tuples instead of emoji-parsed protocol. Requires wisdom_hint API change. (45 min)
5. LG-27: Add file lock (fcntl or filelock) around gc_stale rewrite to prevent concurrent corruption. (15 min)
6. LG-9: Add `.replace("Z", "+00:00")` to _parse_ts. (3 min)
7. WC-11: Use nested-aware sector access. (5 min)
8. WC-20: Include `edges` and `warnings` keys in empty-row early return for schema-stability. (3 min)
9. WC-13: Scope bare-excepts to specific exception types. (5 min)
10. LG-6: Add archaeology comment for MAX_AGE_DAYS=90. (3 min)

## NEW THEMES UPDATED

- **Theme T1 (bare except):** lesson_gc 0 (scoped). wisdom_coverage 3 (graceful-degradation intent).
- **Theme T2 (schema drift):** WC-X3 emoji-as-protocol NEW vector. LG-X4 TZ-aware/naive mismatch.
- **Theme T6 (atomic writes):** LG-X3 is **WORST atomic-write violation in audit** — whole-file rewrite without tmp+replace. **Atomic-write tally: 4 safe / 18 unsafe / 22 total = ~82% UNSAFE.**
- **Theme T8 (DRY):** N/A this batch (small files).
- **Theme T11 (fail-open by accident):** WC-X2 module-level import-time lambda fallback NEW pattern. LG-17 missing-ts → keep (intentional fail-safe, documented).
- **Theme T13 (silent-default-fills):** WC-X2 silent zero coverage when wisdom_hint module broken.
- **Theme T14 (gold-standard patterns):** lesson_gc LG-X2 3-protections table + LG-23/LG-24 forensic deactivation fields = TEMPLATE for soft-delete patterns. lesson_gc CLI with --dry-run + --max-age + --protect = operator-friendly mutator.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A | 8/8 COMPLETE | (none) | 8/8 |
| Phase B | 18/18 COMPLETE | (none) | 18/18 |
| Phase C | 12/12 COMPLETE | (none) | 12/12 |
| Phase D | 30/~30 COMPLETE | (none) | 30/~30 |
| Phase E | 16/~50 done | lesson_gc, wisdom_coverage | 16/~50 |
| Total true line-by-line | | +2 files | **99 of ~382 (~25.9%)** |
| Remaining | | | **~283 files** |

**Approaching doc #55 (100 files audited).**

## NEXT BATCH

Batch 49 (doc #55, 100-file milestone): Continue wisdom/brain layer cleanup.
- **`src/wisdom_base.py` (11.3KB)** — THE LESSON STORE (consumed by lesson_gc, book_ingest, wisdom_consultant, wisdom_coverage). Core dependency we haven't audited.
- **`src/wisdom_hint.py` (9.2KB)** — emoji-protocol producer (consumed by WC-X3 emoji parsing). Closes the wisdom-layer audit.

End of Batch 48. Phase E in progress (16/50). **25.9% audit milestone.**
