# Audit Batch 2b — All Other GitHub Workflows (15 files)

**Date:** 2026-05-12
**Files:** All 15 workflows in `.github/workflows/` except `daily-picks.yml` (audited in Batch 2a)
**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

## Workflow inventory in plain English

| # | Workflow | What it does | When it fires |
|---|---|---|---|
| 1 | `backup.yml` | Backs up `data/` folder to GitHub Releases | Daily 23:00 UTC |
| 2 | `ci.yml` | Runs tests + syntax check + smoke tests | On every push/PR to main |
| 3 | `evaluate.yml` | Closes pending picks, generates dashboards, ships exec X-ray | Weekday 22:00 UTC (after US close) |
| 4 | `holiday_renewal_reminder.yml` | Reminds you to add NYSE holidays for next year | Jan 1 + Jul 1 each year |
| 5 | `hypothesis_weekly.yml` | Runs weekly hypothesis review | Sundays 15:00 UTC |
| 6 | `intraday_monitor.yml` | Monitors open positions during US market hours | Every 30 min during market hours |
| 7 | `late_watch_only.yml` | Backup path: send late watch-only ideas if daily-picks missed | 09:25 + 09:40 ET on weekdays |
| 8 | `monthly_xray.yml` | Generates LLM-driven monthly X-ray review | 1st of month 22:00 UTC |
| 9 | `news_engine.yml` | Pulls news, classifies, updates watchlist | Every 30 min during 8-23 UTC weekdays |
| 10 | `news_evidence.yml` | Builds news outcome attribution + evidence reports | Weekday 22:30 UTC |
| 11 | `nightly_brain.yml` | Brain maintenance + Sunday meta-brain digest | Daily 23:00 UTC |
| 12 | `watchdog.yml` | Pre-market check: if no picks logged, ALERT + auto-trigger daily-picks | 09:10 + 09:18 ET weekdays |
| 13 | `weekend_reflection.yml` | Saturday 8 AM SGT reflection generator | Saturday 00:00 UTC |
| 14 | `weekly_report.yml` | Weekly performance report card | Saturday 01:00 UTC |
| 15 | `yearly_recap.yml` | Yearly recap to Telegram | Jan 2 12:00 UTC |

**Plain English:** Your project has FIFTEEN automated jobs running on schedule, plus the main `daily-picks.yml`. That's 16 cron-driven processes. They generate, evaluate, learn, alert, back up, and report. Worth understanding the orchestration as a whole.

---

## CROSS-CUTTING FINDINGS (apply across many workflows)

### 🚨 X-1: Dependency-install patterns are inconsistent across workflows
| Workflow | What gets installed |
|---|---|
| `daily-picks.yml` | `requirements.txt + pytest` |
| `daily-picks.yml` (late-watch path) | only `yfinance + curl_cffi` (BUG-W9) |
| `late_watch_only.yml` | only `yfinance + curl_cffi` (same risk!) |
| `intraday_monitor.yml` | only `yfinance + pandas` (line 74) |
| `news_evidence.yml` | `requirements.txt + yfinance + curl_cffi` (line 95-96) — pinned versions ON TOP of requirements |
| `nightly_brain.yml` | `requirements.txt` (full) |
| Others | `requirements.txt` (full) |

- **Plain English:** Some workflows install ONLY 2 libraries; others install everything. The "minimal install" workflows risk runtime failures if their scripts grew dependencies over time.
- **Why critical:** `intraday_monitor.yml` runs **52 times per day** with only yfinance+pandas. If `scripts/intraday_monitor.py` ever imports `requests`, `pyyaml`, `dotenv`, etc., it crashes — silently not alerting you of position issues mid-day.
- **Severity:** 🚨 Likely silent failures.

### 🚨 X-2: Pip cache configured in only 2 of 15 workflows
- ✅ `ci.yml` (line 20: `cache: pip`)
- ✅ `hypothesis_weekly.yml` (line 23: `cache: pip`)
- ❌ All other 13 workflows install fresh every run
- **Cost impact:** ~30 sec × hundreds of runs/month = hours of free compute saved
- **Severity:** 🟡 Cost / speed; easy fix.

