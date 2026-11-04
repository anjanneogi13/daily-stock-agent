# Watch-Only Outcome Report

Monitoring-only evidence. Not official picks. Not buy instructions. Not paper trading.

- Date: **2026-11-04**
- Outcomes: **2**
- Evaluated: **2**
- Average end-of-window return: **-0.7214**
- Official pick stats mutated: **false**
- Paper trading enabled: **false**
- Live trading enabled: **false**

## Status Counts
- timeout: **2**

## Outcomes
- CRWD (opening_range_watch_only): status=**timeout**, tp_hit=**false**, sl_hit=**false**, which_hit_first=**neither**, mfe=**2.4415**, mae=**-3.0906**, end_return=**-1.5916**, data=**bar_sequence_available**
  - OR quality=**failed_retest_or_range_reentry**, quality_score=**25**, sustained=**false**, false_breakout=**true**, volume=**neutral**, time=**opening_30m**, flags=**watch_only_opening_range_quality, retested_or_high_or_failed_inside_range**
- TSLA (opening_range_watch_only): status=**timeout**, tp_hit=**false**, sl_hit=**false**, which_hit_first=**neither**, mfe=**0.893**, mae=**-1.9585**, end_return=**0.1488**, data=**bar_sequence_available**
  - OR quality=**failed_retest_or_range_reentry**, quality_score=**40**, sustained=**true**, false_breakout=**true**, volume=**weak**, time=**morning_followthrough**, flags=**watch_only_opening_range_quality, retested_or_high_or_failed_inside_range, end_of_window_above_opening_range_high, volume_weak**

## Safety

- This artifact is watch-only evidence.
- It must not be mixed with official pick performance.
- It did not write `data/picks_log.csv`.
- It did not write `data/signal_journal.jsonl`.
- It did not write `data/learning_journal.jsonl`.
- It did not create paper trades.
- It did not enable live trading.

