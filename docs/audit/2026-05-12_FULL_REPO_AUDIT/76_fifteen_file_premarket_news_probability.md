# Batch 70 — 15-FILE BATCH — TRUE LINE-BY-LINE — PREMARKET/NEWS/PROBABILITY/RISK

**Date:** 2026-05-12
**Files (15):** finnhub_data (277), fundamentals (143), llm_agent (207), layman_translator (225), news_engine (163), news_classifier (135), market_news (211), premarket_decision_contract (269), premarket_filter (25), premarket_readiness_gate (197), premarket_sanity_gate (301), probability_engine (353), risk_metrics (167), theme_scoring_guardrails (95), wow_trend (107)
**Phase:** G/H. **Total LOC audited this batch: ~3,178 lines (heaviest batch yet).**

## TOP HEADLINE FINDINGS (one per file)

1. **FH-X1: finnhub_data.py** is **THE FINNHUB FUNDAMENTALS + CROSS-VALIDATION FETCHER** (277 lines). 24h cache + **27-field metric extraction** + **`_safe_pct` percent-to-decimal converter** + **E2c cross_validate_price** (May 4 2026 archaeology) with 2%/5% warn/block thresholds. **Graceful: if Finnhub down, returns is_valid=True (don't punish for infra)** — Theme T31 yfinance/web brittleness defense **2nd-source-cross-validation gold standard.**
2. **FN-X1: fundamentals.py** is **THE 11-DIMENSION COMPOSITE SCORER** (143 lines). Weighted 0-1 composite from 11 metrics (5 valuation 35% + 3 growth 25% + 2 profitability 20% + 2 health 10% + 1 cashflow 8% + 1 RS 2%). **Per-metric 5-tier dispatch + auto-renormalization** when fields missing (`weights / total_w`). Per Batch 67 + this batch FH-X1 producer-consumer.
3. **LLM-X1: llm_agent.py** is **THE 4-PROVIDER LLM CASCADE** (207 lines). **Claude → Gemini → OpenAI → rule-based** + **per-provider quota-exhaustion latch** (mutex flag + skip-rest-of-run) + 12h disk cache + **1.5s throttle** (50 RPM Claude tier-1 archaeology) + TZ-aware timestamps + **backward-compat naive-cache normalization**. **First audited LLM orchestrator.**
4. **LT-X1: layman_translator.py** is **T52 — THE PLAIN-ENGLISH TRANSLATION LAYER** (225 lines). 9 conversion functions (score_to_words / confidence_label / risk_label / money / pct / r_multiple_words / pick_to_layman / outcome_to_layman / verdict_line). **5 design principles in docstring**: no jargon / short sentences / answer "why does this matter" / honest / KEEP all actionable trading data. **Bug fix 2026-05-05 archaeology** for real CSV column names. **2nd audited layman/translator module.**
5. **NE-X1: news_engine.py** is **THE 3-SOURCE NEWS PIPELINE** (163 lines). Alpaca (primary) + Yahoo RSS (per-watchlist-ticker) + SEC EDGAR (declared but not implemented) + 48h dedup TTL via news_seen.json + jsonl append-only news_log + **0.2s polite-sleep between Yahoo calls.** **First audited multi-source news aggregator.**
6. **NC-X1: news_classifier.py** is **THE CLAUDE-POWERED HEADLINE CLASSIFIER** (135 lines). **9-field JSON contract** (sentiment / sentiment_score / urgency / urgency_score / category / tradeable_score / primary_ticker / rationale / action_window) + 21-keyword heuristic fallback + markdown-fence stripping + **batch-prioritization (Alpaca > Yahoo)** + smoke test. Per Batch 65 NC-X2 + this batch consumer.
7. **MN-X1: market_news.py** is **THE FINNHUB-GENERAL + LLM SENTIMENT DIGESTER** (211 lines). 4h cache + 6-key sentiment JSON (sentiment / score / narratives / key_risks / key_catalysts / summary) + **Claude → Gemini fallback via REST** (no SDK) + markdown-fence stripping + neutral-default skeleton. **First audited Gemini-via-REST module** (no SDK dependency).
8. **PDC-X1: premarket_decision_contract.py** is **THE LANE 1 OFFICIAL DECISION CONTRACT** (269 lines). **2-decision enum** (official_pick / official_no_pick) + **27-field required for pick + 18-field required for no_pick** + 11-cause primary_no_pick taxonomy + 7-field numeric validation + **safety_flags MUST be False (paper_trading_enabled / live_trading_enabled)** + behavior-neutral (no production effect). **First audited contract module.** Gold standard schema discipline.
9. **PF-X1: premarket_filter.py** (25 lines, **smallest in batch + 4th smallest in audit**) is **THE GAP-CHECK SHORT-CIRCUIT**. yfinance fast_info + max_gap_up=3% + max_gap_down=-5% + **defensive (true, "no premarket data — allow") + (true, "...failed — allowing")** = FAIL-OPEN philosophy. **Per Batch 66 MG-5/B68 RG fail-open vs fail-defensive Theme T30 — adds another fail-OPEN instance.**
10. **PRG-X1: premarket_readiness_gate.py** is **THE LANE 1 DATA-READINESS GATE** (197 lines). **5-status dispatcher** (not_ready_empty_universe / no_market_data / low_market_data_coverage / provider_degraded / ready) + 25% min coverage + 25 min fetched count + 4 warning categories + 11-key JSON-safe payload. **Fail-CLOSED to no_pick** explicit ✅. **Producer for PDC-X1 NO_PICK_DATA_PROVIDER_DEGRADED + NO_PICK_DATA_READINESS_FAILED.**
11. **PSG-X1: premarket_sanity_gate.py** is **THE LANE 1 PER-PICK SANITY GATE** (301 lines). 4-action dispatch (SAFE / HALF_SIZE / SKIP_TODAY / WATCH_ONLY) + 7 sequential guards + **gap_pct >= 3% → HALF_SIZE chasing-risk** + **price ≤ stop_loss → SKIP** + **negative gap eats SL buffer (>60%) → SKIP** + market_snapshot with VIX≥25 → skip_all + SPY ≤-1.5% → skip_all. **Apply-half-size mutates plan in-place + plan["premarket_size_multiplier"]=0.5.** Heaviest gate audited.
12. **PE3-X1: probability_engine.py** is **PROBABILITY ENGINE v0.1 — THE 6-LAYER MULTI-SIGNAL DECISION BRAIN** (353 lines). **HONEST STATUS** (line 12-15): "REAL integration, HEURISTIC math... future v0.2 will replace combiner with logistic regression trained on historical outcomes." 5 REGIME × 6 NEWS × 4 CATALYST adjustments + **SignalState + ProbabilisticDecision @dataclass** + 4 in-script CLI tests. Per Batch 67 stock_stats + B67 calibration consumer chain.
13. **RKM-X1: risk_metrics.py** is **THE SHARPE/SORTINO/MAX-DD/CALMAR ENGINE** (167 lines). **Pure stdlib (no scipy/numpy)** + Sharpe per-period + Sortino with downside-deviation + max_drawdown on equity curve + **naive 50-trade/year annualization with sqrt(50)≈7.07** + **dual % vs R-multiple metrics** + **n<30 sample_warning flag** ✅. **3rd audited Pure-stdlib statistical module** (joins SA + HE).
14. **TSG-X1: theme_scoring_guardrails.py** is **THE THEME-AWARE-SCORING DISABLED-STATE PROOF** (95 lines). 5 future-fields named + **7 prerequisites tuple** (historical_validation / forward_observation / train_test_discipline / overfitting_review / clear_tests / founder_approval / readiness_gate_preserved) + **frozen @dataclass ThemeScoringStatus all defaults False** + **assert_theme_scoring_disabled raises RuntimeError** + 4-key boolean safety flag dict. Per B69 SS-X1 sibling. **4th audited frozen-dataclass.**
15. **WT-X1: wow_trend.py** is **T46 — THE 7d-VS-PRIOR-7d DELTA TABLE** (107 lines). 5-metric WoW comparison (n / win_rate / mean_r / total_r / alpha) + **end-exclusive window** + per-metric 🟢↑/🔴↓ arrow with good_positive flag + 5-line Telegram footer + **'' return if no prior-week baseline.** Schema-stable.

## CRITICAL CROSS-FILE FINDINGS

- **NEW Theme T34 (LLM PROVIDER CASCADE):** **3 audited LLM-using modules** with similar Claude→Gemini→fallback patterns:
  - LLM-X1 (rationale): Claude → Gemini → OpenAI → rule-based + quota-latch
  - NC-X1 (news classify): Claude → heuristic fallback
  - MN-X1 (market sentiment): Claude → Gemini-via-REST → neutral-default
  
  **PROBLEM:** 3 modules, 3 different cascade implementations. **No shared LLM-orchestration helper.** Operator-confusion + 3 places to update model name (CLAUDE_MODEL = "claude-sonnet-4-5" hardcoded in all 3).
- **PE3-X1 OBSERVE-MODE EXPLICIT v0.1:** Probability Engine **HONEST STATUS docstring** — heuristic math, not Bayesian. Catalogged as **26th OBSERVE-MODE module** with **EXPLICIT HONESTY about non-finalness.** Gold standard humility.
- **THEME T30 EXPANSION (FAIL-OPEN cases now 3):** **PF-X1 25-line gap-check** adds 3rd fail-OPEN instance:
  - B66 MG-5/6 spy_trend → fail-OPEN bullish
  - B68 RG-X1 market_regime → fail-DEFENSIVE transition (different)
  - **B70 PF-X1 gap_check → fail-OPEN allow** (this batch)
  - **B70 FH-X1 cross_validate_price → fail-OPEN is_valid=True if Finnhub down** (acceptable: "don't punish for infra issues")
  
  **2 fail-OPEN cases (PF + FH) are intentional + documented.** MG-5 fail-OPEN is the ONLY UNINTENDED instance to fix.
- **LANE 1 PRODUCTION-READINESS PIPELINE FULLY AUDITED END-TO-END (4-MODULE CHAIN):**
  - PRG-X1 readiness gate (data-coverage check before scoring) → 
  - scoring (B62) → 
  - PSG-X1 sanity gate (per-pick fresh price + market snapshot) → 
  - PDC-X1 contract validation (27-field required + safety_flags=False)
  
  **4-module Lane 1 chain COMPLETE.**
- **PURE-STDLIB STATISTICAL MODULES NOW 3** (Theme T29): SA-X1 Wilson + HE-X1 binomial + this batch RKM-X1 Sharpe/Sortino/MaxDD/Calmar. **Pattern: deliberate avoidance of scipy/numpy in core decision/metric modules.**

## src/finnhub_data.py — LINE BY LINE

- FH-1 GOOD (1): 1-line docstring.
- FH-2 BUG (1): Module docstring undersells — 2 functions (fetch_fundamentals + fetch_finnhub_quote + cross_validate_price).
- FH-3 BUG (15): mkdir at import time. **16th cross-cutting import-time side-effect.**
- FH-4 GOOD (10): load_dotenv() — env initialization at import.
- FH-5 GOOD (12-16): 4 named constants.
- FH-6 GOOD (19-29): _cache_get with **TTL check + Exception → None** defensive.
- FH-7 BUG (27): bare Exception. Theme T1.
- FH-8 BUG (35): Naive datetime.now() — should be TZ-aware. **5th naive-datetime instance.**
- FH-9 GOOD (41-43): _safe_pct percent-to-decimal **with explicit comment.** ✅
- FH-10 GOOD (46-151): fetch_fundamentals with **27-field skeleton + 2 try blocks (profile + metric) + cache write on every path.**
- FH-11 GOOD (52-74): **27-field skeleton with 7 categorized sections** — operator-readable.
- FH-12 GOOD (76-79): No API key path → cache + return empty (idempotent).
- FH-13 GOOD (89-92): Finnhub-marketCap-millions conversion with explicit comment.
- FH-14 GOOD (105-108): Multiple field-name fallbacks (peTTM or peAnnual / pbAnnual or pb / etc.) — defensive.
- FH-15 GOOD (110): "Finnhub returns percentages; convert to decimals" inline archaeology.
- FH-16 GOOD (134-142): pfcf-derived FCF computation with **div-by-zero guard.**
- FH-17 BUG (93, 147): 2 bare Exception. Theme T1.
- FH-18 GOOD (155): Backwards-compat alias `fetch_info = fetch_fundamentals`.
- FH-19 GOOD (159-163): **E2c May 4 2026 archaeology** with rationale.
- FH-20 GOOD (163-204): fetch_finnhub_quote with **schema documentation in docstring** + `c == 0` invalid-ticker dispatch.
- FH-21 BUG (180): Inline import os, urllib, json. **32nd cross-cutting inline-import.**
- FH-22 GOOD (192-194): "Finnhub returns c=0 for invalid tickers — treat as None" archaeology.
- FH-23 GOOD (195-200): All-field defensive type cast `float(... or 0) or None`.
- FH-24 GOOD (207-276): cross_validate_price with **23-line in-function docstring + 6-key result.**
- FH-25 GOOD (236-239): Primary-price sanity (catches the "XXYYZZ123 case" — operator archaeology).
- FH-26 GOOD (245-248): **Graceful: if Finnhub unavailable → is_valid=True** with reason. ✅ Operator-explicit fail-OPEN-for-infra-issues. **Theme T30 intentional + documented variant.**
- FH-27 GOOD (251-254): avg-based disagreement pct.
- FH-28 GOOD (256-275): 3-tier dispatch (block / warn / agree) with **operator-readable reason text per tier.**

## src/fundamentals.py — LINE BY LINE

- FN-1 GOOD (1-3): 3-line docstring with **input + output + composite range.**
- FN-2 GOOD (7-134): score_fundamentals with **11-dimension weighted-list pattern.**
- FN-3 GOOD (8): "Weighted composite of 11 fundamental dimensions" — operator-explicit.
- FN-4 GOOD (9): `weights = []  # list of (sub_score, weight)` — schema comment.
- FN-5 GOOD (11-45): VALUATION 35% with 4 metrics (PE 12% + PEG 15% + PB 4% + PS 4%).
- FN-6 GOOD (23): `🔥 undervalued vs growth` PEG<1.0 verdict comment — operator readable.
- FN-7 GOOD (47-72): GROWTH 25% with 3 metrics (eps_q 10% + eps5 8% + rev 7%).
- FN-8 GOOD (66): `info.get("revenueGrowth") or info.get("revenueGrowth5Y")` — fallback chain.
- FN-9 GOOD (74-91): PROFITABILITY 20% with 2 metrics (pm 10% + roe 10%).
- FN-10 GOOD (93-109): HEALTH 10% with 2 metrics (de 5% + cr 5%).
- FN-11 GOOD (111-119): CASH FLOW 8% with fcf_yield only.
- FN-12 GOOD (121-129): RS 2% with relativeToSP500_52w.
- FN-13 GOOD (131-134): **Auto-renormalization `total_w = sum(w)` then `sum(s*w)/total_w`** ✅ — handles missing fields.
- FN-14 GOOD (132): `if not weights: return 0.5` — neutral default if NO data.
- FN-15 GOOD (137-143): passes_filters with min_market_cap quality filter.

## src/llm_agent.py — LINE BY LINE

- LLM-1 GOOD (1-4): 4-line docstring with **provider priority + cache + throttle.**
- LLM-2 GOOD (9-11): 3 named module consts.
- LLM-3 BUG (10): mkdir at import time. **17th cross-cutting.**
- LLM-4 GOOD (13): CLAUDE_MODEL = "claude-sonnet-4-5" — single-source-of-truth (but **3 modules duplicate this string**).
- LLM-5 GOOD (17-19): _cache_key with **sort_keys + default=str + md5 trunc.**
- LLM-6 GOOD (22-36): _cache_get with **TZ-aware backward-compat** (naive cache files normalized to UTC). ✅ Migration-discipline gold standard.
- LLM-7 BUG (34): bare Exception. Theme T1.
- LLM-8 GOOD (39-45): _cache_put with **TZ-aware UTC.** ✅
- LLM-9 BUG (44): bare Exception pass.
- LLM-10 GOOD (49-51): 3 module-level state lists (mutable single-element list = pythonic mutable global).
- LLM-11 GOOD (52): _MIN_INTERVAL = 1.5 with **"50 RPM tier-1, ~1.2s safe" archaeology.**
- LLM-12 GOOD (55-59): _throttle with elapsed-vs-min sleep.
- LLM-13 GOOD (63-73): _rule_based with **deterministic top-3 factors + safe-defaults + "Confirm independently. No certainty implied." disclaimer.** ✅
- LLM-14 GOOD (77-98): _build_prompt with **DAY vs SWING dispatch + 5-numbered-instruction template + word limit + sentence-completion mandate.** Operator-trust + LLM-control gold standard.
- LLM-15 GOOD (100-109): _claude single-call with temperature=0.4 (consistent across 3 LLM modules).
- LLM-16 BUG (101): Inline import. **33rd cross-cutting.**
- LLM-17 GOOD (113-124): _gemini with **SDK-version try/except** (newer config vs older fallback).
- LLM-18 BUG (114, 118): 2 inline imports.
- LLM-19 GOOD (128-135): _openai standard call.
- LLM-20 BUG (129): Inline import.
- LLM-21 GOOD (139-142): _is_quota_error keyword-based with 6 quota-keywords.
- LLM-22 GOOD (146-155): _try_provider wrapper with **(text, err) tuple return** + str truncation [:120].
- LLM-23 GOOD (158-195): _explain_uncached with **3-provider sequential cascade + per-provider quota latch + final rule-based fallback.**
- LLM-24 GOOD (169-171): **Quota-exhausted → set latch → skip rest of run.** ✅ One-time switch per run.
- LLM-25 GOOD (198-206): explain_pick public API with cache check.

## src/layman_translator.py — LINE BY LINE

- LT-1 GOOD (1-16): 16-line docstring with **5 design principles + technical-channel-stays-unchanged separation.** Gold standard.
- LT-2 GOOD (24-32): score_to_words with **5-tier dispatch + None handling.**
- LT-3 GOOD (35-41): confidence_label with 4-tier dispatch.
- LT-4 GOOD (44-50): risk_label with 5-tier dispatch.
- LT-5 GOOD (56-70): money + pct with **3-branch sign dispatch** + try/except.
- LT-6 GOOD (73-81): r_multiple_words with **6-tier outcome dispatch** ("big win" / "solid win" / "small win" / "small loss" / "loss" / "full stop-loss hit").
- LT-7 GOOD (87-94): _company_suffix with **trim-long-name + skip-if-empty-or-equals-ticker** logic.
- LT-8 GOOD (97-137): pick_to_layman with **6-line per-pick output + KEEPS all actionable data per docstring mandate.**
- LT-9 GOOD (101-103): Inner _f helper with default + try/except (acceptable inline closure).
- LT-10 GOOD (106-110): **3 fallback chains** for entry/sl/tp/qty fields (handles old + new CSV column names).
- LT-11 GOOD (113-115): **Risk + reward + R:R formulas** with div-by-zero guards.
- LT-12 GOOD (120-123): DAY vs SWING hold-time dispatch.
- LT-13 GOOD (130-136): 6-line emoji-prefixed output.
- LT-14 GOOD (143-181): outcome_to_layman with **2026-05-05 bug-fix archaeology** (real CSV column names).
- LT-15 GOOD (149-150): **Dual-column fallback** (evaluation_status OR status).
- LT-16 GOOD (157-165): **PnL computed from actual_return_pct + entry + qty when pnl_dollar absent** — schema-flexibility.
- LT-17 GOOD (170-181): 6-status dispatch with emoji + amount.
- LT-18 GOOD (187-196): verdict_line with **6-tier verdict** based on (wr, total_pnl) joint.
- LT-19 GOOD (199-207): beat_market_line with **3-branch dispatch** (about-even / beat / trailed).
- LT-20 GOOD (213-217): header helper.
- LT-21 GOOD (220-224): footer_explainer with **explanatory disclaimer**.

## src/news_engine.py — LINE BY LINE

- NE-1 GOOD (1-4): 4-line docstring.
- NE-2 GOOD (14-16): 3 source URL templates.
- NE-3 GOOD (18-20): 3 named paths + TTL.
- NE-4 GOOD (23-29): _load_seen with try/except → {}.
- NE-5 BUG (27): bare Exception → {}.
- NE-6 GOOD (32-44): **_save_seen with TZ-aware cutoff prune-on-save.** ✅
- NE-7 BUG (32): **NO ATOMIC WRITE.** **50th unsafe writer.** news_seen.json could corrupt dedup if interrupted.
- NE-8 BUG (42): bare Exception pass.
- NE-9 GOOD (47-85): fetch_alpaca_news with **TZ-aware UTC start + headers + 8-field item normalization.**
- NE-10 GOOD (51-53): No-credentials early skip with print.
- NE-11 GOOD (66-68): HTTP non-200 → log + return [] (operator-readable).
- NE-12 BUG (83): bare Exception → []. Theme T1.
- NE-13 GOOD (88-120): fetch_yahoo_rss with **per-ticker XML regex + 0.2s polite-sleep + cap at 20 tickers.**
- NE-14 GOOD (91): `tickers[:20]` cap — operator-explicit anti-spam.
- NE-15 GOOD (100): `[:3]` per-ticker item cap — operator-explicit.
- NE-16 GOOD (108): id format `f"yahoo_{tk}_{abs(hash(title.group(1)))}"` — deterministic dedup.
- NE-17 BUG (118): bare Exception continue.
- NE-18 GOOD (123-145): fetch_all_news with **2-source dedup-by-id + per-source counter via seen update.**
- NE-19 GOOD (148-155): append_news_log append-only jsonl. **Acceptable for audit trail.**
- NE-20 GOOD (158-163): __main__ smoke test. **21st __main__.**

## src/news_classifier.py — LINE BY LINE

- NC-1 GOOD (1-4): 4-line docstring.
- NC-2 GOOD (10-37): CLASSIFIER_PROMPT with **9-field JSON contract + tradeable_score 5-bucket guide.**
- NC-3 GOOD (24): **JSON-only, no markdown** — defensive prompt.
- NC-4 GOOD (40-76): classify_news with **import-fallback + no-key-fallback + Claude call + markdown-fence strip + JSON parse + classified_at stamp.**
- NC-5 BUG (43-45): Inline `import anthropic`. **34th cross-cutting.**
- NC-6 GOOD (62): Hardcoded "claude-sonnet-4-5" — **DRIFTS with LLM-X1 CLAUDE_MODEL + MN-X1 CLAUDE_MODEL.** Theme T2 (16th drift instance).
- NC-7 GOOD (68-71): markdown-fence stripping with **```json prefix handling.**
- NC-8 BUG (74): bare Exception → fallback. Theme T1.
- NC-9 BUG (73): Naive `datetime.now().isoformat()` — should be TZ-aware UTC.
- NC-10 GOOD (79-116): _heuristic_fallback with **21-keyword bag-of-words** (11 bullish + 9 bearish + 5 high-urgency).
- NC-11 GOOD: **6th audited keyword-bag-of-words module.** Theme T8 consolidation.
- NC-12 GOOD (89-100): Sentiment + urgency 3-tier dispatch + tradeable formula `(|score-0.5|*2) * urgency`.
- NC-13 GOOD (102-116): 9-field schema-stable return matching Claude contract.
- NC-14 GOOD (113): action_window dispatch by tradeable threshold.
- NC-15 GOOD (119-123): classify_batch with **Alpaca-priority sort + max_items cap.**
- NC-16 GOOD (126-136): __main__ MaxLinear test fixture. **22nd __main__.**

## src/market_news.py — LINE BY LINE

- MN-1 GOOD (1-4): 4-line docstring with provider priority.
- MN-2 BUG (20): mkdir at import. **18th cross-cutting.**
- MN-3 GOOD (16-22): 6 named consts + 2 cache TTLs.
- MN-4 GOOD (24): CLAUDE_MODEL drift-source #2 with NC-X1 + LLM-X1.
- MN-5 GOOD (27-32): 2 cache_path helpers with **per-hour granularity** (`%Y%m%d_%H`).
- MN-6 GOOD (35-58): fetch_market_news with **mtime-vs-TTL freshness check + Finnhub general-news fetch + sort by datetime desc.**
- MN-7 BUG (44): bare Exception pass.
- MN-8 BUG (50): Cache write at line 54 — **NO ATOMIC.** **51st unsafe writer.**
- MN-9 BUG (56): bare Exception → []. Theme T1.
- MN-10 GOOD (61-80): _build_sentiment_prompt with **head_text limit [:30] + STRICT JSON template + 6-field schema.**
- MN-11 GOOD (83-91): _strip_markdown_fences with **```json prefix + closing ``` strip** — robust.
- MN-12 GOOD (94-104): _claude_sentiment standard call.
- MN-13 BUG (96): Inline import.
- MN-14 GOOD (107-116): **_gemini_sentiment via REST POST (no SDK)** — first audited Gemini-via-REST. Operator-flexible.
- MN-15 GOOD (115): Operator-readable `f"Gemini HTTP {r.status_code}: {r.text[:200]}"`.
- MN-16 GOOD (119-183): analyze_market_sentiment with **6-key default + cache check + Claude → Gemini → default cascade + JSON parse + per-key setdefault for missing fields.**
- MN-17 GOOD (171-172): **`for k in default: result.setdefault(k, default[k])`** — schema-fill-from-default. ✅ Robustness gold standard.
- MN-18 BUG (177): bare Exception pass.
- MN-19 GOOD (180-183): JSON parse failure → log raw + return default. Operator-debuggable.
- MN-20 GOOD (186-194): get_market_briefing one-shot wrapper.
- MN-21 GOOD (197-210): __main__ smoke test with **operator-readable category-by-category print.** **23rd __main__.**

## src/premarket_decision_contract.py — LINE BY LINE

- PDC-1 GOOD (1-16): 16-line docstring with **6 explicit non-behaviors + behavior-neutral mandate.**
- PDC-2 GOOD (24-31): 4 named version + lane constants.
- PDC-3 GOOD (33-36): VALID_DECISIONS frozenset.
- PDC-4 GOOD (38-69): **OFFICIAL_PICK_REQUIRED_FIELDS 27-field tuple** — operator-readable categorization (artifact, identification, version, time, technical, plan, regime, safety).
- PDC-5 GOOD (71-95): OFFICIAL_NO_PICK_REQUIRED_FIELDS 18-field tuple.
- PDC-6 GOOD (97-105): OFFICIAL_PICK_NUMERIC_FIELDS 7-field tuple for type validation.
- PDC-7 GOOD (107-119): **OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES 11-cause set** (DATA_PROVIDER_DEGRADED / READINESS_FAILED / MARKET_CLOSED / WINDOW_MISSED / NO_SCORED_CANDIDATES / FILTERS_REMOVED_ALL / HARD_BLOCKED / SANITY_BLOCKED / RISK_GATE_BLOCKED / RUNTIME_FAILURE / UNKNOWN_POST_FILTER_GATING).
- PDC-8 GOOD (121-124): SAFETY_FLAGS 2-tuple.
- PDC-9 GOOD (127-137): _is_missing with **empty-dict/list-allowed but None/blank-string-rejected** documented policy.
- PDC-10 GOOD (140-141): _missing_required_fields list comprehension.
- PDC-11 GOOD (144-149): _validate_safety_flags with **explicit `is not False` check** (not `not value`) — handles truthy non-False values like 1/"true". ✅ Operator-correct.
- PDC-12 GOOD (152-165): _validate_numeric_fields with **type-cast + range-check (non-negative for score/risk_reward/quantity/risk_dollars; positive for entry/stop_loss/take_profit).**
- PDC-13 GOOD (168-200): validate_official_pick with **5 validation passes** + **list-of-errors return (no exception thrown)** — operator-test-friendly.
- PDC-14 GOOD (177): `f"missing required field: {field}"` — operator-readable per-error.
- PDC-15 GOOD (188-198): 3 type-validation guards (score_components mapping / risk_flags list / invalidation_conditions list).
- PDC-16 GOOD (203-241): validate_official_no_pick mirror with **primary_cause whitelist check.**
- PDC-17 GOOD (236-237): `watch_only_available not in {True, False}` — boolean coerce check.
- PDC-18 GOOD (244-251): validate_official_decision dispatcher.
- PDC-19 GOOD (254-268): contract_summary JSON-safe export with **paper_trading_enabled: False + live_trading_enabled: False explicit.** ✅ Safety-by-default.

## src/premarket_filter.py — LINE BY LINE (smallest in batch — 25 lines)

- PF-1 GOOD (1): 1-line docstring.
- PF-2 GOOD (4-5): gap_check signature with **2 named thresholds.**
- PF-3 GOOD (10-15): yfinance fast_info + **dual-key fallback** (previousClose / previous_close + lastPrice / last_price / regularMarketPrice).
- PF-4 BUG-T30 (15-16): Missing data → `(True, 0.0, "no premarket data — allow")` = **fail-OPEN.** Operator-archaeology says "allow" — possibly intentional but **un-flagged in cross-module risk philosophy.** Per Theme T30.
- PF-5 GOOD (17-22): 3-branch dispatch (gap-up / gap-down / OK).
- PF-6 GOOD (23-24): Exception → `(True, 0.0, "...failed — allowing")` = **fail-OPEN.** Operator-explicit comment.
- PF-7: **Module is operator-correct (intentional fail-OPEN with documented reason)** but **inconsistent with B66 MG-5 fail-OPEN-WITHOUT-DOCUMENTATION** which is the actually-buggy one.

## src/premarket_readiness_gate.py — LINE BY LINE

- PRG-1 GOOD (1-11): 11-line docstring with **fail-closed mandate explicit.**
- PRG-2 GOOD (18-19): 2 named defaults (25% min coverage + 25 min count).
- PRG-3 GOOD (22-26): _safe_int with `value or 0` — handles None.
- PRG-4 GOOD (29-33): _safe_float duplicate (**27th instance** — Theme T8).
- PRG-5 GOOD (36-75): _provider_attempt_summary with **6-counter aggregate + 4-counter ohlcv-stage** — operator-readable telemetry.
- PRG-6 GOOD (38-39): isinstance dict guards.
- PRG-7 GOOD (78-191): build_premarket_readiness_decision with **5-status dispatcher.**
- PRG-8 GOOD (78-85): keyword-only args + 2 default kwargs.
- PRG-9 GOOD (94-101): Input sanitization with **clamping** (min_fetch_coverage to [0,1] + min_fetched_count to ≥1).
- PRG-10 GOOD (107-114): 4 warning categories (rate_limited / unauthorized / ohlcv_empty / ohlcv_errors).
- PRG-11 GOOD (116-128): not_ready_empty_universe early-return with **NO_PICK_DATA_READINESS_FAILED + 11-key payload.** ✅ Schema-stable.
- PRG-12 GOOD (130-142): not_ready_no_market_data with **NO_PICK_DATA_PROVIDER_DEGRADED.**
- PRG-13 GOOD (144-159): not_ready_low_market_data_coverage with **fetched/universe ratio in human_readable_summary.**
- PRG-14 GOOD (166-178): **not_ready_provider_degraded with 3-condition AND gate** (≥10 attempts + 0 successes + errors+empty ≥ attempts).
- PRG-15 GOOD (180-191): Pass case with `passed=True + status=ready + empty primary_no_pick_cause` — schema-stable.
- PRG-16 GOOD (194-196): assert_premarket_readiness_or_no_pick wrapper.

## src/premarket_sanity_gate.py — LINE BY LINE

- PSG-1 GOOD (1-13): 13-line docstring with **4 explicit non-behaviors.**
- PSG-2 GOOD (20-23): 4 ACTION_* constants + ACTIONABLE_ACTIONS subset.
- PSG-3 GOOD (28-34): _safe_float duplicate (**28th instance**).
- PSG-4 GOOD (37-41): _extract_entry_stop with **plan-or-pick-fallback chain.**
- PSG-5 GOOD (44-156): evaluate_premarket_sanity with **7 sequential guards + 4 action dispatches.**
- PSG-6 GOOD (54-57): Defensive type checks for plan dict + market_snapshot.
- PSG-7 GOOD (59-69): **Base WATCH_ONLY skeleton + 7-key audit dict** with `actionable: False` default (fail-CLOSED).
- PSG-8 GOOD (71-93): 3 sequential WATCH_ONLY guards (entry / stop_loss / current_price).
- PSG-9 GOOD (99-105): global_action == "skip_all" → SKIP_TODAY ("broad market risk").
- PSG-10 GOOD (107-113): **Price ≤ stop_loss → SKIP** with operator-readable price comparison.
- PSG-11 GOOD (115-121): **Negative gap eats >60% of SL buffer → SKIP.** ✅ Sophisticated guard.
- PSG-12 GOOD (123-130): gap_pct ≥ 3% → HALF_SIZE chasing-risk + **size_multiplier=0.5.**
- PSG-13 GOOD (132-139): global_action == "half" → HALF_SIZE.
- PSG-14 GOOD (141-148): negative gap ≤ -1.5% → HALF_SIZE careful-fill.
- PSG-15 GOOD (150-156): Default SAFE with size_multiplier=1.0.
- PSG-16 GOOD (159-166): _apply_half_size with **in-place plan mutation + 2 audit fields** (premarket_size_multiplier + premarket_sanity_reason).
- PSG-17 GOOD (169-205): apply_premarket_sanity_decisions with **per-candidate sanity + 4 sanity-fields stamped + tuple (official, blocked) return.**
- PSG-18 GOOD (208-222): fetch_latest_price with **5d history + Close.iloc[-1] + None-on-fail defensive.**
- PSG-19 BUG (215): Inline import yfinance. **35th cross-cutting.**
- PSG-20 BUG (220): bare Exception → None. Theme T1.
- PSG-21 GOOD (225-279): fetch_market_snapshot with **SPY/QQQ/SOXX/VIX 4-symbol fetch + per-symbol _pct_change + 4-tier global_action dispatch.**
- PSG-22 GOOD (252-264): SPY ≤ -1.5% → skip_all + VIX ≥ 25 → skip_all + SOXX ≤ -2% → semi sector warning. **Operator-readable thresholds.**
- PSG-23 BUG (234, 241): 2 inline imports + 2 bare Exception.
- PSG-24 GOOD (282-300): run_premarket_sanity_gate **end-to-end orchestrator** with snapshot + per-candidate price + apply.

## src/probability_engine.py — LINE BY LINE

- PE3-1 GOOD (1-25): **25-line docstring with HONEST STATUS section + 6-Layer architecture + 3-replaces enumeration + 3 doc references.** Gold standard humility.
- PE3-2 GOOD (12-15): **"REAL integration, HEURISTIC math... future v0.2 will replace combiner with logistic regression"** — operator-trust + roadmap visibility. ✅
- PE3-3 BUG (33-35): `sys.path.insert(0, ...)` at module top — **side-effect at import time. 19th cross-cutting.**
- PE3-4 GOOD (49-55): REGIME_ADJUSTMENTS 5-key dispatch table.
- PE3-5 GOOD (53): "Finding #5: SPY -2 to -5% from SMA" archaeology comment for chop regime.
- PE3-6 GOOD (57-65): NEWS_ADJUSTMENTS 6-bucket table.
- PE3-7 GOOD (67-73): CATALYST_ADJUSTMENTS 4-bucket table with day-thresholds.
- PE3-8 GOOD (77): DEFAULT_P_WIN_PRIOR = 0.50 with comment "later: actually compute from picks_log.csv" — roadmap visibility.
- PE3-9 GOOD (82-91): SignalState @dataclass with 7 fields.
- PE3-10 GOOD (94-124): ProbabilisticDecision @dataclass with **17 fields + adjustments_applied audit trail + to_dict method.** ✅
- PE3-11 GOOD (129-137): _classify_news with **5-tier × 2-sentiment dispatch.** Critical: `score >= 0.9 + sentiment != bullish → strong_negative` — symmetry handled.
- PE3-12 GOOD (140-150): _classify_catalyst 4-bucket dispatch.
- PE3-13 GOOD (153-161): _confidence_label with **3-tier (low/medium/high) based on n_signals + p_win-vs-0.5 strength.**
- PE3-14 GOOD (166-272): compute_probabilistic_decision **6-layer sequential pipeline.**
- PE3-15 GOOD (191-204): Layer 1 with **base_sl + base_tp from stock_stats + safe-default fallback (2.0 + 1.5) + adjustments_applied stamp.**
- PE3-16 GOOD (212-220): Layer 2 regime with **n_signals counter only if not "unknown"** — prevents fake signal counting.
- PE3-17 GOOD (222-229): Layer 3 news with **same not-neutral counter discipline.**
- PE3-18 GOOD (231-239): Layer 4 catalyst with **same not-far counter discipline.**
- PE3-19 GOOD (242-245): Layer 4b watchlist with **>0.05 threshold + small-contribution comment.**
- PE3-20 GOOD (247-253): Layer 5 combine + clip with **3 invariants** (p_win clamp [0.05, 0.95] + sl_pct floor 0.5 + R:R ≥ 1.2 enforcement).
- PE3-21 GOOD (255-269): Layer 6 conversion with **2-decimal price rounding + 4-decimal pct rounding + buy_zone ±0.5% + trigger +0.3%.**
- PE3-22 GOOD (277-290): format_decision with **operator-readable 7-line emoji-prefixed output + audit-trail line.**
- PE3-23 GOOD (295-353): **__main__ with 4 distinct test scenarios** (base / bull+positive / bear+earnings / best-case). **24th __main__ + most-comprehensive smoke test.**

## src/risk_metrics.py — LINE BY LINE

- RKM-1 GOOD (1-19): 19-line docstring with **convention statement + usage example.**
- RKM-2 GOOD (24-27): 3 named consts.
- RKM-3 GOOD (30-40): _load_closed_chrono with **dual-status filter + chronological sort with fallback.**
- RKM-4 BUG (33): No `newline=""`.
- RKM-5 GOOD (43-47): _f duplicate (**29th instance**).
- RKM-6 GOOD (50-58): _sharpe with **n<2 None + sd==0 None defensive guards.**
- RKM-7 GOOD (61-71): _sortino with **downside-only deviation + n<2 None + dd==0 None.** ✅ Pure-stdlib statistics.
- RKM-8 GOOD (74-94): _max_drawdown with **equity curve construction + peak tracking + trough_idx.** Operator-readable.
- RKM-9 GOOD (97-140): compute_risk_metrics with **dual returns% + R-multiples computation + naive 50-trade/year annualization + 14-key result.**
- RKM-10 GOOD (101-102): Empty closed → 2-key skeleton (schema-stable).
- RKM-11 GOOD (118): "Naive annualization: assume avg trade ≈ 5 trading days... sqrt(50) ≈ 7.07" — operator-archaeology + math made explicit. ✅
- RKM-12 GOOD (122-124): Calmar formula with abs() + None-when-DD-zero.
- RKM-13 GOOD (126-140): 14-key result including **`sample_warning: n < 30`** ✅ + dual %-vs-R-multiple metrics.
- RKM-14 GOOD (143-166): format_risk_text with **sample warning + 8-line aligned plain-text table + em-dash for None values.**

## src/theme_scoring_guardrails.py — LINE BY LINE

- TSG-1 GOOD (1-7): 7-line docstring with **explicit-reviewed-change mandate.**
- TSG-2 GOOD (15-21): FUTURE_THEME_SCORING_FIELDS 5-tuple — operator-readable schema.
- TSG-3 GOOD (23-31): REQUIRED_PREREQUISITES **7-tuple** (historical_validation / forward_observation / train_test_discipline / overfitting_review / clear_tests / founder_approval / readiness_gate_preserved). **Documents the validation discipline before unlock.** ✅
- TSG-4 GOOD (33-40): THEME_SCORING_SAFETY_FLAGS 6-key all-False dict.
- TSG-5 GOOD (43-54): **`@dataclass(frozen=True)` ThemeScoringStatus** with **6 boolean fields all default False + 2 tuple fields.** **4th audited frozen dataclass.** Per B69 SS-X1 sibling.
- TSG-6 GOOD (57-59): theme_scoring_status as_dict export.
- TSG-7 GOOD (62-84): assert_theme_scoring_disabled with **4-key enabled-set check + sorted joined error.**
- TSG-8 GOOD (87-94): explain_theme_scoring_guardrail human-readable wrapper.

## src/wow_trend.py — LINE BY LINE

- WT-1 GOOD (1-7): 7-line docstring with **getting better/worse/flat philosophy.**
- WT-2 BUG (14-16): _to_float duplicate (**30th instance** — Theme T8 NOW 30 modules).
- WT-3 GOOD (19-29): _within with **end-exclusive comment + dual-key fallback (evaluated_on / pick_date) + ISO date split.**
- WT-4 BUG (27): bare Exception continue.
- WT-5 GOOD (32-47): _summarize with **None-skeleton + filtered-list aggregates + max(len, 1) div-by-zero guard.**
- WT-6 GOOD (50-67): compare with **today injectable + 3-window construction + per-metric delta dict.**
- WT-7 GOOD (54-55): `start_this = today - 7d` and `start_last = today - 14d` — operator-readable.
- WT-8 GOOD (70-75): _arrow with **good_positive flag** for metrics where higher-is-bad (e.g., drawdown).
- WT-9 GOOD (78-106): format_footer with **'' return if no prior baseline + 5-line Telegram block + alpha-line conditional.**

## CONSOLIDATED CROSS-CUTTING (THIS BATCH)

### NEW Theme T34 (LLM PROVIDER CASCADE)
- **LLM-X1** rationale: Claude → Gemini → OpenAI → rule-based + per-provider quota latch + 12h cache + 1.5s throttle
- **NC-X1** news classify: Claude → 21-keyword heuristic
- **MN-X1** market sentiment: Claude (SDK) → Gemini (REST, no SDK) → 6-key default skeleton

**PROBLEM:** 3 modules independently implement Claude→fallback cascades. **CLAUDE_MODEL = "claude-sonnet-4-5"** hardcoded in 3 places (Theme T2 16th drift). **Recommend:** create `src/llm_router.py` with shared cascade + single CLAUDE_MODEL source.

### Theme T30 (FAIL-OPEN vs FAIL-DEFENSIVE) UPDATE
| Module | Mode | Documented |
|---|---|---|
| B66 MG-5/6 spy_trend | fail-OPEN bullish | ❌ undocumented (BUG) |
| B68 RG-X1 market_regime | fail-DEFENSIVE transition 0.8× | ✅ "Finding #4 fix May 4 2026" |
| B68 RM-X1 risk_mult | fail-DEFENSIVE 0.7× unknown | ✅ "anti-over-size" |
| **B70 PF-X1 gap_check** | **fail-OPEN allow** | **✅ "no premarket data — allow"** |
| **B70 FH-X1 cross_validate_price** | **fail-OPEN is_valid=True** | **✅ "don't punish for infra issues"** |

**4 of 5 instances are documented; only MG-5 fail-OPEN is undocumented + therefore the bug.**

### Theme T6 (ATOMIC WRITES) UPDATE
| Module | Status |
|---|---|
| B69 DS-X1 _save_sent | ✅ ATOMIC (9th) |
| **NE-7 _save_seen** | ❌ unsafe (50th) |
| **MN-8 cache.write_text** | ❌ unsafe (51st) |

**Tally: 9 safe / 51 unsafe / 60 = ~85% UNSAFE.**

### Theme T8 (DRY) UPDATE
- _safe_float / _to_float / _f duplicates: **30 modules** (PRG-4 + PSG-3 + WT-2 + RKM-5 add 4 this batch). **30 IS BREAKING POINT.**
- Keyword-bag-of-words modules: **6 vocabularies** (NC-10 adds 21-keyword 6th).
- CLAUDE_MODEL hardcoded: **3 modules** (LLM-X1 + NC-X1 + MN-X1).

### Theme T13 (SCHEMA-STABLE) — heaviest batch yet
- FH-X1 27-field skeleton + 6-key cross_validate result
- FN-X1 0.5 default if no fundamentals
- LLM-X1 _try_provider tuple return
- NE-X1 8-field item normalization
- NC-X1 9-field schema-stable Claude+heuristic
- MN-X1 6-field default skeleton
- PDC-X1 27-field + 18-field + 7-numeric required tuples
- PRG-X1 11-key schema-stable across all 5 statuses
- PSG-X1 7-key audit dict + 4-action dispatch
- PE3-X1 17-field ProbabilisticDecision + adjustments_applied trail
- RKM-X1 14-key with sample_warning + 2-key empty skeleton
- TSG-X1 6-key safety flags
- WT-X1 None-skeleton on empty + structured deltas

**13 schema-stable modules this batch — gold-standard discipline.**

### Theme T14 (gold standard) — also heaviest
- FH-X1 E2c cross_validate archaeology + intentional fail-OPEN-with-comment + Finnhub-marketCap-millions converter
- FN-X1 11-dimension auto-renormalization (handles missing fields)
- LLM-X1 backward-compat naive→TZ-aware cache normalization + per-provider quota-latch + 4-provider cascade + sentence-completion mandate
- LT-X1 5 design principles + technical-channel-stays-unchanged + 2026-05-05 bug-fix archaeology + 6-line per-pick output preserving all actionable data
- NE-X1 polite 0.2s sleep + per-source caps + TZ-aware cutoff prune-on-save
- NC-X1 9-field JSON contract + 21-keyword heuristic fallback + Alpaca-priority sort
- MN-X1 schema-fill-from-default robust JSON parse + Gemini-via-REST (no SDK)
- PDC-X1 27-field required + 11-cause primary_no_pick taxonomy + safety_flags=False explicit + behavior-neutral mandate + list-of-errors return
- PRG-X1 fail-CLOSED to no_pick + 5-status dispatcher + clamping defensive
- PSG-X1 7-sequential-guards + size_multiplier in-place mutation + 4-tier global_action market snapshot
- PE3-X1 HONEST STATUS docstring + 25-line module docstring + 6-Layer architecture + Layer 5 invariants (p_win clamp + R:R ≥ 1.2) + 4-scenario __main__
- RKM-X1 pure-stdlib Sharpe/Sortino/MaxDD/Calmar + sample_warning n<30 + dual %-vs-R metrics
- TSG-X1 7-prerequisite tuple + frozen dataclass + safety-by-default
- WT-X1 good_positive flag for arrow direction

### Cross-cutting tally summary (this batch only)
| Metric | Before | This batch | After |
|---|---:|---:|---:|
| _safe_float duplicates | 26 | 4 | **30 modules** ⚠️ |
| Bare-except | mod | 14 | continues moderate |
| Inline imports | 31 | 5 (FH-21 + LLM-16,18,18,20 + NC-5 + MN-13 + PSG-19,23 = ~9) | **~40 cumulative** |
| Import-time side effects | 15 | 4 (FH-3 + LLM-3 + MN-2 + PE3-3 sys.path) | **19** |
| Unsafe writers | 49 | 2 (NE + MN) | **51 / 60 = ~85% UNSAFE** |
| Atomic writers | 9 | 0 | **9** |
| TZ-aware modules | 19 | 2 (LLM-X1 + NE-X1) | **21** |
| Naive datetime usage | catalog | 4 (FH-8 + NC-9 + others) | **catalog ongoing** |
| DATED archaeology | 37 | 6 (FH E2c + LLM RPM + LT 2026-05-05 + NE Alpaca + PE3 Finding#5 + chop regime) | **43** |
| Frozen dataclasses | 3 | 1 (TSG ThemeScoringStatus) | **4** |
| Regular dataclasses | 8 | 2 (PE3 SignalState + ProbabilisticDecision) | **10** |
| OBSERVE-MODE modules | 25 | 1 (PE3 explicit) | **26** |
| __main__ smoke tests | 25 | 4 (NE + NC + MN + PE3) | **29** |
| Pure-stdlib statistical | 2 | 1 (RKM) | **3** |
| **NEW Theme T34 LLM cascade** | new | 3 modules | **3** |
| Theme T30 fail-modes | 3 | 2 (FH + PF, both documented) | **5** (1 unintended) |

## SUMMARY (Batch 70 — 15-FILE)

| File | Show-stop | Data/safety | Code smell | Good code | Findings |
|---|---:|---:|---:|---:|---:|
| finnhub_data | 5 | 0 | 0 | 23 | 28 |
| fundamentals | 0 | 0 | 0 | 15 | 15 |
| llm_agent | 6 | 0 | 0 | 19 | 25 |
| layman_translator | 0 | 0 | 0 | 21 | 21 |
| news_engine | 5 | 0 | 0 | 15 | 20 |
| news_classifier | 3 | 0 | 0 | 13 | 16 |
| market_news | 5 | 0 | 0 | 16 | 21 |
| premarket_decision_contract | 0 | 0 | 0 | 19 | 19 |
| premarket_filter | 1 | 0 | 0 | 6 | 7 |
| premarket_readiness_gate | 1 | 0 | 0 | 15 | 16 |
| premarket_sanity_gate | 4 | 0 | 0 | 20 | 24 |
| probability_engine | 1 | 0 | 0 | 22 | 23 |
| risk_metrics | 1 | 0 | 0 | 13 | 14 |
| theme_scoring_guardrails | 0 | 0 | 0 | 8 | 8 |
| wow_trend | 2 | 0 | 0 | 8 | 10 |
| **TOTAL** | **34** | **0** | **0** | **233** | **267** |

## TOP 15 CRITICAL FIXES from Batch 70

1. **NEW Theme T34 (HIGH-IMPACT consolidation):** Create `src/llm_router.py` consolidating LLM-X1 + NC-X1 + MN-X1 cascades into single shared helper. **Single CLAUDE_MODEL source-of-truth.** **3 hardcoded "claude-sonnet-4-5" instances reduced to 1.** (1.5 hours)
2. **_safe_float / _to_float NOW 30 MODULES (Theme T8 BREAKING POINT):** Execute consolidation immediately. (1 hour with import migration)
3. **Theme T30 fix scope refined:** **MG-5/6 spy_trend is the ONLY UNINTENDED fail-OPEN.** PF-X1 + FH-X1 fail-OPEN are intentional + documented. **Single-module fix scope** vs original 5-module concern. (10 min)
4. **NE-7 + MN-8 (2 unsafe writers this batch):** Apply DS-X1 atomic pattern. (5 min each)
5. **Inline imports now ~40 cumulative:** FH-21 + LLM-16/18/20 + NC-5 + MN-13 + PSG-19/23 = 9 this batch. **CRITICAL: bulk hoist all to module top.** (15 min for ~40 modules)
6. **Import-time side effects now 19:** FH-3 + LLM-3 + MN-2 + PE3-3 sys.path-insert. **Defer to first call OR use __init__.** (10 min)
7. **PE3-3 sys.path.insert AT IMPORT TIME:** Affects entire Python process. **Move into `if __name__ == "__main__"` block.** (1 min)
8. **PSG-X1 + RKM-X1 + WT-X1 + TSG-X1 (Lane 1 docs):** Document Lane 1 production-readiness pipeline (PRG → scoring → PSG → PDC contract) in `docs/LANE_1_PIPELINE.md`. (30 min)
9. **CR-X1 (B69) + SC-X1 + LLM CLAUDE_MODEL drift = ALL 3 hardcoded-cache cases:** Bundle Theme T28 review with single owner. (1 hour)
10. **PE3-X1 PROBABILITY ENGINE v0.1 → v0.2 roadmap:** Document v0.1→v0.2 logistic-regression-replaces-heuristic plan in `docs/PROBABILITY_ENGINE_V02.md`. (45 min)
11. **PE3-2 OBSERVE-MODE catalog (26 modules):** Update `docs/OBSERVE_MODE_DISCIPLINE.md` with PE3-X1 honest-status pattern. (5 min)
12. **PDC-X1 27-field validation:** Verify all premarket pick producers (main.py + parallel_scorer + premarket_sanity_gate) actually emit all 27 fields — likely some misses. (45 min audit)
13. **TSG-X1 7-prerequisite checklist:** Bind to actual progress tracker — currently abstract. Should map to specific PR or doc per prerequisite. (20 min)
14. **MN-17 schema-fill-from-default pattern:** Adopt across other LLM modules in this batch. Currently only MN-X1 has this robustness. (20 min)
15. **PSG-X1 fetch_market_snapshot:** SPY/QQQ/SOXX/VIX 4-symbol parallel fetch — currently sequential. Could parallelize for 4× speedup. (30 min)

## NEW THEMES UPDATED

- **NEW Theme T34 (LLM provider cascade):** 3-module independent implementations + 3 hardcoded CLAUDE_MODEL strings. Top consolidation candidate.
- **Theme T30 (fail-mode):** SCOPE-NARROWED — only MG-5/6 is unintended; PF-X1 + FH-X1 are intentional + documented.
- **Theme T28 (hardcoded-cache renewal):** CR-X1 (B69 CRITICAL) + SC-X1 + LLM CLAUDE_MODEL × 3 = 5 instances need bundled review.
- **Theme T8 (DRY):** _safe_float at **30 MODULES — BREAKING POINT.**
- **Theme T13 (schema-stable):** **13 modules this batch — heaviest single batch.**
- **Theme T14 (gold standard):** **14 modules this batch — also heaviest.**
- **Theme T29 (pure-stdlib statistical):** RKM-X1 joins SA + HE = **3 audited modules.**
- **Theme T2 (drift):** 16th instance — CLAUDE_MODEL hardcoded in 3 places.

## COVERAGE TRACKER

| Phase | Status | Cumulative |
|---|---|---:|
| Phase G | done | 30/~30 |
| Phase H | started | 0/~30 |
| Total true line-by-line | **+15 files (15 successful, 0 failures)** | **221 of ~378 (~58.5%)** |

**🎯 58.5% AUDIT MILESTONE. Phase G COMPLETE. Lane 1 production-readiness pipeline (PRG → PSG → PDC) FULLY AUDITED. LLM cascade triple-implementation identified for consolidation.**

## NEXT BATCH (15-FILE)

Batch 71: Phase H. Candidates:
- backtester/ subdirectory files
- patterns/ subdirectory files (16 detectors per B61 PA reference)
- market_data_providers/ subdirectory files
- Plus remaining src/: hard_blocks (B65 already), indicators (B63 retry), market_calendar (B66 already), market_data_health (B66 already), market_guard (B66 already), missing_data_gate, nightly_conductor (B65 already), official_artifact_loader, official_pick_artifact, opening_range_scanner, paper_trader, parallel_scorer (B66 already), pause_state (B69 already), performance_*, pick_evaluator (B64 already), pick_logger, picks_csv, portfolio_risk_gate, position_monitor, quarterly_report, scorer (B62 already), self_awareness (B65 already), signal_journal (B66 already), smell_faculty (B65 already), stock_stats, weekly_review (B65 already), wisdom_base (B49 already), wisdom_coverage, wisdom_hint (B65 already), yearly_report

End of Batch 70. **🎯 58.5% audit milestone. NEW Theme T34 (LLM cascade) catalogged. Lane 1 pipeline COMPLETE.**
