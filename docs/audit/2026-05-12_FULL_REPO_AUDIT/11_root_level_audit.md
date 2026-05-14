# Audit Batch 5 — Root-level files (12 files)

**Date:** 2026-05-12
**Files (12):**
- Code: main.py (90 KB / ~2,400 lines), app.py (105 lines), backtest.py (43 lines), evaluate_picks.py (84 lines), conftest.py (4 lines)
- Config: config.yaml (91 lines), config/auto_pause.json, config/weights.json
- Build/ops: Makefile (109 lines), requirements.txt (23 lines), .env.example (8 lines), .gitignore (254 lines)
- Doc: README.md (157 lines)

**Note on main.py:** at 90 KB / ~2,400 lines, file-content fetch was truncated. This audit infers main.py findings from cross-references in Batches 1-4 (test_monitoring_mode_no_paper_default, test_smell_wired_in_main, test_main_t51_guard_no_pick_artifact, test_premarket_decision_contract, repeated mentions throughout). For full main.py file-by-file audit, request a dedicated batch — it likely deserves 4-6 sub-batches.

---

## CROSS-CUTTING FINDINGS

### 🚨 R-X1: main.py is a 90 KB single file
At ~2,400 lines, main.py is ~3.7x larger than the next-largest scripts file (intraday_monitor at 24 KB). For comparison, the entire `app.py` (Streamlit dashboard) is 105 lines.

Plain English: main.py is the daily-picks orchestrator. It coordinates universe → fetch → score → smell → judgment → memory → voice → wisdom. From references in tests:
- `_should_log_paper_trade()` (tested in test_monitoring_mode_no_paper_default.py)
- `_safe_trade_type_for_pick()` (line 36)
- `_yf_ticker_for_sector_benchmark()` (line 50)
- `_latest_close_for_sector_benchmark()` (line 56)
- T51 holiday/no-pick guard (test_main_t51_guard_no_pick_artifact.py)
- Smell faculty wire-up (test_smell_wired_in_main.py)

A 2,400-line orchestrator is a **God-object anti-pattern**. Most of the modules in src/ exist precisely to keep main.py small; instead, main.py grew anyway.

Severity: 🚨 Maintainability + review burden + merge-conflict magnet.

### 🚨 R-X2: Two `evaluate_picks.py` files (root + scripts/)
- `/evaluate_picks.py` (84 lines): pandas-based evaluator with `rich` table output. Reads `data/trades.csv`. Standalone.
- `/scripts/evaluate_picks.py` (74 lines, audited in Batch 3e): wraps src.pick_evaluator + dashboard + position_monitor + breakdowns + risk + auto_cooldown.

Plain English: TWO files with the same name doing **completely different things**. Root version reads `data/trades.csv` (does it exist?); scripts version reads `data/picks_log.csv`. Easy to run the wrong one and get nonsense output.

Severity: 🚨 Naming collision = operational confusion. Delete root version OR rename to `evaluate_legacy.py`.

### 🚨 R-X3: Root `evaluate_picks.py` reads `data/trades.csv` — file likely doesn't exist
Line 10: `def evaluate(csv_path: str = "data/trades.csv", ...)`. The actual canonical artifact is `data/picks_log.csv`. From .gitignore line 245: `!data/picks_log.csv` is the only CSV explicitly tracked. **`data/trades.csv` is not mentioned anywhere else in the audit.**

Plain English: this script is dead. Reads a file that's never written. Likely a vestige from an earlier iteration.

Severity: 🚨 Dead code in repo root, indistinguishable from active code.

### 🚨 R-X4: `backtest.py` references `src.backtester.backtest_simple` — function existence unknown
Line 7: `from src.backtester import backtest_simple`. Per Batch 2 inventory, src/ has `backtester.py` but the per-function audit didn't confirm `backtest_simple` exists. This script may already be broken.

Combined with `Makefile` having NO `backtest` target (lines 19-26 list test targets only), this script is invisibly orphaned.

Severity: 🚨 Likely dead code OR latent breakage.

