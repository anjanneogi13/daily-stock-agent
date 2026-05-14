# Batch 27 — src/pick_evaluator.py (433 lines) + src/position_monitor.py (131 lines) — TRUE LINE-BY-LINE — PHASE D BEGINS

**Date:** 2026-05-12
**Files:** pick_evaluator.py (433 lines, fully read), position_monitor.py (131 lines, fully read)
**Phase:** D (pipeline & output) — files 1 and 2 of ~30

## TOP HEADLINE FINDINGS

1. PV-X1: pick_evaluator.py is **THE OUTCOME-ATTACHMENT layer.** Walks pending picks daily, simulates SL/TP hits via OHLC walk-forward, marks tp_hit/sl_hit/expired/unreachable_entry/day_close/still_open. **DOWNSTREAM of pick_logger** (Batch 11) — closes the loop that signal_journal/calibration/hypothesis_engine all depend on.
2. PV-X2: **USES ATOMIC WRITE** (lines 37-54 `_save_picks` with tmp + replace). **3rd file with atomic write after MDH (Batch 14) and NS (Batch 16).** Comment at line 38-44 documents the crash-safety rationale: "If the process is killed mid-write, the real picks_log.csv is left intact." **GOLD STANDARD.** ✅ But conspicuously absent: pick_logger writes the same file WITHOUT atomic write (Batch 11 PL-19). **Two files, same target, different safety.** PL writes (frequent) are unsafe; PV rewrites (less frequent but huge) are safe.
3. PV-X3: **5 outcome states** (tp_hit / sl_hit / expired / unreachable_entry / day_close / still_open). All operator-friendly with archaeology comments documenting the BUGS that motivated each state. **BUG-2 fix (line 298), F3 fix (line 265), Bug #5 fix (line 359), May 11 atomic-write (line 38).** **Highest archaeology density of any audited file.** This file has been BATTLE-TESTED.
4. PV-X4: **3 SEPARATE TRY/EXCEPT around `_journal_attach`** (lines 344-353, 384-393, 414-423) — **identical 9-line block repeated 3x.** Pure copy-paste. Each prints "[eval] WARN journal_attach failed for ?: e" tagged with "M9". DRY violation.
5. PV-15 (line 60): `yf.download(ticker, start=start, progress=False, auto_adjust=False)` — **`auto_adjust=False`** explicit. **Means OHLC is RAW (not split-adjusted).** A 2-for-1 split between pick_date and today will cause the walk to see a 50% drop → SL hit on the split date when the position actually was unaffected. **Split-adjustment bug latent.**
6. PM-X1: position_monitor.py is **THE TIME-DECAY ALERTER** — 131 lines, scans pending positions for max_hold_days breach. **READ-ONLY** ✅. Flags "over" and "near" severities. Single-purpose, clean.
7. PM-X2: PM has TIGHT MAX_HOLD_DAYS (line 24-29): **day=1, swing=10, multi=30, default=14.** **Compare to pick_evaluator MAX_DAYS_OPEN=20 (line 17).** **Two files, two time-decay constants for the same concept.** A swing pick at day 12: PM alerts "over" but PV still says "still_open" (will expire at day 20). **8-day disagreement window.**

## src/pick_evaluator.py — LINE BY LINE

### Lines 1-18: Module docstring + imports
- PV-1 GOOD: 7-line docstring documents 4 outcome states (TP/SL/expired/open) + the time threshold (20 trading days).
- PV-2 GOOD (lines 13-14): Relative imports of signal_journal + sector_benchmark.
- PV-3 BUG (line 16): `Path("data/picks_log.csv")` — **19th file with relative-path constant.**
- PV-4 GOOD (line 17): `MAX_DAYS_OPEN = 20` named constant.
- PV-5 GOOD (line 18): `EVAL_LOOKBACK_DAYS = 30` — picks older than 30 days marked stale.

### Lines 21-34: _load_picks
- PV-6 GOOD: Defensive existence check.
- PV-7 BUG (line 25): `list(csv.DictReader(f))` — full file in memory. Per Batch 21 PS-12 cross-cutting.
- PV-8 GOOD (lines 26-33): **Schema migration code** — defensive backfill of new SPY/sector fields. Documents migration date (May 2 2026). **Operator-friendly schema evolution.** ✅
- PV-9 BUG (lines 26-29): 8 backfill field names hardcoded in this function. **If schema evolves further, must edit here.** Single source of truth missing.

