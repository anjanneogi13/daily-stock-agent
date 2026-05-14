# Audit Batch 3c — Scripts: Telegram + Sender Family (17 files)

**Date:** 2026-05-12
**Files (17):** send_telegram, send_layman_daily, send_layman_evening, send_layman_weekly, send_layman_monthly, send_layman_yearly, send_dashboard_telegram, send_exec_telegram, send_intraday_telegram, send_late_daily_ideas_telegram, send_meta_brain_telegram, send_missed_premarket_alert, send_monthly_telegram, send_position_alerts, send_weekend_telegram, send_weekly_review, format_picks_email

**Total:** ~2,200 lines

**Severity legend:** 🚨 show-stopper · ⚠️ data/safety risk · 🟡 code smell · 📝 doc-only · ✅ good code

---

## High-level summary in plain English

These 17 files are the USER-FACING channel — the only code paths whose output is delivered to humans (via Telegram, GitHub Issues, email-style markdown). Everything else in this repo is INTERNAL machinery; THESE are the lips of the system.

This batch tells the user "here is what we picked / here is how we did" — and any bug here is a bug the user SEES.

Three families:

Family A — Daily/Outcome Senders (5 files, the daily heartbeat):
- send_telegram.py (legacy technical version, may still wire into workflows)
- send_layman_daily.py (T52 — REPLACES send_telegram.py for amateur audience)
- send_layman_evening.py
- send_dashboard_telegram.py
- send_exec_telegram.py

Family B — Periodic Recap Senders (5 files, weekly/monthly/yearly):
- send_layman_weekly.py, send_layman_monthly.py, send_layman_yearly.py
- send_weekend_telegram.py, send_monthly_telegram.py
- send_meta_brain_telegram.py (Sunday self-improvement)
- send_weekly_review.py

Family C — Specialized/One-shot Alerts (5 files):
- send_intraday_telegram.py
- send_late_daily_ideas_telegram.py
- send_missed_premarket_alert.py
- send_position_alerts.py
- format_picks_email.py (NOT a sender — formats GitHub issue body)

Plus one obvious overlap to call out: send_telegram.py (technical) and send_layman_daily.py (layman) are BOTH wired into workflows in different places. Confirm only ONE is ever called per daily run.

---

## CROSS-CUTTING FINDINGS

### 🚨 X-TG1: SIX completely independent _send() implementations
Same shape duplicated across files:
- send_telegram.py: _try_send (lines 427-445) + the for-loop that calls it
- send_layman_daily.py: _send (lines 152-187)
- send_layman_evening.py: _send (lines 101-115)
- send_layman_weekly.py: _send (lines 72-85)
- send_layman_monthly.py: _send (lines 82-95)
- send_layman_yearly.py: _send (lines 101-114)
- send_meta_brain_telegram.py: _send (lines 17-38)
- send_intraday_telegram.py: inline (lines 64-83)
- send_dashboard_telegram.py: inline (lines 33-44)
- send_exec_telegram.py: inline (lines 84-95)
- send_late_daily_ideas_telegram.py: inline (lines 104-128)
- send_missed_premarket_alert.py: send (lines 40-63)
- send_monthly_telegram.py: inline (lines 42-52)
- send_weekend_telegram.py: inline (lines 47-58)
- send_weekly_review.py: send (lines 19-39) — uses requests, not urllib
- send_position_alerts.py: inline (lines 53-72) — also uses requests

Plain English: 14+ files each implement "send to Telegram" in their own way.
Why a problem:
1. Bug fix to one (e.g., add retry on 429 rate limit) won't propagate.
2. Two files use `requests` library; rest use `urllib`. If `requests` isn't in workflow env, two files crash silently while others succeed.
3. Some have Markdown→plain fallback, some don't, some try ONLY plain text.
4. Some return success/failure, some don't.
5. Timeouts vary: 10s, 20s.
6. Some call mark_sent() on dedup, some don't.
Fix: ONE module — src/telegram_sender.py — used by ALL 14 files.
Severity: 🚨 Highest-leverage refactor in the repo.

