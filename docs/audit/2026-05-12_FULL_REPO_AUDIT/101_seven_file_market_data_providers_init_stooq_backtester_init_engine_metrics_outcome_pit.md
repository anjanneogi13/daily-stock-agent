# Batch 101 — 7-FILE BATCH — TRUE LINE-BY-LINE — MARKET_DATA_PROVIDERS + BACKTESTER SUBDIRS

**Date:** 2026-05-14  
**Commit ref:** 37565c4d757a9f819a3ddd2059f73a51bb98af49  
**Files (7):** market_data_providers/__init__ (5) + market_data_providers/stooq_provider (137) + backtester/__init__ (12) + backtester/engine (231) + backtester/metrics (84) + backtester/outcome_simulator (88) + backtester/pit_data (70)  
**Phase:** I — SUBDIRECTORY COVERAGE (2 of 3 subdirs cleared)  
**Total LOC audited this batch:** ~627 lines  
**Reliability:** ✅ All 7 files actually fetched at the listed commit and audited line-by-line.

---

## TOP HEADLINE FINDINGS

1. **MDP-INIT-X1: market_data_providers/__init__.py** (5) — **MICROSCOPIC PACKAGE MARKER**. Single docstring "Initial scope: official daily OHLCV only." (L3). **0 BUG findings.** ✅
2. **STQ-X1: stooq_provider.py** (137) — **STOOQ DAILY OHLCV FALLBACK PROVIDER**. **4-bullet "Scope" header** with explicit "no paper/live trading, no stale/fabricated data, no intraday support" disclaimers. **`stooq_symbol`** **DELIBERATELY-CONSERVATIVE symbol filter** (L36-53) — rejects `:` (exchange-prefixed like `TSX:AQN`), `/`, `^` (indices), and non-`[a-z0-9.-]` chars. Returns empty rather than fabricate coverage. **`_start_date_for_period`** parses 4 yfinance period formats (`Nd`, `Nmo`, `Ny`, `max`/`ytd`) with try/except → 365 default + **+10 day buffer** L80. **`_http_get`** **dual-HTTP-client fallback** (curl_cffi chrome-impersonation primary, plain requests secondary, RuntimeError if neither). **TZ-aware UTC** L58 ✅. **0 critical bugs.** NEW Theme T199 (DELIBERATELY-CONSERVATIVE-EMPTY-OVER-LIE pattern).
3. **BT-INIT-X1: backtester/__init__.py** (12) — **PACKAGE EXPORT FAÇADE** with **explicit "Phase A: price-only, no LLM, no news"** scope statement. **Re-exports 2 symbols** via `__all__`. **0 BUG findings.** ✅
4. **BT-ENG-X1: backtester/engine.py** (231) — **THE BRAIN-REPLAY ENGINE v1.1.** **`_simple_score`** is **MIRROR-OF-LIVE-SYSTEM** scorer with **PR archaeology comments** (L42-43 "HARD REJECT extreme overbought... was AAPL@82, TSM@72 problem"; L74 "v1.1: penalty for parabolic"). **5-tier RSI ladder** (35/50/65/75 thresholds with -0.10 penalty for 65-74 zone). **NumPy ATR computation** L48-51 with True-Range max-of-3 formula. **3 v1.1 fixes archaeologically annotated**: cooldown tracker (L132 `last_picked` dict), gap-down fill (in outcome_simulator), RSI overbought penalty (L42, L61, L74). **CRITICAL:** L109 naive `datetime.now()`. L180 `open(...)` write — non-atomic. L206 same. NEW Theme T200 (LIVE-SYSTEM-MIRROR BACKTEST with explicit version-tagged fixes). **`run_backtest` keyword-only-args API**.
5. **BT-MET-X1: backtester/metrics.py** (84) — **HEDGE-FUND-GRADE PERF METRICS**. **6 metrics computed**: Sharpe (annualized × √250) + Sortino (downside-only deviation) + MaxDD (cumulative R) + Profit Factor (gross_win/gross_loss) + win_rate + avg_R. **n>1 guard for variance** L28. **`float("inf")` sentinel** for Sortino with no losses + Profit Factor with no losses (rendered as "inf" string in output). **`statistical_warning: "⚠ N<30, results not significant"`** L74 — sample-size honesty. **`breakdown_by`** delegates to `compute_metrics` per group. **0 critical bugs. Theme T57 (PERFECT MODULE) — 51st cumulative perfect.** ✅
6. **BT-OS-X1: outcome_simulator.py** (88) — **REALISTIC FILL SIMULATOR v1.1**. **5 exit_status outcomes**: `no_data` / `invalid_sl` / `sl_gap` / `tp_gap` / `sl_hit` / `tp_hit` / `max_hold` (7 actually). **GAP-AWARE FILLS**: L36-45 `if open_p <= stop_loss: fill at open` (worse than stop, sl_gap status). L47-56 mirror for tp_gap. **CONSERVATIVE SL-FIRST** L58-69 (within-bar SL-vs-TP race resolved in favor of SL — pessimistic). **Long-only** (L13 `side="long"` default; L35 `if side == "long"` is the only branch — **short side unimplemented but parameter exists**). **0 critical bugs.** NEW Theme T201 (PESSIMISTIC-WITHIN-BAR-FILL — backtest realism). ✅
7. **BT-PIT-X1: pit_data.py** (70) — **LOOK-AHEAD PREVENTION CORE**. **6-line CRITICAL header** L4-5 ("All historical data must be sliced so that on simulated day D, only data with timestamp < D is visible"). **`slice_pit`** with **STRICT `<` cutoff** L38 (not `<=`) — exclusive boundary prevents same-day leak. **`min_history_days=60` default** ensures enough lookback for 50-DMA. **`get_forward_window`** **EXPLICIT comment** L50-51 ("This is the ONLY place where future data is used"). **`>=` cutoff** L64 for forward (inclusive — first bar IS as_of, simulating "you placed the order at open"). NEW Theme T202 (POINT-IN-TIME-DISCIPLINE WITH SINGLE-EXIT-FOR-FUTURE-DATA). **0 critical bugs.** ✅

