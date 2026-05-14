# Batch 99 — 11-FILE BATCH — TRUE LINE-BY-LINE — SECTOR/SEMI + THEME GUARDRAILS + WISDOM CONSULTANT/COVERAGE + WoW + REPORTS

**Date:** 2026-05-14  
**Commit ref:** 37565c4d757a9f819a3ddd2059f73a51bb98af49  
**Files (11):** sector_benchmark (80) + sector_breakdown (84) + sector_pnl (60) + semiconductors (67) + theme_scoring_guardrails (95) + wow_trend (107) + wisdom_consultant (71) + wisdom_coverage (85) + weekly_review (352) + quarterly_report (276) + yearly_report (94)  
**Phase:** H continuation — SECTOR/SEMI INTELLIGENCE + WISDOM SURFACE + REPORTING TRIPTYCH  
**Total LOC audited this batch:** ~1,371 lines  
**Reliability:** ✅ All 11 files actually fetched at the listed commit and audited line-by-line.

---

## TOP HEADLINE FINDINGS

1. **SB-X1: sector_benchmark.py** (80) — **ALPHA-vs-SECTOR-NOT-SPY map**. **TAG_TO_ETF 8-key + SECTOR_TO_ETF 26-key dual lookup** with **explicit precedence (tag wins, then sector, then SPY fallback)**. **Bug #8a 2026-05-05 archaeology** (L46-48: "yfinance returns specific subsector strings, not generic top-level sectors. Without these, ~70% of picks fell through to SPY fallback, corrupting sector-relative alpha learning"). **Includes em-dash variants** (L53/L54) for yfinance format compat. **0 critical bugs.** ✅
2. **SBd-X1: sector_breakdown.py** (84) — **T28 weekly per-sector P&L panel.** `_enrich_with_sector_etf` mutates list in place (idempotent — skips already-tagged). **5-tier verdict ladder** (🌟 STRONG / 🟢 OK / 🟡 MIXED / 🟠 WEAK / 🔴 BLEEDING). **Sorted worst-first** ("bleeding sectors should leap off the page" L64). Markdown table formatter with em-dash for None. **0 critical bugs.** ✅
3. **SP-X1: sector_pnl.py** (60) — **TINY T46 Pillar 6** sister to sector_breakdown — uses `sector OR tag OR "UNKNOWN"` ladder + uppercase + `/` split for primary tag. **3-tier verdict** (PROFITABLE/FLAT/LOSING). **Sorted best-first** (`-r["total_r"]`) — opposite of sector_breakdown. Inconsistency: SBd worst-first, SP best-first. NEW Theme T189 (REPORTING-SORT-INCONSISTENCY across sister modules).
4. **SC-X1: semiconductors.py** (67) — **CURATED 47-TICKER SEMI UNIVERSE WITH AI-WEIGHT TAGGING** (NVDA=1.00, ALAB/AVGO/SMCI=0.95, MRVL/AMD/MU/ASML/TSM=0.90, ... POWI=0.40 floor). **3 ETFs included** (SOXX/SMH/SOXL) tagged with category. **4 helper functions** (get_semi_tickers / get_semi_meta / is_semi / semi_categories). **0 BUG findings. Theme T57 (PERFECT MODULE).** ✅
5. **TG-X1: theme_scoring_guardrails.py** (95) — **PRIORITY 8 EXPLICIT-DISABLE GUARDRAIL**. **6-flag SAFETY dict ALL False** + **7-prerequisite REQUIRED tuple** (historical_validation, forward_observation, train_test_discipline, overfitting_review, clear_tests, founder_approval, readiness_gate_preserved). **`@dataclass(frozen=True) ThemeScoringStatus`** mirrors the dict + adds prerequisites tuple. **`assert_theme_scoring_disabled` raises RuntimeError** if config tries to flip ANY of 4 enable-keys to truthy. NEW Theme T190 (DISABLED-BY-DEFAULT WITH HUMAN-READABLE EXPLAIN method). **0 critical bugs.** ✅
6. **WoW-X1: wow_trend.py** (107) — **WEEK-OVER-WEEK TREND COMPARATOR**. `_within` end-exclusive date filter with **2-key date fallback** (evaluated_on, pick_date). **`_summarize`** 6-field aggregator with **n=0 zero-defense** returning all zeros. **`_arrow` direction-aware emoji** (🟢↑/🔴↓ for good_positive metrics, swap for bad-positive). **Conditional alpha row** L101 (only renders if either week had alpha data). **CRITICAL:** L25/L52 naive `datetime.now()` and `fromisoformat`. Boundary-overlap edge case: end_this is inclusive in semantics but `_within` uses `<` end-exclusive — minor consistency to verify.
7. **WC-X1: wisdom_consultant.py** (71) — **PILLAR 2 OBSERVE-MODE LIFETIME CAP** at `SCORE_ADJ_CAP=0.05` (L22). **3-section pipeline** (kill list check → pattern matching → cap). **Per-pattern adjustment** ±0.02 (edge=+0.02, drag=-0.02). **EXPLICIT v0.1/v0.2 disclaimer in docstring** (L12-13). NEW Theme T191 (CAPPED-OBSERVATION-MODE versioning pattern). **0 critical bugs.** ✅
8. **WCv-X1: wisdom_coverage.py** (85) — **T33 daily coverage stat** with **T42 matched/violated split** (✨ edges vs ⚠ warnings). **Lambda fallback** L15-17 when wisdom_hint module unavailable — **graceful degradation** to no-op. **Pluralization-correct singular/plural rendering** L75-77. NEW Theme T192 (LAMBDA-NOOP IMPORT FALLBACK). **0 critical bugs.** ✅
9. **WR-X1: weekly_review.py** (352) — **THE GRAND ORCHESTRATOR** that composes 8 sub-systems into one Sunday Telegram + markdown snapshot. **6-tier letter-grade ladder** (A/B/C+/C-/D/F-crisis-pause). **`what_worked`/`what_failed`** per-tag/per-trade-type ≥0.5 R / ≤-0.3 R thresholds with min n=2. **B6 `rules_violated_on_losers`** — for each loser, find high-conf rules whose triggers fire (the "we knew better" diagnostic). **5-pillar footer integration** (Calibration Brain T40 / Pillar 1 hypothesis+self-awareness / Pillar 4 learning journal+weights / Pillar 5 30d CIs / Pillar 6 WoW+sector P&L). **EVERY external integration wrapped in try/except → silent pass** (graceful degradation). **CRITICAL:** L23 mkdir at import time. L148 naive `datetime.now()`. L348 naive datetime in filename. **6 silent except** swallow integration failures.
10. **QR-X1: quarterly_report.py** (276) — **PILLAR 6 v0.1 QUARTERLY MARKDOWN GENERATOR** using **`subprocess` git log integration** (L46-55) with 10s timeout + silent except → empty list. **9-summary-metric aggregator** (closed/wins/losses/expired/win_rate/total_r/avg_r/avg_return/avg_alpha_spy/avg_alpha_sec). **Hypothesis engine integration** with **dual-import fallback** (relative then absolute) for both hypothesis_engine and wisdom_base. **Top-5 winners + top-5 losers** sorted by R-multiple. **`_quarter_label`** computes Y_QN from month. **CRITICAL:** L21 mkdir at import time. L150 naive datetime. L167 timestamp says "UTC" but uses naive `datetime.now()` (TZ-LIE bug).
11. **YR-X1: yearly_report.py** (94) — **TINY T46 PILLAR 6** annual-letter scaffold with **explicit "deferred to v2" footer** ("Tax-loss harvesting · wash-sale ledger · 1099-equiv · Buffett-style narrative are scheduled for v2"). **6-status closed-set** (sl_hit/tp_hit/max_hold/sl_gap/tp_gap/day_close — broader than QR-X1's 4-status set!). **CLI with --year + --out** + smoke-print. NEW Theme T193 (HONEST-DEFERRED-SCOPE FOOTER). Inconsistency vs QR-X1 closed-status set.

---

## TOP-LEVEL CRITICAL FIXES (priority order)

1. **QR-X1 TZ-LIE BUG (L167):** Says "UTC" in output but uses naive `datetime.now()`. Either remove "UTC" label OR convert to TZ-aware UTC. **10 min.**
2. **WoW-X1 + QR-X1 + YR-X1 + WR-X1 naive datetime usage** — 6+ locations. **Fix: TZ-aware UTC consistently.** **30 min.**
3. **WR-X1 + QR-X1 mkdir at import time** — 2 modules. **Fix: lazy mkdir at first call.** **15 min.**
4. **SP-X1 vs SBd-X1 sort-direction inconsistency** — sister modules sort opposite directions. **Fix: pick one convention (worst-first preferred for surfacing problems) OR document why both.** **15 min.**
5. **QR-X1 vs YR-X1 closed-status set inconsistency** — QR uses 4-status, YR uses 6-status (includes max_hold/sl_gap/tp_gap). **Fix: extract to module constant, share.** **15 min.**
6. **WR-X1 6 silent except blocks** — pillar integration failures invisible. **Fix: log to stderr or structured channel for diagnostic visibility.** **30 min.**
7. **WoW-X1 inclusive vs exclusive date boundary** — `_within` uses `<` end-exclusive but `today` is `today` (technically inclusive). Edge case at midnight UTC. **Fix: document semantics OR use TZ-aware end-of-day.** **15 min.**
8. **QR-X1 git log via subprocess** — failure mode (no git, detached commit, etc) returns empty list silently. **Fix: log to stderr.** **10 min.**

---

## NEW THEMES INTRODUCED THIS BATCH

- **T189 (REPORTING-SORT-INCONSISTENCY across sister modules):** SBd vs SP — same-purpose modules sort opposite directions without explanation. Anti-pattern.
- **T190 (DISABLED-BY-DEFAULT WITH HUMAN-READABLE EXPLAIN method):** TG-X1 — `explain_theme_scoring_guardrail` returns docs-ready narrative for reports. Operator-friendly.
- **T191 (CAPPED-OBSERVATION-MODE versioning pattern):** WC-X1 — explicit v0.1/v0.2 disclaimer + ±0.05 hard cap. Aligns with T173 (HONEST-STATUS-DISCLAIMER) from batch 96.
- **T192 (LAMBDA-NOOP IMPORT FALLBACK):** WCv-X1 — `lambda *a, **k: ""` as graceful degradation when import fails. Better than try/except per-call.
- **T193 (HONEST-DEFERRED-SCOPE FOOTER):** YR-X1 — "scheduled for v2 (multi-week build)" footer instead of pretending the feature works. Operator-honesty.

---

## src/sector_benchmark.py (80 lines) — LINE BY LINE

- SB-1 GOOD (L1-11): **11-line docstring with motivation example** (SEMI vs SOXX vs SPY).
- SB-2 GOOD (L15-25): `TAG_TO_ETF` 8-key dict — most-specific first.
- SB-3 GOOD (L28-59): `SECTOR_TO_ETF` 26-key dict with **3 alias groups** (Financial/Financial Services/Financials, Consumer Cyclical/Consumer Discretionary, Materials/Basic Materials).
- SB-4 GOOD (L46-48): **Bug #8a 2026-05-05 archaeology** — preserves the diagnostic of "70% of picks fell through to SPY".
- SB-5 GOOD (L53-54): **Em-dash variants** (`Software—Application` etc) for yfinance compat — operator-aware of typography quirks.
- SB-6 GOOD (L62-79): `resolve_sector_etf` priority cascade — tag → sector → SPY fallback.
- SB-7 GOOD (L70): `tag.split("/")[0].strip().upper()` — primary-tag extraction.
- **SB-8: 0 BUG findings.** ✅

---

## src/sector_breakdown.py (84 lines) — LINE BY LINE

- SBd-1 GOOD (L1-6): T28 docstring referencing src.sector_benchmark.
- SBd-2 GOOD (L9-10): Imports from sister modules — clean coupling.
- SBd-3 GOOD (L13-27): `_enrich_with_sector_etf` — **idempotent skip** if already enriched + try/except → SPY fallback + `or "SPY"` belt-and-suspenders default.
- SBd-4 BUG-MINOR (L24-25): Silent `except Exception: etf = "SPY"` — sector resolution failures invisible.
- SBd-5 GOOD (L30-42): `_verdict` 5-tier ladder with explicit threshold cascade. Returns "⚪ N/A" for None total_r.
- SBd-6 GOOD (L45-66): `sector_breakdown` master:
  - L50-51: empty-defense
  - L52-53: enrich + delegate to breakdown_by
  - L54-63: per-row verdict mapping
  - L65: **worst-first sort** with None-defense (`if d["total_r"] is not None else 0`)
- SBd-7 GOOD (L64): "Worst first — bleeding sectors should leap off the page" — operator-design rationale.
- SBd-8 GOOD (L69-83): Markdown table formatter with em-dash for None values.

---

## src/sector_pnl.py (60 lines) — LINE BY LINE

- SP-1 GOOD (L1-5): T46 Pillar 6 docstring noting R-as-dollar-proxy.
- SP-2 GOOD (L10-12): `_to_float` defensive coercion.
- SP-3 GOOD (L15-44): `per_sector_pnl` master:
  - L18-20: 3-key fallback (sector OR tag OR "UNKNOWN") + uppercase + primary-tag split
  - L23-26: per-sector R-multiple aggregation with None filter
  - L27-29: wins/total/mean computation
  - L30-33: 3-tier verdict ladder (PROFITABLE/FLAT/LOSING)
  - L34-42: 7-field row dict
  - L43: **best-first sort** (`-r["total_r"]`)
- SP-4 BUG (L43): **Sort opposite to SBd-X1** — sister module sorts worst-first; this sorts best-first. Theme T189.
- SP-5 GOOD (L47-59): Markdown table formatter — clean.

---

## src/semiconductors.py (67 lines) — LINE BY LINE

- SC-1 GOOD (L1): Tiny docstring.
- SC-2 GOOD (L4-51): **47-ticker SEMI_UNIVERSE dict** with consistent 3-field schema (name/category/ai_weight).
- SC-3 GOOD (L4-50): AI-weight ladder — NVDA=1.00 (anchor), ALAB/SMCI/AVGO=0.95, MRVL/AMD/MU/ASML/TSM=0.90, ARM/SNPS/CDNS/CRDO/ANET=0.85, AMAT/LRCX=0.80, KLAC/MPWR/RMBS=0.75, COHR/TER/VICR/DELL=0.70, MCHP=0.45, POWI=0.40 (floor).
- SC-4 GOOD (L48-50): 3 ETFs included — SOXX/SMH/SOXL — for benchmark/leverage exposure.
- SC-5 GOOD (L53-54): `get_semi_tickers(min_ai_weight)` — single-line filter comprehension.
- SC-6 GOOD (L56-57): `get_semi_meta` returns empty dict on miss (vs raising).
- SC-7 GOOD (L59-60): `is_semi` simple membership check.
- SC-8 GOOD (L62-66): `semi_categories` inverts dict to category → tickers map.
- **SC-9: 0 BUG findings. Theme T57 (PERFECT MODULE) — 49th cumulative perfect.** ✅

---

## src/theme_scoring_guardrails.py (95 lines) — LINE BY LINE

- TG-1 GOOD (L1-7): **7-line docstring with explicit "Priority 8 intentionally does NOT enable" declaration**.
- TG-2 GOOD (L15-21): `FUTURE_THEME_SCORING_FIELDS` 5-tuple (forward-spec).
- TG-3 GOOD (L23-31): `REQUIRED_PREREQUISITES` 7-tuple including human-process gates (founder_approval, readiness_gate_preserved).
- TG-4 GOOD (L33-40): `THEME_SCORING_SAFETY_FLAGS` 6-key dict ALL False — closed by default.
- TG-5 GOOD (L43-54): `@dataclass(frozen=True) ThemeScoringStatus` mirrors dict + 2 tuple fields. **frozen** prevents mutation.
- TG-6 GOOD (L57-59): `theme_scoring_status()` returns `asdict(...)` — JSON-safe.
- TG-7 GOOD (L62-84): `assert_theme_scoring_disabled` master:
  - L68-69: cfg None-defense + isinstance check
  - L70-71: explicit RuntimeError if theme_scoring not dict
  - L73-78: 4-key enabled set
  - L79-84: collect ALL violations into single error message (not first-fail-fast)
- TG-8 GOOD (L83): Sorted enabled-keys for deterministic error output.
- TG-9 GOOD (L87-94): `explain_theme_scoring_guardrail` returns docs-ready narrative — Theme T190.
- **TG-10: 0 BUG findings.** ✅

---

## src/wow_trend.py (107 lines) — LINE BY LINE

- WoW-1 GOOD (L1-7): T46 docstring.
- WoW-2 GOOD (L14-17): `_to_float` defensive coercion.
- WoW-3 GOOD (L19-29): `_within` end-exclusive date filter with **2-key fallback** (evaluated_on, pick_date) + per-key try/except continue.
- WoW-4 BUG (L25): `datetime.fromisoformat(str(v).split("T")[0])` — naive datetime.
- WoW-5 GOOD (L32-47): `_summarize` 6-field aggregator with **n=0 all-zeros default** + None-filter on rs/alphs.
- WoW-6 GOOD (L43): `wins / max(len(rs),1)` — zero-defense.
- WoW-7 GOOD (L50-67): `compare` master:
  - L52: today defaults to naive `datetime.now()`
  - L53-55: 3-window construction (today, today-7d, today-14d)
  - L56-57: this/last filtering with end-exclusive boundary
  - L58-59: per-window summary
  - L60-66: 5-delta computation
- WoW-8 BUG (L52): Naive `datetime.now()` default.
- WoW-9 GOOD (L70-75): `_arrow` direction-aware with `good_positive` flag for metrics where down-is-good.
- WoW-10 GOOD (L78-106): `format_footer` master:
  - L80-82: empty-baseline early return
  - L86-88: trades line with absolute count + delta
  - L89-92: WR line with arrow + percentage delta
  - L93-100: mean R + total R lines
  - L101-105: **conditional alpha row** (only if either week had data)

---

## src/wisdom_consultant.py (71 lines) — LINE BY LINE

- WC-1 GOOD (L1-14): **14-line docstring with full return shape + observe-mode v0.1/v0.2 disclaimer**.
- WC-2 GOOD (L22): `SCORE_ADJ_CAP = 0.05` — explicit cap module constant.
- WC-3 GOOD (L25-70): `consult_before_pick` master:
  - L31-36: 4-field result skeleton
  - L39-46: kill-list check (informational only — no score adj)
  - L48-63: pattern-matching loop with edge=+0.02 / drag=-0.02 per match
  - L66-67: explicit cap clamp (both directions)
  - L68: round to 3 decimals
- WC-4 GOOD (L42-45): Kill warning is operator-readable with reason + expiry date.
- WC-5 GOOD (L46): "No score adj — kill is informational; main.py / scorer decides whether to drop" — clean separation of concerns.
- WC-6 GOOD (L55-57): Pattern message includes WR/n/p_value — full statistical context.
- **WC-7: 0 BUG findings.** ✅

---

## src/wisdom_coverage.py (85 lines) — LINE BY LINE

- WCv-1 GOOD (L1-10): T33 docstring with example output.
- WCv-2 GOOD (L13-17): **`try/except` import with lambda no-op fallback** — Theme T192. Better than per-call try/except.
- WCv-3 GOOD (L20-65): `coverage` master:
  - L26-29: empty-rows zero-stats default
  - L31-32: 5 counters initialized
  - L33-55: per-row hint extraction with per-call try/except
  - L42-43: `bool((wh or "").strip())` defensive truthy check
  - L48-53: T42 matched/violated split via emoji detection in pattern hint
  - L54-55: union-tag if either hint present
  - L57-65: 7-field result dict
- WCv-4 GOOD (L36-37/L40-41): Per-call try/except → empty string (not raising) — operator-friendly.
- WCv-5 GOOD (L52): Detects edges via "✨" OR "🟢" — covers both hint styles.
- WCv-6 GOOD (L68-84): `format_footer` Telegram-ready:
  - L70-71: empty-stats early return
  - L72-78: base line with **pluralization-correct** singular/plural ("lesson" vs "lessons")
  - L79-83: T42 matched/warnings extension only if meaningful
- **WCv-7: 0 BUG findings.** ✅

---

## src/weekly_review.py (352 lines) — LINE BY LINE

- WR-1 GOOD (L1-11): 11-line docstring describing Sunday cycle.
- WR-2 BUG-MINOR (L23): `REPORTS.mkdir(parents=True, exist_ok=True)` at import time (T118).
- WR-3 GOOD (L26-37): `grade` 6-tier letter ladder with crisis-pause rendering.
- WR-4 GOOD (L40-60): `what_worked` per-tag/per-trade-type ≥0.5 R, min-n=2.
- WR-5 GOOD (L64-101): **B6 `rules_violated_on_losers`** — for each loser, find high-conf rules whose triggers fire (the "we knew better" diagnostic).
- WR-6 GOOD (L91): `min_confidence=0.85` — only high-conf rules count as "violated".
- WR-7 GOOD (L96): `max(ls, key=lambda L: L.get("confidence", 0))` — picks best (highest-conf) violated rule per loser.
- WR-8 GOOD (L103-121): `what_failed` mirror of what_worked with -0.3 R threshold.
- WR-9 GOOD (L124-144): `recommended_actions` — 6-rule generator:
  - L126-127: F-grade → 50% size cut
  - L129-130: sector α negative → ETF-losing alert
  - L132-133: WR<30% with n≥4 → tighten threshold
  - L135-138: SWING/DAY-specific allocation reduction
  - L140-141: default "continue current strategy"
  - L143: hypothesis review pointer
- WR-10 BUG (L148): naive `datetime.now()`.
- WR-11 GOOD (L147-169): `build_report` master assembles 9-field dict.
- WR-12 GOOD (L172-337): `format_telegram` master with **5-pillar footer integration**:
  - L172-216: header + grade + 7d performance + post-mortem + sectors + wisdom base
  - L218-230: Calibration Brain (T40) try/except → silent
  - L233-267: Pillar 1 (Layer 4 hypothesis + Layer 5 self-awareness) try/except → silent
  - L270-294: Pillar 4 (learning journal + weight history) try/except → silent
  - L297-307: Pillar 5 (rolling 30d CIs) try/except → silent
  - L310-330: Pillar 6 (WoW + sector P&L) try/except → silent (2 sub-blocks)
  - L332-335: Recommended actions
- WR-13 BUG (L229/L249/L259/L266/L293/L306/L319/L329): **8 silent except** — all integration failures invisible.
- WR-14 GOOD (L242-249): Self-awareness rendering with paused/active label + 0-10 score + classification.
- WR-15 GOOD (L256-258): Hypothesis journal renders base WR for context.
- WR-16 GOOD (L282-285): Learning journal sub-extraction with per-kind filtering — only renders if non-zero.
- WR-17 GOOD (L340-344): `format_markdown` reuses telegram + simple `*` → `**` swap.
- WR-18 BUG (L348): naive `datetime.now()` in filename.

---

## src/quarterly_report.py (276 lines) — LINE BY LINE

- QR-1 GOOD (L1-8): 8-line docstring with output path.
- QR-2 BUG-MINOR (L21): `REPORTS.mkdir(...)` at import time (T118).
- QR-3 GOOD (L24-28): `_to_float` defensive coercion.
- QR-4 GOOD (L31-43): `_load_picks_in_range` — date-string parse with strptime + range filter.
- QR-5 GOOD (L46-55): `_git_log_since` **subprocess integration** with 10s timeout + silent except → empty list.
- QR-6 BUG-MINOR (L54): Silent except — git failures invisible.
- QR-7 GOOD (L58-60): `_quarter_label` = `Y_QN` from month math.
- QR-8 GOOD (L63-93): `_summary_metrics` 11-field aggregator with None-filter on each metric list.
- QR-9 BUG (L64): **`closed_set = {"tp_hit", "sl_hit", "expired", "day_close"}`** — 4-status; differs from YR-X1's 6-status. Inconsistency.
- QR-10 GOOD (L96-101): `_top_movers` returns (winners, losers) tuple via 2-direction sort.
- QR-11 GOOD (L104-133): `_journal_summary` master:
  - L107-119: per-line JSON parse + range filter + outcome filter
  - L122-126: **dual-import fallback** (relative then absolute) for hypothesis_engine
  - L127-133: 5-field result with edges/drags detail lists
- QR-12 GOOD (L122-126): Defensive dual-import — works in both module and script context.
- QR-13 GOOD (L136-145): `_wisdom_summary` mirror dual-import for wisdom_base.
- QR-14 GOOD (L148-275): `generate_report` master — 270 lines markdown construction:
  - L150: naive `datetime.now()` default
  - L160: out_path uses quarter label
  - L163-189: Headline section
  - L192-201: Top winners table
  - L204-213: Top losers table
  - L216-237: Hypothesis findings with edges/drags
  - L240-253: Wisdom base state with top-5 lessons
  - L256-265: System changes via git log (top 25)
  - L267-274: Footer with auto-gen attribution
- QR-15 BUG-CRITICAL (L167): `f"**Generated:** {datetime.now().strftime(...)} UTC"` — **TZ-LIE BUG**: says "UTC" but uses naive `datetime.now()` (system-local time, not UTC).
- QR-16 GOOD (L274): `out_path.write_text("\n".join(md))` — non-atomic but acceptable for report files.

---

## src/yearly_report.py (94 lines) — LINE BY LINE

- YR-1 GOOD (L1-8): T46 docstring with **explicit "PDF/LLM/tax-form generation explicitly deferred (multi-week build)"** — Theme T193.
- YR-2 GOOD (L20-22): `_to_float` defensive coercion.
- YR-3 GOOD (L25-34): `_load_year` — 4-char prefix match for year filtering (avoids strptime overhead).
- YR-4 BUG-MINOR (L31): `(row.get("pick_date") or "")[:4]` — assumes ISO format. Edge case: malformed date with non-year prefix would silently miss.
- YR-5 GOOD (L37-54): `build_report` master:
  - L38: year defaults to `datetime.now().year` (TZ-naive but year-precision OK across most TZs)
  - L40-41: **6-status closed-set** (sl_hit/tp_hit/max_hold/sl_gap/tp_gap/day_close) — broader than QR-X1!
  - L42-43: per-metric None filter
  - L44-53: 8-field result dict
- YR-6 BUG (L40-41): Closed-status set differs from QR-X1 (T46 inconsistency).
- YR-7 GOOD (L57-75): `format_markdown` with explicit "scheduled for v2" footer.
- YR-8 GOOD (L78-89): `main` argparse CLI with `--year` + `--out` + smoke print.
- YR-9 GOOD (L92-93): Standard `if __name__ == "__main__": raise SystemExit(main())` pattern.

---

## CONSOLIDATED CROSS-CUTTING (THIS BATCH)

### NEW Themes T189-T193 (5 new)

- **T189 (REPORTING-SORT-INCONSISTENCY across sister modules):** SBd vs SP — sort opposite directions without explanation.
- **T190 (DISABLED-BY-DEFAULT WITH HUMAN-READABLE EXPLAIN method):** TG-X1 — `explain_theme_scoring_guardrail` for docs.
- **T191 (CAPPED-OBSERVATION-MODE versioning pattern):** WC-X1 — explicit v0.1/v0.2 + ±0.05 hard cap.
- **T192 (LAMBDA-NOOP IMPORT FALLBACK):** WCv-X1 — `lambda *a, **k: ""` for graceful degradation.
- **T193 (HONEST-DEFERRED-SCOPE FOOTER):** YR-X1 — "scheduled for v2" instead of pretending feature works.

### Theme T57 (PERFECT MODULES) NOW 49 cumulative
- +1 this batch: SC (semiconductors). (SB has Bug #8a archaeology only — could count; SBd has minor silent except; TG/WC/WCv all have ≥1 minor finding pattern — not strictly perfect.)

### Theme T6 (atomic writes) UPDATE
- **0 atomic this batch.**
- **0 unsafe writers this batch** (all files are read-only or single-write report generators).
- Running tally unchanged: ~18 safe / ~136 unsafe.

### Cross-cutting tally summary (this batch only)

| Metric | Count this batch |
|---|---:|
| Files actually fetched & line-audited | 11/11 ✅ |
| Total lines audited | 1,371 |
| Bare `except:` | 0 |
| Silent `except Exception` (no log) | 11 (WR ×8, QR ×1, SBd ×1, WoW ×1) |
| Naive datetime usage | 6 (WoW ×2, QR ×2, WR ×2, YR ×0 — year-precision OK) |
| TZ-LIE bugs | 1 (QR-X1 L167) |
| TZ-aware UTC | 0 |
| Atomic writers | 0 |
| Unsafe writers | 0 |
| Inline imports | 12+ (WR ×11 pillar integrations, QR ×2 dual-import) |
| Module-level side effects | 2 (WR mkdir, QR mkdir) |
| Dataclasses | 1 (TG-X1 frozen) |
| `__main__` smoke tests | 1 (YR-X1 CLI) |
| 0-BUG perfect modules | 1 (SC) |
| Operator-readable archaeology | 4 (Bug #8a, B6, T28, T33, T40, T42, T46, "violated _rule_") |
| Explicit-disabled guardrails | 1 (TG-X1) |
| Sort inconsistencies | 1 (SBd worst-first vs SP best-first) |
| Status-set inconsistencies | 1 (QR 4-status vs YR 6-status) |

---

## SUMMARY (Batch 99 — 11-FILE)

| File | Critical | Bug | Code smell | Good | Total findings |
|---|---:|---:|---:|---:|---:|
| sector_benchmark | 0 | 0 | 0 | 7 | 7 |
| sector_breakdown | 0 | 1 | 0 | 7 | 8 |
| sector_pnl | 0 | 1 | 0 | 4 | 5 |
| semiconductors | 0 | 0 | 0 | 8 | 8 |
| theme_scoring_guardrails | 0 | 0 | 0 | 9 | 9 |
| wow_trend | 0 | 2 | 0 | 8 | 10 |
| wisdom_consultant | 0 | 0 | 0 | 6 | 6 |
| wisdom_coverage | 0 | 0 | 0 | 6 | 6 |
| weekly_review | 0 | 4 | 1 | 13 | 18 |
| quarterly_report | 1 | 4 | 1 | 12 | 18 |
| yearly_report | 0 | 2 | 0 | 7 | 9 |
| **TOTAL** | **1** | **14** | **2** | **87** | **104** |

---

## TOP 10 PRIORITY FIXES FROM BATCH 99

1. **QR-X1 TZ-LIE bug (L167)** — fix or remove "UTC" label. **10 min.**
2. **WoW + QR + WR + YR naive datetime usage** — 6+ locations migrate to TZ-aware UTC. **30 min.**
3. **WR + QR mkdir at import time** — lazy-init at first call. **15 min.**
4. **SBd vs SP sort inconsistency** — pick worst-first convention OR document. **15 min.**
5. **QR vs YR closed-status set inconsistency** — extract to shared constant. **15 min.**
6. **WR-X1 8 silent except in pillar integrations** — log to stderr for diagnostic. **30 min.**
7. **WoW boundary-overlap edge case** — document `<` end-exclusive semantics. **10 min.**
8. **QR-X1 git subprocess silent except** — log to stderr. **10 min.**
9. **YR-X1 4-char year prefix** — add isdigit check for malformed dates. **10 min.**
10. **SBd silent except → SPY** — log sector resolution failures. **10 min.**

---

## COVERAGE TRACKER (HONEST)

| Phase | Files in `src/` | Verifiably audited (this convo, line-by-line) |
|---|---:|---:|
| Pre-batch-99 | 92 | 76 |
| **Post-batch-99** | **92** | **87** |
| Remaining `src/` top-level | — | **5 files (~5%)** |

Plus subdirectories: `src/backtester/` (5), `src/market_data_providers/` (2), `src/patterns/` (10) — all unverified.

End of Batch 99.