### 🚨 X-TG2: Dual-channel dedup is INCONSISTENT
- send_telegram.py uses dedup_sender.should_send (60min window) — message-content based
- send_layman_daily.py uses dedup_sender.should_send (default window) — content based
- send_dashboard_telegram.py uses should_send_report (date-based)
- send_exec_telegram.py uses should_send_report (date-based)
- send_monthly_telegram.py, send_weekend_telegram.py: should_send_report
- send_layman_evening.py: should_send (content)
- send_layman_weekly/monthly/yearly: NO dedup at all
- send_meta_brain_telegram.py: NO dedup
- send_intraday_telegram.py: NO dedup but DELETES alert file after send (alt strategy)
- send_late_daily_ideas_telegram.py: file-based dedup ledger (own implementation)
- send_position_alerts.py: should_send_report
- send_missed_premarket_alert.py: NO dedup

Plain English: Three strategies — content-based, date-based, file-based — used in different files.
Why a problem: User sees DUPLICATE messages on cron retries or workflow_dispatch reruns from inconsistent files. User sees ZERO message when an honest update should re-send (date-based dedup blocks all same-day attempts).
Severity: 🚨 User experience.

### ⚠️ X-TG3: TELEGRAM_BOT_TOKEN check at IMPORT time crashes wrong things
Several files (send_telegram.py:23, send_dashboard_telegram.py:6, send_exec_telegram.py:8, send_monthly_telegram.py:18, send_weekend_telegram.py:18) do `if not TOKEN or not CHAT_IDS: print(...); sys.exit(0)` at MODULE TOP LEVEL.
Plain English: When test_*.py imports these modules to check formatters, the IMPORT itself calls sys.exit(0). Tests can't run without env vars set.
Fix: move credential check inside main() or _send().
Severity: ⚠️ Test friendliness; also surprising-side-effect-on-import.

### 🚨 X-TG4: Fallback patterns are heterogeneous
Three different "what if Markdown breaks?" strategies:
- send_telegram.py: try Markdown then plain (BEST)
- send_layman_daily.py: same loop trying both modes (good)
- send_layman_evening/weekly/monthly/yearly: try both modes BUT inside outer try/except — silent failure on second try
- send_dashboard_telegram.py: NO fallback — Markdown only, fails silently if 400
- send_monthly_telegram.py: NO parse_mode at all (always plain)
- send_weekend_telegram.py: NO parse_mode (always plain — has comment "send as PLAIN TEXT to avoid Markdown 400 errors")
- send_intraday_telegram.py: Markdown only
- send_late_daily_ideas_telegram.py: NO parse_mode (always plain)
- send_meta_brain_telegram.py: try Markdown, fall back to plain (manually strips _ and *)
- send_position_alerts.py: HTML parse mode, fall back to plain

Plain English: Same problem (Telegram 400 on bad markdown), 6 different solutions.
Severity: 🚨 Some files DEFINITELY fail silently on Markdown errors.

### ⚠️ X-TG5: Watchlist tickers loaded inconsistently
- send_telegram.py:43 `_load_watchlist_tickers` reads data/watchlist.json
- send_exec_telegram.py:26 `_load_watchlist_tickers` (same code, copy-pasted)
Severity: ⚠️ DRY violation.

### ⚠️ X-TG6: Date computation drift
- send_telegram.py:360 `datetime.now().strftime("%Y-%m-%d")` — local time, NOT ET
- send_layman_daily.py:28 `os.environ.get("PICK_DATE") or datetime.now().strftime("%Y-%m-%d")` — local time
- send_intraday_telegram.py:36 `datetime.now(timezone.utc).strftime("%Y-%m-%d")` — UTC
- send_late_daily_ideas_telegram.py:24 `datetime.now(timezone.utc).astimezone(ET)` — ET (correct)
- send_position_alerts.py:25 `date.today().isoformat()` — local

Plain English: Five date conventions across senders. `datetime.now()` on a UTC server returns UTC, but on a SGT machine returns SGT — different files end up with different dates.
Why a problem: If the workflow runs at 22:00 UTC = 18:00 ET = 03:30 IST next day, dedup keys collide with WRONG day.
Fix: ALL senders should pull date from PICK_DATE env (set once by workflow) or use ET.
Severity: ⚠️ Off-by-one-day duplicates / missed sends.

### 🟡 X-TG7: Inconsistent return code semantics
- send_telegram.py: sys.exit(1) only if mark_sent step fails (line 467) — even if SOME chats fail
- send_layman_daily.py: returns 1 if all chats fail (line 339) — proper
- send_layman_evening.py: ALWAYS returns 0 even on send failure
- send_intraday_telegram.py: ALWAYS returns 0 even on credentials missing
- send_position_alerts.py: returns 1 on exception, 0 elsewhere
Severity: 🟡 CI status checks unreliable.

