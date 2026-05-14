# Audit — `src/auto_cooldown.py`
**LOC:** 137 | **Wired in:** ⚠️ Reads `signal_journal.load_closed()` (currently empty due to brain loop break) | **Tests:** `tests/test_auto_cooldown.py`  
**Suggestion-only context:** Adds tickers to wisdom kill-list — which DOES block them in `wisdom_consultant`. Real effect.

## Findings

### F6-1 — L20 `CONSECUTIVE_LOSS_THRESHOLD = 3`
- **Behavior:** 3 consecutive losses on a ticker → 14-day kill.
- **Risk:** With brain loop broken, no losses recorded → no cooldowns triggered. But once force-close runs (PR-A4), every overdue swing becomes a synthetic loss. Could mass-kill 9+ tickers all at once on day 1.
- **Verdict:** 🔴 **LOOSEN**
- **Fix:** Filter `closed` to exclude `outcome == "max_hold_force_close"` events. Only real-stop-hit and real-target-hit should count.

### F6-2 — L58-104 `scan_and_cool(apply=False)`
- **Behavior:** Defaults to dry-run.
- **Verdict:** ✅ **KEEP**

### F6-3 — L82-91 `wisdom_base.add_to_kill_list(...)` — IRREVERSIBLE
- **Code:** Once added, stays for `cool_off_days=14` days.
- **Risk:** No "remove early" mechanism if a wrongly-cooled ticker has news/catalyst.
- **Verdict:** ✅ **KEEP** but add `--force-uncool TICKER` admin command (out of scope here).

## Summary
- LOOSEN: 1 (F6-1 — exclude force-close losses from cooldown signal)
- KEEP: 2 (F6-2, F6-3)
- ACTION: Apply F6-1 fix BEFORE PR-A4 ships (otherwise day-1 mass cooldown).