### ⚠️ R-X5: `app.py` (Streamlit dashboard) imports `src.tracker` — Batch 4 noted `tracker` is "reachable but possibly stale"
Line 16: `from src.tracker import performance_summary`. Test `test_audit_dead_code.py:46-48` explicitly says "tracker is reachable via app.py + scripts." So app.py is the lifeline keeping tracker.py from being dead-code flagged.

But: is anyone running `streamlit run app.py`? The README mentions it (line 100) but it's not in any workflow, not in cron, not in main.py. If the answer is "no, nobody runs the Streamlit dashboard anymore," then **tracker.py is effectively dead** and the only thing keeping it pseudo-alive is a never-used dashboard.

Severity: ⚠️ Hidden coupling: a dashboard nobody runs is propping up a module nobody calls.

### ⚠️ R-X6: `app.py` is module-top execution (X-IO5 family)
Lines 19-29 + 31-41 (sidebar) + 43+ (run_btn block) all execute on import. Streamlit-typical pattern, but means `import app` from a test would crash. Not testable in normal pytest flow.

Severity: ⚠️ Acceptable for Streamlit but explains zero test coverage of this file.

### ⚠️ R-X7: `app.py` and `main.py` use DIFFERENT scoring code paths
- app.py line 60: `composite_score(sig, fund, sent, cfg["weights"], ticker=tk, ...)` — 4 positional args.
- Per test_basic.py:36 + test_faculty_integration.py:76: same `composite_score(sig, 0.7, 0.6, weights, ...)` signature.
- main.py likely uses `parallel_scorer` (per test_news_engine.py:274 grep test).

Plain English: the dashboard uses raw `composite_score` while production uses `parallel_scorer`. If they drift (different weight handling, different bucketing), the dashboard misleads.

Severity: ⚠️ Two scoring paths = two truths.

### ⚠️ R-X8: `config.yaml` has comments encoding KNOWN BUGS / EXCLUSIONS as data
Lines 14-22:
```yaml
excluded_tickers:
- MRVL          # original exclusion (owner preference)
- UNH    # -1.35R avg per pick — worst loser in universe
- TEAM   # -1.00R avg per pick
- SMCI   # -0.94R avg per pick — also high vol penalty
- DIS    #  -0.64R avg per pick
- SCHW   # -0.64R avg per pick
```

This duplicates `bootstrap_wisdom.py`'s SEED_KILLS list (Batch 3e BUG-BW3). Now the same 5 tickers are encoded in **two separate places**:
- `config.yaml` `universe.excluded_tickers`
- `scripts/bootstrap_wisdom.py` `SEED_KILLS`

Plain English: if you delist UNH from one but not the other, mysterious behavior ensues.

Severity: ⚠️ Configuration drift waiting to happen.

### ⚠️ R-X9: `config.yaml` line 38-42: SEMI bias DISABLED, but the keys remain at neutral
```yaml
sector:
  # ⚠ DISABLED 2026-05-02: backtester proved SEMI bias = -24.8 Sharpe leak
  semi_boost: 1.0     # was 1.1
  ai_boost: 0.0       # was 0.2
```

Code that reads these keys still runs. Since `1.0` and `0.0` are no-ops, the code is effectively dead. **But the keys signal intent.** A future engineer might think "let's re-enable SEMI" and quietly raise these without remembering the -24.8 Sharpe disaster.

Severity: ⚠️ Dead-config-by-default. Better: delete the `sector:` block entirely OR rename to `_disabled_sector_DO_NOT_RE_ENABLE`.

### ⚠️ R-X10: `config.yaml` has FOUR scoring threshold systems, all hardcoded
1. `output.min_score: 0.55` (line 52) — global min
2. `day_trading.min_score: 0.65` (line 66)
3. `swing_trading.min_score: 0.55` (line 77)
4. `monster.threshold: 0.60` (line 86)