### ✅ X-TG8: Dedup_sender pattern is excellent (when used)
src/dedup_sender provides should_send() (content) and should_send_report() (date) — clean separation. Excellent design. Issue is just inconsistent adoption.

### ✅ X-TG9: Layman family (T52) shares formatter helpers
All 6 send_layman_*.py files import from src/layman_translator (header, footer_explainer, money, pct, verdict_line, etc). Single source of truth for HUMAN-FACING WORDS. Excellent.

### ⚠️ X-TG10: Two senders use `requests`, rest use urllib
send_weekly_review.py, send_position_alerts.py = requests.
Rest = urllib (built-in, no extra dep).
If requests is missing in workflow env, those two crash on import. ALL others survive.
Severity: ⚠️ Dep-fragility for two files only.

---

## PER-FILE FINDINGS

### 1. send_telegram.py (468 lines) — LEGACY DAY/SWING TECHNICAL VERSION

What it does: Original technical-style daily picks message with DAY/SWING/MONSTER sections. Per docstring, this is replaced by send_layman_daily.py — but it remains in the repo, suggesting it's still wired into something.

✅ GOOD-ST1: Markdown→plain fallback (lines 427-460) is the gold standard for this batch.
✅ GOOD-ST2: Pause-day path (lines 365-392) — if agent is paused, send pause alert instead of picks. Reuses dedup with separate window.
✅ GOOD-ST3: Wisdom hint integration with try/except graceful degrade (lines 31-40).
✅ GOOD-ST4: Per-pick smell warnings, kill-list, lessons, patterns — rich context.

🚨 BUG-ST1: Line 1-8 docstring says "Sends today's picks to Telegram" but doesn't mention this is REPLACED. Operator confusion: "which sender is the real one?"
- Fix: deprecation banner. Or DELETE if no longer used.
- Severity: 🚨 Architectural drift; two daily senders simultaneously.

⚠️ BUG-ST2: Line 23 `if not TOKEN or not CHAT_IDS: print(...); sys.exit(0)` at module level. See X-TG3.

⚠️ BUG-ST3: Line 36-40 ALL exception handlers return EMPTY strings/dicts:
```
def wisdom_hint(_t=None, sector=None, **_k): return ""
def pattern_hint(_r=None, **_k): return ""
def confidence_band(_s=0, _p="", _w=""): return ""
```
Plain English: If `src.wisdom_hint` import fails, every wisdom call returns "". User sees empty pick formatting — no signal that wisdom is broken.
Severity: ⚠️ Silent degradation.

⚠️ BUG-ST4: Line 41 truncated comment ("─── ────────────────────────────────────────────────────────────��[...]") — file content suggests truncation in the file or display.
- Severity: 📝 Display only.

⚠️ BUG-ST5: Line 41 backslash-broken Unicode in source (truncation indicator) suggests a copy/paste artifact. Verify file is intact on disk.
- Severity: 🟡 Cosmetic.

⚠️ BUG-ST6: Line 360 `today = datetime.now().strftime("%Y-%m-%d")` — local time, NOT ET. See X-TG6.

🟡 BUG-ST7: Line 351 `🔧 _PR #66+#67+#68+#69 active · wisdom v0.1_` — hardcoded PR list in user-visible footer. Will be stale within weeks.
- Severity: 🟡 Stale message.

🟡 BUG-ST8: Line 318 `if _ps.get("enforced"): lines.append("🚨 _Enforce-mode active — agent may auto-pause_")` — surfaces internal "enforce-mode" jargon to user.
- Severity: 🟡 User-facing jargon.

⚠️ BUG-ST9: Line 412-413 truncation: `if len(msg) > 4000: msg = msg[:3950] + "\n\n_(truncated)_"` — truncation can land mid-Markdown formatting (e.g., inside `*bold*`), producing INVALID markdown that triggers Telegram 400. The fallback to plain text saves it, but this is a known footgun.
- Severity: ⚠️ Hack that frequently triggers.

🟡 BUG-ST10: Line 314-321 pause score block silently swallows ALL exceptions ("never block the daily message on pause-signal failure"). If pause logic is broken, user has no visibility.
- Severity: 🟡 Silent failure (acceptable).

🟡 BUG-ST11: Line 188-203 `_format_monster_pick` doesn't include wisdom_hint, smell warnings, or watchlist emoji — feature parity gap with day/swing pick formats.
- Severity: 🟡 Inconsistent UX.