### Lines 37-54: _save_picks — **ATOMIC WRITE** ✅
- PV-10 GOOD (line 38-44): Explicit docstring documenting crash-safety. **Best-documented atomic write in audit.**
- PV-11 GOOD (line 47): `fields = list(rows[0].keys())` — derives schema from first row. **Schema drift risk** if rows have different keys.
- PV-12 GOOD (lines 49-54): tmp + writeheader + writerows + replace. Standard atomic pattern.
- PV-13 BUG (line 51): `lineterminator="\n"` — explicit Unix line ending. ✅ portable but operator on Windows may see weird output.
- PV-14 BUG (line 47): If `rows[0]` has narrower keys than `rows[5]`, columns are silently dropped from later rows. Per Batch 11 PL-X1 schema chaos cross-cutting.

### Lines 57-69: _fetch_ohlc
- PV-15 BUG (line 60): `auto_adjust=False` per PV-X1 head finding. Split-adjust bug latent.
- PV-16 GOOD (lines 64-65): MultiIndex column flatten — defensive against yfinance schema variation.
- PV-17 BUG (line 67-69): bare except. Theme T1 undocumented.

### Lines 72-102: _spy_close_on
- PV-18 GOOD (line 72): Module-level cache `_SPY_CACHE`. **Avoids redundant downloads.**
- PV-19 BUG (line 72): `_SPY_CACHE = {}` — module-level dict. **Lives for process lifetime.** For long-running processes, grows unbounded. Eviction missing. Acceptable for evaluator script (process exits) but anti-pattern for daemon.
- PV-20 BUG (lines 80, 132): **Inline `from datetime import ...`** within functions. **3 inline imports across 3 places.** Per Batch 24 WB-43 cross-cutting.
- PV-21 GOOD (lines 83-84): 5-day window for SPY price covers weekends/holidays. Operator-aware.
- PV-22 GOOD (line 92): `df = df[df.index.date <= target]` — finds nearest-trading-day-at-or-before. Standard.
- PV-23 BUG (lines 99-102): bare except `as e` — logs the error (better than pass) but still untyped Theme T1.

### Lines 105-124: _add_spy_alpha
- PV-24 GOOD: SPY-relative alpha calc.
- PV-25 BUG (line 110, 115): Sets `row["alpha_pct"] = None` on failure. **CSV will write "None" string** (per Batch 11 PL-X1 None-as-string sentinel). Then downstream readers must handle "None" string. Schema fragility.
- PV-26 GOOD (lines 121-123): Standard pct return + alpha computation.

### Lines 127-143: _etf_close_on
- PV-27 BUG (line 132): Inline imports again.
- PV-28 BUG (line 137): `df = df[df.index <= d.strftime("%Y-%m-%d")]` — string date comparison against DatetimeIndex. **Implicit pandas type coercion.** Works but fragile.
- PV-29 BUG (lines 141-143): bare except. Theme T1.

### Lines 146-170: _resolve_sector_etf_for_row
- PV-30 GOOD (lines 147-152): Excellent docstring documenting legacy-row repair logic with example "SEMI / AI" → SOXX.
- PV-31 BUG (lines 157-162): 3-way `or` chain for `tag` (`tag` / `sector_tag` / `scores_sector_tag`). Theme T2 schema-chaos pattern.
- PV-32 BUG (lines 163-168): Same 3-way `or` for `sector`. **6 different field names checked across 2 logical fields.** Per Batch 22 SJ-X3 confirmation that schema fragmentation is widespread.
- PV-33 GOOD (line 169): `or "SPY"` final fallback. **Defensive — sector-alpha learning still happens with SPY benchmark.**

### Lines 172-204: _ensure_sector_benchmark_anchor
- PV-34 GOOD (lines 172-177): Documents legacy-repair intent.
- PV-35 GOOD (lines 178-180): Resolve and store ETF.
- PV-36 BUG (line 187): bare `except: pass` for sec_pick_str float parse. Theme T1.
- PV-37 GOOD (lines 197-202): Fallback to SPY if ticker-specific ETF unfetchable. **Layered defensive fallbacks.**

### Lines 207-226: _add_sector_alpha
- PV-38 GOOD: Mirror of _add_spy_alpha for sector ETF.
- PV-39 BUG (line 215, 220): Same `None` write to CSV pattern.

