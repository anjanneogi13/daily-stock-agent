# Audit Batch 105 — `news_signal_evidence_report.py` (566 lines) + `discover_themes.py` (763 lines) — FULL line-by-line

**Pinned commit:** `31b868b8`
**Total lines audited in this batch:** 1,329
**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

# PART A — `scripts/news_signal_evidence_report.py` (566 lines, 20.8 KB)

## A.1 Header + imports (lines 1–32)

### ✅ GOOD-NSER1: Excellent module docstring (lines 2–19)
- Documents purpose ("read-only News Signal Evidence Report"), explicit safety claim ("does not mutate official pick stats"), exhaustive list of inputs read AND outputs written. Best-in-class header in the repo.

### ✅ GOOD-NSER2: `from __future__ import annotations` (line 20)
- Forward-references work without quoting. Modern Python 3.10+ style.

### ⚠️ BUG-NSER1: `ZoneInfo` only — no fallback for missing tzdata (line 27)
- On Windows or stripped containers without `tzdata` package, `ZoneInfo("America/New_York")` raises `ZoneInfoNotFoundError` at module import time → cannot import the script. Other repo files (per Batches 75, 86) wrap in try/except.
- **Severity:** ⚠️ Container portability.

## A.2 Helpers (lines 34–82)

### ⚠️ BUG-NSER2: `_today_et()` uses UTC then converts (line 35)
- `datetime.now(timezone.utc).astimezone(ET)` — correct. But the rest of the project mixes UTC `now()` and naive `now()`. Repo-wide inconsistency (matches main.py BUG-M31).

### ⚠️ BUG-NSER3: `_safe_float` returns `default` for `"None"` string (lines 38–44)
- Treats Python `None`, empty string, AND literal `"None"` as missing. A row with explicit `tradeable_score=0` is indistinguishable from missing.
- **Severity:** 🟡 Quiet conflation.

### ⚠️ BUG-NSER4: `load_json` swallows ALL exceptions silently (lines 47–53)
- `except Exception: return default` — corrupt JSON → empty dict, no log, no metric. Operator never sees the silent data loss.
- **Severity:** ⚠️ Silent data loss.

### ⚠️ BUG-NSER5: `load_jsonl` increments `invalid` for non-dict objects (lines 56–72)
- A JSONL line of `[1,2,3]` is "invalid" — but it's still valid JSON. Mislabels schema mismatch as parse failure.
- **Severity:** 🟡 Diagnostic accuracy.

### ⚠️ BUG-NSER6: `load_jsonl` reads entire file into memory (line 61)
- `path.read_text().splitlines()` — fine for daily news log, but if `news_log.jsonl` grows to GB, OOM. No streaming.
- **Severity:** 🟡 Scaling cliff.

### ⚠️ BUG-NSER7: `load_csv` swallows all errors (lines 75–82)
- Same issue as NSER4. Bad CSV → empty list → all downstream "official picks news usage" silently shows 0.
- **Severity:** ⚠️ Silent data loss.

## A.3 `_news_log_summary` (lines 85–120)

### ✅ GOOD-NSER3 (corrected): `isinstance(cls, dict)` guard on line 97 prevents crash from schema drift on `classification` field.

### ⚠️ BUG-NSER9: `tradeable_score >= 0.85` magic number (line 102)
- "high tradeable" threshold hardcoded. Doesn't match the 0.80/0.70 thresholds in `discover_themes.classify_lifecycle`.
- **Severity:** 🟡 Magic + cross-file inconsistency.

### ✅ GOOD-NSER4: Returns `dict(sorted(...))` for stable keys (lines 114–116)
- Deterministic JSON output. Good for diff-friendly artifacts.

## A.4 `_signals_summary` (lines 123–166)

### ⚠️ BUG-NSER10: `score_delta > 0` excludes zero (line 150)
- A signal with `score_delta=0` is neither bullish nor bearish nor hard_block. Vanishes from all 3 buckets but still counted in `active`.
- **Severity:** 🟡 Edge case.

### ✅ GOOD-NSER5: `active.sort(key=lambda x: (-abs(x["score_delta"]), x["ticker"]))` (line 155)
- Sort by absolute strength + ticker tiebreak. Stable, deterministic.

