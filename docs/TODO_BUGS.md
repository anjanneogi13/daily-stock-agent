
## company-name writer falls back to ticker (Bug #6, found 2026-05-05)

**Severity:** Low (UX cosmetic)
**File:** wherever `picks_log.csv` is written (likely `src/pick_logger.py`)
**Symptom:** When yfinance/upstream company-name lookup fails, the writer
stores the ticker as the company name (NVDA company="NVDA"). Translator
detects this and falls back to ticker-only display. User sees "NVDA"
instead of "NVDA (NVIDIA Corporation)".
**Fix idea:** Writer should store empty string when lookup fails, NOT
echo the ticker. Translator logic stays unchanged (already handles empty).
**Effort:** 15 min. Do AFTER intraday→CSV write architecture (Step 4).

## Bug #7 — Day-trades picked on non-trading days (filed 2026-05-05)
MPWR was logged as `trade_type=day` on 2026-05-02 (a Saturday). Day
trades on weekends/holidays make no sense — they cannot execute on
pick_date. Likely the scanner ran (or backfilled) on a non-market day
without guarding `trade_type=day` selection.

**Symptoms:** day picks on Sat/Sun, holidays, evenings.
**Likely culprit:** scanner / picks generator. Investigate:
- `scripts/morning_brain.py` or whatever produces day-trade tags
- Should reject `trade_type=day` if today is not a US trading day
- OR convert the pick to `trade_type=swing` automatically with note

**Workaround in place (Bug #5 fix):** evaluator now uses next trading
bar at-or-after pick_date, so weekend day-picks still get closed
correctly. But the upstream UX is wrong — user receives a "day-trade"
alert that's actually a swing.

**Severity:** Low (cosmetic/UX, not data corruption — eval is correct)
**Test:** `test_day_pick_on_weekend_uses_next_trading_bar` guards eval
                                          robustness regardless.

## Bug #8 — `sector_close` never populated at pick time (CRITICAL, filed 2026-05-05)
`src/pick_logger.py:149` writes `p.get("sector_close", "")` but NOTHING
upstream ever produces `sector_close`. Result: 0% fill on closed picks.
Cascades to kill `sector_close_at_exit`, `sector_return_pct`,
`sector_alpha_pct` — the entire sector-relative-performance pipeline.

**Impact on brain:** Zero sector-alpha learning. Brain cannot
distinguish "good pick in a hot sector" from "good pick on its own
merit". Sector-rotation strategy is invisible.

**Fix path:** In whatever produces the pick dict (likely
`scripts/morning_brain.py` or `src/parallel_scorer.py`), look up the
sector ETF Close at pick time using `_etf_close_on(etf, pick_date)`
already present in `pick_evaluator.py` — refactor to a shared helper.

**Severity:** CRITICAL — unlocks 4 dead columns at once.

## Bug #9 — `alpha_pct` not backfilled for pre-May-1 picks (HIGH, filed 2026-05-05)
The `_add_spy_alpha` calculator was added 2026-05-01. 9 closed picks
from 2026-04-28 → 2026-04-29 have `spy_close` populated but BLANK
`spy_close_at_exit` / `alpha_pct`. Easy backfill via existing
`_spy_close_on()`.

**Impact:** Lost SPY-relative learning data for 9 picks.
**Fix:** One-shot backfill script. ~30 min.

## Bug #10 — `sector_etf` populated only 8.3% (MEDIUM, filed 2026-05-05)
Same root cause as #8 (sector lookup not happening at pick time).
Likely auto-resolves when #8 is fixed. Verify post-#8.

## Bug #11 — `days_to_earnings` populated only 33% (MEDIUM, filed 2026-05-05)
Earnings proximity is the single highest-alpha known signal in equities
(post-earnings drift, pre-earnings vol crush). Currently captured 1/3
of the time. Almost certainly silent yfinance failure.

**Fix path:** Find the writer, add error logging, retry, OR fall back
to a calendar-based approximation.

## Bug #12 — Trail-data 41% (INFORMATIONAL, filed 2026-05-05)
`original_sl`, `current_sl`, `peak_price`, `trail_active`, `current_tp`,
`tp_raises`, `sl_tightens` all 41% — feature shipped partway through
the dataset. New picks populate, old ones don't. Non-actionable.

## Bug #13 — Tiered TP system (`tp1`, `tp2`, `qty_t1-3`) 0% used (DESIGN DEBT, filed 2026-05-05)
Schema promises multi-tier exits. Code never activates them.
**Decision needed:** ship the feature or rip the columns. Half-built
features are noise in the schema and confuse downstream consumers.
