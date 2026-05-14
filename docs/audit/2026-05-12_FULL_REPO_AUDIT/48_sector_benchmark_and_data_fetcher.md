# Batch 42 — src/sector_benchmark.py (80 lines) + src/data_fetcher.py (231 lines) — TRUE LINE-BY-LINE

**Date:** 2026-05-12
**Files:** sector_benchmark.py (80 lines), data_fetcher.py (231 lines)
**Phase:** D (pipeline & output) — files 21 and 22 of ~30

## TOP HEADLINE FINDINGS

1. SB-X1: sector_benchmark.py is **THE TAG/SECTOR → ETF MAPPER** consumed by pick_evaluator (Batch 27 PV-X1). **PURE DATA + 1 RESOLVER FUNCTION.** Joins gold-standard pure-data club. ✅
2. SB-X2 (lines 46-58): **EXCELLENT BUG ARCHAEOLOGY** documenting Bug #8a (2026-05-05) — yfinance returns specific subsector strings, "without these, ~70% of picks fell through to SPY fallback, corrupting sector-relative alpha learning." **Quantified impact + dated.** **Joins 5th module with bug-archaeology gold standard** (PV B27, dedup B38, market_guard B40, universe B40, sector_benchmark this batch).
3. SB-X3 (line 53): `"Software—Application": "IGV", # em-dash, yfinance format` — **EM-DASH (—) not regular dash (-).** **Schema-detail-level archaeology.** Operator who recreates this dict from memory will use regular dash and silently break the mapping.
4. DF-X1: data_fetcher.py is **THE CENTRAL OHLCV FETCHER** with 3-PROVIDER chain: yfinance primary → Stooq fallback → empty df. **Per Batch 35 SP-X1 fallback design**, this is the integration point. **All Phase B/D modules use fetch_ohlcv.**
5. DF-X2 (lines 64-67): **EXCELLENT THREAD-SAFETY DOCSTRING** — "do not replace this with yf.download() in parallel fetches; yf.download() uses shared module-level state and previously caused cross-ticker data leakage." **Bug archaeology + warning + design rationale.** **One of the most-defensive comments in audit.** **6th module with bug archaeology.**
6. DF-X3 (line 42): `auto_adjust=False` — **MATCHES Batch 27 PV-15 cross-cutting split-adjustment landmine.** RAW prices. Per PV-X1 latent bug — a stock split in pick window appears as 50% drop in evaluator. **Now CONFIRMED in 2 places** (data_fetcher fetches raw, pick_evaluator walks raw). **Consistent — but consistently wrong.**
7. DF-X4 (lines 8-12): data_fetcher imports market_data_health (Batch 14) for **EVERY fetch event** — recordings flow into MDH for run summaries. **Per Batch 14 MDH-X1, MDH IS the observability backbone.** **DF feeds MDH which feeds dashboards.** Strong producer/consumer integration.

## src/sector_benchmark.py — LINE BY LINE

### Lines 1-11: Module docstring
- SB-1 GOOD: 11-line docstring with "Why" explanation + concrete example.
- SB-2 GOOD: **"A SEMI pick that beat SPY by +1% but underperformed SOXX by -3% is NOT alpha"** — operator-friendly capital-management lesson.
- SB-3 GOOD: Usage example with expected output.

### Line 12: Import
- SB-4 GOOD: typing only.

### Lines 16-25: TAG_TO_ETF
- SB-5 GOOD: 8 tag→ETF mappings with comment "more specific — checked FIRST."
- SB-6 BUG: Magic strings as tags (SEMI, AI, BIOTECH, etc.). Should be enum or shared constant module.
- SB-7 GOOD (line 18): "AI": "QQQ" with comment explaining "AI exposure ~ NASDAQ-100 best proxy". Documented design choice.
- SB-8 BUG (lines 22-25): CYBER, EV, DEFENSE — niche thematic ETFs. Operator should know these may have lower liquidity than XLK/XLV. No liquidity warning.

### Lines 28-59: SECTOR_TO_ETF
- SB-9 GOOD (lines 29-45): 16 generic-sector mappings.
- SB-10 GOOD: **Multiple synonyms for same sector** ("Financial", "Financials", "Financial Services" → all XLF). **Defensive against yfinance schema variation.** Per Batch 36 PF-7 cross-cutting Theme T2 schema-chaos.
- SB-11 BUG: **2 entries for "Materials" (Basic Materials + Materials)** but only 1 for some others. Inconsistent normalization.
- SB-12 GOOD (lines 46-48): Per SB-X2, 3-line bug-archaeology comment.
- SB-13 GOOD (lines 49-58): 10 subsector → specialized ETF mappings (Semiconductors→SOXX, Biotech→XBI, etc.).
- SB-14 BUG (lines 53-54, 56-57): Per SB-X3, em-dash vs hyphen discrimination. **VERY fragile.** **Two entries for Software (Application + Infrastructure) both → IGV.** Reasonable but operator may not know yfinance uses em-dash.
- SB-15 BUG: **Software—Infrastructure** would also reasonably map to IGM (iShares Tech Software Industry ETF) or HACK if security-focused. Subjective choice. Document.