Plus `weights:` (lines 29-36) listing 7 weights that should sum to 1.0:
0.18 + 0.20 + 0.08 + 0.05 + 0.14 + 0.12 + 0.23 = **1.00 ✅** (verified)

But: nowhere in config does it say "weights MUST sum to 1.0". A future edit could break invariant silently.

Severity: ⚠️ No invariant enforcement on critical config.

### ⚠️ R-X11: `config/weights.json` is a SECOND weights file with different meaning
- `config.yaml` `weights:` — factor weights for composite score (sum to 1.0).
- `config/weights.json` `factors:` — per-bucket multipliers (1.0 = neutral, mutated by `weight_applier.py` per proposals, capped 5%/week).

Plain English: two files named/keyed similarly, doing very different things. weight_applier mutates one (`config/weights.json`) but config.yaml stays static. Brain-controlled knobs vs. founder-controlled knobs.

Severity: ⚠️ Documented in `_doc` field (line 4) — good — but easy to confuse. Rename `config/weights.json` to `config/factor_multipliers.json` for clarity.

### ⚠️ R-X12: `config/auto_pause.json` line 2: `"enforced": false`
The auto-pause feature (Pillar 5 — Self-Awareness, Batch 2/3 multiple references) has its enforcement gate **OFF**. Comment line 5 says "Set enforced=true on Wed May 6 2026 after 3-day calibration."

Today's date in audit context: 2026-05-12. **It's been 6 days past the planned enforcement date and the gate is still off.**

Severity: ⚠️ Dormant safety mechanism. Either the founder forgot OR the calibration showed it shouldn't enforce — and there's no record of which.

### ⚠️ R-X13: `requirements.txt` has NO version-pinning for some packages
- `anthropic>=0.40.0` (line 19) — open upper bound
- `alpaca-py>=0.20.0` (line 22) — open upper bound

All other packages are `==X.Y.Z` pinned. The two LLM/broker libs are the most likely to introduce breaking changes. Inconsistent policy.

Severity: ⚠️ Reproducibility risk for the most important integrations.

### ⚠️ R-X14: `.env.example` line 7: `TRADING_MODE=paper`
The README says "monitoring-only" is the default operating posture (line 11). `test_monitoring_mode_no_paper_default.py:4-7` asserts that when `TRADING_MODE` is UNSET, paper logging is OFF.

But `.env.example` defaults `TRADING_MODE=paper` — so a fresh dev setup would ENABLE paper-trade logging. **Contradicts the documented safety stance.**

Severity: ⚠️ Setup default contradicts the security model. Change to `TRADING_MODE=monitoring`.

### ⚠️ R-X15: `requirements.txt` missing a key dependency
- Tests use `pytest.fixture`, `monkeypatch`, `tmp_path` extensively — fine, all in pytest.
- Tests use `pandas` — pinned ✅
- `gemini_helper.py` (Batch 3e) imports `google.generativeai` — but `requirements.txt` line 17 has `google-genai==0.3.0` (different package!). The package `google-genai` is the NEW SDK; `google-generativeai` is the OLD. Need to verify which one `gemini_helper.py` actually uses.

Severity: ⚠️ Possible package-name mismatch = pip install succeeds, runtime ImportError.

### ⚠️ R-X16: `.gitignore` line 225: `data/` ignored, then 30+ exception rules
Lines 225 + 240-253: ignore `data/` entirely, then `!data/learning/`, `!data/exec_report_*.json`, `!data/premarket_check.json`, `!data/picks_log.csv`, `!data/books/`.

Plain English: 30+ explicit exceptions are needed because `data/` is broadly excluded. New artifact files require a `.gitignore` edit OR they vanish. This is the WHY behind X-DA1 (Batch 1) — a new evidence file silently doesn't get committed.

Severity: ⚠️ Operational footgun. **Recommend invert: track `data/` by default, exclude only known-large/transient subdirs.**

### 🟡 R-X17: `Makefile` has 32 targets — comprehensive but inconsistent comment style
Lines 11-65 use `## comment` syntax for help auto-gen (line 15: `grep -E '^[a-zA-Z_-]+:.*?##'`). Lines 78-108 (books, calibration, weights) DON'T use `##` syntax → invisible in `make help`.

