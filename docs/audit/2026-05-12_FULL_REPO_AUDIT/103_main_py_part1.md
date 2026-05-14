# Audit Batch 103 — `main.py` Part 1 (lines 1–954 of 1817)

**File:** `main.py` (root-level orchestrator)
**Pinned commit:** `020a4e8b`
**Actual size:** 1,817 lines (smaller than the 2,400 estimate from earlier batches — will complete in Part 2)
**This batch covers:** imports → helper functions → `run()` from start through the news-signals stage (line 954)
**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

## SECTION A — Imports + module-level setup (lines 1–98)

### ✅ GOOD-M1: Docstring is honest (line 1)
"Daily Stock Picker — CLI entrypoint with regime + earnings filters + Week 3 wiring." Tells you what this file is. Most 2k-line orchestrators don't.

### 🚨 BUG-M1: PEP-8 violation, multiple imports on one line (line 2)
`import os, yaml` — not catastrophic but signals informal style. The whole file uses this pattern.
- **Severity:** 🟡 Style.

### ⚠️ BUG-M2: 27 src.* imports at module top, no try/except (lines 8–34)
If ANY `src/` module fails to import (typo, missing dep, circular import), `main.py` crashes before the run() function is even defined. Test files can't import `main` to test single helpers without all 27 src modules loading cleanly.
- Compare: `app.py` has the same problem (Batch 5 BUG-R-X6).
- **Severity:** ⚠️ Test/refactor friction.

### 🚨 BUG-M3: `subprocess.run([_sys.executable, "scripts/bootstrap_wisdom.py"], ...)` runs on EVERY IMPORT (lines 92–97)
- **Plain English:** Just importing `main` (e.g., from a test, from a REPL, from a different orchestrator) **executes a subprocess that mutates wisdom_base files**. With `capture_output=True, timeout=10`.
- **Why a problem:**
  1. Test isolation broken — every test that imports main runs the seeder.
  2. `check=False` means failures are silent.
  3. `capture_output=True` discards seeder output — if it ever matters that seeding failed, you'd never know.
  4. The bare `except: pass` (line 96) swallows EVERYTHING (KeyboardInterrupt, MemoryError, ImportError).
- **Compare to Batch 5 R-X1:** this is one of the specific "module-level side effect" anti-patterns the audit warned about.
- **Severity:** 🚨 Module-level mutation + silent failure on a critical brain operation.

### ✅ GOOD-M2: `_safe_trade_type_for_pick` (lines 36–47) — Bug #7 doc
Docstring explains exactly what historical bug it patches. Forensic-friendly. Same model citizen as the backfill scripts (Batch 3a).

### ⚠️ BUG-M4: `_yf_ticker_for_sector_benchmark` imports yfinance LAZILY but calls hard (lines 50–53)
`import yfinance as yf` inside the function — fails on missing dep at CALL time, not import time. Caller has no way to know yf is missing until called.
- **Severity:** 🟡 Documented "test seam" intent (line 51 docstring) — acceptable but the lazy import is undocumented.

### ⚠️ BUG-M5: `_latest_close_for_sector_benchmark` swallows ALL exceptions (lines 56–64)
- Line 62 `except Exception: return None` — **including AttributeError, KeyError, network errors, rate-limit errors, ALL the same**.
- Caller cannot distinguish "ETF doesn't exist" from "yfinance rate-limited us today."
- **Severity:** ⚠️ Silent provider failure (continues from Batch 3d X-IO2).

### ⚠️ BUG-M6: `_sector_benchmark_for_pick` defaults to "SPY" twice (lines 67–87)
- Line 76: if `resolve_sector_etf` returns falsy → use "SPY"
- Lines 82–85: if sector ETF has no quote AND etf != "SPY" → fallback to SPY
- Returns `(etf, None)` if both fail (line 87) — caller gets the ORIGINAL etf name with no quote, not "SPY" with no quote. Inconsistent.
- **Severity:** ⚠️ Sector_alpha learning gets `(SPY, None)` vs `(<original>, None)` depending on path. Downstream wisdom may bucket these differently.

---

## SECTION B — Helper functions (lines 100–626)

