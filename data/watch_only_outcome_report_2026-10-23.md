# Watch-Only Outcome Report

Monitoring-only evidence. Not official picks. Not buy instructions. Not paper trading.

- Date: **2026-10-23**
- Outcomes: **2**
- Evaluated: **2**
- Average end-of-window return: **-0.934**
- Official pick stats mutated: **false**
- Paper trading enabled: **false**
- Live trading enabled: **false**

## Status Counts
- timeout: **2**

## Outcomes
- QQQ (opening_range_watch_only): status=**timeout**, tp_hit=**false**, sl_hit=**false**, which_hit_first=**neither**, mfe=**0.0911**, mae=**-0.4949**, end_return=**-0.4554**, data=**bar_sequence_available**
  - OR quality=**sustained_breakout_no_target_yet**, quality_score=**65**, sustained=**true**, false_breakout=**false**, volume=**confirmed**, time=**late_morning**, flags=**watch_only_opening_range_quality, overextended_at_observation, end_of_window_above_opening_range_high, volume_confirmed**
- AVGO (opening_range_watch_only): status=**timeout**, tp_hit=**false**, sl_hit=**false**, which_hit_first=**neither**, mfe=**0.1103**, mae=**-1.523**, end_return=**-1.4126**, data=**bar_sequence_available**
  - OR quality=**failed_retest_or_range_reentry**, quality_score=**20**, sustained=**false**, false_breakout=**true**, volume=**weak**, time=**midday**, flags=**watch_only_opening_range_quality, retested_or_high_or_failed_inside_range, volume_weak**

## Safety

- This artifact is watch-only evidence.
- It must not be mixed with official pick performance.
- It did not write `data/picks_log.csv`.
- It did not write `data/signal_journal.jsonl`.
- It did not write `data/learning_journal.jsonl`.
- It did not create paper trades.
- It did not enable live trading.