## A.5 `_watchlist_summary` (lines 169–205)

### ⚠️ BUG-NSER11: Three nearly-identical comprehensions (lines 178–180)
- DRY violation. If `sentiment` field is renamed, must update 3 lines.
- **Severity:** 🟡

### ⚠️ BUG-NSER12: `top_items` sliced to 20 — silent truncation (line 204)
- Operator doesn't see a "truncated to 20 of N" hint in the JSON.
- **Severity:** 🟡 Lossy.

## A.6 `_late_ideas_summary` (lines 208–229)

### ⚠️ BUG-NSER13: `news_rows` filter assumes only 2 source values (line 209)
- If a new source like `"theme_signal"` is added, it's silently excluded.
- **Severity:** 🟡 Schema-drift blindness.

### ⚠️ BUG-NSER14: `items` field returns ALL rows (lines 215–228)
- Unbounded. If late_ideas has 1000 rows, JSON balloons. Compare to `_watchlist_summary` which slices to 20.
- **Severity:** 🟡 Inconsistency.

## A.7 `_run_status_summary` (lines 232–248)

### ⚠️ BUG-NSER15: `int(r.get("items_fetched") or 0)` crashes on non-numeric (line 235)
- If field is `"abc"`, `int("abc")` crashes. No try/except.
- **Severity:** ⚠️ Schema-drift crash.

### ⚠️ BUG-NSER16: `latest = rows[-1]` assumes time-sorted (line 233)
- JSONL append-order, but if any process writes out-of-order, `[-1]` is wrong "latest".
- **Severity:** 🟡 Subtle correctness.

## A.8 `_official_picks_news_summary` (lines 251–281)

### ⚠️ BUG-NSER17: `r.get("watch_only") or ""` then `.lower() == "true"` (line 262)
- Treats only string `"true"` as truthy. If CSV has `"True"` or `"1"`, treated as not-watch-only. Inconsistent with `discover_themes._boolish`.
- **Severity:** ⚠️ Cross-file boolean parsing inconsistency.

### ⚠️ BUG-NSER18: `_safe_float(r.get("news_boost"), 0.0)` then `bool()` (line 259)
- `bool(0.0) = False`. A pick with explicit zero boost is "no news fields". Conflation.
- **Severity:** 🟡 Logic conflation.

## A.9 `_outcomes_summary` (lines 284–338)

### ⚠️ BUG-NSER19: `_safe_float(...)` returns `None` on parse failure OR genuine missing (lines 295–298)
- Conflation. `None` outcome means parse failure OR missing.
- **Severity:** ⚠️ Lossy diagnostics.

### ⚠️ BUG-NSER20: `top_evaluated` sort tiebreak uses `or 0` (line 325)
- `None or 0 = 0`. Missing-data rows sort with zero-return rows.
- **Severity:** 🟡

### ⚠️ BUG-NSER21: `top_evaluated` truncated to 20 silently (line 329)
- Same as NSER12.

## A.10 `build_report` (lines 341–397)

### ✅ GOOD-NSER6: `exists` block (lines 373–381)
- Explicitly reports which input files were present.

### ✅ GOOD-NSER7: `invalid_json_lines` block (lines 382–387)
- Surface-level visibility of parse failures.

### ⚠️ BUG-NSER22: `mode: "monitoring_only"` hardcoded (line 359)
- If TRADING_MODE env is later changed, this artifact lies. No env read.
- **Severity:** 🟡 Static claim.

### ⚠️ BUG-NSER23: `paper_trading_enabled: False` hardcoded (line 362)
- Per main.py BUG-M94, `_should_log_paper_trade` is env-driven. This script unconditionally claims false.
- **Severity:** ⚠️ Misleading safety claim.

### ⚠️ BUG-NSER24: `live_trading_enabled: False` hardcoded (line 363)
- Same issue as NSER23.
- **Severity:** ⚠️ Misleading safety claim.

### ⚠️ BUG-NSER25: No try/except around any of the 7 summary calls (lines 388–394)
- If any one summary helper crashes, the whole report dies. No partial degradation.
- **Severity:** ⚠️ Brittle pipeline.