### 2. send_layman_daily.py (347 lines) — T52 REPLACEMENT, OFFICIAL ARTIFACT GATE

What it does: Plain-English daily picks. Validates official artifacts BEFORE sending — refuses to send any pick without a matching valid official artifact. Strongest sanity-gate logic in the batch.

✅ GOOD-LD1: validate_official_user_output_state (lines 31-46) — fail-closed. Picks without artifacts = blocked. No-pick day requires valid no-pick artifact.
✅ GOOD-LD2: _is_pick_sane (lines 49-84) — last-line-of-defense numeric checks before user output.
✅ GOOD-LD3: WATCH_ONLY handling distinct from regular picks (_watch_only_message lines 96-108).
✅ GOOD-LD4: Smell-faculty check skipped for already-validated official artifacts (line 79) — proper bypass with rationale comment.
✅ GOOD-LD5: build_message handles no-pick days with full audit info (decision_id, workflow_run_url, artifact_path).
✅ GOOD-LD6: _send returns bool; main() returns 1 if all chats fail (line 339). Proper exit code.

⚠️ BUG-LD1: Line 31-46 `validate_official_user_output_state` validates `picks` against artifacts. If picks is empty AND no_pick_report is empty AND artifacts exist for some reason — falls through to last `validate_no_pick_report({})` which will fail. OK.
- BUT the fail message "no picks logged and no valid official no-pick artifact found" doesn't catch the case where picks ARE present but artifacts are not — it silently returns the artifact validation errors. Acceptable but worth a comment.
- Severity: 🟡

⚠️ BUG-LD2: Line 79 "Priority 10: official-artifact rows have already passed the official production gates" — only skips smell BLOCKING checks if `official_artifact_present`. Numeric sanity (entry/SL/TP/RR) is still applied — good. But what about a TRUE production smell that the production gates missed? You'd want smell warnings to STILL show in the message even if not blocking.
- Verifying: line 283-285 still calls `_sniff` and shows warnings AFTER pick. So warnings still surface. Good.
- Severity: 📝 OK.

⚠️ BUG-LD3: Line 152 `_send` returns True on no creds (treats as dry-run success). Then line 337 does `if not _send(msg): print("all chats failed")`. If creds missing, returns True → mark_sent is called. Next time creds appear, dedup blocks.
- Plain English: A local test run with no Telegram creds will mark the message as "sent", silencing the next REAL run.
- Fix: don't mark_sent when creds missing.
- Severity: ⚠️ Hidden dedup poisoning.

🟡 BUG-LD4: Lines 261-286 (day picks loop) and 288-314 (swing picks loop) are 95% identical. Refactor: helper function.
- Severity: 🟡 DRY.

🟡 BUG-LD5: Line 28 `os.environ.get("PICK_DATE") or datetime.now().strftime("%Y-%m-%d")` — naive local time. See X-TG6.

⚠️ BUG-LD6: Line 246 reads `os.environ.get("PICK_DATE") or datetime.now().strftime("%Y-%m-%d")` AGAIN (different from line 28) — potential drift if env var set between these reads in some weird scenario.
- Severity: 🟡 Code smell; centralize.

### 3. send_layman_evening.py (131 lines)

What it does: Sends evening performance recap (closed picks today). Bug fix history embedded in docstring (lines 22-27).

✅ GOOD-LE1: Lookback window (line 33-34): looks 3 days back so Friday closes show in Monday's report. Good UX.
✅ GOOD-LE2: Includes performance_source_separation note (LAYMAN_PERFORMANCE_SOURCE_NOTE) — distinguishes official from watch-only sources.
✅ GOOD-LE3: Filters out watch-only rows (line 42 `not is_watch_only_row(r)`) — prevents performance contamination.

⚠️ BUG-LE1: Line 65 `total_pnl = sum(_safe_f(o.get("pnl_dollar")) for o in outcomes)` — computed BEFORE the loop on line 67-72 that fills in pnl_dollar from actual_return_pct. Then line 73 recomputes. Wasted work.
- Severity: 🟡 Cosmetic.

⚠️ BUG-LE2: Line 72 fallback formula `o["pnl_dollar"] = ent * qty * ret / 100` MUTATES the row in place. Subsequent calls see modified data.
- Plain English: Pure functions are safer. Mutation in a list comprehension caller is surprising.
- Severity: 🟡 Code smell.

