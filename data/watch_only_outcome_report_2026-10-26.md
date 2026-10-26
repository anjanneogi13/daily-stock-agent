# Watch-Only Outcome Report

Monitoring-only evidence. Not official picks. Not buy instructions. Not paper trading.

- Date: **2026-10-26**
- Outcomes: **3**
- Evaluated: **3**
- Average end-of-window return: **0.0002**
- Official pick stats mutated: **false**
- Paper trading enabled: **false**
- Live trading enabled: **false**

## Status Counts
- timeout: **3**

## Outcomes
- QQQ (opening_range_watch_only): status=**timeout**, tp_hit=**false**, sl_hit=**false**, which_hit_first=**neither**, mfe=**0.6544**, mae=**0.0218**, end_return=**0.4165**, data=**bar_sequence_available**
  - OR quality=**sustained_breakout_no_target_yet**, quality_score=**75**, sustained=**true**, false_breakout=**false**, volume=**confirmed**, time=**morning_followthrough**, flags=**watch_only_opening_range_quality, end_of_window_above_opening_range_high, volume_confirmed**
- TSLA (opening_range_watch_only): status=**timeout**, tp_hit=**false**, sl_hit=**false**, which_hit_first=**neither**, mfe=**0.4628**, mae=**-0.5538**, end_return=**-0.5269**, data=**bar_sequence_available**
  - OR quality=**failed_retest_or_range_reentry**, quality_score=**20**, sustained=**false**, false_breakout=**true**, volume=**weak**, time=**late_morning**, flags=**watch_only_opening_range_quality, retested_or_high_or_failed_inside_range, volume_weak**
- NVDA (opening_range_watch_only): status=**timeout**, tp_hit=**false**, sl_hit=**false**, which_hit_first=**neither**, mfe=**0.2915**, mae=**-0.546**, end_return=**0.111**, data=**bar_sequence_available**
  - OR quality=**failed_retest_or_range_reentry**, quality_score=**40**, sustained=**true**, false_breakout=**true**, volume=**weak**, time=**late_morning**, flags=**watch_only_opening_range_quality, retested_or_high_or_failed_inside_range, end_of_window_above_opening_range_high, volume_weak**

## Safety

- This artifact is watch-only evidence.
- It must not be mixed with official pick performance.
- It did not write `data/picks_log.csv`.
- It did not write `data/signal_journal.jsonl`.
- It did not write `data/learning_journal.jsonl`.
- It did not create paper trades.
- It did not enable live trading.