## A.11 `format_markdown` (lines 400–533)

### 🟡 BUG-NSER26: 130-line markdown formatter, hard to maintain (lines 400–533)
- All formatting inline. No template helper.
- **Severity:** 🟡 Maintainability.

### ⚠️ BUG-NSER27: f-string with no None handling (line 454)
- `f"- **{item['ticker']}** {item['score_delta']:+.3f}"` crashes if score_delta is None.
- **Severity:** 🟡

### ⚠️ BUG-NSER28: Hardcoded slice `[:20]` and `[:10]` repeated (lines 452, 471, 492)
- Magic numbers. Not configurable.
- **Severity:** 🟡

### ✅ GOOD-NSER8: "## Next evidence gap" footer (lines 526–531)
- Self-documents what the report DOESN'T do. Honest scope-limit.

## A.12 `write_outputs` (lines 536–543)

### 🚨 BUG-NSER29: NOT atomic write (lines 541–542)
- `json_path.write_text(...)` directly. If process killed mid-write, corrupt JSON.
- **Severity:** 🚨 Single-file-corruption risk.

## A.13 `main` (lines 546–565)

### ✅ GOOD-NSER9: `argparse` with sane defaults (lines 547–551)
- `--date` defaults to today, `--data-dir` to `DATA_DIR`, `--no-write` for dry runs.

### ⚠️ BUG-NSER31: No exit code on partial failure (line 561)
- Always returns 0. If 4 of 7 input files were missing, still success.
- **Severity:** ⚠️ CI/operator can't distinguish partial vs complete success.

### ✅ GOOD-NSER10: `if __name__ == "__main__": raise SystemExit(main())` (lines 564–565)
- Proper Python entrypoint with explicit exit code.

---

## 📊 PART A summary — `news_signal_evidence_report.py`

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 1 |
| ⚠️ Data/safety risk | 14 |
| 🟡 Code smell | 13 |
| ✅ Good code | 10 |
| **Total** | **38 findings** |

### Top 5 fixes for this file
1. **NSER29** — atomic write helper for the JSON+MD outputs (corrupt-on-crash risk).
2. **NSER23+NSER24** — read env for paper/live trading flags instead of hardcoding (misleading safety claim).
3. **NSER25** — wrap each of the 7 summary calls in try/except for partial degradation.
4. **NSER15** — `int(... or 0)` → safe-int helper (schema-drift crash).
5. **NSER17** — unify `_boolish` parsing across this file and `discover_themes.py`.

---

# PART B — `scripts/discover_themes.py` (763 lines, 29.8 KB)

## B.1 Header + imports (lines 1–28)

### ✅ GOOD-DT1: Excellent docstring with safety contract (lines 2–14)
- Explicit "observe-only" with 5-bullet safety claim. Best safety-statement style in the repo.

### ✅ GOOD-DT2: Stdlib-only imports (lines 18–25)
- No 3rd-party deps. Container-portable.

## B.2 SAFETY constant (lines 30–37)

### ✅ GOOD-DT3: Module-level SAFETY dict (lines 30–37)
- Single source of truth for safety claims.

### ⚠️ BUG-DT1: SAFETY values are static — same misleading-claim risk as NSER23 (lines 32–36)
- `paper_trading_enabled: False` etc. don't reflect actual env state.
- **Severity:** ⚠️

## B.3 THEME_STOPWORDS (lines 39–71)

### 🟡 BUG-DT2: `"buy"` and `"eps"` listed TWICE (lines 41, 47, 50, 54)
- `"buy"`, `"eps"`, `"estimate"`, `"estimates"` all duplicated. Set absorbs duplication, but reveals careless maintenance.
- **Severity:** 🟡 Code hygiene.

### ⚠️ BUG-DT3: Stopwords are English-only and lowercased (lines 39–71)
- Non-English headlines bypass all filtering.
- **Severity:** 🟡 i18n blindness.

### ⚠️ BUG-DT4: Hardcoded analyst names "canaccord", "genuity", "morgan", "stanley", "ubs" (lines 53, 64, 70)
- Maintained by hand. Will drift as new analysts/providers appear.
- **Severity:** 🟡 Maintenance burden.

