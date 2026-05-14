# Audit — `src/hard_blocks.py`
**LOC:** 330 | **Wired in:** ✅ Yes — `main.py` calls `apply_hard_blocks(picks)` after scoring | **Tests:** `tests/test_hard_blocks.py` (~60% coverage)  
**Suggestion-only context:** **DEEPLY VIOLATES CONTRACT** — every block returns `(False, reason)` and the candidate is silently removed (no Telegram footprint).

## Findings

### F2-1 — L171-193 `_block_sl_buffer` tiered SL minimums
- **Code:** Tier table 1.5%/2%/2.5%/3% by price; reject if buffer < tier.
- **Behavior:** Drops candidates whose SL is too tight even after pattern engine's stop calc.
- **Risk:** Pattern engine already produces sound stops. Forcing 1.5%+ on a $200 stock can ruin the R/R math the brain just calculated. **Worse, the rejection is silent — no Telegram explains why.**
- **Verdict:** 🔴 **LOOSEN**
- **Fix:** Don't drop. Auto-widen SL to the minimum + recompute R/R. Skip only if the new R/R falls below `min_risk_reward`. (Lets the brain's choice survive when it can.)

### F2-2 — L60-88, L197-215 `_block_recent_pick` 5-day cooldown
- **Code:** `COOLDOWN_DAYS = 5` — rejects any ticker picked in the last 5 calendar days.
- **Behavior:** Reads `data/picks_log.csv` for ANY past pick of this ticker (regardless of outcome — winning trades are punished as much as losing ones).
- **Risk:** 🔴🔴🔴 **TOP SILENT KILLER.** If the agent picked NVDA Monday and NVDA broke out Tuesday-Friday on news, the agent CANNOT pick it again. Combined with the small high-quality universe, the agent runs out of new ideas in 5 days.
- **Verdict:** 🔴 **LOOSEN**
- **Fix:** Apply cooldown ONLY if the previous pick LOST (`evaluation_status in ('sl_hit','expired_loss','max_hold_loss')`). Reduce to 3 days. Add `force=True` override for the wisdom layer to allow re-entries.

### F2-3 — L132-153, L217-237 `_block_weak_sector` (-2% sector ETF)
- **Code:** `SECTOR_ETF_DROP_THRESHOLD = -2.0` — reject all stocks in any sector whose ETF is down ≥2%.
- **Behavior:** Pulls XLK/XLF/etc. last-day % change. If down 2%+, rejects every candidate in that sector.
- **Risk:** A 2% sector down day is a NORMAL day. Sometimes it's the best buying opportunity (mean reversion). Hard-blocking kills these. **Also: `_safe_pct_change` uses `period="3d"` daily history, NOT premarket sector futures — so it's reacting to YESTERDAY'S sector move, not today's.**
- **Verdict:** 🔴 **LOOSEN**
- **Fix:** Change to soft-warn (HIGH severity, no block) below -3%. Block only at -5%+ (genuine sector crisis).

### F2-4 — L158-168 `_block_penny` (price < $5)
- **Code:** `MIN_PRICE = 5.00`
- **Behavior:** Reject if price < $5.
- **Risk:** Reasonable — penny stocks have execution & manipulation issues. Excludes legitimate sub-$5 names but losses outweigh gains on average.
- **Verdict:** ✅ **KEEP**

### F2-5 — L240-252 `_block_catastrophic_news`
- **Code:** Calls `news_signals.is_hard_blocked(ticker)`.
- **Behavior:** Blocks on bankruptcy / fraud / SEC investigation news.
- **Verdict:** ✅ **KEEP** — genuine no-touch list.

### F2-6 — L162 fail-closed on missing entry price
- **Code:** `return False, "missing entry price (broken upstream pick)"`
- **Behavior:** If pick has no entry, drop it.
- **Verdict:** ✅ **KEEP** — correct fail-closed.

### F2-7 — L308-327 silent audit log
- **Code:** Writes `data/hard_blocks_log.json` (last 100 entries).
- **Behavior:** Logged for forensic review but **never surfaced in Telegram.**
- **Risk:** When user complains "agent found nothing today," nobody reads this file.
- **Verdict:** 🔴 **LOOSEN** (in PR-A3, not PR-A2)
- **Fix:** Pipe block summary to Telegram diagnostic when blocked_count > 50% of input.

### F2-8 — Module-level: silent removal pattern
- All blocks return `(False, reason)` and the caller silently drops them.
- No mechanism to convert "block" into "warn and pass with HALF_SIZE" the way `premarket_sanity_gate` (PR-A) now does.
- **Verdict:** 🔴 **LOOSEN** — adopt same pattern as PR-A: blocks become HALF_SIZE warnings unless they are existential (penny, catastrophic news, missing entry).

## Test gaps
- No test for cumulative effect of all 5 blocks running sequentially (which is what production does).
- No test asserting silent-removal failure mode (the F2-7 visibility gap).

## Summary
- LOOSEN: 4 (F2-1, F2-2, F2-3, F2-7) + module-level pattern shift (F2-8)
- KEEP: 4 (F2-4, F2-5, F2-6, plus the audit-log mechanism itself)
- LOC delta: ~50 lines

## ⚠️ This is the file most likely causing your "agent finds nothing" problem.
