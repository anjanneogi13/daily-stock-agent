# 📋 Chat Handoff Protocol

> **Why this exists:** AI chat sessions reset. The repo doesn't. This protocol ensures continuity.

## 🎯 START OF EVERY NEW CHAT SESSION

Paste this prompt as your FIRST message:

```
Resuming work on daily-stock-agent. Before doing anything, read:

1. docs/CONTEXT.md (project identity + principles)
2. docs/ROADMAP.md (current state + phases)
3. docs/reference/PROBABILITY_ENGINE_DESIGN.md (architecture)
4. Most recent file in docs/sessions/
5. Recent files in docs/decisions/

Then summarize:
- Where are we in the roadmap?
- What was the last session about?
- Any open bugs or decisions?
- What's the recommended next action?

Wait for my approval before coding.
```

## 🎯 END OF EVERY SESSION

Before closing chat:

1. **Update `docs/ROADMAP.md`**
   - Tick completed boxes
   - Add new bugs discovered
   - Update Session Log table

2. **Create session handoff in `docs/sessions/YYYY-MM-DD-{topic}.md`**
   - What we shipped
   - What we decided
   - What broke (and how we fixed)
   - What's pending for next session

3. **For architectural decisions, create ADR**
   - File: `docs/decisions/ADR-NNN-{decision}.md`
   - Increment NNN sequentially

4. **Commit and push**
   ```bash
   git add docs/
   git commit -m "docs: session handoff YYYY-MM-DD"
   git push origin main
   ```

## 🎯 MID-SESSION RULES

- Important decision made? → Add to `docs/decisions/` IMMEDIATELY
- Bug discovered? → Add to `docs/ROADMAP.md` Phase 0 IMMEDIATELY
- Lesson learned? → Add to `docs/learnings/` IMMEDIATELY

DO NOT trust your memory or the AI's memory. Trust the repo.

## 🎯 ANTI-PATTERNS (Don't Do These)

❌ "I'll remember to write that down later" — You won't
❌ "The AI knows what we discussed yesterday" — It doesn't
❌ "Let me just code this real quick" — Decision lost
❌ "We can refactor the docs later" — Later never comes

## 🎯 NAMING CONVENTIONS

- **Sessions:** `YYYY-MM-DD-{descriptive-topic}.md`
  - Example: `2026-05-02-probability-vision-defined.md`
- **ADRs:** `ADR-NNN-{kebab-case-decision}.md`
  - NNN starts at 001, increment by 1
- **Learnings:** `YYYY-MM-DD-{lesson}.md`
- **Bugs:** Tracked in ROADMAP.md, not separate files