### ⚠️ BUG-DT5: Stopwords mix word stems and full words inconsistently (lines 39–71)
- `"announc"` (stem) but `"announces"` (full word). Inconsistent filtering.
- **Severity:** 🟡

## B.4 Helpers `_safe_float`, `load_json` (lines 74–89)

### ✅ GOOD-DT4: `_safe_float` allows `default=None` (lines 74–80)
- Better than NSER3 because explicit None-default lets callers distinguish "missing" from "zero".

### ⚠️ BUG-DT6: `load_json` swallows all errors (lines 83–89)
- Same as NSER4. Silent data loss.
- **Severity:** ⚠️

## B.5 `_normalize_token` (lines 92–110)

### ⚠️ BUG-DT7: Hardcoded plural→singular dict only covers 6 cases (lines 95–101)
- Coverage gap.
- **Severity:** 🟡

### ⚠️ BUG-DT8: Suffix stripping crude (lines 104–109)
- Crude stemmer; would lose precision in real-world use.
- **Severity:** 🟡 Algorithmic crudeness.

### 🟡 BUG-DT9: Length check `len(token) > 7` is arbitrary (lines 104, 106, 108)
- Why 7? No justification.
- **Severity:** 🟡 Magic.

## B.6 `_tokenize` (lines 113–125)

### ✅ GOOD-DT5: Regex `[A-Za-z][A-Za-z0-9+\-]{1,}` (line 114)
- Captures alphanumeric tokens including `+/-`.

### ⚠️ BUG-DT10: `len(t) < 3 and t not in {"ai", "ev"}` whitelist (line 120)
- Only "ai" and "ev" allowed as 2-char tokens. "5G", "IT", "VR", "AR", "ML", "BI" all filtered out. Theme detection will miss these explicitly.
- **Severity:** ⚠️ Coverage gap for real themes.

## B.7 `extract_theme_terms` (lines 128–188)

### ✅ GOOD-DT6: Excellent docstring explaining "candidate themes derived from evidence" (lines 129–133)

### ⚠️ BUG-DT11: `unigram_limit = min(len(ranked_tokens), max(6, max_terms // 2))` (line 174)
- Mathematically opaque. Could be just `min(len(ranked_tokens), 6)`.
- **Severity:** 🟡 Cognitive overhead.

### ⚠️ BUG-DT12: Bigram dedup against `ranked` is O(n²) (lines 183–186)
- `if term not in ranked` on a list. Scaling cliff if max_terms grows.
- **Severity:** 🟡

### ⚠️ BUG-DT13: `priority_bigram` only uses 2 tokens (line 170)
- A category like "ai_chip_supply_chain" → `"ai chip"` only. Loses "supply chain" entirely.
- **Severity:** 🟡 Information loss.

## B.8 `_watchlist_items`, `_news_signal_items` (lines 191–205)

### ⚠️ BUG-DT14: Two nearly-identical helpers (lines 191–205)
- DRY violation.
- **Severity:** 🟡

## B.9 `load_evidence` (lines 208–257)

### ⚠️ BUG-DT15: Bare `except Exception: pass` for picks_log (lines 237–238)
- Silent data loss.
- **Severity:** ⚠️

### 🟡 BUG-DT16: `input_status.rows` re-iterates `evidence` 3 times (lines 244, 249, 254)
- O(n×3) when O(n×1) suffices.
- **Severity:** 🟡 Performance.

### ✅ GOOD-DT7: Tags each evidence row with `source` (lines 218, 223, 234)

### ⚠️ BUG-DT17: `watch_only` boolean parsing differs from NSER17 (line 235)
- Here: `{"1","true","yes"}`. In NSER17: only `"true"`. Cross-file inconsistency.
- **Severity:** ⚠️

## B.10 `_theme_id`, `_sentiment_score`, `_pick_returns` (lines 260–283)

### ✅ GOOD-DT8: `_theme_id` produces stable, filesystem-safe ID (lines 260–261)

### ⚠️ BUG-DT18: `_sentiment_score` returns 0.0 for empty (line 272)
- An empty bucket and a perfectly-balanced bucket both return 0.0.
- **Severity:** 🟡

