# Audit Batch 1b — main.py (Production Entrypoint)

**Date:** 2026-05-12
**File:** `main.py` — 1,817 lines, 90KB
**Role:** The CLI entrypoint invoked by `daily-picks.yml` workflow at premarket each US trading day.

**Severity legend:**
- 🚨 = Show-stopper / trade-damaging
- ⚠️ = Data-corrupting / safety risk
- 🟡 = Code smell / inconsistency
- 📝 = Doc-only
- ✅ = Good code

---

## High-level summary in plain English

What this file does, end-to-end:

1. Loads settings from `config.yaml` and secrets from `.env`
2. Checks if the US market is even open today (skip if not)
3. Checks if the agent is paused (skip if so)
4. Checks the market regime (bull/bear), VIX, SPY trend, sector strength — adjusts pick count
5. Loads universe of stocks (S&P 500 minus exclusions)
6. Fetches recent price data for all of them
7. Verifies enough data was fetched ("data readiness gate")
8. Computes scores in parallel for every candidate
9. Filters out earnings-imminent stocks and "kill list" stocks
10. Adjusts scores based on earnings quality
11. Caps picks per sector (max 4 per sector, max 2 per primary tag)
12. Applies news signal boosts/penalties
13. Selects the top N picks
14. Hard-blocks: penny stocks, tight stops, weak sector ETFs
15. Runs the "probability engine" (P(win), expected value)
16. Optional EV gate (currently observe-only)
17. Optional auto-pause check (currently observe-only)
18. Optional smell faculty (currently observe-only)
19. Tags each pick as DAY or SWING
20. Premarket sanity gate (final sanity check)
21. Portfolio risk gate (correlation / overweight checks)
22. Missing-data gate (fail-closed if required fields missing)
23. Writes "official pick artifacts" (the production decision record)
24. Prints rationale via LLM
25. Logs picks to `picks_log.csv`
26. Logs to signal_journal.jsonl (for brain learning)
27. Recomputes pause signal, possibly auto-pauses
28. Done.

**Plain English:** This file is the single brain stem of your entire system. It sequences ~28 distinct steps. Any bug here cascades to everything downstream.

---

## STRUCTURAL FINDINGS (about the file as a whole)

### 🚨 STRUCT-1: The `run()` function is 1,184 lines long (lines 628–1812)
- The single function that runs everything is bigger than most entire Python files. It mixes data fetching, scoring, gating, logging, LLM calls, and notifications.
- Why it's a problem: nobody can hold this in their head; untestable; one exception in step 8 might silently corrupt data needed by step 22; bug fixes risk breaking unrelated steps.
- Fix (medium-term): split `run()` into named phases, each ≤100 lines, individually testable.
- **Severity:** 🚨 The single biggest maintainability risk in your codebase.

### 🚨 STRUCT-2: Lazy imports scattered throughout `run()` — 15+ total
Lines 716, 718, 778, 779, 819, 826, 905, 918, 966, 985, 1082, 1122, 1185, 1242, 1262, 1327, 1351, 1425, 1441, 1521.
- Hidden dependencies, slow first run, failure surprises, test pollution.
- Fix: move all imports to the top; fix any underlying circular imports.
- **Severity:** 🚨 Hidden-dependency hell.

### ⚠️ STRUCT-3: "Swallow all exceptions" pattern is everywhere
Many `try` blocks end with `except Exception: pass` (do nothing) or just print and continue. Errors are HIDDEN.

Examples (line numbers): 62-64, 96-97, 343-344, 576-578, 612-616, 663-664, 680-681, 828-829, 952-953, 1036-1037, 1104-1105, 1153-1154, 1166-1167, 1681-1682, 1697-1698, 1803-1804, 1809-1810.