### ⚠️ BUG-M7: `load_config` no validation (lines 100–102)
- Reads `config.yaml`, returns dict, **no schema validation**. Missing keys cause `KeyError` 200 lines later in `run()`.
- Specifically: `cfg["output"]["top_n_picks"]` (line 698) crashes if either key missing.
- **Severity:** ⚠️ Late-binding crashes.

### ⚠️ BUG-M8: `_candidate_report_value` truncates at 10/30 silently (lines 105–117)
- Line 110: `value[:10]` for lists.
- Line 114: `list(value.items())[:30]` for dicts.
- **Plain English:** Diagnostic dumps silently drop data past 10 list items or 30 dict keys. A pick with 50 indicators has 20 silently missing in the diagnostic JSON.
- **Severity:** ⚠️ Silent diagnostic loss; debugging mystery later.

### ✅ GOOD-M3: `_news_action_window` (lines 121–145)
Docstring documents the exact bug discovered 2026-05-11 (list-vs-dict shape ambiguity at main.py:1183). Defensive helper. Excellent.

### ⚠️ BUG-M9: `_news_action_window` returns `None` when `aw` is empty string (line 145)
`return aw or None` — if aw is `""`, returns None. Probably intended, but `aw == "off"` or `aw == "0"` would also coerce. No issue today; flag for future.
- **Severity:** 📝 Minor.

### ⚠️ BUG-M10: `_summarize_candidate_for_report` repeats news_action_window logic (lines 165–169)
- It calls `_news_action_window(news, scores)` AND ALSO checks `news_signal.get("action_window")`. Three places competing for the same value. If news_signal disagrees with scores disagrees with news, which wins?
- Order shows: `scores.get("news_action_window")` wins, then `news_signal.action_window`, then `_news_action_window` fallback.
- **Severity:** 🟡 Three sources of truth.

### ⚠️ BUG-M11: `_classify_no_pick_cause` ladder uses `>=` not `==` (lines 201, 208, 219)
- `len(sanity_blocked) >= len(pre_sanity)` — but if pre_sanity has 5 items and sanity_blocked somehow ends up with 6 (duplicates? bug?), this is still True. Should ASSERT exact match or use `len(...) == len(pre)`.
- **Severity:** 🟡 Silently masks an upstream bug.

### ⚠️ BUG-M12: Cause detection consumes pre/post lists by REFERENCE (lines 199–222)
- Reads `diag.get("premarket_sanity_blocked_candidates")`. If diag isn't built yet (early failure path), these are None and isinstance fails → silently skipped. Next ladder rung tested.
- Plain English: an early failure with diag={} silently drops through to the generic `NO_PICK_UNKNOWN_POST_FILTER_GATING` branch (line 262).
- **Severity:** ⚠️ Misclassified no-pick causes when diagnostics builder fails.

### ⚠️ BUG-M13: `_classify_no_pick_cause` returns `int(...)` on possibly-None values (lines 236–241)
- `int(pipe.get("final_pick_count") or 0)` — `or 0` correctly coerces None.
- BUT `int("3.5")` raises ValueError. If pipeline ever stores floats or strings, crashes.
- **Severity:** 🟡 Type-fragile.

### 🚨 BUG-M14: `_write_daily_picks_candidate_diagnostics_report` swallows ALL errors (lines 269–344, line 343 `except Exception: pass`)
- This is a critical Lane 1 artifact write. Failure modes: disk full, permission denied, schema bug, JSON serialization error.
- Bare `except Exception: pass` means the **only Lane 1 audit trail for this run silently disappears**.
- **Severity:** 🚨 Silent loss of Lane 1 diagnostic artifact (the very thing the rest of the audit infrastructure depends on).

### ⚠️ BUG-M15: Same function — NOT atomic write (lines 298–300, 340–342)
- `(data_dir / f"...{date_str}.json").write_text(json.dumps(...))` — direct overwrite.
- **Compare to Batch 3a X-AB1:** backfills do atomic write-then-rename. This file does NOT.
- Mid-write crash → corrupted JSON read by daily_intelligence_brief downstream.
- **Severity:** ⚠️ Mid-write corruption window. Same bug class as Batch 3b X-AV6.

### ⚠️ BUG-M16: `now_dt_utc` then `astimezone(ET)` for date_str (line 281)
- Date string is ET. But `timestamp_utc` is UTC. **Two clocks in one record.** Already noted as Batch 3d X-IO3 family.
- **Severity:** 🟡 Acceptable here (date_str represents trading day, timestamp_utc represents wall clock) but could be commented.