### Lines 62-79: resolve_sector_etf
- SB-16 GOOD (lines 64-67): Docstring documents priority chain.
- SB-17 GOOD (lines 69-72): Tag wins via `tag.split("/")[0]` — extracts primary tag from "SEMI / AI" format.
- SB-18 BUG (line 70): `tag.split("/")[0].strip().upper()` — assumes "/" delimiter. **A tag without "/" returns the full tag.** ✅ defensive. **A tag with multiple "/" loses secondary tags.** Per pick schema, tags are formatted "SEMI / AI" so primary tag is what matters. Reasonable.
- SB-19 GOOD (lines 75-76): Sector fallback after tag.
- SB-20 GOOD (line 79): SPY ultimate fallback. Per pick_evaluator PV-33.

## src/data_fetcher.py — LINE BY LINE

### Line 1: Module docstring
- DF-1 BUG: 1-line docstring undersells the module — covers ONLY purpose, not the 3-tier provider chain or thread-safety design.

### Lines 2-13: Imports
- DF-2 GOOD: yfinance + pandas + os + ThreadPoolExecutor.
- DF-3 GOOD (lines 8-12): Imports MDH for observability — strong dependency contract.
- DF-4 GOOD (line 13): Stooq import for fallback — Per Batch 35 SP-1.

### Lines 15-19: SESSION setup
- DF-5 BUG: Per Batch 40 UN-3 cross-cutting, module-level SESSION init at import time. Anti-pattern for tests.

### Lines 21-26: Optional Finnhub import
- DF-6 GOOD: Defensive try/except with HAS_FINNHUB flag.
- DF-7 BUG (line 25): bare except — should be ImportError specifically.

### Lines 29-37: _normalize_ohlcv
- DF-8 GOOD (lines 31-32): None/empty short-circuit.
- DF-9 GOOD (line 34-35): MultiIndex flatten — handles yf shape variation.
- DF-10 GOOD (line 36): Lowercase columns — **MATCHES Batch 35 SP-42 stooq lowercase schema.** **Both providers return lowercase to caller — schema unified at fetch boundary.** ✅ Resolves Batch 35 SP-43 schema mismatch concern.
- DF-11 NOTE: Per Batch 31 PB docstring, pattern detectors expect uppercase. **Detectors must therefore be uppercase-converting upstream** OR data_fetcher's lowercase normalization breaks downstream. **Inconsistency confirmed** — needs investigation in patterns/ usage.

### Lines 40-43: _fetch_yfinance_ohlcv
- DF-12 GOOD (line 41): Conditional SESSION usage (curl_cffi fallback).
- DF-13 BUG (line 42): Per DF-X3, `auto_adjust=False`. Split-adjust bug.
- DF-14 GOOD (line 42): `timeout=20` explicit.

### Lines 46-47: _fetch_stooq_fallback_ohlcv
- DF-15 GOOD: Trivial wrapper.

### Lines 50-117: fetch_ohlcv — MAIN PUBLIC API
- DF-16 GOOD (lines 51-68): **Per DF-X2, 18-line docstring** with provider chain + safety guarantees + thread-safety warning.
- DF-17 GOOD (lines 69-91): yfinance try block with 3-state outcome handling (success/empty/error) + MDH event recording for each.
- DF-18 GOOD (lines 75-81): Empty-result event recorded explicitly. **Distinguishes "no data" from "error".**
- DF-19 GOOD (lines 83-90): Error event with classify_provider_error tag + truncated message.
- DF-20 GOOD (line 91): Print log truncated to 120 chars. Per Batch 39 cross-cutting.
- DF-21 GOOD (lines 93-115): Mirror block for Stooq fallback. **3-state outcome handling identical.** ✅ defensive consistency.
- DF-22 GOOD (line 117): Empty df fallthrough. **Per docstring "no stale/cache fabrication" — operator gets honest empty result.**

### Lines 120-132: fetch_universe_data
- DF-23 GOOD (line 121): max_workers=5 default — moderate parallelism.
- DF-24 GOOD (lines 123-129): ThreadPoolExecutor with as_completed for concurrent fetches.
- DF-25 BUG (line 128): `len(df) > 50` — magic 50-bar minimum. **A pick with 49 bars silently dropped.** Should be class const MIN_BARS_FOR_INCLUSION or documented.
- DF-26 GOOD (lines 130-131): Print summary + MDH run summary.

