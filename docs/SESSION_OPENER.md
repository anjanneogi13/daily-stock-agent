# 🎬 SESSION OPENER — Paste this verbatim when returning to a new Claude chat

**Purpose:** Zero context loss. Future-Claude reads the right docs in the right order before doing anything.

**Last updated:** 2026-05-04 (after 8-commit sprint)

---

## ✅ The opener (copy-paste verbatim)

I am Anjan, returning after [X days/weeks].

Last session was 2026-05-04 (Monday) where we shipped 8 commits transforming the agent (1 code + 7 docs). The agent now has a soul (agent_memoir.py) and a 7-faculty vision documented permanently.

Before you ask me anything, please read these docs in this exact order:

docs/CHANGE_LOG.md (newest entries on top — what changed when)
docs/AGENT_PHILOSOPHY.md (the 7-faculty vision + 8 design rules)
docs/ARCHITECTURE.md (especially Section 8 — faculty map)
docs/FINAL_ROADMAP.md (Phases 9, 9.5, 10 are the future)
docs/NEXT_SESSION.md (homework + path A/B/C/D options)
Then check the current state:

Run: cat data/agent_memoir.json Tell me if it has real content (mission, lifetime stats, narrative).
Run: ls -la data/learning_journal.jsonl Confirm it is growing (size > 0, modified recently).
Look at the latest Sunday hypothesis report. Confirm buckets are REAL (high/mid/low, bull/bear/chop), NOT "unknown".
Once you have done all 8 steps, give me a 5-line status summary and ask which path I want to work on:

Path B: validate today fixes worked (if buckets still "unknown")
Path A: polish layman voice (if Telegram messages felt off)
Path C: build Phase 9 curiosity_engine.py (if 4+ weeks data exists)
Path D: power-user features (earnings-week, pre-market gaps)
Do NOT start coding anything until I confirm the path.

Code

---

## 🔑 Why this opener works

It does 4 things every future Claude session needs:

1. **Sets context** — tells future-Claude what we shipped last time
2. **Forces doc-reading FIRST** — prevents assumptions and hallucinations
3. **Verifies production state** — checks if memoir/buckets actually working in real life (not just in code)
4. **Forces founder to choose path** — prevents future-Claude from rushing into code before priority is set

---

## 📋 Quick reference — what each doc contains

| Doc | What it answers |
|---|---|
| `CHANGE_LOG.md` | "What changed and when?" (append-only timeline) |
| `AGENT_PHILOSOPHY.md` | "Why does this agent exist?" (7 faculties + 8 design rules) |
| `ARCHITECTURE.md` | "How is it built?" (system design + Section 8 faculty map) |
| `FINAL_ROADMAP.md` | "What is next?" (Phases 1-10, current + future) |
| `NEXT_SESSION.md` | "Where did we leave off?" (homework + path options) |
| `BUSINESS_PLAN.md` | "Where is this going?" (24-month strategic plan) |
| `AGENT_SCHEDULE.md` | "When does each piece run?" (8 cron schedules) |
| `SESSION_OPENER.md` | "How do I restart cleanly?" (this file) |

---

## 🛠️ Maintenance — when to update this file

Update SESSION_OPENER.md whenever:

- A new must-read doc is added to `docs/`
- A core verification step changes (e.g. new data file to check)
- A path option (A/B/C/D) becomes obsolete or a new one emerges
- The "last session" reference becomes stale (>1 month old)

Keep it short. This is a launchpad, not a manual.

---

## 💡 Pro tip

If you forget which docs to read, just ask Claude:

> "Read docs/SESSION_OPENER.md and follow it."

That single sentence is enough. Future-Claude will pick up everything from here.
