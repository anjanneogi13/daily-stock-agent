# 🧠 Weekend Review — 2026-04-29

## 📊 The Week in One Sentence
We generated 26 picks but none have closed yet, so we can't evaluate performance — however, the premarket warning system caught several bad setups before they could hurt us.

## ✅ What's Working Well
- **The premarket filter is saving us from disasters.** On April 28th, ARM, AVGO, and RMBS were all flagged "SKIP TODAY" in premarket, and all three would have hit stop-loss if traded. The system correctly identified danger before the market even opened.
- **Stop-losses protected us when they fired.** RMBS on 2026-04-28 hit its stop at -9.2%, but would have continued crashing to -21% to -25% by close. Without that stop, we'd have lost an extra 12-16% on that trade alone.

## ❌ What Went Wrong
- **We're picking semiconductor stocks on the worst possible days.** On April 28th, the semiconductor sector (SOXX) was down -3.05% in premarket. Despite this massive red flag, we still generated picks for LRCX, ALAB, ARM, AVGO, ONTO, TSM, and RMBS — and every single one either crashed or got stopped out. These were predictable losers.
- **Many picks never showed any upside momentum.** Stocks like LRCX, ALAB, and ONTO opened down and just kept falling. For example, LRCX's "best" moment was still -2.22% down. We're catching falling knives instead of waiting for any sign of strength.
- **Some stop-losses appear too tight.** ARM and TSM both hit their stops on April 28th, but the price barely moved further down (less than -0.2% additional drop). We may be getting shaken out right at the bottom instead of giving trades room to breathe.

## 🔧 Suggested Changes (For Your Review)

### Suggestion 1: Add a sector-wide kill switch for semiconductor picks

**The problem:** On April 28th, SOXX was down -3.05% in premarket, yet we still generated 7 semiconductor picks that day. The premarket filter flagged them individually, but we shouldn't even be considering these stocks when the entire sector is collapsing.

**The fix:** Before generating any picks, check if SOXX is down -2% or more in premarket. If yes, completely skip all semiconductor stocks for that day — don't even run them through the normal selection process.

**Where in the code:** `scripts/stock_screener.py` or wherever the initial universe of stocks is filtered before analysis begins.

**How to test:** Manually set SOXX premarket change to -2.5% and verify that no semiconductor tickers (LRCX, NVDA, TSM, ARM, AVGO, AMAT, etc.) appear in that day's picks at all.

**Confidence:** High — we have clear evidence that 7/7 semiconductor picks failed on a day when SOXX was down hard. This pattern repeated multiple times in the observations.

### Suggestion 2: Require a "first 15 minutes strength check" before entry

**The problem:** Stocks like LRCX, ALAB, and ONTO opened down and never recovered. LRCX's best moment all day was still -2.22% in the red. We're entering trades at the open without waiting to see if the stock shows any buying pressure.

**The fix:** After the market opens, wait 10-15 minutes. Only enter the trade if the stock has recovered to at least -0.5% from open or is showing green. If it's still bleeding heavily after 15 minutes, skip the trade for that day.

**Where in the code:** `scripts/trade_execution.py` or the order placement logic — add a timer and price check between 9:30 AM and 9:45 AM before submitting the buy order.

**How to test:** On a simulated bad day (like April 28th), verify that LRCX and ALAB would NOT have been entered because they were still down -3% to -5% at 9:45 AM.

**Confidence:** Medium — we have strong evidence that opening losers stay losers, but this adds complexity and might cause us to miss some good entries. Worth testing on historical data first.

### Suggestion 3: Widen stop-losses by 1-2% for high-volatility stocks

**The problem:** ARM and TSM both hit their stops on April 28th (around -5% to -8.8%), but then the price barely moved further (only -0.01% to -0.16% additional drop). We're getting stopped out right at the intraday low instead of letting normal volatility play out.

**The fix:** For stocks with average true range (ATR) above a certain threshold (e.g., $5 daily range), add 1.5-2% cushion to the stop-loss. So instead of -5%, use -6.5% or -7% to avoid getting shaken out by normal price swings.

**Where in the code:** `scripts/risk_management.py` or wherever stop-loss levels are calculated — add an ATR check and adjust the stop percentage accordingly.

**How to test:** Backtest ARM and TSM trades from April 28th with a -7% stop instead of -5% and see if they would have recovered instead of stopping out.

**Confidence:** Low — while we have 5 examples of "tight stops," we also have 6 examples where stops saved us from much bigger losses (like RMBS). Needs more data before making this change permanent.

## 🎓 Lesson of the Week
The most important lesson is that **sector context matters more than individual stock signals.** When an entire sector is getting hammered (like semiconductors down -3% in premarket), even your "best" picks from that sector are likely to fail. No amount of technical analysis on an individual stock can overcome a sector-wide selloff. The premarket filter caught this for individual stocks, but we need to think bigger — if the whole neighborhood is on fire, don't go house shopping there at all.

## ⏭️ What I'd Watch For Next Week
- **How many picks actually close** — we need at least 20 completed trades before making major system changes.
- **Whether CDNS and ANET continue trending up** — these were the only two stocks showing promise on April 28th (+1.46% and +1.24%), both outside the semiconductor disaster zone.
- **If sector-wide selloffs happen again** — watch for days when entire sectors (not just semis) are down -2%+ in premarket, and see if our picks in those sectors fail consistently.