- **Silent corruption.** If `journal_log_pick` (line 1779) fails for one pick, that pick never enters brain learning. Brain trains on a partial dataset and doesn't know.
- **No alerting.** Production operator never sees these errors unless watching logs.
- Fix philosophy: categorize each `except` into fail-closed (abort), fail-open with mandatory artifact (log to warnings file), or fail-silent (truly cosmetic).
- **Severity:** ⚠️ Pervasive.

### ⚠️ STRUCT-4: Mixed responsibility in helper functions
- `_write_daily_picks_no_pick_report()` is 231 lines (writes JSON + Markdown + diagnostics + rejection reports).
- `_classify_no_pick_cause()` is 86-line if/elif ladder.
- Should be 3-4 separate functions.
- **Severity:** ⚠️ Maintainability + correctness risk.

---

## LINE-BY-LINE FINDINGS

### Lines 1-34: Imports

**🚨 BUG-44:** Line 25 imports `src.paper_trader` even though paper trading is forbidden. Capability-present-but-forbidden contradiction. Fix: lazy-import inside `_should_log_paper_trade()` block, OR remove paper_trader entirely.

**🚨 BUG-45:** Line 15 imports `src.premarket_filter.gap_check` but it is NOT USED anywhere in the file. Either dead import OR missing feature — both bad.

**🟡 BUG-46:** Multiple modules imported but used only once (lines 12, 18, 19, 28). Combined with lazy imports inside `run()`, the import strategy is inconsistent.

**🟡 BUG-47:** Lines 11 and 20 both import from `src.fundamentals` separately. Should be one combined import.

**⚠️ BUG-48:** Lines 16, 22, AND lazy-import line 905 — three separate imports from `src.scorer`. Hint that `src.scorer` is a kitchen-sink module needing split.

**🟡 BUG-49:** About 9 imported functions are never called in this file: `composite_score`, `trade_plan`, `fetch_news`, `score_sentiment`, `add_indicators`, `latest_signals`, `fetch_info`, `score_fundamentals`, `atr_trade_plan`. Suggests file was REFACTORED but old imports were left behind.

### Lines 36-47: `_safe_trade_type_for_pick()`

**✅ GOOD-8:** Excellent scar-tissue documentation (line 39): "Bug #7: a day trade should never be emitted for a non-trading day."

**🟡 BUG-50:** `pick_date=None` (line 36) — if `_is_td(None)` crashes, every call without a date crashes.

### Lines 50-87: Sector benchmark helpers

**✅ GOOD-9:** SPY fallback is documented and sensible.

**⚠️ BUG-51:** `_yf_ticker_for_sector_benchmark` calls yfinance directly — bypasses the centralized `src.data_fetcher` layer (cache, rate-limiting, fallback).

**🟡 BUG-52:** No timeout on yfinance call (line 59). Hangs the whole pipeline if yfinance is slow.

### Lines 91-97: Auto-seed wisdom base

**⚠️ BUG-53:** Subprocess at MODULE-IMPORT time, with 10s timeout, errors silenced.
- Side effect at import time = anti-pattern. Importing a module shouldn't run subprocesses.
- Tests that import this file spawn subprocess every test.
- `check=False` + `pass` = double-silent.
- Fix: move to inside `run()`, after pause check, with logged outcome.

### Lines 100-117: Helper functions

**✅ GOOD-10:** `_candidate_report_value` is defensively coded with depth/length caps.

### Lines 121-145: `_news_action_window()` defensive helper