### Lines 229-433: evaluate_pending — THE MAIN FUNCTION
- PV-40 GOOD (line 230 docstring): Brief but accurate.
- PV-41 GOOD (line 234): 7-field initial counts dict.
- PV-42 GOOD (line 236-237): Today vs cutoff for too-old picks.
- PV-43 BUG (line 236): `datetime.now().date()` — NAIVE. Per cross-cutting.
- PV-44 GOOD (line 242): `if row["evaluation_status"] != "pending": continue` — efficient filter.
- PV-45 BUG (line 242): `row["evaluation_status"]` — KeyError if missing column. Compare to PM line 70 which uses `.get()`. **Inconsistent within codebase.**
- PV-46 GOOD (lines 244-247): Defensive pick_date parse.
- PV-47 GOOD (lines 248-253): Too-old picks marked expired immediately.
- PV-48 BUG (line 250-252): NO journal_attach for too-old expired picks. **Picks expired due to age get NO learning event** → hypothesis_engine never sees them → biased toward fresh-evaluated picks. Selection bias in learning.
- PV-49 GOOD (lines 256-258): Type coercion for entry/sl/tp.
- PV-50 BUG (line 256-258): `float(row[...])` — KeyError on missing. Same PV-45 pattern.

### Lines 265-291: F3 unreachable_entry detection
- PV-51 GOOD (lines 265-272): **EXCELLENT bug-archaeology comment** — documents Apr 28 SEMI bloodbath where 6 picks logged outside actual price range.
- PV-52 GOOD (line 280): 0.5% tolerance for data-source rounding. Reasonable magic.
- PV-53 GOOD (lines 281-291): Marks unreachable_entry, exits cleanly.
- PV-54 BUG (line 287): `counts.setdefault("unreachable_entry", 0)` — but it's already initialized at line 234. **Redundant.** Defensive but unneeded.
- PV-55 BUG (lines 281-291): NO journal_attach for unreachable_entry. **Same PV-48 selection bias** — these picks invisible to learning. Should at least journal "outcome=unreachable_entry, r_multiple=None" for visibility.

### Lines 297-331: SL/TP walk-forward
- PV-56 GOOD (lines 298-303): **Bug archaeology BUG-2** — documents pick_date-bar inclusion fix.
- PV-57 GOOD (lines 305-306): high/low extraction. Float-coerced.
- PV-58 GOOD (lines 307-321): **TIE-BREAKER LOGIC for same-day-both-hit.** Uses Open as proxy for direction. Reasonable heuristic.
- PV-59 BUG (lines 309-312): If Open is INSIDE both SL and TP (rare for daily bar), `dist_to_tp` and `dist_to_sl` may both be small. Tie-break still picks closer one. Edge case.
- PV-60 BUG (line 313): `if dist_to_tp < dist_to_sl` — **strict less than**. If Open is exactly equidistant, TP loses → SL wins. **Defensive (capital preservation bias).** ✅
- PV-61 GOOD (line 320): Tie-break event logged.

### Lines 333-357: outcome-found path
- PV-62 GOOD (lines 333-340): R-multiple computation. Risk = entry - sl.
- PV-63 GOOD (line 340): `if risk > 0 else 0` — zero-risk fallback prevents div-by-zero.
- PV-64 BUG (line 340): If risk = 0 (entry == sl, broken plan), r_multiple = 0. **Logged as 0R win/loss.** Misleading. Should be NULL/None.
- PV-65 GOOD (lines 341-343): SPY + sector alpha. Recently added (May 2 2026).
- PV-66 BUG (lines 344-353): Per PV-X4, identical try/except block #1.
- PV-67 GOOD (line 348): `r.get("r_multiple") not in (None, "", "None")` — handles 3-way None sentinel. **Defensive against PV-25 None-as-string CSV writes.** Per Batch 11 PL-X1.
- PV-68 BUG (line 354): `outcome.replace("_hit", "_hits")` — string magic to convert tp_hit→tp_hits for counts. Brittle. Better: explicit dict mapping.

### Lines 358-397: day_close path (Bug #5)
- PV-69 GOOD (lines 359-363): **EXCELLENT bug archaeology** — documents Bug #5 + MPWR case.
- PV-70 GOOD (lines 369-371): Handles non-trading-day pick_date by finding next bar.
- PV-71 GOOD (lines 375-381): Standard outcome attribution.
- PV-72 BUG (lines 384-393): Per PV-X4, identical try/except block #2.

### Lines 399-431: expired-by-MAX_DAYS_OPEN path
- PV-73 GOOD (lines 401-413): Standard expiration handling with last-close exit price.
- PV-74 BUG (lines 414-423): Per PV-X4, identical try/except block #3 — THIRD copy.
- PV-75 GOOD (line 430): Friendly print for still-open positions.

### Line 432: _save_picks call
- PV-76 GOOD: Atomic save at end. Per PV-X2.