### 🚨 BUG-M17: `_write_daily_picks_no_pick_report` ALSO swallows all errors (lines 348–578, line 576 `except Exception: pass`)
- Same as BUG-M14 but worse: this is the **only no-pick evidence artifact**. If it fails, downstream classification (data_readiness_report, daily_intelligence_brief, layman senders) all see "no artifact" → cascade-default to wrong status.
- The comment on line 577 admits the design choice: "Do not hide the original no-pick failure if reporting fails." But the original "failure" is a return statement, not an exception, so there's nothing to hide. **The bare except hides only the artifact-write failure.**
- **Severity:** 🚨 Silent loss of THE most important Lane 1 artifact.

### ⚠️ BUG-M18: `_write_daily_picks_no_pick_report` — TWO atomic-write violations (lines 441–443, 488–490, 513–515, 573–575)
- Four direct `.write_text()` calls. None atomic.
- **Severity:** ⚠️ Mid-write corruption × 4 artifact paths.

### ⚠️ BUG-M19: `_write_daily_picks_no_pick_report` writes `candidate_diagnostics` and `diagnostics` keys to BOTH (lines 393, 412, 413)
- Line 393: `"candidate_diagnostics": diagnostics or {}`
- Line 412: `payload["diagnostics"] = diagnostics or {}`
- Line 413: `payload["candidate_diagnostics"] = diagnostics or {}` (overwrites line 393)
- **Plain English:** The same value stored in TWO keys. Downstream readers must check both. Schema duplication.
- **Severity:** ⚠️ Schema bloat + drift risk.

### ⚠️ BUG-M20: `summarize_market_data_health` import is INSIDE the try block (lines 399–402)
- If `src.market_data_health` is broken, falls back to `payload["market_data_health"] = {}` SILENTLY (line 402 bare except).
- The function `_classify_no_pick_cause` then gets `{}` for market_data_health — incorrectly classifies provider-degraded runs as `NO_PICK_UNKNOWN_POST_FILTER_GATING`.
- **Severity:** ⚠️ Silent classification failure.

### ⚠️ BUG-M21: `data_readiness_status` ladder uses string literals not constants (lines 415–438)
- 7 hardcoded status strings. If a downstream consumer expects the literal `"not_ready_data_provider_degraded"` and you change it to `"data_provider_degraded"`, no test catches it.
- Compare to Batch 4 T-X3: the audit team prefers contract constants for exactly this.
- **Severity:** ⚠️ Schema drift waiting to bite.

### 🚨 BUG-M22: `_write_guard_no_pick_artifact_for_main` — bare except prints to RPRINT (lines 611–615)
- Line 613: `rprint(f"[dim]guard no-pick artifact writer failed: {e} ...")` inside `except Exception as e`.
- BUT line 614–615: `except Exception: pass` wrapping the rprint itself.
- **Plain English:** If the artifact writer fails AND rprint also fails (e.g., stdout closed), still pass. If the artifact writer SUCCEEDS but a later error happens, also pass.
- The function is supposed to return False on failure but the second except may swallow True → False conversion in some code paths. Subtle.
- **Severity:** 🟡 Defensive but confusing.

### ✅ GOOD-M4: `_should_log_paper_trade` (lines 619–625)
- Defaults to `"monitoring"` when env unset. Explicit lowercase. Single source of truth.
- Test `test_monitoring_mode_no_paper_default.py` verifies this. Excellent.

---

## SECTION C — `run()` start through guard sections (lines 628–727)

### 🚨 BUG-M23: `pipeline` dict initialized in run(), not module-level (lines 631–642)
- 11 keys hardcoded with default 0. If a new stage is added (e.g., `news_engine_count`) but you forget to add to this initial dict, KeyError later when `pipeline["new_key"]` is read.
- **Compare to Batch 3b BUG-CC4:** the artifact completeness checker has the same drift problem with its hardcoded ARTIFACTS list.
- **Severity:** ⚠️ Manifest drift.

### ✅ GOOD-M5: T51 market-closed guard with bare-return + artifact write (lines 650–664)
- Calls `_is_td()` then `_why_closed()` then `_next_td()` for context.
- Writes guard no-pick artifact before returning (lines 658–661).
- Compare to Batch 5 R-X1 issue: this is the fix the audit referenced.

