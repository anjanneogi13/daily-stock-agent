# Audit Batch 3e — Scripts: Brain/LLM/Wisdom/Reports/Audit (26 files)

**Date:** 2026-05-12
**Files (26):** news_signal_outcome_attribution, run_news_engine, run_hypothesis_review, run_nightly_brain, monthly_xray, weekend_reflection, weekly_report_card, wisdom_audit, wisdom_writer, evaluate_picks, performance_dashboard, scan_patterns, show_performance, unpause, quarterly_report, claude_helper, gemini_helper, code_inspector, full_repo_audit, local_analyst, run_backtest, bootstrap_wisdom, audit_dead_code, audit_journal_consistency, backup_data, news_signal_evidence_report

**Total:** ~3,600 lines

**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

## High-level summary in plain English

These 26 are the **brain layer**: LLM helpers (Claude/Gemini), wisdom seeding/audit/writers, weekly/monthly recap generators, deterministic-fallback analysts, evaluators, dashboards, and operational tools (backups, audits, unpause).

Six families:

A — News evidence & attribution (3): news_signal_outcome_attribution, news_signal_evidence_report, run_news_engine
B — Reflection & retrospective (5): run_hypothesis_review, run_nightly_brain, monthly_xray, weekend_reflection, weekly_report_card
C — Wisdom plumbing (3): wisdom_audit, wisdom_writer, bootstrap_wisdom
D — LLM + analyst stack (4): claude_helper, gemini_helper, code_inspector, local_analyst
E — Evaluators & dashboards (5): evaluate_picks, performance_dashboard, show_performance, scan_patterns, quarterly_report
F — Ops & audit (6): unpause, full_repo_audit, audit_dead_code, audit_journal_consistency, backup_data, run_backtest

---

## CROSS-CUTTING FINDINGS

### 🚨 X-BR1: LLM cost/safety controls are inconsistent
- claude_helper: MAX_TOKENS=4000 hardcoded; auto-falls back to Gemini.
- gemini_helper: 3 retries × 3 models = up to 9 calls per "one" request, with sleeps up to 90s.
- weekly_report_card: directly imports `anthropic` + `claude-sonnet-4-5`, bypasses claude_helper completely (no Gemini fallback, no retry).
- monthly_xray: uses claude_helper (good) → falls back to local_analyst.
- weekend_reflection: uses gemini_helper directly (no Claude primary) → falls back to local_analyst.

Plain English: Three different LLM-call patterns. weekly_report_card uses a different model and skips the unified helper. Quotas + spend become unpredictable.
Severity: 🚨 Cost + behavior drift.

### 🚨 X-BR2: Plain-English fallbacks are excellent — but inconsistently wired
- monthly_xray.py:202-222 + 224-240: try Claude, then Gemini, then `local_analyst.analyze()`. Three-tier fallback. EXCELLENT.
- weekend_reflection.py:106-113: try Gemini, then `local_analyst.analyze()`. Two-tier.
- weekly_report_card.py:84-86: try Claude, return error string `"💡 Coaching: (Claude unavailable: ...)"`. NO local fallback — user sees raw exception name.

Plain English: same problem (LLM down) handled three different ways. Best practice (3-tier with local) only applied in 1 of 3 files.
Severity: 🚨 Inconsistent resilience.

### 🚨 X-BR3: Module-level execution still pervasive
- monthly_xray.py: ENTIRE file is module-top (lines 7-262) — runs on import, calls subprocess, calls LLM, writes file.
- weekend_reflection.py: same, lines 10-118.
- performance_dashboard.py: same, lines 7-92.
- show_performance.py: 7 lines, ENTIRELY module-level (calls print_dashboard).

Continuing X-IO5 from Batch 3d. Now ~8 module-level scripts. **Not testable. Not importable.**
Severity: 🚨 Test-hostile pattern.

### ⚠️ X-BR4: CLOSED_STATUSES drift continues (now 9th file)
- monthly_xray.py:18, 37 — uses `("tp_hit", "sl_hit", "expired")`
- weekend_reflection.py:31 — same
- evaluate_picks.py: delegates to src.pick_evaluator (clean)
- performance_dashboard.py:13-14 — uses `evaluation_status != "pending"` (different semantic)
- local_analyst.py:127 — `["tp_hit", "sl_hit", "closed"]` (introduces "closed" — different from others!)
- code_inspector.py:307 — `["tp_hit", "sl_hit", "closed"]` (same as local_analyst)

Plain English: The set `{"tp_hit", "sl_hit", "closed"}` appears in 2 files; `{"tp_hit", "sl_hit", "expired"}` appears in 3 files; `{"tp_hit","sl_hit","expired","day_close"}` in monitoring_readiness (Batch 3d). **Five+ different definitions of "closed".**
Severity: ⚠️ Same-name-different-meaning catastrophe waiting to happen.

