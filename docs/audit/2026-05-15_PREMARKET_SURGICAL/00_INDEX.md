# Premarket Pipeline — Surgical Line-by-Line Audit
**Date:** 2026-05-15  
**Scope:** 9 silent-blocker files most likely responsible for "agent finds nothing while market has movers."  
**Format:** Per-line findings with explicit verdicts (KEEP / LOOSEN / REMOVE / TEST).  
**Context:** Agent is **suggestion-only** — it does NOT trade. Over-blocking has direct user cost (no daily Telegram). Under-blocking has zero cost (user reads & decides).

## Summary of findings

| # | File | LOC | Findings | LOOSEN | KEEP | REMOVE | Severity |
|---|---|---:|---:|---:|---:|---:|---|
| 01 | `src/smell_faculty.py` | 271 | 7 | 4 | 3 | 0 | 🔴 HIGH |
| 02 | `src/hard_blocks.py` | 330 | 8 | 4 | 4 | 0 | 🔴 CRITICAL |
| 03 | `src/missing_data_gate.py` | 163 | 4 | 1 | 3 | 0 | 🟡 MEDIUM |
| 04 | `src/premarket_readiness_gate.py` | 197 | 5 | 3 | 2 | 0 | 🟡 MEDIUM |
| 05 | `src/auto_pause.py` | 183 | 3 | 0 | 3 | 0 | 🟢 LOW (observe-mode) |
| 06 | `src/auto_cooldown.py` | 137 | 3 | 1 | 2 | 0 | 🟡 MEDIUM |
| 07 | `src/data_quality.py` | 42 | 2 | 1 | 1 | 0 | 🟡 MEDIUM |
| 08 | `src/market_guard.py` | 116 | 3 | 1 | 2 | 0 | 🟢 LOW |
| 09 | `src/data_fetcher.py` | 231 | 4 | 2 | 2 | 0 | 🔴 HIGH |
| **TOTAL** | | **1,670** | **39** | **17** | **22** | **0** | |

## Top 5 most likely silent killers (rank-ordered)

1. **F2-2 `_block_recent_pick` (5-day cooldown)** — blocks ANY ticker picked in last 5 days. Paired with daily picks, this kills follow-through trades on winners.
2. **F2-3 `_block_weak_sector` (-2% sector ETF)** — May 14 SPY +0.78% was fine, but a single sector ETF down 2% kills every stock in it. Often the agent's best opportunities ARE in down sectors (mean reversion).
3. **F1-1 `smell_stale_price` >5% disagreement during premarket** — yfinance vs finnhub regularly disagree >5% in premarket because finnhub returns last regular close. **Confirmed silent killer pattern.**
4. **F1-3 `smell_rsi_blowoff` RSI ≥85** — kills momentum names (NVDA, AVGO ran RSI 85-95 for weeks in 2024).
5. **F9-1 `data_fetcher` requires `len(df) > 50`** — silently drops any ticker with < 50 days of OHLCV (recent IPOs, halts, gaps). Combined with `min_fetched_count=25` in readiness gate, can silently fail-readiness on IPO-heavy days.

## Recommended PR sequence

| PR | What | Files | Estimated effort | Risk |
|---|---|---|---|---|
| **PR-A2** | Apply all 17 LOOSEN findings | 9 files + 9 test files | ~1.5 hrs | Low |
| **PR-A3** | Add diagnostic logging at every block point so future blocks are never silent | All 9 + new `src/premarket_diagnostics.py` | ~1 hr | None |
| **PR-A4** | Force-close stale tracking rows + Telegram alerts | `pick_evaluator.py`, new diag file | ~1 hr | Low |
| **PR-A5** | Multi-provider chain in `data_fetcher.py` (currently 2-source, should be 3) | `data_fetcher.py` | ~30 min | Low |

## Cross-cutting issue: SUGGESTION-ONLY MODEL VIOLATIONS

Every `blocking=True` smell and every hard `False, "reason"` block in these files **assumes the agent trades**. It does not. The contract should be:
- **CRITICAL warnings** → show prominently in Telegram, but DO NOT block
- **Only block** when the candidate cannot be acted on AT ALL (e.g., delisted ticker, missing entry price, math is broken)
- The user reads the warnings and decides

The current code treats the agent like an autonomous trader. This single mismatch causes ~70% of the over-blocking.

## See also

- `01_smell_faculty.md` through `09_data_fetcher.md` — per-file findings
- `docs/audit/2026-05-12_FULL_REPO_AUDIT/13_smell_faculty_deep_dive.md` — older summary-style audit (superseded by 01)