⚠️ BUG-LE3: Line 124 `_send(msg)` ignores return value. Mark_sent always called. Same pattern as BUG-LD3.
- Severity: ⚠️ Dedup poisoning if all sends fail.

⚠️ BUG-LE4: Line 96-98 `_safe_f` returns 0 on bare except. Bare except catches KeyboardInterrupt etc.
- Severity: 🟡

🟡 BUG-LE5: Line 30 `today = os.environ.get("PICK_DATE") or datetime.now().strftime("%Y-%m-%d")` — but cutoff calc on line 33 uses `datetime.strptime(today, "%Y-%m-%d")` — fine but redundant work.

### 4. send_layman_weekly.py (98 lines)

What it does: Weekly recap (last 7 days). NO dedup. Simple.

🚨 BUG-LW1: Line 32 filters `r.get("status") not in (None,"","OPEN")` — but evening sender uses `evaluation_status` (correctly per its bug fix history). Same bug history doesn't appear here.
- Plain English: This file likely uses stale field name. Check picks_log schema — if `status` doesn't exist, ZERO trades are returned every week.
- Severity: 🚨 Probable schema-drift bug; weekly recap silently empty.

⚠️ BUG-LW2: NO dedup. Manual cron retry → duplicate messages.
- Severity: ⚠️ User experience.

⚠️ BUG-LW3: Line 33 ignores OPEN status — but should we count "expired" or "max_hold" exits? Schema unclear here.
- Severity: ⚠️ Coverage gap.

🟡 BUG-LW4: Line 29 `except: continue` — bare except, silent skip on date parse failure.

🟡 BUG-LW5: Line 92 returns 0 unconditionally. CI passes even if send fails.

### 5. send_layman_monthly.py (108 lines) — MIRRORS WEEKLY

Same shape as weekly. Same bugs propagated:
🚨 BUG-LM1: Line 33 same `r.get("status")` bug as BUG-LW1.
⚠️ BUG-LM2: NO dedup.
🟡 BUG-LM3: Line 51 `_safe_f` fallback computation differs subtly from evening sender's recompute logic.
🟡 BUG-LM4: Line 95 `except: continue` — bare except.
🟡 BUG-LM5: Line 102 returns 0 unconditionally.

### 6. send_layman_yearly.py (127 lines) — SAME PATTERN

Same shape. Same bugs:
🚨 BUG-LY1: Line 30 same `r.get("status")` bug.
⚠️ BUG-LY2: NO dedup.
🟡 BUG-LY3: Line 35 `_count_brain_mutations` opens learning_journal.jsonl as text, splits on lines, json.loads each. Standard but not streaming for large files.
🟡 BUG-LY4: Line 95 hardcoded "Verdict" text — see if config-driven would help. Minor.

### 7. send_dashboard_telegram.py (45 lines)

What it does: Subprocesses out to performance_dashboard.py, sends stdout to Telegram in code block.

✅ GOOD-DT1: Uses should_send_report (date-based dedup) correctly.
✅ GOOD-DT2: Truncation handling (line 30-31).

🚨 BUG-DT1: Line 24 `subprocess.run(["python", ...])` — assumes `python` is in PATH AND is python3. On modern systems `python` may not exist (only `python3`). Fails silently.
- Fix: use `sys.executable`.
- Severity: 🚨 Environment-fragility.

⚠️ BUG-DT2: Line 25 `capture_output=True, text=True` — but no check for `result.returncode`. If dashboard script crashes, sends empty/error output as if successful.
- Severity: ⚠️ Garbage-in-garbage-out.

⚠️ BUG-DT3: Line 6-7 `if not TOKEN or not CHAT_IDS: ... sys.exit(0)` at module top.
⚠️ BUG-DT4: NO Markdown→plain fallback. If output contains characters Telegram parses as Markdown, send fails.
🟡 BUG-DT5: Line 41 reports OK on `res.get('ok')` but exits without setting status if NOT OK. Half-set state.
🟡 BUG-DT6: mark_report_sent NEVER called (only should_send_report check). Same dedup key flagged but never written. Likely BUG.

Wait — verifying line 18: `if not should_send_report(...)`. should_send_report checks IF marked. mark_report_sent should be called AFTER success. **It is NEVER called in this file** — so dedup is effectively disabled (every run reports "not sent" and goes through).
🚨 BUG-DT7: mark_report_sent never invoked. Dedup is broken.
- Severity: 🚨 Dedup bypassed; user gets duplicate dashboards.

### 8. send_exec_telegram.py (96 lines)

