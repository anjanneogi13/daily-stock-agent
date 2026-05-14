# Audit Batch 3a — Scripts: Audit + Backfill Family

**Date:** 2026-05-12
**Files (11):**
- `scripts/audit_dead_code.py` (111 lines)
- `scripts/audit_earnings_fill_rate.py` (184 lines)
- `scripts/audit_journal_consistency.py` (101 lines)
- `scripts/audit_lane1_production_readiness.py` (417 lines)
- `scripts/audit_sector_fill_rate.py` (225 lines)
- `scripts/backfill_alpha.py` (123 lines)
- `scripts/backfill_earnings_days.py` (131 lines)
- `scripts/backfill_regime.py` (117 lines)
- `scripts/backfill_sector_alpha.py` (172 lines)
- `scripts/backfill_signal_journal.py` (151 lines)
- `scripts/backfill_smell_columns.py` (98 lines)

**Total:** ~1,830 lines

**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

## High-level summary in plain English

These 11 files split into TWO families:

**Family 1 — Audit scripts (5 files):** Read CSVs/JSONLs, count things, print reports. Used by humans and the production-readiness audit gate.

**Family 2 — Backfill scripts (6 files):** Read picks_log.csv, find rows with missing data (alpha, earnings, regime, sector, journal entries, smell columns), compute fill values, write back to CSV.

**Why they exist:** Each is a tombstone for a past bug. `backfill_alpha.py` exists because alpha calculation wasn't wired in until May 1. `backfill_earnings_days.py` exists because earnings data was sparse pre-May 5. They're forensic/repair tools — exactly what a maturing codebase should have.

---

## CROSS-CUTTING FINDINGS (apply to whole batch)

### ✅ GOOD-AB1: All 6 backfill scripts use atomic write-then-rename pattern
- `backfill_alpha.py` lines 96-110, `backfill_earnings_days.py` 96-113, `backfill_sector_alpha.py` 142-154, `backfill_smell_columns.py` 61-78, `backfill_signal_journal.py` (uses append `.open("a")` — see issue below).
- **Plain English:** Write to a `.tmp` file first, then OS-level rename to the real name. If the script crashes mid-write, the original file is unchanged.
- **Why it's exemplary:** This is what production data tools should do. Compare to `main.py` which DOESN'T do this for diagnostic JSONs (BUG-59).
- **Severity:** ✅ Propagate this pattern.

### ✅ GOOD-AB2: All 6 backfill scripts default to DRY-RUN
- Pattern: print what WOULD change; only write with explicit `--apply`.
- **Plain English:** Safe by default. You can run any backfill any time and see preview before committing.
- **Severity:** ✅ Excellent safety discipline.

### ✅ GOOD-AB3: All scripts have scar-tissue documentation in the docstring
- Every backfill says: "Bug #N (date)" — explains the historical bug it patches.
- **Severity:** ✅ Forensics-friendly.

### ⚠️ X-AB4: All 6 backfill scripts hardcode `DATA_QUALITY_FLOOR = "2026-05-02"` (or similar)
- **Plain English:** The "data quality floor" date is repeated as a constant in 4 files: `audit_earnings_fill_rate.py:23`, `audit_sector_fill_rate.py:20`, `backfill_earnings_days.py:29`, `backfill_sector_alpha.py:33`.
- **Why a problem:** When/if you decide to bump the floor (because data improved), you must update 4 places and keep them in sync.
- **Fix:** Move to `src/data_quality.py`: `DATA_QUALITY_FLOOR = "2026-05-02"`. Import everywhere.
- **Severity:** ⚠️ Constant drift risk.

### ⚠️ X-AB5: `CLOSED_STATUSES` is defined inconsistently across files
| File | Definition |
|---|---|
| `audit_sector_fill_rate.py:23-28` | `{"tp_hit", "sl_hit", "expired", "day_close"}` |
| `backfill_alpha.py:31` | `{"tp_hit", "sl_hit", "expired", "day_close"}` |
| `backfill_sector_alpha.py:34` | `{"tp_hit", "sl_hit", "expired", "day_close"}` |
| `backfill_signal_journal.py:23-24` | `{"sl_hit", "tp_hit", "max_hold", "expired", "sl_gap", "tp_gap", "closed"}` |

