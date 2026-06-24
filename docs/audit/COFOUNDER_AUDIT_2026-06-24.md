# 🔍 COFOUNDER AUDIT — `anjanneogi13/daily-stock-agent`
## Full-repository audit against the 29-item product vision
*Date: 2026-06-24 · HEAD = main · Output-only. Prior-audit-doc claims labeled unverified per Hard Rules. Severities carried from staged corrections.*

---

## 1. EXECUTIVE SUMMARY (plain English)

You set out to build an honest, monitoring-only daily stock-pick agent that learns from its results, explains every pick, and never trades real money without you. **The good news: the safety spine is real and genuinely well-built.** It does not place trades, it defaults to "watch only," it runs a serious multi-factor scorer through a thick stack of fail-closed risk gates every morning, it degrades gracefully when data is missing, and it ships picks to Telegram with sensible duplicate-suppression. **About half the vision is honestly delivered — and it's the half that keeps you safe.**

**The hard news: most of the "smart, self-improving, backtest-proven" half is unproven, un-wired, or quietly broken — and it's broken by one root cause.** The system writes its "memory" and "learning" to files that are **excluded from git and never restored**, so every night it forgets almost everything: the kill-switch's pause record, the factor-suppression list, the weight-change history (which silently turns its "5%/week" safety cap into 5%/**night**), and its own "memoir." The single learning file it *does* save is the one **nothing reads.**

Four things a non-coder would never catch on their own:
1. The **"backtester-proven losers"** claim that drives real ticker exclusions rests on a **survivorship-biased universe** and a **mis-annualized Sharpe**, has **zero tests**, and is hardened into a green test that makes an empty claim look validated.
2. Your entire pick history — `picks_log.csv` — is rewritten **non-atomically by multiple concurrent jobs**, risking corruption of the one file everything else depends on.
3. The **kill-switch / drawdown circuit-breaker is observe-only by default** ("does NOT pause anything"), and its state file isn't durable anyway.
4. **"Monster" picks secretly widen their own stop-loss to 5% *after* the risk gate already approved them** (BUG-M97), so the risk you're shown isn't the risk that passed the safety check — and the two saved records of the same pick can even disagree.

On top of that, **everything goes to one Telegram channel** — there's no separate Monster channel and no "I'm alive" heartbeat — so a silent failure stays silent.

**Cost is NOT a concern** (worst case ~3,200 LLM calls/week ≈ ~$25/week; realistically a few dollars). **Security is clean** (no eval/pickle/shell-injection; secrets handled correctly — an earlier Alpaca-credentials worry was mine and is withdrawn).

**Bottom line:** this is a safe, over-ambitious *monitoring* tool wearing an autonomous-AI-hedge-fund costume. Make the state durable, prove or retire the backtester, make `picks_log.csv` writes atomic, fix the monster-after-gate bypass, and either enforce or relabel the kill-switch — and the costume starts matching the body. None of this is a disaster; all of it is fixable in roughly one focused engineering month.

---

## 2. ALIGNMENT SCORECARD — ALL 29 ITEMS

**Legend:** ✅ wired · 🟡 built-not-wired · 🟠 partial/stub · 🔵 not-built · ❌ absent · 👻 scope-creep · ⚠️ built-wrong/flagged
*Dual-state items are bucketed by their **worst half**, with the nuance noted in evidence.*

| # | Item (abbrev) | Bucket | 1-line evidence (file:LINE) | Prior-audit ref |
|---|---|---|---|---|
| 1 | Pre-market picks before open | ✅ | `daily-picks.yml` cron + `main.run()`; 09:20 ET cutoff; multi-fire guard `main.py:719-726` | matches |
| 2 | Post-open picks shortly after open | ✅ | post-open path + watch-only late lane `generate_late_daily_ideas.py` | matches |
| 3 | Intraday picks; ⚠️ if delayed/free data as real-time | ⚠️ | **free ~15-min-delayed yfinance** `intraday_scanner.py:48,95` (`interval="5m",prepost=False`) surfaced as `current_price`/`price` | **prior missed** |
| 4 | Monster Hunter on **separate** channel; any time incl weekends | 🔵 | monster scoring real (`monster_hunt.py`) but **separate channel not built** — all senders use one `TELEGRAM_CHAT_ID`; no `MONSTER_CHAT_ID` | **prior missed** |
| 5 | Conviction + allocation % from reproducible formula, **no hardcoded constants** | ⚠️ | scorer real (`scorer.py:221`) BUT weights hardcoded in `config.yaml`; intraday `50+momentum` (`intraday_scanner.py:70-83`); late flat 1.5/3% (`generate_late_daily_ideas.py:251`) — violates no-hardcoded rule | partially matches |
| 6 | Outcome logging + config-tuning; **no self-rewriting .py; logic via human PR** | ⚠️ | logs ✅; but `weight_applier._save` rewrites `config/weights.json` + `nightly_brain.yml:58-72` auto-commits to `main`, **no PR** (unified w/#7) | matches |
| 7 | Weekly retrain; weights swapped **atomically w/ rollback** | ⚠️ | `nightly_conductor` retunes; state **non-durable** (gitignored), no atomic swap, no rollback (unified w/#6) | **prior missed depth** |
| 8 | Weekly/monthly/quarterly/yearly reports | ✅ | `weekly_review.py`, `monthly_xray.py`, `quarterly_report.py` + senders | matches |
| 9 | Off-hours → dated artifact not idle CPU | ✅ | nightly/weekend jobs emit dated `data/learning/*.md` | matches |
| 10 | RAG over finance material, **each pick cites chunks** or decoration | 🟡 | "books into brain" `data/books/*.yaml` + `wisdom_consult`; picks do **not cite chunks**; tilt capped ±0.05 (`parallel_scorer.py:147`) → decoration | partially matches |
| 11 | Backtester deterministic, PIT, no-lookahead, **no survivorship**, walk-forward | ⚠️ | no-lookahead ✅ (`pit_data.py:38`); survivorship-biased + √250 Sharpe + dev-only + 0 tests | matches |
| 12 | Regime labeling in backtest+live, per-regime, incl 2020/2008/2000 | 🟠 | live regime ✅ (`regime.py`); backtester regime partial; **named historical crises not evidenced** | partially matches |
| 13 | Multi-agent ensemble (referee), defined I/O; Pillar-N w/o runtime role = 👻 | 👻 | no technical/fundamental/news/macro→referee ensemble; `meta_brain`/`agent_memoir`/`smell_faculty`/Pillars ornamental | matches |
| 14 | Telegram: swing/intraday one chan, monster another; idempotent; rate-limited | ❌ | idempotent ✅ (`dedup_sender`); **rate-limit ❌** (bare urlopen, no 429) **AND channel-sep ❌** (one chat) — 2 of 3 fail | **prior missed (2 of 3)** |
| 15 | Secrets in env, retries+backoff, graceful degradation, structured logs | ✅ | secrets via `secrets.*`; degradation pervasive (`nightly_conductor._step`); JSONL run-status logs | matches |
| 16 | Paper-default, real-money behind hard flag; reconcile TRADING_MODE; gates code-checked | ✅ | `TRADING_MODE` unset⇒no paper (`main.py:625`), test-locked; contract enforces `paper/live=False` | matches |
| 17 | Calibration; if breaks, picks **auto-suppressed** not silently shown | 🟡 | `pattern_layer.auto_enable_disable` computes; suppression state (`pattern_stats.json`) **gitignored→resets** → not durably suppressed | **prior missed depth** |
| 18 | Kill-switch + drawdown breaker; **verify auto_pause enforces** | ⚠️ | `pause_state.load_config()→{"enforced":False}` (`:25-26`); `auto_pause.py:9-11` "does NOT pause"; pause-state file also gitignored | matches |
| 19 | Explainability: top-3 reasons + what-invalidates + data-used + data-missing + model/agent version | 🟠 | `official_pick_artifact`: `selection_reason`✅, `invalidation_conditions`✅, `score_components`✅, `scoring_version`/`commit_sha`✅; **data-missing partial, top-3 not structured, official lane only** | **moved UP from provisional** |
| 20 | Position sizing, **caps enforced** (1–2%, exposure, sector) | ✅ | `portfolio_risk_gate.evaluate_candidate_portfolio_risk` rejects >risk%·1.05 + sector/tag caps (`:177-184`); wired `main.py:1330` | matches |
| 21 | Exit plan WITH entry (entry/SL/TP/time-stop); BUG-M97 monster mutates after gates | ⚠️ | exits delivered ✅; **BUG-M97 CONFIRMED** — monster overwrites SL/TP/qty `main.py:1672-1676` **after** risk gate (`:1330`)+artifact (`:1567`); flat 5% stop (`monster_hunt.py:126`) un-revalidated; time-stop weak | **confirmed real** |
| 22 | Versioning: model ver + **config HASH** + **data snapshot ts** + commit SHA per pick | 🟠 | `commit_sha`✅ + `config_version="config.yaml"` (**string, not hash**, `main.py:380`) + **no data-snapshot ts**; only official artifact, not `picks_log.csv` rows | matches |
| 23 | Vendor fallback chain (**Finnhub→**yfinance→Stooq→skip), source recorded | 🟠 | yfinance→Stooq + `provider_failure_taxonomy` + `provider_status` ✅; **Finnhub not in chain** → partial | matches |
| 24 | "No-pick is valid"; verify `write_guard_no_pick_artifact.py` enforces | ✅ | no-pick contract + causes (`premarket_decision_contract.py:108-120`); guard wired (`main.py:581-617`) + tests | matches |
| 25 | **Survivorship-free UNIVERSE** (delisted incl.); if today's list → ⚠️ critical | ⚠️ | `run_backtest.py:21-29` uses **today's survivors** over history → ⚠️ critical per item's own instruction | matches |
| 26 | Adversarial regimes (2008/2020-Mar/2022/boring) before shipping | 🔵 | no adversarial-regime test harness; not in CI | matches |
| 27 | Human-in-loop: every config/weight change = PR + Telegram approval; verify proposer/applier | ⚠️ | `weight_applier` auto-applies + `nightly_brain.yml` auto-commits to `main`; **no PR, no approval** (impact nil — file unread) | matches |
| 28 | Sector cap/day **AND** reject 60-day return corr > 0.7 | ❌ | sector/tag caps ✅ (`scorer.py:7,22`); **0.7 correlation guard absent** — no corr computation anywhere (worst-half = absent) | matches |
| 29 | **Heartbeat channel** posts "I'm alive / what I sent today" | ❌ | `watchdog.yml` fires **only on failure** to **same chat** (`:95`); no positive heartbeat, no own channel | **prior missed** |

### Scorecard tally (exactly one bucket per item)

| Bucket | Count | Item #s |
|---|---|---|
| ✅ wired | **8** | 1, 2, 8, 9, 15, 16, 20, 24 |
| 🟡 built-not-wired | **2** | 10, 17 |
| 🟠 partial / stub | **4** | 12, 19, 22, 23 |
| ⚠️ built-wrong | **9** | 3, 5, 6, 7, 11, 18, 21, 25, 27 |
| 🔵 not-built | **2** | 4, 26 |
| 👻 scope-creep | **1** | 13 |
| ❌ absent | **3** | 14, 28, 29 |
| **TOTAL** | **29** | ✅8 + 🟡2 + 🟠4 + ⚠️9 + 🔵2 + 👻1 + ❌3 = **29** ✔ |

### Non-goals (scope-creep check)

| Non-goal | Present? | Verdict | Evidence |
|---|---|---|---|
| Real-money auto-execution / broker | No | ✅ correctly absent | no order placement anywhere; `alpaca` used for news only |
| Crypto / options / futures | No | ✅ correctly absent | equities-only universe |
| Market-direction timing models | Borderline | 🟡 watch | `regime.market_regime` is a bull/bear gate (defensible, not a timing model) |
| Social-sentiment scraping | No | ✅ correctly absent | news = RSS/Alpaca headlines only |
| Web UI / dashboard | Partial | 👻 minor | `streamlit==1.38.0` (`requirements.txt:7`) + a dashboard script → mild scope-creep |
| LLM that rewrites its own source | No (.py) | ✅ correctly absent | LLM writes prose only; **but** auto-rewrites `config/weights.json` (see #6/#27) |

---

## 3. TOP 10 BROKEN / FAKE / DANGEROUS (ranked)

1. **🔴 P0 — Systemic statelessness (the root cause).** Brain/learning/safety state is gitignored and never restored (`.gitignore:225`; `run_nightly_brain.py:9-15` has no restore; no `actions/cache`/`download-artifact` in `nightly_brain.yml`). Breaks memory, factor-suppression, kill-switch persistence, **and** silently turns the 5%/week weight cap into 5%/night (`weight_applier.py:65-73` reads empty history). **Fix:** commit the state files **or** add `actions/cache`/artifact-restore at job start.
2. **🔴 P0 — Unified broken brain (#6+#7).** Nightly cron rewrites `config/weights.json` (`weight_applier.py:47`) and auto-commits to `main` with no PR (`nightly_brain.yml:58-72`) — but no scorer reads it (`parallel_scorer.py:50` uses `cfg["weights"]`; `scorer.py:221`), and the five files that *do* matter are dropped. **Zero pick-impact today, latent-critical if ever wired.** **Fix:** stop auto-committing weights; gate any weight change behind a PR; decide whether `config/weights.json` should feed scoring at all.
3. **🔴 P1 — `picks_log.csv` corruption risk.** `picks_csv.update_pick_row` does a non-atomic truncate+rewrite (`picks_csv.py:42-45`) on the durable pick history, with concurrent writers (intraday monitor + evaluate) and a git-rebase-push loop. **Fix:** tmp-file + `os.replace`; add a cross-workflow lock.
4. **⚠️ HIGH — BUG-M97: risk gate bypassable by post-gate mutation (#21).** Monster treatment overwrites SL/TP/qty at `main.py:1672-1676` **after** the portfolio risk gate (`:1330`), missing-data gate (`:1427`), and official-artifact validation (`:1567`) — widening the stop to a flat 5% (`monster_hunt.py:126`) that the per-trade-risk cap (`portfolio_risk_gate.py:177`) never re-checks. **Shown/logged risk ≠ gate-approved risk for any pick with `monster_score ≥ 0.60`** (`main.py:1664`). Bounded today only because trading is off. **Fix:** move the monster block *before* the risk gate, or re-run `apply_portfolio_risk_gate` + re-validate the artifact after mutation.
5. **🟠 HIGH — Backtester "proven" is unproven.** Survivorship-biased universe (`run_backtest.py:21-29`), √250-scaled-per-trade Sharpe (`src/backtester/metrics.py`), dev-only/not-in-CI, **zero tests**, hardened by `test_exclusions.py:12` ("UNH,TEAM,SMCI,DIS,SCHW … proven losers"). **Fix:** point-in-time universe w/ delisted names; per-period Sharpe; one CI run; add `test_backtester*`; or relabel exclusions "heuristic, unverified."
6. **🟠 HIGH — Kill-switch / circuit-breaker is observe-only (#18).** `pause_state.load_config()→{"enforced":False}` default (`:25-26`); `auto_pause.py:9-11` "ONLY reports. Does NOT pause anything." The pause-state file is also gitignored, so even if flipped a pause wouldn't survive a run. **Fix:** set `enforced:true`, commit `config/auto_pause.json`, make `pause_state.json` durable; or relabel "advisory."
7. **⚠️ #25 critical — Survivorship in the universe.** Per the item's own instruction, today's-list universe = ⚠️ critical (`run_backtest.py:21-29`). **Fix:** historical index membership incl. delisted names.
8. **❌ #28 — No correlation guard.** Sector/tag caps exist; the "reject 60-day return corr > 0.7 issued together" half is entirely absent (no correlation computation anywhere). **Fix:** add pairwise 60-day return correlation among finalists; reject pairs > 0.7.
9. **❌ #29 + 🔵 #4 + ❌ #14 — One channel, no heartbeat.** All senders use one `TELEGRAM_CHAT_ID`; no `MONSTER_CHAT_ID`/`HEARTBEAT_CHAT_ID`; `watchdog.yml:95` alarms only on failure. Silent success/failure stays silent; monster mixes with swing. **Fix:** add two chat IDs; route monster separately; post a daily success heartbeat.
10. **⚠️ #3 — Delayed-free data presented as intraday-live.** `intraday_scanner.py:48,95` uses free ~15-min-delayed yfinance, surfaced as `current_price`/`price`. **Fix:** label "delayed ~15m" in output, or move to a real-time feed before any action.

*(Honorable mention / 🟡 MED — no global LLM budget + load-bearing unpinned dep: per-job caps exist (`max_items=20`) but no cumulative $ ceiling/observability; `anthropic>=0.40.0` (`requirements.txt:19`) unpinned, no lockfile, no LLM-client test.)*

---

## 4. TOP 10 THAT ACTUALLY WORK WELL (honest)

1. **Trading hard-off, test-locked (#16).** `TRADING_MODE` unset ⇒ no paper (`main.py:625`); `test_monitoring_mode_no_paper_default.py` enforces. The core safety promise is real.
2. **Morning multi-factor scorer (#1,2).** `scorer.composite_score` — 7 components + 12-indicator suite (`scorer.py:48-235`) — is genuine, not a stub.
3. **Position-sizing & concentration caps ENFORCED (#20).** `portfolio_risk_gate` actually *rejects* over-risk/over-concentration candidates (`portfolio_risk_gate.py:163-184`), wired at `main.py:1330` — declared **and** enforced (caveat: BUG-M97 mutates after it).
4. **No-pick is a real, first-class output (#24).** Full no-pick contract + 12 causes + guard + tests (`premarket_decision_contract.py:108-120`, `main.py:581-617`). The pipeline has ~6 fail-closed return points.
5. **Graceful degradation (#15).** Every brain step and scorer sub-system is failure-wrapped; fail-closed on safety, fail-open on cosmetics.
6. **Vendor fallback chain (#23, partial).** yfinance→Stooq with failure taxonomy and `provider_status` surfaced on no-pick.
7. **Backtester *mechanics* (the half that's right).** No look-ahead (`pit_data.py:38` strict `<`) and conservative SL-first tie-break (`outcome_simulator.py:62`).
8. **Journals are atomic (corrects "85% unsafe").** `signal_journal` append + outcome-rewrite use `os.write`+fsync / tmp+`os.replace` (`signal_journal.py:200-262`); `news_signals`/`market_data_health` also atomic.
9. **Telegram idempotency (#14 half).** `dedup_sender` + per-report sent-ledgers + post-send file deletion prevent duplicate sends on retry.
10. **Security hygiene + reproducibility groundwork.** No eval/exec/pickle/`yaml.load`/shell-on-input; secrets via `secrets.*` (Alpaca-creds flag withdrawn). The official artifact *does* stamp `commit_sha`+versions (`official_pick_artifact.py:184-192`) — a real foundation for #22.

*(Found 10 — the safety/pipeline/delivery spine is genuinely solid.)*

---

## 5. HIDDEN FINDINGS

- **The statelessness disease is ONE root cause behind 4–5 separate vision failures** (#7 memory, #17 suppression, #18 kill-switch durability, #6/#27 weight history+cap). Fixing persistence fixes a cluster — the single highest-leverage change in the repo.
- **The cruel irony of the nightly commit:** the only brain file that survives to git (`config/weights.json`) is the one **nothing reads**; the five that matter are silently dropped (`nightly_brain.yml:62-65` adds gitignored paths → no-op).
- **BUG-M97 sub-finding — artifact vs CSV divergence:** the official pick artifact is written *before* monster mutation (`main.py:1567`) while `picks_log.csv` is written *after* (`main.py:1735`), so the **same monster pick can record different SL/TP in the two durable records** — the artifact shows the pre-monster (gate-approved) stop, the CSV shows the widened 5% stop. Two sources of truth, two different risk numbers.
- **Green-checkmark theater:** `test_exclusions.py:1-12` hardens an unproven "backtester-proven losers" claim into a passing test that *cites a roadmap doc* — making an empty foundation look validated to a non-coder.
- **Brain cosplay (#13 👻):** `meta_brain`, `agent_memoir`, `self_awareness`, `smell_faculty`, `hypothesis_engine`, Pillars 1–6 — large, real code with **no distinct runtime role** in pick selection (the EV gate, auto-pause, and smell faculty are all **OBSERVE-MODE by default**: `main.py:1045,1079,1120`). The "🧠 Brain learned X this week" Telegram footer narrates learning that doesn't durably happen.
- **Dead/duplicate code:** root `backtest.py` imports a **deleted** `backtest_simple` (`backtest.py:7` → import error if run); root `evaluate_picks.py` is a dead twin of the live `scripts/evaluate_picks.py`; ~7 interleaved one-shot `backfill_*` scripts mix with production.
- **`picks_log.csv` is a database committed to git** (`.gitignore:245` force-tracks it) and rewritten by ≥4 workflows — code+state entanglement plus the non-atomic corruption risk above.
- **Same-file timezone inconsistency (confirmed in code):** `intraday_scanner.py:179` uses `datetime.now(timezone.utc)` for the observation date while `:244` uses `datetime.now(ET)` — different date basis in one file. The broader "~8 wrong-clock bugs" scope is **per prior-audit-doc `104_main_py_part2.md` and is unverified.**
- **Prompt-injection surface:** untrusted news headlines flow unsanitized into Claude (`news_classifier.py:48-52`, `llm_agent.py:78`); can nudge `tradeable_score`/sentiment (capped ±0.03, gate-protected) — medium for signal integrity, low for safety.
- **Cost reality (corrects prior "160/week"):** News Engine = ~160 **runs**/week (`news_engine.yml:11`), up to **~3,200 Claude calls/week** worst-case ≈ **~$25/week** ceiling; realistically a few $/week. Not a concern.
- **Multiple observe-mode gates stack:** EV gate (`BRAIN_ENFORCE_EV`, `main.py:1045`), auto-pause (`AUTO_PAUSE_ENABLED`, `:1079`), smell faculty (`SMELL_ENFORCE`, `:1120`) are **all off by default** — so several "safety/brain" layers are wired but inert.

---

## 6. DELTA vs PRIOR AUDIT (2026-05-12 full-repo audit)

| Category | Finding | Notes |
|---|---|---|
| **(a) Still true (confirmed this audit)** | **BUG-M97 monster-after-gates — CONFIRMED REAL** (`main.py:1672-1676` after risk gate `:1330`/artifact `:1567`); main.py magic-numbers/not-config-driven (#5); no `repo_now_et()` helper (TZ smell persists); backtester unproven | BUG-M97 upgraded from prior "flagged" to **verified** with full gate-order trace |
| **(b) Fixed since 2026-05-12** | `signal_journal` made atomic (PR-A4.5, `:255-262`); `news_signals`/`market_data_health` atomic; regime "unknown" hardened (`regime.py`); company-name fallback (PR-A2.6); per-pick journal try/except + quarantine (`main.py:1766-1808`) | Real improvements — the journals are no longer the corruption risk |
| **(c) Refuted / outdated** | "85% of writers unsafe" → **journals atomic; only `picks_csv` is the real gap**; "Alpaca creds exposed" → **standard secrets, non-issue**; "160 Anthropic calls/week" → **~3,200 calls/week worst-case** (runs≠calls) | Three prior figures corrected this audit |
| **(d) Prior audit MISSED** | **Systemic statelessness** (gitignored state breaks kill-switch/suppression/cap/memory at once); **weights auto-commit writes a file nothing reads**; **one-channel / no-monster-channel / no-heartbeat** (#4/#14/#29); **delayed-free data as intraday-live** (#3); **`picks_csv` non-atomic + concurrent writers**; **correlation guard absent** (#28); **artifact-vs-CSV SL/TP divergence** | The headline new findings |

---

## 7. PRIORITIZED ROADMAP (10 tasks)

| # | What to do (hand to an engineer) | Why | Effort | Files | Acceptance criterion |
|---|---|---|---|---|---|
| 1 | **Make brain/safety state durable.** At each nightly job start, restore prior state via `actions/cache` (or `download-artifact`); commit the small JSON/JSONL state files instead of gitignoring them. | Fixes the statelessness root cause behind #6/#7/#17/#18 | **M** | `nightly_brain.yml`, `.gitignore`, `run_nightly_brain.py` | After two consecutive nightly runs, `weight_history.jsonl`/`agent_memoir.json`/`pattern_stats.json` from run 1 are present at run 2; the weight cap accounts across days |
| 2 | **Stop auto-committing strategy config to `main`; require a PR.** Remove `config/weights.json` from the nightly `git add`; open a PR with the diff + Telegram approval for any weight change. | Satisfies #6/#27 human-in-loop | **S** | `nightly_brain.yml`, `weight_applier.py` | No direct-to-main weight commits; weight changes appear only via reviewed PRs |
| 3 | **Make `picks_log.csv` writes atomic + serialized.** Switch `update_pick_row` to tmp-file + `os.replace`; add a lock so monitor/evaluate don't rewrite concurrently. | Prevents corruption of the durable pick history | **S** | `picks_csv.py`, intraday/evaluate workflows | Concurrent-write stress test never truncates/corrupts the CSV |
| 4 | **Either enforce or relabel the kill-switch.** *Relabel path:* rename `auto_pause` UI/docs to "advisory." *Enforce path:* set `enforced:true`, commit `config/auto_pause.json`, and make `pause_state.json` durable — **requires Task 1 first**, else a triggered pause is wiped next run. | #18 safety brake is observe-only (`pause_state.py:25-26`) and its state file is non-durable | **S to relabel / M to enforce — enforce path BLOCKED-BY Task 1** | `config/auto_pause.json`, `src/pause_state.py`, `src/auto_pause.py`, docs | *Relabel:* no UI/Telegram text implies an active auto-pause. *Enforce:* a simulated >X% 30-day drawdown actually suppresses picks **and** the pause persists into the next scheduled run |
| 5 | **Fix BUG-M97: re-validate risk after monster mutation.** Move the monster SL/TP/qty block to *before* the portfolio risk gate, or re-run `apply_portfolio_risk_gate` + re-validate the official artifact after mutation, so widened stops are checked and the artifact and CSV agree. | #21 — shown risk must equal gate-approved risk; eliminate artifact-vs-CSV divergence | **S** | `main.py` (move block ~1654-1682 above `:1330`, or re-validate), `monster_hunt.py`, `official_pick_artifact.py` | A monster pick whose 5% stop exceeds the per-trade-risk cap is blocked or resized; artifact SL/TP == `picks_log.csv` SL/TP for every pick |
| 6 | **Fix the backtester's universe + Sharpe, put one run in CI.** Use point-in-time index membership incl. delisted names; annualize Sharpe correctly per period; add `test_backtester*`/`test_metrics*`. | #11/#12/#25 — make "proven" mean proven | **L** | `src/backtester/*`, `tests/`, a new CI workflow | Backtest reproduces in CI on pinned dates; metrics test passes; exclusions traceable to a real run |
| 7 | **Split Telegram channels + add a heartbeat.** Introduce `MONSTER_CHAT_ID` and `HEARTBEAT_CHAT_ID`; route monster alerts to their own channel; add a scheduled workflow that posts a daily "I'm alive + what I sent today" message even on no-pick days. | #4/#14/#29 — make silent failure loud; stop monster mixing with swing | **M** | all `scripts/send_*.py`, new `.github/workflows/heartbeat.yml`, repo/Actions secrets | Monster posts only to its chat; a heartbeat arrives daily (incl. no-pick days); swing/intraday unaffected |
| 8 | **Add a correlation guard.** Compute pairwise 60-day return correlation among finalists; reject co-issued pairs > 0.7. | #28 missing half | **M** | `portfolio_risk_gate.py`, `scorer.py` | Two 0.9-correlated finalists are never issued together; a test covers the 0.7 boundary |
| 9 | **Label data freshness + complete explainability + pin deps + real config hash.** Mark intraday output "delayed ~15m"; add structured top-3 reasons + explicit data-missing + model version to every Telegram pick; pin `anthropic`/`alpaca-py` + lockfile; replace `config_version="config.yaml"` with a sha256 + data-snapshot timestamp written to `picks_log.csv` rows. | #3/#19/#22 honesty + reproducibility + LLM stability | **M** | `intraday_scanner.py`, `send_telegram.py`, `official_pick_artifact.py`, `picks_csv.py`, `requirements.txt` | Each pick shows top-3 reasons, what-invalidates, data-missing, model+commit; intraday flagged delayed; pinned deps; each pick row carries a config hash + snapshot ts |
| 10 | **Quarantine dead/duplicate code + decide the brain's status.** Delete root `backtest.py`/`evaluate_picks.py` twins, prefix one-shot `backfill_*`; either give the Pillar/brain modules a real runtime role or label them "experimental" and silence the "Brain learned X" claim. | Legibility (#13 👻); stop the fake-learning narrative | **M** | root `*.py`, `scripts/backfill_*`, `meta_brain.py` + weekly footer | No import-error dead files; brain footer reflects only durable, wired learning |

*(Quick add-on to Task 9: a global daily LLM call/$ counter with a circuit-breaker — cost is low but currently unobserved.)*

---

## 8. BRUTAL VERDICT

**Real vs aspirational: ~50% real, ~50% aspirational** — but the split is not random. The **safety, morning-pipeline, and delivery spine is genuinely real** (8 of 29 items fully wired, plus partials, and they're the ones that protect you: no trading, enforced risk caps, no-pick as a first-class output, graceful degradation, fallback data, atomic journals). The **"autonomous, self-improving, backtest-proven, multi-agent" superstructure is mostly aspirational** — not because the code is absent (it's voluminous) but because it's **un-wired, unproven, or non-durable.** The defining defect is **systemic statelessness**: one root cause that simultaneously guts memory (#7), factor-suppression (#17), the kill-switch's durability (#18), and the weight-cap (#6) — so the "learning loop" is mechanically a nightly recompute-and-forget, and the "🧠 Brain learned X this week" message is, bluntly, narration of something that doesn't persist. The sharpest single bug is **BUG-M97**: the one place a safety gate is actively defeated, by the system's own monster logic widening a stop after the gate approved it.

**Distance from the 29-item vision:** roughly **one focused engineering month** from "honest and coherent," **not** close to "autonomous AI fund." The biggest gap is **integrity-of-claims, not feature count** — most items are *attempted*. Make state durable (Task 1), prove or retire the backtester (Task 6), atomic-write the pick log (Task 3), fix the monster-after-gate bypass (Task 5), enforce-or-relabel the kill-switch (Task 4), and split channels + heartbeat (Task 7), and the alignment jumps from ~50% to ~75% real with mostly Small/Medium tasks.

**Realistic for a solo non-coder?** **The monitoring tool: yes — it already works and is safe.** **The full vision: no, not as currently scoped.** The brain/backtester/multi-agent ambitions are exactly where a solo non-coder gets quietly misled by their own system — green tests on unproven claims, "learning" that forgets, a kill-switch that's a status light, a risk gate a monster pick steps around. The honest move is to **shrink the surface to what's durable and true**, then grow deliberately.

### KILL (3) — remove or stop pretending *now* (currently misleading or net-negative)
1. **The "backtester-proven" claim and its test-hardening** (#11/#12/#25) — kill the "proven" language in `test_exclusions.py` and docs **today**; rebuild the engine later only if you'll fund a real point-in-time universe. Keeping the claim is actively misleading.
2. **The auto-commit of `config/weights.json` to `main`** (#6/#27) — it writes a file nothing reads and violates human-in-loop for zero benefit. Kill the auto-commit entirely; keep only a PR-gated path.
3. **The "🧠 Brain learned X this week" narrative + ornamental Pillar/brain modules** (#13) — kill the *claim* now and archive `meta_brain`/`agent_memoir`/`self_awareness`/`smell_faculty` to an `experimental/` namespace until they have a durable runtime role. They add cosplay, not picks.

### DEFER (3) — genuinely good, but value depends on the foundation first
1. **Multi-agent ensemble with a referee** (#13 done right) — a real technical/fundamental/news/macro→referee design with defined I/O. Worth building, but only after the spine is durable; defer until Tasks 1–5 land.
2. **RAG that actually cites chunks per pick** (#10) — promote from decoration to influence-with-citation. Defer until explainability (#19) is structured (Task 9).
3. **Adversarial regime testing** (#26) + per-regime crisis backtests (#12) — defer until the backtester (Task 6) is trustworthy; testing on 2008/2020 is meaningless on a survivorship-biased engine.

*The difference: **Kill** = remove the claim today because it's misleading or net-negative. **Defer** = a good idea whose payoff requires the durable, honest foundation to exist first.*

---
*End of audit. Coverage: Stages 1A–1F inventory + 4 deep-dives (backtester, weights-tracking, idea-generators, brain-persistence) + cross-cutting (cost/security/timezone/atomicity) + full 29-item alignment. All severities carried as staged: P0 systemic-statelessness · P0 unified-broken-brain · P1 picks_csv-corruption · ⚠️-HIGH BUG-M97 · HIGH backtester-unproven · HIGH kill-switch-observe-mode · MED cost/dep/timezone/injection. Corrections applied: Alpaca-creds → non-issue; "160/wk" → ~3,200 calls/wk (~$25/wk ceiling); "85% unsafe writers" → journals atomic, picks_csv is the real gap; timezone same-file UTC-vs-ET inconsistency confirmed-in-code, "~8 bugs" scope prior-audit-doc-unverified. Output-only mode honored — no files written, no issues opened.*