### ⚠️ BUG-M24: Bare `except Exception as _e` for market calendar check (lines 663–664)
- "[dim]market-calendar check failed: {_e} — proceeding[/dim]" — proceeds even if calendar is broken.
- **Plain English:** if market_calendar.py is broken, agent runs ON A WEEKEND/HOLIDAY and produces picks for non-trading days.
- **Severity:** ⚠️ Fail-open on safety check (should be fail-closed).

### ✅ GOOD-M6: Pause check (lines 666–682)
- Reads pause state, prints reason+until+days_remaining, writes `data/last_run_paused.json` for the Telegram sender, then HARD STOP.
- Comment line 682: "← HARD STOP. No picks, no journaling, no Telegram picks." — explicit and clear.

### ⚠️ BUG-M25: `_P("data/last_run_paused.json").write_text(...)` — NOT atomic (lines 677–679)
- If pause-write fails mid-write, sender reads garbage.
- **Severity:** 🟡 Same atomic-write family.

### 🚨 BUG-M26: Pause artifact write inside bare `except: pass` (line 680–681)
- If artifact write fails, agent still returns (line 682). Sender then has no pause info.
- **Severity:** ⚠️ Pause day → no Telegram alert because file missing.

### ⚠️ BUG-M27: Market guards run BEFORE multi-fire dedup (lines 687–708)
- VIX/SPY/sector calls happen on every cron multi-fire. Wasteful provider calls.
- The dedup check is at line 721. **Move dedup BEFORE network calls.**
- **Severity:** ⚠️ Wasted API quota on duplicate fires.

### ⚠️ BUG-M28: `vix_level()` / `spy_trend()` / `sector_strength()` — no error handling (lines 688–691)
- If any returns garbage (None or {}), line 691 `if v.get("weak")` crashes on None.
- **Severity:** ⚠️ Provider hang/error → run dies.