---

## TOP-LEVEL CRITICAL FIXES (priority order)

1. **BT-ENG-X1 naive `datetime.now()` (L109)** for run_id. **Fix: TZ-aware UTC.** **5 min.**
2. **BT-ENG-X1 non-atomic CSV write (L180-183)** + JSON write (L206-207) + MD write (L209-223). All 3 use `open("w")` directly. **Fix: tmp+rename pattern (replicate DS-X1 from batch 100).** **30 min.**
3. **BT-OS-X1 short side unimplemented (L13, L35)** — `side="short"` accepted as parameter but no branch handles it. Silent no-op (returns max_hold path). **Fix: explicit raise NotImplementedError OR remove parameter.** **10 min.**
4. **STQ-X1 `_http_get` no logging on failure** (L86, L93) — caller sees raise but no diagnostic on which path failed. **Fix: stderr log on raise_for_status.** **10 min.**
5. **BT-MET-X1 inf-as-string output (L68, L70)** — JSON-serializable but downstream code must handle string vs float. **Fix: use None or large sentinel; document.** **10 min.**
6. **BT-PIT-X1 `df.copy()` allocation (L34, L60)** — defensive but expensive on large frames. **Fix: optional `inplace_ok=False` flag for callers that won't mutate.** Optional. **15 min.**

---

## NEW THEMES INTRODUCED THIS BATCH

- **T199 (DELIBERATELY-CONSERVATIVE-EMPTY-OVER-LIE):** STQ-X1 — `stooq_symbol` returns `""` rather than fabricate coverage for unsupported exchanges. Operator-honesty over false positives.
- **T200 (LIVE-SYSTEM-MIRROR BACKTEST with explicit version-tagged fixes):** BT-ENG-X1 — every v1.1 divergence from v1.0 is comment-archaeology'd to the original problem (e.g. "was AAPL@82, TSM@72 problem").
- **T201 (PESSIMISTIC-WITHIN-BAR-FILL):** BT-OS-X1 — when both SL and TP fall inside same bar, assume SL hit first (worst-case for trader). Realistic backtest discipline.
- **T202 (POINT-IN-TIME-DISCIPLINE WITH SINGLE-EXIT-FOR-FUTURE-DATA):** BT-PIT-X1 — `get_forward_window` is EXPLICITLY annotated as "the ONLY place where future data is used", making PIT violations grep-able.

