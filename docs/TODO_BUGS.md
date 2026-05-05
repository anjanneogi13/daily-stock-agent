
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