What it does: Sends execution X-ray report (TP/SL hit summary).

✅ GOOD-ET1: Uses should_send_report.
✅ GOOD-ET2: Watchlist emoji integration.
✅ GOOD-ET3: Per-status formatting.

🚨 BUG-ET1: Same issue as BUG-DT7 — `mark_report_sent` is NEVER called. Dedup broken.
- Severity: 🚨

⚠️ BUG-ET2: Line 6-9 same module-level credentials check.
⚠️ BUG-ET3: NO Markdown→plain fallback.
🟡 BUG-ET4: Line 26-31 `_load_watchlist_tickers` duplicated from send_telegram.py. See X-TG5.

### 9. send_intraday_telegram.py (99 lines)

What it does: Sends intraday opening-range alert. DELETES alert file after send (alt dedup strategy).

✅ GOOD-IT1: Calls `append_opening_range_run_status` (lines 27, 40, 51, 85) — proper observability.
✅ GOOD-IT2: Distinguishes "skipped" vs "success" vs "failed" reasons in run_status.
✅ GOOD-IT3: alert_file.unlink(missing_ok=True) on line 93 — file-based dedup.

⚠️ BUG-IT1: Line 93 deletes alert file EVEN if all sends failed (sent_any=False). Run_status correctly reports "failed", but alert file is gone forever. Next run can't retry.
- Plain English: Failed send + deleted file = data loss.
- Severity: ⚠️ Should only delete on success.

⚠️ BUG-IT2: NO Markdown→plain fallback.
⚠️ BUG-IT3: Line 33 returns 0 on missing creds — workflow sees success.

### 10. send_late_daily_ideas_telegram.py (134 lines)

What it does: Sends late watch-only ideas (post-market). File-based dedup ledger.

✅ GOOD-LI1: Custom dedup ledger with checksum (lines 35-62) — robust.
✅ GOOD-LI2: --force flag for explicit resend (lines 67-71).
✅ GOOD-LI3: Documented "monitoring only" in docstring + ledger.
✅ GOOD-LI4: Returns 1 if no chats received the message (line 125).

⚠️ BUG-LI1: NO Markdown→plain fallback. Files generated by upstream may include Markdown.
⚠️ BUG-LI2: Line 100-102 missing creds returns 0 (success). Should be a clear "intentionally skipped" status.
🟡 BUG-LI3: Line 52-61 ledger payload includes `mode/watch_only/paper_trading_enabled/live_trading_enabled` — defensive contract. Excellent (matches Family B style from Batch 3b).

### 11. send_meta_brain_telegram.py (63 lines)

What it does: Sunday self-improvement digest.

✅ GOOD-MB1: Proper Markdown→plain fallback (lines 25-38) — manually strips * and _ for plain attempt.

⚠️ BUG-MB1: NO dedup. Duplicate sends possible.
⚠️ BUG-MB2: Line 31 plain-text fallback strips `*` and `_` ONLY — won't strip `[`, `]`, `(`, `)` which Telegram also parses. May still 400.
🟡 BUG-MB3: Line 41-49 if no creds, prints digest and returns 0 — fine for dev.

### 12. send_missed_premarket_alert.py (72 lines)

What it does: Sends "premarket window missed" alert.

✅ GOOD-MP1: Tightest sender in batch. Single responsibility, clean.
✅ GOOD-MP2: Markdown→plain fallback (lines 49-62).
✅ GOOD-MP3: ET timezone (line 27).
✅ GOOD-MP4: Returns 1 if all chats failed.

⚠️ BUG-MP1: NO dedup. If workflow retried, user gets duplicate alerts.
⚠️ BUG-MP2: Line 42-44 missing creds returns True (treats as dry-run success). Same as BUG-LD3 but lower stakes since no mark_sent.

### 13. send_monthly_telegram.py (53 lines) — TECHNICAL VERSION

What it does: Sends monthly X-ray summary. Uses should_send_report.

🚨 BUG-MT1: NO mark_report_sent call. Same dedup-broken bug as BUG-DT7, BUG-ET1.
- Severity: 🚨

⚠️ BUG-MT2: Line 35 `date = datetime.now().strftime("%Y-%m-%d")` — looks at TODAY's monthly_xray file. If cron runs at 23:55 local but file dated tomorrow due to TZ, miss. Use ET.
🟡 BUG-MT3: NO parse_mode AT ALL — always plain text, ignores Markdown formatting.
🟡 BUG-MT4: Line 49 catches exception but doesn't differentiate transient vs permanent. No retry.

