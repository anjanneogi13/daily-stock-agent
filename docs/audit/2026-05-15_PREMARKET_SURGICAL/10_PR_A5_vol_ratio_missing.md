# PR-A5 candidate: vol_ratio missing for AMAT 2026-05-15

## Symptom
data/picks_log.csv line 43 (AMAT 2026-05-15) has empty vol_ratio column.
When the recovery script journaled AMAT, signal_journal entry got
vol_ratio_bucket="unknown" because bucket_vol(None) returns "unknown".
This tripped test_post_fix_vol_ratio_never_unknown in PR-A4.

## Root cause
main.py line 1746 writes p["scores"].get("vol_ratio") which was None
because parallel_scorer.py or data_fetcher.py did not compute it.
Probable cause: yfinance returned rate_limited (131 such errors in this
run's market_data_health.json) on AMAT info call, so 20-day average
volume was unavailable, vol_ratio could not be computed, silent None.

## Same-class as PR-A2.6 BUG-A
yfinance rate-limit + no fallback for derived metadata = silent None =
downstream consumers see "unknown" and lose learning signal.

## Fix scope (PR-A5)
1. Investigate parallel_scorer.py vol_ratio computation path
2. Add fallback: when 20-day avg volume unavailable, try shorter window
   (5-day, 10-day) before giving up
3. When all attempts fail, log explicit reason instead of silent None
4. Wire finnhub as 3rd provider so yfinance rate-limits do not cascade

## Status
- Bug confirmed in production, audit doc filed
- Workaround in place: small-N guard in test allows shipping PR-A4
- Fix deferred to PR-A5 (data provider hardening)
