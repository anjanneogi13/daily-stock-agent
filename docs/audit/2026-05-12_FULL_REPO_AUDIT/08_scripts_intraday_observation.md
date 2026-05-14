# Audit Batch 3d — Scripts: Intraday + Observation Pipeline (12 files)

**Date:** 2026-05-12
**Files (12):** intraday_scanner, intraday_monitor, intraday_news, generate_late_daily_ideas, daily_watch_only_learning_report, backtest_opening_range_observations, review_opening_range_observations, daily_observation, monitoring_readiness, daily_execution_report, record_daily_picks_run_status, premarket_check

**Total:** ~2,750 lines

**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

## High-level summary in plain English

These 12 files are the **observation/evidence-building pipeline** — the "watch-only universe" that runs in parallel with Lane 1 official picks. None of these is allowed to create a real pick or paper trade. They generate evidence for future "is this strategy ready to go live?" gates.

Three families:

Family A — Intraday Scanning + Monitoring (3 files):
- intraday_scanner.py (the engine — opening-range scan, momentum scan, observation persistence)
- intraday_monitor.py (the orchestrator — runs every 30min, monitors open picks, scans for new opps)
- intraday_news.py (small Finnhub news fetcher with materiality classifier)

Family B — Watch-Only Idea Generation + Reporting (3 files):
- generate_late_daily_ideas.py (post-cutoff "we missed the window" fallback)
- daily_watch_only_learning_report.py (cross-artifact summary)
- premarket_check.py (tags day's picks with SAFE/HALF/SKIP/WATCH)

Family C — Observation Backtest + Execution X-ray (3 files):
- backtest_opening_range_observations.py (read-only outcome join over OR observations)
- review_opening_range_observations.py (read-only summary)
- daily_observation.py (lesson-extraction logger)

Family D — Operational Status + Readiness (3 files):
- daily_execution_report.py (full intraday X-ray of each pick — TP/SL hits, MFE/MAE)
- monitoring_readiness.py (gate-check: are we ready for paper trading?)
- record_daily_picks_run_status.py (workflow observability — JSONL audit log)

---

## CROSS-CUTTING FINDINGS

### ✅ X-IO1: Strong observe-only safety contract
Almost EVERY file in this batch declares "observe-only / monitoring-only / no paper trading / no live trading" in docstring AND in artifact payloads. Examples:
- intraday_scanner.py:259-263 (per-bar artifact safety dict)
- intraday_scanner.py:438-441 (refresh function safety dict)
- generate_late_daily_ideas.py:339-343
- daily_watch_only_learning_report.py:250-258
- review_opening_range_observations.py:150-153
- backtest_opening_range_observations.py:196-198
- monitoring_readiness.py:151 ("Paper trading remains forbidden until all gates pass")
- record_daily_picks_run_status.py:164-165

Plain English: Every artifact this batch produces SAYS "I am not a buy instruction." Excellent.
Severity: ✅ Best-in-class observability discipline.

### 🚨 X-IO2: yfinance dependency is fragile and silent
Multiple files use `try: import yfinance as yf except: yf = None`:
- intraday_scanner.py:11-14 (returns {} on failure)
- generate_late_daily_ideas.py:27-30 (returns {} on failure)
- daily_execution_report.py:17-21 (sys.exit(0) on failure!)
- premarket_check.py:16-19 (sys.exit(0) on failure!)
- build_stock_stats.py (Batch 3b) same pattern

Plain English: yfinance is a third-party library with NO SLA, NO documented rate limits, and a history of silent breakage when Yahoo changes their API.

Different files handle missing yfinance DIFFERENTLY:
- daily_execution_report exits 0 (workflow sees success)
- premarket_check exits 0 (workflow sees success)  
- intraday_scanner returns empty quote (downstream sees zero candidates)
- generate_late_daily_ideas returns empty market context (idea has no quote)

Why a problem: When Yahoo breaks (and it WILL), the agent silently shifts from "real evidence" to "no evidence" with NO loud signal. You'd find out days later via "no picks have intraday data."

Fix: A single src/quote_provider.py with proper failure classification (provider_failure_taxonomy is already imported in some files — apply EVERYWHERE).
Severity: 🚨 Single-vendor silent dependency.

### ⚠️ X-IO3: Date computation drift continues
Same as Batches 3b/3c. In this batch:
- intraday_monitor.py:46 `TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")` — UTC
- intraday_scanner.py:179 default UTC date for opening_range_observation_path
- intraday_scanner.py:244 default ET date for opening_range_bar_path
- intraday_scanner.py:452 default ET date for momentum observations
- daily_execution_report.py:24 local time
- daily_observation.py:11 local time
- premarket_check.py:21 local time
- record_daily_picks_run_status.py: ET (correct)
- generate_late_daily_ideas.py: ET (correct)
- daily_watch_only_learning_report.py: ET (correct)

Plain English: Within ONE FILE (intraday_scanner.py), opening-range OBSERVATIONS use UTC date but opening-range BARS use ET date. At 22:00 UTC = 18:00 ET (same day) it works. Near midnight UTC, observations and bars land in DIFFERENT date buckets and the backtest can't join them.

Severity: ⚠️ Latent off-by-one across artifact joins.

### ⚠️ X-IO4: load_jsonl reimplemented in 4 files (again)
- intraday_scanner.py:340-356 `_load_opening_range_observation_rows` (returns rows + bad count)
- intraday_scanner.py:273-287 `_load_existing_opening_range_bar_rows` (rows only)
- daily_watch_only_learning_report.py:39-57 `load_jsonl` (returns rows + invalid)
- backtest_opening_range_observations.py:72-85 `load_jsonl` (rows + invalid)
- review_opening_range_observations.py:59-86 `load_observations` (slightly fancier)

Plain English: 5 distinct JSONL loaders, all doing 95% the same thing.
Severity: ⚠️ Same DRY violation noted in Batches 3a/3b. Batch 3 has now produced ~10 implementations of "load JSONL".

### 🚨 X-IO5: Module-level side effects galore
Files with significant logic at MODULE-IMPORT time (not in main):
- intraday_monitor.py:26-40 (market calendar guard at import — calls sys.exit(0)!)
- daily_execution_report.py: ENTIRE file is module-level (lines 24-211) — runs on import
- daily_observation.py: ENTIRE file is module-level (lines 11-127) — runs on import
- premarket_check.py: ENTIRE file is module-level (lines 21-133) — runs on import

Plain English: Cannot import these for testing. `import scripts.daily_execution_report` will:
1. Read sys.argv[1]
2. Try to fetch yfinance data
3. Call sys.exit() if no data
4. Print 200 lines of report to stdout
…all during the import.

Why a problem: Tests can't run, refactors can't reuse helpers, REPL exploration impossible.
Fix: wrap in `def main(): ...` and `if __name__ == "__main__": main()`.
Severity: 🚨 Test-hostile + reuse-hostile.

### ⚠️ X-IO6: Two competing intraday scanners ("opening_range" vs "momentum")
intraday_scanner.py implements BOTH:
- Opening-range breakout scan (preferred, run first)
- Generic momentum scan (legacy, runs second)

Both produce candidates. But:
- Opening-range observations go to `opening_range_observations_*.jsonl`
- Momentum observations go to `intraday_momentum_observations_*.jsonl`
- Dedupe fingerprints are SHARED (`sent_alerts` set)

Plain English: Two scanners share dedupe state but write different artifacts. If a ticker is detected by BOTH on the same day (early opening-range hit + later momentum hit), the second is suppressed by dedupe but you don't see WHY.
Severity: ⚠️ Confusing semantics; loss of visibility into "would have alerted."

### ⚠️ X-IO7: Hardcoded watchlist in scanner
intraday_scanner.py:21-34 — `DEFAULT_WATCHLIST` of ~50 tickers hardcoded.
Plain English: Same drift problem as build_stock_stats.py (Batch 3b BUG-SS1). Adding NVDA-class names = code change.
Override exists (`data/watchlist.txt`) but defaults are stale.
Severity: ⚠️ Drift.

### 🟡 X-IO8: `get_live_quote` doesn't return RSI but caller assumes it might
intraday_monitor.py:191-194 `live.get("rsi")` — but `get_live_quote` (intraday_scanner.py:42-68) NEVER computes RSI.
Plain English: Adaptive TP/SL logic reads `live.get("rsi")` which is always None. Adaptive features partially broken.
Fix: either compute RSI in get_live_quote or remove the consumer logic.
Severity: ⚠️ Dead-feature pretending to work.

### ⚠️ X-IO9: Bar-volume timing assumption brittle
intraday_scanner.py: opening-range = 6 × 5min bars (hardcoded inside src/opening_range_scanner per Batch 3b notes). intraday_monitor.py walks bars with no time check.
Plain English: assumes 5-minute bar interval; if yfinance returns different interval (unlikely but possible), logic silently produces wrong width/volume.
Severity: 🟡

### 🟡 X-IO10: print() everywhere instead of logging
Every file uses `print(...)` for status. No log levels, no structured logging, no rotation.
Plain English: workflow logs are noisy and unfilterable. Cannot suppress info-level for production runs.
Severity: 🟡 Operability.

### ✅ X-IO11: Atomic-style append for JSONL artifacts
Most JSONL writes use `with out.open("a") as f: f.write(json.dumps(...) + "\n")` — the OS-level append is atomic for small writes (<4KB on Linux). Good pattern.
Severity: ✅ Correct for JSONL.

But: write_opening_range_bar_artifact (intraday_scanner.py:294-337) does READ-MODIFY-WRITE (merge_existing), which is NOT atomic. Race risk if two monitor instances run.

---

## PER-FILE FINDINGS

### 1. intraday_scanner.py (743 lines) — THE INTRADAY ENGINE

What it does: Opening-range breakout detection + momentum scan + observation persistence + retention refresh + run-status logging. Largest file in batch.

✅ GOOD-IS1: Excellent multi-artifact split (observations / bars / run_status / momentum) with helper paths. Clean.
✅ GOOD-IS2: NEW_OPPORTUNITY_CUTOFF_MINUTES = 15:15 ET (line 184) — explicitly suppresses late-day opportunity creation. Smart.
✅ GOOD-IS3: opening_range_bars_match_session check (line 229-239) — refuses to emit observations from previous session's bars. Defensive.
✅ GOOD-IS4: refresh_opening_range_bar_artifacts_for_observations (lines 359-442) — repairs retention gap where candidate is observed before enough forward bars exist. Genuinely sophisticated.
✅ GOOD-IS5: Per-row safety dict in every observation (mode, watch_only, paper_trading_enabled, live_trading_enabled, official_pick_stats_mutated). Auditable.

🚨 BUG-IS1: Line 142-146 `detect_opening_range_breakout` from src.opening_range_scanner — this is hidden coupling to source, not visible at import time. If src.opening_range_scanner changes signature, breaks silently.
- Severity: ⚠️ Cross-module contract.

🚨 BUG-IS2: Line 17-18 imports `from src.opening_range_scanner` and `from src.provider_failure_taxonomy` — but the import block is BEFORE sys.path adjustment. If this file is invoked from a directory that doesn't have `src` in sys.path (i.e., not from repo root), import fails immediately at script start.
- Plain English: hardcoded assumption that cwd = repo root.
- Severity: ⚠️ Workdir-fragility.

⚠️ BUG-IS3: Line 51 `last_close = float(hist["Close"].iloc[-1])` — uses last bar of 5-day intraday history. If market is OPEN, this is the latest delayed quote (~15min lag for free yfinance). If market is CLOSED, this is yesterday's close. Caller has no way to distinguish.
- Severity: ⚠️ Stale-quote risk.

⚠️ BUG-IS4: Line 70-83 `score_opportunity` formula:
- Hardcoded magic numbers (50 base, +4×change capped at 25, +10 per vol tier, +15 catalyst).
- Same "magic ladder" issue as BUG-WO4 in Batch 3b.
- Severity: ⚠️ Brain-irrelevant heuristic.

⚠️ BUG-IS5: Line 60-65 `vol_ratio` divides today_vol by avg_vol of last 20 days. But today_vol from a partial intraday session vs full-day historical average is APPLES-TO-ORANGES.
- Plain English: at 10:00 ET, today's volume is naturally low; vol_ratio falsely reads 0.3 even on normal days.
- Fix: scale by trading-hours-elapsed.
- Severity: 🚨 Fundamentally wrong vol_ratio metric.

⚠️ BUG-IS6: Line 712-715 `fp = f"NEW|{ticker}|{int(score/10)}"` — momentum dedupe fingerprint. If the same ticker scores 71 on first run and 79 on second, both produce fp `NEW|TICK|7`. But if it scores 79 then 81, two different fps emitted. Inconsistent dedupe granularity.
- Severity: 🟡 Edge case.

⚠️ BUG-IS7: Line 320-322 `merged[key] = row` — when merging existing+new bars by timestamp key, NEW row OVERWRITES existing. If existing was correct and new is corrupted, lost forever. Should prefer first-write-wins.
- Severity: 🚨 Data corruption window.

⚠️ BUG-IS8: Line 155-159 `score = 75 + min(float(result.get("breakout_pct") or 0) * 3, 15)` — opening-range candidates start at 75 base score. Hardcoded. No basis. (Compare: momentum starts at 50 and might reach 75 organically.) Different scales not normalized for comparison.
- Severity: 🟡 Score-scale inconsistency.

🟡 BUG-IS9: Line 278-287 `_load_existing_opening_range_bar_rows` reads ENTIRE file into list with .splitlines(). Same memory issue as Batch 3b BUG-CL2.

🟡 BUG-IS10: Line 336 `f.write(json.dumps(row, sort_keys=True) + "\n")` inside `with out.open("w")` — overwrites whole file. If interrupted mid-write, file truncated.
- Atomic-write pattern from backfills NOT applied here.
- Severity: ⚠️ Mid-write corruption (already noted as X-AV6 family).

🟡 BUG-IS11: `_bar_ts_to_et` line 200-216: graceful fallback to `datetime.now()` on parse failure. Silent. Two consecutive bars with bad ts could BOTH map to same "now" and dedupe-collide.

### 2. intraday_monitor.py (360 lines) — ORCHESTRATOR (every 30min)

What it does: Loads today's pending picks, monitors live prices, fires SL/TP closes to CSV, computes adaptive trailing stops, scans for new opps, writes intraday alert markdown.

✅ GOOD-IM1: Bug-fix history embedded in docstring (line 99-117) — explains why _close_pick_in_csv exists.
✅ GOOD-IM2: load_todays_picks falls back to "most recent date" if today's missing (lines 71-77) — handles weekend/holiday/replay.
✅ GOOD-IM3: idempotency comment on _close_pick_in_csv (lines 107-109) — documents that caller must filter pending. Defensive.
✅ GOOD-IM4: Three-layer safety: trailing_stop + adaptive_tp + adaptive_sl. Each wrapped in try/except so one failure doesn't block others.
✅ GOOD-IM5: Run-status events at start, skip-no-picks, completed (lines 297-349) — proper observability.

🚨 BUG-IM1: Line 26-39 market calendar guard runs at MODULE IMPORT TIME and calls sys.exit(0). Same as X-IO5.

⚠️ BUG-IM2: Line 46 `TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")` — UTC date. But picks_log uses local pick_date. At 04:00 UTC = 23:00 ET (previous day), TODAY=2026-05-13 but yesterday's picks are pick_date=2026-05-12. load_todays_picks falls through to "use last available date" — but writes evaluation under wrong TODAY.
- Severity: 🚨 Off-by-one-day evaluation drift.

⚠️ BUG-IM3: Line 138-263 `monitor_existing_picks` is 125 lines doing everything (price check, trailing SL, adaptive TP, adaptive SL, news, alert dedupe). Untestable monolith.
- Severity: 🟡 Refactor needed.

⚠️ BUG-IM4: Line 174 `flags.append(("hit_sl", ...))` then line 175-176 `_close_pick_in_csv(...)` — closes the pick, but then continues to check TP, vol_spike, trail_raise. After SL hit, the subsequent flags are MEANINGLESS but still added to alert.
- Plain English: User sees "hit_sl + halfway_tp + vol_spike" alert; only the first matters.
- Severity: 🟡 Confusing alert.

⚠️ BUG-IM5: Line 234-243 `should_tighten_sl` — only updates SL if `sl_updates`. But if sl_updates is set and `should_t` is False but peak_rsi changed, only peak_rsi is written. OK.
- BUT: line 239 `sl = new_sl_t` is INSIDE the `if should_t:` branch but line 168 already set `sl = new_sl` from trailing. After this block, sl could be EITHER trailing-raised OR adaptive-tightened. Subsequent halfway_tp / TP checks use this final sl. Should be deliberate; comment doesn't say.
- Severity: 🟡 Behavior unclear from code.

⚠️ BUG-IM6: Line 245-250 `fetch_recent_news` called for EVERY pick on EVERY 30min check — that's 50 picks × 13 runs/day × Finnhub api calls = 650 free-tier hits. Free Finnhub is 60/min. Easy to hit limits silently.
- Severity: 🚨 API rate-limit waste.

🟡 BUG-IM7: Line 354 `OUT_FILE.write_text(msg)` — overwrites previous alert file. Each run replaces. But sender (send_intraday_telegram.py) deletes file after send. Race: if monitor writes alert + sender starts reading old + monitor overwrites + sender finishes reading — could send old alert.
- Severity: 🟡 Race window (rare).

🟡 BUG-IM8: Line 36-39 catches ImportError silently for market_calendar — older deployments without market_calendar pass through. Acceptable but no logging.

### 3. intraday_news.py (55 lines) — Finnhub news fetcher

What it does: Tiny utility — fetch recent news for a ticker via Finnhub, classify materiality by keyword.

✅ GOOD-IN1: Tightest file. Single responsibility.
✅ GOOD-IN2: Lookback time-window filter (line 35-43) — only material if recent.

🚨 BUG-IN1: Line 21 `if not FINNHUB_KEY: return []` — silent. If env var missing in production, monitor never sees ANY news. No warning.
- Plain English: news-driven scoring silently disabled.
- Severity: 🚨 Silent feature outage.

⚠️ BUG-IN2: Line 22-23 builds `from=yesterday&to=today` — Finnhub API treats date range as inclusive day boundaries. With 45-min lookback, fetching 2 days of news to filter to <1hr is wasteful (10-100x more data than needed).
- Severity: 🟡 API waste.

⚠️ BUG-IN3: Line 8-16 MATERIAL_KEYWORDS — pure keyword match, no negation handling. `"NOT downgraded"` matches `"downgrade"`. False positives on hedged news headlines.
- Severity: 🟡 Heuristic limitation.

⚠️ BUG-IN4: Line 41 `datetime.fromtimestamp(ts, tz=timezone.utc)` — assumes Finnhub returns UTC unix timestamp. Documented in their API but not validated.
- Severity: 📝 OK-but-fragile assumption.

🟡 BUG-IN5: Line 32 `print(f"[news] {ticker} fetch failed: {e}")` — prints exception text only. Doesn't tell upstream "this was rate-limit (retry later)" vs "this was 401 (key bad)".

### 4. generate_late_daily_ideas.py (544 lines)

What it does: Generates "late watch-only" ideas after the 09:20 ET official cutoff. Reads news_signals.json + watchlist.json. Outputs JSONL + markdown.

✅ GOOD-LI1: Per-payload safety verification — checks watch_only=True, mode=monitoring_only embedded in EVERY emitted row (line 339-343).
✅ GOOD-LI2: classify_catalyst_type (lines 109-121) suppresses acquisition_event_arbitrage — avoids surfacing M&A spread plays without an event-arb model.
✅ GOOD-LI3: detect_risk_flags (lines 124-147) — explicit flag taxonomy; news_only_no_breadth_confirmation is a real-world-honest disclaimer.
✅ GOOD-LI4: compute_display_score (lines 150-189) — hard caps at 95 (standard) or 75 (corporate-action). Explicitly REJECTS 100/100 displays for news-only ideas. Excellent product-safety code.
✅ GOOD-LI5: Line 308-309 — REFUSES to emit acquisition events. Hard guardrail.
✅ GOOD-LI6: Line 318-320 — refuses unresolved entity (no quote AND no company name). Quality gate.

⚠️ BUG-LI1: Line 38-55 — five long regex patterns hardcoded as module constants. Maintainable but no test coverage suggested.
⚠️ BUG-LI2: Line 198-242 fetch_market_context — calls yfinance, returns {} on failure. Same X-IO2 problem.
⚠️ BUG-LI3: Line 37 `VALID_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9.\-]{0,6}$")` — disallows BRK.B (matches), but BRK-B with hyphen ALSO matches. Probably fine but fragile.
⚠️ BUG-LI4: Line 285-287 — `if action_window == "ignore": return None` — silent skip. No log telling operator "5 ideas ignored due to action_window".
- Severity: 🟡

🟡 BUG-LI5: Line 534 writes count to `/tmp/late_daily_ideas_count` — ephemeral file passed via env between workflow steps. Brittle but documented.

### 5. daily_watch_only_learning_report.py (452 lines)

What it does: Cross-artifact summary report. Reads late ideas, opening-range observations, momentum observations, run-status. Outputs JSON + markdown.

✅ GOOD-DW1: Compliance auditing (lines 103-109, 143-148, 180-187) — flags any row that fails safety contract (`watch_only != True` or `mode != monitoring_only`). Defensive.
✅ GOOD-DW2: Distinguishes `count` vs `unsafe_count` — exposes safety violations as first-class data.
✅ GOOD-DW3: Honest "learning_gaps" array (lines 299-304) — admits what report CAN'T tell you. Refreshing.
✅ GOOD-DW4: Markdown output includes safety section (lines 405-415) — re-stating guarantees in user-readable form.

⚠️ BUG-DW1: Line 282-284 calls `summarize_*` on rows — but each summary recomputes the unsafe set independently (with slightly different criteria for late vs OR vs momentum). Easy to drift. Could share a `_safety_compliant(row, expected_scanner)` helper.
⚠️ BUG-DW2: Line 218 `latest = rows[-1] if rows else {}` — assumes JSONL is sorted by time. NOT enforced anywhere. If a backfill writes out-of-order, "latest_event" lies.
- Severity: ⚠️ Sort-order assumption.

🟡 BUG-DW3: No `--strict` flag to fail on unsafe_count > 0. Report just observes.

### 6. backtest_opening_range_observations.py (287 lines)

What it does: Read-only outcome join. For each opening-range observation, find subsequent bars and check: did SL or TP hit first? Output backtest summary.

✅ GOOD-BO1: Line 140-143 — explicit "Conservative same-bar ambiguity: stop-loss first" policy with comment. Defensive.
✅ GOOD-BO2: max_hold_minutes parameterized (default 240 = 4hr) — sensible day-trade horizon.
✅ GOOD-BO3: Line 208 `sample_too_small`: True if n_evaluated < 30. Surfaces statistical-significance honestly.
✅ GOOD-BO4: Line 196-198 paper_trading_enabled=False, ready_for_paper_trading=False, paper_trading_note. Defensive contract.

⚠️ BUG-BO1: Line 23 `from scripts.review_opening_range_observations import DEFAULT_PATTERN, load_observations` — same private-function-import coupling noted in Batch 3a BUG-BA1 / Batch 3b BUG-WO1.
- Severity: ⚠️ Hidden coupling × 3 files now.

⚠️ BUG-BO2: Line 113 `deadline = obs_ts + timedelta(minutes=max_hold_minutes)` — uses observation timestamp + 240 min. If observation_ts is at 15:30 ET, deadline is 19:30 ET (post-market). Bars beyond market close don't exist; "missing_bar_data" not "timeout" returned.
- Plain English: Late-day observations get classified as data-missing, not as "ran out of session."
- Severity: ⚠️ Misleading status for late observations.

⚠️ BUG-BO3: Line 203 `r_values = [_to_float(o.get("r_multiple")) for o in evaluated if _to_float(...) is not None]` — calls _to_float twice per row. Cheap but ugly.

🟡 BUG-BO4: No filtering by date range. `--observations` glob gets ALL historical files. For long-running repos, summary counts unbounded.

### 7. review_opening_range_observations.py (255 lines)

What it does: Read-only summary stats over opening-range observation files (count by ticker, by date, avg breakout, top by score, compliance audit).

✅ GOOD-RO1: Tightest read-only review tool. Single responsibility.
✅ GOOD-RO2: non_compliant detection (lines 111-126) explicitly checks watch_only=True AND mode=monitoring_only AND scanner=opening_range. Strict.
✅ GOOD-RO3: ready_for_paper_trading=False (line 170) — never inferred from observation data.

⚠️ BUG-RO1: Line 81 `row["_source_file"] = str(path)` — mutates loaded row to add metadata. If the same row is read later by a different consumer, sees `_source_file` key it didn't expect.
- Plain English: schema pollution.
- Severity: 🟡 Polluted dict.

⚠️ BUG-RO2: Line 130-132 `top_by_score = sorted(rows, key=lambda r: _to_float(r.get("score"), -1) or -1, reverse=True)[:10]` — `_to_float(..., -1) or -1` evaluates to -1 if score is 0 (because `0 or -1 = -1`).
- Plain English: A real score of 0 gets sorted same as missing score. Edge case but real.
- Severity: 🟡

🟡 BUG-RO3: No `--from-date` / `--to-date` filter. Same as BUG-BO4.

### 8. daily_observation.py (127 lines)

What it does: Reads exec_report.json + premarket_check.json, generates plain-English lessons, appends to data/learning/observations.jsonl.

✅ GOOD-DO1: Lesson taxonomy (sl_well_placed, sl_too_tight, tp_too_early, tp_well_placed, premarket_correct, premarket_overcautious, weak_pick, promising, missed_opportunity) — 9 distinct lesson types, each with evidence object.
✅ GOOD-DO2: Premarket-tag cross-check (lines 73-76) — "we said SKIP and it was right" feedback loop.

🚨 BUG-DO1: ENTIRE file is module-top-level (no main() function). Same as X-IO5.
🚨 BUG-DO2: Line 17 `if not xp.exists(): print(...); sys.exit(0)` — exits 0 on missing exec report. Workflow sees success but NO observations logged.
- Plain English: silent observation loss on any day exec_report wasn't produced.
- Severity: 🚨 Silent learning gap.

⚠️ BUG-DO3: Line 27-28 `picks = {p["ticker"]: p for p in csv.DictReader(...) if p.get("pick_date") == date}` — assigned but NEVER USED below. Dead code.
- Severity: 🟡 Dead code.

⚠️ BUG-DO4: Line 63-72 SL_too_tight threshold `further > -0.5` (less than 0.5% drop after SL hit). Hardcoded magic number. Different from any other adaptive threshold in codebase.
- Severity: 🟡 Magic threshold.

⚠️ BUG-DO5: Line 80 `further > 2` for tp_too_early — another magic threshold.

🟡 BUG-DO6: Line 120 `with out.open("a") as f` — append mode, atomic for small writes. OK.

🟡 BUG-DO7: No dedup. If script runs twice for same date, observations DUPLICATED in journal. Downstream consumers count same lesson twice.
- Severity: ⚠️ Dedup missing.

### 9. monitoring_readiness.py (202 lines)

What it does: Computes per-bucket (day/swing/monster) readiness scores from picks_log.csv. Gate-check for "are we ready to enable paper trading?"

✅ GOOD-MR1: Excellent docstring (lines 1-15) — explains thresholds with rationale.
✅ GOOD-MR2: classify_bucket distinguishes monster from day/swing (lines 68-81) with override logic. Clean.
✅ GOOD-MR3: Two-condition gate (lines 99-109): need both win-rate threshold AND positive expectancy. Belt-and-suspenders.
✅ GOOD-MR4: Default min_n=30 (line 44) — minimum sample size hardcoded in one place. Tunable via --min-n.
✅ GOOD-MR5: Line 180 "win rate alone is not enough" — explicit anti-Goodhart-law guidance.

⚠️ BUG-MR1: Line 29 `DATA_QUALITY_FLOOR = "2026-05-02"` — hardcoded date. After ~6mo of data accumulation past the floor, this remains static. If you ever raise the floor (e.g., new data quality fix), code change required.
- Severity: 🟡 Hardcoded epoch.

⚠️ BUG-MR2: Line 31-36 yet another `CLOSED_STATUSES` definition. See Batch 3a X-AB5 / Batch 3b BUG-CE4 — now × 7 files.
- Severity: ⚠️ Schema drift continues.

⚠️ BUG-MR3: Line 38-42 thresholds hardcoded (day=0.60, swing=0.66, monster=0.90). No source/justification. Documented in docstring but not config-driven.
- Severity: 🟡 Magic thresholds.

⚠️ BUG-MR4: Line 75 `monster_score >= 0.90` — magic 0.90 different from THRESHOLDS["monster"] 0.90. Coincidence; not enforced as same constant. Could drift.
- Severity: 🟡 Drift risk.

🟡 BUG-MR5: No statistical-significance test — n=30 with WR=66% has wide confidence interval. Wilson lower bound (suggested for Batch 3b BUG-CE3) would apply here too.

### 10. daily_execution_report.py (212 lines) — INTRADAY X-RAY

What it does: For each pick on a date, fetches 5min bars, computes did-fill / SL-vs-TP-first / MFE / MAE / counterfactuals. Writes JSON + prints human-readable.

✅ GOOD-DE1: Counterfactual analysis (lines 110-119) — "if NO SL set, what would close-of-day be?" Excellent for SL-placement learning.
✅ GOOD-DE2: MFE/MAE per pick (lines 99-100) — gold-standard pick-quality metrics.
✅ GOOD-DE3: chronological SL-vs-TP detection (lines 86-97) — bar-by-bar walk forward, conservative same-bar policy.

🚨 BUG-DE1: Module-level execution. Same as X-IO5.
🚨 BUG-DE2: Line 20 `print("Missing yfinance/pandas — skipping"); sys.exit(0)` — workflow sees success when entire X-ray skipped.
- Severity: 🚨 Silent feature outage.

⚠️ BUG-DE3: Line 39-40 fetches start=date-2 to end=date+2 — 4-day window for ONE day's intraday. yfinance call expensive; fine but unexamined.
⚠️ BUG-DE4: Line 70 `filled = day_low <= entry` — assumes ANY low-touch fills the limit. Real-world: exchange queue, partial fills, slippage. This is best-case fill assumption.
- Severity: 🟡 Optimistic fill model.

⚠️ BUG-DE5: Line 92-97 same-bar SL-AND-TP edge case: outer if-check `if sl_hit_idx is not None or tp_hit_idx is not None` then nested same — two breaks but the conditional logic is awkward. Hard to read.
- Plain English: works but worth a comment.
- Severity: 🟡 Code smell.

⚠️ BUG-DE6: Line 187-189 OPEN-status block uses `r['no_tp_best_pct']` and `r['no_sl_worst_pct']` — these only exist for OPEN status (line 146). KeyError if accessed for any other status.
- Severity: 🟡 Schema-fragile (not currently triggered).

🟡 BUG-DE7: Line 212 prints raw data path BUT also wrote it line 152. Two prints, no progress structure.

### 11. record_daily_picks_run_status.py (235 lines)

What it does: Append one event row to data/daily_picks_run_status_YYYY-MM-DD.jsonl. Workflow observability.

✅ GOOD-RS1: Excellent docstring + explicit safety contract.
✅ GOOD-RS2: build_record returns DICT (testable) separate from append_record (writes file). Clean separation.
✅ GOOD-RS3: GitHub env vars captured in every record (lines 173-181) — workflow run id, sha, ref. Traceability.
✅ GOOD-RS4: include_diagnostics flag (line 207-211) optional — caller controls whether to do heavy artifact reads.
✅ GOOD-RS5: _infer_no_pick_cause_from_pipeline (lines 59-81) — backfill compatibility for older reports without primary_no_pick_cause.

⚠️ BUG-RS1: Line 28-35 `today_picks_count` — silent bare-except returns 0. If picks_log corrupted, status row says "0 picks" when actually unknown.
- Severity: ⚠️ Hides corruption.

⚠️ BUG-RS2: Line 49-56 `_load_json` same silent pattern. Same X-AV4 family.

🟡 BUG-RS3: Line 166 `"official_premarket_pick": event in {...}` — hardcoded set of 5 event names. If you add new events later, this set may be out of date silently.
- Severity: 🟡 Drift-prone enum.

🟡 BUG-RS4: Line 39 `os.getenv("DAILY_PICKS_STATUS_DATA_DIR", "data")` — env override for tests. OK but not documented in docstring.

### 12. premarket_check.py (134 lines) — TAGS PICKS

What it does: For today's picks, fetch SPY/QQQ/SOXX/VIX, fetch each pick's last close, tag SAFE/HALF/SKIP/WATCH. Writes data/premarket_check.json.

✅ GOOD-PC1: Plain-English docstring with tag taxonomy.
✅ GOOD-PC2: Three-condition global action (skip_all if SPY -1.5% or VIX 25; half if SPY -0.7% or VIX 20). Clear ladder.
✅ GOOD-PC3: Per-pick tags include `actionable` boolean (line 114) — downstream consumers don't need to parse the emoji string.

🚨 BUG-PC1: Module-level execution. Same as X-IO5.
🚨 BUG-PC2: Line 19 yfinance import error → sys.exit(0). Same X-IO2.
🚨 BUG-PC3: Line 36-44 `safe_last` — fetches "5d" history of DAILY bars, returns close[-2] vs close[-1]. But during PREMARKET (08:30 ET), close[-1] IS yesterday's close (today not yet closed). So `prev = close[-2]` is day-before-yesterday and `curr = close[-1]` is yesterday. The "premarket change" is YESTERDAY's close-to-close, NOT today's premarket gap.
- Plain English: This script is named "premarket_check" but it computes YESTERDAY'S close-to-close, NOT today's premarket movement.
- During market hours, close[-1] is intraday last bar (CORRECT-ish, mid-day quote).
- Severity: 🚨 Mis-named function; entire script may be measuring the wrong thing.

⚠️ BUG-PC4: Line 73-74 `if soxx_chg <= -2.0` — adds warning but does NOT change global_action. Inconsistent: SPY -1.5% → skip_all, VIX 25 → skip_all, but SOXX -2% → just a warning. SOXX is more volatile so threshold may be different, but inconsistency unstated.
- Severity: ⚠️ Asymmetric ladder.

⚠️ BUG-PC5: Line 97 `gap_pct <= -sl_buffer * 0.6` — magic 0.6. "Already 60% to SL premarket = SKIP." No basis.
- Severity: 🟡 Magic threshold.

⚠️ BUG-PC6: Line 99 `gap_pct >= 3.0` — magic 3% gap-up threshold for HALF SIZE. Same.

🟡 BUG-PC7: Line 21 `today = datetime.now().strftime("%Y-%m-%d")` — local time. See X-IO3.

🟡 BUG-PC8: Line 51 `vix_disp = f"{vix_curr:.1f}" if vix_curr else "n/a"` — but `vix_curr` could be 0.0 (legitimate) which would also map to "n/a". Edge case.

🟡 BUG-PC9: No SAFETY dict in output payload. premarket_check.json just has data, no monitoring_only / official_premarket_pick contract. Other Family B reports DO include this.
- Severity: ⚠️ Missing safety contract.

---

## Summary of Batch 3d (12 files)

### By severity
| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 14 |
| ⚠️ Data/safety risk | 36 |
| 🟡 Code smell | 27 |
| 📝 Doc-only | 1 |
| ✅ Good code | 38 |
| Total | 116 findings |

### Top 10 things to fix in this batch (in order)

| # | Bug | Why first | Fix difficulty |
|---|---|---|---|
| 1 | BUG-PC3 (premarket_check measures YESTERDAY'S close-to-close, not today's gap) | The script's entire purpose is broken; SAFE/HALF/SKIP tags are wrong | Medium: use real premarket quote feed |
| 2 | BUG-IS5 (vol_ratio compares partial-day vs full-day avg) | Intraday volume signal systematically wrong; biases scoring | Medium: scale by trading-hours-elapsed |
| 3 | BUG-IM6 (intraday_monitor calls Finnhub 650+ times/day on 50 picks) | Free-tier rate limits hit silently; news disabled | Easy: cache per-ticker per-30min |
| 4 | BUG-IM2 (intraday_monitor TODAY=UTC; mismatches local pick_date) | Off-by-one-day; eval status writes to wrong row near midnight | Easy: use ET |
| 5 | BUG-IS7 (bar merge: new overwrites existing) | Data corruption window if new is malformed | Easy: prefer first-write-wins |
| 6 | BUG-IN1 (Finnhub key missing → silent return) | News-driven scoring silently disabled | Easy: warn loudly |
| 7 | BUG-DO2 (daily_observation exits 0 on missing exec_report) | Silent learning gap; observations.jsonl falls behind | Easy: distinguish missing vs error |
| 8 | BUG-DO7 (daily_observation no dedup) | Duplicated observations distort learning if cron retries | Medium: dedup by (date, ticker, type) |
| 9 | BUG-DE2 (daily_execution_report sys.exit(0) on yfinance missing) | Workflow sees success when X-ray skipped | Easy: distinguish missing vs error |
| 10 | X-IO5 (module-level side effects in 4 files) | Tests can't run; refactors blocked | Medium: wrap in main() |

### What this batch tells us about the project

- **The observe-only safety contract is genuinely the strongest part of the codebase.** Every artifact embeds `mode/watch_only/paper_trading_enabled/live_trading_enabled`. Every reader checks compliance. This is a real engineering achievement.
- **But the data plumbing underneath is fragile.** yfinance (free-tier Yahoo Finance, no SLA) is the data source for: intraday monitoring, premarket tags, late ideas, execution X-ray, stock stats. When Yahoo breaks, EVERYTHING breaks silently.
- **`premarket_check.py` may be measuring the wrong thing entirely.** safe_last() returns yesterday-vs-day-before during premarket hours, not today's premarket gap. The downstream SAFE/HALF/SKIP tags rely on this. **WORTH MANUAL VERIFICATION TODAY.**
- **Adaptive TP/SL features partially broken.** They read `live.get("rsi")` which is always None because get_live_quote never computes RSI.
- **Magic-number thresholds everywhere.** 9 files have hardcoded thresholds (vol_ratio>=2 = +10pts, breakout>=2% = overextended, soxx<=-2% = warning, etc). Each defensible alone; collectively ungovernable. Brain learning targets won't know what these mean.
- **`intraday_monitor.py` calls Finnhub 650+ times per trading day.** Free tier is 60 req/min. You will hit limits. News integration likely silently degraded most days.
- **Module-level side effects in 4 files** (intraday_monitor's calendar guard, daily_execution_report, daily_observation, premarket_check) make testing impossible. Test coverage of this batch is likely zero.

### Glossary additions

| Term | Plain English |
|---|---|
| Opening-range breakout | First 30 minutes after open define a high/low range. A break above (or below) signals momentum. |
| MFE / MAE | Max Favorable Excursion / Max Adverse Excursion. The best/worst unrealized P&L during a trade's life. |
| Counterfactual | "What if SL hadn't been set?" — runs the no-SL scenario to evaluate whether the SL helped or hurt. |
| Sample-too-small | When n<30, the win rate has wide confidence interval. Treat as preliminary, not actionable. |
| Wilson lower bound | Statistical method for "95% confident the win rate is at least X%." Better than naive ratio for small n. |
| Watch-only universe | All ideas the agent generates that are NOT official picks — late ideas, opening-range observations, intraday momentum hits. |
| Provider failure taxonomy | Classification of WHY data fetch failed (rate-limit / auth / stale-session / not-found / network). Enables targeted retries. |

---

End of Batch 3d.

Cumulative findings across batches 1a + 1b + 2a + 2b + 3a + 3b + 3c + 3d:
- Show-stoppers: 104
- Data/safety risks: 200
- Code smells: 166
- Doc-only: 14
- Good code: 189
- Total: 673 findings across 82 files (~21,150 lines)

Next: Batch 3e — Scripts: themes/news/learning/wisdom/misc (~22 files):
- discover_themes.py, news_signal_evidence_report.py, news_signal_outcome_attribution.py, run_news_engine.py
- run_hypothesis_review.py, run_nightly_brain.py, monthly_xray.py, weekend_reflection.py, weekly_report_card.py
- wisdom_audit.py, wisdom_writer.py, evaluate_picks.py, performance_dashboard.py
- scan_patterns.py, show_performance.py, unpause.py, quarterly_report.py
- claude_helper.py, gemini_helper.py, code_inspector.py, full_repo_audit.py, local_analyst.py, run_backtest.py