### ⚠️ BUG-DT19: `_pick_returns` only reads `actual_return_pct` (line 280)
- Misses other return fields in the picks_log schema.
- **Severity:** 🟡 Coverage gap.

## B.11 RETURN/RELATIVE_STRENGTH field aliases (lines 286–297)

### ✅ GOOD-DT9: Field aliases as module constants (lines 286–297)

### ⚠️ BUG-DT20: Aliases conflate `relative_strength_vs_spy_pct` AND `alpha_pct` (line 294)
- These mean different things in the repo (per Batch 99).
- **Severity:** ⚠️ Semantic conflation.

## B.12 `_first_float`, `_boolish`, `_count_boolish`, `_avg` (lines 300–323)

### ⚠️ BUG-DT21: `_boolish` accepts `"breakout"` and `"new_high"` as truthy (line 311)
- Domain-coupled boolean parsing. Pollutes generic helper.
- **Severity:** 🟡

### ✅ GOOD-DT10: `_avg` returns None for empty (line 323)
- Distinguishes "no data" from "zero average".

## B.13 `_provider_evidence` (lines 326–347)

### ⚠️ BUG-DT22: Bare except inside Counter increment (lines 338–339)
- Silent skip.
- **Severity:** 🟡

### ⚠️ BUG-DT23: Reads two date-stamped files (lines 327–328)
- If the date string format ever changes (timezone shift), files won't match.
- **Severity:** ⚠️ Date-mismatch risk.

## B.14 `_theme_market_evidence` (lines 350–462)

### 🚨 BUG-DT24: 113-line function does too many things (lines 350–462)
- Should be 4–5 functions.
- **Severity:** 🟡 Maintainability.

### ⚠️ BUG-DT25: `mean(...)` repeated DRY violation (lines 422, 432)
- Both use `mean()` not `_avg()`.
- **Severity:** 🟡

### 🚨 BUG-DT26: Magic adjustment constants (lines 442–445)
- `0.15`, `0.20`, `5.0` clamp, `0.75`, `4.0` clamp. Six magic numbers, no comments. Not config-driven.
- **Severity:** ⚠️ Magic + opaque scoring algorithm.

### ⚠️ BUG-DT27: `tickers_with_return_evidence` calls `_first_float` 4× per row (lines 414–418)
- O(n × 4 × ~3 alias keys).
- **Severity:** 🟡

### ⚠️ BUG-DT28: `_provider_evidence` called twice per `build_theme_discovery` (lines 393, 625)
- With 50 themes → 50× file-read of `market_data_health_{date}.json`.
- **Severity:** ⚠️ I/O thrash.

## B.15 `classify_lifecycle` (lines 465–485)

### ⚠️ BUG-DT29: Ten hardcoded thresholds (lines 473–484)
- `<= -5`, `>= 3`, `< -0.25`, `>= 10`, `>= 0.80`, `>= 0.45`, `>= 5`, `>= 0.70`, `>= 0.35`, `>= 0.20`. No documentation, no config.
- **Severity:** ⚠️ Opaque classification algorithm.

### ⚠️ BUG-DT30: Order of checks matters but isn't documented (lines 473–485)
- Whichever check is first wins. Unstated priority.
- **Severity:** 🟡 Hidden precedence.

## B.16 `_theme_risk_flags` (lines 488–510)

### ✅ GOOD-DT11: `list(dict.fromkeys(flags))` for dedup-preserve-order (line 510)

### ⚠️ BUG-DT31: 4 different flag-emission cascades (lines 492–508)
- Spread across `if` statements without grouping.
- **Severity:** 🟡

## B.17 `build_theme_discovery` (lines 513–651)

### 🚨 BUG-DT32: 138-line function — too long (lines 513–651)
- Eight responsibilities in one function.
- **Severity:** 🟡 Refactor needed.

### 🚨 BUG-DT33: Theme score formula has magic numbers (lines 563–571)
- Six weights, no documentation, no config, no derivation.
- **Severity:** ⚠️ Opaque scoring.

### ⚠️ BUG-DT34: `theme_score` clamped to `[0.0, 100.0]` (line 592)
- Additive formula can easily exceed 100. Clamping loses signal at the top end.
- **Severity:** 🟡