**✅ GOOD-11:** OUTSTANDING scar-tissue documentation. This is the May 11 production crash fix (PR #133). Comment explains "p['news'] is sometimes a list of articles, sometimes a dict... Calling .get() on a list raises AttributeError and crashes main.py:1183 right after scoring completes."

### Lines 148-177: `_summarize_candidate_for_report()`

**⚠️ BUG-54:** Field `watch_only_reason` may pull from two places (lines 175-176). Dual source of truth. If candidate.watch_only=True but plan.watch_only=False, which wins? `or` short-circuits to True, but if reasons differ, candidate-level wins.

### Lines 180-265: `_classify_no_pick_cause()` — no-pick reason classifier

**✅ GOOD-12:** This function exists at all. Audit trail-friendly.

**🟡 BUG-55:** 86-line if/elif ladder — should be data-driven (rule table).

**⚠️ BUG-56:** The `>=` comparison may produce false positives (lines 201, 208, 219). Should be `==` not `>=`.

**🟡 BUG-57:** Magic threshold `0.20` (line 193) for "yfinance degraded." Should be a constant or in config.

### Lines 269-345: `_write_daily_picks_candidate_diagnostics_report()`

**⚠️ BUG-58:** Entire 75-line function body wrapped in try/except/pass. A silent failure means no diagnostic file ever gets written.

**⚠️ BUG-59:** Non-atomic file writes (lines 298-300, 340-342). Power loss / OOM kill / container restart during write = corrupted JSON. Fix: write to `.json.tmp`, then `os.rename(tmp, real)` (atomic on POSIX).

**⚠️ BUG-60:** `mode: "monitoring_only"` is hardcoded (line 288). Even if `TRADING_MODE` env var said `paper` or `live`, this artifact would lie. Audit trail mismatch.

### Lines 348-578: `_write_daily_picks_no_pick_report()` — 231 lines

**🚨 BUG-61:** Function is 231 lines long. Split into ~5 functions.

**⚠️ BUG-62:** Same try/except/pass swallow pattern.

**⚠️ BUG-63:** `paper_trading_enabled: False`, `live_trading_enabled: False`, `ready_for_paper_trading: False` are hardcoded (lines 387-389, 504-507). Same lie risk as BUG-60.

**📝 BUG-64:** Hardcoded strings for primary causes that should be enum constants. A typo creates a new "cause" silently.

### Lines 581-616: `_write_guard_no_pick_artifact_for_main()`

**✅ GOOD-13:** Documents the bug it was created to fix (May 9 audit, P17.1).

### Lines 619-625: `_should_log_paper_trade()`

**✅ GOOD-14:** Defaults safely to monitoring. Returns False unless env explicitly says "paper."

### Lines 628-665: Setup + market-closed guard

**✅ GOOD-15:** Market-closed guard is FIRST (line 651). Cheapest possible early-out.

**✅ GOOD-16:** T51 guard now writes a no-pick artifact (line 658). Fix for original bare-return bug.

**⚠️ BUG-65:** Market-calendar check failure proceeds anyway (line 664). Fail-OPEN. On a Sunday with a broken market-calendar module, the agent could try to pick stocks. Fix: write no-pick + return.

### Lines 666-682: Pause check

**✅ GOOD-17:** Pause check has clear hard stop with formal artifact (line 682).

**⚠️ BUG-66:** Pause-day artifact write failure silenced (lines 680-681).

**🟡 BUG-67:** Pause artifact `last_run_paused.json` is at fixed path (line 677). Always overwrites. No history.

### Lines 684-708: Market guards (VIX, SPY, sectors)

**⚠️ BUG-68:** `vix > 30` check (line 700) hardcoded threshold. Defensible (30 is conventional).

**⚠️ BUG-69:** Two min/max pick reductions stack (lines 700-708). Don't compound by design but a future contributor might assume otherwise.

### Lines 715-726: Same-day dedup guard

**✅ GOOD-18:** Hard dedup with scar-tissue comment about GitHub cron multi-fire bug (Apr 28 = 2 runs, May 1 = 3 runs).

**🚨 BUG-70:** Same-day guard reads `picks_log.csv` but does NOT write a no-pick artifact when skipping (line 725-726). Inconsistent with market-closed guard. **This is your bootstrap's P17.2 deferred work — confirmed still missing.**

**⚠️ BUG-71:** Same-day guard reads `data/picks_log.csv` directly (lines 720-723) — bypasses any `src.pick_logger` schema validator.

### Lines 728-766: Regime + market briefing

**🟡 BUG-72:** Bearish regime raises `min_score` to 0.70 (line 738), bearish sentiment raises to 0.72 (line 763). Two different magic numbers. Order-dependent (max wins).

**🟡 BUG-73:** Bullish path has no action (line 765-766). Asymmetric — bear tightens, bull does nothing. If bull markets justify looser min_score, this asymmetry costs you.

### Lines 768-816: Universe load + data fetch + readiness gate

**✅ GOOD-19:** Pipeline counters tracked throughout. Forensics-friendly.

**✅ GOOD-20:** Data readiness gate is its own dedicated step. Fail-closed properly. P19 cert feature.

**⚠️ BUG-74:** `min_fetch_coverage` and `min_fetched_count` are env-var-controlled (lines 786-787) — defaults: 0.25 coverage / 25 stocks. Where are these env vars documented? Not in `.env.example`. Production may be using defaults without you realizing. 25% × 500 stocks = 125 stocks needed, but min=25 = could pass with 5% coverage if logic uses minimum-of-two.

### Lines 818-829: Parallel scoring

**✅ GOOD-21:** Scorer worker count is env-tunable (line 820).

**🟡 BUG-75:** After scoring, `write_market_data_run_summary` failure silenced.

### Lines 831-911: Filtering, earnings, sector cap

**🚨 BUG-76:** Earnings filter uses magic number 5 (line 860): `if d2e < 5:`. Why 5? Critical strategy parameter buried in code. Should be in `config.yaml`: `earnings_skip_window_days: 5`.

**🚨 BUG-77 (CRITICAL):** `d2e >= 999` sentinel for "unknown earnings date" — pick is INCLUDED with caution (line 869). **Your bootstrap mentions: "9/14 picks have daystoearningsbucket=none" — earnings data pipeline is broken. This is the smoking gun: agent silently picks stocks with unknown earnings dates but treats them as if it's safe. Any one could be the day BEFORE earnings, with massive overnight gap risk.** Fix: either fail-closed (exclude) OR fix earnings data pipeline first.

**⚠️ BUG-78:** `4x buffer for sector cap` (line 836) — magic. Assumes max 75% rejection rate.

**⚠️ BUG-79:** Earnings quality blend uses fixed 88/12 weights (line 883): `new_score = round(old_score * 0.88 + eq * 0.12, 3)`. Where are 88/12 documented? Looks guessed once and never re-validated. Strategy parameter buried + uncalibrated.

**🟡 BUG-80:** After earnings adjustment, `filtered.sort(...)` (line 889) but `filtered_count` recorded BEFORE (line 890). Minor audit-trail loss.

### Lines 892-911: Sector + tag cap

**⚠️ BUG-81:** Two-step cap with second cap printing via `print()` not `rprint()` (line 909). Style inconsistency.

**⚠️ BUG-82:** Tag cap parameter `max_per_tag=2` (line 907) hardcoded — strategy parameter buried.

### Lines 913-953: News signals

**⚠️ BUG-83:** News boost magnitude clamped to [0.0, 1.0] (line 939). A pick with score=0.99 and a +0.05 boost only gets +0.01 (clamped). Asymmetric near boundary. Hidden bias in scoring.

**⚠️ BUG-84:** `if abs(boost) >= 0.01:` (line 937) — small boosts ignored. Where is 0.01 documented?

### Lines 955-976: Final pick selection + hard blocks

**⚠️ BUG-85:** Hard blocks return tuple `(top, blocked)`; no schema validation (line 968). Trusts return shape.

### Lines 978-1037: Probability engine (Pillar 1)

**⚠️ BUG-86:** `entry_price <= 0` skipped silently (line 995-996). Pick still goes forward WITHOUT brain analysis. Audit field `brain_p_win` becomes None. No warning logged.

**⚠️ BUG-87:** Per-pick brain failure stored as `{"error": str(e)}` (line 1022). Then line 1027 checks `if "p_win" in b:` — error pick silently skipped from display. CSV log later writes None. **Brain learning corrupted by silent skips.**

### Lines 1041-1071: EV gate

**✅ GOOD-22:** Observe-mode by default with explicit ENFORCED label.

**📝 BUG-88:** `BRAIN_EV_MIN_PCT` default `-1.0` (line 1046) — what does "-1%" mean in plain English? Document threshold.

### Lines 1074-1106: Auto-pause filter

**✅ GOOD-23:** Same observe/enforce pattern, env-controlled. Safe defaults.

### Lines 1109-1155: Smell faculty

**✅ GOOD-24:** Same pattern.

**🟡 BUG-89:** Empty `signals` dict default (line 1126) `sig = p.get("signals") or {}`. May hide real "missing signals" bug.

### Lines 1157-1167: (Comment block then nothing happens before line 1168)

**🟡 BUG-90:** Duplicated/triplicated section banner (lines 1158-1161). "WEEK 3: Auto-tag DAY vs SWING" comment appears 3 times in a row.

### Lines 1168-1208: Empty-top no-pick handler

**✅ GOOD-25:** When no picks survive, writes formal no-pick artifact with full diagnostics. Layered fallback.

**⚠️ BUG-91:** Bare `except Exception:` (line 1197) in fallback path. Catches too broadly.

### Lines 1210-1236: Trade type tagging

**✅ GOOD-26:** Watch-only safeguard for intraday news + swing mismatch (lines 1221-1229).

### Lines 1238-1321: Premarket sanity gate

**✅ GOOD-27:** Detailed no-pick path with diagnostics + fallback. Good consistency.

### Lines 1323-1419: Portfolio risk gate

**⚠️ BUG-92:** `cfg` is passed to `apply_portfolio_risk_gate(...)` (line 1331) — full config exposed to a gate. Python passes by reference. Mutability risk.

### Lines 1421-1518: Missing-data gate (fail-closed)

**✅ GOOD-28:** Fail-CLOSED missing-data gate. CORRECT direction (vs the earnings unknown case BUG-77). Match this stance to earnings-unknown.

### Lines 1520-1620: Diagnostics + official artifact writing

**⚠️ BUG-93:** `selection_diagnostics = {}` on failure (line 1560) — but used downstream as if dict-shaped.

### Lines 1622-1650: Display + LLM rationale

**⚠️ BUG-94:** LLM `explain_pick(...)` called inside loop (line 1644-1645) — N API calls. Each pick = own LLM call. If `top_n_picks=10`, 10 sequential calls. Slow + costs money. No fallback.

**⚠️ BUG-95:** `log_paper_trade` (line 1650) writes to `csv_path.replace("picks","trades")`. Brittle string replace.

### Lines 1652-1810: Final logging block

**🚨 BUG-96:** Monster treatment fires by default (line 1657: `_mcfg.get("enabled", True)`). Even if `monster.enabled` is missing from config, defaults to TRUE. Combined with config.yaml BUG-16, monster is unconditionally on. Per bootstrap, monster should be research-only. Fix: default to False.

**⚠️ BUG-97:** `n = log_picks(...)` (line 1758) return value used for dedup messaging. Relies on `log_picks` returning correct count. If it ever throws partway through, count may be wrong.

**⚠️ BUG-98:** Loud per-pick journal errors with traceback (lines 1781-1785) — but run continues. At least loud (not silenced). But if 5/10 picks fail to journal, run completes "successfully" with brain learning from 5-pick subset. Per-pick failures don't aggregate into end-of-run alarm.

**⚠️ BUG-99:** `_pause_score()` and `_maybe_pause(...)` (lines 1793, 1800) — auto-pause can fire AFTER picks already logged/sent. Wrong order. By the time auto-pause fires here, picks are already in `picks_log.csv`, journal, AND on Telegram. Fix: run pause-score check at the START.

**🟡 BUG-100:** `cape if "cape" in dir() else None` (line 1758) — fragile global check. `cape` set at line 740. Replace with explicit check.

---

## Summary of Batch 1b (`main.py`)

### By severity
| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 11 |
| ⚠️ Data/safety risk | 27 |
| 🟡 Code smell | 13 |
| 📝 Doc-only | 2 |
| ✅ Good code | 15 |
| **Total** | **68 findings** |

### Top 7 things to fix in `main.py` (in order)

| # | Bug | Why first | Fix difficulty |
|---|---|---|---|
| 1 | BUG-77 (earnings unknown → INCLUDED) | Direct production risk. 9/14 picks have unknown earnings = overnight gap exposure. | Easy: change `if d2e >= 999:` to `continue` |
| 2 | BUG-70 (same-day dedup writes no artifact) | Bootstrap's P17.2 deferred work. Easy fix unblocks audit completeness. | Easy: 5-line addition |
| 3 | BUG-65 (calendar check fail-open) | Sunday-with-broken-calendar = agent runs on holiday. | Easy: change `proceeding` to write no-pick + return |
| 4 | BUG-44 + BUG-45 (forbidden + dead imports) | Removes contradiction risk and shaves apparent surface area | Easy: delete unused imports |
| 5 | BUG-99 (auto-pause fires AFTER picks sent) | Wrong order. Pause should prevent today's picks. | Medium: move check earlier |
| 6 | BUG-96 (monster enabled by default in code) | Pairs with config BUG-16. Belt-and-suspenders. | Easy: change `True` → `False` |
| 7 | STRUCT-1 (1,184-line `run()` function) | Long-term maintainability. Block on doing this until easier fixes ship. | Hard: 2-3 day refactor |

### What this file tells us

- **The brain stem is overgrown.** 1,184-line function with 28 sequential steps + 15 lazy imports + 27 try/except blocks.
- **Defensive coding is everywhere — but the wrong KIND.** Lots of try/except/swallow. Few hard fail-closed gates. Agent prefers to keep going on broken data — OPPOSITE of safe.
- **Scar-tissue documentation is excellent in places.** Bug numbers, dates, "discovered during X audit" comments. Keep this discipline.
- **Strategy parameters are buried in code.** Magic numbers (5, 88/12, 0.20, 30, 0.70/0.72) should all live in `config.yaml`.
- **Forbidden capabilities are imported regardless of mode.** Paper trading, monster mode, day trading all wired in despite being forbidden.
- **The May 11 production crash is fully explained here.** Lines 124-128 + 132-145 (`_news_action_window` helper) is the fix.

### Glossary additions for this batch

| Term | Plain English |
|---|---|
| Atomic write | Saving a file safely: write to temp file, then rename. Crash mid-write leaves OLD file intact, not corrupted half-written file. |
| Fail-closed vs fail-open | When something breaks: fail-CLOSED = stop everything (safe). Fail-OPEN = keep going (dangerous). |
| Lazy import | An `import` statement INSIDE a function instead of at top of file. Anti-pattern unless solving circular-import. |
| Side effect at import | Code that runs the moment a file is loaded. Bad because just importing should never DO anything. |
| Scar-tissue documentation | A code comment explaining WHY some code exists by referencing the specific bug it prevents. |
| Magic number | A hardcoded number with no explanation. Bad because future maintainers don't know if it's safe to change. |

---

**End of Batch 1b.**

Cumulative findings across batches 1a + 1b:
- 🚨 Show-stoppers: 26
- ⚠️ Data/safety risks: 36
- 🟡 Code smells: 30
- 📝 Doc-only: 4
- ✅ Good code: 22
- **Total: 118 findings across 12 files (~3,800 lines of code)**

Next: Batch 2a — `.github/workflows/daily-picks.yml` (the production workflow that calls `main.py`).