### ⚠️ BUG-M29: Pick-count adjustment writes to cfg dict (line 707)
- `cfg["output"]["top_n_picks"] = adjusted_picks` — mutates loaded config.
- If cfg is cached/reused (it isn't currently), changes persist.
- **Severity:** 🟡 Mutation of config; convention is config = read-only.

### 🚨 BUG-M30: Multi-fire guard reads picks_log.csv inefficiently (lines 716–727)
- Opens file with no encoding, iterates ALL rows of `picks_log.csv` (could be thousands), checks `pick_date == _today`. **O(n) on every run.**
- Worse: line 723 reads each row but only ever checks `pick_date`. csv.DictReader with no row limit.
- **Severity:** ⚠️ Performance; will degrade over years.

### 🚨 BUG-M31: `_today = _date.today().strftime("%Y-%m-%d")` (line 719) — local time
- This is the LOCAL machine's date. GitHub Actions runs in UTC. SGT machine = different date.
- **Plain English:** at 23:00 ET (next day in UTC), `_today` is tomorrow in UTC. Multi-fire guard compares against **WRONG date**.
- Compare to Batch 3d BUG-PC3 / X-IO3 / Batch 3c X-TG6 — same family.
- **Severity:** 🚨 Wrong-date dedup near midnight; multi-fire guard fails.

### ⚠️ BUG-M32: Multi-fire guard EXITS without writing no-pick artifact (line 726)
- `return` with no artifact. Downstream Lane 1 validators see "no run today" — wrong status.
- **Severity:** ⚠️ Lane 1 audit gap on multi-fire skip.

### ⚠️ BUG-M33: File handle not closed if csv parse fails (lines 722–725)
- `with _log.open() as _f:` — context manager OK. But `csv.DictReader` errors are not handled → propagates as exception, ignored by callers because there's no try/except above.
- Actually re-checking: no try, so an exception here would crash the whole run. Probably the *desired* behavior, but inconsistent with the bare-except patterns elsewhere.
- **Severity:** 📝 Inconsistent error handling style.

---

## SECTION D — Regime, briefing, universe, fetch (lines 728–774)

### ✅ GOOD-M7: Regime check with bullish/bearish min_score adjustment (lines 728–738)
- If bearish: raise min_score floor to 0.70. Defensive.

### ⚠️ BUG-M34: `cape` guard bug (line 741, line 1758)
- Line 741 `if cape.get("cape"):` — what if `cape` is None? AttributeError. `get_cape()` is unaudited at call site here.
- Worse: line 1758 `cape if "cape" in dir() else None` — `dir()` returns ALL local names, so `"cape"` is ALWAYS in dir() once line 740 runs, even if get_cape failed mid-call. **The check is meaningless.**
- **Severity:** ⚠️ Defensive code that doesn't actually defend.

### ⚠️ BUG-M35: Market briefing — NO error handling (lines 745–760)
- `get_market_briefing()` not wrapped. If LLM call fails or news fetch hangs, run dies after expensive fetch+score work.
- **Severity:** ⚠️ Run-killer late in pipeline.

### ⚠️ BUG-M36: Bearish-sentiment min_score bumped to 0.72, but bullish path doesn't lower it (lines 762–766)
- Bearish: tighten to 0.72. Bullish: keep standard. **Asymmetric.** No "loosen min_score on strong bullish" path.
- Defensible (be conservative on the loose side) but undocumented.
- **Severity:** 📝 Worth a comment.

---

## SECTION E — Data readiness, scoring, filtering (lines 776–890)

### ✅ GOOD-M8: Data readiness gate (lines 776–816)
- Imports inside try (lines 778–779) — safe degradation.
- Calls `build_premarket_readiness_decision` with env-overridable thresholds (lines 786–787). Configurable.
- On failure: writes no-pick report, prints, returns. Defensive.

### ⚠️ BUG-M37: `float(os.getenv("PREMARKET_MIN_FETCH_COVERAGE", "0.25"))` — no validation (line 786)
- If env is set to garbage like "0.25%", `float("0.25%")` raises ValueError. Crashes.
- Same for `int(...)` on line 787.
- **Severity:** 🟡 Env-injection fragility.

### 🚨 BUG-M38: Bare `except Exception as e` swallows readiness-gate import errors (lines 805–816)
- If `src.market_data_health` or `src.premarket_readiness_gate` can't be imported, falls into the except, writes no-pick report saying "data-readiness gate failed unexpectedly", returns.
- **Plain English:** Module import errors are conflated with runtime gate failures. Operator can't tell "gate ran and failed" from "gate never loaded."
- **Severity:** ⚠️ Diagnostic ambiguity.

### ✅ GOOD-M9: Parallel scorer with env-tunable workers (lines 819–823)
- `DAILY_SCORER_WORKERS` env override. Documented in print message.

### ⚠️ BUG-M39: `int(os.getenv(..., "4"))` — no validation (line 820)
- Same env-injection fragility.

### 🟡 BUG-M40: `write_market_data_run_summary` wrapped in bare except: pass (lines 825–829)
- Health-summary write failure silenced. Consistent pattern but always concerning.
- **Severity:** 🟡

### 🚨 BUG-M41: `cfg["output"]["top_n_picks"] * 4` magic multiplier (line 836)
- Comment says "4x buffer for sector cap". Hardcoded. If sector cap raises max_per_sector to 6, this 4x is wrong.
- **Severity:** 🟡 Magic number; coupling between two unrelated configs.

### 🚨 BUG-M42: Wisdom-kill check uses `.get("wisdom_kill")` truthy (line 838)
- If wisdom_kill is `"false"` (string), evaluates True. If it's `0`, False.
- No type contract documented.
- **Severity:** 🟡 Type-fragility on a hard-drop check.

### ⚠️ BUG-M43: `days_to_earnings(p["ticker"])` called per pick, no batching (line 858)
- 12 picks × 1 yfinance call = 12 sequential blocking calls. Per Batch 3d audit, yfinance has no SLA.
- **Severity:** ⚠️ Sequential blocking; rate-limit risk.

### ⚠️ BUG-M44: `if d2e < 5` magic threshold (line 860)
- Hardcoded "5 days to earnings" cutoff. No config knob.
- **Severity:** 🟡 Magic threshold (Batch 3d theme continued).

### ⚠️ BUG-M45: `if d2e >= 999:` sentinel value (line 869)
- 999 is the "earnings unknown" sentinel from `days_to_earnings`. **Magic sentinel — should be a constant.**
- Line 859 sets `p["days_to_earnings"] = d2e if d2e < 999 else None` but line 869 still tests `>= 999`. Should test `is None`.
- **Severity:** 🟡 Sentinel inconsistency.

### 🚨 BUG-M46: Earnings-unknown picks INCLUDED with caution (lines 869–871)
- Comment says "included with caution" but **no `watch_only=True` flag set**. Just a print.
- Compare to Batch 3a BUG-BE2 fix: backfill SKIPS earnings-unknown rows.
- **Plain English:** Picks where we don't know if earnings are tomorrow get FULL official-pick treatment. Dangerous.
- **Severity:** 🚨 Production safety contradiction (audit referenced this as "main.py BUG-77" in earlier batch).

### ⚠️ BUG-M47: `if len(filtered) >= cfg["output"]["top_n_picks"] * 3:` — magic 3x (line 872)
- Different from line 836's 4x. Two different multipliers, no rationale, easy to drift.
- **Severity:** 🟡 Inconsistent magic numbers.

### ✅ GOOD-M10: Earnings quality blend formula commented (lines 882–885)
- `0.88 * old + 0.12 * eq` weights both shown clearly.
- Stores `composite_pre_earnings` for audit trail.
- Magic 0.88/0.12 weights, but at least visible.

### ⚠️ BUG-M48: `analyze_earnings` per pick, NO error context (lines 877–888)
- Bare except prints `"earnings err for {ticker}: {e}"` — no traceback, no severity.
- Sets `p["earnings"] = {}` — downstream `ea.get("earnings_quality", 0.5)` then **uses 0.5 default for all error cases**, blending neutral 0.5 into composite. **Silent score corruption** for tickers with broken earnings data.
- **Severity:** ⚠️ Silent degradation.

### 🟡 BUG-M49: Sort by composite, no tie-breaker (line 889)
- `filtered.sort(key=lambda x: x["scores"]["composite"], reverse=True)` — deterministic-enough for floats but ties resolved by insertion order, which depends on parallel scorer worker order.
- **Severity:** 🟡 Non-deterministic ordering on ties.

---

## SECTION F — Sector cap, news signals (lines 893–954)

### ⚠️ BUG-M50: Sector padding silently overwrites missing sector with "Unknown" (lines 898–902)
- Loops all filtered picks. If `info_short.sector` empty, pads with `sector_tag` or "Unknown".
- Then `apply_sector_cap` treats all "Unknown" as same sector → all-but-2 dropped.
- **Plain English:** If yfinance sector lookup failed for 5 tickers, only 2 of them survive sector cap based on whether the FIRST 2 happened to be picked. Unfair to the rest.
- **Severity:** ⚠️ Silent ranking distortion.

### ⚠️ BUG-M51: `apply_sector_cap(filtered, max_per_sector=2, ...)` — magic 2 (line 903)
- BUT the comment line 911 says "max 4/sector". **Code disagrees with its own comment.** Either code is wrong or comment is wrong.
- Looking at Batch 1a BUG-CFG-1: `config.yaml` has no `max_per_sector` setting. So this is hardcoded.
- **Severity:** 🚨 Code/comment disagreement on a critical sector-diversification rule.

### ⚠️ BUG-M52: `apply_tag_cap(capped, max_per_tag=2)` — another magic 2 (line 907)
- Tier 1 fix per comment line 904. No config knob.
- **Severity:** 🟡 Magic threshold.

### 🟡 BUG-M53: `print(...)` instead of `rprint(...)` (line 909)
- Mixes plain print with rprint everywhere else.
- **Severity:** 🟡 Style consistency.

### ⚠️ BUG-M54: News signals try/except silently degrades (lines 916–953)
- Bare except prints "News signals unavailable" — but **CONTINUES with capped list unchanged**.
- If news_signals module is broken, picks get NO news boosts → scoring is wrong but appears fine.
- **Severity:** ⚠️ Silent feature degradation.

### ⚠️ BUG-M55: `if abs(boost) >= 0.01:` magic threshold (line 937)
- Boosts smaller than 1% are silently ignored. No config knob.
- **Severity:** 🟡 Magic threshold.

### ✅ GOOD-M11: News field shape hardening (lines 928–936)
- Comment explicitly says "Hardened 2026-05-11" — only stash inside p["news"] if it's dict-shaped.
- Defensive against the list-vs-dict bug from BUG-M11/_news_action_window history.

### ⚠️ BUG-M56: `capped.sort(...)` after news boost (line 951)
- Re-sorts inside the try. If a later pick had a huge negative boost moving it out of top_n, the sort handles that — but the trim happens later (line 956 in Part 2). Race window.
- **Severity:** 📝 OK (the trim comes after the try block).

---

## 📊 Summary of Batch 103 (lines 1–954, ~52% of file)

### By severity
| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 9 |
| ⚠️ Data/safety risk | 30 |
| 🟡 Code smell | 15 |
| 📝 Doc-only | 3 |
| ✅ Good code | 11 |
| **Total** | **68 findings in lines 1–954** |

### Top 7 things to fix in this part of main.py

| # | Bug | Why | Fix difficulty |
|---|---|---|---|
| 1 | **BUG-M3** (subprocess seed runs on EVERY import) | Test isolation broken; tests can't import main; module-level mutation | Easy: move into `run()` |
| 2 | **BUG-M31** (multi-fire guard uses LOCAL date) | Wrong-date dedup at midnight; multi-fire guard fails on UTC vs ET boundary | Easy: use ET via ZoneInfo |
| 3 | **BUG-M46** (earnings-unknown picks treated as official) | 12 of 14 picks on May 11 had unknown earnings — production safety contradiction | Medium: route to watch_only OR skip |
| 4 | **BUG-M14 + M17** (artifact writes swallow ALL errors) | The TWO most important Lane 1 artifacts can silently disappear | Easy: log error to stderr loud |
| 5 | **BUG-M51** (sector cap = 2 but comment says 4) | Code/comment disagreement on diversification rule | Easy: pick one, fix the other, add config |
| 6 | **BUG-M30** (multi-fire guard reads ALL CSV rows) | O(n) on every run; degrades over years | Easy: read just last few rows OR last-modified marker |
| 7 | **BUG-M50** (Unknown sector silently lumped) | Failed sector lookups crowd into "Unknown" bucket → unfair sector cap | Medium: skip cap for Unknown OR alert |

### What this part of main.py tells us about the project

- **Helpers above `run()` are well-documented but defensively brittle.** Bug-fix history in docstrings is excellent (BUG-M3 docstring explains May 11 fix). But the bare-except pattern is everywhere.
- **Module-level subprocess (BUG-M3) is the worst architectural choice in this file.** Tests cannot cleanly import main. Every import seeds wisdom.
- **Lane 1 artifact writes (no-pick + diagnostics) are NOT atomic and silently swallow failures.** This contradicts the discipline of `scripts/backfill_*` (Batch 3a) which all do atomic writes. The most important artifacts have the weakest writers.
- **Date handling is broken at the multi-fire guard** (BUG-M31). Combined with X-IO3/X-TG6/BUG-PC3 pattern from earlier batches, **this codebase has at least 8 known wrong-clock bugs.** A single `repo_now_et()` helper would fix the family.
- **Earnings-unknown handling contradicts the audit's intent.** Backfills correctly skip; main.py includes them with a print. The documented bug (BUG-77 referenced in Batch 3a) is REAL and confirmed here at line 869.
- **Magic thresholds everywhere**: `< 5` days, `>= 0.01` boost, `4*` buffer, `3*` early-stop, `2/sector`, `2/tag`, `0.88/0.12` blend. None are config-driven.

### What's left for Part 2 (lines 955–1817, ~862 lines)

- Hard blocks (apply_hard_blocks)
- Probability engine + EV gate
- Auto-pause faculty
- Smell faculty
- Trade-type tagging + watch-only stamping
- Premarket sanity gate
- Portfolio risk gate
- Missing-data fail-closed gate
- Candidate diagnostics builder
- Official pick artifact writer
- Display table + LLM rationales
- Monster treatment
- picks_log.csv writer (the big append loop)
- Signal journal logger
- Pause-signal output

---

**End of Batch 103.**

Cumulative findings across all code batches (1a/1b/2a/2b/3a/3b/3c/3d/3e/4/5/103):
- 🚨 Show-stoppers: **132** (123 + 9)
- ⚠️ Data/safety risks: **280** (250 + 30)
- 🟡 Code smells: **219** (204 + 15)
- 📝 Doc-only: **17** (14 + 3)
- ✅ Good code: **271+** (260 + 11)
- **Total: ~919 findings across 299 files, ~25,700 lines of code line-audited**