### 🚨 X-3: Push-retry pattern duplicated in 13 workflows with subtle variations
| Workflow | Retry count | Sleep | Strategy |
|---|---|---|---|
| `daily-picks.yml` (3 places) | 5 | linear `i*2` | with stash |
| `evaluate.yml` (2 places) | 3 | fixed 3s | no stash |
| `intraday_monitor.yml` | 3 | fixed 5s | no stash |
| `late_watch_only.yml` | 5 | linear `i*2` | no stash |
| `monthly_xray.yml` | 3 | fixed 3s | no stash |
| `news_engine.yml` | 3 | fixed 3s | no stash |
| `news_evidence.yml` | 5 | linear `i*2` | no stash |
| `nightly_brain.yml` | 3 | fixed 5s | no stash |
| `watchdog.yml` | 3 | linear `i*2` | no stash |
| `weekend_reflection.yml` | 3 | fixed 3s | no stash |
| `weekly_report.yml` | 3 | fixed 3s | no stash |
| `hypothesis_weekly.yml` | none — single attempt with `|| true` | — | — |
| `news_evidence.yml` | 5 | linear | no stash |

- **Plain English:** Same code copied 13+ times with different retry counts. When you need to fix one (e.g., add stash for a workflow that started conflicting), you must update 13.
- **Severity:** 🚨 Drift risk + hard to maintain.

