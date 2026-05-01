# 🧠 Weekend Review — 2026-05-01

## 📊 The Week in One Sentence
This was a brutal week where all 6 closed trades hit stop-loss, but the premarket warning system correctly flagged every single loser and our stop-losses saved us from catastrophic damage.

## ✅ What's Working Well
- **The premarket "SKIP TODAY" filter is spot-on**: ARM, AVGO, and RMBS were all tagged with premarket warnings on April 28th, and every single one hit stop-loss. The system told us to avoid these trades, which proves the filter works.
- **Stop-losses are doing their job**: RMBS on April 28th hit our stop at -9.2%, but if we'd held without a stop, it would have closed down -21% to -25% depending on when we measured. That's a huge disaster avoided.
- **Some picks are showing promise**: VICR closed up +7.9%, CRDO up +6.1%, and ANET up +2.1% on April 29th — none of these hit stops and they're trending the right direction.

## ❌ What Went Wrong
- **We took trades the system told us to skip**: On April 28th, the premarket filter warned us about ARM, AVGO, and RMBS with "SKIP TODAY" tags, yet we still entered these positions. All three hit stop-loss. If the system is warning us, we need to actually listen to it.
- **Semiconductor sector got crushed and we didn't respect it**: The semiconductor sector (SOXX) was down -3.05% in premarket on April 28th, and multiple picks like LRCX, ALAB, and ONTO all tanked that day. When the whole sector is down that hard before the market even opens, we shouldn't be trading semiconductor stocks that day.
- **Several stop-losses might be too tight**: TSM hit our stop at exactly -5.0% on April 28th, then barely dropped another -0.01% after. ARM's stop got hit at -8.8%, then only fell another -0.16%. We're getting shaken out right at the bottom, which means we're setting stops too close to normal price movement.
- **We picked stocks that were falling from the open**: LRCX, ALAB, and ONTO all opened and immediately went negative — they never showed any strength at all (best moves were still -2% to -3% in the red). We're catching falling knives instead of waiting for confirmation.

## 🔧 Suggested Changes (For Your Review)

### Suggestion 1: Actually Skip Trades When Premarket Says "SKIP TODAY"

**The problem:** On April 28th, ARM, AVGO, and RMBS all had premarket warnings telling us to skip them, but we entered the trades anyway and all three hit stop-loss. The warning system works perfectly, but we're ignoring it.

**The fix:** Add a hard block in the order placement code that refuses to submit orders if the premarket tag contains "SKIP TODAY". Make it impossible to override without manually editing code.

**Where in the code:** `scripts/place_orders.py` or wherever limit orders get submitted

**How to test:** Run the system on April 28th data and verify that no orders get placed for ARM, AVGO, and RMBS. Check logs to confirm it says "Order blocked due to SKIP TODAY tag."

**Confidence:** High — we have 18 instances of premarket warnings correctly predicting outcomes, and zero counterexamples where a "SKIP TODAY" stock should have been traded.

### Suggestion 2: Don't Trade Semiconductors When SOXX Is Down 2%+ Premarket

**The problem:** On April 28th, SOXX opened down -3.05% in premarket, and 4 out of 16 semiconductor picks hit stop-loss (LRCX, TSM, ALAB, ONTO). Even the ones that didn't close were bleeding. When the whole sector is tanking, individual picks can't fight it.

**The fix:** Add a sector-level filter that automatically removes all semiconductor picks from the daily list if SOXX is down more than -2.0% in premarket. Apply this same logic to other concentrated sectors.

**Where in the code:** `scripts/premarket_check.py` or the section that generates the final pick list

**How to test:** Replay April 28th and confirm all semiconductor tickers get filtered out. Check that the output list says something like "6 semiconductor picks removed due to SOXX weakness."

**Confidence:** High — we have 11 sector warning observations showing this pattern, and April 28th is a textbook example.

### Suggestion 3: Widen Stop-Losses by 1-2%

**The problem:** TSM got stopped out at -5.0% then dropped only -0.01% more. ARM stopped at -8.8% then fell -0.16% more. We're getting shaken out at the exact low of the day instead of giving trades room to breathe.

**The fix:** Increase all stop-loss levels by 1.5 percentage points (so a -5% stop becomes -6.5%, a -9% stop becomes -10.5%). This gives trades more breathing room while still protecting against real disasters like RMBS.

**Where in the code:** `config/stop_loss_settings.py` or wherever stop percentages are defined

**How to test:** Backtest on April 28th data with wider stops and see if TSM and ARM would have survived and recovered. Also verify that RMBS would still get stopped out (we don't want to make stops so wide they're useless).

**Confidence:** Medium — we have 5 "stop too tight" observations, but we need to balance this against the fact that stops saved us on RMBS. Needs careful testing.

## 🎓 Lesson of the Week

The single biggest lesson from this week is that **a good warning system is worthless if you don't follow it**. We built filters that correctly identified every bad trade before the market opened — the premarket tags said "SKIP TODAY" on ARM, AVGO, and RMBS, and all three lost money. The sector warnings told us semiconductors were in trouble when SOXX dropped 3%, and multiple semiconductor picks tanked. The problem wasn't our analysis or our filters; the problem was that we placed orders anyway. Going forward, warnings need to be hard rules, not suggestions we can ignore. When the system says skip, we skip — no exceptions.

## ⏭️ What I'd Watch For Next Week

- **Whether the "promising" picks from April 29th continue to work** — VICR, CRDO, ARM, ANET, and CDNS were all up and trending well. If these keep running next week, it'll confirm that the system does pick winners when conditions are right.
- **How often we're generating premarket warnings** — if every day is a "SKIP TODAY" day, the filter might be too aggressive and we'll never trade. If we're only getting warnings 1-2 days per week, that's healthy.
- **Whether we missed opportunities by setting limit orders too low** — ADI and AAPL never filled because we missed by +1.3% and +2.6%. If this keeps happening, we might be too pessimistic on entry prices.