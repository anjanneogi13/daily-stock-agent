# 🏛️ Daily Stock Agent — Architecture

**Last updated:** 2026-05-03
**Tests:** 805 passing · **Modules:** 78 · **Workflows:** 14 · **Health:** 10/10

---

## 0. The 24-hour Rhythm (Singapore Time)

| When (SGT) | When (US ET) | What happens | Who reads it |
|---|---|---|---|
| **Mon-Fri 8:30 PM** | 8:30 AM ET | 🌅 Daily picks → Telegram (layman) | User |
| Mon-Fri 9:30 PM – 4 AM | 9:30 AM – 4 PM ET | 📊 Intraday monitor every 30 min | Files only |
| **Tue-Sat 6:00 AM** | 6:00 PM ET (prev day) | 🌆 Performance recap → Telegram (layman) | User |
| **Daily 7:00 AM** | 11:00 PM UTC | 🌙 Nightly Brain — 7-step self-improvement | Files (`learning_journal.jsonl`) |
| **Sat 9:00 AM** | 1:00 UTC Sat | 📅 Weekly recap → Telegram (layman) | User |
| **Mon 7:00 AM** | 11:00 PM UTC Sun | 🧠 Self-Improvement Report → Telegram | User |
| **1st of month 6:00 AM** | 22:00 UTC | 📆 Monthly recap → Telegram (layman) | User |
| **Jan 2 8:00 PM** | 12:00 UTC | 🎊 Year-in-Review → Telegram (layman) | User |

---

## 1. The 8 Pillars (all live)

| # | Pillar | Module | Status |
|---|---|---|---|
| 1 | **Context-aware scoring** | `parallel_scorer.py`, `scorer.py` | ✅ Live |
| 2 | **Wisdom base** (lessons learned) | `wisdom_base.py`, `wisdom_hint.py`, `wisdom_consultant.py` | ✅ Live |
| 3 | **Pattern engine** (16 chart patterns × regime) | `pattern_engine.py`, `pattern_layer.py`, `pattern_stats.py` | ✅ Live + WIRED into scoring |
| 4 | **Calibration loop** (per-factor accuracy → weight tweaks) | `calibration.py`, `weight_proposer.py`, `weight_applier.py` | ✅ Live (5%/wk safety cap) |
| 5 | **Auto-pause** (degraded health → pause) | `auto_pause.py`, `pause_state.py`, `self_awareness.py` | ✅ Live |
| 6 | **Hypothesis engine** (Wilson 95% CI tests) | `hypothesis_engine.py` | ✅ Live |
| 7 | **News & watchlist** | `news_engine.py`, `watchlist.py` | ✅ Live |
| 8 | **Auto-promote + lesson GC** | `auto_promote.py`, `lesson_gc.py` | ✅ Live |

---

## 2. The Self-Improvement Loop (NEW — May 3 2026)

┌─ EVERY NIGHT 11 PM UTC (Mon-Sun) ─────────────────────────┐ │ src/nightly_conductor.py — single orchestrator │ │ │ │ Step 1: pattern_scan (300 tickers on holidays) │ │ Step 2: pattern_stats (per-pattern × per-regime) │ │ Step 3: pattern_auto_e_d (kill losers, restore good) │ │ Step 4: calibration_propose (per-factor accuracy) │ │ Step 5: weight_apply (under 5%/wk safety cap) │ │ Step 6: auto_promote (winners → wisdom lessons) │ │ Step 7: lesson_gc (drop stale lessons) │ │ │ │ Each step isolated in try/except — one failure can't │ │ break the chain. Single 'nightly_brain_run' event emitted │ │ to learning_journal.jsonl. │ └─────────────────────────────────────────────────────────────┘

┌─ EVERY SUNDAY 11 PM UTC ─────────────────────────────────────┐ │ src/meta_brain.py — reasons about the brain itself │ │ │ │ - recent_mutations(7d) │ │ - categorize by kind │ │ - detect_stuck_areas (no learning in 14d?) │ │ - suggest_hypotheses (outperforming buckets) │ │ - format_telegram_digest → plain English │ └──────────────────────────────────────────────────────────────┘