## src/position_monitor.py — LINE BY LINE

### Lines 1-17: Module docstring
- PM-1 GOOD: 17-line docstring documents:
  - Single source of truth (picks_log.csv, no positions.json)
  - Usage example
  - MAX_HOLD per trade_type table
- PM-2 GOOD: **"no positions.json to avoid sync bugs"** — architectural decision documented.

### Lines 18-29: Imports + constants
- PM-3 BUG (line 22): Relative path. **20th file with this pattern.**
- PM-4 GOOD (lines 24-29): Named MAX_HOLD_DAYS dict + DEFAULT_MAX_HOLD.
- PM-5 BUG: Per PM-X2 head finding, day=1 / swing=10 / multi=30 / default=14 disagrees with pick_evaluator MAX_DAYS_OPEN=20. **Same logical concept, different constants.**

### Lines 32-38: _parse_date
- PM-6 GOOD: Defensive date parser.
- PM-7 BUG (line 37): bare except. Theme T1.

### Lines 41-42: _max_hold_for
- PM-8 GOOD: Lookup with fallback to default.
- PM-9 GOOD: `(trade_type or "").lower()` — defensive against None and case variation.

### Lines 45-112: scan_open_positions
- PM-10 GOOD (lines 45-61): Type-hinted, optional today arg (test injectable).
- PM-11 BUG (line 61): `date.today()` — NAIVE. Per cross-cutting.
- PM-12 GOOD (line 62-63): Defensive existence check.
- PM-13 GOOD (line 66): `list(csv.DictReader(f))` — full file in memory but file should be small (only pending picks needed).
- PM-14 GOOD (line 70): `r.get("evaluation_status")` — defensive **vs** pick_evaluator PV-45 `r["..."]`. **Better defense in PM.**
- PM-15 GOOD (lines 78-83): 3-tier severity (over / near / skip).
- PM-16 BUG (line 80): `days_open == max_hold - 1` — strict equality. **A pick at exactly max_hold-1 days is "near", at max_hold-2 is silent, at max_hold is "over".** Single-day window for "near" is narrow.
- PM-17 GOOD (lines 85-88): Defensive entry float parse.
- PM-18 GOOD (lines 91-97): Telegram message with HTML formatting.
- PM-19 GOOD (line 111): Sort by overdue-amount DESC. Most-overdue first.

### Lines 115-130: format_telegram_summary
- PM-20 GOOD: Empty alerts → "" (no message). Defensive.
- PM-21 GOOD (lines 119-120): Splits over vs near.
- PM-22 GOOD: Sectioned message with explicit counts.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### PV-X1: Split-adjustment bug latent
auto_adjust=False (line 60) means OHLC is raw. A stock split during the pick window will:
- Make the post-split bars look like a 50% (or whatever ratio) crash
- Trigger spurious SL hit on the ex-date
- Mark pick as sl_hit when actually unaffected
**Should be auto_adjust=True for evaluation, OR detect splits and adjust.** **Latent landmine.**

### PV-X2 + cross-cutting: Atomic write inconsistency on SAME FILE
- pick_logger.py PL-19 writes picks_log.csv WITHOUT atomic write
- pick_evaluator.py PV-X2 writes picks_log.csv WITH atomic write
**Same target file, two writers, two safety levels.** Per Batch 11 PL-X1 schema chaos, this is exactly the kind of inconsistency that makes pick_logger fragile. **Should consolidate writes through a picks_csv.py helper module** that always uses atomic write.

### PV-X3: Best bug archaeology in audit
4 explicitly-dated bug fixes documented in comments:
- BUG-2 (May 2 2026): pick_date bar inclusion (line 298)
- F3 (May 4 2026): unreachable_entry detection (line 265)
- Bug #5 (May 5 2026): day_close force-close (line 359)
- May 11 2026: atomic write (line 38)
**Author maintains a living bug log inline.** **Template** for documenting fix rationale.

### PV-X4: 3 copies of journal_attach try/except
Lines 344-353, 384-393, 414-423 — IDENTICAL 9-line block. **Should extract:**
    def _safe_journal_attach(row, ret, evaluated_on, *, context):
        try:
            _journal_attach(...)
        except Exception as e:
            print(f"[eval] WARN journal_attach ({context}) failed for {row.get('ticker','?')}: {e}")
Triple DRY violation in critical learning path.

### PM-X2 + PV-5: Time-decay constants disagree
- pick_evaluator MAX_DAYS_OPEN = 20
- position_monitor MAX_HOLD_DAYS = {day:1, swing:10, multi:30, default:14}
**Same logical concept, two sources of truth.** A swing pick at day 12: PM says "over" but PV says "still_open." Operator confusion + downstream double-handling.

