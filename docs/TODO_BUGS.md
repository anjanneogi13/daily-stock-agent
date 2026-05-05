
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