Code

---

## 3. Calendar Awareness (NEW — May 3 2026)

`src/market_calendar.py`

- Hardcoded NYSE holidays for **2026, 2027, 2028** (3-year buffer)
- Half-day awareness (Black Friday, Christmas Eve)
- Weekend skip everywhere (`main.py`, `intraday_monitor.py`)
- **Holidays = deep-learning days** (300 ticker scan vs 100)
- 3-layer renewal reminder system:
  1. Sunday Self-Improvement Report
  2. Monthly X-Ray Telegram
  3. GitHub Issue auto-opened Jan 1 + Jul 1 yearly
- Escalating tone: 📅 soft → ⚠️ urgent → 🚨 critical
- Annual user action: ~30 sec (~once every 2-3 years)

---

## 4. Dual-Channel Reporting (NEW — May 3 2026)

| Channel | Audience | Lives in | Telegram? |
|---|---|---|---|
| **Technical** | The AI agent (its own learning) | `signal_journal.jsonl`, `learning_journal.jsonl`, `exec_report_*.json`, `picks_log.csv` | ❌ No |
| **Layman** (NEW) | User + future amateurs | 5 `send_layman_*.py` scripts | ✅ Yes — only thing user sees |

`src/layman_translator.py` is the single source of truth for plain-English conversions:
- `score_to_words(0.92)` → `'excellent'`
- `pick_to_layman(pick)` → full plain-English with all prices
- `outcome_to_layman(out)` → `'✅ NVDA — hit profit target (+$120)'`
- `verdict_line(7,2,250)` → `'🎯 GREAT — agent crushed it today'`

---

## 5. Workflow Inventory (14 total)

| Workflow | Schedule (UTC) | Purpose |
|---|---|---|
| daily-picks.yml | 12:30 + 13:30 Mon-Fri | Pick stocks → layman Telegram |
| evaluate.yml | 22:00 Mon-Fri | Compute outcomes → layman recap |
| intraday_monitor.yml | every 30min during US hours | SL/TP proximity alerts |
| news_engine.yml | every 30min | News → watchlist boost |
| nightly_brain.yml | 23:00 daily | 7-step self-improvement |
| weekend_reflection.yml | 00:00 Sat | LLM-graded reflection |
| weekly_report.yml | 01:00 Sat | Weekly metrics + layman Telegram |
| hypothesis_weekly.yml | 15:00 Sun | Statistical edge tests |
| monthly_xray.yml | 22:00 1st of month | Monthly deep dive + layman Telegram |
| yearly_recap.yml | 12:00 Jan 2 | Year-in-Review layman Telegram |
| holiday_renewal_reminder.yml | 12:00 Jan 1 + Jul 1 | Auto-issue if calendar buffer low |
| backup.yml | 23:00 daily | Backup data/ |
| watchdog.yml | 13:35 + 14:35 Mon-Fri | Verify morning run happened |
| ci.yml | on push | Test gate |

---

## 6. Safety Mechanisms

| Risk | Defense |
|---|---|
| Weight changes too fast | 5%/factor/week cap in `weight_applier.py` |
| Promoting noise as wisdom | Wilson 95% CI required in `hypothesis_engine.py` |
| Killing patterns prematurely | Min 30 trades + mean_R < -0.30 |
| Bad strategy keeps running | Auto-pause when 14d health degrades |
| Forgetting old lessons too fast | Lesson GC requires 90+ days stale |
| Single bad day skews learning | Rolling 30d windows |
| US market closed → corrupted data | `is_trading_day()` check in main.py |
| Telegram message duplicates | `dedup_sender.py` with content-hash |
| Brain stuck without warning | Meta-Brain flags 14d-no-mutation as 'stuck' |

---

## 7. What's NEXT (deferred to future sessions)

See `docs/FINAL_ROADMAP.md` and `docs/NEXT_SESSION.md` for the prioritized backlog.
