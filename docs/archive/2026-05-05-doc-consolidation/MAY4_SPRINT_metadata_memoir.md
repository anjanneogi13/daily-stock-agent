# Sprint: 2026-05-04 — Metadata Fix + Agent Memoir

**Trigger:** Founder read first weekly hypothesis report on Telegram (2026-05-03).

## What the report revealed

- 9 closed picks, base win-rate 11.1%
- 0 edges + 0 drags found
- ALL 9 picks tagged as "unknown" across composite_score, regime, vol_ratio, monster_score, brain_p_win
- False alarm: "No brain mutations in last 14d" (system was 1 day old)

## Root cause

Field-name mismatch in `src/signal_journal.py build_signals()`:
- Looked for `scores.get("composite")`
- Real field name is `score` (top-level)
- Same issue for vol_ratio, monster_score, p_win
- Result: every pick looked identical to the brain → couldn't learn anything

## Fixes shipped (5 changes)

1. **Defensive build_signals()** — tries multiple field aliases per signal
2. **Age-aware stuck detection** — requires system_age_days >= stuck_days
3. **NEW src/agent_memoir.py** — narrated self-portrait written nightly
4. **Wired memoir as Step 8** in nightly_conductor
5. **Test updated 7 -> 8 steps** for new pipeline

## Verification (before commit)

| Check | Result |
|---|---|
| Syntax all 4 files | 4/4 valid |
| build_signals smoke test | composite='high' (was 'unknown') |
| Memoir writes JSON | confirmed |
| Nightly conductor | 8/8 steps green |
| Full test suite | 805 passing |

## Why this matters (founder insight)

> "Agent should not forget its mistakes and learnings, the wins, and what its task is supposed to be."

This sprint addresses BOTH:
- Tactical: brain wasn't learning (Fix #1)
- Philosophical: agent had no narrative continuity (Fix #3)

The memoir is the agent's soul — identity continuity across nightly runs.

## What this does NOT fix (intentionally)

- 11% win rate (only 9 trades — too small to act on)
- Cron scheduling (verified working last night)
- "unknown" tags in EXISTING data (historical, can't backfill)

Only future picks benefit. Old picks stay "unknown" forever.

## Trigger conditions to revisit

- Sunday May 10 report still all "unknown" → schema mismatch elsewhere
- Memoir file empty after a week → picks_log not updating
- 30+ trades and brain still no edges → strategy itself needs tuning

---
*Permanent entry: docs/CHANGE_LOG.md 2026-05-04*