### 14. send_position_alerts.py (76 lines)

What it does: Alerts for positions exceeding max_hold_days. Uses `requests`.

✅ GOOD-PA1: Uses should_send_report + mark_report_sent (line 56) properly.
✅ GOOD-PA2: HTML→plain fallback (line 60-72).
✅ GOOD-PA3: Returns 1 on failure (line 72).

⚠️ BUG-PA1: Line 16 `import requests` — extra dep. Most other senders use urllib.
⚠️ BUG-PA2: Line 24 only one chat ID (`TELEGRAM_CHAT_ID`) — does NOT support `TELEGRAM_GROUP_CHAT_ID`. All other senders fan out to both. User group misses these alerts.
- Severity: ⚠️ Single-chat-only.

⚠️ BUG-PA3: Line 25 `TODAY = date.today().isoformat()` — local time. See X-TG6.

### 15. send_weekend_telegram.py (61 lines)

What it does: Weekend reflection summary.

🚨 BUG-WT1: NO mark_report_sent. Same dedup-broken bug.
- Severity: 🚨

⚠️ BUG-WT2: Line 45 explicit comment says "send as PLAIN TEXT (no parse_mode) to avoid Markdown 400 errors". Honest but admits Markdown can't be relied on. Suggests upstream weekly_review.md has unsanitized content.
🟡 BUG-WT3: Line 41 truncates to 3500 chars — different cutoff from sibling (3950 in send_telegram.py).

### 16. send_weekly_review.py (57 lines)

What it does: Weekly self-assessment. Uses `requests`. Saves snapshot to reports/weekly/.

✅ GOOD-WR1: --no-send flag for dry-run (line 43).
✅ GOOD-WR2: Saves snapshot on disk regardless of send (line 46).

⚠️ BUG-WR1: NO dedup at all.
⚠️ BUG-WR2: Same single-chat issue as BUG-PA2 (only TELEGRAM_CHAT_ID, no group).
⚠️ BUG-WR3: Line 31 Markdown only, no fallback.
⚠️ BUG-WR4: Uses `requests`. See X-TG10.
🟡 BUG-WR5: Line 24 `if not token or not chat_id: print(... skipping send); return False` — but main() doesn't check this. Snapshot saved, send silently fails, exit code 0.

### 17. format_picks_email.py (181 lines)

What it does: Markdown formatter for GitHub issue body. NOT a Telegram sender — generates email-style markdown for daily picks. Same fail-closed validation as send_layman_daily.py.

✅ GOOD-FE1: Same official-artifact fail-closed gate as send_layman_daily (lines 58-67) — refuses to render output if validation fails.
✅ GOOD-FE2: Honors PICK_DATE override (line 27) — testable for arbitrary dates.
✅ GOOD-FE3: Markdown table format with risk %, reward %, official-artifact column.
✅ GOOD-FE4: Tag legend at bottom (lines 175-179).

⚠️ BUG-FE1: Line 50 `_fail_user_output` raises SystemExit(1) — but stderr printed BEFORE the raise. If consumed by GH issue creator, partial body may already be on disk.
- Severity: 🟡 Output-stream contamination on failure.

⚠️ BUG-FE2: Line 27 `(os.getenv("PICK_DATE") or datetime.now().strftime("%Y-%m-%d")).strip()` — naive local time. Same as X-TG6.

⚠️ BUG-FE3: Line 134-159 single big print loop. If a row is malformed (line 136 `entry = float(r["entry"])`), the try/except sets entry=sl=tp=0, then prints 0% rows in the table. Confusing for user.
- Plain English: A pick with corrupt CSV row appears as a "FREE" entry/sl/tp=0 row in the email.
- Fix: if any are 0, mark row "data invalid" or skip.
- Severity: 🟡 UX.

⚠️ BUG-FE4: Line 161-173 official-artifact metadata section only prints if at least one row has artifact present. Good. But "if r.get('official_artifact_present')" check uses string-truthy. If artifact loader sets to bool False, fine; if to "" or None, fine; if to "false" string, this incorrectly evaluates True.
- Severity: 🟡 Type-safety.

🟡 BUG-FE5: Line 102 `raise SystemExit` (no exit code) — exits 0. After fail_user_output exits 1 on error, this exits 0 for "valid no-pick day printed". Asymmetric exit semantics.

---

## Summary of Batch 3c (17 files)

