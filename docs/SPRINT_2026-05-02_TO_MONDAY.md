# 🎯 Weekend Sprint — Monday Market Open Deadline

> **Goal:** Clean baseline running Monday 8:30 PM SGT (US market open)
> **Cutoff Sat:** 4:00 PM SGT (today)
> **Sunday:** Variable (user will indicate)
> **Test:** Monday's live picks reveal real capability

---

## ⏱️ TIME BUDGET

| Block | When | Hours | Mode |
|---|---|---|---|
| **Sat Sprint 1** | NOW → 4 PM SGT | ~3 hr | Bug fixes + benchmark |
| **Sat Break** | 4 PM → ? | rest | Eat, walk, family |
| **Sat Sprint 2** | Evening (optional) | 2-3 hr | Wisdom base seed |
| **Sun Sprint** | Morning + afternoon | 4-6 hr | Polish + Alpaca paper |
| **Sun Cutoff** | 5 PM SGT (firm) | — | Stop. Sleep. |
| **Mon Test** | 8:30 PM SGT | live | Watch agent perform |

---

## 🎯 PRIORITIES (RUTHLESS RANKING)

### MUST SHIP (Saturday afternoon, ~3 hr)
1. **BUG-1** — Penny stock SLNH bypassed min_price filter (45 min)
2. **BUG-4** — Same-ticker cooldown (TSM picked 3× in 4 days) (45 min)
3. **VAL-2** — SPY benchmark column in picks_log (60 min)
4. **TEST** — Manual smoke test, verify fixes (30 min)

### SHOULD SHIP (Saturday evening OR Sunday, ~3 hr)
5. **BUG-2** — Pending evaluations not closing (60 min)
6. **BUG-3** — Regime "unknown" debug (60 min)  
7. **VAL-5** — "No picks today" capability (60 min)

### NICE TO SHIP (Sunday only if time, ~4 hr)
8. **WIS-1 to WIS-4** — Wisdom base v1 (3 hr)
9. **VAL-1** — Alpaca paper integration (3 hr — pick ONE of #8 or #9)

### EXPLICITLY NOT THIS WEEKEND
- ❌ Brain v1 / self-learning ML
- ❌ Vision chart reading  
- ❌ Multi-bagger strategy
- ❌ MA stack 5/10/20/30 (defer to next weekend)
- ❌ Earnings reactor
- ❌ Any 8-PR mega-build

---

## 🟢 SATURDAY 4 PM CHECKPOINT — Definition of Success

By 4 PM SGT today, the agent will:
- ✅ Reject penny stocks <$5 properly (BUG-1)
- ✅ Not pick same ticker twice in 5 days (BUG-4)
- ✅ Log SPY return alongside each pick (VAL-2)
- ✅ Pass smoke test (manual workflow_dispatch run)

**If we hit 4 PM checkpoint → Monday is already a "win" on baseline measurement.**

---

## 🟡 SUNDAY GOAL — Definition of Stretch Win

ONE of these (not both):
- **Path A:** Wisdom Base v1 — 10 books extracted, per-pick rule check
- **Path B:** Alpaca paper integration — real fills tracked Monday

Plus the "should ship" items 5-7 if time permits.

---

## 📋 MONDAY MORNING TEST PLAN

When you wake Monday morning SGT (before work):
1. Check no GitHub Actions errors overnight
2. Check ROADMAP.md for any last-minute notes I left

Monday 8:30 PM SGT (after work, market opens):
3. Watch Telegram for picks
4. Screenshot the message
5. Note: penny stocks present? duplicates? SPY benchmarks shown?
6. Compare picks to actual market open prices
7. Wait for evening close
8. Check evaluation runs Tuesday morning

By Friday May 8:
9. Run weekly review
10. Calculate alpha vs SPY for week's picks
11. Update ROADMAP.md with results

---

## 🚨 RED LINES (Stop work if hit)

- 🛑 **It's 4 PM Sat and bug fixes incomplete** → Stop, ship what's done, update roadmap, take break
- 🛑 **Sun 5 PM and tests failing** → Roll back to last green commit. DO NOT push broken code.
- 🛑 **Any moment: "I'm tired and forcing it"** → Stop. Bad code worse than no code.
- 🛑 **Sun 8 PM** → Lights out. Sleep is non-negotiable for Monday work.

---

## 📊 SESSION LOG (update after each sprint)

| Time | What shipped | Bugs found | Energy level |
|---|---|---|---|
| Sat 1 PM | starting BUG-1 | — | high |
| | | | |

---

*Living doc. Update after each sprint block.*