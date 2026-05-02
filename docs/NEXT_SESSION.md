# NEXT SESSION — Sunday May 3, 2026 SPRINT PLAN

Updated: Saturday evening end-of-day
Mode: CODE DAY — structured sprint
Time budget: 4-6 hours (your call)
Strategy: Ship everything that does NOT depend on Monday live validation

---

## SPRINT GOAL

Clear execution-layer debt so Monday live picks have the best chance
of validating Saturday leak fixes. Close bottom-5 ticker bleed and
4 outstanding bugs.

Success metric: End Sunday with 4 of 5 BUGs resolved + bottom-5 dropped.

---

## SUNDAY TASK LIST (Priority Order)

### TASK 1 — Drop Bottom-5 Tickers (15 min) — EASIEST WIN
Why first: Backtester data proved these lose. Pure config.
Tickers to drop: UNH, TEAM, SMCI, DIS, SCHW

Steps:
1. Find universe definition file
2. Add to new data/do_not_trade.yaml exclusion list
3. Modify universe loader to skip them
4. Add 1 test
5. Commit

Open chat: "Start Task 1 - drop bottom-5 tickers"

---

### TASK 2 — Fix BUG-3 Regime unknown (45 min)
Why: Regime fetch fails silently leading to "unknown" with no filter.

Steps:
1. Find why regime returns "unknown" (likely SPY data fetch fail)
2. Add retry + fallback to last-known-regime
3. Add 1hr cache
4. Add test for fallback path
5. Commit

Open chat: "Start Task 2 - fix BUG-3 regime unknown"

---

### TASK 3 — Fix BUG-2 Pending Evaluation (45 min)
Why: 38 picks stuck in pending = no R-multiple data.

Steps:
1. Diagnose which picks are pending and why
2. Likely off-by-one in evaluator date logic
3. Patch + backfill stuck records
4. Add test
5. Commit

Open chat: "Start Task 3 - fix BUG-2 pending evaluation"

---

### TASK 4 — Fix BUG-5 SL Too Tight (45 min)
Why: Quality picks (NVDA, AVGO, RMBS) rejected with 1.8-2.8% SL.

Steps:
1. Find SL min check in hard_blocks.py or scorer.py
2. Implement tiered SL minimums by stock price tier:
   - $100 and up: 1.5% min SL
   - $30 to $99: 2.0% min SL
   - $10 to $29: 2.5% min SL
   - under $10: 3.0% min SL
3. Add test per tier
4. Commit

Open chat: "Start Task 4 - fix BUG-5 tiered SL minimums"

---

### TASK 5 — Port Cooldown To Live (60 min)
Why: Backtester has cooldown logic, live does not. BUG-4 full fix.

Steps:
1. Find cooldown code in src/backtester/
2. Extract into src/cooldown.py shared module
3. Wire into main.py pre-scoring filter
4. Refactor backtester to use shared module
5. Add tests
6. Commit

Open chat: "Start Task 5 - port cooldown to live"

---

### TASK 6 STRETCH — PR Triage (60 min)
Steps:
1. List all 13 open PRs (#60-86)
2. For each: merge / close-as-obsolete / keep-with-comment
3. Goal: under 5 open PRs by end of session

Open chat: "Start Task 6 - PR triage"

---

### TASK 7 STRETCH — Pillar 2 Wisdom Base Curation (60 min)
No code. Pure thinking work. Sets up Week 2 build.

Steps:
1. Curate list of 10 trading books
2. Pick top 5 rules from your memory of each
3. Create skeleton data/wisdom_base.json
4. Document LLM extraction plan for actual run later

Open chat: "Start Task 7 - wisdom base curation"

---

## DO NOT DO SUNDAY

- Pillar 1 Layer 4 hypothesis testing — needs Monday data
- Backtester Phase B walk-forward — Phase A is enough
- Brain weight retuning — needs more outcomes
- New features beyond bug fixes — stay focused
- Touch sector/tag/boost config — already patched, let it run
- Touch workflow cron schedules — already patched, let it run

---

## MONDAY MAY 4, 2026 — VALIDATION DAY

Time: 8:30 PM SGT (8:30 AM ET)

Pass criteria:
- Workflow runs today: target 1 (catastrophe if 2+)
- Picks logged: target 5-10 (catastrophe if 12+)
- % SEMI tagged: target under 40% (catastrophe if over 60%)
- Distinct sectors: target 3 or more (catastrophe if 1)

---

## BACKLOG (After Monday Validates)

Week of May 5-9:
- Pillar 1 Layer 4 (hypothesis testing — UNBLOCKED by backtester)
- Wed May 6 — Flip BRAIN_ENFORCE_EV=true
- Wed May 6 — Flip AUTO_PAUSE_ENABLED=true
- Backtester Phase B (walk-forward validation)

Week of May 10-16:
- Pillar 2 (Wisdom Base) full build
- LLM extraction script run

Week of May 17-30:
- Pillar 3 (Pattern Recognition) — 2-week build

Month of June:
- Pillar 4 (Feedback Loop)
- Pillar 5 (Self-Awareness completion)
- Alpaca paper trading integration

---

## CURRENT STATE SNAPSHOT

- Total commits Saturday: 55
- Tests passing: 245
- Open PRs: 13 (target: under 5 by end Sunday)
- BUGs remaining: 4 (target: 0 by end Sunday)
- Algorithm validated: YES — Sharpe +0.97 backtest
- Live execution: 2 leaks patched, awaiting Monday validation

---

## PROTOCOL REMINDER

You: "check NEXT_SESSION.md"
Me: read it, tell you which task to start
You: "start Task N"
Me: give exact code/commands
Both: ship it
Me: end of session — update FINAL_ROADMAP.md + rewrite this file

---

Owner: Anjan Neogi, Singapore
This file overwritten end of every session.