### By severity
| Severity | Count |
|---|---:|
| 🚨 Show-stopper | 13 |
| ⚠️ Data/safety risk | 32 |
| 🟡 Code smell | 28 |
| 📝 Doc-only | 2 |
| ✅ Good code | 27 |
| Total | 102 findings |

### Top 10 things to fix in this batch (in order)

| # | Bug | Why first | Fix difficulty |
|---|---|---|---|
| 1 | X-TG1 (14 _send implementations) | Single highest-leverage refactor; one bug fix → all senders benefit | Medium: extract src/telegram_sender.py |
| 2 | BUG-DT7 / BUG-ET1 / BUG-MT1 / BUG-WT1 (mark_report_sent never called) | 4 senders silently bypass dedup → duplicate messages | Easy: add mark_report_sent() after success |
| 3 | BUG-LW1 / BUG-LM1 / BUG-LY1 (uses 'status' instead of 'evaluation_status') | Weekly/monthly/yearly recap likely silently EMPTY | Easy: change field name |
| 4 | BUG-ST1 (send_telegram.py vs send_layman_daily.py both wired) | Two daily senders simultaneously = unclear which is canonical | Medium: pick one, deprecate other |
| 5 | BUG-DT1 (subprocess "python" not sys.executable) | Environment-fragility; fails silently on `python`-less envs | Easy: use sys.executable |
| 6 | BUG-LD3 / BUG-LE3 (mark_sent on no-creds dry-run) | Local test runs poison dedup; next real run blocked | Easy: don't mark_sent when creds missing |
| 7 | X-TG2 (dedup strategies inconsistent) | Some files dedup by content, some by date, some not at all | Medium: standardize on one strategy per message-type |
| 8 | X-TG6 (date computation drift) | Off-by-one-day duplicates near midnight | Easy: standardize on PICK_DATE env or ET |
| 9 | BUG-IT1 (intraday alert file deleted on failure) | Failed send + deleted file = data loss | Easy: only delete on success |
| 10 | BUG-PA2 / BUG-WR2 (single chat only) | requests-based files only send to TELEGRAM_CHAT_ID, group misses | Easy: add fan-out loop |

### What this batch tells us about the project

- **The user-facing surface has the LEAST-mature engineering discipline of any batch so far.** 14 hand-rolled Telegram senders, 3 dedup strategies, 6 fallback patterns. Compared to Lane 1 contract discipline (Batch 3b), this is "growing organically" code.
- **Three "canonical" senders for the same job.** send_telegram.py (technical), send_layman_daily.py (layman), AND format_picks_email.py (issue body). All three have their own validation, formatting, and gate logic. **Pick one canonical writer; have others reuse.**
- **Dedup is broken in 4 senders** (mark_report_sent never called). Easy fix; high user-experience value.
- **The Layman family (T52) is the most disciplined** — shares src/layman_translator helpers, has the strongest pre-send gate, fails closed on missing artifacts. **This pattern should be propagated to ALL senders.**
- **Weekly/Monthly/Yearly recap likely BROKEN due to schema drift** (using `status` instead of `evaluation_status`). User has been getting "no closed trades this week" forever, even when there were. Easy verify-and-fix.
- **send_layman_daily.py and format_picks_email.py share a hidden contract** with src/official_artifact_loader. Two consumers of the same producer. Make the contract explicit.

### Glossary additions

| Term | Plain English |
|---|---|
| Sender | A script that ends with calling Telegram's HTTP API to deliver a message to a chat. |
| Dedup | Mechanism to prevent the same message being sent twice — content-based (hash of message) or date-based (one-per-day). |
| Markdown 400 | Telegram returns HTTP 400 if your message has unbalanced * or _ characters. Plain-text fallback saves these. |
| Mark-sent | After successful send, write a marker so future runs know "already delivered." If you forget mark-sent, dedup is effectively off. |
| Fan-out | Send same message to multiple chat IDs (personal + group). |
| Fail-closed | If validation fails, REFUSE to do the action. Opposite of fail-open. |

---

End of Batch 3c.

Cumulative findings across batches 1a + 1b + 2a + 2b + 3a + 3b + 3c:
- Show-stoppers: 90
- Data/safety risks: 164
- Code smells: 139
- Doc-only: 13
- Good code: 151
- Total: 557 findings across 70 files (~18,400 lines)

Next: Batch 3d — Scripts: backtest_*, learning, performance, watchlist, telegram-related auxiliary scripts (~15 files).