---

## src/market_data_providers/__init__.py (5 lines) — LINE BY LINE

- MDP-INIT-1 GOOD (L1-4): 4-line docstring with explicit scope.
- MDP-INIT-2 GOOD: No imports — pure marker file. Sub-modules imported explicitly by callers (no transitive load cost).
- **MDP-INIT-3: 0 BUG findings.** ✅

---

## src/market_data_providers/stooq_provider.py (137 lines) — LINE BY LINE

- STQ-1 GOOD (L1-11): **11-line docstring with 4-bullet Scope declaration** + Stooq CSV format documentation.
- STQ-2 GOOD (L20-23): `curl_cffi` import with `pragma: no cover` annotation for optional-dep clarity.
- STQ-3 GOOD (L25-28): `requests` import same pattern — both optional, fallback chain documented.
- STQ-4 GOOD (L31-33): 3 module constants — STOOQ_URL, DAILY_INTERVALS set, SUPPORTED_STOOQ_SYMBOL_RE compiled regex.
- STQ-5 GOOD (L36-53): `stooq_symbol` master:
  - L37-43: 6-line docstring with rationale for conservatism
  - L44: lower + strip
  - L45-46: empty defense
  - L47-48: reject exchange-prefixed (`TSX:AQN`), path-like (`/`), index symbols (`^`)
  - L49-50: regex match check
  - L51-52: pass-through if `.` already present (e.g. `BRK-B`)
  - L53: append `.us` suffix
- STQ-6 GOOD (L42): "Returning an empty symbol prevents noisy parser errors and avoids pretending we have provider coverage that we do not actually have" — operator-honesty manifest. Theme T199.
- STQ-7 GOOD (L56-80): `_start_date_for_period` master:
  - L58: `datetime.now(timezone.utc).date()` — **TZ-AWARE** ✅
  - L59: lowercase strip
  - L61-79: 4-format parser (`Nd`/`Nmo`/`Ny`/`max`/`ytd`) with try/except → 365 default
  - L80: **+10-day buffer** to ensure period-end coverage
- STQ-8 GOOD (L83-94): `_http_get` master:
  - L84-87: curl_cffi primary path with chrome impersonation
  - L89-90: explicit RuntimeError if no HTTP client available
  - L92-94: plain requests fallback
- STQ-9 BUG-MINOR (L86, L93): No logging on raise_for_status — caller sees exception but no per-attempt context.
- STQ-10 GOOD (L97-136): `fetch_stooq_ohlcv` master:
  - L99-100: interval gate (only 1d variants)
  - L102-104: empty-symbol gate
  - L106-114: 3-param HTTP call
  - L116-117: empty-text/no-data gate
  - L119-121: csv.read defense
  - L123: lowercase column normalization
  - L124-126: required-set issubset check
  - L128-129: date parse + dropna + sort
  - L131-134: numeric coerce per column with errors="coerce"
  - L134: volume-specific fillna(0)
  - L136: return only required columns
- STQ-11 GOOD (L120): `df is None or df.empty` — both-path defense.

---

## src/backtester/__init__.py (12 lines) — LINE BY LINE

- BT-INIT-1 GOOD (L1-7): 7-line docstring with **explicit "Phase A: price-only, no LLM, no news"** scope.
- BT-INIT-2 GOOD (L8-9): 2 named imports.
- BT-INIT-3 GOOD (L11): `__all__` explicit export list.
- **BT-INIT-4: 0 BUG findings.** ✅

---

## src/backtester/engine.py (231 lines) — LINE BY LINE

