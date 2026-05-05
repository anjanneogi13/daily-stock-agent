# 🏥 REPO HEALTH — Single Source of Truth

> **Read this FIRST in every new Claude session.**
> Generated: 2026-05-05 after commit `79a9890` from `scripts/full_repo_audit.py`
> Refresh: re-run that script weekly. If anything below changes, update this file.

---

## 🎯 30-SECOND SUMMARY

| Metric | Value | Status |
|---|---|---|
| Total tests | **1237 passed, 28 skipped** | ✅ |
| Total commits | 400+ | ✅ |
| `src/*.py` modules | 80+ | ✅ |
| Workflows | 14 (13 scheduled, 1 manual) | ✅ |
| Defensive layers active | 7 (data trust chain) | ✅ |
| Audit dashboards | 5 permanent | ✅ |
| Picks logged | 39+ (post-floor evidence still building) | ⏳ |

---

## 🚀 CURRENT PRODUCT STATUS — Monitoring-first launch

The agent is **monitoring-ready**, not execution-ready.

- No real-money trading.
- No paper trading integration yet.
- 2-week observation window first.
- Then a second 2-week validation window after architecture stabilizes.
- Paper trading eligibility requires:
  - day trades >60% win rate plus positive expectancy
  - swing trades >66% win rate plus positive expectancy
  - monster / long holder picks >90% win rate plus positive expectancy

Recent launch-readiness fixes:

- report issue upsert — workflows update same-day report issues instead of duplicating them.
- smell verdict persistence — smell_codes/smell_severities/smell_messages now persist to picks_log.
- earnings fill-rate — post-floor `days_to_earnings` is filled and audited.
- sector benchmark fill-rate — post-floor sector ETF/close/alpha fields are filled and audited.
- full_repo_audit import-safe and CSV-safe — importing audit script no longer launches nested pytest; quoted CSV commas no longer corrupt regime counts.
- company-name fallback — future unresolved company names persist blank instead of ticker-as-company; tracked historical rows were backfilled.
- SPY alpha fill-rate — all closed tracked rows have `spy_close_at_exit`, `spy_return_pct`, and `alpha_pct`.
- Daily Picks workflow reliability — multiple guarded cron chances; post-send persistence now recovers `picks_log.csv` and fails if push cannot persist state.
- Telegram sender reliability — daily sender marks dedup only after confirmed delivery to at least one configured chat.
- Tiered exits decision — tiered TP columns are reserved schema in monitoring mode, not active execution logic.
- Hard-block coverage — penny, stop-loss buffer, cooldown, weak-sector, catastrophic-news, and audit-log behavior are locked by tests.

Decision record: `docs/decisions/2026-05-05-monitoring-first-no-paper-trading.md`

---

## 🛡️ DEFENSIVE LAYERS (data trust chain)

Pre-pick: stale_price smell (E2c.2) ✅ Post-pick: unreachable_entry guard (F3) ✅ Persistence: journal consistency lock (F4) ✅ Workflow: git-add complete (F6,G1-G4) ✅ Analysis: DATA_QUALITY_FLOOR fence (E5-B) ✅ (floor=2026-05-02) Reporting: sample-size honesty (E5-C) ✅ Enforce: readiness scorer (F5) ✅ (3 gates ⏳ waiting on data)

Code

---

## 🚦 OBSERVE-MODE GATES (do NOT flip manually)

⏳ SMELL_ENFORCE n=0/30 blocked: n=0 < 30 smell-tagged closed picks
🟡 BRAIN_ENFORCE_EV n=1/30 blocked: insufficient closed post-floor picks and not enough EV-tagged outcomes
🟡 AUTO_PAUSE_ENABLED n=1/50 blocked: insufficient closed post-floor picks

Code

`scripts/check_enforcement_readiness.py` is the only authority. When it says READY, set the env var. Until then, default false.

---

## 📁 SRC MODULES (81 total, 78 live)

### ❌ Untested but in use (P5 — write tests)
- `earnings_analyzer` (214 lines)
- `llm_agent` (202 lines)
- `market_news` (210 lines)
- `performance_stats` (127 lines)
- Smaller: `monster_data`, `paper_trader`, `picks_csv`, `cape_ratio`

### Intentional dead (locked by `audit_dead_code.py`)
- `book_ingest` — CLI: `python -m src.book_ingest`
- `yearly_report` — CLI: `python -m src.yearly_report`

---

## ⚙️ WORKFLOWS (14 total)

