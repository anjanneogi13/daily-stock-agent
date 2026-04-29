# 🧠 Weekend Review — 2026-04-29

## 📊 The Week in One Sentence
We generated 28 picks but none closed yet, so this is a "read the temperature" review — and honestly, the temperature reading shows we're picking stocks on terrible days and our premarket filters are catching problems *after* we've already made bad picks.

## ✅ What's Working Well
- **The premarket filter is doing its job** — ARM, AVGO, and RMBS all got tagged "SKIP TODAY" on April 28th and indeed all hit their stop losses, proving the filter spotted danger correctly
- **Stop losses are saving us from disasters** — RMBS would have closed down 21-25% without the stop loss, but instead got stopped out at -9%, saving us from a catastrophic loss on April 28th

## ❌ What Went Wrong
- **We're picking semiconductor stocks on awful sector days** — On April 28th, the semiconductor sector (SOXX) was down -3.05% in premarket, and we still generated picks for LRCX, ALAB, ARM, AVGO, ONTO, TSM, and RMBS. These weren't just losses, they were "falling knife" entries where stocks never showed any strength.
- **18 out of 28 picks were weak from the start** — Stocks like LRCX, ALAB, and ONTO got filled at open and immediately dropped, never recovering. Their "best case" movements were still negative (MFE around -2% to -3%), meaning we bought at exactly the wrong time.
- **Some stop losses might be too tight** — TSM hit its stop loss at -5%, then only dropped another -0.01% after that. ARM stopped out at -8.8% and only fell -0.16% more. We're getting shaken out right at the bottom.
- **All 28 picks came from the same bad day** — Every single observation is from April 28th, which suggests the system either isn't running daily or only ran once during a market bloodbath.

## 🔧 Suggested Changes (For Your Review)

### Suggestion 1: Block picks entirely when sector is down big in premarket
**The problem:** On April 28th, SOXX was down -3.05% in premarket, yet the system still generated 10+ semiconductor picks that day. The premarket filter tagged them "SKIP TODAY" but only *after* they were already selected as picks. That's backwards — we shouldn't be picking them at all.

**The fix:** Add a sector health check *before* stock selection runs. If SOXX is down -2% or worse in premarket, don't generate any semiconductor picks that day. Same logic could apply to other sectors (XLF for financials, XLE for energy, etc.).

**Where in the code:** `scripts/daily_picker.py` or wherever the main pick generation logic runs — needs to check sector ETF prices before filtering individual stocks

**How to test:** Run it on historical data from April 28th, 2026. It should generate zero semiconductor picks that day. Then test on a normal day (SOXX flat or up) and confirm picks still generate.

**Confidence:** High — the data clearly shows 4+ stop losses hit when SOXX was down -3%, and the pattern is obvious enough that this would prevent a lot of pain.

---

### Suggestion 2: Widen stop losses by 1-2% to avoid getting shaken out at the exact bottom
**The problem:** TSM stopped out at -5.00% and then only dropped -0.01% more. ARM stopped out at -8.8% and dropped just -0.16% after. We're getting stopped out within pennies of the low, suggesting our stops are so tight they're catching normal intraday volatility instead of true breakdowns.

**The fix:** Increase stop loss distances by 1-2 percentage points, or use ATR (Average True Range) instead of fixed percentages. For a stock like TSM, a -6% or -7% stop would let it breathe without risking much more downside.

**Where in the code:** Wherever stop loss percentages are defined — likely `config.yaml` or `stop_loss_calculator.py`

**How to test:** Backtest the same April 28th picks with wider stops. Check how many would have avoided the stop hit and recovered. If most still tanked, the tight stops aren't the problem. If several recovered, wider stops would help.

**Confidence:** Medium — we only have 5 examples of "too tight" stops, and 3 of them (ARM, TSM twice) are marginal. Need more data to be sure, but the pattern is suggestive.

---

### Suggestion 3: Don't run picks at all on days when market opens down sharply
**The problem:** Every single one of the 28 picks came from April 28th, a day when semiconductors opened down -3%. The system generated picks into a falling market, resulting in 18 "weak pick" observations where stocks never showed any upward movement at all.

**The fix:** Add a "market circuit breaker" that checks SPY or QQQ at open. If the market is down more than -1% in the first 15 minutes, cancel all picks for the day or switch to a "wait and see" mode. Only enter trades if the market stabilizes or bounces.

**Where in the code:** `scripts/market_open_monitor.py` or the execution/order entry script that runs at 9:30 AM

**How to test:** Simulate April 28th with the rule active — it should either generate no picks or delay them until later in the day. Then test on a normal down -0.3% open to make sure it doesn't block too aggressively.

**Confidence:** High — catching a falling knife is one of the most common ways to lose money, and we have 18 examples from a single day proving we did exactly that.

---

### Suggestion 4: Reduce position size or skip entirely when premarket filter says "SKIP TODAY"
**The problem:** The system correctly tagged ARM, AVGO, and RMBS as "SKIP TODAY" on April 28th, but they still appear in the observations as picks that hit stop losses. If the filter is working but we're still entering these trades, the filter isn't connected to the execution logic.

**The fix:** Make the "SKIP TODAY" tag enforceable — either completely block order entry for those tickers, or reduce position size to 25% as a "test only" allocation. The filter should have teeth, not just be a warning.

**Where in the code:** `scripts/order_execution.py` or wherever the premarket tags feed into actual trade decisions

**How to test:** Manually set a stock's premarket tag to "SKIP TODAY" and verify the system either doesn't place an order or only places a tiny one. Confirm normal picks still execute at full size.

**Confidence:** High — we already built the filter and it's working. We just need to wire it up so the system actually listens to it.

## 🎓 Lesson of the Week
The single most important lesson this week: **Don't fight the tape**. When an entire sector is getting crushed in premarket (like semiconductors down -3% on April 28th), there are no "good picks" in that sector that day — only varying degrees of bad. Our system correctly identified the danger with premarket warnings, but then went ahead and generated picks anyway. The edge isn't in finding the one stock that goes up when everything else is down; the edge is in having the discipline to sit out and wait for a better day. Cash is a position too.

## ⏭️ What I'd Watch For Next Week
- **Whether the system runs on multiple days** — all 28 picks came from April 28th. If this is a bug (system only ran once), that's a problem. If it's by design (only run once a week), we need more frequent picks to build a real dataset.
- **How many of the "promising" picks actually close** — CDNS and ANET were both up around +1.2-1.5% on April 28th. Let's see if they reach take profit or reverse course.
- **Whether semiconductor sector conditions improve** — if SOXX stays weak, we should see the new "block sector picks" rule (if implemented) kick in and prevent more falling knife entries.