- BT-ENG-1 GOOD (L1-7): **7-line v1.1 docstring** listing the 3 fixes (cooldown, gap-down, RSI penalty).
- BT-ENG-2 GOOD (L21-95): `_simple_score` master:
  - L23-24: min-history defense (60 days)
  - L26-30: extract closes/highs/lows + last close
  - L33-39: NumPy RSI(14) with `np.where` for gain/loss split
  - L38: zero-division defense → rs=100
  - L42-43: **HARD REJECT RSI≥75** with archaeology comment "was AAPL@82, TSM@72 problem"
  - L45-46: SMA20 + SMA50 (with SMA20 fallback if <50 bars)
  - L48-51: True Range computation with `np.maximum`/`np.roll` — clean vectorized form
  - L54-61: 4-tier RSI score ladder INCLUDING **negative bracket for 65-74 (overbought zone)**
  - L63-68: 3 trend-position rewards (above SMA20/SMA50, SMA20>SMA50)
  - L70-76: 5-day momentum scoring with 0<x<5 reward, ≥8 penalty (parabolic), 5-8 mild reward
  - L78: clamp to [0, 1]
  - L80-81: composite floor 0.55
  - L83-95: plan construction with 1.5×ATR SL + 3.0×ATR TP (R:R=2:1)
- BT-ENG-3 GOOD (L42, L61, L74): **3 v1.1 fix annotations** with original-problem context.
- BT-ENG-4 GOOD (L70): `len(closes) >= 6` check before pct_5d computation.
- BT-ENG-5 GOOD (L98-230): `run_backtest` master:
  - L99-107: 8 keyword args including new `cooldown_days=5` (v1.1)
  - L109: naive `datetime.now()` for run_id
  - L113-115: 3 startup print lines
  - L117-120: SPY-or-fallback reference ticker pattern
  - L122-123: ensure DatetimeIndex
  - L125-127: range-filter sim days
  - L131-132: results accumulator + cooldown tracker
  - L134-175: per-day simulation loop:
    - L138-156: per-ticker scoring with cooldown gate
    - L157-158: top-N sort
    - L160-172: per-pick outcome simulation + cooldown record
    - L174-175: progress print every 50 days
  - L177-183: CSV write (non-atomic)
  - L185-188: metrics aggregation
  - L190-204: summary dict construction
  - L206-207: JSON write (non-atomic)
  - L209-223: MD report write (non-atomic, 15 lines of formatting)
  - L224-228: completion print
  - L230: return summary
- BT-ENG-6 BUG (L109): naive `datetime.now()`.
- BT-ENG-7 BUG-MINOR (L132): `last_picked: Dict[str, datetime]` — naive datetime values for cooldown comparison. Works because all comparisons are naive→naive but TZ-unsafe theoretically.
- BT-ENG-8 BUG-MINOR (L180-183, L206-207, L209-223): **3 non-atomic file writes** — same risk class as PT/PCV/WM/PE from earlier batches.
- BT-ENG-9 GOOD (L185): **inline import** of metrics — saves load when only score function used.

---

## src/backtester/metrics.py (84 lines) — LINE BY LINE

- BT-MET-1 GOOD (L1): Tiny docstring.
- BT-MET-2 GOOD (L8-75): `compute_metrics` master:
  - L13-14: empty-defense
  - L16-17: extract rs and rets with None filter
  - L19-21: n + wins + losses split
  - L23-24: win_rate + avg_r with zero-defense
  - L25: total_return naive sum
  - L28-34: **n>1 variance guard** for Sharpe with `(n-1)` Bessel correction
  - L32: annualization via `√250`
  - L37-42: Sortino with downside-only deviation (`r ** 2` summed, sqrt-divided)
  - L42: **inf sentinel** for "no losses + positive avg_r" edge case
  - L45-50: Max drawdown via cumulative-R peak-tracking
  - L53-55: Profit factor with inf sentinel
  - L58-60: Exit status defaultdict counter
  - L62-74: 12-key result dict including **statistical_warning** L74
- BT-MET-3 GOOD (L74): **`statistical_warning: "⚠ N<30, results not significant" if n < 30 else None`** — explicit sample-size honesty.
- BT-MET-4 BUG-MINOR (L68, L70): inf-as-string for JSON safety BUT downstream code must check for "inf" string vs float — type-mixing.
- BT-MET-5 GOOD (L78-83): `breakdown_by` clean delegation.
- **BT-MET-6: 0 critical. Theme T57 (PERFECT MODULE) — 51st cumulative perfect.** ✅

