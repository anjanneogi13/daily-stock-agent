# Watch-Only Outcome Report

Monitoring-only evidence. Not official picks. Not buy instructions. Not paper trading.

- Date: **2026-11-09**
- Outcomes: **2**
- Evaluated: **2**
- Average end-of-window return: **0.3559**
- Official pick stats mutated: **false**
- Paper trading enabled: **false**
- Live trading enabled: **false**

## Status Counts
- timeout: **2**

## Outcomes
- QQQ (opening_range_watch_only): status=**timeout**, tp_hit=**false**, sl_hit=**false**, which_hit_first=**neither**, mfe=**0.7635**, mae=**-0.0857**, end_return=**0.3296**, data=**bar_sequence_available**
  - OR quality=**sustained_breakout_no_target_yet**, quality_score=**65**, sustained=**true**, false_breakout=**false**, volume=**weak**, time=**midday**, flags=**watch_only_opening_range_quality, end_of_window_above_opening_range_high, volume_weak**
- NVDA (opening_range_watch_only): status=**timeout**, tp_hit=**false**, sl_hit=**false**, which_hit_first=**neither**, mfe=**0.6885**, mae=**-1.2421**, end_return=**0.3822**, data=**bar_sequence_available**
  - OR quality=**failed_retest_or_range_reentry**, quality_score=**40**, sustained=**true**, false_breakout=**true**, volume=**weak**, time=**midday**, flags=**watch_only_opening_range_quality, retested_or_high_or_failed_inside_range, end_of_window_above_opening_range_high, volume_weak**

## Safety

- This artifact is watch-only evidence.
- It must not be mixed with official pick performance.
- It did not write `data/picks_log.csv`.
- It did not write `data/signal_journal.jsonl`.
- It did not write `data/learning_journal.jsonl`.
- It did not create paper trades.
- It did not enable live trading.

