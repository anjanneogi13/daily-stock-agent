# Audit — `src/auto_pause.py`
**LOC:** 183 | **Wired in:** ⚠️ Observe-mode (does NOT actually pause as of audit date) | **Tests:** `tests/test_auto_pause.py` (good)  
**Suggestion-only context:** Currently safe — never blocks anything because `_is_enforced()` defaults False.

## Findings

### F5-1 — L25-31 `_is_enforced()` reads `config/auto_pause.json`
- **Behavior:** Returns False unless config flag is explicitly set.
- **Status:** Per docstring, "Manual flip from observe → enforce planned for Wed 2026-05-06."
- **Verdict:** ✅ **KEEP** — current state is safe.

### F5-2 — L154 `would_pause = score >= 8`
- **Behavior:** Reports what would happen if enforced.
- **Verdict:** ✅ **KEEP** — observable, no side effect.

### F5-3 — `compute_score` uses `_load_closed()` which reads `picks_log.csv` filtered by `evaluation_status in CLOSED`
- **Behavior:** With the brain-loop currently broken (no closed trades), this returns empty → score=0 → no pause signal.
- **Verdict:** ✅ **KEEP** — irrelevant until force-close runs (PR-A4 unjams the brain loop).

## Critical: do NOT enable enforcement until brain loop is fixed
If enforcement is flipped on while picks_log has only stale "pending" rows and no closed trades, the score = 0 and nothing happens. Safe.

But if enforcement is flipped on AFTER force-close populates the journal with synthetic max_hold_force_close losses, the agent could auto-pause itself. **Add a guard: don't count `max_hold_force_close` as a real loss in the pause score.**

## Summary
- LOOSEN: 0 right now
- KEEP: 3 (file is correctly observe-mode)
- ACTION: Add brain-loop-aware filter when enforcement is enabled (post-PR-A4).
