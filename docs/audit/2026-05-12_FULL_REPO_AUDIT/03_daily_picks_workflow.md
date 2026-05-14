# Audit Batch 2a — daily-picks.yml (Production Workflow)

**Date:** 2026-05-12
**File:** `.github/workflows/daily-picks.yml` — 527 lines
**Role:** GitHub Actions workflow. Cron-triggered Mon-Fri during US premarket hours. Runs `main.py`, validates artifacts, commits, sends Telegram.

**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

## High-level summary in plain English

What this workflow does, in order:

1. **Trigger:** every weekday at 12:05/12:20/12:35/12:50 UTC and same minutes in 13:00 and 14:00 UTC = **12 attempts per day** (between 08:05 and 10:50 ET roughly)
2. **Concurrency lock:** only one run at a time. Subsequent runs wait or skip.
3. **Checkout:** pulls full git history of `main` branch
4. **Guard step:** decides if this attempt should actually run
   - If market closed → write no-pick artifact, exit
   - If before 08:00 ET → skip
   - If after 09:20 ET → write "missed window" no-pick artifact, set flag for late watch-only path
   - If picks already logged today → skip (dedup)
   - Otherwise → proceed
5. **If missed window:** generate "late watch-only daily ideas" (separate code path) and Telegram them
6. **Commit run-status artifacts** (even on skip)
7. **Set up Python + install dependencies**
8. **Run 3 dry-run validations** (Lane 1 official pick / no-pick / production-readiness audit)
9. **Build per-stock statistics** (top 100 tickers, ~3 minutes)
10. **Run agent** (`python main.py`) — THE ACTUAL PICK GENERATION
11. **On failure:** Telegram an alert
12. **Verify CSV was written** (must have today's picks OR valid no-pick artifact)
13. **Verify official decision artifacts** (matching ticker count)
14. **Write workflow summary**
15. **Upload artifacts** (JSONs + Markdown)
16. **Commit results** with up-to-5 push retries (handles concurrent push conflicts)
17. **Premarket sanity check**
18. **Format picks as Markdown**
19. **Create/update GitHub issue** with picks (emails you)
20. **Send picks to Telegram**
21. **Commit post-send artifacts** (telegram_sent.json, etc.)

**Plain English:** This workflow is your "alarm clock + driver." It wakes up 12 times a morning, decides if it should drive, drives once, then logs everything.

---

## STRUCTURAL FINDINGS

### 🚨 STRUCT-W1: Workflow is 527 lines of YAML — too long, too procedural
- Like `main.py`, this file is a kitchen-sink workflow doing 21 sequential things.
- Why a problem: hard to see the shape. A bug in step 14 might affect step 19 in subtle ways. Reusable patterns (push-retry, status-record, telegram-send) are repeated.
- Fix (medium-term): extract reusable pieces into composite actions or sub-workflows in `.github/workflows/_shared/`.
- **Severity:** 🚨 Maintainability.

### 🚨 STRUCT-W2: Same `record_daily_picks_run_status.py` script called 14+ times
- Lines 47, 60, 67, 75, 87, 94, 106, 134, 146, 148, 167, 290, 294, 296, 318, 320, 333, 338, 344, 357, 361, 470, 472.
- Each call has hardcoded `--event` and `--reason` strings.
- Why a problem: typos create new "events" silently. No central registry of valid event names. Hard to know what events are emitted without grepping the YAML.
- Fix: define event names as constants in the script itself, or a YAML anchor / matrix of named event tuples.
- **Severity:** 🚨 Naming-discipline risk for downstream observability.

### ⚠️ STRUCT-W3: Push-retry-with-stash logic duplicated 3 times
- Lines 199-205 (status push), 402-427 (results push), 503-520 (post-send push)
- Each has slight variations in retry count (3 vs 5), error message, and stash strategy.
- Why a problem: when a bug is fixed in one, the others lag.
- Fix: move to `.github/scripts/git_push_with_retry.sh`, call once.
- **Severity:** ⚠️ Drift risk.

### ⚠️ STRUCT-W4: Three separate `git add -f` lists scattered throughout
- Lines 179-187 (status artifacts list), 393 (results list, truncated in fetch), 494 (post-send list, truncated in fetch).
- Why a problem: when you add a new artifact file, you have to remember WHICH of three lists to add it to. Easy to miss.
- Fix: consolidate into a manifest file (`.github/workflows/_artifact_manifest.txt`).
- **Severity:** ⚠️ Artifact drift risk.

### 🟡 STRUCT-W5: No timeout on the workflow or the `Run agent` step
- Default GitHub Actions timeout is 6 hours per job, 360 minutes per step.
- Your `main.py` typically takes ~5-10 minutes. If it ever hangs (e.g., yfinance call without timeout — see main.py BUG-52), it will burn 6 hours of GitHub Actions minutes.
- Fix: add `timeout-minutes: 30` at the job level, or `timeout-minutes: 20` at the `Run agent` step level.
- **Severity:** 🟡 Cost / billing risk.

### ⚠️ STRUCT-W6: `continue-on-error: true` only used once (line 281)
- Only on stats-build step.
- Other steps (push, telegram) fail-loudly which is correct, but readers might wonder why this one is different.
- Severity: 🟡 Style consistency only.

---

## LINE-BY-LINE FINDINGS

### Lines 1-19: Workflow header + triggers

**🚨 BUG-W1:** Schedule `cron: '5,20,35,50 12-14 * * 1-5'` (line 17) = **12 attempts per workday** (4 minutes per hour × 3 hours × 5 days)
- Plain English: every weekday morning, GitHub triggers this workflow up to 12 times. The guard step decides which one actually runs.
- Why a problem: GitHub charges minutes per trigger even if you exit immediately. 12 attempts × 5 days × 4 weeks = 240 attempts/month. Each "skip" still uses ~30-60 sec of compute (checkout + guard).
- Defensible: needed because GitHub schedules are best-effort. With cron drift up to 15 min, 12 attempts ensures one happens in window.
- Fix consideration: 4 attempts (e.g., 12:05, 12:35, 13:05, 13:35) might be enough, halving the noise. Or use a single triggered workflow that runs longer-but-once.
- **Severity:** ⚠️ Cost; maybe over-engineered.

**⚠️ BUG-W2:** `cancel-in-progress: false` (line 25)
- Plain English: if a second run starts while first is running, second WAITS (doesn't cancel first).
- Why a problem: with 12 cron attempts, conceivably 2 could overlap if first takes >15 min. Both will run sequentially → second one's guard will dedup-skip → wasted compute but safe.
- Could be `cancel-in-progress: true` if first one is "stuck" — but then it loses partial state.
- Severity: 🟡 Defensible, but document the trade-off.

**📝 BUG-W3:** `env: DAILY_FETCH_YF_FULL_INFO: false` (line 4) at top level
- Single env var at workflow level with no comment explaining what it controls.
- Fix: add comment `# When true, fetches yfinance full info for each ticker (slower but more accurate). Disabled in prod for speed.`
- Severity: 📝 Doc.

### Lines 27-39: Job + checkout

**✅ GOOD-W1:** `permissions: contents: write, issues: write` (lines 30-32) — explicit minimal permissions
- Why good: principle of least privilege. Doesn't grant `actions: write` or other dangerous permissions.

**✅ GOOD-W2:** `fetch-depth: 0` and `ref: main` (lines 37-38) with comments
- Why good: explicit about needing full history (for rebase) and always pulling latest main.

### Lines 40-95: Guard step

**✅ GOOD-W3:** Multi-condition guard with explicit no-pick artifact writes (lines 56-79)
- Plain English: market-closed, before-window, missed-window all write formal no-pick artifacts. Audit-friendly.

**🚨 BUG-W4:** Critical bug pattern — `TODAY_ROWS=$(grep -c "^$ET_DATE" data/picks_log.csv 2>/dev/null || true)` (line 83)
- Plain English: counts CSV rows starting with today's ET date. If grep fails, returns empty.
- Why a problem (subtle): if `$ET_DATE` happens to match a substring INSIDE a date column (it won't here, but the pattern is fragile), or if CSV first column changes meaning, count is wrong.
- BIGGER problem: the `2>/dev/null || true` masks errors. If `picks_log.csv` is corrupted, you get TODAY_ROWS=0 → workflow proceeds → may DOUBLE-LOG picks for the day.
- Fix: use a Python helper that validates CSV schema first, returns "today logged?" boolean.
- **Severity:** ⚠️ Dedup defeat risk.

**🟡 BUG-W5:** Same pattern (line 84): `TODAY_ROWS="${TODAY_ROWS:-0}"`
- Plain English: defensive default-0 if variable empty.
- Why borderline-OK: belt-and-suspenders. But masks the underlying bash quirk where `grep -c` returns nothing on empty match.

**🚨 BUG-W6:** Indentation glitch — line 84 has weird indentation (2 spaces vs 6)
- Look at lines 82-85 in the YAML — line 84 (`TODAY_ROWS="${TODAY_ROWS:-0}"`) has different indentation.
- This is bash inside a YAML `run:` block, so YAML doesn't care, but bash treats whitespace consistently.
- Severity: 🟡 Cosmetic but suggests rushed edit.

**🚨 BUG-W7:** Missed-window check is `>` not `>=` (line 72)
- Plain English: `if [ $ET_MINUTES_OF_DAY -gt $OFFICIAL_CUTOFF ]` — greater-than, not greater-or-equal.
- At exactly 09:20 ET, condition is FALSE → proceeds with picks.
- Either intentional (09:20 still allowed) or off-by-one. No comment explains.
- Severity: 🟡 Edge case.

**⚠️ BUG-W8:** No protection against `python -c "from src.market_calendar..."` failing (line 56)
- If the import fails, `$MARKET_OPEN` is empty.
- Then line 57: `if [ "$MARKET_OPEN" != "true" ]` → "" != "true" is true → writes no-pick artifact and skips.
- This is fail-CLOSED (good!) but the user wouldn't know WHY the agent skipped (broken module vs holiday).
- Fix: capture stderr, log it, distinguish "not trading day" from "calendar broken."
- **Severity:** ⚠️ Diagnostic gap.

### Lines 97-115: Late-watch-only dedup guard

**✅ GOOD-W4:** Separate dedup file for late watch-only (line 102)
- Plain English: even if missed window fires multiple times, late-ideas are sent only once.

### Lines 117-150: Late watch-only Python setup + send

**🚨 BUG-W9:** Late-watch-only path installs ONLY 2 deps (line 127): `pip install yfinance==0.2.65 curl_cffi==0.7.4`
- Plain English: the late-ideas script gets ONLY these two libraries. Not full requirements.txt.
- Why a problem: `scripts/generate_late_daily_ideas.py` (18KB) probably needs MORE than these. If it imports `pandas`, `numpy`, `yaml`, `dotenv`, `feedparser`, etc., it crashes. Either:
  - (a) the script is unusually self-contained (unlikely at 18KB), or
  - (b) production has been masking this with fall-through error handling
- Fix: install full requirements.txt to be safe. Cost: ~30 sec extra per missed-window run.
- **Severity:** 🚨 Likely runtime failure.

**🟡 BUG-W10:** Two inline thresholds (line 132): `--max-results 5 --min-score 0.40`
- Plain English: late ideas capped at 5 picks with min score 0.40 (lower than daily-picks 0.55).
- Why a problem: parameters buried in workflow. Should be in `config.yaml` under `late_watch_only:` section.
- Severity: 🟡 Parameter drift.

**⚠️ BUG-W11:** Line 133: `COUNT=$(cat /tmp/late_daily_ideas_count 2>/dev/null || echo 0)` — count read but never used
- The `COUNT` variable is set but never referenced after line 134 (which appears truncated in the fetched file).
- If the recording line 134 actually uses `$COUNT`, it's fine. If not, this is dead code.
- Severity: 🟡 Possible dead code (need full line 134 view).

### Lines 152-205: Commit run-status artifacts (skipped attempt)

**✅ GOOD-W5:** Self-heal persistence marker (lines 165-171)
- Plain English: if status file doesn't have current run_id, append a marker. Ensures every run is auditable even when individual `record_daily_picks_run_status.py` calls failed.

**✅ GOOD-W6:** Use of `shopt -s nullglob` (line 178)
- Plain English: bash setting that makes unmatched globs return empty instead of literal `*`. Prevents `git add data/foo_*.json` from trying to add a literal file named `data/foo_*.json` when no matches.

**⚠️ BUG-W12:** Push retry with `for i in 1 2 3` (line 199) = max 3 attempts, sleep 2/4/6 sec
- Plain English: up to 3 push attempts with linear backoff.
- Why a problem (vs results push at lines 404 = 5 retries): inconsistent retry strategy. If status push fails after 3, it's lost. Results push retries 5×.
- Fix: unify to 5 retries everywhere.
- Severity: ⚠️ Reliability inconsistency.

### Lines 207-217: Python setup + dependencies

**✅ GOOD-W7:** Python 3.12 pinned (line 211).

**🟡 BUG-W13:** `pip install -r requirements.txt pytest` (line 217)
- Plain English: installs everything in requirements.txt plus pytest.
- Why interesting: pytest isn't in `requirements.txt` (you have it pinned at 8.3.3 there, line 15 — actually IT IS there). So `pytest` here is REDUNDANT with `requirements.txt`.
- Severity: 🟡 Redundant install.

**🟡 BUG-W14:** No pip cache configured
- Plain English: every workflow run re-downloads all packages (could be 200MB+).
- Fix: add `cache: 'pip'` to `setup-python@v5` step.
- Saves ~30 sec/run × 240 runs/month.
- Severity: 🟡 Cost optimization.

### Lines 219-272: Lane 1 dry-run validations + production-readiness audit

**✅ GOOD-W8:** Three pre-flight validations before main.py runs
- Lane 1 official pick dry-run, no-pick dry-run, production-readiness audit.
- Why good: catches obvious breaks before committing to real picks.

**⚠️ BUG-W15:** Each dry-run hardcodes `/tmp/lane1-...` paths (lines 223, 237, 262)
- Plain English: temporary directory paths inline three times.
- Why a problem: if path scheme changes, must update in multiple places.
- Severity: 🟡 Repetition.

**⚠️ BUG-W16:** Dry-run failures crash the workflow (no `continue-on-error`)
- Plain English: if Lane 1 dry-run fails, entire workflow fails BEFORE main.py runs.
- Defensible: dry-run failure means production would also fail. Better to abort early.
- Concern: if dry-run is BROKEN (not the production path), it blocks real picks.
- Fix: add a `continue-on-error: true` with loud warning, OR ensure dry-run scripts have very limited dependency surface.
- Severity: 🟡 Acceptable trade-off.

**🟡 BUG-W17:** Output of audit cat'd into `$GITHUB_STEP_SUMMARY` (line 263)
- If audit markdown is huge (>1MB), GitHub truncates the summary.
- Severity: 🟡 Defensive truncation needed.

### Lines 275-281: Build per-stock statistics

**🟡 BUG-W18:** `continue-on-error: true` (line 281) + inline `|| echo "..."` (line 279)
- Plain English: stats build can fail silently both ways.
- Comment claims "non-fatal" — fine, but combined `||` and `continue-on-error` is double-defensive.
- Severity: 🟡 Belt-and-suspenders.

### Lines 283-298: Run agent

**🚨 BUG-W19 (CRITICAL):** No timeout on `python main.py` (line 291)
- Plain English: if main.py hangs (e.g., yfinance call without timeout — main.py BUG-52), this step runs until GitHub's 6-hour default kills it.
- Fix: add `timeout-minutes: 25` to this step.
- **Severity:** 🚨 Cost + reliability risk.

**✅ GOOD-W9:** Explicit `${PIPESTATUS[0]}` (line 292) capture preserves main.py's exit code through the `tee` pipe
- Plain English: `tee` always succeeds. Without `PIPESTATUS`, you'd lose main.py's exit code.

**⚠️ BUG-W20:** No retry on agent run
- Plain English: if main.py fails once (transient yfinance error), workflow gives up.
- Defensible: main.py itself has internal retries. But for transient failures, a single workflow-level retry might recover the day.
- Severity: ⚠️ Lost-run risk for transient failures.

### Lines 300-321: Failure Telegram alert

**✅ GOOD-W10:** Failure telegram with both personal + group chat fallback (line 310)

**⚠️ BUG-W21:** `MSG="..."` (line 308) is truncated in our fetch — but contains `%0A` for newlines (URL-encoded)
- Telegram's HTTP API accepts text directly; `%0A` only works if the API URL-decodes. With `-d "text=$MSG"` curl form-encoding, this might double-encode.
- Severity: 🟡 May cause garbled alerts.

**⚠️ BUG-W22:** SENT detection by grep `'"ok":true'` in response (line 315)
- Plain English: claims success if Telegram API returned `"ok":true`.
- Why fragile: malformed JSON response could match by accident.
- Fix: parse JSON properly.
- Severity: 🟡 Edge case.

### Lines 323-345: Verify CSV was written

**🚨 BUG-W23:** Same `grep -c "^$ET_DATE"` pattern (lines 327, 351, 485) repeated 3 times
- Why a problem: same fragility as BUG-W4. Three places to break independently.
- Fix: extract into helper script `scripts/check_picks_logged_today.sh "$ET_DATE"`.
- Severity: ⚠️ Repetition.

**✅ GOOD-W11:** Falls back to `validate_daily_no_pick.py` if zero picks logged (line 331)
- Plain English: zero picks with valid no-pick artifact = success. Zero picks WITHOUT no-pick artifact = critical failure.

### Lines 347-362: Verify official decision artifacts

**✅ GOOD-W12:** `validate_official_pick_artifacts.py --expected-count "$TODAY_ROWS"` (line 356)
- Plain English: explicitly verifies pick artifact count matches CSV row count. Catches the case where main.py wrote partial artifacts.

### Lines 364-369: Workflow summary

**✅ GOOD-W13:** Always-runs (`if: always()`) summary writer

### Lines 371-386: Upload artifacts

**🟡 BUG-W24:** Artifact name has `${{ github.run_id }}` (line 252, 269, 375) — every run creates new artifact bundle
- Plain English: artifacts named `official-decision-artifacts-12345`, `...-12346`, etc.
- Why a problem: GitHub keeps these for 90 days by default. With 240 runs/month × 90 days ≈ 720 artifact bundles. Storage costs + clutter.
- Fix: set `retention-days: 30` on each `upload-artifact` step.
- Severity: 🟡 Cost/clutter.

### Lines 388-427: Commit results (with retry safety)

**🚨 BUG-W25:** `git add -f data/learning/ data/exec_report_*.json data/premarket_check.json data/picks_log.csv data/telegram_sent.json data/learning_journal.jsonl data/last_regime.json data/hard_blocks...` (line 393, truncated in fetch)
- The truncated line is the artifact list — likely 10-20 files.
- Why a problem (a) hard to read (b) easy to miss adding new artifacts (c) `-f` force-add bypasses .gitignore (good for tracked data, dangerous for accidental).
- Fix: extract list to a manifest.
- Severity: ⚠️ Artifact drift + readability.

**✅ GOOD-W14:** Push retry with auto-stash (lines 403-422)
- Plain English: if `git push` fails (because someone else pushed first), pull-rebase, retry. If unstaged changes in the way (concurrent step writing), stash them and retry.
- Why good: addresses the real "Apr 30 lost CSV writes" bug mentioned in concurrency comment line 22.

**⚠️ BUG-W26:** `git stash pop` failure silenced with `|| true` (line 414, 419)
- Plain English: if stash-pop has a conflict, ignored.
- Why a problem: any unstaged changes from the stash are LOST.
- Severity: ⚠️ Silent data loss possible.

### Lines 429-435: Premarket sanity check + format picks

**🟡 BUG-W27:** No comment explaining what `premarket_check.py` does at this stage
- Already passed sanity gates inside main.py. Why again?
- Severity: 📝 Doc.

### Lines 437-458: Create issue with picks (emails you)

**✅ GOOD-W15:** Uses an `upsertIssue` helper (line 443) — single source of truth
- Plain English: external script handles issue create-or-update.

**⚠️ BUG-W28:** `assignees: ['anjanneogi13']` (line 457) — your username hardcoded
- Plain English: every daily picks issue is assigned to you (correct for now).
- Why a problem: when the project gets a co-founder or moves to an org, you have to remember to change this. And if you ever change your username, breaks.
- Fix: read from `.github/workflows/_config.yml` or repo secret.
- Severity: 🟡 Single-user assumption.

### Lines 460-474: Send picks to Telegram

**✅ GOOD-W16:** Status-record on both success and failure paths (lines 470, 472).

### Lines 476-526: Commit post-send artifacts

**✅ GOOD-W17:** Conditional `picks_log.csv` add (lines 488-492)
- Plain English: only stage picks_log.csv if today has rows. Avoids re-committing header churn after a zero-pick run.
- Why good: addresses real "M-B fix" mentioned in step name.

**⚠️ BUG-W29:** Same artifact list pattern as BUG-W25 (line 494)
- Truncated in fetch. Same maintainability issue.

**⚠️ BUG-W30:** Same push-retry pattern as lines 403-422 (lines 503-520) — third copy.
- Same as STRUCT-W3.

---

## Summary of Batch 2a (`daily-picks.yml`)

### By severity
| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 8 |
| ⚠️ Data/safety risk | 13 |
| 🟡 Code smell | 13 |
| 📝 Doc-only | 2 |
| ✅ Good code | 17 |
| **Total** | **53 findings** |

### Top 6 things to fix in `daily-picks.yml` (in order)

| # | Bug | Why first | Fix difficulty |
|---|---|---|---|
| 1 | BUG-W19 (no timeout on main.py) | One yfinance hang = 6 hours of wasted compute. Trivial fix. | Easy: add `timeout-minutes: 25` |
| 2 | BUG-W9 (late-watch-only installs only 2 deps) | Likely runtime failure today on missed-window paths | Easy: install full requirements.txt |
| 3 | BUG-W4 / W23 (fragile `grep -c` for dedup) | If picks_log.csv ever corrupts, dedup defeated → double-log risk | Medium: extract to validated helper script |
| 4 | STRUCT-W3 / BUG-W30 (push retry duplicated 3×) | Three places to fix when one bug found | Medium: extract `git_push_with_retry.sh` |
| 5 | BUG-W14 (no pip cache) | Free 30-sec saving × 240 runs = 2 hours/month free | Easy: add `cache: 'pip'` to setup-python |
| 6 | STRUCT-W2 (14+ event-name strings ungoverned) | Observability quality drifts as event names typo | Medium: add event constants script |

### What this workflow tells us about the project

- **Production discipline is GOOD where it matters.** The agent run is wrapped in proper retries, the no-pick contract holds end-to-end (every skip writes formal artifact), and there's a self-heal persistence marker.
- **Three duplicate push-retry blocks** suggest organic growth — fix-once-fix-everywhere now.
- **The 12-attempt cron schedule** is defensible (GitHub schedule is best-effort) but should be documented.
- **The late-watch-only path is a separate code-tree** that may be running on insufficient dependencies in production — high-confidence runtime failure waiting to happen.
- **Hardcoded username** (anjanneogi13) and hardcoded paths reflect single-user origin.
- **The dry-run validation gates BEFORE main.py runs** are the correct way to fail fast — keep this pattern.

### Glossary additions

| Term | Plain English |
|---|---|
| Cron | A scheduling syntax `minute hour day month weekday`. `5,20,35,50 12-14 * * 1-5` = "minutes 5/20/35/50 of hours 12-14 UTC, every day, Mon-Fri". |
| Concurrency group | GitHub Actions feature: only one run per group at a time. Used here to prevent overlapping daily-picks runs. |
| GITHUB_STEP_SUMMARY | A markdown file each step can append to. Shows up as a summary panel on the workflow run page. |
| `if: always()` | Run this step even if a previous step failed. Used here for cleanup + artifact upload. |
| `continue-on-error: true` | If this step fails, don't fail the whole workflow. Skip and move on. |
| Stash (git) | Temporarily save uncommitted changes so you can do something else (like pull). `git stash pop` restores them. |
| Push-retry-with-rebase | A pattern: try to push; if rejected (someone else pushed first), pull their changes via rebase, then retry your push. |
| Dry-run | A simulated execution that validates everything works WITHOUT producing real output (no Telegram, no artifacts). |

---

**End of Batch 2a.**

Cumulative findings across batches 1a + 1b + 2a:
- 🚨 Show-stoppers: 34
- ⚠️ Data/safety risks: 49
- 🟡 Code smells: 43
- 📝 Doc-only: 6
- ✅ Good code: 39
- **Total: 171 findings across 13 files (~6,200 lines code+yaml)**

Next: Batch 2b — the other 15 GitHub workflows (some small, some medium).