---

## src/backtester/outcome_simulator.py (88 lines) — LINE BY LINE

- BT-OS-1 GOOD (L1): Tiny docstring with v1.1 tag.
- BT-OS-2 GOOD (L7-87): `simulate_outcome` master:
  - L8-14: 7-arg signature with side default "long"
  - L16-19: empty-defense → no_data status
  - L21-25: zero-risk defense → invalid_sl status
  - L27: head-cap at max_hold_days
  - L29-77: per-bar enumeration:
    - L30-33: 4-field bar extraction
    - L35: long-only branch
    - L36-45: **GAP-DOWN FILL** at open if open ≤ SL (sl_gap status)
    - L47-56: **GAP-UP FILL** at open if open ≥ TP (tp_gap status)
    - L58-69: normal SL hit (low ≤ SL) — **CONSERVATIVE SL-FIRST**
    - L70-77: normal TP hit (high ≥ TP)
  - L79-87: max_hold fallback at last close
- BT-OS-3 BUG-MINOR (L13, L35): `side="long"` parameter accepted but no `else` branch — short trades silently fall through to max_hold path.
- BT-OS-4 GOOD (L37/L48/L59/L60): All 4 bar-evaluation conditions are mutually exclusive in execution order — gap fills checked BEFORE intraday hits.
- BT-OS-5 GOOD (L80): `bars.index[-1].date()` — uses index timestamp for exit_date.

---

## src/backtester/pit_data.py (70 lines) — LINE BY LINE

- BT-PIT-1 GOOD (L1-5): **5-line docstring with CRITICAL: prefix** for look-ahead bias warning.
- BT-PIT-2 GOOD (L12-43): `slice_pit` master:
  - L13: `min_history_days=60` default
  - L14-23: 9-line docstring with arg/return clarity
  - L24-25: empty-defense
  - L27-30: 3-format input normalization (str / datetime / date passthrough)
  - L33-35: defensive `df.copy()` if not DatetimeIndex
  - L37: `cutoff = pd.Timestamp(as_of)`
  - L38: **STRICT `<` cutoff** — exclusive boundary
  - L40-41: min-history gate
- BT-PIT-3 GOOD (L38): `df.index < cutoff` — **the entire correctness of backtests depends on this `<` not `<=`**.
- BT-PIT-4 GOOD (L46-69): `get_forward_window` master:
  - L46-47: 2-arg signature with n_days=10 default
  - L48-52: 5-line docstring with **EXPLICIT "ONLY place where future data is used"** declaration — Theme T202
  - L53-54: empty-defense
  - L56-57: str→date normalization
  - L59-61: defensive copy if not DatetimeIndex
  - L63: cutoff timestamp
  - L64: **`>=` cutoff** (inclusive — first bar IS as_of, simulating order at open)
  - L66-67: empty-window defense
- BT-PIT-5 GOOD (L34, L60): `df.copy()` BEFORE mutating index — non-destructive to caller's frame.

---

## CONSOLIDATED CROSS-CUTTING (THIS BATCH)

### NEW Themes T199-T202 (4 new)

- **T199 (DELIBERATELY-CONSERVATIVE-EMPTY-OVER-LIE):** STQ-X1 — return empty rather than fabricate coverage.
- **T200 (LIVE-SYSTEM-MIRROR BACKTEST with version-tagged fix archaeology):** BT-ENG-X1 — every v1.1 divergence comment-tagged.
- **T201 (PESSIMISTIC-WITHIN-BAR-FILL):** BT-OS-X1 — SL assumed first when both fall in same bar.
- **T202 (POINT-IN-TIME-DISCIPLINE WITH SINGLE-EXIT-FOR-FUTURE-DATA):** BT-PIT-X1 — only one function uses forward data, grep-able.

