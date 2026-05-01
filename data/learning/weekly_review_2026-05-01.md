# 🧠 Weekend Review — 2026-05-01

## 📊 The Week in One Sentence
The bot got absolutely hammered this week with a 0% win rate (6 trades closed, all stopped out), mostly because it jumped into semiconductor stocks on a day when the entire sector was collapsing.

## ✅ What's Working Well
- **The premarket warning system is doing its job** — ARM, AVGO, and RMBS all got tagged "SKIP TODAY" in premarket, and they all hit stop loss. The filter correctly identified danger, we just didn't listen to it.
- **Stop losses saved us from disaster** — RMBS would've closed down -21% to -25% without protection, but the stop loss cut it at -9%. That's the difference between a bad day and a catastrophic one.

## ❌ What Went Wrong
- **We traded into a sector meltdown** — On April 28th, semiconductors were down -3.05% in premarket (SOXX), yet the bot still entered 10+ semiconductor picks. Result: multiple stocks like LRCX, ALAB, and ONTO immediately dropped 4-8% and never recovered.
- **Chasing falling knives** — Nearly every losing trade (LRCX, ALAB, ONTO) showed the same pattern: filled at open, went straight down, best case was still negative. These weren't unlucky stops — these were bad entries into stocks already bleeding.
- **Stop losses might be slightly too tight on some picks** — ARM and TSM both hit their stops and then barely moved lower (less than -0.2% further drop). We got shaken out right at the low point.

## 🔧 Suggested Changes (For Your Review)

### Suggestion 1: Actually Block Trades When Sector is Down Big in Premarket
**The problem:** The premarket checker tagged ARM, AVGO, and RMBS as "SKIP TODAY" because semis were down -3%, but the bot still entered those trades anyway. The warning existed but wasn't enforced — it was just a label that got ignored.

**The fix:** When SOXX is down -2% or worse in premarket, automatically remove ALL semiconductor picks from the entry list for that day. Don't just warn — actually prevent the orders from being placed.

**Where in the code:** `scripts/premarket_check.py` (the part that checks SOXX) and `scripts/place_orders.py` (where it decides which picks to actually trade)

**How to test:** On the next day SOXX is down -2%+ premarket, verify that zero semiconductor orders get placed and check the logs to confirm they were filtered out.

**Confidence:** High — we have clear evidence that 4 out of 6 losing trades happened on a day with a -3% semiconductor sector drop, and all the "SKIP TODAY" tags were correct predictions.

---

### Suggestion 2: Don't Enter Stocks Already Red at the Open
**The problem:** LRCX, ALAB, and ONTO all filled at open and immediately went negative with no recovery (best case was still -2% to -3% down). The bot is catching stocks mid-fall instead of waiting to see if they stabilize.

**The fix:** Add a 15-minute delay after market open before entering positions. Only place the order if the stock hasn't dropped more than -1.5% in the first 15 minutes. Let the falling knife hit the ground first.

**Where in the code:** `scripts/place_orders.py` — add a check after 9:45am that compares current price to opening price before submitting limit orders.

**How to test:** Paper trade for a week with the new rule and compare: how many "weak pick" observations disappear? Did we avoid the worst losses while still catching good entries?

**Confidence:** Medium — the pattern is very clear in this week's data (18 "weak_pick" flags), but we need to verify this doesn't cause us to miss good opportunities on normal days.

---

### Suggestion 3: Widen Stop Losses Slightly for High-Quality Large Caps
**The problem:** TSM and ARM both hit stop loss and then the price immediately stopped falling (within -0.01% to -0.16% further drop). We got stopped out at the exact low, suggesting the stop was placed right where everyone else's stops were sitting.

**The fix:** For stocks over $100B market cap with low volatility (like TSM), widen the stop loss from -5% to -6.5% to give them more breathing room through normal intraday chop.

**Where in the code:** `scripts/calculate_stops.py` or wherever stop loss percentages are defined — add a conditional that checks market cap and adjusts the stop accordingly.

**How to test:** Backtest the last 3 months of TSM/NVDA/AAPL picks and see: would a -6.5% stop have kept us in more winning trades without significantly increasing losses on the real losers?

**Confidence:** Low — we only have 5 "sl_too_tight" observations, which isn't enough data to be sure. This could just be bad luck. Worth testing but not urgent.

## 🎓 Lesson of the Week
When the whole sector is bleeding before the market even opens, individual stock picks don't matter — the tide will sink everything. The bot correctly identified the danger (premarket warnings worked perfectly), but we didn't have the infrastructure to actually *act* on that warning and cancel the orders. It's like having a smoke detector that beeps but no one leaves the building. The next step is making sure warnings automatically translate into "do not trade" decisions, not just labels in a Telegram message.

## ⏭️ What I'd Watch For Next Week
- **Whether we keep seeing "weak_pick" flags on normal market days** — if the falling knife pattern continues even without sector crashes, the 15-minute delay becomes critical.
- **Any stops that are "well placed"** — RMBS showed what a good stop looks like (saved 12-18% of additional losses). Let's count how often our stops actually protect us vs. just shake us out.
- **Missed opportunities from being too conservative** — we missed ADI and AAPL this week because limit orders were too low. If this becomes a pattern, we're leaving money on the table by being too pessimistic on entry prices.