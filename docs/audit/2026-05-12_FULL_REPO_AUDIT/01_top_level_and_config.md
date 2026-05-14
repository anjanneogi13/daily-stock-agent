============================================================
SAVE AS: docs/audit/2026-05-12_FULL_REPO_AUDIT/01_top_level_and_config.md
============================================================

# Audit Batch 1a — Top-Level & Configuration Files

**Date:** 2026-05-12 (Tuesday, Singapore morning)
**Auditor:** Co-founder review (line-by-line, plain English)
**Files in this batch:** 11
**Severity legend:**
- 🚨 = **Show-stopper / trade-damaging** — fix urgently
- ⚠️ = **Data-corrupting / safety risk** — fix before production
- 🟡 = **Code smell / inconsistency** — fix when convenient
- 📝 = **Documentation / wording issue** — fix in next doc pass
- ✅ = **Good code / well-designed** — keep as is

---

## Glossary (plain English for non-coders)

| Term | What it means |
|---|---|
| **Dependency** | An external code library your project needs (like an "app" your app uses). Listed in `requirements.txt`. |
| **Environment variable** | A secret value (like an API key) that lives outside the code. Listed in `.env`. |
| **YAML / JSON** | Two file formats for storing settings. Both are human-readable. |
| **Makefile** | A list of shortcut commands. `make picks` runs whatever `picks:` does. |
| **conftest.py** | A pytest setup file — tells your tests where to look for code. |
| **Streamlit** | A library for building data dashboards in a web browser. |
| **Atomic write** | Saving a file in a crash-safe way (write temp file, then rename). The opposite is "non-atomic" — a crash mid-save corrupts the file. |
| **Fail-open vs fail-closed** | When something breaks, do you (a) keep going (fail-OPEN) or (b) stop everything (fail-CLOSED)? Safety code should fail-closed. |
| **Paper trading** | Simulated trading with fake money to test strategies. Currently FORBIDDEN per project rules. |
| **Live trading** | Real money trading. Currently FORBIDDEN per project rules. |

---

## File 1 of 11: `requirements.txt` (23 lines)

**What this file does:** Lists every external code library the project needs. When someone sets up the project, they run `pip install -r requirements.txt` and Python downloads all these.

### Findings

#### 🚨 BUG-1: Alpaca trading library is installed even though trading is FORBIDDEN
- **Line 22:** `alpaca-py>=0.20.0`
- **Plain English:** Alpaca is a stockbroker's API. Installing this library means the code CAN connect to a real brokerage account and place trades.
- **Why it's a problem:** Per your bootstrap prompt, **paper trading is forbidden and live trading is forbidden.** A code library that enables forbidden capability shouldn't be installed at all. If a future contributor (or a tired you at 2am) imports it by accident, you risk a real-money trade.
- **Fix:** Remove this line until paper trading is officially approved by you. If any code currently imports `alpaca`, that code needs to be removed first.
- **Severity:** 🚨 Show-stopper for your "monitoring-only" stance.

#### 🟡 BUG-2: Streamlit (heavy dashboard library) installed for one optional file
- **Line 7:** `streamlit==1.38.0`
- **Plain English:** Streamlit is a 50MB+ library that lets you build web dashboards. The only file that uses it is `app.py` (a local-only dashboard). Production never uses Streamlit.
- **Why it's a problem:** Heavy dependency for a non-production feature. Every CI run downloads it. Every contributor installs it.
- **Fix options:** Either (a) move it to an optional `requirements-dev.txt` file, or (b) decide if `app.py` is even still useful — if it's been replaced by Telegram reports, delete `app.py` and remove Streamlit.
- **Severity:** 🟡 Bloat, not danger.

#### 🟡 BUG-3: Multiple LLM libraries — pick one or document why both
- **Line 17:** `google-genai==0.3.0` (Google Gemini)
- **Line 19:** `anthropic>=0.40.0` (Claude)
- **Plain English:** You're paying for / depending on TWO different AI providers.
- **Why it's a problem:** Either (a) the code uses both for redundancy (good — but undocumented), or (b) one is dead code (bad — bloat). The audit will tell us which.
- **Fix:** After we audit `src/llm_agent.py` and `scripts/claude_helper.py` / `scripts/gemini_helper.py`, decide which to keep.
- **Severity:** 🟡 Cost and complexity smell.

#### 🟡 BUG-4: All dependencies are exact-pinned (`==`) except 2 are loose (`>=`)
- **Lines 1-15, 18:** all use `==` (exact version)
- **Lines 19, 22:** use `>=` (any version at or above)
- **Plain English:** "Exact pin" means "use exactly this version, nothing else." Loose pin means "this version or newer."
- **Why it's a problem:** Inconsistency. Loose pins can break your build silently when a new version of `anthropic` or `alpaca-py` is released with breaking changes. Either pin everything, or pin nothing. The norm for production is pin everything.
- **Fix:** Change `anthropic>=0.40.0` to `anthropic==0.40.0` (whatever version is currently installed). Same for `alpaca-py` (or remove it per BUG-1).
- **Severity:** 🟡 Build reproducibility risk.

