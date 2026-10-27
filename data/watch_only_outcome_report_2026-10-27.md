# Watch-Only Outcome Report

Monitoring-only evidence. Not official picks. Not buy instructions. Not paper trading.

- Date: **2026-10-27**
- Outcomes: **3**
- Evaluated: **3**
- Average end-of-window return: **-0.3424**
- Official pick stats mutated: **false**
- Paper trading enabled: **false**
- Live trading enabled: **false**

## Status Counts
- sl_hit: **1**
- timeout: **2**

## Outcomes
- DE (opening_range_watch_only): status=**sl_hit**, tp_hit=**false**, sl_hit=**true**, which_hit_first=**sl**, mfe=**-0.0107**, mae=**-2.457**, end_return=**-1.614**, data=**bar_sequence_available**
  - OR quality=**false_breakout_stop_hit**, quality_score=**10**, sustained=**false**, false_breakout=**true**, volume=**confirmed**, time=**opening_30m**, flags=**watch_only_opening_range_quality, retested_or_high_or_failed_inside_range, stop_hit_before_target, volume_confirmed**
- QQQ (opening_range_watch_only): status=**timeout**, tp_hit=**false**, sl_hit=**false**, which_hit_first=**neither**, mfe=**0.4726**, mae=**-0.0793**, end_return=**0.2697**, data=**bar_sequence_available**
  - OR quality=**sustained_breakout_no_target_yet**, quality_score=**75**, sustained=**true**, false_breakout=**false**, volume=**confirmed**, time=**late_morning**, flags=**watch_only_opening_range_quality, end_of_window_above_opening_range_high, volume_confirmed**
- XLK (opening_range_watch_only): status=**timeout**, tp_hit=**false**, sl_hit=**false**, which_hit_first=**neither**, mfe=**0.4757**, mae=**-0.0317**, end_return=**0.3171**, data=**bar_sequence_available**
  - OR quality=**sustained_breakout_no_target_yet**, quality_score=**65**, sustained=**true**, false_breakout=**false**, volume=**weak**, time=**late_morning**, flags=**watch_only_opening_range_quality, end_of_window_above_opening_range_high, volume_weak**

## Safety

- This artifact is watch-only evidence.
- It must not be mixed with official pick performance.
- It did not write `data/picks_log.csv`.
- It did not write `data/signal_journal.jsonl`.
- It did not write `data/learning_journal.jsonl`.
- It did not create paper trades.
- It did not enable live trading.