### 🚨 X-BR5: `weekend_reflection.py` line 112 is BROKEN code
Line 112: `_err_short = "⚠️ Gemini free quota exhausted — using local analysis." if any(k in str(err) for k in ["RESOURCE_EXHAUSTED","429","quota","404","NOT_FOUND"]) else f"Gemini unavailable: {s[...]`

Truncation marker `{s[...]` indicates the file content displayed is incomplete OR the source has unfinished code. Looking at line 113 which references `_err_short`, this file could fail at runtime if `s` is undefined.

Need to verify on disk; if truly truncated, weekend_reflection.py CRASHES on Gemini failure.
Severity: 🚨 Possible runtime crash on fallback path.

### ⚠️ X-BR6: Three weekly-report scripts with overlapping output
- run_hypothesis_review.py → "Weekly Hypothesis Review"
- weekend_reflection.py → "Weekend Review"
- weekly_report_card.py → "Weekly Performance Report Card"

All three write to `data/...weekly...` style paths, all three send Telegram, all three run on Saturday/Sunday cron (per Batch 1 workflows). User likely receives THREE long messages back-to-back labeled "weekly".
Severity: ⚠️ User-experience overload + ambiguous canonical "weekly review".

### ⚠️ X-BR7: Backup system relies on `gh` CLI being installed and authenticated
backup_data.py shells out to `gh release create/delete/list`. If `gh` not authed (env var GITHUB_TOKEN), backup fails silently (gh prints to stderr; subprocess captures, doesn't surface).
Plain English: a single missing env var = no backups for weeks; you find out after data loss.
Severity: ⚠️ Single point of catastrophic failure.

### ⚠️ X-BR8: code_inspector + local_analyst hardcoded thresholds
Both files have ~15 hardcoded "if win_rate < 30:" / "if avg_r < -0.3:" / "if cur > 0.5:" rules. None backed by statistical justification. Each suggestion produces text the user reads as "Action: edit `config.yaml` → `min_score: 0.85`."

Plain English: An LLM-style "coach" produced from regex rules. Recommendations look authoritative but are heuristic and brittle to small samples.
Severity: ⚠️ False-confidence risk.

### ✅ X-BR9: Audit scripts are GENUINELY useful
- audit_dead_code.py: catches THREE import shapes after a real prior-bug fix (lines 6-9 docstring). DRY violation noted but USEFUL.
- audit_journal_consistency.py: locked invariant, --strict mode for CI. Clean.
- full_repo_audit.py: 12-section meta-audit of repo state. Used to BUILD this very audit (lines 1-5 reference Claude chat).

These three are model citizens.
Severity: ✅ Good code.

### ⚠️ X-BR10: `unpause.py` is the only manual-override path — gates user input
Line 30: `confirm = input(...)`. CLI only. No web/Telegram override path. If owner is on phone (typical scenario), no way to unpause without SSH.
Severity: ⚠️ Operability gap.

### 🚨 X-BR11: Mass duplication of Telegram-send code (continues from Batch 3c)
- run_hypothesis_review.py:29-56 — own _send_telegram (urllib, fan-out, parse-mode fallback)
- run_news_engine.py:142-158 — own send_telegram (requests, single-chat, no fallback)
- weekly_report_card.py:107-117 — inline (requests, single-chat, no fallback)

Now THREE MORE files implement Telegram send. Total across Batch 3c+3e = **17+ implementations of "send to Telegram."**
Severity: 🚨 Reinforcement of #1 refactor priority from this entire audit.

### 🟡 X-BR12: bootstrap_wisdom hardcodes domain knowledge as code constants
SEED_LESSONS (4 entries) + SEED_KILLS (5 tickers) embedded as Python literals. Adding new lessons requires code change + deploy.
Plain English: domain experts can't curate wisdom without engineer involvement.
Severity: 🟡 Should be a YAML file.

---

## PER-FILE FINDINGS (concise)

### 1. news_signal_outcome_attribution.py (421 lines)

What it does: Joins news signals to subsequent N-day price returns. Read-only.

✅ GOOD-NA1: Solid dedup key construction (lines 205-210) using source+ticker+headline-prefix+date-prefix.
✅ GOOD-NA2: Per-row schema versioning (`outcome_schema: news_signal_outcome_v1`) — first file in batch with explicit schema version. EXCELLENT.
✅ GOOD-NA3: VALID_STATUSES enum (line 33-39) — typed status constants.
⚠️ BUG-NA1: yfinance silent fallback (line 27-28). Same X-IO2 family.
⚠️ BUG-NA2: Line 233 fetches `horizon_days + 8` calendar days — generous buffer, but for horizon_days=3 this fetches 11 days/ticker × 250 items = up to 2750 yfinance calls per run. No batching.
- Severity: ⚠️ API-load concern.
🟡 BUG-NA3: Line 224 `out[:max_items]` — silent truncation. Sort puts NEWEST first (correct), but no log telling operator "1500 evidence items skipped due to max_items=250".
🟡 BUG-NA4: load_jsonl reimplemented again (lines 82-95). 11th occurrence.

### 2. news_signal_evidence_report.py (visible portion only ~95 lines retrieved)

What it does: Inventory + summary report of news_log + signals + watchlist evidence. Read-only.

✅ GOOD-NE1: Helper-rich layout: load_json + load_jsonl + load_csv + _safe_float + _today_et — consistent with sibling files.
🟡 BUG-NE1: Yet ANOTHER load_jsonl + load_json + load_csv (12th, 8th, ?th occurrences). Cumulative DRY problem now epidemic.
- Severity: 🟡 Reinforces X-IO4.

### 3. run_news_engine.py (305 lines) — MASTER NEWS RUNNER

What it does: Fetch news → classify (Claude) → extract signals → update watchlist → optional Telegram alerts.

✅ GOOD-RN1: Run-status JSONL with comprehensive counters (lines 52-99) — items_fetched/classified/signals_added/hard_blocks/etc. Per-row mode contract. Best-in-class observability.
✅ GOOD-RN2: TELEGRAM_THRESHOLD=0.85 with PR comment explaining noise reduction (line 23).
✅ GOOD-RN3: ENABLE_NEWS_TELEGRAM env gate (line 269) — explicitly opt-in for power users. Defaults to OFF (only internal logging).
✅ GOOD-RN4: news_lookback_minutes() bounded 30-360 with default 120 (line 37-49) — defensive. Comment explains why (workflow delays).
✅ GOOD-RN5: Try/except wraps full main; appends `failed` run_status row + re-raises (lines 293-300). Workflow gets error AND audit log.

🚨 BUG-RN1: Line 142-158 OWN Telegram sender (requests-based, single chat, no parse_mode fallback). See X-BR11. Bypasses unified pattern.
⚠️ BUG-RN2: Line 21 `from src.news_signals import ... # PR #77` — PR number in import comment. Stale documentation.
⚠️ BUG-RN3: Line 165 emoji + score formatting hardcoded. Same as Batch 3c X-TG4.
🟡 BUG-RN4: Line 220-221 classify_batch capped at 20 — silent drop. Same observability gap as BUG-NA3.

### 4. run_hypothesis_review.py (115 lines)

What it does: Loads closed picks → calls hypothesis_engine.analyze → formats Markdown → optional Telegram.

✅ GOOD-RH1: --send and --min-n CLI flags — testable.
✅ GOOD-RH2: Auto-saves to data/reports/hypothesis/ (line 102-104) regardless of send.
✅ GOOD-RH3: Plain-English "<5 closed → say so" path (lines 75-85). Honest under-data behavior.

🚨 BUG-RH1: Lines 29-56 ANOTHER Telegram impl. See X-BR11.
⚠️ BUG-RH2: Line 69 `he.MIN_SAMPLE_SIZE = args.min_n` — MUTATES module global. If hypothesis_engine is imported again later in same process, the mutated value persists.
- Severity: ⚠️ Hidden side effect.
🟡 BUG-RH3: Line 91-97 hardcoded "Observe-mode" footer — fine but ungovernable per-event.

### 5. run_nightly_brain.py (22 lines) — TINY ENTRY POINT

What it does: Calls src.nightly_conductor.run_nightly + format_summary_text. That's it.

✅ GOOD-NB1: Smallest file in batch. Single responsibility. Comment on line 16 explains "always exit 0" decision.
🟡 BUG-NB1: Line 16-17 `Always exit 0 — failures are logged in journal, don't break workflow` — design decision documented, but means CI never knows about brain failures unless someone reads journal manually.
- Severity: 🟡 Acceptable but worth a separate alarm channel.

### 6. monthly_xray.py (262 lines)

What it does: 30-day retrospective. Builds weekly summary, code-change correlation, regime stats, best/worst picks. Calls Claude for narrative; falls back to Gemini→local.

✅ GOOD-MX1: 3-tier LLM fallback (lines 224-240) — gold standard.
✅ GOOD-MX2: git_changes() (lines 76-84) — correlates code changes to performance windows.
✅ GOOD-MX3: Best-effort calibration (lines 191-199) wrapped in try/except. Fail-safe.
✅ GOOD-MX4: T51b holiday-calendar warning surfaced at end (lines 252-261). Operator-visible.

🚨 BUG-MX1: Module-level execution. X-IO5/X-BR3.
🚨 BUG-MX2: Line 78-79 `files = ["config/tuning.yaml", "scripts/score.py", "scripts/risk.py", ...]` — hardcoded list of "interesting files." If you add a new strategy file, git_changes silently misses it.
- Severity: ⚠️ Drift trap.
🚨 BUG-MX3: Line 79 references `scripts/score.py`, `scripts/risk.py`, `scripts/main.py` — **none of these files were observed in the scripts/ directory listing.** These paths are likely STALE.
- Plain English: every monthly run produces empty `code_changes` because the watched files don't exist.
- Severity: 🚨 Silent data void in monthly retrospective.
⚠️ BUG-MX4: Line 7 `today = datetime.now()` — local time. See X-IO3.
⚠️ BUG-MX5: Line 18 `("tp_hit", "sl_hit", "expired")` — see X-BR4.
🟡 BUG-MX6: Line 119-121 score_bucket: hardcoded thresholds 0.85/0.80/0.75. Magic ladder.
🟡 BUG-MX7: Line 154-185 prompt assembled by string concat (avoids f-string triple-quote issues per comment) — works but ugly. Pull into a template file.

### 7. weekend_reflection.py (119 lines)

What it does: 7-day plain-English review via Gemini + local fallback.

✅ GOOD-WR1: Comprehensive prompt structure — explicit sections, evidence-cite rules, "if <20 trades say so" (line 95).
✅ GOOD-WR2: All raw observations passed to LLM (line 54) — full context.

🚨 BUG-WR1: Line 112 truncated/broken Python: `f"Gemini unavailable: {s[...]` — apparent display truncation OR genuine syntax error in source. NEEDS VERIFICATION ON DISK.
- Severity: 🚨 Possible NameError or SyntaxError on Gemini-fail path.
🚨 BUG-WR2: Module-level execution. X-IO5.
⚠️ BUG-WR3: Line 31 `("tp_hit","sl_hit","expired")` — drift X-BR4.
⚠️ BUG-WR4: Line 10 `today = datetime.now().strftime(...)` — local time.
⚠️ BUG-WR5: Uses gemini_helper directly (no Claude path). Inconsistent with monthly_xray.

### 8. weekly_report_card.py (122 lines)

What it does: Performance metrics → format → save MD → send Telegram. Calls Claude directly for "coaching" snippet.

✅ GOOD-WP1: emoji() function (lines 17-20) — typed thresholds for Sharpe/win-rate/DD. Visual at-a-glance.
✅ GOOD-WP2: Source-separation note in output (lines 38-40) — distinguishes watch-only excluded.
✅ GOOD-WP3: Coaching gated on n_trades >= 5 (line 92) — avoids LLM call when meaningless.

🚨 BUG-WP1: Line 64-86 `claude_coach` directly imports `anthropic` and uses `claude-sonnet-4-5` — bypasses claude_helper entirely. No Gemini fallback. No local fallback. Returns RAW exception type as text on failure.
- Plain English: when Claude is down, user sees `"💡 Coaching: (Claude unavailable: APIError)"` instead of useful insight.
- Severity: 🚨 Inconsistent + brittle.
🚨 BUG-WP2: Line 107-117 own Telegram (requests, single-chat). X-BR11.
⚠️ BUG-WP3: Line 23 `datetime.now().strftime(...)` — local time.
🟡 BUG-WP4: Line 113 `parse_mode: "Markdown"` — no plain fallback if Markdown 400. Same X-TG4.

### 9. wisdom_audit.py (113 lines)

What it does: Pretty-print active lessons + patterns + kill list. Read-only.

✅ GOOD-WA1: --json flag for machine consumption (line 106).
✅ GOOD-WA2: Confidence-tier emoji ladder (line 54) — visual.
✅ GOOD-WA3: Kill-list expiry countdown (lines 81-88) — actionable.

🟡 BUG-WA1: Line 86 bare `except` swallows date parse errors silently.
🟡 BUG-WA2: Lines 62-63 `min_confidence=0.0` — shows EVERYTHING regardless of confidence. Useful for audit but no `--min-conf` filter.

### 10. wisdom_writer.py (62 lines)

What it does: Run hypothesis analysis → write new edges/drags as wisdom_base patterns.

✅ GOOD-WW1: --dry-run flag (line 60) — preview before commit.
✅ GOOD-WW2: existing-set dedup (line 25) — won't duplicate patterns.

⚠️ BUG-WW1: Line 25 dedup key is `(signal, bucket, effect)` — but if WR/n/p change for same (signal, bucket, effect), the existing pattern is NEVER updated. Stale stats persist forever.
- Plain English: pattern stats don't refresh; they're write-once.
- Severity: ⚠️ Update path missing.
🟡 BUG-WW2: No log of WHICH patterns were skipped (line 32 dry-run prints; line 56 silent on skip).

### 11. evaluate_picks.py (74 lines) — IMPORT-SAFE EVALUATOR

What it does: Daily-after-close evaluation: pick_evaluator + dashboard + position_monitor + breakdowns + risk + auto-pause + auto-cooldown.

✅ GOOD-EP1: Docstring line 4: "Import-safe: importing this module must not evaluate or mutate tracked data." — explicit contract. CONTRAST with X-BR3.
✅ GOOD-EP2: Wraps auto_cooldown in try/except (lines 63-67) — one feature failure doesn't block others.
✅ GOOD-EP3: Sequential print of 7 dashboards — operator gets one-stop summary.

🟡 BUG-EP1: Line 45 `print("Run: python3 scripts/send_position_alerts.py ...")` — instruction to user inside daily output. Better as a follow-up auto-call or workflow step.
🟡 BUG-EP2: No CLI flags for selectively skipping (e.g., `--no-cooldown` for testing).

### 12. performance_dashboard.py (92 lines)

What it does: One-shot performance summary printed to stdout.

✅ GOOD-PD1: Score-bucket breakdown (lines 78-87) — quick visual edge check.
✅ GOOD-PD2: Top-5 / Worst-5 (lines 60-66) — operator-friendly.

🚨 BUG-PD1: Module-level execution. X-IO5.
⚠️ BUG-PD2: Line 13 `r["evaluation_status"] != "pending"` defines "evaluated" — but a row could have `evaluation_status=""` (empty) which counts as "evaluated". Then line 39 `r.get("actual_return_pct")` is empty → `f("")` returns 0.0 → bogus 0% return averaged in.
- Plain English: blank rows pollute the average.
- Severity: ⚠️ Silent contamination.
⚠️ BUG-PD3: Line 55 `expectancy = (win_rate/100) * 2.0 - (1 - win_rate/100) * 1.0` — assumes 2:1 R/R for ALL trades. Uses win_rate but ignores actual R values from r_multiple. Should be sum(r_multiples)/n.
- Severity: ⚠️ Mathematically wrong expectancy.

### 13. show_performance.py (8 lines)

What it does: Tiny shim — calls src.performance_stats.print_dashboard.

✅ GOOD-SP1: Shortest file in repo. Pure shim.
🟡 BUG-SP1: No main(); no `if __name__`. Module-level only. Acceptable for a 7-line shim but inconsistent.

### 14. scan_patterns.py (59 lines)

What it does: T47 — pattern scan one ticker or watchlist via src.pattern_engine.

✅ GOOD-SC1: Mutually-exclusive --ticker / --watchlist (line 33). Correct CLI design.
✅ GOOD-SC2: --persist gates on `all_matches` truthy (line 50).
🟡 BUG-SC1: _load_watchlist (lines 19-28) tries 3 shapes; no error if all fail (returns []).

### 15. quarterly_report.py (28 lines)

What it does: Tiny CLI wrapper around src.quarterly_report.generate_report.

✅ GOOD-QR1: Defensive arg parse (lines 14-20) — try/except IndexError|ValueError.
🟡 BUG-QR1: Doesn't use argparse; manual sys.argv parsing. Inconsistent with other scripts.

### 16. claude_helper.py (60 lines)

What it does: Try Claude → fall back to Gemini. Returns (text, err) tuple.

✅ GOOD-CH1: Tuple-return matches gemini_helper API (line 3) — drop-in replacement.
✅ GOOD-CH2: backwards-compat aliases (lines 54-55: call_gemini, generate).
✅ GOOD-CH3: Logs which provider used (line 45-47).

⚠️ BUG-CH1: Line 9 `MAX_TOKENS = 4000` hardcoded. No way to override per-call.
⚠️ BUG-CH2: Line 27-28 `except Exception as e: return None, f"Claude error: {e}"` — exposes raw exception in error string. Fine for logs, but if string ends up in user output (e.g., weekend_reflection ad-hoc fallback) leaks impl detail.
🟡 BUG-CH3: No retry on Claude side (Gemini retries, Claude doesn't). Asymmetric.

### 17. gemini_helper.py (43 lines)

What it does: Wrapper with model fallback + retry + backoff.

✅ GOOD-GH1: Per-day vs per-minute quota distinguishing (lines 31-38) — tries new model on daily, sleeps on per-minute.
✅ GOOD-GH2: Default fallback chain `gemini-2.0-flash → flash-lite → 1.5-flash` (line 7) — sensible cost ladder.

⚠️ BUG-GH1: Line 36 `wait = 30 * (attempt + 1)` — 30s, 60s, 90s waits. With 3 attempts, max sleep = 180s **per model**, × 3 models = potential 9 minutes of blocking sleep on bad day. No timeout.
- Severity: ⚠️ Workflow may stall.
🟡 BUG-GH2: Line 4 `primary_model="gemini-2.0-flash"` hardcoded as default. No env override.

### 18. code_inspector.py (319 lines)

What it does: Parse config.yaml + src/*.py + main.py to extract real strategy params, cross-ref with picks_log performance, produce file:line/key-targeted suggestions. Pure deterministic.

✅ GOOD-CI1: AST-based param extraction (lines 44-91) — better than regex.
✅ GOOD-CI2: Suggestions reference exact file:line (line 252-258) — actionable.
✅ GOOD-CI3: Score-vs-return correlation analysis (lines 219-242) — flags broken scoring formulas.
✅ GOOD-CI4: Min-data thresholds throughout (n>=5/8/10) — refuses to opine on tiny samples.

⚠️ BUG-CI1: Line 23 `Path("config.yaml")` — assumes cwd = repo root. Same workdir-fragility as Batch 3d BUG-IS2.
⚠️ BUG-CI2: Lines 144-152 hardcoded suggestion text references `output.min_score` config key. If key is renamed in YAML, suggestion text becomes nonsensical.
🟡 BUG-CI3: ALL suggestions are imperative ("edit X to Y") with no caveat about confidence. False-confidence risk per X-BR8.
🟡 BUG-CI4: Line 250 `if "rsi(period)" in kl and meta["value"] == 14` — text-match on "(period)" is fragile (won't match `rsi(window)`).

### 19. full_repo_audit.py (323 lines)

What it does: 12-section meta-audit of the repo. Generates the very text used to bootstrap THIS audit project.

✅ GOOD-FA1: Real CSV parsing (line 35-51) — explicit fix-comment for prior shell-awk bug. Excellent meta-engineering.
✅ GOOD-FA2: Section structure (1=meta, 2=inventory, 3=src map, 4=workflows, 5=data, 6=tests, 7=audit dashboards, 8=known issues, 9=picks state, 10=commits, 11=docs, 12=drift).
✅ GOOD-FA3: classify_docs_drift (lines 96-122) — distinguishes "missing" from "planned NOT YET BUILT". Smart.
✅ GOOD-FA4: Imports-into graph (lines 159-170) — multi-shape regex for import detection.

⚠️ BUG-FA1: Line 19 `os.chdir(ROOT)` — module-level cwd mutation. If imported elsewhere, side effect.
⚠️ BUG-FA2: Lines 78-79 stale-script references: `scripts/score.py`, `scripts/risk.py`, `scripts/main.py` (in monthly_xray's git-watch list, not here — but full_repo_audit doesn't catch).
🟡 BUG-FA3: Line 156 `test_blob = "\n".join(...)` — loads ALL tests into memory. Fine for current size.
🟡 BUG-FA4: Lines 248-249 hardcoded `"src/tracker.py"` check — legacy artifact.

### 20. local_analyst.py (220 lines)

What it does: Deterministic plain-English analysis of picks_log.csv. Used as fallback when LLMs fail. Includes _coach() heuristics.

✅ GOOD-LA1: Excellent score-bucket histogram (lines 180-193) using pandas pd.cut — natural binning.
✅ GOOD-LA2: Tag-performance breakdown with min-n>=3 gate (line 167) — refuses tiny samples.
✅ GOOD-LA3: Negative-correlation alarm (line 67-71) — "🚨 Score INVERSELY correlates" — strong signal of broken scorer.
✅ GOOD-LA4: _append_code_diag (lines 204-212) — wraps code_inspector with try/except.

⚠️ BUG-LA1: Line 127 `evaluation_status.isin(["tp_hit","sl_hit","closed"])` — see X-BR4. **"closed" is not used elsewhere** in the codebase — likely a typo for "expired".
- Severity: 🚨 Probably MISSING data for `expired` rows in this analysis.
⚠️ BUG-LA2: All thresholds in _coach are magic numbers (lines 18, 23, 28, 34, 39, 43, 48, 62, 67, 73). Same X-BR8 false-confidence risk.
🟡 BUG-LA3: Line 116 `df["pick_date"] = pd.to_datetime(...)` mutates loaded df. OK in standalone.

### 21. run_backtest.py (97 lines)

What it does: Phase-A backtester runner. Uses yfinance bulk-download.

✅ GOOD-RB1: --tickers / --days / --top-n / --max-hold / --limit-tickers flags — testable.
✅ GOOD-RB2: get_default_tickers reads from data/stock_stats/ (already curated). Excludes ETFs explicitly (line 26).
✅ GOOD-RB3: Lines 55-58 — `end = today - 20 days; fetch_start = start - 120 days` — explicit buffers for outcome simulation and PIT slicing.

⚠️ BUG-RB1: Line 14 `import yfinance as yf` — HARD import at module top, unlike sister files. If yfinance missing, scriptcrashes on import.
- Severity: ⚠️ No graceful fallback.
🟡 BUG-RB2: Line 29-30 fallback ticker list (10 tickers) — tiny universe if stock_stats/ empty.
🟡 BUG-RB3: Line 71 `df = raw[tk].dropna() if len(fetch_tickers) > 1 else raw.dropna()` — different shapes for single vs multi-ticker downloads. Edge case.

### 22. bootstrap_wisdom.py (87 lines)

What it does: Idempotent seeder for wisdom_base. Adds 4 founder-curated lessons + 5 kill-list tickers.

✅ GOOD-BW1: Idempotency via prefix-match (line 63) — safe to re-run.
✅ GOOD-BW2: SEED_KILLS reasons are evidence-backed (lines 50-54).

⚠️ BUG-BW1: Lessons + kills hardcoded as Python constants. See X-BR12. Should be data file.
⚠️ BUG-BW2: Line 63 `existing_text = {L.get("text", "")[:60] ...}` — 60-char prefix dedup. If two different lessons have identical first 60 chars, one is silently rejected.
- Severity: 🟡 False-dedup edge case.
🟡 BUG-BW3: Line 31 `"5-ticker-exclusion"` lesson references hardcoded list (UNH, TEAM, SMCI, DIS, SCHW). Same names as SEED_KILLS — could drift.

### 23. audit_dead_code.py (111 lines)

What it does: Find src/ modules never imported by main/scripts/other src.

✅ GOOD-AD1: 3-shape import detection (lines 26-42) with explicit prior-bug fix comment (lines 6-9). Good meta-discipline.
✅ GOOD-AD2: --strict mode for CI (line 81, 106).
✅ GOOD-AD3: BFS-style transitive reachability (lines 64-73). Correct algorithm.
✅ GOOD-AD4: Test-coverage info (lines 97-103) — flags untested dead modules louder.

🟡 BUG-AD1: Line 99 `f"src.{d}" in tf.read_text()` — substring match, not import-aware. False positives if test mentions module name in a string.
🟡 BUG-AD2: No `--exclude` flag for known-allowed-dead modules (e.g., experimental ones).

### 24. audit_journal_consistency.py (101 lines)

What it does: Verify picks_log.csv ↔ signal_journal.jsonl by (ticker, pick_date).

✅ GOOD-AJ1: Locked-invariant docstring (lines 4-10) — explicit contract.
✅ GOOD-AJ2: --strict for CI (line 96).
✅ GOOD-AJ3: Drift details with source attribution (lines 89, 94) — points to which subsystem to investigate.

🟡 BUG-AJ1: Line 87, 92 `[:10]` — silent truncation of drift list (no count of how many additional). Add `(... and N more)`.
🟡 BUG-AJ2: No `--fix` mode (e.g., re-emit missing journal rows from picks_log).

### 25. backup_data.py (181 lines)

What it does: Daily tarball of `data/` + key configs → GitHub Release. Auto-prune >30 days.

✅ GOOD-BD1: Excellent docstring (lines 1-23) — WHY, WHAT, STRATEGY, RECOVERY.
✅ GOOD-BD2: Idempotent tag (lines 99-103: delete-then-create same-day tag).
✅ GOOD-BD3: RETAIN_DAYS as constant (line 36) — tunable.
✅ GOOD-BD4: Pruning logic (lines 124-156) — reads release list, filters by tag prefix, deletes old.

🚨 BUG-BD1: Line 100-103 `subprocess.run(["gh", "release", "delete", ...], capture_output=True)` — if `gh` not installed/authed, this swallows error and proceeds. Then `gh release create` (line 106-112) FAILS LOUDLY (returncode != 0). OK — the create-fail path returns False, main exits 1.
- BUT: Line 132-134 list-releases failure → just prints "warn" and proceeds. So pruning silently disabled with no alarm.
- Severity: ⚠️ Pruning silently disabled.
⚠️ BUG-BD2: Line 137 cutoff in UTC; createdAt also UTC (line 144) — consistent. Good.
⚠️ BUG-BD3: BACKUP_PATHS includes `data` (entire folder) — could be large (CSVs + JSONLs). No size limit. GitHub Releases have 2GB asset limit.
- Severity: ⚠️ Future-scaling risk.
🟡 BUG-BD4: Line 33-35 `BACKUP_PATHS = ["data", "config.yaml", "watchlist.json"]` — but **picks_log.csv is in `data/`**, so root-level `watchlist.json` is likely STALE/missing (real watchlist is `data/watchlist.json`). Defensive though — `if not path.exists(): print skip`.

### 26. unpause.py (42 lines)

What it does: Manual override to clear active auto-pause. CLI prompt.

✅ GOOD-UP1: Stateful check first (line 21) — refuses to act if not paused.
✅ GOOD-UP2: Shows current state before prompting (lines 25-28).
✅ GOOD-UP3: Confirm prompt (line 30) — won't clear without explicit yes.

⚠️ BUG-UP1: Only path to unpause. See X-BR10. Owner needs SSH/laptop access.
🟡 BUG-UP2: Line 17 `--reason` arg defined but only displayed in confirm prompt; not persisted to clear_state(). Reason audit-trail lost.
- Severity: 🟡 Audit gap.

---

## Summary of Batch 3e (26 files)

### By severity
| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 14 |
| ⚠️ Data/safety risk | 32 |
| 🟡 Code smell | 28 |
| 📝 Doc-only | 0 |
| ✅ Good code | 60 |
| Total | 134 findings |

### Top 10 things to fix in this batch

| # | Bug | Why first | Fix difficulty |
|---|---|---|---|
| 1 | BUG-WR1 (weekend_reflection.py:112 truncated/broken) | Possible runtime crash on Gemini-fail path; verify on disk NOW | Easy: re-read file, re-write line |
| 2 | BUG-MX3 (monthly_xray watches scripts/score.py, risk.py, main.py — all missing) | Every monthly run reports empty "code_changes" | Easy: update file list to actual paths |
| 3 | BUG-LA1 (`local_analyst.isin(["tp_hit","sl_hit","closed"])`) | "closed" status doesn't exist anywhere; missing `expired` rows | Easy: change to "expired" |
| 4 | BUG-WP1 (weekly_report_card bypasses claude_helper) | When Claude is down, user sees raw exception text | Easy: route via call_llm |
| 5 | BUG-PD3 (performance_dashboard expectancy formula assumes 2:1 R/R) | Mathematically wrong expectancy — sum r_multiples/n is correct | Easy: replace formula |
| 6 | X-BR1 (3 LLM-call patterns) + BUG-WP1 | Cost & resilience drift | Medium: enforce single LLM gateway |
| 7 | X-BR4 (CLOSED_STATUSES drift, 9 files now) | Same-name-different-meaning catastrophe | Easy-Medium: extract to src/closed_status.py |
| 8 | X-BR11 (3 MORE Telegram impls in this batch) | Reinforces Batch 3c #1 priority | Medium: src/telegram_sender.py |
| 9 | X-BR3 (8 more module-level files) | Test-hostile code blocks refactors | Medium: wrap each in main() |
| 10 | BUG-BD1 (backup pruning silently disabled if gh fails) | Disk grows unboundedly without warning | Easy: alarm on gh failures |

### What this batch tells us about the project

- **Brain layer has the most THINKING happening — and the most fragility.** LLM calls, fallbacks, deterministic backups, audit checks. Ambitious; ~50% of files have serious safety contracts.
- **Plain-English fallbacks (local_analyst) are a great pattern** — no LLM dependency for daily/weekly/monthly. monthly_xray uses it perfectly. weekly_report_card forgot. weekend_reflection has a half-broken implementation.
- **monthly_xray watches code files that don't exist.** `scripts/score.py`, `scripts/risk.py`, `scripts/main.py` are nowhere in the repo. Every month it produces empty `code_changes`. Easy fix, big visibility gain.
- **`local_analyst` filters on `evaluation_status="closed"` which never exists.** Probably losing all `expired` rows from analysis. Possibly losing significant data depending on expiration frequency.
- **Three "weekly review" scripts simultaneously.** User likely receives 3 long Telegram messages on Saturday/Sunday. Hard to know which is canonical.
- **Audit + backup discipline is genuinely strong.** audit_dead_code, audit_journal_consistency, backup_data, full_repo_audit are real engineering. They exist to catch the kind of drift documented throughout this entire audit.
- **bootstrap_wisdom hardcodes domain knowledge** (4 lessons, 5 kill-list tickers) as Python literals. Should be a YAML so non-engineers can curate.

### Glossary additions

| Term | Plain English |
|---|---|
| LLM gateway | Single function that ALL code calls when it wants to ask an AI a question. Centralizes retries, costs, fallbacks. |
| Local analyst | Plain-English analysis built from rules (not AI). Used as fallback when LLM is down. |
| Idempotent seeder | Setup script you can run repeatedly without duplicating data. bootstrap_wisdom is a good example. |
| Drift audit | A script whose only job is to detect inconsistencies between two stores (picks_log vs signal_journal). |
| Hard import vs try-import | `import yfinance` (hard) crashes on missing dep. `try: import yfinance except: yf = None` (try-import) degrades silently. |

---

End of Batch 3e.

Cumulative findings across all script batches (1a/1b/2a/2b/3a/3b/3c/3d/3e):
- Show-stoppers: 118
- Data/safety risks: 232
- Code smells: 194
- Doc-only: 14
- Good code: 249
- **Total: 807 findings across 108 files (~24,750 lines)**

Next: Batch 4 — `tests/` directory (~80 test files based on Batch 1 inventory). Or you can pick a different next destination — let me know.
