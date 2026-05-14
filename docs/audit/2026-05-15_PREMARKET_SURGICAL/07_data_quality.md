# Audit — `src/data_quality.py`
**LOC:** 42 | **Wired in:** Used by analysis/learning code (NOT premarket pick selection) | **Tests:** thin  
**Suggestion-only context:** Filters HISTORICAL data for backtest/learning. Does NOT affect today's premarket pick directly.

## Findings

### F7-1 — L22 `DATA_QUALITY_FLOOR = date(2026, 5, 2)`
- **Behavior:** Excludes all picks dated before May 2, 2026 from analysis.
- **Risk:** Hardcoded date. Today is May 14 → only 12 days of usable history → tiny sample for calibration/learning.
- **Verdict:** 🔴 **LOOSEN** (long-term)
- **Fix:** When new safety gates are added, BUMP the floor. When old gates are loosened (this PR series), CONSIDER if old picks become valid again. For now, keep date but document next review = +90 days.

### F7-2 — L25-36 `is_above_floor` — defaults False on parse error
- **Behavior:** Conservative.
- **Verdict:** ✅ **KEEP**

## Summary
- LOOSEN: 1 (F7-1 — process for updating floor)
- KEEP: 1 (F7-2)
- IMPACT: Indirect. Affects how the brain learns, not whether the agent picks.
