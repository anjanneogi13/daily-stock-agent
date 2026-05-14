# Batch 67 — 13-FILE BATCH (2 failed) — TRUE LINE-BY-LINE — PILLAR 3+4 LEARNING LOOP

**Date:** 2026-05-12
**Files (13):** watchlist_manager (191), news_sentiment (46), news_signals (384), pattern_layer (131), pattern_engine (80), pattern_stats (106), hypothesis_engine (184), calibration (387), weight_proposer (282), weight_applier (233), lesson_gc (144), learning_journal (69), auto_promote (166)
**FAILED:** intraday_monitor.py, monitor_loop.py — fetch errors (likely size/path). Will retry next batch.
**Phase:** F (final) + Phase G (Pillar 3+4 closure). **Total LOC audited this batch: ~2,403 lines.**

## TOP HEADLINE FINDINGS (one per file)

1. **WM-X1: watchlist_manager.py** is **THE 3-DAY ROLLING NEWS-FRESHNESS BOOSTER** (191 lines). PR #68 archaeology: **5-tier freshness multiplier** (<4h=2.0× / <8h=1.5× / <24h=1.0× / <48h=0.6× / ≥48h=0.3×) + ±0.30 boost cap. Per Batch 65 NS-X2 cross-cutting catalysts — **complementary fresh-news amplifier**.
2. **NSE-X1: news_sentiment.py** (46 lines, **smallest in batch + 2nd smallest in audit**) is **THE YAHOO-RSS KEYWORD SCORER** with 28+30 word lists + dampened net-per-article formula → [0.05, 0.95]. **Per B65 NC-X2 + B40 cross-cutting keyword-list — 4th audited keyword-bag-of-words module.**
3. **NSI-X1: news_signals.py** is **THE PR #77 CATALYST→SCORE MAPPER** (384 lines). 12-row CATALYST_RULES dict (7 bullish + 5 bearish) + 11-keyword CATASTROPHIC list + **30-phrase NEGATIVE_REACTION list** + atomic_write + last-write-wins-merge with abs(delta) prefer + 180-day catastrophic TTL + EVC-style "good-news-sold" detection. **Producer for B65 HB-20 _block_catastrophic_news consumer.** **3rd audited atomic writer.**
4. **PL-X1: pattern_layer.py** is **T49 / Pillar 3 Layer 6 — THE PATTERN×REGIME EDGE MULTIPLIER** (131 lines). Returns multiplier ∈ [0.85, 1.15] from pattern_stats lookup. **auto_enable_disable kills patterns with mean_r ≤ -0.30 AND n ≥ 30.** **Producer for B66 PS2 parallel_scorer consumer.** **Closes Pillar 3 Layer 6 chain.**
5. **PE2-X1: pattern_engine.py** (80 lines, smallest single-purpose) is **THE PER-TICKER DETECTOR DISPATCHER**. Iterates ALL_DETECTORS, writes to data/patterns.jsonl with date+ticker+regime stamps. Per Batch 65 NC2-6 + B62 PR-X1 cross-cutting registry pattern — **3rd audited registry consumer.**
6. **PS3-X1: pattern_stats.py** is **THE pattern.jsonl × picks_log.csv JOIN AGGREGATOR** (106 lines). Joins on (ticker, date) → per-(pattern, regime) bucket with n / wins / win_rate / mean_r / total_r. **Producer for PL-X1 + auto_promote + hypothesis_engine.**
7. **HE-X1: hypothesis_engine.py** is **PILLAR 1 LAYER 4 — STATISTICAL EDGE/DRAG DETECTOR** (184 lines). **Pure stdlib binomial CDF (no scipy)** + 2-sided p-value vs base_rate + 4-class output (edges / drags / low_sample / summary). **OBSERVE-MODE explicitly stated** in docstring + report footer. **3rd audited Pure-stdlib statistical module** (after B66 SA-X1 Wilson + binomial here).
8. **CL-X1: calibration.py** is **T37+T38 — THE 5-FACTOR×PER-MONTH ATTRIBUTION ENGINE** (387 lines). 4 bucketers (rsi/score/atrpct/month) + BucketStat @dataclass + per_factor_report + per_timeframe_report + 4-CLI sub-commands + telegram_footer_lines + open_proposals_summary. **Producer for B65 NC2-9 _step_calibration_propose consumer.**
9. **WP-X1: weight_proposer.py** is **T39 — THE READ-ONLY PROPOSAL GENERATOR** (282 lines). Proposal @dataclass + 4-class action (boost/penalize/kill/None) + ±5% delta cap + √n confidence scaling + bias_R thresholds (+0.10/-0.10/-0.30+wr<35%). **Per Batch 65 NC2-9 cross-cutting** — producer for WA-X1.
10. **WA-X1: weight_applier.py** is **T44 / Pillar 4 — WEEKLY-CAPPED MUTATOR** (233 lines). 5%/week-per-(factor, ISO-week) cap + multiplier floor 0.0/ceil 1.5 + idempotent proposal_id dedup + dual-journal (weight_history + learning_journal). **Per B57 weight_applier-related cross-cutting + this batch LJ-X1 producer-consumer.**
11. **LG2-X1: lesson_gc.py** is **T32 — THE LESSON STALE-DEACTIVATOR** (144 lines). 90-day default + 0.90 protect_conf + active=False (never delete) + deactivated_at + deactivated_reason. **NEVER DELETE archaeology — preserves audit trail.** Per B49 WB-X1 cross-cutting wisdom_base consumer.
12. **LJ2-X1: learning_journal.py** (69 lines, **smallest in batch**) is **THE BRAIN-MUTATION APPEND-ONLY LOG**. 5-kind enum + days-cutoff filter + by_kind summary. **Producer for B65 MB-X1 meta_brain consumer + B65 WR-X1 weekly_review consumer + B65 NC2-X1 nightly_conductor producer + this batch WA-X1 producer.** **Most-cross-referenced module in entire audit.**
13. **AP-X1: auto_promote.py** is **T29 — THE PATTERN→LESSON BRIDGE** (166 lines). 4-criteria gate (sample≥40 + p≤0.01 + signal in KNOWN + effect ∈ {drag, edge}) + **idempotency via auto_promote:{signal}:{bucket} marker tag** + confidence-from-p clamped to [0.7, 0.95]. **Closes pattern→wisdom learning loop.**