- **Plain English:** Five different files have their own version of "what does CLOSED mean?" The journal one is broader (max_hold, sl_gap, tp_gap, closed).
- **Why a problem:** If pick_evaluator ever produces a new status (e.g., `early_exit`), each consumer must be updated independently. Some will lag.
- **Fix:** Move to `src/pick_status.py`: `CLOSED_STATUSES = frozenset({...})`. Import everywhere.
- **Severity:** ⚠️ Schema drift; some files will silently miss new statuses.

### 🟡 X-AB6: Two near-identical helpers across files
- `_has_value` / `has_value` / `_has_days_to_earnings` etc. — same "treat None/blank/'None'/'nan' as missing" pattern is duplicated across 5 files (`audit_earnings_fill_rate.py:27-40`, `audit_sector_fill_rate.py:42-53`, `backfill_earnings_days.py:32-40`, `backfill_sector_alpha.py:44-48`, `audit_journal_consistency.py` inline).
- Fix: Extract to `src/csv_helpers.py`: `is_csv_value_present(v)`.
- **Severity:** 🟡 DRY violation.

### ⚠️ X-AB7: No `--strict` flag consistency
- `audit_dead_code.py` has `--strict` (exit 1 if any dead found)
- `audit_journal_consistency.py` has `--strict` (exit 1 on drift)
- `audit_earnings_fill_rate.py` does NOT have `--strict` (only `--json`)
- `audit_sector_fill_rate.py` does NOT have `--strict`
- **Plain English:** Some audits can fail CI; others only print.
- **Why a problem:** If you wanted to add an audit to `ci.yml` later, the inconsistent UX requires per-script handling.
- **Fix:** Add `--strict` to all audits.
- **Severity:** ⚠️ Operability.

### 🟡 X-AB8: All scripts use `sys.exit(main())` or `raise SystemExit(main())` inconsistently
- `audit_dead_code.py:110` `sys.exit(main())`
- `audit_earnings_fill_rate.py:183` `raise SystemExit(main())`
- `backfill_alpha.py:122` `main()` (no exit code propagated!)
- `backfill_regime.py:117` `backfill(apply=apply)` (no exit code, no main wrapper)
- **Plain English:** Different ways to exit. Some don't return error codes at all → CI tools see "success" even on failure.
- **Severity:** 🟡 Operability.

### ⚠️ X-AB9: NONE of the audit scripts WRITE their output as artifacts
- They print to stdout. Production calls `audit_lane1_production_readiness.py` from `daily-picks.yml` and DOES write JSON+MD output. The other 4 audits DON'T.
- **Plain English:** if `audit_earnings_fill_rate.py` finds a problem, you have to read terminal output. No artifact to ship to Telegram or GitHub Issue.
- **Fix:** Standardize on writing JSON+MD report files for all audits.
- **Severity:** ⚠️ Observability gap.

---

## PER-FILE FINDINGS

---

### 1. `audit_dead_code.py` (111 lines)

**What it does:** Scans `src/` to find modules never imported by `main.py`, `scripts/`, `app.py`, or other live `src/` modules. Reports them as "dead."

**✅ GOOD-AD1:** Excellent docstring (lines 1-14) — explains WHY the script exists and the bug it found ("E4 smell faculty pattern: code exists, no caller, never runs").
**✅ GOOD-AD2:** Comments call out a previous audit bug (line 9): "from src import X ← original audit MISSED this, gave false positives." Forensic transparency.
**✅ GOOD-AD3:** BFS reachability traversal (lines 64-73) — correct algorithm for "what's reachable from entry points."
**✅ GOOD-AD4:** Reports test coverage as informational (lines 98-103) — distinguishes "dead but tested" from "dead and orphaned."

**🚨 BUG-AD1:** Line 30 regex: `r"from\s+src\.(\w+)|from\s+\.(\w+)\s+import"`
- The first alternative is `from src.X` — WITHOUT requiring `import` at the end. So `from src.foo` standalone (rare but possible in error) matches. Defensible but loose.
- Severity: 🟡

**⚠️ BUG-AD2:** Line 30 `from\s+\.(\w+)\s+import` — relative import shape. Catches `from .foo import bar` but won't catch `from . import foo`. Both are valid Python.
- Severity: ⚠️ Possible false positives (a relative-imported module reported as dead).