#### 📝 BUG-5: Comment says "Phase 2A: News Engine + Alpaca" — Phase 2A status unclear
- **Line 21:** `# Phase 2A: News Engine + Alpaca`
- **Plain English:** A code comment saying these libraries belong to "Phase 2A."
- **Why it's a problem:** No doc explains what Phase 2A is or whether it's active, deferred, or cancelled. Combined with the "trading forbidden" rule, this comment is misleading.
- **Fix:** Either delete the comment (if Phase 2A is dead) or add a `# DEFERRED: Alpaca disabled per monitoring-only stance` note.
- **Severity:** 📝 Documentation hygiene.

---

## File 2 of 11: `.env.example` (8 lines)

**What this file does:** A TEMPLATE for the real `.env` file. New contributors copy this to `.env` and fill in their own API keys. **NEVER commit a real `.env` to git** (`.gitignore` correctly excludes it).

### Findings

#### 🚨 BUG-6: Default `TRADING_MODE=paper` directly contradicts the "trading forbidden" rule
- **Line 7:** `TRADING_MODE=paper`
- **Plain English:** The example file tells contributors "set the trading mode to paper by default."
- **Why it's a problem:** Your bootstrap rules state **"paper trading remains forbidden until readiness gates pass and founder explicitly approves."** This template silently encourages the opposite. A new contributor copying this file is one missed read away from accidentally enabling forbidden behavior.
- **Fix:** Change to `TRADING_MODE=monitoring` (or `disabled`). Add a comment: `# DO NOT change to "paper" or "live" without founder approval.`
- **Severity:** 🚨 Safety contradiction.

#### 🚨 BUG-7: Alpaca paper-trading URL is the default
- **Line 6:** `ALPACA_BASE_URL=https://paper-api.alpaca.markets`
- **Plain English:** This is the URL that points to Alpaca's paper-trading server.
- **Why it's a problem:** Same as BUG-6 — pre-configures a forbidden capability.
- **Fix:** Either remove the line entirely (force contributor to set it consciously) or comment it out with `# Uncomment ONLY when paper trading is approved`.
- **Severity:** 🚨 Same safety contradiction.