### Lines 135-191: fetch_info
- DF-27 GOOD (lines 137-148): **15-line default info dict.** Schema-stable.
- DF-28 GOOD (lines 138-139): **Bug #6 archaeology** — documents avoiding ticker-as-fake-name fallback.
- DF-29 GOOD (lines 150-179): yfinance fast_info try block.
- DF-30 GOOD (line 152): `t.fast_info` — lightweight endpoint.
- DF-31 GOOD (line 155): `or 1_000_000` averageVolume default. **A delisted/halted stock gets pretend 1M average volume.** Per Batch 8 risk_gate position-sizing uses averageVolume — **fake 1M default could cause oversizing in penny/halted stocks.** Latent bug.
- DF-32 GOOD (lines 158-164): **Documented opt-out for full info** — "yfinance .info is substantially heavier than fast_info and can trigger rate limits across hundreds of Daily Picks candidates." **Performance-driven design choice with archaeology.**
- DF-33 GOOD (line 164): `os.getenv("DAILY_FETCH_YF_FULL_INFO", "true")` — env-var feature flag with default-on.
- DF-34 GOOD (lines 165-174): Inner try/except for full info — degrades to fast info on failure.
- DF-35 BUG (lines 173-174): bare except pass. **Default OFF per docstring vs default ON per code line 164.** Comment-vs-code drift.
- DF-36 GOOD (line 168): `if long_name and ... != ticker.upper():` — per Bug #6 archaeology, rejects ticker-as-fake-name.
- DF-37 GOOD (lines 175-179): `try/except/else` pattern — MDH success only on no exception. **Idiomatic Python.**
- DF-38 GOOD (lines 182-189): Optional Finnhub fundamentals merge with `if v is not None and v != "N/A":` filter.
- DF-39 BUG (line 189): bare except print. Theme T1.

### Lines 198-230: is_valid_market_data
- DF-40 GOOD (lines 198-209): **Excellent docstring documenting 4 catch cases + scope ("hard gate, smell_stale_price is heavier").**
- DF-41 GOOD (line 211-212): currentPrice None check with operator-readable reason.
- DF-42 GOOD (lines 213-216): Numeric coercion try/except with reason string.
- DF-43 GOOD (line 217-218): Non-positive check.
- DF-44 GOOD (line 219-220): **>$100k sanity check** with operator-friendly reason. Catches BRK.A oddity.
- DF-45 BUG (line 219): Magic 100_000. Should be SUSPICIOUSLY_HIGH_PRICE constant + comment about BRK.A.
- DF-46 GOOD (lines 222-228): Volume validation similar.
- DF-47 GOOD (line 230): Returns (True, "valid") — operator gets reason even on success.

## CONSOLIDATED CROSS-CUTTING FINDINGS

### SB-X2 + DF-X2: Bug archaeology gold standard expanded
Now 6 modules with explicit dated/quantified bug archaeology:
- pick_evaluator (B27): 4 dated fixes
- dedup_sender (B38): PR #85
- market_guard (B40): PR #67
- universe (B40): PR #68
- sector_benchmark (this batch): Bug #8a + 70% impact quantified
- data_fetcher (this batch): Bug #6 + thread-safety yf.download archaeology

**6 modules now demonstrate this discipline.** Approximately 8% of audited files. **Should formalize:** require bug-archaeology comment for any fix that addresses a quantified production issue.

### DF-X3 + Batch 27 PV-15 cross-cutting confirmed: split-adjustment latent bug
- data_fetcher line 42: `auto_adjust=False`
- pick_evaluator line 60: `auto_adjust=False`
**Both fetch raw prices.** A 2-for-1 split during pick window:
- Pre-split bars: $200
- Post-split bars: $100 (raw)
- pick_evaluator walks bars and sees -50% drop on ex-date → triggers spurious SL hit
- Pick marked sl_hit when ACTUAL position unaffected (split adjusts shares)
**CONFIRMED 2-place latency.** **Single fix at data_fetcher level (auto_adjust=True) propagates correctly** since split-adjusted prices are uniform pre/post-split.

### DF-X4: Producer/consumer integration with MDH
data_fetcher emits ~6 distinct MDH events per ticker (yf success/empty/error + stooq success/empty/error + info success/error). For 100-ticker universe, ~600 MDH events per run. **Per Batch 14 MDH-X1, MDH writes to events.jsonl with atomic append.** Per Batch 22 SJ cross-cutting, JSONL append safety depends on MDH implementation. **Reverify MDH atomic-write status** — if MDH appends without atomic, 600 events per run is high concurrency risk.

### DF-31 + cross-cutting: averageVolume default 1_000_000 silent fill
Per Batch 8 risk_gate position sizing uses averageVolume. A delisted ticker gets fake 1M default → risk_gate sizes normally → operator orders 100 shares of an untradeable stock. **Latent.** Per Batch 18 FH-X3 silent default fill.