Plain English: the most recent additions (book_ingest, calibration, weight_proposer) are missing from the help menu.

Severity: 🟡 Discoverability gap.

### 🟡 R-X18: `conftest.py` is 3 lines — adequate but `tests/conftest.py` is missing
Root `conftest.py` adds project root to sys.path. Good for `from src.X import Y` and `from scripts.Y import Z` patterns. But Batch 4 found ~20 test files repeating `sys.path.insert(0, str(Path(__file__).parent.parent))`. Since root conftest.py exists, those inserts are redundant.

Severity: 🟡 DRY waste in tests, not a bug.

### 🟡 R-X19: `README.md` heavily emphasizes safety — good — but doesn't mention current Phase
README line 7: "Current Status" / "monitoring-only / no paper trading / no live trading". But which roadmap phase? Lane 1 / Lane 2 / Phase 2A / Phase 2B? Newcomers can't orient without reading 5 other docs.

Severity: 🟡 Onboarding gap.

### 🟡 R-X20: `app.py` imports `from src.llm_agent import explain_pick` then calls it on every pick
Line 100: `st.write(explain_pick(p["ticker"], ...))`. If user clicks "Run Agent" and there are 10 picks, this fires 10 LLM calls SYNCHRONOUSLY in the UI thread. No spinner, no async, no caching beyond Streamlit's `@st.cache_data(ttl=600)` on config.

Plain English: dashboard spending real money on LLM calls per refresh, with no rate limiting.

Severity: 🟡 Dashboard cost-blowup risk if anyone actually opens it.

### ✅ R-X21: `config.yaml` has EXCELLENT documentation comments
Comments explain:
- WHY MRVL excluded (owner preference)
- WHY 5 tickers added (backtester evidence with citation)
- WHY SEMI bias disabled (with link to session doc)
- WHY day_trading params chose those values

This is rare and admirable. Most YAML configs in production projects are mute.

### ✅ R-X22: `Makefile` separates dry-run from write operations
- `wisdom-dryrun` vs `wisdom-promote`
- `wisdom-gc-dryrun` vs `wisdom-gc`
- `calibrate-propose` (dry-run default!) vs `calibrate-propose-save`

Defensive shape. Operator is one keystroke away from a write but can't do it accidentally.

### ✅ R-X23: `.env.example` lists ALL needed secrets
6 keys. Concise. Matches README "Required Secrets" table (lines 142-148). Good.

### ✅ R-X24: `requirements.txt` is readable + grouped
Lines 1-19 are core. Lines 21-22 grouped under `# Phase 2A: News Engine + Alpaca`. Better than the 50-package alphabetical soup most projects have.

### ✅ R-X25: `evaluate_picks.py` (root) uses rich tables for human output
If the script is alive (R-X3 disputes this), the output is well-formatted. Color-coded P/L. Per-row outcome resolution by simulating SL/TP first-hit.

But the methodology has a **subtle bug worth flagging:**

#### 🚨 BUG-EP-LOOP-1: Same-bar SL+TP hit ordering is not handled (root evaluate_picks.py)
Lines 44-48:
```python
for _, bar in hist.iterrows():
    if bar["low"] <= sl:
        outcome = "SL HIT"; break
    if bar["high"] >= tp:
        outcome = "TP HIT"; break
```

If a bar's high >= tp AND its low <= sl on the SAME bar, this code ALWAYS marks SL HIT (because the SL check is first). This is the classic "intra-bar order ambiguity" problem.

The proper version is in `src/pick_evaluator.py` (Batch 2/Batch 3e references) which uses Open-distance-to-SL vs Open-distance-to-TP tie-breaker (test_pick_evaluator.py:180-218 verifies this).

Plain English: root evaluate_picks.py has the bug that scripts/ + src/ already fixed.

Severity: 🚨 Mathematically wrong + duplicated logic the rest of the repo has solved. Reinforces R-X2 — DELETE root evaluate_picks.py.