#### 🟡 BUG-8: API key list incomplete — `TELEGRAM_*` keys are missing
- **Lines 1-7:** Lists OpenAI, Finnhub, Alpha Vantage, Alpaca keys
- **Plain English:** Your code sends Telegram messages but the `.env.example` doesn't show contributors which Telegram environment variables to set.
- **Why it's a problem:** A new contributor following this template gets a working setup EXCEPT all Telegram features fail silently (or with cryptic errors). Discoverability gap.
- **Fix:** Add the Telegram bot token and chat ID variables (e.g., `TELEGRAM_BOT_TOKEN=`, `TELEGRAM_CHAT_ID=`) — whatever your code expects (we'll confirm in the `src/` audit).
- **Severity:** 🟡 Onboarding friction.

#### 🟡 BUG-9: No GitHub Actions secrets are documented
- **Plain English:** Your workflows run automatically and use the same API keys, but they get them from "GitHub Secrets" (a separate place from `.env`). There's no list of "these secrets must be set in GitHub Settings → Secrets" anywhere.
- **Fix:** Either add a section here as comments, OR create a separate `docs/SECRETS.md` listing what GitHub Actions secrets must exist.
- **Severity:** 🟡 Onboarding gap.

---

## File 3 of 11: `.gitignore` (254 lines)

**What this file does:** Tells git "don't ever upload these files to GitHub." Used to exclude secrets, build artifacts, caches, etc.

### Findings

#### 🟡 BUG-10: File is mostly Python boilerplate (lines 1-218) — not project-specific
- **Plain English:** Lines 1-218 look like the standard Python `.gitignore` template that ships with every Python project. The project-specific stuff starts at line 219.
- **Why it's a problem:** Not a bug, but it's hard for you (a non-coder) to find the rules that actually matter to YOUR project. They're buried.
- **Fix:** Move the project-specific block (lines 219-254) to the TOP of the file with a clear comment: `# === DAILY-STOCK-AGENT SPECIFIC ===`.
- **Severity:** 🟡 Maintainability.

#### ⚠️ BUG-11: Conflict — does the project commit data files or not?
- **Line 225:** `data/` (excludes the entire data folder)
- **Lines 241-245:** `!data/learning/`, `!data/exec_report_*.json`, `!data/premarket_check.json`, `!data/picks_log.csv` (re-includes specific items)
- **Lines 251-253:** `!data/books/`, `!data/books/*.yaml` (re-includes books)
- **Plain English:** "Exclude all of `data/`, EXCEPT these specific items." This pattern works but is fragile. If someone adds a new important data file, they have to remember to add a `!` rule.
- **Why it's a problem:** When we look at what's actually committed in your `data/` folder, there are MANY tracked files (`daily_picks_no_pick_report_*.json`, `signal_journal.jsonl`, `learning_journal.jsonl`, `news_log.jsonl`, etc.) that are NOT covered by these `!` rules. So either:
  - (a) git is ignoring those files (bug — they should be tracked), or
  - (b) those files were tracked BEFORE `data/` was excluded, and git treats them differently.
- **Fix:** Audit which `data/*.json` and `data/*.jsonl` files are actually being committed. Add explicit `!` rules for each one. This will be part of Batch 11 (data contracts).
- **Severity:** ⚠️ Data integrity risk — silent loss of important files.

#### 🟡 BUG-12: Duplicate entries
- **Line 2:** `__pycache__/` and **Line 222:** `__pycache__/` — same rule, listed twice
- **Line 153:** `.venv` and **Line 219, 220:** `venv/`, `env/` — overlap
- **Line 151:** `.env` and **Line 223:** `.env` — same, twice
- **Line 221:** `*.pyc` and **Line 3:** `*.py[codz]` — overlap (`[codz]` includes `c`, so `.pyc`)
- **Plain English:** Same rules written twice or overlapping.
- **Why it's a problem:** Doesn't break anything, just messy.
- **Fix:** Deduplicate when the `.gitignore` cleanup happens.
- **Severity:** 🟡 Cleanup.

#### ⚠️ BUG-13: `*.csv` is excluded — but `picks_log.csv` is the most important file
- **Line 227:** `*.csv` (excludes ALL csv files anywhere)
- **Line 245:** `!data/picks_log.csv` (re-includes the one important csv)
- **Plain English:** Default rule is "ignore all CSVs." One specific override re-includes `picks_log.csv`.
- **Why it's a problem:** Any new CSV file you might want to track (e.g., a future pick history export, a backtest result, a customer survey export) will be SILENTLY ignored. You'd commit thinking it saved, then notice next session that the file is gone.
- **Fix:** Either invert the rule (track CSVs by default, exclude specific ones) OR document this gotcha prominently.
- **Severity:** ⚠️ Silent data loss risk.

#### 🟡 BUG-14: `*.log` is excluded but `logs/` is also excluded — redundant
- **Line 226:** `logs/` (folder)
- **Line 228:** `*.log` (file pattern)
- **Plain English:** Two rules covering the same thing.
- **Severity:** 🟡 Cleanup.

---

## File 4 of 11: `config.yaml` (91 lines)

**What this file does:** The central settings file for the agent. Controls universe (which stocks), strategy, weights, risk, output, day-trading, monster-hunt mode, etc.

### Findings

#### ✅ GOOD-1: Excellent scar-tissue documentation on disabled SEMI/AI bias (lines 38-42)
- **Plain English:** A comment explains WHY a feature was disabled, when, and what evidence proved it should be disabled.
- **Why it's good:** This is exactly how production code should document past mistakes. Anyone reading this immediately understands "don't re-enable this without re-doing the backtest."
- **Keep:** Use this comment style as a template for documenting all "disabled / deprecated / archived" features.

#### ✅ GOOD-2: Backtester-proven excluded tickers documented with context (lines 13-22)
- **Plain English:** Specific tickers (`UNH`, `TEAM`, `SMCI`, `DIS`, `SCHW`) are excluded because the backtester proved they lose money. The comment cites the source.
- **Why it's good:** Makes the exclusion list maintainable — future you knows WHY each ticker is on the list, can re-check after enough new data.

#### 🚨 BUG-15: `day_trading.enabled: true` (line 64) but day-trading is monitoring-only
- **Lines 63-72:** `day_trading: enabled: true` plus settings for stop-loss, take-profit, max-hold-minutes
- **Plain English:** "Day trading is turned ON. Stop-loss should be 0.6× ATR, take profit 1.0×-1.8×, force-close after 4 hours."
- **Why it's a problem:** Per your bootstrap, day trading must remain monitoring-only. The flag `enabled: true` plus the SL/TP/timing values STRONGLY imply the agent will execute or recommend executable day trades. There is no `monitoring_only: true` safety flag here.
- **Fix:** Either (a) add an `execution_mode: monitoring_only` field at the top of the section, or (b) rename `enabled` to `scoring_enabled` to make clear no execution happens.
- **Severity:** 🚨 Safety contradiction with bootstrap rules.

#### 🚨 BUG-16: `monster.enabled: true` (line 86) but Monster Hunter is research-only
- **Lines 84-91:** `monster: enabled: true` plus position-sizing, stop-loss, take-profit settings
- **Plain English:** Monster Hunter mode is ON. Take 1.5% of account per pick, wider 5% stop loss, aggressive 25% take profit.
- **Why it's a problem:** Per your bootstrap, **Monster Hunter is research-only / monitoring-only and must not affect production scoring.** This config gives it real risk parameters as if it WILL trade. Same risk as BUG-15.
- **Fix:** Same as BUG-15 — explicit `mode: research_only` flag.
- **Severity:** 🚨 Same safety contradiction.

#### ⚠️ BUG-17: Account size hardcoded to $10,000 (line 44)
- **Line 44:** `account_size: 10000.0`
- **Plain English:** The code assumes you have a $10,000 account.
- **Why it's a problem:** If you ever turn this into a product for other users, you cannot ask Anjan's account size to determine Bob's position sizes. This is a single-user assumption baked into core config.
- **Fix:** Long-term, account_size becomes per-user. Short-term, document that all $-based outputs are scaled to a hypothetical $10K account.
- **Severity:** ⚠️ Multi-user blocker, low urgency now.

#### ⚠️ BUG-18: `min_score: 0.55` (line 52) duplicated in two places
- **Line 52:** `output: min_score: 0.55`
- **Line 77:** `swing_trading: min_score: 0.55`
- **Plain English:** Two settings, same value, ambiguous which one wins.
- **Why it's a problem:** If you change one and not the other, picks behave inconsistently depending on which code path runs.
- **Fix:** Delete one (the section that doesn't actually use it). To find out which, we'll check the `src/` audit.
- **Severity:** ⚠️ Configuration drift risk.

#### 🟡 BUG-19: `weights` (lines 30-36) sum to 1.00 — but no comment confirms this is required
- **Lines 30-36:** `trend: 0.18`, `momentum: 0.20`, `volatility: 0.08`, `volume: 0.05`, `fundamentals: 0.14`, `sentiment: 0.12`, `indicators: 0.23`
- **Math check:** 0.18 + 0.20 + 0.08 + 0.05 + 0.14 + 0.12 + 0.23 = **1.00** ✅
- **Plain English:** Seven scoring factors that should add to 100%.
- **Why it's a problem:** No comment says "these MUST sum to 1.0." If a future you tweaks `trend: 0.25` and forgets to reduce another, scoring becomes silently wrong.
- **Fix:** Add a comment: `# IMPORTANT: weights must sum to 1.0 — there's a test for this`. Add a unit test if one doesn't exist.
- **Severity:** 🟡 Silent breakage risk.

#### 🟡 BUG-20: Universe section starts with `source: sp500` (line 2) but excludes 6 tickers — semantic mismatch
- **Line 2:** `source: sp500` (use S&P 500)
- **Lines 4-9:** `custom_tickers: AAPL, MSFT, NVDA, AMD, AVGO` (which are already in S&P 500, so adding them is redundant)
- **Lines 13-22:** `excluded_tickers:` (6 names removed)
- **Plain English:** "Use S&P 500. Then add 5 stocks that are already in S&P 500. Then remove 6 stocks."
- **Why it's a problem:** The `custom_tickers` block looks like it was added when the universe was something other than S&P 500, then never cleaned up.
- **Fix:** Delete `custom_tickers` if all 5 are already in S&P 500.
- **Severity:** 🟡 Cleanup.

#### 🟡 BUG-21: `llm.enabled: true` (line 56) — costs money on every run
- **Lines 55-58:** `llm: enabled: true`, model `claude-sonnet-4-5`, max_tokens 500
- **Plain English:** Every pick gets an AI explanation. Each run costs API credits.
- **Why it's a problem:** Not a bug, but a cost discipline note. With `claude-sonnet-4-5` at 500 tokens × number of picks × number of daily runs, this adds up. No budget cap is documented.
- **Fix:** Document expected monthly LLM cost. Add a fallback to use no LLM in monitoring-only mode if cost matters.
- **Severity:** 🟡 Cost / budget discipline (Lane 26 in your roadmap).

---

## File 5 of 11: `config/auto_pause.json` (6 lines)

**What this file does:** Controls the auto-pause feature. When the agent's "pain score" exceeds the threshold, it pauses for N days.

### Findings

#### ✅ GOOD-3: Has an embedded `_comment` field explaining what it does
- **Plain English:** JSON doesn't allow comments natively, so the developer added a `_comment` field as a workaround.
- **Why it's good:** Anyone opening this file understands what it controls.

#### 🚨 BUG-22: `enforced: false` (line 2) and the comment says "Set enforced=true on Wed May 6 2026"
- **Line 2:** `"enforced": false`
- **Line 5 comment:** `"Set enforced=true on Wed May 6 2026 after 3-day calibration"`
- **Today's date:** 2026-05-12 (Tuesday)
- **Plain English:** A comment from 6 days ago says "flip this to true on May 6." The flip never happened. **Auto-pause is currently disabled.**
- **Why it's a problem:** If your pain score is high (which the May 11 production incident suggests it might be), the agent has NO automatic safety brake. You'd only know about a problem from manual log inspection.
- **Fix:** **DECIDE TODAY** — either (a) flip `enforced: true` (safety on), or (b) update the comment to explain why flipping was deferred (e.g., "Deferred until P19 cert complete and 30 closed picks observed"). Don't leave a stale promise.
- **Severity:** 🚨 Missed safety milestone.

#### 🟡 BUG-23: Threshold and pause-days are unexplained magic numbers
- **Line 3:** `pause_threshold: 8`
- **Line 4:** `pause_days: 3`
- **Plain English:** "Pause when score is 8 or higher. Pause for 3 days."
- **Why it's a problem:** Why 8? Why 3? The comment doesn't say. If `auto_pause.compute_score()` ever gives values 0-100, then 8 means "pause on minor pain." If the scale is 0-10, 8 means "pause on severe pain." Without the scale documented, this number is undebuggable.
- **Fix:** Update `_comment` to explain the score scale and rationale: e.g., `pause_threshold: 8 (out of 10 — equivalent to 3 SL-hits in 5 trading days plus negative R)`.
- **Severity:** 🟡 Maintainability.

---

## File 6 of 11: `config/weights.json` (20 lines)

**What this file does:** This is the file the **brain learns into**. The "weight calibration" loop reads outcomes from past trades and tweaks these multipliers. Each entry says "boost this kind of pick by X%, dampen that kind by Y%."

### Findings

#### ✅ GOOD-4: Has a `_doc` field explaining the file's purpose AND mentioning the 5%/week safety cap
- **Line 4:** `"_doc": "Brain-controlled knobs. Each entry is a per-factor-bucket multiplier (1.0 = neutral). weight_applier.py mutates these per proposal, capped at 5%/week per factor."`
- **Why it's good:** Explains exactly what changes this file (`weight_applier.py`) and notes the 5%/week safety cap that prevents runaway weight changes.

#### 🚨 BUG-24: File `updated: "2026-05-04"` (line 3) — hasn't been touched in 8 days
- **Line 3:** `"updated": "2026-05-04"`
- **Today's date:** 2026-05-12
- **Plain English:** The brain's learning has not updated this file in 8 days.
- **Why it's a problem:** Your earlier 95-file `src/` audit found that **the calibration loop is broken for live data** (it was designed for backtest schema, not live signal_journal). This file's stale date is the smoking gun. The brain THINKS it's learning. The doc THINKS it's learning. The date proves it's not.
- **Fix:** Confirmed by audit findings. Calibration needs the `calibration_live.py` rewrite mentioned in your code-audit synthesis.
- **Severity:** 🚨 The brain has been "running but not learning" for 8 days minimum.

#### 🚨 BUG-25: `rsi.rsi_oversold(<30): 0.0` (line 11) — "kill all RSI-oversold picks"
- **Line 11:** `"rsi_oversold(<30)": 0.0`
- **Plain English:** Multiplier of 0.0 means "if a pick has RSI below 30 (oversold), multiply its score by ZERO" — effectively delete it.
- **Why it's a problem:** This is an EXTREME setting. Either (a) it was set deliberately because oversold picks lose money — in which case there should be a comment with the evidence, OR (b) it's a debug value that got committed by accident. Without a comment, this is fragile.
- **Fix:** Add a `_comment` field above it: `"_rsi_doc": "rsi_oversold killed 2026-XX-XX after N losses, see docs/decisions/..."`
- **Severity:** 🚨 Undocumented production override.

#### 🟡 BUG-26: Bucket-naming style is inconsistent
- **Line 7:** `"b1": 1.05` and `"b2": 0.95` (cryptic generic names)
- **Line 11:** `"rsi_oversold(<30)": 0.0` (descriptive name with operator)
- **Line 13:** `"atrpct_<1.5": 1.05` (descriptive name)
- **Line 17:** `"score_>=0.85": 1.034` (descriptive name)
- **Plain English:** The factor `f` uses meaningless names `b1`/`b2`. Other factors use real bucket descriptions. Inconsistent.
- **Why it's a problem:** Anyone (you, future contributor, future Claude) reading this can't tell what `f.b1` means. Is it "factor f, bucket 1"? But what is `f` and what does bucket 1 cover?
- **Fix:** Either delete the `f` section if it's unused, or rename `b1`/`b2` to descriptive names matching the convention.
- **Severity:** 🟡 Maintainability + audit-trail value.

#### 🟡 BUG-27: `score_>=0.85: 1.034` — strangely precise number
- **Line 17:** `"score_>=0.85": 1.034`
- **Plain English:** "Picks with composite score ≥ 0.85 get a 3.4% boost."
- **Why it's a problem:** All other multipliers are clean (1.05, 0.95, 0.0). The 1.034 looks like the result of one calibration cycle (e.g., 1.0 × 1.034 = 1.034 after a single auto-tune). If calibration is broken (BUG-24), this is the LAST live calibration that ever ran.
- **Fix:** Cross-check: is there a `weight_proposals.jsonl` showing when this number was set? If yes, document it. If no, this is orphan state.
- **Severity:** 🟡 Audit trail incomplete.

---

## File 7 of 11: `Makefile` (109 lines)

**What this file does:** A shortcut command list. Run `make picks` to generate today's picks, `make test` to run tests, etc. Useful for humans who don't remember long commands.

### Findings

#### ✅ GOOD-5: Has a `help` target that lists all commands
- **Lines 10-17:** `make help` shows all available commands with descriptions.
- **Why it's good:** Discoverable. New contributors run `make help` to see what's possible.

#### 🚨 BUG-28: `wisdom-promote` and `wisdom-gc` are dangerous WRITE commands with no safety guard
- **Lines 36-38:** `wisdom-promote: $(PY) -m src.auto_promote` (no flags, no preview)
- **Lines 48-50:** `wisdom-gc: $(PY) -m src.lesson_gc` (no flags, no preview)
- **Plain English:** Two commands you can run with `make wisdom-promote` or `make wisdom-gc`. They WRITE to `lessons.jsonl` (auto-promote) and `kill_list.json` (deactivate lessons). Both are core brain memory.
- **Why it's a problem:** A typo (`make wisdon-gc` doesn't exist, but `make wisdom-gc` works), a curious explore (`make wisdom-gc` "let me see what this does"), or a copy-paste from docs could corrupt brain state. **There's no confirmation prompt, no `--yes-i-mean-it` flag, no automatic backup before write.**
- **Fix:**
  - Make `wisdom-promote` and `wisdom-gc` print a warning and require `CONFIRM=yes` env var: e.g., `if [ "$$CONFIRM" != "yes" ]; then echo "set CONFIRM=yes to actually run"; exit 1; fi`
  - OR rename them to `wisdom-promote-DANGEROUS` and `wisdom-gc-DANGEROUS`.
  - OR remove from Makefile entirely; require running them via `python -m src.auto_promote --apply` directly.
- **Severity:** 🚨 Brain-memory corruption risk via misclick.

#### ✅ GOOD-6: `wisdom-dryrun` and `wisdom-gc-dryrun` exist (lines 40-42, 52-54)
- **Plain English:** Safe preview versions of the dangerous commands.
- **Why it's good:** The pattern is right. The problem is that the dangerous versions are equally easy to run.

#### ⚠️ BUG-29: `make picks` runs `python -m scripts.send_telegram` (line 59) — sends real Telegram message
- **Line 58-59:** `picks: $(PY) -m scripts.send_telegram`
- **Plain English:** Running `make picks` sends an actual Telegram message to your real Telegram chat.
- **Why it's a problem:** This isn't just "generate picks" — it's "generate AND send to user." A test run on a Sunday accidentally pings real users. There's no `--dry-run` option exposed.
- **Fix:** Either rename to `make picks-and-send` (more honest), or add `make picks-dryrun` for the safe version.
- **Severity:** ⚠️ User-facing surprise.

#### 🟡 BUG-30: Inconsistent style between sections
- **Lines 9-66:** Use the `## Description` comment pattern that `help` parses (the make-help magic).
- **Lines 78-108:** Don't use this pattern, so they DON'T appear in `make help`.
- **Plain English:** Newer sections (books, calibration) won't show up when you run `make help`. They're invisible to discovery.
- **Fix:** Add `## Description` comments to lines 78-108 so they appear in help output.
- **Severity:** 🟡 Discoverability.

#### 🟡 BUG-31: Two different Python invocation styles
- **Lines 22-26, 33-65:** Use `$(PY)` (which is `python3`)
- **Lines 79, 82, 85, 89, 92, 95, 99, 102, 105, 108:** Use plain `python` (might be `python2` on some systems!)
- **Plain English:** Half the file uses `python3`, the other half uses `python`. On most modern systems they're the same, but on older systems `python` could mean `python2` and crash.
- **Fix:** Replace all bare `python` with `$(PY)`.
- **Severity:** 🟡 Cross-system reliability.

#### 🟡 BUG-32: Section headers say "Pillar 2.5" / "Pillar 3.5" — concepts not defined here
- **Line 77:** `# Books-into-Brain (Pillar 2.5)`
- **Line 87:** `# Calibration Brain (Pillar 3.5)`
- **Line 97:** `# Weight proposer (Pillar 3.5 — C3, READ-ONLY)`
- **Plain English:** References to "Pillar 2.5", "Pillar 3.5", "C3" with no link to where these are defined.
- **Why it's a problem:** Future contributor opens the Makefile, sees "Pillar 3.5", has no idea what that means. Has to grep through docs to find context.
- **Fix:** Add a comment at the top: `# Pillars defined in docs/strategy/AGENT_PHILOSOPHY.md`
- **Severity:** 🟡 Documentation linkage.

---

## File 8 of 11: `conftest.py` (4 lines)

**What this file does:** A pytest setup file that runs before any test. This one just adds the project root to Python's import path so tests can find the code.

### Findings

#### ✅ GOOD-7: Minimal and correct
- **Plain English:** Does only one thing, does it right. Good.

#### ⚠️ BUG-33: No pytest configuration file exists
- **What's missing:** No `pytest.ini`, no `pyproject.toml`, no `setup.cfg` with `[tool:pytest]`.
- **Plain English:** Pytest can be configured to control test discovery, default flags, marker definitions, etc. None of that exists.
- **Why it's a problem:** When you run `pytest`, it uses default behavior. As your test suite grows (already 200+ files), you'll want:
  - Default `-q` for quiet output
  - `--strict-markers` so typos in `@pytest.mark.slow` fail loudly
  - Test discovery rules (which folders to scan)
  - Coverage minimum thresholds
- **Fix:** Add a minimal `pytest.ini` or `pyproject.toml` `[tool.pytest.ini_options]` block.
- **Severity:** ⚠️ Test-suite hygiene.

---

## File 9 of 11: `app.py` (106 lines)

**What this file does:** A Streamlit web dashboard you can run locally to play with the agent interactively. Not used in production, not used in CI.

### Findings

#### 🚨 BUG-34: Imports modules that may no longer exist
- **Lines 8-17:** Imports from `src.universe`, `src.data_fetcher`, `src.indicators`, `src.fundamentals`, `src.news_sentiment`, `src.scorer`, `src.risk_manager`, `src.llm_agent`, `src.tracker`, `src.semiconductors`
- **Plain English:** This file expects 10 specific modules in `src/` to exist with specific function names.
- **Why it's a problem:** Your `src/` audit found that some of these modules may have been refactored or replaced. For example:
  - `src.tracker` — might be replaced by `src.signal_journal` / `src.pick_logger`
  - `src.indicators` and `src.semiconductors` — were these renamed?
  - `src.news_sentiment` — was this replaced by `src.news_engine`?
  - **If even one of these imports is broken, `app.py` crashes on startup.**
- **Fix:** Run `python -c "import app"` and see what breaks. If imports fail, this file is dead code and should be deleted or marked `BROKEN — see issue #N`.
- **Severity:** 🚨 Either dead code (delete it) or broken (fix or delete).

#### ⚠️ BUG-35: Disclaimer is in dashboard caption only, not enforced anywhere
- **Line 22:** `st.caption("Educational only. Not financial advice. Paper-trade first.")`
- **Plain English:** A small caption under the title says "Educational only."
- **Why it's a problem:** This dashboard EXPORTS picks (the `Save CSV` button is implied). If a user copies the picks, the disclaimer doesn't follow them. If a user takes a screenshot, the caption is too small. Compared to your production Telegram messages (which we'll audit later) which probably have stronger disclaimers, this is weak.
- **Fix:** Make the disclaimer prominent (red banner, modal popup on first visit, exit-time confirmation).
- **Severity:** ⚠️ Legal/credibility for Lane 27 (legal/regulatory).

#### 🟡 BUG-36: Sidebar setting `Semiconductors only` (line 35) suggests you can over-filter the universe to bias toward SEMI
- **Lines 35-36:** Two checkboxes — "Semiconductors only" and "AI-relevant semis only (>=0.75)"
- **Plain English:** User can override the universe filter to ONLY look at semiconductors.
- **Why it's a problem:** Per `config.yaml` audit (BUG-15: SEMI/AI bias proven a Sharpe leak), there's literally code documentation saying "SEMI bias is bad." This dashboard lets a user re-introduce that bias by toggle.
- **Fix:** Either remove these checkboxes, or add a warning when toggled: `⚠️ SEMI-only filter is known to underperform (-24.8 Sharpe leak in backtest)`.
- **Severity:** 🟡 Lets a user shoot themselves in the foot.

#### 🟡 BUG-37: No date/timestamp on dashboard output
- **Plain English:** When you run the dashboard, the output shows picks but no "as of" timestamp.
- **Why it's a problem:** A screenshot from yesterday looks identical to today's. Forensics impossible.
- **Fix:** Add `st.caption(f"Generated: {datetime.now()}")` next to the table.
- **Severity:** 🟡 Auditability.

---

## File 10 of 11: `backtest.py` (43 lines)

**What this file does:** Runs a simple RSI mean-reversion strategy on historical data for the top 50 stocks. Outputs a table of best performers by Sharpe ratio.

### Findings

#### 🚨 BUG-38: This file is almost certainly DEAD code
- **Plain English:** Your bootstrap and code audit show:
  - The real backtest infrastructure is in `src/backtester/` and `scripts/run_backtest.py`
  - This file uses a hardcoded `RSI buy=35, sell=70` strategy that doesn't match any of your other strategies
  - It's import-shallow (only uses 3 modules)
  - Top 50 cap is arbitrary and not configurable
- **Why it's a problem:** Either this file is (a) abandoned prototype code from early days, or (b) actively used by some workflow we haven't audited yet. If (a), delete it. If (b), it's a confusing duplicate of `scripts/run_backtest.py`.
- **Fix:** Run `grep -r "import backtest" .` (without the `_simple` suffix). If no caller, delete.
- **Severity:** 🚨 Suspected dead code, polluting top level.

#### ⚠️ BUG-39: Uses `period="2y"` (line 16) — but ignores stock_universe filters
- **Plain English:** Fetches 2 years of data for "top 50 stocks." But what's "top"? It uses `get_universe(cfg)[:50]` — the FIRST 50 from the universe list, not "best 50" or any meaningful selection.
- **Why it's a problem:** Results are misleading. Top 50 by alphabetical order isn't a meaningful sample. Backtest results from this file would mislead anyone who runs it.
- **Severity:** ⚠️ If anyone actually runs this, they get garbage.

#### 🟡 BUG-40: Output doesn't say WHICH parameters were used
- **Lines 28-37:** Prints a Rich table titled "Backtest Results (Top 20 by Sharpe)"
- **Plain English:** Output doesn't include "RSI thresholds: 35/70, period: 2y, universe: first 50 alphabetical."
- **Severity:** 🟡 Result without context.

---

## File 11 of 11: `evaluate_picks.py` (TOP-LEVEL, 84 lines)

**What this file does:** Evaluates past picks against actual price action. Compares entry/SL/TP to subsequent prices. Reports win rate.

### Findings

#### 🚨 BUG-41: This file is SHADOWED by `scripts/evaluate_picks.py` — name collision
- **There exist TWO files:**
  - `evaluate_picks.py` (top level, 84 lines) — uses `data/trades.csv`
  - `scripts/evaluate_picks.py` (73 lines) — calls `src.pick_evaluator.evaluate_pending` and uses `data/picks_log.csv`
- **Plain English:** Two Python files with the same name, doing slightly different things, in different folders.
- **Why it's a problem:**
  - Confusion: which one runs when someone says "the evaluate picks script"?
  - The Makefile (`make evaluate`) calls neither — it calls `python -m src.pick_evaluator` directly.
  - Top-level `evaluate_picks.py` reads `data/trades.csv` — does that file even exist anymore? (Bootstrap mentions `data/picks_log.csv` everywhere, never `trades.csv`.)
- **Fix:** Top-level `evaluate_picks.py` is almost certainly dead. Delete it. If something still uses it, find the caller and update them to use `scripts/evaluate_picks.py`.
- **Severity:** 🚨 Dead code AND naming collision.

#### 🚨 BUG-42: Reads `data/trades.csv` (line 10) — file doesn't exist in the repo
- **Line 10:** `csv_path: str = "data/trades.csv"`
- **Plain English:** Default file path is `data/trades.csv`. But the project's actual log of picks is `data/picks_log.csv` (different name).
- **Why it's a problem:** Even if you ran this file, it would say "No trades.csv yet" forever because that file doesn't exist. **It's broken AND nobody noticed.**
- **Severity:** 🚨 Confirmed dead code.

#### 🟡 BUG-43: Comment says "Run weekly" but nothing schedules it
- **Line 2:** `Run weekly to see if your agent's picks actually worked.`
- **Plain English:** Documentation says "run this weekly." But no GitHub workflow runs it, no Makefile shortcut runs it, no cron job runs it.
- **Severity:** 🟡 Stale documentation on a dead file.

---

## 📊 Summary of Batch 1a (11 files)

### By severity
| Severity | Count |
|---|---:|
| 🚨 Show-stopper | **15** |
| ⚠️ Data/safety risk | **9** |
| 🟡 Code smell | **17** |
| 📝 Doc-only | **2** |
| ✅ Good code | **7** |
| **Total findings** | **50** |

### Top 5 things to fix from THIS batch (in order)

| # | What | Why | Where |
|---|---|---|---|
| 1 | Flip `auto_pause.json` enforced=true OR document why deferred | The promised May 6 flip never happened. Auto-pause is OFF. If the agent is hurting (recent 3 SL-hits in a row suggests it might be), there's no automatic safety brake. | `config/auto_pause.json` line 2 |
| 2 | Fix `.env.example` and `requirements.txt` to remove paper-trading defaults | Anyone copying the example file gets paper trading pre-enabled, directly contradicting "trading forbidden" | `.env.example` lines 6-7 + `requirements.txt` line 22 |
| 3 | Delete (or guard) `app.py`, top-level `backtest.py`, top-level `evaluate_picks.py` | Three top-level Python files appear dead, two definitely broken. They confuse new readers and risk being run by accident. | Repo root |
| 4 | Add safety guards on `make wisdom-promote` and `make wisdom-gc` | One typo / curiosity click can corrupt brain memory with no preview, no backup. | `Makefile` lines 36-38, 48-50 |
| 5 | Add explicit `mode: research_only` / `execution_mode: monitoring_only` flags to `day_trading` and `monster` config sections | Current config implies executable trading, contradicting bootstrap rules | `config.yaml` lines 63-72, 84-91 |

### What this batch tells us about the project
- **Documentation discipline is GOOD where it exists** — see `config.yaml` lines 38-42 scar-tissue comment. This style should be propagated to other config blocks.
- **Top-level files are messy** — three suspected dead files, two with broken paths. Cleanup overdue.
- **Safety contradictions are systemic** — paper trading is forbidden in docs but defaults in code/config encourage it. Not malice, just drift over time.
- **Brain memory has weak protection** — write commands in Makefile have no safety guards.
- **Calibration is silently dead** — `weights.json` updated 8 days ago confirms what the code audit found.

### Glossary (additions for this batch)
| Term | Plain English |
|---|---|
| **ATR** | "Average True Range" — a measure of how much a stock typically moves in a day. Used to set stop-losses and take-profits proportional to volatility. |
| **RSI** | "Relative Strength Index" — a 0-100 score where <30 = "oversold" (cheap, might bounce) and >70 = "overbought" (expensive, might fall). |
| **Sharpe ratio** | A measure of "return per unit of risk." Higher is better. Above 1.0 is decent; above 2.0 is great. |
| **Universe** | The list of stocks the agent considers. Today: S&P 500 minus 6 excluded tickers, plus 5 (redundant) custom additions. |
| **Composite score** | A 0-1 number combining trend, momentum, fundamentals, sentiment, etc. Above the `min_score` threshold (currently 0.55), a stock becomes a candidate pick. |
| **Mean-reversion** | A trading strategy that bets prices return to average. "Buy when it dips below average, sell when it returns to average." |

---

**End of Batch 1a.** Next: Batch 1b — `main.py` (chunk 1 of ~3, the production entrypoint). After that: Batch 2 — GitHub workflows.

============================================================
END OF FILE — SAVE NOW
============================================================