## CRITICAL CROSS-FILE FINDINGS (this batch)

- **PILLAR 3+4 LEARNING LOOP NOW FULLY AUDITED END-TO-END:**  
  PE2 (detector dispatch) → PS3 (stats aggregation) → PL (multiplier consumer + auto_enable_disable) → AP (pattern→lesson promotion) → wisdom_base → wisdom_hint (B65 WH-X1 consumer) + LG2 (stale GC). **6-module Pillar 3+4 chain COMPLETE.**
- **CALIBRATION → PROPOSAL → APPLICATION CHAIN COMPLETE:**  
  CL (per_factor_report) → WP (propose with 4-action class) → WA (apply with 5%/wk cap) → LJ2 (journal). **4-module calibration chain COMPLETE.**
- **OBSERVE-MODE EXPLICIT TALLY:** HE-X1 docstring + format_report footer "OBSERVE-MODE: No weights auto-changed" — **22nd → 23rd audited OBSERVE-MODE module.**
- **ATOMIC WRITE TALLY UPDATE:** **8 safe / 41 unsafe / 49 = ~84% UNSAFE.** NSI-X1 _save_signals adds 8th safe writer (tmp + replace). Most other writers in this batch are append-only (jsonl) — acceptable.
- **PURE-STDLIB STATISTICAL MODULES:** SA-X1 (B66 Wilson CI) + HE-X1 (this batch binomial CDF) — **NEW Theme T29: pure-stdlib statistical discipline** (no scipy/numpy dependencies in core decision modules).
- **KEYWORD-BAG-OF-WORDS DUPLICATION (Theme T8):** 4 modules: B53 NS-3 + B65 NC-X2 + B40 UN cross + this batch NSE-X1. **Plus this batch NSI-X1 ADDS 30-phrase NEGATIVE_REACTION list** as 5th vocab. Strong consolidation case.

## src/watchlist_manager.py — LINE BY LINE