### 🚨 X-4: Hardcoded `assignees: ['anjanneogi13']` in 5 workflows
- `daily-picks.yml` line 457
- `evaluate.yml` lines 90, 126
- `monthly_xray.yml` line 70
- `weekend_reflection.yml` line 71
- (`weekly_report.yml` does NOT — line 73 doesn't include assignees, slight inconsistency)
- **Severity:** 🟡 Single-user assumption.

### ⚠️ X-5: `git push || true` swallows push failures in 6 workflows
- `evaluate.yml` line 66, 161
- `hypothesis_weekly.yml` line 43
- `monthly_xray.yml` line 91
- `weekend_reflection.yml` line 93
- `weekly_report.yml` line 94
- **Plain English:** If push fails after retries, the `|| true` makes the workflow report SUCCESS anyway. **You'd never know commits weren't pushed.**
- **Severity:** ⚠️ Silent push loss.

### ⚠️ X-6: 3 distinct dedup-marker strategies
| Strategy | Used by |
|---|---|
| `data/.last_run_X.txt` marker file | evaluate, monthly_xray, weekend_reflection, weekly_report |
| `data/late_daily_ideas_sent_DATE.json` | late_watch_only |
| `grep -c "^DATE" data/picks_log.csv` | daily-picks, watchdog |
| No dedup at all | backup, ci, holiday_renewal, hypothesis_weekly, intraday_monitor, news_engine, news_evidence, nightly_brain, yearly_recap |
- **Plain English:** Three different ways to say "did this already run today?" Inconsistent.
- **Severity:** ⚠️ Maintainability.

### ⚠️ X-7: Many `git add` commands use `2>/dev/null || true` — silent on missing files
- Examples: evaluate L61, intraday L92-95, late_watch L125, news_engine L52, weekend L88, hypothesis L41
- If an artifact path TYPO'd silently, you'd never know — `git add foo_typo_*.json` matches nothing, then `|| true` masks it.
- **Severity:** ⚠️ Silent artifact loss.

### 🟡 X-8: Python version inconsistency
- Python `3.11` used by: backup, ci, hypothesis_weekly, monthly_xray, weekend_reflection, weekly_report
- Python `3.12` used by: daily-picks, evaluate, holiday_renewal, intraday_monitor, late_watch_only, news_engine, news_evidence, nightly_brain, watchdog, yearly_recap
- **Plain English:** Two Python versions across 15 workflows. If a `src/` module uses 3.12-only syntax (`type X = int` PEP 695), the 3.11 workflows crash.
- **Severity:** 🟡 Cross-version bug risk; pin one version everywhere.

### 🟡 X-9: Timeout configured in only 4 of 15 workflows
- ✅ backup (10), ci (10), hypothesis_weekly (10), news_engine (8), news_evidence (15)
- ❌ Other 10 workflows have no timeout — default 6 hours per job
- **Severity:** 🟡 Cost risk for any workflow that hangs.

---

## PER-WORKFLOW LINE-BY-LINE FINDINGS

---

### 1. `backup.yml` (56 lines) — Daily Backup System

**✅ GOOD-B1:** Has `timeout-minutes: 10` (line 22) — protected
**✅ GOOD-B2:** Has `concurrency` (lines 15-17) — no overlapping backups
**✅ GOOD-B3:** Verifies release exists after backup (lines 48-55) — fails loudly if backup didn't actually create release

**⚠️ BUG-B1:** Line 32 uses Python 3.11 but the actual `backup_data.py` script may import newer-Python features. No reason to pin to 3.11 here. Severity: 🟡

**⚠️ BUG-B2:** Line 9 cron `'0 23 * * *'` — runs every day including weekends. Backups on Sat/Sun will mostly back up unchanged data (no new picks). Wastes ~2 backups/week. Severity: 🟡 Cost.

**🚨 BUG-B3:** No size cap or retention check on the backup. If `data/` ever grows large (current is small, but `signal_journal.jsonl` and `news_log.jsonl` grow forever), backups will eventually fail or eat GitHub Release storage. **No documented retention policy.** Severity: 🚨 Future scale issue.

**⚠️ BUG-B4:** Verifies release tag named `backup-YYYY-MM-DD`. If backup script writes a different tag format, verification fails. Two source of truth (workflow vs script). Severity: ⚠️

---

### 2. `ci.yml` (59 lines) — Continuous Integration

**✅ GOOD-CI1:** Has `cache: pip` (line 20) — saves ~30 sec/run
**✅ GOOD-CI2:** Has `timeout-minutes: 10` (line 12)
**✅ GOOD-CI3:** Syntax check on ALL .py files before pytest (lines 30-44) — catches obvious imports/syntax errors
**✅ GOOD-CI4:** `bootstrap_wisdom.py` run twice (lines 51-52) — idempotency check
**✅ GOOD-CI5:** Smoke tests for quarterly + weekly (lines 54-58)

**🚨 BUG-CI1:** **`pytest tests/ -q --tb=short` (line 47) has NO failure threshold.** If 199 of 200 tests pass, CI is green. If your test count is 200+ (per inventory), one new flaky test makes CI useless overnight.
- Fix: enforce strict pass with `--strict-markers --maxfail=1` or set up CI to flag new failures vs known.
- Severity: ⚠️

**🚨 BUG-CI2:** **No coverage measurement, no coverage threshold.** A "passing" CI tells you nothing about untested code paths. Given the audit revealed many silent failure paths in main.py, coverage data would be invaluable.
- Fix: add `pytest-cov`, set minimum threshold (start at current %, increase over time).
- Severity: 🚨

**🚨 BUG-CI3:** **CI runs only `tests/` — but what about `scripts/` and root .py files?** No tests for `scripts/*.py` (80 files). No tests for `main.py`, `app.py`, `backtest.py`, `evaluate_picks.py`. Combined with massive script surface, untested code dominates.
- Severity: 🚨 Test coverage gap.

**⚠️ BUG-CI4:** `python -c "..."` heredoc syntax check (lines 31-44) is fragile — embeds Python code as a string in YAML in a shell script. If anyone touches indentation, breaks.
- Fix: extract to `scripts/syntax_check.py`.
- Severity: 🟡

**⚠️ BUG-CI5:** Smoke test `quarterly_report.py --days 30` (line 55) will fail if there isn't 30 days of data. New repo / fresh checkout will fail CI on this step.
- Severity: 🟡 Brittle bootstrap.

**🟡 BUG-CI6:** Python 3.11 (line 19) — see X-8.

**🟡 BUG-CI7:** No matrix testing across Python versions. Production runs 3.12. CI tests 3.11. Mismatch.
- Severity: ⚠️

**🟡 BUG-CI8:** No linter (ruff, flake8, black). Style drift over time.
- Severity: 🟡

---

### 3. `evaluate.yml` (162 lines) — Daily Pick Evaluation

**✅ GOOD-E1:** Single-fire schedule with explicit DST math (lines 5-8) — defensive comment
**✅ GOOD-E2:** Marker-file dedup with workflow_dispatch bypass (line 30) — manual override works
**✅ GOOD-E3:** `continue-on-error: true` on position alerts (line 145) — non-fatal step explicitly marked

**🚨 BUG-E1:** Steps 50-52 run `evaluate_picks.py` — but as audited in Batch 1a (BUG-41/42), there are TWO `evaluate_picks.py` files (top-level vs scripts/). The workflow runs `scripts/evaluate_picks.py`. The top-level one is dead.
- Severity: 🚨 (already counted in Batch 1a)

**🚨 BUG-E2:** Line 70 `performance_dashboard.py > /tmp/dashboard.txt 2>&1 || true`
- Plain English: pipes BOTH stdout AND stderr to the file, then ignores any error.
- Why a problem: the dashboard text saved to `/tmp` will include error messages mixed with data. Then line 81 reads this and posts as an issue body. **A failed dashboard run becomes a polluted GitHub issue posted to you.**
- Severity: ⚠️ Issue pollution.

**⚠️ BUG-E3:** Two separate `git add` + commit blocks (lines 54-66 AND 153-161) — two pushes per run.
- Plain English: workflow commits TWICE, increasing chance of conflicts with concurrent workflows.
- Fix: consolidate to one commit at the end.
- Severity: ⚠️

**⚠️ BUG-E4:** Line 99 `python scripts/send_layman_evening.py` — sends Telegram BEFORE execution X-ray report is generated (line 105). The evening Telegram doesn't include exec X-ray data.
- Plain English: order issue — exec X-ray happens AFTER the user-facing summary already sent.
- Severity: ⚠️ Order of operations.

**🟡 BUG-E5:** Line 58 commit author email `41898282+github-actions[bot]@users.noreply.github.com` is the GitHub-Actions bot prefix, but other workflows use `github-actions[bot]@users.noreply.github.com` (no number). Inconsistent.
- Severity: 🟡 Style drift.

**🟡 BUG-E6:** Line 137 `python scripts/send_exec_telegram.py $DATE` — passes date as positional arg without quotes. If `$DATE` is empty (something went wrong), script gets ZERO args. No fail-safe.
- Severity: 🟡

**🟡 BUG-E7:** No timeout on this workflow. Could hang if any step hangs (LLM call, Telegram, etc.)
- Severity: 🟡

---

### 4. `holiday_renewal_reminder.yml` (109 lines) — NYSE Holiday Cache Reminder

**✅ GOOD-H1:** Excellent design — fires twice a year (Jan 1 + Jul 1), creates GitHub issue with detailed instructions, auto-skips if already-open issue exists
**✅ GOOD-H2:** Comments explain what the reminder is for (lines 87-90)
**✅ GOOD-H3:** Issue body includes step-by-step instructions for non-coder maintenance (lines 79-85) — exemplary

**⚠️ BUG-H1:** Line 36 inline `python3 -c "..."` heredoc — same fragility as BUG-CI4. If `src.market_calendar` API changes (renaming `renewal_urgency`), workflow breaks silently next Jan 1 / Jul 1.
- Severity: ⚠️ Long-tail breakage waiting to happen.

**🟡 BUG-H2:** `${{ steps.check.outputs.msg }}` (line 53) interpolated into JS template literal. If `msg` contains backticks or `${...}`, breaks the JS.
- Severity: 🟡

**🟡 BUG-H3:** No timeout.
- Severity: 🟡

---

### 5. `hypothesis_weekly.yml` (44 lines) — Weekly Hypothesis Review

**✅ GOOD-HW1:** Has `timeout-minutes: 10` and `cache: pip`
**✅ GOOD-HW2:** Single-fire schedule with comment explaining timing relative to other workflows

**⚠️ BUG-HW1:** Line 43 `git push || true` — see X-5. Silent push loss.

**⚠️ BUG-HW2:** Line 41 `git add data/reports/hypothesis/ || true` — silent on missing dir. If `run_hypothesis_review.py` writes to a DIFFERENT path (e.g., script refactored), no commits ever happen, no error surfaced.
- Severity: ⚠️

**🟡 BUG-HW3:** No dedup guard. If GitHub double-fires Sundays 15:00 (rare but possible), runs twice.
- Severity: 🟡

---

### 6. `intraday_monitor.yml` (108 lines) — Intraday Position Monitor

**✅ GOOD-IM1:** Detailed DST guard with comment explaining the dual-cron strategy (lines 5-15)
**✅ GOOD-IM2:** Proper opening-range targeted vs baseline cron separation
**✅ GOOD-IM3:** Manual dispatch bypasses time guard (line 36-39) — usable for debugging

**🚨 BUG-IM1:** Line 74 `pip install yfinance pandas` — see X-1 (minimal install).
- **Highest-impact case** because this runs **52 times per day** during market hours (every 30 min × 6.5 hours × 4-7 weekdays/week).
- Severity: 🚨

**🚨 BUG-IM2:** Line 79 `python scripts/intraday_monitor.py` — no timeout, no error handling. If yfinance hangs (no timeout in main.py BUG-52), this workflow hangs for 6 hours, blocking concurrency-grouped subsequent runs.
- Combined with BUG-IM3, the workflow group key uses `${{ github.run_id }}` (line 19) which is UNIQUE per run — so concurrency isn't actually preventing overlaps.
- Severity: 🚨

**⚠️ BUG-IM3:** Concurrency group uses `${{ github.event.schedule || github.run_id }}` (line 19) — for scheduled runs, group is the cron string; for manual, group is the unique run ID. Manual triggers bypass the lock.
- Plain English: two manual triggers in 30 sec = two parallel runs.
- Severity: ⚠️

**🚨 BUG-IM4:** Line 86 `python scripts/send_intraday_telegram.py` — sends Telegram even if monitor produced nothing useful. No "if alerts" gate. Silent on what triggered the send.
- Severity: ⚠️ Telegram spam risk.

**⚠️ BUG-IM5:** Line 77 secret `FINNHUB_API_KEY` is set, but line 86 (Telegram step) doesn't have it. If `send_intraday_telegram.py` needs Finnhub, fails.
- Severity: 🟡 Speculative.

**⚠️ BUG-IM6:** Up to 4 `git add -f data/...` lines (92-95). If a NEW alert artifact type is added, easy to forget.
- Severity: 🟡 Manifest drift.

**🟡 BUG-IM7:** No timeout (workflow-level).
- Severity: 🟡

**🟡 BUG-IM8:** Permission `contents: write` (line 26) — needed for commit. OK but should also add `actions: read` to allow log access.
- Severity: 🟡

---

### 7. `late_watch_only.yml` (145 lines) — Late Watch-Only Daily Ideas (independent)

This is a SEPARATE workflow from the late-watch path inside `daily-picks.yml`. Two paths to do the same thing.

**🚨 BUG-LW1 (CRITICAL):** **There are TWO ways to send late watch-only ideas:**
- Path A: inside `daily-picks.yml` (lines 117-150 in Batch 2a)
- Path B: this entire separate workflow `late_watch_only.yml`
- Both have similar guards and call the same `send_late_daily_ideas_telegram.py`
- **Risk:** double-sending. Both paths might trigger and both send Telegrams.
- **Mitigation present:** the `data/late_daily_ideas_sent_${ET_DATE}.json` ledger (lines 102 in 2a, 125 in 2b) prevents duplicate sends.
- **But:** if both run nearly simultaneously, neither sees the OTHER's ledger write yet → race condition → double-send.
- Fix: pick ONE path, delete the other.
- Severity: 🚨 Architecture redundancy + race condition.

**✅ GOOD-LW1:** Excellent header comment (lines 9-14) declaring safety constraints — model for other workflows.
**✅ GOOD-LW2:** Wrong-DST-slot guard (line 51) prevents 14:25/14:40 UTC from running outside intended hour.
**✅ GOOD-LW3:** Three-stage dedup (DST slot, before cutoff, official picks present) — robust.

**🚨 BUG-LW2:** Same minimal install (line 92) — see X-1.

**⚠️ BUG-LW3:** Line 67 same fragile `grep -c` pattern as BUG-W4.

**🟡 BUG-LW4:** Inline thresholds on line 99 — same as BUG-W10.

---

### 8. `monthly_xray.yml` (92 lines) — Monthly X-Ray

**✅ GOOD-MX1:** Single-fire SGT-based schedule with comment

**⚠️ BUG-MX1:** Line 41 Python 3.11 — see X-8.
**⚠️ BUG-MX2:** Line 91 `git push || true` — see X-5.
**⚠️ BUG-MX3:** Lines 50-51 expose BOTH `GEMINI_API_KEY` and `ANTHROPIC_API_KEY` — uses both LLM providers? Or only one and the other is dead? See req.txt BUG-3.
- Severity: 🟡 Cost / dead-secret risk.

**🟡 BUG-MX4:** No timeout on a workflow that calls multiple LLMs (could rack up costs if it loops).
- Severity: 🟡

**🟡 BUG-MX5:** Line 70 `assignees: ['anjanneogi13']` — see X-4.

---

### 9. `news_engine.yml` (58 lines) — News Engine

**✅ GOOD-NE1:** Has `timeout-minutes: 8`
**✅ GOOD-NE2:** Excellent comment about removing duplicate cron (lines 7-10) — "the previous EDT+EST pair caused 2x Anthropic API calls every 30 min"
**✅ GOOD-NE3:** Concurrency group prevents overlapping runs of same cron schedule

**🚨 BUG-NE1:** Lines 40-42 expose **`ALPACA_API_KEY`, `ALPACA_API_SECRET`, `ALPACA_BASE_URL`** as secrets to the news engine.
- Plain English: News engine has access to your trading account credentials.
- Why a problem: news engine should NOT need trading credentials. If `run_news_engine.py` ever has a bug or is compromised, it could place trades.
- **Combined with BUG-1 (Alpaca dependency present):** real attack surface.
- Fix: REMOVE these env vars from this workflow. News engine doesn't need them.
- Severity: 🚨 Security: principle of least privilege violated.

**🟡 BUG-NE2:** No `concurrency cancel-in-progress: true` — successive 30-min cron fires can pile up if one runs slowly.
- Defensible: news is incremental, queueing is OK.
- Severity: 🟡

**⚠️ BUG-NE3:** Cron `'*/30 8-23 * * 1-5'` = 32 runs/day × 5 = **160 runs/week**. Each calls Anthropic API. **Cost discipline:** is this needed at this frequency?
- Severity: 🟡 Cost.

**🟡 BUG-NE4:** Line 58 `git push || true` — see X-5.

---

### 10. `news_evidence.yml` (169 lines) — News Outcome Evidence

**✅ GOOD-NV1:** Header comment (lines 3-5) declares monitoring-only intent — exemplary
**✅ GOOD-NV2:** Workflow-level `env:` block (lines 41-46) explicitly sets `PAPER_TRADING_ENABLED=false`, `LIVE_TRADING_ENABLED=false`, `TRADING_MODE=monitoring`, etc. — defensive
**✅ GOOD-NV3:** Input validation with regex (lines 66-77) for date/numeric inputs — best example of input validation in any workflow
**✅ GOOD-NV4:** **Two-stage execution**: preflight no-write run (lines 98-110) BEFORE generation (lines 112-122) — catches errors before mutating state
**✅ GOOD-NV5:** **Safety check** (lines 132-139): `git diff --exit-code` against critical files — fails workflow if news evidence accidentally mutated picks_log/journals
**✅ GOOD-NV6:** Has `timeout-minutes: 15`
**✅ GOOD-NV7:** Comment about keeping large JSONs out of git (lines 146-148) — storage discipline

**This is the most disciplined workflow in the repo. It should be the model.**

**⚠️ BUG-NV1:** Line 96 installs `yfinance==0.2.65 curl_cffi==0.7.4` ON TOP of `requirements.txt`. Pinned overrides — if `requirements.txt` already pins these (it does — line 11 `yfinance==0.2.65`), the override is redundant.
- Severity: 🟡 Redundant.

**⚠️ BUG-NV2:** Line 161 retry-with-exit (no `|| true` here, good) — but inconsistent with siblings.
- Severity: 🟡

---

### 11. `nightly_brain.yml` (110 lines) — Nightly Brain Maintenance

**✅ GOOD-NB1:** Comment explains scheduling relative to other workflows (lines 4-6)
**✅ GOOD-NB2:** Dual-job design: `nightly-brain` always runs, `meta-brain-sunday` only on Sundays (line 76)
**✅ GOOD-NB3:** **Verify step** (lines 35-57) — checks that brain steps actually succeeded by reading `learning_journal.jsonl`. Loud failure if 4+ steps failed.

**🚨 BUG-NB1:** Line 55-56 fail-threshold is `failed >= 4`. If 3 of 5 brain steps fail, workflow is GREEN. **You'd never know the brain is partially broken.**
- Fix: lower threshold OR send Telegram alert at any failure.
- Severity: ⚠️

**⚠️ BUG-NB2:** Line 42-43: if `learning_journal.jsonl` doesn't exist, `sys.exit(0)` — silent pass. If the file SHOULD exist (post-bootstrap), this hides a bigger problem.
- Severity: ⚠️

**🚨 BUG-NB3:** Line 65 commits `config/weights.json` — the brain-controlled file (BUG-24 in Batch 1a). **No safety guard here either.** If `run_nightly_brain.py` corrupts `weights.json`, this workflow auto-pushes the corruption.
- Combined with stale `weights.json` (last updated May 4 per BUG-24): the brain's inability to update weights might be self-inflicted by a silent error in this workflow.
- Severity: 🚨 No protection on brain memory write.

**⚠️ BUG-NB4:** No timeout. Brain maintenance can be slow + LLM-heavy.
**⚠️ BUG-NB5:** Line 76 `if: github.event.schedule == '0 23 * * *' || github.event_name == 'workflow_dispatch'` — meta-brain-sunday triggers for ANY scheduled fire of this workflow, then the inner `if dow == 7` check filters. Wasteful (uses checkout job slot for non-Sundays, even if no work done).
- Severity: 🟡

**🟡 BUG-NB6:** Line 20 `token: ${{ secrets.GITHUB_TOKEN }}` — explicit token specification (others use default). Inconsistent.
- Severity: 🟡

---

### 12. `watchdog.yml` (138 lines) — Morning Run Watchdog

**✅ GOOD-WD1:** Excellent header comment (lines 3-13) declaring safety constraints
**✅ GOOD-WD2:** **Auto-rescue** (lines 73-89): if no picks logged AND before cutoff, calls GitHub API to manually trigger `daily-picks.yml`. This is sophisticated.
**✅ GOOD-WD3:** Wrong-DST-slot guard (line 48)
**✅ GOOD-WD4:** Status records on every branch (5+ event types)
**✅ GOOD-WD5:** Different message based on whether before/after cutoff (lines 69-72)

**🚨 BUG-WD1:** Line 24 `permissions: actions: write` — required for the rescue trigger. This is a SIGNIFICANT permission. If watchdog is compromised, it can trigger ANY workflow.
- Plain English: watchdog has the power to start daily-picks (and any other workflow).
- Mitigation: restricted to one specific workflow_dispatch (line 76). Still: principle of least privilege violated.
- Fix: explore if a fine-grained PAT or limited scope is possible.
- Severity: ⚠️ Security.

**🚨 BUG-WD2:** Line 73-79 `curl -X POST .../actions/workflows/daily-picks.yml/dispatches` — if the workflow filename ever changes, breaks silently (returns 404, sends Telegram alert). No symbolic ref.
- Severity: 🟡 Renaming risk.

**⚠️ BUG-WD3:** Line 56 same fragile `grep -c` pattern.
**⚠️ BUG-WD4:** Line 92 `MSG="..."` truncated in fetch — same `%0A` URL-encoding concern as BUG-W21.
**⚠️ BUG-WD5:** Line 110-118 forces `exit 1` (line 113, 118) at end of EVERY watchdog scenario including "alert sent successfully." 
- Plain English: watchdog ALWAYS fails the workflow run (red ❌) when picks are missing, even if it successfully alerted you.
- Why this is intentional: red GitHub run = visible alert in repo "Actions" tab.
- Why it's still confusing: workflow is "failing on purpose" — observability tools (PagerDuty, etc.) can't distinguish "real failure" from "intentional alert failure."
- Fix: either (a) document this clearly, or (b) use exit 0 + GitHub Issue + Telegram for alerting.
- Severity: ⚠️ Anti-pattern but functional.

---

### 13. `weekend_reflection.yml` (94 lines) — Weekend Reflection

**✅ GOOD-WR1:** Marker-file dedup
**✅ GOOD-WR2:** Comment explaining schedule relative to weekly_report (line 7)

**🟡 BUG-WR1:** Python 3.11 (line 42) — X-8.
**⚠️ BUG-WR2:** Line 93 `git push || true` — X-5.
**🟡 BUG-WR3:** Line 71 hardcoded assignee — X-4.
**🟡 BUG-WR4:** No timeout.
**⚠️ BUG-WR5:** Line 65 issue body uses template literal with backticks — same fragility as BUG-H2 if message contains special chars.

---

### 14. `weekly_report.yml` (95 lines) — Weekly Performance Report

**✅ GOOD-WP1:** Marker-file dedup with workflow_dispatch bypass
**✅ GOOD-WP2:** Concurrency lock with comment "belt-and-suspenders" (lines 11-15)

**🚨 BUG-WP1:** Line 76-81 (`Send weekly recap to Telegram`) **is missing the `if: steps.guard.outputs.skip != 'true'` gate** — every other step has it. **If dedup says "already ran," Telegram still fires.**
- Plain English: re-runs (e.g., manual dispatch on the same day) will SKIP everything except the Telegram. You'd get a duplicate Telegram with no fresh data.
- Severity: 🚨 Telegram spam on re-run.

**🟡 BUG-WP2:** Python 3.11 (line 44) — X-8.
**⚠️ BUG-WP3:** Line 94 `git push || true` — X-5.
**🟡 BUG-WP4:** No timeout.
**🟡 BUG-WP5:** Line 73 `assignees:` MISSING here (other workflows have it). Inconsistent.

---

### 15. `yearly_recap.yml` (26 lines) — Yearly Recap

**Smallest workflow.**

**🚨 BUG-YR1:** **No dedup guard.** If GitHub double-fires Jan 2 12:00 UTC, sends Telegram twice.
- Severity: 🚨 (annual event, but still).

**🚨 BUG-YR2:** **No timeout.**
**⚠️ BUG-YR3:** Line 19 `pip install -r requirements.txt` — installs full deps for what is probably a small Telegram script. Wasteful for once-a-year.
**⚠️ BUG-YR4:** No commit step — if `send_layman_yearly.py` writes any artifact, it's lost (Actions runner is ephemeral).
**🟡 BUG-YR5:** Permission `contents: read` (line 10) — most minimal of all workflows. Good. But could need write if ever logging.

---

## Summary of Batch 2b (15 workflows)

### By severity
| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 22 |
| ⚠️ Data/safety risk | 38 |
| 🟡 Code smell | 31 |
| 📝 Doc-only | 0 |
| ✅ Good code | 35 |
| **Total** | **126 findings** |

### Top 10 things to fix across all workflows

| # | Bug | Why first | Fix difficulty |
|---|---|---|---|
| 1 | BUG-NE1 (news_engine has Alpaca trading credentials) | Security — principle of least privilege violated. News engine should NEVER have trading creds. | Easy: remove env vars from news_engine.yml |
| 2 | BUG-LW1 (two parallel paths for late-watch-only) | Architecture redundancy + race condition risk for double-Telegram | Medium: pick one, delete other |
| 3 | BUG-WP1 (weekly_report Telegram fires even after dedup) | Telegram spam on re-runs | Easy: add `if:` gate to step |
| 4 | BUG-NB3 (nightly_brain auto-pushes corrupted weights.json) | Brain corruption risk — explains why weights.json hasn't updated | Medium: validate before commit |
| 5 | X-1 (minimal-install workflows) | intraday_monitor runs 52×/day on yfinance+pandas only — silent failures probable | Easy: install full requirements.txt |
| 6 | BUG-CI2 + CI3 (no coverage, no script tests) | CI is essentially "syntax + 200 tests" — major blind spot | Medium: add pytest-cov + scripts coverage |
| 7 | BUG-CI1 (no failure threshold on tests) | One flaky test poisons CI invisibly | Easy: --strict-markers --maxfail |
| 8 | X-3 (push-retry duplicated 13×) | When you find a push bug, must fix 13 places | Hard: extract shared script |
| 9 | X-5 (`git push || true` in 6 workflows) | Silent push failures | Easy: remove `|| true` |
| 10 | BUG-IM1 (intraday hangs ⇒ 6-hour billing) | Cost + reliability for highest-frequency workflow | Easy: add timeout-minutes |

### What these 15 workflows tell us about the project

- **Production discipline IS uneven.** `news_evidence.yml` is exemplary (input validation, preflight, safety check, timeout). `yearly_recap.yml` has none of those.
- **There's an intentional `news_evidence.yml` template** that should be propagated. Use it as the model.
- **Three workflows have hidden security/safety gaps**: news_engine has Alpaca creds, nightly_brain auto-pushes brain memory without validation, watchdog has actions:write permission.
- **Late-watch-only is implemented TWICE** (in daily-picks.yml AND late_watch_only.yml) — pick one.
- **Cost / billing is unmanaged.** No timeouts on 10 workflows, no pip cache on 13, news_engine fires 32×/day with LLM call each, intraday fires 52×/day. Total bill is much higher than necessary.
- **Single-user fingerprints everywhere.** `anjanneogi13` hardcoded in 5 workflows. Fine for now; remember when scaling.

### Glossary additions

| Term | Plain English |
|---|---|
| `concurrency group` | A label that GitHub uses to ensure only one workflow run per group runs at a time. |
| `cancel-in-progress: true/false` | When a new run starts in the same group: cancel the running one (true) or queue/skip the new one (false). |
| `workflow_dispatch` | Manual trigger button. Lets you run a workflow on demand from the GitHub UI. |
| `runs-on: ubuntu-latest` | The OS+VM image GitHub provides. Free tier: 2-core Linux VM. |
| `permissions: contents: write` | Lets the workflow's `GITHUB_TOKEN` push commits. Without this, push fails. |
| `timeout-minutes` | Max time a step or job can run before GitHub kills it. Default 6 hours per job. |
| `secrets.X` | A value stored in GitHub Settings → Secrets, accessible only to workflows. |
| `matrix testing` | Running the same tests across multiple Python versions, OSes, etc. — catches version-specific bugs. |

---

**End of Batch 2b.**

Cumulative findings across batches 1a + 1b + 2a + 2b:
- 🚨 Show-stoppers: 56
- ⚠️ Data/safety risks: 87
- 🟡 Code smells: 74
- 📝 Doc-only: 6
- ✅ Good code: 74
- **Total: 297 findings across 28 files (~12,000 lines code+yaml)**

Next: Batch 3a — `scripts/` directory part 1 (we'll start with the highest-impact orchestrator scripts and work down).
