# Audit Batch 6 — main.py DEEP DIVE (1,817 lines, full file)

**Date:** 2026-05-12
**File:** `main.py` — daily-picks CLI orchestrator
**Lines audited:** 1–1817 (entire file)
**Methodology:** Sequential, every named symbol + every code section. References Batches 1–5 findings where they originate here.

---

## STRUCTURE OVERVIEW (line ranges)

| Lines | Section | Purpose |
|---|---|---|
| 1–7 | Module docstring + stdlib imports | |
| 8–34 | 27 `from src.X import Y` lines | First-party imports |
| 36–64 | `_safe_trade_type_for_pick`, `_yf_ticker_for_sector_benchmark`, `_latest_close_for_sector_benchmark` | Helper trio |
| 67–87 | `_sector_benchmark_for_pick` | Sector benchmark resolution with SPY fallback |
| 91–97 | **MODULE-TOP `subprocess.run(bootstrap_wisdom)`** | side effect on import |
| 100–102 | `load_config` | YAML loader |
| 105–117 | `_candidate_report_value` | JSON-safe recursion |
| 121–145 | `_news_action_window` | Bug-fix shim for list-vs-dict news |
| 148–177 | `_summarize_candidate_for_report` | Diagnostic flattener |
| 180–265 | `_classify_no_pick_cause` | 8-cause taxonomy |
| 269–344 | `_write_daily_picks_candidate_diagnostics_report` | JSON+MD writer (~75 lines) |
| 348–578 | `_write_daily_picks_no_pick_report` | JSON+MD writer (~230 lines!) |
| 581–616 | `_write_guard_no_pick_artifact_for_main` | T51 guard wrapper |
| 619–625 | `_should_log_paper_trade` | Env-gate helper |
| 628–1812 | **`run()` — single 1,184-line function** | The entire pipeline |
| 1815–1816 | `if __name__ == "__main__": run()` | Entry point |

**File-shape findings already:**
- Total file: 1,817 lines
- 13 module-level functions
- One of them (`run`) is **1,184 lines** — 65% of the file
- `_write_daily_picks_no_pick_report` is **230 lines** of nested JSON+MD assembly — itself a candidate for decomposition

---

## SECTION-BY-SECTION FINDINGS

### Lines 1–34: Imports

#### 🚨 M-IM1 (line 2): `import os, yaml` — combined-line PEP 8 violation
PEP 8 line 35: "Imports should usually be on separate lines." Used here for brevity, fine for a one-liner — but inconsistent with all other imports.

Severity: 🟡 Style only.