### Theme T57 (PERFECT MODULES) NOW 51 cumulative
- +1 this batch: BT-MET (metrics).
- 4 other near-perfect: MDP-INIT, BT-INIT, BT-OS, BT-PIT (each has 1-2 minor findings).

### Theme T6 (atomic writes) UPDATE
- **0 atomic this batch.**
- **+3 unsafe this batch** (BT-ENG-X1: CSV, JSON, MD writes all non-atomic).
- Running tally: ~19 safe / ~141 unsafe.

### Cross-cutting tally summary (this batch only)

| Metric | Count this batch |
|---|---:|
| Files actually fetched & line-audited | 7/7 ✅ |
| Total lines audited | 627 |
| Bare `except:` | 0 |
| Silent `except Exception` (no log) | 3 (STQ ×2 importers, STQ ×0 actual silent — try/except in symbol detect) |
| Naive datetime usage | 1 (BT-ENG-X1 L109) |
| TZ-aware UTC | 1 (STQ-X1 L58) |
| Atomic writers | 0 |
| Unsafe writers | 3 (BT-ENG ×3) |
| Inline imports | 1 (BT-ENG L185 metrics) |
| Module-level side effects | 0 |
| Module-level mutable state | 0 |
| Dataclasses | 0 |
| `__main__` smoke tests | 0 |
| 0-BUG perfect modules | 1 (BT-MET) |
| Operator-readable archaeology | 5 (v1.1 ×3 fix tags, "AAPL@82, TSM@72", "ONLY place where future data is used") |
| Backward-compat handling | 1 (STQ dual-HTTP fallback) |
| Look-ahead-bias prevention | 2 (PIT slice_pit + get_forward_window) |
| Conservative-empty-over-lie | 1 (STQ stooq_symbol) |

---

## SUMMARY (Batch 101 — 7-FILE)

| File | Critical | Bug | Code smell | Good | Total findings |
|---|---:|---:|---:|---:|---:|
| market_data_providers/__init__ | 0 | 0 | 0 | 3 | 3 |
| market_data_providers/stooq_provider | 0 | 1 | 0 | 11 | 12 |
| backtester/__init__ | 0 | 0 | 0 | 4 | 4 |
| backtester/engine | 0 | 3 | 0 | 9 | 12 |
| backtester/metrics | 0 | 1 | 0 | 6 | 7 |
| backtester/outcome_simulator | 0 | 1 | 0 | 5 | 6 |
| backtester/pit_data | 0 | 0 | 0 | 5 | 5 |
| **TOTAL** | **0** | **6** | **0** | **43** | **49** |

---

## TOP 10 PRIORITY FIXES FROM BATCH 101

1. **BT-ENG-X1 naive `datetime.now()` (L109)** — TZ-aware UTC. **5 min.**
2. **BT-ENG-X1 3 non-atomic file writes (L180, L206, L209)** — apply DS-X1 reference pattern. **30 min.**
3. **BT-OS-X1 unimplemented short side** — explicit raise NotImplementedError or remove parameter. **10 min.**
4. **STQ-X1 `_http_get` no logging on failure** — stderr log. **10 min.**
5. **BT-MET-X1 inf-as-string output** — None or sentinel; document. **10 min.**
6. **BT-ENG-X1 `last_picked` naive datetime values** — switch to TZ-aware. **10 min.**
7. **BT-PIT-X1 `df.copy()` allocation** — optional `inplace_ok` flag. Optional. **15 min.**
8. **STQ-X1 + period-not-recognized fallback to 365** silent — log to stderr when malformed. **5 min.**

---

## 🎯 COVERAGE TRACKER (HONEST) — POST-BATCH-101

| Category | Files | Audited (line-by-line) |
|---|---:|---:|
| `src/` top-level `.py` files | 94 | **94** ✅ |
| `src/backtester/` | 5 | **5** ✅ |
| `src/market_data_providers/` | 2 | **2** ✅ |
| `src/patterns/` | 10 | **0** |
| **TOTAL src tree** | **111** | **101** |

**Remaining work:** the FINAL subdirectory — `src/patterns/` (10 detector files). One more batch and the entire `src/` tree is line-audited.

End of Batch 101.