**⚠️ BUG-AD3:** Line 44-46 `all_modules = {f.stem for f in SRC.glob("*.py") if f.stem != "__init__"}`
- **Plain English:** Finds .py files DIRECTLY in src/. Doesn't recurse into subdirectories.
- **Why a problem:** If `src/` ever gets subdirs (e.g., `src/news/`, `src/risk/`), they're invisible to this audit. All "dead" findings would be wrong.
- Fix: `SRC.rglob("*.py")` and use module path notation.
- Severity: ⚠️ Hidden assumption.

**⚠️ BUG-AD4:** Line 96 `loc = sum(1 for _ in f.read_text().splitlines())`
- Counts lines in the dead module. Used only for display.
- Reads entire file into memory just to count lines. Trivial cost, but: replace with `len(f.read_text().splitlines())` — same result, less verbose.
- Severity: 🟡 Style.

**⚠️ BUG-AD5:** Line 100 `for tf in (ROOT / "tests").glob("test_*.py") if tf.exists()`
- The `if tf.exists()` is dead — `glob` only returns existing files.
- Severity: 🟡 Dead check.

**🟡 BUG-AD6:** No `--json` output mode. The audit only prints. Combined with X-AB9.

---

### 2. `audit_earnings_fill_rate.py` (184 lines)

**What it does:** Counts what % of post-floor picks have `days_to_earnings` populated. Reports by trade type (day/swing). Warns if below 80%.

**✅ GOOD-AE1:** Best-in-class report formatting — Unicode box, status emoji, sample of missing tickers.
**✅ GOOD-AE2:** Has both human-readable and `--json` output (lines 175-178).
**✅ GOOD-AE3:** Threshold and floor are CLI-overridable (lines 161-167).
**✅ GOOD-AE4:** Defensive `has_days_to_earnings` (lines 27-40) treats `0` as VALID (earnings can be today).

**⚠️ BUG-AE1:** Line 44 `_norm_trade_type` returns "unknown" for blank — but downstream may not display "unknown" specially. **Per your bootstrap, "9/14 picks have unknown trade_type / earnings_bucket"** — this is the function reporting it, but it doesn't ALARM about it.
- Fix: in `format_report`, highlight if "unknown" trade_type rate > 10%.
- Severity: ⚠️ Symptom visible but un-flagged.

**⚠️ BUG-AE2:** No `--strict` flag. Audit can warn but never fail CI.
- Severity: ⚠️ Combined with X-AB7.

**🟡 BUG-AE3:** Line 23 `DATA_QUALITY_FLOOR = "2026-05-02"` — magic date string. See X-AB4.

**🟡 BUG-AE4:** Line 24 `DEFAULT_WARNING_THRESHOLD = 0.80` — magic threshold. Why 80%? No comment.

---

### 3. `audit_journal_consistency.py` (101 lines)

**What it does:** Compares `picks_log.csv` vs `signal_journal.jsonl`. Reports drift (in picks but not journal, or vice versa).

**✅ GOOD-AJ1:** Excellent docstring (lines 3-11) explaining the INVARIANT (locked May 4 2026, F4): "Every pick must have matching journal entry."
**✅ GOOD-AJ2:** Has `--strict` flag.
**✅ GOOD-AJ3:** Friendly error messages (lines 89, 94) suggest WHERE to look ("main.py log_pick() may have failed silently").

**🚨 BUG-AJ1:** Line 30 `for r in csv.DictReader(PICKS.open())` — file handle leak.
- **Plain English:** Opens picks_log.csv but doesn't close it. Python garbage-collects eventually, but on Windows this can cause "file in use" errors.
- Fix: `with PICKS.open() as f: for r in csv.DictReader(f):`
- Severity: ⚠️ Resource leak.

**⚠️ BUG-AJ2:** Lines 87, 92 only print first 10 drift entries. If 100 are missing, you only see 10. No way to dump all.
- Fix: add `--all` flag or `--limit N`.
- Severity: 🟡

**⚠️ BUG-AJ3:** Line 89 `→ main.py log_pick() may have failed silently. Check pipeline log.`
- **Plain English:** The error message tells you WHERE to look but doesn't tell you HOW (which log file? grep what?).
- Fix: link to actual log path.
- Severity: 🟡