---

## SUMMARY

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 5 |
| ⚠️ Data/safety risk | 12 |
| 🟡 Code smell | 4 |
| 📝 Doc-only | 0 |
| ✅ Good code | 5 |
| Total | 26 findings |

### Top 7 things to fix in this batch

| # | Action | Why | Effort |
|---|---|---|---|
| 1 | DELETE root `/evaluate_picks.py` | Reads non-existent `data/trades.csv`; has buggy SL/TP order logic; collides with scripts/evaluate_picks.py | 1 min |
| 2 | DELETE or fix root `/backtest.py` | Imports `src.backtester.backtest_simple` whose existence is unverified; not in Makefile; possibly dead | 5 min (verify first) |
| 3 | Change `.env.example` `TRADING_MODE=paper` → `TRADING_MODE=monitoring` | Setup default contradicts "monitoring-only" safety posture | 1 min |
| 4 | Reconcile `config/auto_pause.json` `enforced=false` | 6 days past planned enforcement date — was it intentional? Add a comment OR turn it on | 5 min |
| 5 | Verify `gemini_helper.py` package import vs `requirements.txt:17` (`google-genai` vs `google-generativeai`) | Package-name mismatch could cause runtime ImportError on fresh install | 5 min |
| 6 | Decompose `main.py` (~2,400 lines) into orchestrator + helpers | God-object hindering review/test | Multi-day refactor |
| 7 | Pin `anthropic` and `alpaca-py` to specific versions | Open upper bounds = surprise breaking changes | 2 min |

### What this batch tells us about the project

- **The root directory is the messiest part of the repo.** Two files named `evaluate_picks.py`, one of them dead. A `backtest.py` likely-dead. A 90KB `main.py`. A Streamlit `app.py` no one runs but that keeps another module alive by being its only importer.
- **Config is well-commented but architecturally split across 3 files** (config.yaml, config/auto_pause.json, config/weights.json) with overlapping concerns. SEMI exclusions duplicated in config.yaml AND bootstrap_wisdom.py.
- **The safety story has gaps at the boundary:** README says monitoring-only; `.env.example` defaults to paper; `auto_pause.json` says "enforce on May 6" but it's May 12 and still off.
- **Makefile is the best citizen:** 32 targets, dry-run/write separation, auto-help. Use this style as template.
- **README is genuinely good:** clear safety boundaries, table of secrets, doc index. One of the best public-facing READMEs in the repo.

---

## CUMULATIVE FINAL TOTALS (all batches 1a/1b/2a/2b/3a/3b/3c/3d/3e/4/5)

| Severity | Count |
|---|---:|
| 🚨 Show-stopper | **123** |
| ⚠️ Data/safety risk | **250** |
| 🟡 Code smell | **204** |
| 📝 Doc-only | **14** |
| ✅ Good code citations | **260+** |
| **Total findings** | **~851 across 298 files** |

## What's left

After this batch:
1. ✅ Workflows (.github/) — Batches 1a, 1b
2. ✅ src/ — Batches 2a, 2b
3. ✅ scripts/ — Batches 3a, 3b, 3c, 3d, 3e
4. ✅ tests/ — Batch 4 (meta)
5. ✅ Root files — this batch
6. ⏳ docs/ — multi-hundred markdown files. Recommend a meta-batch.
7. ⏳ main.py deep-dive (90KB) — would be 4-6 sub-batches if you want it.
8. ⏳ data/ schemas — already covered in passing throughout. Optional standalone batch.

Recommended next:
- **Option A:** docs/ meta-audit (similar approach to tests/) — completes the high-level circuit.
- **Option B:** main.py deep-dive (the only remaining unaudited high-risk surface). Would be the single most valuable batch given main.py is ~2,400 lines of orchestrator logic and likely has the highest finding density.
- **Option C:** Synthesis report — consolidate all 851 findings into a prioritized "fix this in order" list with effort estimates.

End of Batch 5.