| Workflow | Schedule | Persists |
|---|---|---|
| `daily-picks.yml` | 12:30+13:30 UTC weekdays | picks_log, learning_journal, last_regime, hard_blocks_log, agent_memoir, weight_history, telegram_sent ✨G1-G4 |
| `evaluate.yml` | 22:00 UTC weekdays | picks_log, learning_journal, signal_journal ✨G1 |
| `news_engine.yml` | every 30m, 8-23 UTC | news_log, news_seen, news_signals, watchlist ✨F6 |
| `nightly_brain.yml` | 23:00 UTC daily | patterns, pattern_stats, weight_proposals, weight_history, learning_journal, agent_memoir ✨G2 |
| `intraday_monitor.yml` | every 30m, 13-21 UTC | intraday_alerts |
| `weekend_reflection.yml` | Sat 00:00 UTC | learning/, exec_report |
| `weekly_report.yml` | Sat 01:00 UTC | metrics_daily, metrics_history |
| `hypothesis_weekly.yml` | Sun 15:00 UTC | reports/hypothesis/ |
| `monthly_xray.yml` | 1st of month | learning/monthly_xray |
| `backup.yml`, `watchdog.yml`, `holiday_renewal_reminder.yml`, `yearly_recap.yml`, `ci.yml` | various | (see file) |

---

## 💾 KEY DATA FILES (status as of 2026-05-04)

| File | Size | Persistence |
|---|---|---|
| `news_log.jsonl` | 844 KB | ✅ every 30 min |
| `learning_journal.jsonl` | 145 KB (788 entries) | ✅ FIXED tonight (G1) |
| `news_signals.json` | 100 KB | ✅ FIXED tonight (F6) |
| `signal_journal.jsonl` | 14 KB | ✅ per pick |
| `picks_log.csv` | 6 KB | ✅ per pick |
| `agent_memoir.json` | 1 KB | ✅ FIXED tonight (G2) |
| `last_regime.json` | small | ✅ FIXED tonight (G3) |
| `hard_blocks_log.json` | 1 KB | ✅ FIXED tonight (G4) |

**Deleted tonight (orphans):** `signal_journal.backup.jsonl`, `signal_journal.recalibrated.jsonl`, `src/backtester.py` (34-line stub).

---

## 🔧 PERMANENT AUDIT DASHBOARDS

python scripts/audit_dead_code.py # detects unused modules python scripts/audit_journal_consistency.py # detects store drift python scripts/check_enforcement_readiness.py # gate-flip readiness python scripts/full_repo_audit.py # full repo scan

Code

Run weekly. Each <2 sec. If output changes meaningfully, update this file.

---

## 🚨 RECURRING BUG PATTERN (now defensively locked)

> **"Code runs. Logs say success. But the OUTPUT doesn't reach where it needs to go."**

Caught and fixed:
- F1: wisdom generated → never sent to Telegram
- F2: smell faculty existed → never imported into main
- F3: outcome `sl_hit` → trade was physically impossible
- F6: news signals computed → workflow `git add` omitted file
- G1-G4: 4 more files (learning_journal, agent_memoir, last_regime, hard_blocks_log) → workflows omitted them

**Now locked by `tests/test_workflow_persistence_complete.py` (6 tests).**
Future YAML changes that strand a data file = CI fails immediately.

---

## 🎯 PENDING WORK (no new features — fixes only)

| # | Issue | Effort | Source |
|---|---|---|---|
| O1 | Wait for n≥30 smell-tagged closed post-floor picks before flipping SMELL_ENFORCE | data wait | Bug #17A/#17B |
| P5a | `hard_blocks` gate logic test coverage | fixed | This audit |
| P5b | Write tests for `llm_agent`, `market_news`, `earnings_analyzer` | varies | This audit |
| P3 | SPY alpha historical audit/backfill verification (`Bug #9`) | fixed | TODO_BUGS |
| O2 | Wait for n≥30 closed post-floor picks for BRAIN_ENFORCE_EV and n≥50 for AUTO_PAUSE_ENABLED | 3-6 weeks | F5 (data) |
| P6 | Company-name fallback cleanup (`Bug #6`) | fixed | TODO_BUGS |

---

## 🚪 NEXT-SESSION DOOR-OPENERS

"Read docs/REPO_HEALTH.md and tell me what's pending."

"Run all 5 audit dashboards and tell me what changed since REPO_HEALTH.md."

"Check enforcement readiness and monitoring readiness after more closed post-floor picks accumulate."

"Audit src/llm_agent.py coverage and add tests for llm_agent, market_news, earnings_analyzer."

Code

---

## 📊 PICKS_LOG STATE (after data-quality fix commit `79a9890`)

- 39 picks total, 5 unique days (2026-04-28 → 2026-05-04)
- Post-floor rows: 3
- Post-floor closed for enforcement readiness: 1 quality-filtered closed row
- Earnings fill-rate post-floor: 100%
- Sector benchmark fill-rate post-floor: 100%
- Smell persistence schema present; waiting for smell-tagged closed outcomes

---

*If this file is older than 7 days, re-run `python scripts/full_repo_audit.py` and refresh.*