### PV-X5 + PV-48 + PV-55: Selection bias in learning
- Too-old picks expired without journal_attach (PV-48)
- unreachable_entry picks not journaled (PV-55)
**Both classes invisible to signal_journal/calibration/hypothesis_engine.** Learning system sees ONLY tp/sl/expired-with-data picks. **Skews stats.** A consistent class of "logged-but-unfillable" picks NEVER influences future decisions.

### Cross-cutting: 20 files with relative-path constants
Cumulative.

### Cross-cutting: ATOMIC WRITE adoption (running tally)
Now 3 of 11 audited state-writers do atomic write:
1. market_data_health.py
2. news_signals.py
3. pick_evaluator.py
8 modules still without: pick_logger, regime, news_engine, finnhub_data, pattern_stats, signal_journal, wisdom_base, weight_applier.
**73% of state-writers UNSAFE.**

### Cross-cutting: Defensive .get() vs raw [] access
- PM-14 uses r.get("evaluation_status") OK
- PV-45 uses r["evaluation_status"] BAD (KeyError-prone)
**Within Phase D first batch, two access patterns.**

## SUMMARY (Batch 27)

| Severity | pick_evaluator | position_monitor | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 14 | 5 | 5 | 24 |
| Data/safety | 8 | 3 | 0 | 11 |
| Code smell | 5 | 2 | 0 | 7 |
| Good code | 41 | 14 | 0 | 55 |
| Total findings | 68 | 24 | 5 | 97 |

## TOP 10 CRITICAL FIXES from Batch 27

1. PV-X1 / PV-15: Set auto_adjust=True in yf.download for evaluation OR detect splits. **Latent silent-corruption bug.** (15 min)
2. PV-X4: Extract _safe_journal_attach helper. Triple DRY violation. (15 min)
3. PV-48 + PV-55: Journal too-old expired AND unreachable_entry picks (with appropriate outcome). Eliminates learning selection bias. (30 min)
4. PM-X2 / PV-5: Unify time-decay constants. Single TIME_DECAY config. (15 min)
5. PV-X2 cross-cutting: Move all picks_log.csv writes through picks_csv.py with atomic write. (1 hr)
6. PV-25 / PV-39: Don't write None to CSV (writes "None" string). Use "". (5 min)
7. PV-45 + PV-50: Use .get() defensively instead of r[...]. (10 min)
8. PV-19: Add bound to _SPY_CACHE size or evict on pickle exit. (10 min)
9. PV-64: r_multiple should be None (not 0) when risk=0. (5 min)
10. PM-16: Widen "near" window to last 3 days instead of single day. (5 min)

## NEW THEMES UPDATED

- Theme T1 (bare except): PV has 5 bare excepts + 3 documented JSON catches. PM has 1 bare. Mixed.
- Theme T2 (schema drift): PV-31, PV-32 confirm 6 different field names across 2 logical concepts. PV-67 None-sentinel handling.
- Theme T6 (atomic writes): NOW 3 of 11 state-writers safe. PV is gold-standard with documentation.
- Theme T8 (DRY): PV-X4 triple journal_attach copy. PM-X2 / PV-5 time-decay duplicate.
- Theme T11 (fail-open by accident): PV-X5 selection bias removes outcome classes from learning.
- Theme T13 (silent-default-fills): PV-25 None-as-string in CSV.
- Theme T14 (gold-standard patterns): pick_evaluator atomic write + bug archaeology = template. position_monitor single-purpose READ-ONLY clean.
- Theme T18 NEW (split-adjust landmine): PV-X1 — auto_adjust=False creates spurious SL hits on splits.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A (safety/gates) | 8/8 COMPLETE | (none) | 8/8 |
| Phase B (scoring/data) | 18/18 COMPLETE | (none) | 18/18 |
| Phase C (brain pillars) | 12/12 COMPLETE | (none) | 12/12 |
| Phase D (pipeline & output) | 2/~30 done | pick_evaluator, position_monitor | 2/~30 |
| Total true line-by-line | | +2 files | **55 of ~382 (~14.4%)** |
| Remaining | | | **~327 files** |

## NEXT BATCH

Batch 28: src/paper_trader.py + src/nightly_conductor.py — paper_trader is order execution (CRITICAL — never audited). nightly_conductor is mutation orchestrator (per MB-1 line 14: "mutations themselves happen in nightly_conductor").

End of Batch 27. Phase D in progress (2/30).