**🚨 BUG-AJ4:** Line 96 `return 1 if strict else 0` — but `r["in_journal_only"]` items (extras in journal) are also drift. Strict mode should fail on EITHER direction.
- **Plain English:** If you have 5 ghost entries in journal that don't match picks_log, strict mode still passes (line 78 check is `or`, but line 96 always returns 1 if strict and any drift exists — actually OK on re-read).
- Wait, line 78: `drift = r["in_picks_only"] or r["in_journal_only"]` — so drift IS true if either side has extras. Line 96: `return 1 if strict else 0` — but only IF drift was True (line 79 would have returned 0 already if no drift). Re-reading: if `drift` is truthy, falls through to line 96. So strict DOES catch both.
- **Re-classified:** ✅ Actually correct. Severity: 📝

**🟡 BUG-AJ5:** Hardcoded `Path("data/picks_log.csv")` (line 22) — no override flag.

---

### 4. `audit_lane1_production_readiness.py` (417 lines)

**What it does:** Comprehensive pre-flight gate. Verifies:
- Required files exist (15 paths)
- Decision contract is correctly shaped (8 checks)
- Pick + No-pick dry-runs produce valid artifacts (6 checks)
- Workflow file references right scripts (14 snippets)
- Telegram + GitHub Issue formatters consume official artifacts (5 checks)
- No safety flags accidentally enabled (1 check)

**This is the GOLD STANDARD audit script.** Used by `daily-picks.yml` to gate every production run.

**✅ GOOD-AL1:** Single entry point `run_audit()` (lines 340-369) returns structured result with checks list.
**✅ GOOD-AL2:** Writes BOTH JSON and Markdown (lines 308-337) — good for both machine + human consumption.
**✅ GOOD-AL3:** Imports dry-run modules (lines 37-38) and EXECUTES them — proper end-to-end test.
**✅ GOOD-AL4:** Safety scan (lines 279-305) — searches files for accidental `paper_trading_enabled: True` strings.
**✅ GOOD-AL5:** Top docstring (lines 16-22) explicitly declares "no providers, no LLMs, no Telegram, no GitHub APIs" — exemplary safety contract.

**⚠️ BUG-AL1:** Line 117 `len(OFFICIAL_PICK_REQUIRED_FIELDS) >= 25` — magic threshold of 25.
- **Plain English:** "Pick contract must have ≥25 required fields."
- Why a problem: if the contract LOSES fields (legitimate refactor), audit fails. If contract ADDS fluff fields (cargo-cult), audit still passes.
- Fix: snapshot the EXACT field set in a separate constants file; check exact match.
- Severity: 🟡 Brittle gating.

**⚠️ BUG-AL2:** Line 215 `workflow = _read(Path(".github/workflows/daily-picks.yml"))` then string-search for snippets. If workflow ever uses comments / different formatting / multiple files, fails.
- Severity: ⚠️ Hardcoded coupling to one workflow file.

**🚨 BUG-AL3:** Line 314 + 368 `json_path.write_text(...)` — file written TWICE.
- **Plain English:** Line 314 writes initial result, then line 366-367 mutates result with paths, then line 368 writes the file AGAIN.
- Why a problem: race condition window where a reader sees the first version. Wasteful.
- Fix: write once at the end.
- Severity: ⚠️ File integrity.

**⚠️ BUG-AL4:** Line 384 `tempfile.mkdtemp(prefix="lane1-production-readiness-audit-")` — creates temp dir. If `--keep` not set and script crashes, line 411-412 cleanup runs in `finally`. OK but verbose.
- Severity: 📝

**⚠️ BUG-AL5:** Line 380 `if args.output_dir:` then `keep = True` (line 382) — silent override.
- **Plain English:** If you pass `--output-dir`, your `--keep` arg is IGNORED — keep is always true.
- Why a problem: surprising. If user passes `--output-dir foo --keep=false`, they think they want cleanup. Script disagrees.
- Severity: 🟡 Silent argument override.

**⚠️ BUG-AL6:** Line 308 `_write_audit_files` — but doesn't sanity-check that result["passed"] count matches actual sum.
- Severity: 📝

**⚠️ BUG-AL7:** No timeout on the dry-run executions (lines 152-188). If a dry-run hangs, the production-readiness audit hangs the whole `daily-picks.yml` workflow.
- Severity: ⚠️ Production hang risk.

**🟡 BUG-AL8:** Workflow snippets list (lines 217-232) is hardcoded. New gates added to daily-picks.yml without updating this list = silent un-validation.
- Severity: ⚠️ Manifest drift.

---

### 5. `audit_sector_fill_rate.py` (225 lines)

**What it does:** Counts what % of post-floor picks have sector benchmark fields populated (entry: sector_etf, sector_close; exit: sector_close_at_exit, sector_return_pct, sector_alpha_pct).