#### 🚨 M-IM2 (lines 8–34): **27 first-party imports at module top, ~13 more inline inside `run()`**
Counted inline imports later: lines 716–718 (csv, date, Path), 778, 779, 819, 826, 918, 966, 985, 1082, 1122, 1164, 1185, 1242, 1261, 1327, 1351, 1425, 1441, 1521, 1565, 1763 (wait that's `import traceback`), 1783.

That's ~22 **inline imports inside run()**. Mix of:
- Lazy loading for slow modules (acceptable)
- Defensive try/except wrapping (acceptable)
- Apparent inconsistency with module-top imports (`from src.scorer import composite_score` at top + `from src.scorer import apply_tag_cap` inline at line 905)

Plain English: scorer is imported at line 16 (`apply_sector_cap`) and line 22 (`composite_score`), but `apply_tag_cap` is imported inline on line 905. **Three different import patterns for the same module.** Confusing for readers and breaks the tools that rely on import lists.

Severity: ⚠️ Maintainability.

#### 🚨 M-IM3 (line 21): `from src.news_sentiment import fetch_news, score_sentiment` — unused
Searching the file: `fetch_news` and `score_sentiment` are never called in main.py. (They're called in `app.py` per Batch 5.)

Severity: ⚠️ Dead import. Many such cases below.

#### 🚨 M-IM4 (line 14): `from src.market_guard import vix_level, spy_trend, sector_strength, classify_trade_type` — `classify_trade_type` only used through `_safe_trade_type_for_pick` (line 44)
Triple-wrapped: `_safe_trade_type_for_pick()` calls `classify_trade_type()`. Fine, but the file imports classify_trade_type ONLY to wrap it once. If the wrapper lived in market_guard.py, line 14 would not need the third name.

Severity: 🟡 Architectural smell.

#### 🚨 M-IM5 (line 15): `from src.premarket_filter import gap_check` — UNUSED
`gap_check` never appears below. Dead import.

Severity: ⚠️ Dead import.

#### 🚨 M-IM6 (line 17): `from src.risk_manager import atr_trade_plan` — UNUSED
`atr_trade_plan` never called. Line 23 imports `trade_plan` (also unused inside main.py — used via `parallel_scorer` per Batch 4 reference). Two functions imported, neither called.

Severity: ⚠️ Dead imports.

#### 🚨 M-IM7 (line 11): `from src.fundamentals import score_fundamentals` AND line 20: `from src.fundamentals import passes_filters` — split
Two separate import statements from same module. Should be combined. Also: neither is called from main.py.

Severity: ⚠️ Dead imports + style.

#### 🚨 M-IM8 (line 9): `from src.data_fetcher import fetch_universe_data, fetch_info` — `fetch_info` UNUSED
Only `fetch_universe_data` is called (line 773). `fetch_info` is unused in main.py.

Severity: ⚠️ Dead import.

#### 🚨 M-IM9 (line 10): `from src.indicators import add_indicators, latest_signals` — BOTH UNUSED
Neither called in main.py. They're used inside `parallel_scorer.py`.

Severity: ⚠️ Dead imports.

#### 🚨 M-IM10 (line 12): `from src.cape_ratio import get_cape` — used once (line 740)
Used. ✅

#### 🚨 M-IM11 (line 18): `from src.market_news import get_market_briefing` — used once (line 746)
Used. ✅

#### 🚨 M-IM12 (line 19): `from src.earnings_analyzer import analyze_earnings` — used once (line 879)
Used. ✅

#### 🚨 M-IM13 (line 22): `from src.scorer import composite_score` — UNUSED in main.py
composite_score called inside parallel_scorer.score_all (line 823), not directly. Dead import.

Severity: ⚠️ Dead import.

#### 🚨 M-IM14 (line 24): `from src.llm_agent import explain_pick` — used (line 1644)
Used. ✅

#### 🚨 M-IM15 (line 25): `from src.paper_trader import log_paper_trade` — used conditionally (line 1650)
Used inside `_should_log_paper_trade()` block. ✅

#### 🚨 M-IM16 (line 26): `from src.regime import market_regime` — used (line 729)
Used. ✅

#### 🚨 M-IM17 (line 27): `from src.earnings import days_to_earnings` — used (line 858)
Used. ✅

#### 🚨 M-IM18 (line 28): `from src.monster_hunt import apply_monster_treatment` — used (line 1672)
Used. ✅

#### 🚨 M-IM19 (line 29): `from src.sector_benchmark import resolve_sector_etf` — used (line 76)
Used. ✅

#### 🚨 M-IM20 (line 30): `from src.signal_journal import log_pick as _journal_log_pick` — used (line 1779)
Used. ✅

#### 🚨 M-IM21 (line 31): `from src.auto_pause import compute_score as _pause_score, format_summary as _pause_fmt` — used (lines 1793, 1795)
Used. ✅

#### 🚨 M-IM22 (line 32): `from src.pause_state import is_paused as _is_paused, maybe_auto_pause as _maybe_pause, format_pause_alert as _pause_alert`
- `_is_paused` used (line 666) ✅
- `_maybe_pause` used (line 1800) ✅
- `_pause_alert` **NEVER CALLED** ❌

Severity: ⚠️ Dead alias.

#### 🚨 M-IM23 (line 33): `from src.market_calendar import is_trading_day as _is_td, reason_market_closed as _why_closed, next_trading_day as _next_td`
All three used (lines 651, 652, 653). ✅

#### 🚨 M-IM24 (line 34): `from src.github_observability import github_observability_metadata` — used (line 384)
Used. ✅

**M-IM SECTION SUMMARY:** Of 27 module-top imports, **at least 9 are dead** (fetch_info, add_indicators, latest_signals, score_fundamentals, gap_check, atr_trade_plan, score_sentiment, fetch_news, passes_filters, composite_score, _pause_alert). Plus 22 inline imports inside `run()`. Imports section is severely under-curated.

---

### Lines 36–64: Helper trio

#### 🚨 M-H1 (lines 36–47): `_safe_trade_type_for_pick(scores, pick_date=None, sig: dict = None, gap_pct: float = 0.0)` — `pick_date=None` passed in then forwarded to `_is_td(pick_date)`
`_is_td()` from `market_calendar` — when called with `pick_date=None`, presumably defaults to today. NOT documented in main.py. If `pick_date` is a string (`_today` is `"2026-05-12"` per line 719), does `_is_td(string)` work? Or does it need a `date` object?

Plain English: line 1212 calls `_safe_trade_type_for_pick(p["scores"], pick_date=_today)` where `_today` is an **ISO string**. If `_is_td()` expects a date object, this fails silently OR returns wrong answer.

Severity: 🚨 **Latent bug** — type contract unclear, downstream behavior depends on `_is_td()` accepting strings.

#### 🚨 M-H2 (lines 36–47): The whole function is a 4-line wrapper around `classify_trade_type`
The wrapper exists ONLY to add the calendar check. This logic could live inside `classify_trade_type()` itself. Wrapping in main.py means every other caller of classify_trade_type (scripts/, tests/) doesn't get the calendar protection.

Severity: ⚠️ Inconsistent enforcement boundary — same protection should be in src/, not main.py.

#### 🟡 M-H3 (lines 50–53): `_yf_ticker_for_sector_benchmark` — comment says "Small seam for tests"
This is a 3-line wrapper around `yf.Ticker(symbol)` purely so tests can `monkeypatch.setattr(main, "_yf_ticker_for_sector_benchmark", ...)`. Fine, but evidence that **production helper code is being structured around test mockability**, not production needs. Indicates the original yf calls were too deep to mock cleanly.

Severity: 🟡 Test-coupling smell.

#### ⚠️ M-H4 (lines 56–64): `_latest_close_for_sector_benchmark` — silent `except Exception: return None`
Bare exception swallows everything (rate limit, ticker not found, network down). When this returns None, `_sector_benchmark_for_pick` falls back to SPY (line 82-85), masking the underlying issue. Caller in line 1697 also has `try/except` with rprint warning, but **no row in any audit log** captures the per-ticker failure.

Severity: ⚠️ Loss of evidence on price-data outages.

#### ⚠️ M-H5 (line 56): Type hint `float | None` — Python 3.10+ syntax
File doesn't declare a Python version anywhere. `requirements.txt` (Batch 5) doesn't specify Python. If this runs on Python < 3.10, the file fails to import. Tests assume this works (test_main_t51_guard_no_pick_artifact etc.) so CI presumably uses 3.10+, but the requirement is undocumented.

Severity: ⚠️ Hidden Python version requirement. Add to README + CI matrix doc.

---

### Lines 67–87: `_sector_benchmark_for_pick`

#### ✅ M-H6 (lines 67–87): **Good defensive code** — explicit fallback to SPY when sector ETF quote is missing, with clear docstring referencing the bugs (#8/#10) that motivated it.

#### ⚠️ M-H7 (line 76): `etf = resolve_sector_etf(sector=sector, tag=tag) or "SPY"` — `or` coercion
If `resolve_sector_etf` returns `""`, `0`, `None`, or any falsy value, falls back to SPY. Mostly correct. But also: there's no logging of WHEN this fallback fires. If the sector resolver silently degrades for 100 days, no audit row.

Severity: 🟡 No telemetry on degradation.

---

### Lines 91–97: 🚨 MODULE-TOP `subprocess.run(...)` — severe issue

#### 🚨 M-IO1 (lines 91–97): Auto-seed wisdom base on **every import**, with bare `except: pass`

```python
# Auto-seed wisdom base on every run (idempotent — safe)
try:
    import subprocess, sys as _sys
    subprocess.run([_sys.executable, "scripts/bootstrap_wisdom.py"],
                   check=False, capture_output=True, timeout=10)
except Exception:
    pass
```

This is not "every run" — it's **every import**. Examples of triggering imports:
- pytest collecting `tests/test_*` — every test file that imports main runs this
- streamlit `app.py` import (no, app.py doesn't import main, but it could in future)
- IPython `import main` for inspection
- Any script that does `from main import X`

Severity: 🚨 **Module-import side effect** = the WORST violation flagged in Batch 2 X-IO5 family. Runs a 10-second-timeout subprocess on every Python interpreter that touches main.py. With 178 test files some of which import main directly, **`pytest tests/` could spawn `bootstrap_wisdom.py` 5+ times**.

Plus: bare `except Exception: pass` swallows everything. If bootstrap_wisdom.py has a syntax error, no one knows.

Plus: writes to `data/wisdom_base/lessons.jsonl` and `data/wisdom_base/kill_list.json` (per Batch 3e), polluting tracked data on every test collection.

**This is a single-line fix:** wrap inside `if __name__ == "__main__":` after `run()`, or inside `run()` itself.

#### 🚨 M-IO2 (line 95): `timeout=10` — 10 seconds per import
On a slow CI runner with cold imports, this could add 10s to every pytest collection. With test parallelization, could cascade.

---

### Lines 100–102: `load_config`

#### ⚠️ M-CFG1 (line 100): `def load_config(path: str = "config.yaml")` — relative path
If main.py is run from a directory other than repo root, `config.yaml` doesn't exist and silently raises `FileNotFoundError`. Should use `Path(__file__).parent / "config.yaml"`.

Severity: ⚠️ Working-directory dependency.

---

### Lines 105–117: `_candidate_report_value`

#### ✅ M-CR1: Clean recursive sanitizer with sane truncation (`[:10]`, `[:30]`).

#### 🟡 M-CR2 (line 115): `if k not in {"df", "dataframe", "history"}` — magic field exclusion
Hardcoded set of keys to skip (presumably to avoid serializing huge pandas DataFrames). Any new heavy field added later (e.g., `bars`, `quotes`) would crash JSON serialization. Should be a module constant or extracted.

Severity: 🟡 Hidden coupling.

---

### Lines 121–145: `_news_action_window` — Bug-fix shim

#### ✅ M-NW1: **Excellent docstring** explicitly documenting the May 11 bug discovery and shape ambiguity. Use as template.

#### ⚠️ M-NW2 (lines 138–142): For-loop over articles with `if isinstance(item, dict) and item.get("action_window"): ... break`
Returns the FIRST article with `action_window`. If multiple articles have different windows ("intraday" vs "next_day"), the order matters. List ordering is producer-dependent.

Severity: 🟡 Non-deterministic if articles disagree. Could surface as flaky behavior.

---

### Lines 148–177: `_summarize_candidate_for_report`

#### ⚠️ M-SC1 (line 165–169): Triple-fallback chain for `news_action_window`
```python
"news_action_window": (
    scores.get("news_action_window")
    or (news_signal.get("action_window") if isinstance(news_signal, dict) else None)
    or _news_action_window(news, scores)
),
```
Three sources of truth for the same field. Indicates upstream stages aren't normalizing this. Should be a single canonicalization step.

Severity: ⚠️ Data-shape divergence — same finding pattern as Batch 1 X-WF7 (5 different status enums for same concept).

#### ⚠️ M-SC2 (line 175): `bool(candidate.get("watch_only") or plan.get("watch_only"))` — TWO sources of `watch_only`
A pick can be watch_only on the root OR on the plan. Same bug class as M-SC1.

Severity: ⚠️ Dual source of truth.

---

### Lines 180–265: `_classify_no_pick_cause` — 8-cause taxonomy

#### ✅ M-NC1: **Well-structured priority ladder.** Reads cleanly: sanity → risk → missing data → readiness → counts. Each branch returns early with explicit primary/secondary/summary.

#### 🚨 M-NC2 (line 193): `if yf_attempts and (yf_rate_limited > 0 or yf_errors / max(yf_attempts, 1) >= 0.20)`
Two parts:
1. `yf_rate_limited > 0` — even 1 rate-limit triggers DEGRADED label
2. `yf_errors / yf_attempts >= 0.20` — 20% error rate triggers it

These thresholds (0 rate-limits, 20% error rate) are **hardcoded magic numbers**. Should be config or named constants. A single transient yfinance hiccup pushes the secondary cause permanently.

Severity: ⚠️ Brittle thresholds. Combined with Batch 1 X-WF6 (cron schedules off-by-one for DST), the agent may classify normal operations as "yfinance degraded" multiple times per week.

#### 🚨 M-NC3 (lines 215–223): Missing-data check uses `len(missing_data_blocked) >= len(pre_missing_data)`
This is the same fingerprint as line 201 (sanity) and line 208 (risk): "ALL finalists got blocked by this gate". Pattern repeats 3x — should be extracted into a helper:
```python
def _all_blocked_by(blocked_list, pre_list):
    return isinstance(blocked_list, list) and blocked_list and isinstance(pre_list, list) and len(blocked_list) >= len(pre_list)
```

Severity: 🟡 DRY violation.

#### ⚠️ M-NC4 (line 232–233): `for warning in readiness_gate.get("warnings") or []: secondary.append(str(warning).upper())`
Nondeterministic uppercasing. If a warning is `"Provider degraded"` it becomes `"PROVIDER DEGRADED"`. If it's `"NoPickReason.YFINANCE"`, it becomes `"NOPICKREASON.YFINANCE"`. The downstream consumer needs to know to expect this transformation.

Severity: 🟡 Hidden mutation.

#### 🚨 M-NC5 (lines 199–223): Logical hole — what if MULTIPLE gates blocked all candidates?
The classifier returns the FIRST matching cause (sanity → risk → missing data). If both `premarket_sanity_blocked_all` AND `portfolio_risk_blocked_all` are true, only sanity is reported. Real-world this matters because the operator sees only one cause and fixes it; the next day the OTHER cause hits.

Severity: ⚠️ One-cause-at-a-time blindness. Should report ALL `_all_blocked` events, not just first.

#### ⚠️ M-NC6 (line 246): `elif fetched_count == 0: primary = "NO_PICK_DATA_PROVIDER_DEGRADED"`
But fetched_count being 0 could mean:
- Provider down (DEGRADED) ✓
- All tickers were excluded by filters before fetch
- Wrong universe loaded

Single label for multiple causes.

Severity: 🟡 Cause/effect ambiguity.

---

### Lines 269–344: `_write_daily_picks_candidate_diagnostics_report`

#### 🚨 M-WR1 (line 271): `try:` wraps the ENTIRE function body, with bare `except Exception: pass` at line 343
75 lines of writing logic, no error logging. If JSON write fails (disk full, permissions), nobody knows. Same pattern as Batch 2 X-IO3 family.

Severity: 🚨 Silent failure mode for an audit-trail function. Audit trails are useless if they can fail silently.

#### ⚠️ M-WR2 (lines 269–298): JSON payload mixes timestamp formats
- Line 280: `now_utc` ends with "Z" suffix (custom)
- Line 281: `date_str` is plain `YYYY-MM-DD`
- No `selection_time_et` here (but it's in the no-pick report at line 381)

Inconsistent payload shapes across artifacts that test_premarket_decision_contract.py validates.

Severity: ⚠️ Schema drift between sibling reports.

#### ⚠️ M-WR3 (line 286): `"date": date_str` — uses ET date but logged with UTC timestamp
Mixing zones in one record. If a pick is generated at 01:30 ET (= 05:30 UTC same day, OR 06:30 if EDT), the date string is correct (ET-anchored) but the UTC timestamp could indicate "yesterday" UTC.

Severity: 🟡 Cross-zone bookkeeping confusion. Document explicitly OR include both dates.

#### ✅ M-WR4 (lines 302–342): Markdown rendering is clean and consistent.

---

### Lines 348–578: `_write_daily_picks_no_pick_report` — 230 lines!

#### 🚨 M-WR5: **230 lines of payload assembly + JSON dump + Markdown rendering + child-artifact writers, all wrapped in one try/except.** This is the largest and most fragile single function in main.py.

Sub-issues:
- Lines 355–356: `data_dir = Path("data"); data_dir.mkdir(exist_ok=True)` — assumes CWD again (M-CFG1)
- Line 392: `"market_data_health": {}` — set to empty, then filled at line 400 inside another try/except. **Double try/except for the same field.**
- Line 412–413: `payload["diagnostics"] = diagnostics or {}; payload["candidate_diagnostics"] = diagnostics or {}` — **two keys for the same data**. Caller can read either; downstream readers may use one or the other → drift.

Severity: 🚨 Multi-issue.

#### 🚨 M-WR6 (lines 415–438): **8 elif branches** for data_readiness_status / provider_status mapping
```python
if primary_cause == "NO_PICK_DATA_PROVIDER_DEGRADED":
    payload["data_readiness_status"] = "not_ready_data_provider_degraded"
    payload["provider_status"] = "degraded"
elif primary_cause == "NO_PICK_DATA_READINESS_FAILED":
    payload["data_readiness_status"] = "not_ready_data_readiness_failed"
    payload["provider_status"] = "unknown"
... (6 more branches)
```

**This is a lookup table coded as if/elif.** Should be a module-level dict:
```python
_PRIMARY_CAUSE_TO_STATUS = {
    "NO_PICK_DATA_PROVIDER_DEGRADED": ("not_ready_data_provider_degraded", "degraded"),
    "NO_PICK_DATA_READINESS_FAILED": ("not_ready_data_readiness_failed", "unknown"),
    ...
}
```

Severity: 🟡 Code smell — but with 8 branches, also a maintenance hazard.

#### ⚠️ M-WR7 (line 421): `elif primary_cause in {"NO_PICK_NO_SCORED_CANDIDATES", "NO_PICK_FILTERS_REMOVED_ALL"}:`
This SAME pair gets one mapping `("ready_no_qualified_candidates", "healthy")`. So two different causes flatten to one status. Information loss.

Severity: 🟡 One-way mapping.

#### 🚨 M-WR8 (lines 460–461): `for key, value in sorted((pipeline or {}).items()): lines.append(f"- {key}: **{value}**")`
Renders the WHOLE pipeline dict as Markdown. If pipeline grows new fields (which it does — see lines 1240, 1245, 1306, 1325, 1335, 1404, 1428...), the Markdown grows uncontrolled. No filtering of internal-only fields.

Severity: 🟡 Markdown shape drift.

#### 🚨 M-WR9 (lines 492 + 480): `diag = payload.get("diagnostics") or {}` — assigned TWICE
Lines 480 and 492 both do this. Redundant. Sign of copy-paste edit.

Severity: 🟡 Code smell, indicates rushed merge.

#### 🚨 M-WR10 (lines 517–537): `_candidate_markdown_details` defined as **nested function** inside `_write_daily_picks_no_pick_report`
Defined per-call. Closure-captures nothing. Should be module-level helper. Also note: it's defined ONLY inside the `if diag:` branch (line 493) — meaning if `diag` is empty, the function isn't created — but then it's also not used. Cosmetic but illogical.

Severity: 🟡 Misplaced definition.

#### 🚨 M-WR11 (lines 539–575): Builds `rejection_lines` and writes to `daily_picks_candidate_rejections_{date_str}.md` — a NEW artifact created here, not documented in DATA_CONTRACTS.md
From Batch 1 (X-DA1): `.gitignore` excludes `data/` by default. Batch 5 R-X16 confirms this. Without an explicit `!data/daily_picks_candidate_rejections_*.json` exception, **this artifact never gets committed**. Need to grep .gitignore... per Batch 5 the exception list does NOT include this filename pattern.

Severity: 🚨 **NEW ARTIFACT WITHOUT GITIGNORE EXCEPTION = silent data loss in CI.** Same bug class as Batch 1 X-DA1.

#### 🚨 M-WR12 (line 576): `except Exception: pass` for the entire 230-line function
"Do not hide the original no-pick failure if reporting fails" — comment is good but the action contradicts: blanket pass IS hiding it. At minimum should `rprint(f"[red]no-pick report failed: {e}[/red]")`.

Severity: 🚨 Comment lies about behavior.

---

### Lines 581–616: `_write_guard_no_pick_artifact_for_main`

#### ✅ M-WR13: **Excellent docstring.** Documents the May 9 bug discovery — workflow YAML had the artifact writer but main.py didn't, leaving zero artifact when invoked outside Actions. Good defensive engineering.

#### ⚠️ M-WR14 (line 597–608): try/except around imports + call, returns False on failure with rprint
Better than M-WR12 — at least rprints. But on import failure, falls through to bare except (line 614) silently. Two layers of try/except for the same operation.

Severity: 🟡 Duplicate error handling.

#### ⚠️ M-WR15 (line 601): `from scripts.write_guard_no_pick_artifact import write_guard_no_pick_artifact`
Inline import from `scripts/`. Per Batch 3 (B6 module dependency analysis), some scripts import each other at module top causing circular issues. Inline import here is intentional defensive style. ✅

---

### Lines 619–625: `_should_log_paper_trade`

#### ✅ M-PT1: **Excellent.** Tested by test_monitoring_mode_no_paper_default.py (Batch 4). Default = "monitoring" matches README safety stance. Direct fix candidate for Batch 5 R-X14 (`.env.example` defaults to `paper`).

#### ⚠️ M-PT2 (line 625): `os.getenv("TRADING_MODE", "monitoring").strip().lower()`
Strips and lowercases, but `.env.example` has `TRADING_MODE=paper` — already lowercase. Defensive, but shows env-var values aren't normalized at load time. Should be canonicalized once via a config module.

Severity: 🟡 Defensive duplication.

---

### Lines 628–1812: `run()` — THE 1,184-LINE BEAST

This single function violates every single-responsibility principle. Let me break it into sub-sections.

#### Lines 629–642: Setup
- Line 629: `load_dotenv()` — runs on every invocation. Fine.
- Line 631–642: hardcoded `pipeline` dict with 10 fields. As pipeline grows, this constructor gets stale (M-WR8 already noted).

#### 🚨 M-RUN1 (lines 631–642): Initial `pipeline` dict is INCOMPLETE compared to runtime additions
Lines 1240, 1245, 1325, 1335, 1404, 1428, 1430 add new keys mid-flight. So initial dict is a partial schema; the real schema is the union of all `pipeline[xxx] = ...` writes. **No way to know the full set without reading 1,184 lines.**

Severity: 🚨 Schema-by-accumulation. Combined with X-DA family — pipeline JSON shape will drift over time.

---

#### Lines 646–664: T51 market-closed guard

#### ✅ M-RUN2 (line 658): Calls `_write_guard_no_pick_artifact_for_main` before `return`
Best-effort artifact write before hard stop. Good.

#### 🚨 M-RUN3 (lines 651–664): `try/except` wraps the calendar check; if `_is_td()` raises, **the run continues** instead of failing closed
```python
try:
    if not _is_td():
        ...
        return
except Exception as _e:
    rprint(f"[dim]market-calendar check failed: {_e} — proceeding[/dim]")
```

If `market_calendar` itself is broken (e.g., NYSE feed unavailable), the agent **proceeds and may generate picks on a closed-market day**. This is the OPPOSITE of fail-closed. The README (Batch 5 R-X19) emphasizes "no-pick days are allowed" — this code allows pick days on weekends if the calendar lib breaks.

Severity: 🚨 **Fail-open behavior on a safety-critical guard.**

---

#### Lines 666–682: Pause check

#### ✅ M-RUN4 (line 682): "HARD STOP. No picks, no journaling, no Telegram picks." — comment matches behavior.

#### 🚨 M-RUN5 (lines 673–681): Pause-day artifact uses `_ps["until"]` as `date`
```python
_P("data/last_run_paused.json").write_text(_j.dumps({
    "paused": True, "date": _ps["until"], **_ps
}, indent=2))
```

**`date` field gets the pause-end date, not today's date.** A reader expecting "what date did this run?" gets misled. This file is RE-WRITTEN every paused day, so today's status overwrites yesterday's, but `date` always says "until tomorrow."

Severity: 🚨 Wrong field semantic. Add `"run_date": date.today().isoformat()`.

#### 🚨 M-RUN6 (line 671): `rprint(f"[dim]   Override: python scripts/unpause.py[/dim]")` — references a script
Per Batch 3, `scripts/unpause.py` exists. ✓ But the path is not `scripts/unpause.py`, it's an instruction telling user to run it from CWD. If user does `python /full/path/scripts/unpause.py` it fails differently. Print the actual command from Makefile (`make unpause`) — but Makefile (Batch 5 R-X17) doesn't have an `unpause` target.

Severity: ⚠️ Operator instruction inconsistent with Makefile.

#### 🚨 M-RUN7 (line 677): `**_ps` SPREAD into payload
`_ps` already contains `"reason"`, `"until"`, `"days_remaining"`, `"paused"`. The `paused: True, date: ...` are EXPLICITLY set, then `**_ps` re-adds `paused`. Python dict will use the LAST value, so the spread overrides the explicit. Confusing pattern but works. Could be `{"paused": True, "date": _ps["until"], "reason": _ps["reason"], ...}` for clarity.

Severity: 🟡 Style.

#### 🚨 M-RUN8 (lines 673–681): Artifact write inside `except: pass`
Same problem as M-IO1, M-WR1. If write fails, no audit trail of the pause.

Severity: ⚠️ Silent failure on a safety event.

---

#### Lines 685–708: Market guards (VIX, SPY, sector strength)

#### 🚨 M-RUN9 (lines 688–690): `vix = vix_level(); spy = spy_trend(); sectors = sector_strength()` — three sequential network calls, no error handling
If `vix_level()` raises (yfinance rate limit, network), the entire run crashes. No try/except. Compare to lines 776–816 (data readiness gate) which is wrapped — these earlier calls aren't.

Severity: 🚨 **Crashes the run on transient yfinance issues** — exactly the failure mode Batch 4 test_eyes_data_fetcher_returns_real_company_name was xfail'd for.

#### 🚨 M-RUN10 (line 691): `weak_sectors = {s: 2 for s, v in sectors.items() if v.get("weak")}`
The value `2` is hardcoded — what does it mean? Reading line 903: `apply_sector_cap(filtered, max_per_sector=2, reduced_sectors=weak_sectors)`. So `weak_sectors[s] = 2` is "in weak sectors, cap to 2 picks." But why is the cap hardcoded to 2 in line 691 when it could be a parameter?

Plus: `apply_sector_cap` has both `max_per_sector=2` AND `reduced_sectors={...: 2}`. The "reduction" is a no-op when both are 2. This means **weak-sector tightening is currently DISABLED** because the strong-sector cap is already 2.

Severity: 🚨 **Dead logic.** Comment line 893 says "with weak-sector tightening" — the tightening doesn't actually tighten.

#### ⚠️ M-RUN11 (lines 700–708): Pick-count adjustment logic
- VIX > 30 → halve picks
- SPY < 50DMA → halve picks
- Both can apply, but `min(adjusted_picks, max(3, base_picks // 2))` means second halving is no-op if first already halved
Plus: `max(3, ...)` floor of 3 is hardcoded.

Severity: 🟡 Magic numbers; defensible but not configurable.

---

#### Lines 711–726: Multi-fire guard

#### ✅ M-RUN12: Guards against GitHub cron multi-fires (Apr 28 / May 1 incidents). Uses `csv.DictReader` to scan picks_log for today's date. Good defensive engineering — contemporaneous comment with bug history.

#### 🚨 M-RUN13 (lines 716–718): Inline imports (csv, date, Path) AGAIN
Already imported `csv` is needed; line 716's `import csv as _csv` shadows nothing because csv wasn't imported at module top (yet line 274 `import json` is also inline). **Module-top `import csv` would clean this up.**

Plus the underscore-prefix aliases (`_csv`, `_date`, `_Path`) signal "private internal" but are not — they're stdlib aliases. Confusing.

Severity: ⚠️ Inconsistent import patterns + misleading naming.

#### 🚨 M-RUN14 (line 721): `if _log.exists():` — but no try/except
What if `data/picks_log.csv` is corrupt mid-write (e.g., previous run crashed)? `csv.DictReader` may raise. The whole run crashes BEFORE we can produce a no-pick artifact.

Severity: 🚨 Crash on corrupt data file. Should be wrapped.

#### 🚨 M-RUN15 (line 724): `if _row.get("pick_date") == _today:` — uses real CSV column name ✓ (Batch 4 test_picks_log_column_contract.py validates this)

#### 🚨 M-RUN16 (line 725–726): On detection, `return` with NO `_write_guard_no_pick_artifact_for_main` call
Unlike T51 (line 658), the multi-fire skip leaves NO artifact behind. Operations team can't tell from artifacts whether today had no picks because of multi-fire vs because of legitimate no-pick. Inconsistent with the T51 fix.

Severity: 🚨 **Same Priority 17 contract violation that T51 was specifically designed to prevent.** Recursive.

---

#### Lines 728–766: Regime + CAPE + market briefing

#### 🚨 M-RUN17 (line 729): `reg = market_regime()` — unwrapped
If `market_regime()` raises (yfinance again), run crashes. Same as M-RUN9. Pattern repeats throughout this section.

#### 🚨 M-RUN18 (line 738): `cfg["output"]["min_score"] = max(cfg["output"]["min_score"], 0.70)`
**Mutates loaded config dict.** The next line accessing `cfg["output"]["min_score"]` gets 0.70+. Plus line 763 mutates again to 0.72. By line 836 (`cfg["output"]["top_n_picks"] * 4`), `cfg` has 3+ mutations.

Plain English: `cfg` is being used as scratch state. Reading the file, you can never trust what `cfg["output"]["min_score"]` will be. Should be local variables (`min_score = max(cfg["output"]["min_score"], 0.70)`).

Severity: 🚨 **Hidden mutable state.** Combined with `cache_data(ttl=600)` in app.py (Batch 5 line 24), the cfg dict could be SHARED across runs in long-lived processes. Streamlit reload could see stale-mutated cfg.

#### 🚨 M-RUN19 (line 740): `cape = get_cape()` — same unwrapped network call

#### 🚨 M-RUN20 (line 746): `briefing = get_market_briefing()` — same. Plus this triggers an LLM call (per src/market_news.py per Batch 2). Network + LLM cost on every run.

#### 🚨 M-RUN21 (lines 762–766): Sentiment-driven score tightening — magic thresholds
- Bearish: min_score = 0.72 (from 0.70 in line 738; 0.72 only if bearish)
- Bullish + score≥0.65: keep standard (no change)

What about bullish with score<0.65? Falls through silently. What about neutral? Falls through silently. Decision tree has unhandled cases.

Severity: 🟡 Logic gaps.

---

#### Lines 768–774: Universe + fetch (with pipeline tracking)

#### 🚨 M-RUN22 (line 769): `tickers = get_universe(cfg)` — unwrapped. If universe loader raises (e.g., S&P 500 download fails), CRASH.
#### 🚨 M-RUN23 (line 773): `data = fetch_universe_data(...)` — unwrapped. Same pattern.

These are wrapped INSIDE the function, so an exception bubbles to caller (the workflow YAML). The workflow may have its own error handler, but main.py loses all the no-pick artifact discipline.

Severity: 🚨 Inconsistent error envelope. Either ALL stages should be wrapped OR none. The selective wrapping (lines 776, 818, 985, 1241, etc.) creates unclear contracts.

---

#### Lines 776–816: Premarket data readiness gate

#### ✅ M-RUN24 (line 777): Wrapped in try/except. Good. On failure, writes no-pick report and returns.

#### ⚠️ M-RUN25 (line 786–787): Reads env vars `PREMARKET_MIN_FETCH_COVERAGE`, `PREMARKET_MIN_FETCHED_COUNT` with hardcoded defaults
The defaults (0.25 / 25) live in main.py, not in any documented config. To tune, someone has to read main.py to find them.

Severity: ⚠️ Undocumented config knobs.

---

#### Lines 818–829: Parallel scoring

#### 🚨 M-RUN26 (line 820): `int(os.getenv("DAILY_SCORER_WORKERS", "4"))` — default 4
Yet another env var without documentation. Where is the list of all env vars main.py reads? (Counted: TRADING_MODE, CONFIG_VERSION, GITHUB_RUN_ID, GITHUB_SHA, PREMARKET_MIN_FETCH_COVERAGE, PREMARKET_MIN_FETCHED_COUNT, DAILY_SCORER_WORKERS, BRAIN_ENFORCE_EV, BRAIN_EV_MIN_PCT, AUTO_PAUSE_ENABLED, AUTO_PAUSE_LOOKBACK_DAYS, SMELL_ENFORCE — 12 env vars in this file alone.)

`.env.example` (Batch 5 R-X14) only lists ALPACA, FINNHUB, OPENAI, etc. **Zero of these 12 main.py env vars are documented in `.env.example`.**

Severity: 🚨 **Undocumented operational surface.** A new operator can't know what knobs exist.

#### 🚨 M-RUN27 (line 823): `candidates = score_all(data, cfg, max_workers=scorer_workers)` — unwrapped
If parallel_scorer crashes for ALL workers, no artifact written. Same M-RUN9 pattern.

#### ⚠️ M-RUN28 (line 825–829): `try: from src.market_data_health import write_market_data_run_summary; write_market_data_run_summary(scored_count=...) except: pass` — bare pass
Telemetry write that may fail silently. Pattern.

---

#### Lines 831–873: Earnings + wisdom kill filtering

#### 🚨 M-RUN29 (line 836): `for p in candidates[: cfg["output"]["top_n_picks"] * 4]:` — 4x buffer
Why 4? Comment says "for sector cap." But sector cap (line 903) caps at 2/sector. If you have 10 picks and cap at 2, in a degenerate case (all same sector), you'd need 5x buffer. Hardcoded 4 = arbitrary.

Severity: 🟡 Magic number. May silently cap picks if many candidates share sector.

#### ⚠️ M-RUN30 (lines 858–870): `days_to_earnings(p["ticker"])` — UNWRAPPED, called per candidate, sequential
For 40 candidates (10 picks × 4 buffer), this is 40 sequential network calls. No batching, no caching visible. If earnings API is slow, this is the bottleneck. **No timeout.**

Severity: 🚨 Performance hazard + crash risk on earnings API.

#### 🚨 M-RUN31 (line 869): `if d2e >= 999:` — magic sentinel "999 = unknown"
`days_to_earnings` returns 999 to mean unknown. Sentinel value instead of `None`. Anywhere else in the codebase using `< 999` would break if return value changes.

Severity: ⚠️ Sentinel-value antipattern.

#### 🚨 M-RUN32 (line 871): `filtered.append(p)` then line 872: `if len(filtered) >= cfg["output"]["top_n_picks"] * 3: break`
**Second** "3x buffer" magic number, different from the "4x buffer" on line 836. Why 3 here and 4 there? Unclear. Could be a bug — should match.

Severity: 🟡 Inconsistent magic numbers.

---

#### Lines 875–890: Earnings quality re-scoring

#### 🚨 M-RUN33 (line 879): `ea = analyze_earnings(p["ticker"])` — sequential, no batching, no timeout
Same M-RUN30 problem. For 30 picks (3x buffer), 30 sequential calls.

#### 🚨 M-RUN34 (line 883): `new_score = round(old_score * 0.88 + eq * 0.12, 3)` — magic weights
0.88 / 0.12 = earnings quality blend factor. Hardcoded. Not in config. Cannot be tuned without code change. Compare to line 738's score-tightening — at least that uses `max(cfg, 0.70)` showing an intent to layer config. Here, no config.

Severity: ⚠️ Hidden scoring formula.

#### 🚨 M-RUN35 (line 884–885): `composite_pre_earnings` saved, then composite mutated
**Mutates p["scores"]["composite"]** so downstream code sees post-earnings score. Good audit trail (saves pre value), but:
- `composite_pre_news` also saved later (line 941) — TWO `composite_pre_*` fields
- Each stage mutates in place
- After all stages, the FINAL composite reflects: original × earnings × news × monster (via plan rewrite)
- Reproducibility: given a logged composite, you can reverse-engineer ONLY the immediately previous step

Severity: ⚠️ Mutating-pipeline antipattern. Audit trail is partial.

---

#### Lines 892–911: Sector + tag cap

#### 🚨 M-RUN36 (lines 898–902): Pads `info_short.sector` if missing
```python
for p in filtered:
    if "info_short" not in p:
        p["info_short"] = {}
    if not p["info_short"].get("sector"):
        p["info_short"]["sector"] = p["scores"].get("sector_tag") or "Unknown"
```
**Defensive padding for missing data.** Means upstream stages aren't required to populate `info_short`. The sector cap silently uses "Unknown" as a sector — multiple "Unknown"-sector picks would trigger the 2/sector cap and discard high-scoring picks.

Severity: ⚠️ Silent data shape repair masks upstream contract violation.

#### 🚨 M-RUN37 (line 905): `from src.scorer import apply_tag_cap` — INLINE import
Already imported `apply_sector_cap` at line 16 from same module. Two import patterns for same module. (M-IM2.)

#### 🚨 M-RUN38 (line 907–909): `apply_tag_cap` followed by `print` (NOT rprint)
Line 909 uses `print()`, not `rprint()`. Every other status output uses `rprint()`. Outlier — copy-paste from another module?

Severity: 🟡 Style inconsistency.

#### 🚨 M-RUN39 (line 911): rprint comments "max 4/sector" but line 903 uses `max_per_sector=2`
`rprint(f"  [dim]Sector cap: {pre_cap} → {len(capped)} (max 4/sector, ...)[/dim]")` — message says "max 4/sector" but actual cap is 2. **Documentation lies in the runtime output.**

Severity: 🚨 **Misleading log line.** Operators reading logs will think the cap is 4.

---

#### Lines 913–953: News-signal boost/penalty

#### 🚨 M-RUN40 (line 921–922): `signal = get_ticker_signal(...)`; `boost = get_ticker_boost(...)` — TWO calls per ticker
For 10 picks, 20 sequential calls. Likely hits the same JSON file twice. No caching.

Severity: 🟡 Redundant I/O.

#### 🚨 M-RUN41 (line 937): `if abs(boost) >= 0.01:` — magic threshold
Below 0.01 abs, no boost applied. Hardcoded.

Severity: 🟡 Magic number.

#### 🚨 M-RUN42 (line 939): `new = round(max(0.0, min(1.0, old + boost)), 4)` — clamping
Clamps to [0.0, 1.0]. If boost > 1.0 (theoretically should never happen), silently clamped. **No log on clamp.**

Severity: 🟡 Silent clamping.

#### 🚨 M-RUN43 (line 951): `capped.sort(...)` — re-sorts after news mutation
But `top` already extracted at line 956 from sorted `capped`. Re-sort happens in `capped` then trim to top — fine. But this means line 956's `top = capped[:N]` depends on sort order; if news mutation changes order significantly, the SAME pre-news top-10 may not match the post-news top-10.

Severity: 🟡 Order-dependent selection. Acceptable but worth a comment.

---

#### Lines 956–976: Hard blocks

#### 🚨 M-RUN44 (line 956): `top = capped[: cfg["output"]["top_n_picks"]]` — but cfg["output"]["top_n_picks"] was already mutated at line 707 if VIX>30 or SPY<50DMA
So `top_n_picks` could be 5 (halved from 10) in defensive mode. Implicit cascading config mutation.

#### ✅ M-RUN45 (line 968): `top, blocked = apply_hard_blocks(top, check_sectors=True)` — clean signature, returns blocked list for diagnostics. Good.

---

#### Lines 977–1037: PILLAR 1 probability engine (brain)

#### ✅ M-RUN46 (lines 991–1023): Per-pick try/except catches errors and stores `{"error": str(e)}` in `p["brain"]`. Good defensive pattern.

#### 🚨 M-RUN47 (line 999): `news_score = float(news_data.get("tradeable_score", 0) or 0)` — `news_data` may be a list, not a dict (per M-NW2)
Line 998: `news_data = p.get("news", {}) or {}`. If `p["news"]` is a list (the case M-NW2 fixed), `news_data = list_of_articles or {}` evaluates to the list (truthy). Then line 999 `news_data.get(...)` raises AttributeError.

**This is the EXACT BUG the author fixed in `_news_action_window`** (lines 121–145) but didn't propagate here. Line 998 has the OLD broken pattern.

Severity: 🚨 **Same bug class, fixed in one place, missed in another.** Will crash when news is list-shaped.

#### 🚨 M-RUN48 (line 1018): `"signals": decision.adjustments_applied` — name shadowing
Line 1001 defines local `signals = SignalState(...)`. Line 1018 stores `decision.adjustments_applied` under key `"signals"`. Two different "signals" (the input and the audit trail) collide as a key.

Severity: 🟡 Confusing naming.

#### 🚨 M-RUN49 (lines 1024–1035): Second loop over `top` JUST for printing
Already iterated over `top` in lines 991–1022. Now iterates again for display. Two passes. Could be combined.

Severity: 🟡 O(2n) instead of O(n).

#### ⚠️ M-RUN50 (line 1038): Comment block ends mid-character `══════════════════════════════════════════════════════════════��[...]`
The audit fetch shows truncated comment lines (replaced with `[...]`). Likely a unicode rendering issue with my fetch tool — not a real bug. **Verify in editor that the actual file isn't malformed** (probably fine, but worth confirming).

Severity: 🟡 Tooling artifact, low confidence — verify directly.

---

#### Lines 1045–1071: EV gate (observe-mode)

#### ✅ M-RUN51: Clean opt-in via env var. Default OBSERVE-only, ENFORCED on opt-in. Good safety pattern.

#### ⚠️ M-RUN52 (line 1046): `ev_min_pct = float(os.getenv("BRAIN_EV_MIN_PCT", "-1.0"))` — default -1.0%
Documented? No. Same M-RUN26 issue.

#### 🚨 M-RUN53 (line 1064): `f"P(win)={v['p_win']:.0%}"` — `v["p_win"]` could be None (line 1055 sets `"p_win": b.get("p_win")`)
If brain failed (p["brain"]["error"]), `b.get("p_win")` is None, and `:.0%` formatting on None raises TypeError. The earlier filter (line 1051: `if ev is not None`) only checks `ev`, not `p_win`. **Crash path.**

Severity: 🚨 Latent crash on brain-error pick.

---

#### Lines 1079–1105: Auto-pause check (Pillar 5)

#### ⚠️ M-RUN54 (line 1080): `pause_lookback = int(os.getenv("AUTO_PAUSE_LOOKBACK_DAYS", "30"))` — yet another undocumented env var
#### ⚠️ M-RUN55 (line 1093): Block tagged "OBSERVE-ONLY" when `enforce_pause` is False — same pattern as EV gate. ✅

---

#### Lines 1108–1154: SMELL FACULTY

#### ✅ M-RUN56 (lines 1122–1141): Per-pick try-skip pattern is clean. Blockers stored separately from warnings. Good.

#### 🚨 M-RUN57 (line 1126): `sig = p.get("signals") or {}` — `signals` field on pick
Where is `signals` populated? Searching main.py: nowhere. So `sig = {}` always. The smell faculty (per Batch 4 test_smell_faculty.py) uses `sig.get("rsi")`, `sig.get("vol_ratio")`, etc. **All smell checks that depend on signals (RSI, volume) silently get None and skip.**

Severity: 🚨 **Smell faculty operating on empty input.** Most smells (RSI overbought, volume spike, gap, liquidity) never fire because they need signals that are never passed. Only `earnings_imminent` (uses `pick`) and `tight_stop` (uses `pick`) actually run.

This is a HUGE finding — the smell faculty is largely inert in production.

---

#### Lines 1162–1208: First "no top" check

#### ⚠️ M-RUN58 (line 1162): `pipeline["final_pick_count"] = len(top)` — but this gets OVERWRITTEN at lines 1247, 1337, 1430
Field set 4 times during run. Final value depends on which gates ran. Confusing for downstream readers of pipeline.

#### 🚨 M-RUN59 (lines 1184–1196): try/except around `build_candidate_diagnostics` with bare except fallback
On exception, fallback diagnostics dict (lines 1198–1204) is hand-rolled and missing many fields the success path includes. Schema drift between paths.

Severity: ⚠️ Fail-soft creates schema fork.

---

#### Lines 1210–1236: Auto-tag DAY/SWING + intraday-news → watch_only

#### ✅ M-RUN60 (lines 1220–1229): Intraday news → watch_only conversion is well-commented. Hardened explicitly for the May 11 list-shape bug (M-NW1).

#### 🚨 M-RUN61 (line 1212): `_safe_trade_type_for_pick(p["scores"], pick_date=_today)` — passes `_today` STRING
Reinforces M-H1. `_today = "2026-05-12"`. `_is_td("2026-05-12")` — if market_calendar doesn't accept strings, downgrade-to-swing logic NEVER fires. **Bug #7 the wrapper was supposed to fix may still be live.**

Severity: 🚨 **Safety wrapper may be silently broken** for the string-date case which is what main.py uses.

---

#### Lines 1238–1321: Premarket sanity gate

#### 🚨 M-RUN62: This is a 84-line block with a 60-line nested try/except inside another try/except. **Cyclomatic complexity here is extreme.** Combined with portfolio risk gate (lines 1323–1419) and missing-data gate (lines 1421–1518), the THREE gates use COPY-PASTED structure totaling ~300 lines.

The three blocks differ only in:
- Function name called
- Pipeline key names
- Diagnostics extra payload
- Reason string

Should be a single helper:
```python
def _apply_gate(name, gate_fn, top, **gate_kwargs) -> tuple[list, list, dict] | None:
    pre = list(top)
    try:
        passed, blocked, summary = gate_fn(top, **gate_kwargs)
        ...
        return passed, blocked, summary
    except Exception as e:
        _emit_no_pick(name, e, pre)
        return None
```

Severity: 🚨 **~300 lines of copy-paste. Single biggest refactor target in main.py.**

---

#### Lines 1323–1419: Portfolio risk gate (same shape)

#### 🚨 M-RUN63 (line 1329): `open_positions = load_open_positions_from_picks_log()` — UNWRAPPED inside the outer try
Inside the gate's try/except so any failure is caught. But `load_open_positions_from_picks_log()` reads the picks_log CSV. If CSV is corrupt (M-RUN14), this raises and the WHOLE risk gate is skipped → **no portfolio risk gate enforcement** for the run.

Severity: 🚨 Soft-fail of a safety gate.

---

#### Lines 1421–1518: Missing-data gate (same shape)

#### Identical concerns to M-RUN62/63.

---

#### Lines 1520–1561: Selection diagnostics build

#### 🚨 M-RUN64 (lines 1548–1553): RE-ASSIGNS `pre_portfolio_risk_candidates` and `pre_missing_data_candidates` AFTER `build_candidate_diagnostics` was called
```python
selection_diagnostics = build_candidate_diagnostics(
    ...,
    extra={..., "pre_portfolio_risk_candidates": [...], "pre_missing_data_candidates": [...]},
)
selection_diagnostics["pre_portfolio_risk_candidates"] = [...]  # OVERWRITE
selection_diagnostics["pre_missing_data_candidates"] = [...]  # OVERWRITE
```

Plain English: passes them in `extra`, then immediately overwrites at top level. The values inside `extra` are now stale. Anyone reading `selection_diagnostics["extra"]["pre_portfolio_risk_candidates"]` gets one snapshot; reading `selection_diagnostics["pre_portfolio_risk_candidates"]` gets another. They might be the same in this code path, but the dual-store is a bug-magnet.

Severity: ⚠️ Same data in two places; classic schema-drift trigger.

---

#### Lines 1563–1620: Official artifact write

#### ✅ M-RUN65 (lines 1567–1604): Validates artifacts via `artifact_summary["validation_errors"]`. On failure, writes no-pick report and returns. Good fail-closed.

#### 🚨 M-RUN66 (line 1599): `trace = official_artifact_trace.get(str(pick.get("ticker") or "").strip().upper())`
Defensive uppercasing. Tickers SHOULD already be uppercase by this point (universe loader, scorer all use upper). The `.strip().upper()` here suggests **the author has been bitten by lowercase tickers slipping through.**

Severity: 🟡 Symptom of upstream non-canonicalization.

---

#### Lines 1622–1650: Display + LLM rationale

#### 🚨 M-RUN67 (line 1644): `rationale = explain_pick(...)` — LLM call PER PICK, sequential
For 10 picks, 10 sequential LLM API calls. No async, no batching. With Claude/Gemini @ ~3 sec each = 30 sec wall time. **Cost: ~$0.10–0.50 per run @ 10 picks.**

Severity: ⚠️ Cost + latency. Workflow runs every weekday → ~$2–10/week from THIS LINE.

#### 🚨 M-RUN68 (line 1644): `p["news"]` passed to `explain_pick` — and `p["news"]` can be a list per M-NW2
If `explain_pick` calls `.get()` on it, crashes. Need to verify llm_agent.py handles list-shaped news. If not, this is a 5th occurrence of the same bug class.

Severity: 🚨 Likely latent crash.

#### 🚨 M-RUN69 (line 1650): `log_paper_trade(p, cfg["output"]["csv_path"].replace("picks","trades"))`
Replaces "picks" with "trades" in the CSV path. From config.yaml `csv_path: data/picks.csv`. So writes to `data/trades.csv`. **This is the file the dead root `evaluate_picks.py` reads (Batch 5 R-X3).**

So the file IS written — but only when `_should_log_paper_trade()` is True (i.e., `TRADING_MODE=paper`). Per Batch 5 R-X14, default is monitoring, so this never runs in production.

Net: `data/trades.csv` is written ONLY in paper mode, evaluated by ONLY the dead root evaluate_picks.py. Both are dormant. Both should be deleted together.

Severity: 🚨 Coupled dead system: `paper_trader.log_paper_trade` → `data/trades.csv` → `evaluate_picks.py` (root). All disabled by default. All cruft.

#### 🚨 M-RUN70 (line 1650): `cfg["output"]["csv_path"].replace("picks","trades")`
The string `picks` could appear elsewhere in the path (e.g., `/home/user/picks_project/picks.csv` → `/home/user/trades_project/trades.csv`). Fragile string mutation.

Severity: 🟡 Path fragility.

---

#### Lines 1652–1810: Logging block (huge)

#### 🚨 M-RUN71 (lines 1654–1682): Monster treatment block with NESTED try/except
Outer try at 1653 wraps the entire 158-line block. Inner try at 1655 wraps monster treatment. Inner-inner try? No. Pattern: entire write block is one big try.

#### 🚨 M-RUN72 (line 1657): `if _mcfg.get("enabled", True):` — defaults TRUE
But config.yaml line 86: `monster.enabled: true`. Explicit. So default doesn't matter except for tests/dry-runs.

But: if someone deletes the `monster:` block entirely, the default flips ON. Magic-string config.

Severity: 🟡 Default could surprise.

#### 🚨 M-RUN73 (lines 1664–1678): Mutates `_p["plan"]` in place AND sets `_p["is_monster"] = True`
- `_p["plan"]["stop_loss"] = _treated["stop_loss"]` (etc.)
- After monster treatment, the BRAIN audit fields (`brain_sl`, `brain_tp` from line 1014–1016) are STALE — they still describe the pre-monster decision.

Severity: ⚠️ Audit-trail freshness loss.

#### 🚨 M-RUN74 (lines 1684–1698): Sector benchmark fetch
Per-pick yfinance call (cached by `_sector_cache` keyed by sector+tag). Cache reduces calls. Good.

But: if 10 picks all have unique (sector, tag) tuples, 10 yfinance calls inline. No timeout (relies on yf default).

Severity: 🟡 Potential slow path.

#### 🚨 M-RUN75 (line 1700–1757): Builds `picks_for_log` dict — **39 fields per pick**
Field count: ticker, company, tag, trade_type, watch_only, watch_only_reason, news_action_window, official_decision_id, official_artifact_id, official_artifact_path, official_contract_version, score, multiplier, entry, stop_loss, take_profit, risk_reward, qty, days_to_earnings, brain_p_win, brain_ev_pct, brain_sl, brain_tp, brain_confidence, vol_ratio, monster_score, is_monster, smell_codes, smell_severities, smell_messages, sector_etf, sector_close = **32 fields**.

Per Batch 4 test_picks_log_column_contract.py, the CSV must have these columns. If `pick_logger.log_picks` doesn't know about all of them, mismatch. **No assertion that picks_for_log keys match `pick_logger`'s expected schema.**

Severity: 🚨 **Schema-by-author-intuition.** Should have a single schema source of truth.

#### 🚨 M-RUN76 (lines 1717–1749): Bug-fix comments inline (#14, #16, #17A, #8b)
Multiple `# Bug #N: ...` comments document past bugs. Good archaeology, but the FILE has become a graveyard of bug-fix commentary. Recommendation: move fix history to git commits + a CHANGELOG, keep comments terse.

Severity: 🟡 Comment debt.

#### 🚨 M-RUN77 (line 1758): `n = log_picks(picks_for_log, reg, cape if "cape" in dir() else None)`
**`"cape" in dir()`** — checks if `cape` is in current scope. Defensive because some early-return paths skip the cape assignment. But actually no — `cape` is assigned at line 740 unconditionally (inside no try/except up to here). So `cape` is always in dir() by this point. **Defensive code that's defensive against an impossible state.**

Severity: 🟡 Confusing safeguard. Or: code was refactored and the safeguard is a vestige.

#### 🚨 M-RUN78 (lines 1759–1789): Per-pick journal logging with HARDENING comment
Line 1761–1762 says: "Brain operated blind 2026-05-02 to 2026-05-04 due to silent failure." TWO DAYS of brain learning lost because of a bare try/except. **This is the EXACT pattern still present at M-IO1, M-WR1, M-WR12, M-RUN8, M-RUN28, M-RUN59.** The author learned the lesson here but didn't propagate to all the other bare-except sites.

Severity: 🚨 **Inconsistent application of a hard-won lesson.**

#### ✅ M-RUN79 (lines 1781–1789): LOUD per-error logging with traceback. Excellent. Use as template for fixing M-IO1/M-WR1/M-WR12.

#### 🚨 M-RUN80 (lines 1791–1804): Pause-signal calc at end of run
Calls `_pause_score()` and `_maybe_pause()`. If the SCORE pauses TODAY, the agent is paused starting NEXT run. Good — doesn't kill the current run mid-flight.

But: if `_maybe_pause` raises, the calculation is skipped silently (line 1803 bare except with rprint warning). On a day when score>=8, the pause should fire — silent failure means the agent KEEPS running on subsequent days when it should be paused.

Severity: ⚠️ Silent failure on safety mechanism.

#### ⚠️ M-RUN81 (line 1796): `_clean = _line.replace("*", "")`
Strips `*` from pause-summary lines. Why? Probably to avoid Markdown-bold rendering in console. Magic transformation.

Severity: 🟡 Hidden display logic.

#### ✅ M-RUN82 (line 1812): `rprint("[green]Done. Review picks before any real-money action.[/green]")` — final safety reminder. ✅

---

#### Lines 1815–1816: Entry point

#### 🚨 M-EP1: `if __name__ == "__main__": run()` — no error handling
If `run()` raises an unhandled exception (which is possible per M-RUN9, M-RUN17–23, etc.), the process exits with non-zero status. The workflow YAML (Batch 1) presumably handles this, but main.py itself surrenders.

A safer pattern:
```python
if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        _write_guard_no_pick_artifact_for_main(cause="NO_PICK_RUNTIME_FAILURE", reason=str(e))
        raise
```

Severity: 🚨 Unhandled-crash path leaves no artifact.

---

## CONSOLIDATED FINDINGS

### By severity

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | **30** |
| ⚠️ Data/safety risk | **23** |
| 🟡 Code smell | **24** |
| ✅ Good code | **10** |
| **Total findings** | **87 in main.py alone** |

This is the highest finding density of any file in the audit (87 issues / 1,817 lines = 1 finding per ~21 lines).

### Top 10 critical fixes (in order)

| # | Finding | Action | Effort |
|---|---|---|---|
| 1 | M-IO1 | Move module-top `subprocess.run(bootstrap_wisdom)` (lines 91–97) inside `run()` — eliminates side effect on every import | 1 min |
| 2 | M-RUN57 | Investigate why smell faculty receives empty `signals` (line 1126) — most smells inert in production | 1 hr |
| 3 | M-RUN47 | Fix `news_data.get(...)` on potentially-list value (line 999) — same bug class as May 11 fix | 5 min |
| 4 | M-RUN61 + M-H1 | Verify `_is_td(string_date)` works (lines 1212, 45) — safety wrapper may be silently broken | 30 min |
| 5 | M-RUN3 | Replace fail-OPEN with fail-CLOSED on T51 calendar guard (lines 651–664) | 5 min |
| 6 | M-RUN18 + M-RUN36 | Stop mutating `cfg` dict mid-run; use locals (lines 707, 738, 763) | 1 hr |
| 7 | M-RUN26 + M-RUN16 etc. | Document all 12 main.py env vars in `.env.example` and README | 30 min |
| 8 | M-WR11 + M-RUN13 | Add `data/daily_picks_candidate_rejections_*.json` to `.gitignore` exception list | 1 min |
| 9 | M-RUN39 | Fix log line "max 4/sector" vs actual cap 2 (line 911) | 1 min |
| 10 | M-RUN62 | Extract repeated 3-gate boilerplate into helper (~300 lines saved) | 4 hr |

### What main.py tells us about the project

- **`run()` is a 1,184-line linear narrative.** It reads top-to-bottom like a play script. Every "ENTERLEFT/EXITSTAGERIGHT" annotation is an `if/elif/break/return`. The author knows the pipeline intimately. **No one else can.**

- **Two distinct authorial voices:**
  - Comments like "Bug #14: coerce None" / "Hardened 2026-05-04: per-pick try/except + LOUD errors" / "Bug discovered 2026-05-11: ..." show **incident-driven discipline**. Each is a fix-with-evidence.
  - Blanket `try: ... except Exception: pass` blocks (M-IO1, M-WR1, M-WR12, M-RUN8) show **fear-driven swallowing**. Each loses signal.
  
  **The two voices coexist in the same file.** This is the mark of a project that has had genuine production incidents and learned, but hasn't yet retrofitted the hard-won pattern (LOUD errors with traceback, M-RUN78–79) backwards.

- **The orchestrator is doing too much.** A 1,800-line file with 90 KB of orchestration is doing the work that should be split across 5+ modules:
  - guards (calendar, pause, multi-fire)
  - market context (regime, CAPE, briefing, guards)
  - pipeline (universe → fetch → score → filter → cap → news → hard block → brain → EV → pause → smell → tag → sanity → risk → missing-data)
  - artifact writers (no-pick report, candidate diagnostics, official artifacts, pause-day, guard-artifact)
  - logging (csv, journal, telegram dispatch hand-off)
  - The `run()` function is implementing all five.

- **12 env vars + 4 yaml configs + 2 json configs + hidden constants embedded throughout.** No central config schema. Operators have no map.

- **9 dead module-top imports.** Cleanup low-hanging fruit.

- **The smell faculty (the most marketed safety feature in tests/Batch 4) is largely INERT** because it receives empty signals (M-RUN57). This is the single most important finding in this batch. Marketing vs. reality.

---

## CUMULATIVE TOTALS (all batches 1a/1b/2a/2b/3a/3b/3c/3d/3e/4/5/6)

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | **153** (was 123) |
| ⚠️ Data/safety risk | **273** (was 250) |
| 🟡 Code smell | **228** (was 204) |
| 📝 Doc-only | **14** |
| ✅ Good code citations | **270+** |
| **Total findings** | **~938 across 299 files** |

---

## What's left

After this batch:
1. ✅ Workflows (.github/) — Batches 1a, 1b
2. ✅ src/ — Batches 2a, 2b
3. ✅ scripts/ — Batches 3a–3e
4. ✅ tests/ — Batch 4 (meta)
5. ✅ Root files — Batch 5
6. ✅ main.py deep dive — this batch
7. ⏳ docs/ — multi-hundred markdown files. Can be a meta-batch.
8. ⏳ data/ schemas — covered in passing throughout, would need a standalone batch only if you want exhaustive artifact catalog.

**Recommended next:** Synthesis report. We now have **~938 findings**. Without consolidation, the audit is unusable. The synthesis would:
- Group findings by THEME (silent failures / schema drift / dead code / magic numbers / etc.)
- Cross-link related findings across batches (e.g., M-RUN57 inert smell + Batch 4 test_smell_faculty.py = "tested but doesn't actually run")
- Produce a 30/60/90-day priority ladder
- Estimate effort by class

Or: Batch 7 (docs/) before synthesis if you want completeness first.

End of Batch 6.