- WM-1 GOOD (1-7): 7-line docstring with PR #68 archaeology.
- WM-2 GOOD (13-15): 3 named constants (path/TTL/MIN_SCORE).
- WM-3 GOOD (18-24): _load with 2-tier defensive (file missing or parse fail).
- WM-4 BUG (22): bare Exception → empty. Theme T1.
- WM-5 BUG (27-29): _save **NOT ATOMIC.** **42nd unsafe writer.** Critical because called on every news batch — partial write would corrupt watchlist used by next morning's universe expansion.
- WM-6 GOOD (32-42): _prune_expired with **TZ-aware UTC cutoff** + Z→+00:00 normalization.
- WM-7 BUG (40): bare Exception continue.
- WM-8 GOOD (45-52): _hours_old with **999.0 ancient-default sentinel.**
- WM-9 GOOD (51): bare Exception → 999. Acceptable defensive.
- WM-10 GOOD (55-68): _freshness_multiplier with **5-tier docstring table** matching code branches. ✅
- WM-11 GOOD (71-115): add_from_news with **dedup-by-ticker + score-improvement-only update.**
- WM-12 GOOD (85-97): existing-ticker handling: **UPDATE only if new score > existing** + 7 fields refreshed.
- WM-13 GOOD (99-110): New-ticker entry has **9 fields** including action_window for downstream signals.
- WM-14 GOOD (118-122): get_watchlist with score-desc sort.
- WM-15 GOOD (125-133): get_watchlist_tickers with bullish_only filter (PR #68).
- WM-16 GOOD (136-162): watchlist_score_boost with **freshness-weighted base + ±0.30 cap + sentiment-sign flip.** ✅
- WM-17 GOOD (157-158): Cap clamp `max(-0.30, min(0.30, base))` BEFORE sentiment flip — prevents bearish from breaking cap.
- WM-18 GOOD (165-180): watchlist_meta with 8-key debug payload.
- WM-19 GOOD (183-191): __main__ smoke test pretty-prints. **18th __main__.**

## src/news_sentiment.py — LINE BY LINE

- NSE-1 GOOD (1): 1-line docstring.
- NSE-2 GOOD (5-9): POSITIVE 28-keyword set.
- NSE-3 GOOD (11-16): NEGATIVE 30-keyword set.
- NSE-4 GOOD (19-27): fetch_news via Yahoo RSS feedparser.
- NSE-5 BUG (25): bare Exception → []. Theme T1.
- NSE-6 GOOD (30-45): score_sentiment with **dampened net-per-article formula + 0.05/0.95 clamp** (avoids absolute confidence). ✅
- NSE-7 GOOD (33-34): Empty news → 0.5 neutral.
- NSE-8 GOOD (42): `net = (pos - neg) / max(n_articles, 1)` — div-by-zero defense.
- NSE-9 GOOD (44): Map to [0, 1] via 0.5 + net/4.0 → reasonable scaling.

## src/news_signals.py — LINE BY LINE

- NSI-1 GOOD (1-40): **40-line docstring with PROBLEM SOLVED archaeology + DATA FLOW diagram + CATALYST→SCORE table + CATASTROPHIC keyword examples.** Gold standard.
- NSI-2 GOOD (46-48): 3 named paths.
- NSI-3 GOOD (51-67): CATALYST_RULES 12-row dict with **inline tuples (delta, ttl_days)** + section comments BULLISH/BEARISH.
- NSI-4 GOOD (69-77): CATASTROPHIC_KEYWORDS **11-keyword + observed delisting + nasdaq letter "warning shots"** comment.
- NSI-5 GOOD (79-111): NEGATIVE_REACTION_PHRASES **30-phrase list** with EVC-style archaeology comment. Per cross-cutting catalyst-table theme.
- NSI-6 GOOD (114-115): _now_iso TZ-aware UTC.
- NSI-7 GOOD (118-121): _is_catastrophic 1-line keyword-any check.
- NSI-8 GOOD (124-130): _has_negative_reaction with **em-dash/en-dash normalization** + token squashing. ✅
- NSI-9 GOOD (133-142): _apply_negative_reaction_penalty: **converts +δ to small −0.01 to −0.03 penalty.** Operator-readable formula.
- NSI-10 GOOD (145-152): _load_signals defensive.
- NSI-11 BUG (151): bare Exception → {}. Theme T1.
- NSI-12 GOOD (155-160): **_save_signals IS ATOMIC** (tmp + replace). ✅ **8th audited atomic.**
- NSI-13 GOOD (163-174): _purge_expired with TZ-aware comparison.
- NSI-14 GOOD (179-253): add_signal_from_classification with **catastrophic-FIRST priority + confidence-weighted delta + last-write-wins-with-stronger-prefer.**
- NSI-15 GOOD (197-207): Catastrophic gets **180-day TTL + hard_block=True.**
- NSI-16 GOOD (211-217): Confidence modulation `min(1.0, max(0.3, score_pct / 0.7))` — operator-readable scaling formula.
- NSI-17 GOOD (240-249): **Existing-signal MERGE rule: hard_block always wins; otherwise prefer larger |delta|.** Schema-stable. ✅
- NSI-18 GOOD (258-272): get_ticker_signal with expiry check.
- NSI-19 GOOD (275-297): get_ticker_boost with auto-purge-on-expired.
- NSI-20 GOOD (300-314): is_hard_blocked returns (bool, reason) tuple. **Per B65 HB-20 cross-cutting consumer.**
- NSI-21 GOOD (317-356): rebuild_from_news_log with **lookback days + processed/added counters + final state log.**
- NSI-22 BUG (334, 344): 2 bare Exception. Theme T1.
- NSI-23 GOOD (359-373): stats with bullish/bearish/blocks classification + **M7 archaeology comment** "catches deltas <-0.5 too."
- NSI-24 GOOD (376-383): __main__ CLI with rebuild + stats subcommands. **19th __main__.**

## src/pattern_layer.py — LINE BY LINE

- PL-1 GOOD (1-12): 12-line docstring with **multiplier-range explicit + auto-disable rule.**
- PL-2 GOOD (20-23): 4 named constants + DISABLED_KEY sentinel.
- PL-3 GOOD (26-33): _get_edge with **MIN_SAMPLE_FOR_EDGE=20 gate + regime fallback to 'unknown'.**
- PL-4 GOOD (36-37): _is_disabled 1-line membership check.
- PL-5 GOOD (40-76): pattern_multiplier with **clamp to [0.85, 1.15] + per-detector confidence weighting.**
- PL-6 GOOD (61-63): No-track-record patterns return None edge → no contribution. ✅ Conservative.
- PL-7 GOOD (74): `raw = total_signal * 0.3` — squash factor with operator-readable inline rationale.
- PL-8 GOOD (75): Symmetric clamp via `max(-MAX_BOOST, min(MAX_BOOST, raw))`.
- PL-9 GOOD (79-91): disable/enable_pattern with persistent state via _ps.save.
- PL-10 GOOD (94-130): auto_enable_disable with **kill_threshold_r=-0.30 + min_n=30** archaeology cross-cutting B66 SJ2 calibration.
- PL-11 GOOD (105): Pre-disabled snapshot → enables reactivation detection.
- PL-12 GOOD (110-111): `any()` over regimes → kills if ANY regime is bad. Conservative.
- PL-13 GOOD (122-128): **Learning journal hook with try/except defensive wrap** — log pattern_disabled + pattern_enabled events. Per LJ2-X1 cross-cutting.
- PL-14 BUG (123): Inline import. **22nd cross-cutting.**

## src/pattern_engine.py — LINE BY LINE

- PE2-1 GOOD (1-6): 6-line docstring.
- PE2-2 GOOD (15): Module-level PATTERNS_LOG.
- PE2-3 GOOD (18-46): scan_ticker with **df-or-fetch shortcut for testability** + per-detector try/except + 4-field record stamp.
- PE2-4 BUG (28): bare Exception → []. Theme T1.
- PE2-5 BUG (26): Inline import data_fetcher. **23rd cross-cutting inline import.**
- PE2-6 GOOD (36): Per-detector exception → m=None → continue. **Don't let one broken detector kill all.** ✅
- PE2-7 GOOD (40-44): 4 enrichment fields (date / ticker.upper / direction / regime).
- PE2-8 GOOD (49-59): persist append + count return.
- PE2-9 BUG (56-58): **Append-only write.** Acceptable for jsonl audit trail (no atomic needed for append).
- PE2-10 GOOD (62-79): load_recent with per-line parse + days-cutoff filter.
- PE2-11 BUG (77): bare Exception continue.

## src/pattern_stats.py — LINE BY LINE

- PS3-1 GOOD (1-16): 16-line docstring with **example output JSON + downstream consumer list.**
- PS3-2 BUG (29-31): _to_float duplicate (**22nd instance**).
- PS3-3 GOOD (34-41): _read_jsonl mirror.
- PS3-4 BUG (40): bare except. Theme T1 worst form (caught earlier as PS-7 / MB-5 archaeology).
- PS3-5 GOOD (44-47): _read_picks 1-call.
- PS3-6 BUG (46): No `newline=""`.
- PS3-7 GOOD (50-91): build_stats with **(ticker, pick_date) join key + per-bucket accumulator + 5-key per-bucket result.**
- PS3-8 GOOD (66): defaultdict(lambda: {n,wins,rs}) initialized.
- PS3-9 GOOD (87-89): Div-by-zero guards `if n else 0.0`.
- PS3-10 GOOD (94-98): save with mkdir + trailing newline.
- PS3-11 BUG (97): **NO ATOMIC WRITE.** **43rd unsafe writer.** pattern_stats.json is read by pattern_layer + auto_promote — partial write would corrupt brain decisions next morning.
- PS3-12 GOOD (101-105): load 1-call.

## src/hypothesis_engine.py — LINE BY LINE

- HE-1 GOOD (1-17): 17-line docstring with **OBSERVE-MODE in caps.**
- HE-2 GOOD (23-24): 2 named thresholds.
- HE-3 GOOD (30-34): _binom_pmf with 4-edge-case handling (n<0/k<0/k>n + p=0/p=1).
- HE-4 GOOD (37-38): _binom_cdf 1-line sum.
- HE-5 GOOD (41-53): two_sided_p_value with **right-tail vs left-tail dispatch via expected check.** Mathematically correct.
- HE-6 GOOD (43-44): Edge cases n=0 + base_rate ∉ (0,1) → return 1.0 (no info).
- HE-7 GOOD (59-128): analyze with **3-class output (edges / drags / low_sample)** + per-bucket 7-field record.
- HE-8 GOOD (74-75): base_rate computed once across all rows.
- HE-9 GOOD (78-81): defaultdict + per-(signal, bucket) grouping.
- HE-10 GOOD (89-91): r_mults with **isinstance numeric filter** before mean.
- HE-11 GOOD (103-105): low_sample n<min_n bucket → no p-value calc + tagged separately. ✅
- HE-12 GOOD (107-113): p < alpha + win_rate vs base_rate dispatch into edges/drags.
- HE-13 GOOD (115-117): 3 sorts: edges by vs_base desc, drags by vs_base asc, low_sample by n desc.
- HE-14 GOOD (131-183): format_report with **═-line headers + 3-section dispatcher + OBSERVE-MODE footer.**
- HE-15 GOOD (181): "No weights auto-changed. You decide what to act on." — operator-trust-preserving disclaimer. ✅

## src/calibration.py — LINE BY LINE

- CL-1 GOOD (1-20): 20-line docstring with **6-line CLI usage block.**
- CL-2 GOOD (31): RESULTS_ROOT module const.
- CL-3 GOOD (36-46): list_runs + latest_run with **sorted oldest→newest** ordering.
- CL-4 GOOD (49-70): load_picks with **per-row numeric coercion of 9 fields** with None/empty/"None" defensive.
- CL-5 BUG (55): No `newline=""`.
- CL-6 GOOD (75-107): 4 bucketers (rsi / score / atrpct / month) with **operator-readable bucket names** like "rsi_oversold(<30)".
- CL-7 GOOD (84-89): _score_bucket 4-tier matching B66 SJ2-3 SAME thresholds (<0.5/0.7/0.85). ✅ Cross-module consistency.
- CL-8 BUG (84-89): Drift vs SJ2 (which uses 0.55/0.70/0.79/0.80 calibrated 39-pick distribution). **Theme T2 drift between calibration and signal_journal bucket thresholds.** Operator-confusing.
- CL-9 GOOD (92-100): _atr_bucket as ATR % of entry — operator-readable.
- CL-10 GOOD (112-131): BucketStat @dataclass with as_row method + 7-key dict.
- CL-11 GOOD (134-137): _is_win 1-line r>0 check.
- CL-12 GOOD (140-173): attribute_by with **min_n=5 default + sort by n desc.**
- CL-13 GOOD (152): bare Exception continue. Defensive (acceptable).
- CL-14 GOOD (178-184): FACTOR_KEYS dict with **5 lambdas** — extensible registry.
- CL-15 GOOD (187-201): per_factor_report + per_timeframe_report.
- CL-16 GOOD (204-218): overall_summary with **expectancy_R = mean_r alias** for documentation.
- CL-17 GOOD (223-235): _resolve_run with **3-fallback path resolution** (latest / abs / RESULTS_ROOT/arg).
- CL-18 GOOD (238-248): _fmt_table with auto-width column padding.
- CL-19 GOOD (251-316): main with 5 subcommands + **JSON output flag on each.**
- CL-20 GOOD (323-366): telegram_footer_lines with **graceful try/except → []** + best/worst factor surfacing.
- CL-21 GOOD (343-348): exit_status filter (descriptive, not actionable).
- CL-22 GOOD (369-385): open_proposals_summary with **3-action breakdown (kill/penalize/boost).**
- CL-23 BUG (372): Inline import. **24th cross-cutting.**

## src/weight_proposer.py — LINE BY LINE

- WP-1 GOOD (1-37): 37-line docstring with **decision rules + proposal example + 3-CLI commands.** Gold standard.
- WP-2 GOOD (49-56): 6 named thresholds with **BIAS/KILL constants + DELTA_CAP + DELTA_MULTIPLIER**.
- WP-3 GOOD (59-76): Proposal @dataclass with as_dict method + applied:bool=False default.
- WP-4 GOOD (81-88): _classify with **4-state action dispatch + None for too-neutral.**
- WP-5 GOOD (82): kill criteria = bias_r < KILL AND wr < 0.35 — **conjunctive guard against over-aggressive kills.** ✅
- WP-6 GOOD (91-96): _delta_pct with **kill always = -DELTA_CAP shortcut** + symmetric clamp.
- WP-7 GOOD (99-103): _confidence with **√n / 100 scaling cap at n=100.** Operator-readable.
- WP-8 GOOD (106-110): _rationale builder with sign char + thousand-percent formatting.
- WP-9 GOOD (113-161): propose with **per-bucket guard + 8-field Proposal construction.**
- WP-10 GOOD (129-130): exit_status skip per "not a knob we can twist" inline comment.
- WP-11 GOOD (157-160): **Sort: kills first, then by |delta| × confidence** — most-impactful actionable items first.
- WP-12 GOOD (166-175): write_proposals append-only.
- WP-13 BUG (172): No `newline=""` (jsonl, less critical).
- WP-14 GOOD (178-199): read_proposals with **only_unapplied filter + last-N limit slicing.**
- WP-15 BUG (192): json.JSONDecodeError-scoped except. **GOOD scoping example.**
- WP-16 GOOD (204-210): _fmt_proposal with **emoji-by-action + multi-line per-row.**
- WP-17 GOOD (213-275): main with 3 subcommands (propose/history/review) + dry-run flag.
- WP-18 GOOD (266-274): review subcommand calls out **READ-ONLY — Auto-apply ships in T-future (C6) with safety caps.** Operator-trust + roadmap visibility. ✅

## src/weight_applier.py — LINE BY LINE

- WA-1 GOOD (1-20): 20-line docstring with **schema example + idempotency contract + cap rule.**
- WA-2 GOOD (30-34): 3 named paths + WEEKLY_CAP_PCT = 5.0.
- WA-3 GOOD (38-41): _load with default-skeleton fallback.
- WA-4 GOOD (44-47): _save with **TZ-aware UTC date stamp** + version updated.
- WA-5 BUG (47): **NO ATOMIC WRITE on weights.json.** **44th unsafe writer.** Critical because weights.json is read by parallel_scorer (B66 PS2-X1 indirectly) — partial write corrupts scoring next run.
- WA-6 GOOD (51-52): _pid via 3-tuple → string identity.
- WA-7 GOOD (56-62): _iso_week via isocalendar with try/except fallback.
- WA-8 GOOD (65-68): _used_this_week sums abs(delta_pct) per (factor, week).
- WA-9 GOOD (71-79): _read_history mirror.
- WA-10 BUG (78): bare except. Theme T1.
- WA-11 GOOD (82-85): _append_history append-only (acceptable).
- WA-12 GOOD (89-99): _new_multiplier with **floor 0.0 / ceil 1.5 safety guards** + 4-action dispatch.
- WA-13 GOOD (91-92): kill → 0.0 hard zero. ✅
- WA-14 GOOD (102-186): apply_proposals with **dry_run + cap_pct kwargs + per-action gating + 3-result-class accumulators.**
- WA-15 GOOD (123): Action whitelist `("kill","boost","penalize")` + invalid → skipped_invalid bucket.
- WA-16 GOOD (130-136): Cap accounting: kill always = full cap usage, otherwise abs(delta). Per-(factor, week) tracking.
- WA-17 GOOD (143-154): mutation 9-field record.
- WA-18 GOOD (158): `history.append(mutation)` — **subsequent picks honour week-cap WITHIN SAME RUN.** ✅ Cap consistency.
- WA-19 GOOD (159-166): Learning journal try/except wrap.
- WA-20 BUG (160): Inline import. **25th cross-cutting.**
- WA-21 GOOD (170-177): Proposal-mark-applied via **whole-file rewrite with applied=True flag.**
- WA-22 BUG (173): **NON-ATOMIC** rewrite of proposals.jsonl. **45th unsafe writer.**
- WA-23 GOOD (190-205): history_summary 7-day default with by_action 3-bucket.
- WA-24 GOOD (208-228): _cli with --apply default-dry-run + ASCII-art summary box.

## src/lesson_gc.py — LINE BY LINE

- LG2-1 GOOD (1-18): 18-line docstring with **PROTECTIONS clause + 4-CLI examples.**
- LG2-2 GOOD (25-26): MAX_AGE_DAYS=90 + PROTECT_CONF=0.90 named.
- LG2-3 GOOD (29-36): _parse_ts best-effort.
- LG2-4 GOOD (39-64): find_stale dry-run preview function.
- LG2-5 GOOD (61-62): "fail safe — keep" comment for unparseable ts. **Conservative bias.** ✅
- LG2-6 GOOD (67-103): gc_stale with **dry_run flag + active=False mark + deactivated_at + reason.**
- LG2-7 GOOD (88-94): 3-condition guard before deactivation (active + below protect + parseable + past cutoff).
- LG2-8 GOOD (92): `r["active"] = False` — **never delete, just deactivate.** Per docstring archaeology. ✅
- LG2-9 BUG (99): Whole-file rewrite **NOT ATOMIC.** **46th unsafe writer.** Per B49 WB cross-cutting wisdom_base writes.
- LG2-10 GOOD (109-139): _cli with 3 args + **dry-run preview formatting.**

## src/learning_journal.py — LINE BY LINE

- LJ2-1 GOOD (1-12): 12-line docstring with 5-kind enum.
- LJ2-2 GOOD (19): Module-level JOURNAL.
- LJ2-3 GOOD (22-34): log with **TZ-aware UTC timestamp + arbitrary kwargs payload merge.**
- LJ2-4 GOOD (31-33): mkdir(parents=True) + append-only — acceptable for audit trail.
- LJ2-5 GOOD (37-58): read with optional days cutoff.
- LJ2-6 GOOD (47-49): bare Exception continue.
- LJ2-7 BUG (47, 53): 2 bare Exception. Theme T1.
- LJ2-8 GOOD (61-68): summary with by_kind aggregation.
- LJ2-9 GOOD: **MOST-CONSUMED MODULE in audit** — referenced by 8+ producer/consumer modules. **NO ABSTRACTIONS for kind enum** — string-typed; potential drift. **Theme T2 schema discipline gap.**

## src/auto_promote.py — LINE BY LINE

- AP-1 GOOD (1-28): **28-line docstring with ASCII flow diagram + PROMOTION CRITERIA + IDEMPOTENCY contract.** Gold standard.
- AP-2 GOOD (37-40): 3 named constants + KNOWN_SIGNALS set.
- AP-3 GOOD (43-44): _marker formatter.
- AP-4 GOOD (47-57): _already_promoted with **existing_lessons cache parameter** to avoid O(N×M) reloads.
- AP-5 GOOD (60-66): _confidence_from_p with **clamp [0.7, 0.95]** matching docstring.
- AP-6 GOOD (69-78): _format_text with **avoid/favor verb dispatch by effect.**
- AP-7 GOOD (81-131): promote_patterns with **SNAPSHOT existing once + per-pattern 6-criteria gate + dry_run support.**
- AP-8 GOOD (96): "Snapshot existing lessons once to avoid O(N*M) reloads" — **performance archaeology comment.** ✅
- AP-9 GOOD (108-113): 6 sequential continue-guards with operator-readable column-aligned format.
- AP-10 GOOD (117): tags include 4 entries: signal, bucket, "auto_promote", marker — **dual-tag idempotency.**
- AP-11 GOOD (124-129): On promotion → also append to existing list **so subsequent iterations see it** (avoid double-promote within same run). ✅
- AP-12 GOOD (137-161): _cli with dry-run + tag visualization.

## CONSOLIDATED CROSS-CUTTING (THIS BATCH)

### NEW Theme T29 (PURE-STDLIB STATISTICAL DISCIPLINE)
- **B66 SA-X1** Wilson CI + mean-R SE
- **B67 HE-X1** binomial PMF/CDF + 2-sided p-value

**Pattern:** Core statistical decision modules deliberately avoid scipy/numpy. Operator-clear, dependency-minimal. **Catalog as gold standard.**

### Theme T6 (ATOMIC WRITES) UPDATE
| Module | Status |
|---|---|
| B64 PE3 _save_picks | ✅ ATOMIC |
| B66 MDH2 _save | ✅ ATOMIC |
| **B67 NSI _save_signals** | ✅ ATOMIC |
| WM-5 _save | ❌ unsafe (42nd) |
| PS3-11 save (pattern_stats.json) | ❌ unsafe (43rd) — operator-critical |
| WA-5 _save (weights.json) | ❌ unsafe (44th) — operator-critical |
| WA-22 proposals.jsonl rewrite | ❌ unsafe (45th) |
| LG2-9 LESSONS rewrite | ❌ unsafe (46th) |

**Tally: 8 safe / 46 unsafe / 54 = ~85% UNSAFE.**

**HIGHEST-IMPACT remaining unsafe writers:**
1. PS3-11 pattern_stats.json — read by pattern_layer + auto_promote next morning.
2. WA-5 weights.json — read by parallel_scorer.
3. LG2-9 LESSONS rewrite — read by wisdom_hint on every pick.

### Theme T8 (DRY) UPDATE
- _to_float duplicates: **22 modules** (PS3-2 adds).
- Keyword-bag-of-words modules: **5 vocabularies** (NSE-X1 + NSI NEGATIVE_REACTION as 5th).
- Score-bucket threshold drift: **CL-8 vs SJ2-3** — calibration uses 0.5/0.7/0.85 vs signal_journal uses 0.55/0.70/0.79/0.80. Operator-confusing.

### Theme T26 (OBSERVE-MODE) UPDATE
- 23 audited OBSERVE-MODE modules (HE-X1 explicit + report footer).
- WP-X1 README exists/works in observe mode but **emphasizes "Auto-apply ships in T-future C6"** — operator-trust roadmap visibility.

### Theme T13 (SCHEMA-STABLE returns)
NSI-17 + WP-9 + WA-14 + LG2-6 + AP-7 + HE-7 — all **schema-stable across all return paths**. Strong cross-cutting discipline.

### Cross-cutting tally summary (this batch only)
| Metric | Before | This batch | After |
|---|---:|---:|---:|
| _safe_float duplicates | 21 | 1 | **22 modules** |
| Bare-except | mod | 12 | continues moderate |
| Inline imports | 21 | 4 | **25 cumulative** |
| Import-time side effects | 14 | 0 | **14** |
| Unsafe writers | 41 | 5 | **46 / 54 = ~85% UNSAFE** |
| Atomic writers | 7 | 1 (NSI) | **8** |
| TZ-aware modules | 15 | 4 (WM + NSI + WA + LJ2) | **19** |
| DATED archaeology | 22 | 4 (WM + NSI + PL + AP) | **26** |
| Frozen dataclasses | 3 | 0 | 3 |
| Regular dataclasses | 5 | 3 (CL BucketStat + WP Proposal + AP no, all this batch) | **8** |
| OBSERVE-MODE modules | 22 | 1 (HE) | **23** |
| __main__ smoke tests | 18 | 6 (NSI+CL+WP+WA+LG2+AP) | **24** |
| Pure-stdlib statistical | 1 (SA) | 1 (HE) | **2** |

## SUMMARY (Batch 67 — 13-FILE)

| File | Show-stop | Data/safety | Code smell | Good code | Findings |
|---|---:|---:|---:|---:|---:|
| watchlist_manager | 3 | 0 | 0 | 16 | 19 |
| news_sentiment | 1 | 0 | 0 | 8 | 9 |
| news_signals | 3 | 0 | 0 | 21 | 24 |
| pattern_layer | 1 | 0 | 0 | 13 | 14 |
| pattern_engine | 3 | 0 | 0 | 8 | 11 |
| pattern_stats | 3 | 0 | 0 | 9 | 12 |
| hypothesis_engine | 0 | 0 | 0 | 15 | 15 |
| calibration | 3 | 0 | 0 | 20 | 23 |
| weight_proposer | 1 | 0 | 0 | 17 | 18 |
| weight_applier | 4 | 0 | 0 | 20 | 24 |
| lesson_gc | 1 | 0 | 0 | 9 | 10 |
| learning_journal | 2 | 0 | 0 | 7 | 9 |
| auto_promote | 0 | 0 | 0 | 12 | 12 |
| **TOTAL** | **25** | **0** | **0** | **175** | **200** |

## TOP 15 CRITICAL FIXES from Batch 67

1. **PS3-11 (CRITICAL):** pattern_stats.json non-atomic write — partial write corrupts brain decisions. Apply NSI-12 atomic pattern. (5 min) **HIGHEST IMPACT in batch.**
2. **WA-5 (CRITICAL):** weights.json non-atomic write — read by every scoring run. Atomic pattern. (5 min)
3. **WM-5 (HIGH):** watchlist.json non-atomic — corrupts overnight news data. (5 min)
4. **WA-22 (HIGH):** proposals.jsonl whole-file rewrite non-atomic. (5 min)
5. **LG2-9 (HIGH):** LESSONS rewrite non-atomic — wisdom_base used on every pick. (5 min)
6. **CL-8 / Theme T2:** Score-bucket threshold drift between calibration (0.5/0.7/0.85) and signal_journal (0.55/0.70/0.79/0.80). Operator-confusing. Decide canonical bucketer + reference from one place. (15 min)
7. **LJ2-9 / Theme T2:** learning_journal `kind` is freeform string with no enum/validator — drift waiting to happen. Add KNOWN_KINDS set + validation. (10 min)
8. **NSI-X1 / NSE-X1 / Theme T8:** 5-vocab keyword consolidation now critical. Create `src/keyword_vocabularies.py`. (30 min)
9. **PS3-2 + 22 modules / Theme T8:** _to_float / _safe_float consolidation NOW 22 MODULES — execute. (1 hour)
10. **PE2-5 + WA-20 + CL-23 + PL-14 / Theme T inline-imports:** Hoist 4 inline imports from this batch. (3 min)
11. **PS3-4 worst-form bare-except:** `try: ... except: pass` matches MB-5 + B62 PS-7 worst-form. Replace with json.JSONDecodeError. (1 min)
12. **NSI-23 / NSE / NSI-17 / WP / WA / LG2 / AP archaeology:** Document the **Pillar 3+4 LEARNING LOOP** in `docs/PILLAR_3_4_LEARNING_LOOP.md` — 6-module chain (PE2→PS3→PL→AP→wisdom→hint+LG2). (45 min)
13. **CL → WP → WA → LJ2 chain:** Document the **Calibration→Proposal→Application** chain in `docs/CALIBRATION_CHAIN.md`. (30 min)
14. **HE-X1 + SA-X1 / Theme T29:** Document pure-stdlib statistical discipline in `docs/STATISTICS_PHILOSOPHY.md`. (15 min)
15. **NSE-X1 (smallest in audit at 46 lines):** Add unit tests for keyword scoring edge cases — currently no tests visible. (20 min)

## NEW THEMES UPDATED

- **Theme T1 (bare except):** ~12 in this batch.
- **Theme T2 (drift):** **NEW: CL-8 score-bucket threshold drift** vs SJ2 — 10th drift instance.
- **Theme T6 (atomic writes):** 8 safe / 46 unsafe = 85% UNSAFE. **NSI-12 third audited atomic.** 5 high-impact unsafe writers identified this batch.
- **Theme T8 (DRY):** 22-module _to_float + 5-vocab keyword duplication.
- **Theme T13 (schema-stable):** NSI/WP/WA/LG2/AP/HE 6 modules this batch — strong cross-cutting discipline.
- **Theme T14 (gold standard):** WM-X1 freshness-multiplier 5-tier docstring table + ±0.30 cap before sign flip + 999.0 ancient sentinel. NSE-X1 dampened net-per-article + 0.05/0.95 clamp + neutral-baseline. NSI-X1 40-line docstring with PROBLEM SOLVED + DATA FLOW + CATALYST table + 30-phrase EVC archaeology + atomic_save + last-write-wins-with-stronger-prefer + confidence-modulated delta + 180-day catastrophic TTL + em/en-dash normalization + M7 archaeology. PL-X1 [0.85, 1.15] clamp + per-detector confidence weighting + auto_enable_disable kill threshold + learning-journal hook. PE2-X1 don't-let-one-broken-detector-kill-all + 4-field record stamp. PS3-X1 (ticker, date) join + defaultdict accumulator + div-by-zero guards. HE-X1 17-line docstring with OBSERVE-MODE caps + pure-stdlib binomial + 4-edge-case PMF + right/left tail dispatch + low_sample tagged separately + No-weights-auto-changed footer. CL-X1 20-line docstring with CLI block + 9-field numeric coercion + operator-readable bucket names + 5-lambda registry + telegram_footer with try/except → []. WP-X1 37-line docstring with full proposal example + 4-action class with None for too-neutral + conjunctive kill guard + √n confidence + sort-kills-first + READ-ONLY-with-T-future-roadmap. WA-X1 20-line docstring with idempotency contract + per-(factor, week) cap with within-run-honoring + multiplier floor/ceil safety + dry_run + 3-result-class accumulators. LG2-X1 18-line docstring with PROTECTIONS + active=False (never delete) + fail-safe-keep on unparseable ts. LJ2-X1 minimal-API discipline (log/read/summary) + most-consumed audit-trail. AP-X1 28-line docstring with ASCII flow diagram + IDEMPOTENCY via marker tag + snapshot-once O(N*M) optimization + dual-tag idempotency + within-run promotion-tracking via list append.
- **NEW Theme T29 (PURE-STDLIB STATISTICAL DISCIPLINE):** SA-X1 + HE-X1 — 2 audited core decision modules deliberately avoid scipy/numpy.

## COVERAGE TRACKER

| Phase | Status | Cumulative |
|---|---|---:|
| Phase F | ~36/~38 done | ~36/~38 |
| Total true line-by-line | **+13 files (2 failed)** | **180 of ~382 (~47.1%)** |

**MILESTONE: ~47% AUDIT MARK. Phase F effectively complete (intraday_monitor + monitor_loop pending retry). Pillar 3+4 LEARNING LOOP fully audited. Calibration→Proposal→Application chain fully audited. 2nd Pure-stdlib statistical module (HE) joins SA-X1.**

## NEXT BATCH (15-FILE — RETRY 2 + 13 NEW)

Batch 68: Retry intraday_monitor + monitor_loop + 13 NEW files. Candidates from inventory:
- intraday_monitor (RETRY), monitor_loop (RETRY)  
- patterns/ files (B61 PA referenced 16 detectors), peer_strength, regime, risk_manager
- scorer (B62 audited — already done), sector_breakdown, sector_pnl, send_telegram
- universe, wisdom_consultant, monthly_xray, monthly_review, daily_telegram_block

End of Batch 67. **47.1% audit milestone. Pillar 3+4 + Calibration chain COMPLETE.**