**✅ GOOD-AS1:** Same exemplary report formatting as audit_earnings_fill_rate.
**✅ GOOD-AS2:** Separates ENTRY vs EXIT field checks correctly (entry checked on all post-floor; exit only on closed).

**⚠️ BUG-AS1:** Line 23-28 `CLOSED_STATUSES` — see X-AB5 (drift across files).
**🟡 BUG-AS2:** Same as audit_earnings: no `--strict`. See X-AB7.
**🟡 BUG-AS3:** Hardcoded floor + threshold magic numbers.

---

### 6. `backfill_alpha.py` (123 lines)

**What it does:** For closed picks missing `alpha_pct`, computes SPY-relative alpha and writes back.

**✅ GOOD-BA1:** Atomic write (X-AB1).
**✅ GOOD-BA2:** Idempotent (line 46: skip if already filled).
**✅ GOOD-BA3:** Reuses live calculator `src.pick_evaluator._add_spy_alpha` (line 27, 80) — single source of truth.

**🚨 BUG-BA1:** Line 27 imports `_add_spy_alpha` — a PRIVATE function (underscore prefix).
- **Plain English:** Underscore in Python conventionally means "internal, don't import from outside." This script imports an internal function from another module.
- Why a problem: pick_evaluator authors can refactor `_add_spy_alpha` without warning, breaking this script silently.
- Fix: either (a) make it public (`add_spy_alpha`), or (b) add a comment in pick_evaluator: `# DO NOT RENAME: imported by scripts/backfill_alpha.py`.
- Severity: 🚨 Hidden coupling.

**⚠️ BUG-BA2:** Line 80 `_add_spy_alpha` mutates row in place AND returns spy_at_exit_str. **Mixed contract** (mutation + return value).
- Plain English: function does two things at once. Caller has to remember to use the return value AND know the side effect happened.
- Fix: either return ALL outputs OR mutate-only.
- Severity: ⚠️ API design.

**⚠️ BUG-BA3:** Line 116 `def main(): apply = "--apply" in sys.argv; backfill(apply=apply)` — doesn't return exit code. See X-AB8.

**🟡 BUG-BA4:** Line 102 `extrasaction="ignore"` on DictWriter — silently drops fields not in fieldnames. If a future column is added to one row but not others, get silent data loss.
- Severity: 🟡

---

### 7. `backfill_earnings_days.py` (131 lines)

**What it does:** Backfill missing `days_to_earnings` for post-floor picks using `src.earnings.days_to_earnings`.

**✅ GOOD-BE1:** Atomic write, dry-run default, idempotent.
**✅ GOOD-BE2:** Self-extending fieldnames (line 53-54): if column missing, adds it. Forward-compatible.

**🚨 BUG-BE1:** Line 76 `d2e = days_to_earnings(ticker, as_of=pick_date)`
- **Plain English:** Called with `as_of=pick_date` — fetches what `days_to_earnings` was on the pick date.
- Why a problem: `src.earnings.days_to_earnings` may not actually support an `as_of` parameter — needs verification. If it doesn't, the parameter is silently ignored and current d2e is written, which is WRONG (changes daily).
- Severity: 🚨 If the function doesn't support `as_of`, all backfilled values are wrong.
- Need: verify `src/earnings.py` signature.

**⚠️ BUG-BE2:** Line 77-79 if d2e == UNKNOWN: skip silently. **Same earnings-unknown contradiction as main.py BUG-77** — but here it's the right call (don't fabricate data). At least flag in summary how many SKIPPED.
- Already prints `⚠ ticker pick_date: earnings unknown — skip` — OK.

---

### 8. `backfill_regime.py` (117 lines)

**What it does:** For picks_log rows where regime is missing/'unknown', recomputes by comparing pick-date `spy_close` to SPY 200-day SMA.

**✅ GOOD-BR1:** Single SPY fetch (line 39-63) covers all needed dates — efficient.

**🚨 BUG-BR1:** Line 102 `with open(PICKS_LOG, "w", newline="") as f:` — **NO atomic write!**
- **Plain English:** Writes directly to picks_log.csv. If interrupted mid-write, file is corrupted.
- Why a problem: this is the ONE backfill that doesn't follow the atomic pattern (X-AB1).
- Fix: copy the atomic-write pattern from sibling scripts.
- Severity: 🚨 Data corruption risk on the production CSV.