### ⚠️ BUG-DT35: `tickers[:25]` and `evidence_examples[:6]` magic limits (lines 587, 594)
- Hardcoded slices.
- **Severity:** 🟡

### ⚠️ BUG-DT36: Per-theme `_theme_market_evidence` call inside loop (line 560)
- With 100 themes, 200 redundant disk reads.
- **Severity:** ⚠️ I/O thrash.

### ✅ GOOD-DT12: Three-tier deterministic sort (line 600)

### ⚠️ BUG-DT37: `data_provider_status` dict mostly hardcoded strings (lines 615–629)
- A value of `"available"` doesn't mean data IS available, only that it COULD be.
- **Severity:** ⚠️ Documentation-as-data antipattern.

## B.18 `format_markdown` (lines 662–727)

### 🟡 BUG-DT38: 65-line markdown formatter (lines 662–727)
- Same maintainability issue as NSER26.

### ⚠️ BUG-DT39: `tickers[:12]` slice (line 686). Magic.

### ⚠️ BUG-DT40: `evidence_examples[:3]` and headline `[:140]` slices (lines 714–715). Both magic.

## B.19 `write_outputs` (lines 730–739)

### 🚨 BUG-DT41: NOT atomic write (lines 735, 738)
- Same as NSER29. Crash mid-write → corrupt file.
- **Severity:** 🚨

### ✅ GOOD-DT13: Trailing newline appended `+ "\n"` (lines 735, 738)

## B.20 `main` (lines 742–762)

### ⚠️ BUG-DT42: `--date` default uses UTC not ET (line 744)
- Different from NSER's `_today_et()`. Two scripts using different clocks for the same `--date` semantics.
- **Severity:** ⚠️ Cross-file date inconsistency.

### ⚠️ BUG-DT43: No exit code on partial failure (line 758)
- Same as NSER31.

### ✅ GOOD-DT14: Standard entrypoint pattern (lines 761–762)

---

## 📊 PART B summary — `discover_themes.py`

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 5 |
| ⚠️ Data/safety risk | 18 |
| 🟡 Code smell | 19 |
| ✅ Good code | 14 |
| **Total** | **56 findings** |

### Top 5 fixes for this file
1. **DT26+DT29+DT33** — magic numbers in three scoring/classification functions; move to `config.yaml`.
2. **DT41** — atomic write for the JSON+MD outputs.
3. **DT28+DT36** — cache `_provider_evidence` once at top; avoid 200 disk reads.
4. **DT42** — unify date semantics with NSER (use ET-anchored helper).
5. **DT24+DT32** — refactor 113- and 138-line functions into smaller units.

---

## 🎯 BATCH 105 grand totals

| Severity | NSER | DT | Combined |
|---|---:|---:|---:|
| 🚨 Show-stopper | 1 | 5 | **6** |
| ⚠️ Data/safety risk | 14 | 18 | **32** |
| 🟡 Code smell | 13 | 19 | **32** |
| ✅ Good code | 10 | 14 | **24** |
| **Total** | **38** | **56** | **94 findings in 1,329 lines** |

### Cross-file patterns spotted in Batch 105

1. **Hardcoded safety claims** that don't read env (NSER22-24, DT1) — both files lie if user toggles paper/live mode.
2. **Inconsistent boolean parsing** (NSER17 vs DT17) — same CSV `watch_only` field parsed differently.
3. **Date semantics mismatch** (NSER2 ET vs DT42 UTC) — same `--date` flag means different days near midnight.
4. **Silent error swallowing** in 5+ places (NSER4, NSER7, DT6, DT15, DT22) — operator can't tell partial vs complete success.
5. **Non-atomic writes** in both files (NSER29, DT41) — corrupt-on-crash risk.
6. **Magic numbers everywhere** (NSER9, DT9, DT11, DT26, DT29, DT33, DT34, DT35, DT39, DT40) — no config-driven tuning.

---

## ✅ scripts/ is now 100% line-by-line audited

After Batch 105:
- `scripts/news_signal_evidence_report.py`: 566/566 lines ✅
- `scripts/discover_themes.py`: 763/763 lines ✅
- All other scripts/: covered in Batches 05–09

**Production code coverage: ~100% (excluding tests/).**