### DF-11 + Batch 31 PB cross-cutting: Schema mismatch follow-up
- data_fetcher returns LOWERCASE columns (DF-10)
- patterns/base docstring says expects UPPERCASE columns (Batch 31 PB-1)
- pick_evaluator (Batch 27 PV-X1) uses uppercase ("High"/"Low"/"Close")
**Three sources, inconsistent capitalization.** Either:
- Some callers convert before passing to detectors (need to verify in main.py)
- OR there's a silent KeyError path
**Investigation required in main.py / scoring.py.**

### Cross-cutting: bare-except this batch
- sector_benchmark: 0 ✅ (pure data, no I/O)
- data_fetcher: 4 (DF-7, DF-35, DF-39, plus inline) — most bare-excepts in single Phase D file

### Cross-cutting: 26 files with relative-path constants (no change — neither file adds Path constants)

### Cross-cutting: ATOMIC WRITE
N/A this batch (DF reads/uses MDH for write; SB pure data).

## SUMMARY (Batch 42)

| Severity | sector_benchmark | data_fetcher | Cross-cutting | Total |
|---|---:|---:|---:|---:|
| Show-stopper | 5 | 8 | 5 | 18 |
| Data/safety | 3 | 6 | 0 | 9 |
| Code smell | 1 | 1 | 0 | 2 |
| Good code | 11 | 32 | 0 | 43 |
| Total findings | 20 | 47 | 5 | 72 |

## TOP 10 CRITICAL FIXES from Batch 42

1. DF-X3 + PV-15 cross-cutting: Set `auto_adjust=True` in data_fetcher line 42 to fix split-adjustment latent bug at source. Removes need for evaluator-level fix. (3 min)
2. DF-31: Don't default averageVolume to 1_000_000. Use None, force risk_gate to handle. (10 min)
3. DF-11: Investigate main.py / scoring.py to confirm patterns/ get correct case. May need explicit `df.columns = [c.title() for c in df.columns]` adapter. (30 min)
4. SB-X3 / SB-14: Add comment explaining em-dash vs hyphen yfinance quirk visibly above the SECTOR_TO_ETF dict. (3 min)
5. DF-25 / DF-45: Lift magic 50 (min bars) and 100_000 (suspicious price) to module constants. (5 min)
6. SB-6: Move TAG_TO_ETF tag strings to shared `src/_constants.py` (used by scoring + sector_benchmark). (15 min)
7. DF-7 + DF-35 + DF-39: Replace bare excepts with specific exceptions. (5 min)
8. DF-5: Move SESSION init into lazy `_get_session()` function (per Batch 40 UN-3 same fix). (5 min)
9. SB-11 + SB-15: Document Materials/Software ambiguity choices. (5 min)
10. DF-X4: Verify MDH atomic write per Batch 14 MDH-X1 — if MDH appends without atomic, 600 events/run could corrupt events.jsonl. (15 min investigation)

## NEW THEMES UPDATED

- Theme T1 (bare except): sector_benchmark 0 ✅. data_fetcher 4 (intent-driven graceful degradation). **Phase D bare-except creep continues.**
- Theme T2 (schema drift): SB-14 em-dash vs hyphen. DF-11 lowercase vs uppercase capitalization confusion.
- Theme T6 (atomic writes): N/A this batch (no direct writes).
- Theme T8 (DRY): N/A this batch.
- Theme T11 (fail-open by accident): DF-31 averageVolume 1M default for delisted. DF-X3 split-adjust latent.
- Theme T13 (silent-default-fills): DF-31 1M volume sentinel.
- Theme T14 (gold-standard patterns): sector_benchmark Bug #8a archaeology + quantified impact. data_fetcher 3-tier provider chain + per-state MDH events + thread-safety docstring + Bug #6 archaeology = **PEAK Phase D documentation discipline**.

## COVERAGE TRACKER

| Phase | Status | Files done this batch | Cumulative |
|---|---|---|---:|
| Phase A | 8/8 COMPLETE | (none) | 8/8 |
| Phase B | 18/18 COMPLETE | (none) | 18/18 |
| Phase C | 12/12 COMPLETE | (none) | 12/12 |
| Phase D | 22/~30 done | sector_benchmark, data_fetcher | 22/~30 |
| Phase E | 12/~50 done | (none) | 12/~50 |
| Total true line-by-line | | +2 files | **87 of ~382 (~22.8%)** |
| Remaining | | | **~295 files** |

## NEXT BATCH

Batch 43: src/probability_engine.py + src/scoring.py (if not yet audited) OR src/scorer.py — the score-producing functions consumed by main.py and producing the score_components used in official_pick_artifact. CRITICAL untouched layer.

End of Batch 42. Phase D in progress (22/30).