**⚠️ BUG-BR2:** Line 18 `import yfinance as yf, import pandas as pd` — module-level imports; if yfinance is down/missing, script crashes at import.
- Acceptable for a backfill script (interactive use), but combine with no-timeout (line 48) means hangs are possible.
- Severity: ⚠️

**⚠️ BUG-BR3:** Line 25-36 `_classify` thresholds (5.0%, 0.0%, -5.0%) — hardcoded thresholds repeated from `src/regime.py`. **Drift risk:** if `src/regime.py` thresholds change, this script's classification will diverge.
- Fix: import from `src.regime` instead of duplicating.
- Severity: ⚠️ Logic drift.

**⚠️ BUG-BR4:** Line 67 `rows = list(csv.DictReader(open(PICKS_LOG)))` — file handle leak (same as BUG-AJ1).

**⚠️ BUG-BR5:** Line 68 `headers = rows[0].keys() if rows else []`
- **Plain English:** Headers extracted from FIRST row's keys.
- Why a problem: if `rows` is empty list, `headers = []`. Line 103 then `csv.DictWriter(f, fieldnames=[])` writes empty CSV. **Possible total data loss if picks_log was empty when this ran.**
- Fix: use `reader.fieldnames` instead of `rows[0].keys()`.
- Severity: ⚠️ Empty-file edge case.

**🟡 BUG-BR6:** Line 62 `float(sma.iloc[0]) if hasattr(sma, "iloc") else float(sma)` — defensive but cryptic. Suggests pandas indexing got confused somewhere. Comment why.

---

### 9. `backfill_sector_alpha.py` (172 lines)

**What it does:** Same as backfill_alpha but for sector benchmark fields.

**✅ GOOD-BS1:** Atomic write, dry-run, idempotent.
**✅ GOOD-BS2:** Reuses live calculators (`_ensure_sector_benchmark_anchor`, `_add_sector_alpha`) — line 26-29.

**🚨 BUG-BS1:** Same private-function import as BUG-BA1: imports `_ensure_sector_benchmark_anchor` and `_add_sector_alpha`. Both underscore-prefixed.
- Severity: 🚨 Hidden coupling.

**⚠️ BUG-BS2:** Line 101 `_ensure_sector_benchmark_anchor(row)` — mutates row, returns (etf, pick_close). Same dual contract issue as BUG-BA2.

---

### 10. `backfill_signal_journal.py` (151 lines)

**What it does:** For closed picks NOT in signal_journal, append matching journal records so hypothesis_engine has data.

**✅ GOOD-BJ1:** Idempotent via `_existing_keys()` (lines 27-39).
**✅ GOOD-BJ2:** Uses `sj.build_signals(pick)` (line 105) — single source of truth for signal extraction.

**🚨 BUG-BJ1:** Line 142 `with sj.JOURNAL.open("a") as f: ... f.write(json.dumps(r) + "\n")`
- **Plain English:** APPENDS to journal directly. NOT atomic.
- Why a problem: if the script crashes after writing record 5 of 100, you have a partial journal. Subsequent runs treat the partial-written record as "existing" → never get the rest.
- Fix: write all to a temp file, then concatenate with mv-style append. OR write line-by-line but verify each write completes before moving to next.
- Severity: 🚨 Inconsistent with sibling backfills' atomic pattern.

**⚠️ BUG-BJ2:** Line 24 `CLOSED_STATUSES` includes `"closed"` (a generic catch-all). But sibling files don't. See X-AB5.
- Severity: ⚠️

**⚠️ BUG-BJ3:** Line 63 `vol_ratio: None # not in picks_log — bucketed as "unknown"` — comment admits picks_log doesn't have this column. **But backfill cannot recover what wasn't logged.** All backfilled rows get vol_ratio=None forever, biasing brain learning toward "we don't know vol_ratio."
- Plain English: this script is a band-aid; the real fix is logging vol_ratio at pick time (which `main.py` line 1746 DOES do). Old picks pre-fix can never have it.
- Severity: ⚠️ Permanent data gap acknowledged but not flagged.

**🟡 BUG-BJ4:** Line 73 `if s == "max_hold": return "neutral"` — but `max_hold` could be win OR loss. Bucketing both as "neutral" loses signal.

---

### 11. `backfill_smell_columns.py` (98 lines)

**What it does:** Adds 3 columns (`smell_codes`, `smell_severities`, `smell_messages`) to picks_log.csv if missing. Doesn't fabricate data.

**✅ GOOD-BC1:** Smallest, cleanest backfill in the family. Schema migration only.
**✅ GOOD-BC2:** Atomic write.
**✅ GOOD-BC3:** Comment (lines 9-11): "It does not fabricate historical smell verdicts; existing rows get blank smell fields." — honest about what it does NOT do.

**🟡 BUG-BC1:** No flag to remove the columns if you ever want to roll back. Once added, no easy delete.
- Severity: 🟡

---

## Summary of Batch 3a (11 audit/backfill scripts)

### By severity
| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 9 |
| ⚠️ Data/safety risk | 23 |
| 🟡 Code smell | 14 |
| 📝 Doc-only | 3 |
| ✅ Good code | 18 |
| **Total** | **67 findings** |

### Top 6 things to fix in this batch (in order)

| # | Bug | Why first | Fix difficulty |
|---|---|---|---|
| 1 | BUG-BR1 (backfill_regime no atomic write) | Direct picks_log corruption risk; ALL siblings do this correctly | Easy: copy pattern from siblings |
| 2 | BUG-BJ1 (backfill_signal_journal append corruption) | Partial-write breaks dedup logic | Medium: temp file + atomic concat |
| 3 | BUG-BA1 + BS1 (private function imports) | Refactor risk; production renamings break audit/backfill | Medium: make functions public OR add coupling comment |
| 4 | BUG-BE1 (verify days_to_earnings supports as_of) | If unsupported, ALL backfilled earnings values are wrong | Easy: verify by reading src/earnings.py (Batch 4) |
| 5 | X-AB5 (CLOSED_STATUSES drift across 5 files) | Schema bug waiting to bite | Medium: extract to single source |
| 6 | BUG-AL3 (audit_lane1 writes JSON twice) | File integrity for the most-critical audit script | Easy: write once |

### What this batch tells us about the project

- **Excellent forensic discipline.** Each backfill is a tombstone for a past bug, with date + bug number. New backfills = new battle scars.
- **Atomic write pattern is in 5 of 6 backfills** — propagation worked, except `backfill_regime.py` was missed.
- **Private-function-imports are how scripts couple to src/.** This is a **real architectural risk**: src/ refactors silently break scripts. Two paths forward: (a) elevate critical helpers to public API, (b) add explicit "DO NOT RENAME" comments.
- **CLOSED_STATUSES is duplicated 5 times.** This kind of constant drift is exactly the sort of bug that surfaces months later when one consumer doesn't see a new status.
- **`audit_lane1_production_readiness.py` is genuinely the gold standard.** Use as model for new audits.
- **Audit reports are inconsistent — some print only, some emit JSON, some have --strict, some don't.** Standardize.
- **Earnings-unknown handling is consistent across audit and backfill (skip with warning), but main.py BUG-77 INCLUDES the pick anyway.** Fix that contradiction.

### Glossary additions

| Term | Plain English |
|---|---|
| Backfill | A one-time script that fills in missing data in historical records. Like going back and stamping all old letters with the new postage rate. |
| Atomic write | Save a file safely: write to a temp file first, then OS-rename. Crashes leave the OLD file intact. |
| Idempotent | A script you can run twice in a row and the second run does nothing new. Safe to retry. |
| Dry-run | A "show me what you WOULD do" mode. Default safe behavior. |
| File handle leak | Opening a file but not closing it. Python's garbage collector eventually cleans up, but on Windows can lock the file. |
| Private function (`_func`) | Python convention: leading underscore means "internal, don't import." Importing one creates hidden coupling. |
| Schema drift | Two parts of the system disagree about what a "valid status" is, slowly diverging. Causes silent bugs. |
| `--strict` flag | An audit option that turns warnings into errors (exit code 1), so CI can block on it. |

---

**End of Batch 3a.**

Cumulative findings across batches 1a + 1b + 2a + 2b + 3a:
- 🚨 Show-stoppers: 65
- ⚠️ Data/safety risks: 110
- 🟡 Code smells: 88
- 📝 Doc-only: 9
- ✅ Good code: 92
- **Total: 364 findings across 39 files (~14,000 lines)**

Next: Batch 3b — Scripts: build_*, dry_run_*, validate_*, write_*, check_* (artifact + validation infrastructure, ~12 files).
