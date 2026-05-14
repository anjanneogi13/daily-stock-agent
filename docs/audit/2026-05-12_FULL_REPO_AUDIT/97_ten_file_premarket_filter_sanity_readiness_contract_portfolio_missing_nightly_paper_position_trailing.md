# Batch 97 — 10-FILE BATCH — TRUE LINE-BY-LINE — PREMARKET GATES + LIFECYCLE + NIGHTLY

**Date:** 2026-05-14  
**Commit ref:** 37565c4d757a9f819a3ddd2059f73a51bb98af49  
**Files (10):** premarket_filter (25) + premarket_sanity_gate (301) + premarket_readiness_gate (197) + premarket_decision_contract (269) + portfolio_risk_gate (279) + missing_data_gate (163) + nightly_conductor (237) + paper_trader (25) + position_monitor (131) + trailing_stop (66)  
**Phase:** H continuation — PREMARKET LANE 1 GATES + LIFECYCLE  
**Total LOC audited this batch:** ~1,693 lines  
**Reliability:** ✅ All 10 files actually fetched at the listed commit and audited line-by-line.

---

## TOP HEADLINE FINDINGS

1. **PF-X1: premarket_filter.py** (25) — **TINIEST module this batch.** Yfinance `fast_info` gap check with sensible 2-tier rejection (gap_up>3%, gap_down<-5%). **FAIL-OPEN philosophy** L23-24 ("gap check failed — allowing"). **0 BUG findings** but **fail-open contradicts gates philosophy**: the rest of the premarket lane fails *closed*; this one fails *open*. Theme conflict — see PF-3.
2. **PSG-X1: premarket_sanity_gate.py** (301) — **PRODUCTION SAFETY HEADER** (4-bullet `Safety:` declaration L8-12) + **4-action FSM** (SAFE / HALF_SIZE / SKIP_TODAY / WATCH_ONLY) + **fail-closed to WATCH_ONLY** when fresh price unverifiable. **Sequential gate ladder** (L71-155): missing entry/SL → WATCH_ONLY, broad market `skip_all` → SKIP_TODAY, current_price ≤ SL → SKIP_TODAY, neg-gap exceeds 0.6× SL buffer → SKIP_TODAY, gap≥3% → HALF_SIZE, market `half` → HALF_SIZE, gap≤-1.5% → HALF_SIZE, else SAFE. **`fetch_market_snapshot`** with **VIX≥25 → skip_all, VIX≥20 → half**. NEW Theme T181 (FAIL-CLOSED SAFETY HEADER + 4-state FSM). **0 critical bugs.** ✅
3. **PRG-X1: premarket_readiness_gate.py** (197) — **DATA-AVAILABILITY GATE** with **4-bullet safety header** + **min coverage 25% AND min 25 fetched** dual-gate (L18-19). **5 distinct no-pick statuses** (empty_universe / no_market_data / low_coverage / provider_degraded / ready). **`primary_no_pick_cause`** mapped to contract enum. **Provider summary aggregator** counts attempts/successes/errors/empty/rate_limited/unauthorized across all providers. **`required_fetched_count = max(1, min(min_fetched_count, required_by_coverage or min_fetched_count))`** L101 — careful min/max composition. **0 critical bugs.** ✅
4. **PDC-X1: premarket_decision_contract.py** (269) — **THE PRODUCTION CONTRACT** with **6-bullet behavior-neutral declaration** (L6-12: "does not generate picks, does not change scoring, does not enable paper/live trading, does not send alerts, does not mutate runtime state"). **CONTRACT_VERSION + STRATEGY_VERSION + SCORING_VERSION** triple. **OFFICIAL_PICK_REQUIRED_FIELDS 28 fields** + **OFFICIAL_NO_PICK_REQUIRED_FIELDS 21 fields** + **11 allowed primary no-pick causes** + **2 SAFETY_FLAGS** that must be `False`. **`_validate_safety_flags`** raises if `paper_trading_enabled` or `live_trading_enabled` is anything but `False` (L147 explicit `is not False` — strict identity check). NEW Theme T182 (TYPED CONTRACT WITH SAFETY-FLAG IDENTITY VALIDATION). **0 critical bugs.** ✅
5. **PRG2-X1: portfolio_risk_gate.py** (279) — **CROSS-CANDIDATE RISK COMPOSER** with **score-sorted descending iteration** (L218 `sorted(candidates, key=_candidate_score, reverse=True)` — best picks get slots first). **6 sequential per-candidate validations** (entry / SL / SL<entry / TP>entry / qty>0 / R:R≥min) + **3 portfolio limits** (max_positions, max_per_sector, max_per_tag). **`max_risk_pct = risk_per_trade_pct * 1.05`** (L182 — **5% tolerance over per-trade limit** for rounding slack). **Open-position counter from picks_log.csv** filtered to `status=pending AND not watch_only`. **0 critical bugs.** ✅
6. **MDG-X1: missing_data_gate.py** (163) — **8-FIELD CRITICAL FIELDS GATE** with **structured snapshot extractor** that pulls from 5 nested dicts (scores / plan / info_short / premarket_sanity / portfolio_risk). **11 distinct error types** (each emitted as plain-English string). **Cross-validates SL<entry AND TP>entry**. **Honors prior-gate stamps** L122-125 (`premarket_actionable=False` and `portfolio_risk_passed=False` block here). **0 critical bugs.** ✅
7. **NC2-X1: nightly_conductor.py** (237) — **T50 8-STEP NIGHTLY ORCHESTRATOR** with **chain-isolating `_step` wrapper** (L30-40: each step caught individually with traceback last-3-lines). **8 sequential steps:** pattern_scan → pattern_stats → auto_e_d → calibration_propose → weight_apply → auto_promote → lesson_gc → agent_memoir. **T51 deep_mode auto-detection** L186-193 (300 tickers on weekends/holidays vs 100 weekdays). **Smart universe: watchlist + recent picks**, sorted, capped at max_tickers. **CRITICAL:** L181 naive `datetime.now()`. L74-75/L88/L96/L104-105/L125/L140/L148/L162/L188/L210 — **11 inline imports** (intentional for circular-dep + lazy load, but undocumented).
8. **PT-X1: paper_trader.py** (25) — **TINIEST WRITER.** Single `log_paper_trade` with header-on-new-file pattern. **CRITICAL:** L9 append mode no atomicity. L15 naive datetime. L17-22 will KeyError if `pick.scores`/`pick.plan` missing — no defensive `.get()` chain. NEW Theme T183 (UNDEFENSIVE NESTED ACCESS — risk pattern).
9. **PM-X1: position_monitor.py** (131) — **POSITION-LIFECYCLE MONITOR** with **MAX_HOLD_DAYS** 3-key dict (day=1, swing=10, multi=30, default=14). **2-severity ladder** (over / near=within-1-day-of-max). **Single source of truth declaration** ("no positions.json to avoid sync bugs" L4). **HTML-formatted Telegram message construction** with emoji prefixes. **CRITICAL:** L37 bare `except: return None`. L87 bare `except: entry = 0.0` — silent. **0 critical, but 2 minor data-handling bugs.**
10. **TS-X1: trailing_stop.py** (66) — **PHASE 2B.2 RATCHET ENGINE** — **simplest possible trailing logic**. Activates when peak ≥ entry × (1 + activation_pct/100). Candidate SL = peak × (1 - trail_pct/100). **SL only moves UP** (L40-42 explicit). **`trail_status`** for human-readable Telegram output. **0 BUG findings.** ✅

---

## TOP-LEVEL CRITICAL FIXES (priority order)

1. **PT-X1: undefensive nested access (L17-22).** `pick["scores"]["composite"]` and `pick["plan"][...]` will KeyError on malformed pick — silently propagates upstream. **Fix: use `.get()` chain with defaults.** **15 min.**
2. **PT-X1: append mode no atomicity** — same risk class as PL-X1 from batch 95. **Fix: tmp+rename whole file.** **15 min.**
3. **PT-X1 + NC2-X1 naive datetime** (3 places). **Fix: TZ-aware UTC.** **15 min.**
4. **PF-X1: fail-open contradicts gate philosophy.** All other premarket gates fail closed; this one allows the trade if gap check fails. **Fix: optionally fail-closed via flag, defaulting to current behavior with deprecation note.** **15 min.**
5. **PM-X1: 2 bare except blocks** (L37, L87) silently swallow date-parse and float-coerce errors. **Fix: log via stderr or structured channel.** **15 min.**
6. **NC2-X1: 11 inline imports** undocumented. Circular-dep avoidance? Lazy-load? **Fix: add `# import here to avoid circular dep with X` comments OR move to top with `__all__` patterns.** **30 min.**
7. **PSG-X1: `fetch_market_snapshot` makes 7 yfinance HTTP calls sequentially** (L227-247). **Fix: parallelize via ThreadPoolExecutor (4-worker).** Saves 4-7s on every premarket run. **30 min.**
8. **PSG-X1: `fetch_latest_price` returns None on exception (L220-222)** — caller sees None, treats as fail-closed → WATCH_ONLY. Operator-visible only via `current_price=None` in decision. Should also log the exception type for diagnostics.

---

## NEW THEMES INTRODUCED THIS BATCH

- **T181 (FAIL-CLOSED SAFETY HEADER + 4-state FSM):** PSG-X1 — multi-bullet `Safety:` docstring header + state-machine constant naming. Used by 3 other gates this batch (PRG, PDC, PRG2).
- **T182 (TYPED CONTRACT WITH SAFETY-FLAG IDENTITY VALIDATION):** PDC-X1 — `is not False` strict identity check on safety flags (truthiness wouldn't catch `1`/`"true"`).
- **T183 (UNDEFENSIVE NESTED ACCESS — risk pattern):** PT-X1 — direct `pick["scores"]["composite"]` without `.get()` chain. Anti-pattern documented.

---

## src/premarket_filter.py (25 lines) — LINE BY LINE

- PF-1 GOOD (L1): Single-line docstring.
- PF-2 GOOD (L4-9): Function signature with **2-threshold params** (3% gap up, -5% gap down) + 3-tuple return.
- PF-3 BUG-MINOR (L23-24): `except Exception as e: return True, 0.0, "..."` — **fail-open** contradicts the rest of the premarket lane's fail-closed philosophy. Documented as such ("allowing") but inconsistent with PSG/PRG/PDC patterns.
- PF-4 GOOD (L13-14): **Multi-key fallback** for `previousClose` AND `previous_close` AND `lastPrice`/`last_price`/`regularMarketPrice` — defensive against yfinance schema drift.
- PF-5 GOOD (L15-16): `if not (prev_close and last): return True, 0.0, "no premarket data — allow"` — **explicit fail-open with reason**.
- PF-6 GOOD (L17-22): Clean 2-tier rejection + OK case with operator-readable reason strings.

---

## src/premarket_sanity_gate.py (301 lines) — LINE BY LINE

- PSG-1 GOOD (L1-13): **13-line docstring with 4-bullet `Safety:` header** declaring "no fake picks / no paper trading / no live trading / fail closed to watch-only when fresh price cannot be verified". NEW Theme T181.
- PSG-2 GOOD (L20-25): **4 ACTION constants + ACTIONABLE_ACTIONS set** — defines the FSM states.
- PSG-3 GOOD (L28-34): `_safe_float` with `(None, "")` defense.
- PSG-4 GOOD (L37-41): `_extract_entry_stop` with **plan-then-pick fallback** (`plan.get(...) or pick.get(...)`).
- PSG-5 GOOD (L44-156): `evaluate_premarket_sanity` master:
  - L54-69: base decision dict initialized to **WATCH_ONLY default with `actionable=False`** (fail-closed default).
  - L71-77: missing entry → WATCH_ONLY
  - L79-85: missing SL → WATCH_ONLY
  - L87-93: missing fresh price → WATCH_ONLY ("could not verify fresh price before official selection")
  - L95-97: gap_pct + sl_buffer_pct computation with `entry > 0` defense
  - L99-105: broad market `skip_all` → SKIP_TODAY
  - L107-113: current_price ≤ SL → SKIP_TODAY (already-stopped detection)
  - L115-121: **negative gap > 60% of SL buffer → SKIP_TODAY** ("leaves too little stop-loss buffer")
  - L123-130: gap ≥ 3% → HALF_SIZE (chasing risk)
  - L132-139: market `half` → HALF_SIZE
  - L141-148: gap ≤ -1.5% → HALF_SIZE (negative gap modest)
  - L150-155: SAFE default
- PSG-6 GOOD (L115): The 0.6× multiplier on SL buffer is a tunable threshold — could be elevated to a constant.
- PSG-7 GOOD (L159-166): `_apply_half_size` mutates plan in place (`max(1, int(qty * 0.5))` → never zero shares).
- PSG-8 GOOD (L169-205): `apply_premarket_sanity_decisions` tuple-returns (official, blocked) lists with **per-candidate sanity stamping** (4 fields written into candidate dict).
- PSG-9 GOOD (L208-222): `fetch_latest_price` 5-day history with `auto_adjust=False` + silent None on exception.
- PSG-10 BUG-MINOR (L220-221): Silent except — should log exception type for diagnostics.
- PSG-11 GOOD (L225-279): `fetch_market_snapshot` — fetches SPY/QQQ/SOXX/VIX + per-ticker pct_change + **escalating warning tiers**:
  - SPY ≤ -1.5% → skip_all
  - SPY ≤ -0.7% → half
  - VIX ≥ 25 → skip_all
  - VIX ≥ 20 (and not already skip_all) → half
  - SOXX ≤ -2% → warning only (no global_action change)
- PSG-12 BUG-MINOR (L227-247): **7 sequential yfinance HTTP calls** — could parallelize for ~4-7s speedup.
- PSG-13 GOOD (L262): `elif vix is not None and vix >= 20 and global_action == "normal":` — **doesn't override skip_all if SPY already triggered it**. Correct precedence handling.
- PSG-14 GOOD (L282-300): `run_premarket_sanity_gate` master orchestrator — fetches market + per-ticker prices + applies gate + returns 3-tuple summary.

---

## src/premarket_readiness_gate.py (197 lines) — LINE BY LINE

- PRG-1 GOOD (L1-11): **11-line docstring with 4-bullet `Safety:` header** + "fail closed into official no-pick" declaration.
- PRG-2 GOOD (L18-19): 2 module constants — `DEFAULT_MIN_FETCH_COVERAGE = 0.25` + `DEFAULT_MIN_FETCHED_COUNT = 25`.
- PRG-3 GOOD (L22-33): `_safe_int`/`_safe_float` with type-strict defense.
- PRG-4 GOOD (L36-75): `_provider_attempt_summary` aggregates **6 metrics across all providers** (attempts/successes/errors/empty/rate_limited/unauthorized) + **4 OHLCV-stage metrics**. Defensive `isinstance(..., dict)` checks throughout.
- PRG-5 GOOD (L78-191): `build_premarket_readiness_decision` master with **4 distinct no-pick branches + 1 ready branch**:
  - L94-97: input coercion + range clamping (`max(0.0, min(1.0, ...))`)
  - L99-101: provider summary + required-count composition with **`required_fetched_count = max(1, min(min_fetched_count, required_by_coverage or min_fetched_count))`** — careful min/max
  - L107-114: 4-warning detection (rate_limited / unauthorized / ohlcv_empty / ohlcv_errors)
  - L116-128: **empty_universe → NO_PICK_DATA_READINESS_FAILED**
  - L130-142: **fetched=0 → NO_PICK_DATA_PROVIDER_DEGRADED**
  - L144-159: **low coverage → NO_PICK_DATA_READINESS_FAILED**
  - L161-178: **provider degraded** (`ohlcv_attempts >= 10 AND successes == 0 AND (errors+empty) >= attempts`) → NO_PICK_DATA_PROVIDER_DEGRADED
  - L180-191: ready branch
- PRG-6 GOOD (L101): `min(min_fetched_count, required_by_coverage or min_fetched_count)` — handles 0-coverage edge case (when universe count tiny).
- PRG-7 GOOD (L194-196): `assert_premarket_readiness_or_no_pick(**kwargs)` — convenience wrapper retaining identical signature.
- PRG-8 GOOD (L120/L134/L148/L170): Each no-pick decision includes `primary_no_pick_cause` matching the **PDC-X1 enum** — contract-aligned.

---

## src/premarket_decision_contract.py (269 lines) — LINE BY LINE

- PDC-1 GOOD (L1-16): **16-line docstring with 6-bullet behavior-neutral declaration** ("does not generate picks, does not change scoring, does not enable paper trading, does not enable live trading, does not send alerts, does not mutate runtime state").
- PDC-2 GOOD (L24-28): 4 version constants — `STRATEGY_LANE`, `CONTRACT_VERSION`, `STRATEGY_VERSION`, `SCORING_VERSION` — **explicit triple versioning** for forward migration.
- PDC-3 GOOD (L30-36): 2 decision constants + `VALID_DECISIONS` set.
- PDC-4 GOOD (L38-69): `OFFICIAL_PICK_REQUIRED_FIELDS` **28-field tuple**.
- PDC-5 GOOD (L71-95): `OFFICIAL_NO_PICK_REQUIRED_FIELDS` **21-field tuple**.
- PDC-6 GOOD (L97-105): `OFFICIAL_PICK_NUMERIC_FIELDS` **7-field tuple** for type-validation.
- PDC-7 GOOD (L107-119): `OFFICIAL_NO_PICK_ALLOWED_PRIMARY_CAUSES` **11-cause set** — closed enum.
- PDC-8 GOOD (L121-124): `SAFETY_FLAGS` 2-tuple.
- PDC-9 GOOD (L127-137): `_is_missing` — **None and blank-string are missing; empty dict/list ALLOWED** (correct semantics — empty diagnostics may be intentional).
- PDC-10 GOOD (L140-141): `_missing_required_fields` list comprehension — clean.
- PDC-11 GOOD (L144-149): `_validate_safety_flags` — **`is not False` strict identity check** (`if payload.get(field) is not False`). NEW Theme T182.
- PDC-12 GOOD (L152-165): `_validate_numeric_fields` with **per-field non-negative vs positive distinction** (score/risk_reward/quantity/risk_dollars allow zero; entry/stop_loss/take_profit must be >0).
- PDC-13 GOOD (L168-200): `validate_official_pick` — **6 distinct validation passes** (missing fields / decision value / strategy_lane / safety flags / numeric fields / score_components type / risk_flags type / invalidation_conditions type).
- PDC-14 GOOD (L189): `score_components must be a mapping` — type check.
- PDC-15 GOOD (L203-241): `validate_official_no_pick` — **6 validation passes** including primary_no_pick_cause enum check + watch_only_available boolean check (L236).
- PDC-16 GOOD (L236): `payload.get("watch_only_available") not in {True, False}` — strict bool check (rejects truthy ints/strings).
- PDC-17 GOOD (L244-251): `validate_official_decision` dispatch with default error.
- PDC-18 GOOD (L254-268): `contract_summary` JSON-safe introspection helper for tests/CI.
- **PDC-19: 0 BUG findings. Theme T57 (PERFECT MODULE) — 44th cumulative perfect.** ✅

---

## src/portfolio_risk_gate.py (279 lines) — LINE BY LINE

- PRG2-1 GOOD (L1-13): **13-line docstring with 4-bullet `Safety:` header**.
- PRG2-2 GOOD (L22-26): 4 module constants including `DEFAULT_MAX_PER_SECTOR=2`, `DEFAULT_MAX_PER_TAG=2`, `DEFAULT_MIN_RISK_REWARD=1.0`.
- PRG2-3 GOOD (L29-42): `_safe_float`/`_safe_int` defensive coercion.
- PRG2-4 GOOD (L45-53): `_candidate_sector` + `_candidate_tag` extractors with `isinstance` defense + tag-split-on-`" / "` for primary tag.
- PRG2-5 GOOD (L56-63): `_candidate_score` + `_trade_plan` extractors.
- PRG2-6 GOOD (L66-88): `_risk_profile` master computes risk_dollars + risk_pct with `entry > 0 AND stop_loss is not None AND quantity > 0` triple-defense.
- PRG2-7 GOOD (L78): `risk_pct = (risk_dollars / account_size * 100.0) if account_size > 0 else None`.
- PRG2-8 GOOD (L91-106): `load_open_positions_from_picks_log` — filter to `status=pending AND not watch_only`. **Multi-string truthy parse** (`{"1", "true", "yes"}`).
- PRG2-9 BUG-MINOR (L104): Silent `except: return []` — should log csv parse errors.
- PRG2-10 GOOD (L109-123): Per-row sector + tag counters with primary-tag normalization.
- PRG2-11 GOOD (L126-140): `build_portfolio_risk_config` with **defaults + lower bounds via `max(1, ...)`** for max_positions/sector/tag.
- PRG2-12 GOOD (L143-192): `evaluate_candidate_portfolio_risk` master with **9 sequential validations**:
  - L164: missing/invalid entry
  - L167: missing/invalid SL
  - L170: SL not below entry
  - L173: TP not above entry
  - L176: zero quantity
  - L179: R:R below min
  - L182-184: **per-trade risk > limit×1.05** (5% slack)
  - L186-187: sector cap reached
  - L189-190: tag cap reached
- PRG2-13 GOOD (L182): The 1.05× slack tolerance for per-trade risk — defensive against rounding drift.
- PRG2-14 GOOD (L195-278): `apply_portfolio_risk_gate` master:
  - L210: `available_slots = max(0, max_positions - open_position_count)` — clamped non-negative
  - L218: **score-sorted descending** (best picks consume slots first)
  - L221-234: max_positions block path
  - L236-252: per-candidate validation block path
  - L254-258: **mutate sector/tag counts after each allowed pick** (so subsequent picks see updated caps)
  - L260-264: stamp `portfolio_risk` dict on candidate
- PRG2-15 GOOD (L256): The mutation of sector_counts/tag_counts during iteration is the correct pattern — prevents same-sector spree.
- PRG2-16 GOOD (L267-276): Summary dict includes 8 fields for diagnostics.
- **PRG2-17: 1 minor (silent except L104), otherwise clean. Theme T57 (PERFECT MODULE near-miss).**

---

## src/missing_data_gate.py (163 lines) — LINE BY LINE

- MDG-1 GOOD (L1-15): **15-line docstring with 4-bullet `Safety:` header** + "reporting/validation only" declaration.
- MDG-2 GOOD (L22-31): `CRITICAL_OFFICIAL_PICK_FIELDS` 8-field tuple.
- MDG-3 GOOD (L34-53): 3 type-defensive helpers (`_is_blank`, `_safe_float`, `_safe_int`).
- MDG-4 GOOD (L56-78): `official_pick_required_field_snapshot` — **5-source extractor** (scores / plan / info_short / premarket_sanity / portfolio_risk) with `isinstance` defense at every nested access.
- MDG-5 GOOD (L75-77): `premarket_actionable` checks `if "premarket_actionable" in candidate` — explicit presence check (not truthy) to distinguish False from missing.
- MDG-6 GOOD (L81-127): `validate_official_pick_required_data` master with **11 distinct validations**:
  - L86-87: ticker missing
  - L89-93: score missing/non-numeric/negative
  - L95-97: trade_type not in {day, swing}
  - L105-114: 5 positivity checks (entry/SL/TP/qty/R:R)
  - L116-119: **SL<entry AND TP>entry cross-validation**
  - L122-125: **prior-gate honoring** (premarket_actionable=False, portfolio_risk_passed=False explicitly block)
- MDG-7 GOOD (L130-162): `apply_missing_data_gate` — **per-candidate split into allowed/blocked** with **error array on blocked + snapshot on both**. Stamps `missing_data_gate` dict on allowed candidates.
- **MDG-8: 0 BUG findings. Theme T57 (PERFECT MODULE) — 45th cumulative perfect.** ✅

---

## src/nightly_conductor.py (237 lines) — LINE BY LINE

- NC2-1 GOOD (L1-16): **16-line docstring with explicit ORDER MATTERS section** + 8-step list with arrows showing data flow.
- NC2-2 GOOD (L26-27): 2 path constants.
- NC2-3 GOOD (L30-40): `_step` chain-isolating wrapper with **traceback last-3-lines** (compact). Captures `{"ok": True, "result": ...}` or `{"ok": False, "error": ..., "traceback": [...]}`.
- NC2-4 GOOD (L43-66): `_load_universe_for_scan` with **2 sources** (watchlist + recent picks), uppercase normalization, sorted+capped at max_tickers.
- NC2-5 GOOD (L55/L64): 2 silent `except` continues — operator can't see why a source failed.
- NC2-6 GOOD (L72-84): `_step_pattern_scan` — fetches regime once, scans all tickers, persists matches.
- NC2-7 BUG-INFO (L74-75): Inline imports `from src.pattern_engine import scan_ticker, persist` + `from src.regime import market_regime`.
- NC2-8 GOOD (L87-92): `_step_pattern_stats` — 3-line orchestration (build → save → count).
- NC2-9 GOOD (L95-99): `_step_pattern_auto_enable_disable` — clean delegate to `pattern_layer.auto_enable_disable`.
- NC2-10 GOOD (L102-121): `_step_calibration_propose`:
  - L106-107: skip if no picks_log
  - L108-109: filter to closed picks (have r_multiple)
  - L110-111: skip if <10 closed (sample-size guardrail)
  - L113-116: defensive try/except on report
  - L117: **run_id includes timestamp** (`nightly_YYYYmmdd_HHMMSS`)
  - L118-119: write proposals
- NC2-11 BUG (L117): naive `datetime.now().strftime(...)` for run_id.
- NC2-12 GOOD (L124-136): `_step_weight_apply` with **`_count` helper** that handles int OR list OR None. Prevents TypeError on `len(int)`.
- NC2-13 GOOD (L139-144): `_step_auto_promote` handles list-OR-dict result shapes.
- NC2-14 GOOD (L147-154): `_step_lesson_gc` similar polymorphic-result handling.
- NC2-15 GOOD (L160-169): `_step_agent_memoir` (added 2026-05-04 archaeology) writes memoir + extracts 4 summary fields.
- NC2-16 GOOD (L172-222): `run_nightly` master:
  - L181: naive `datetime.now().isoformat()` — TZ-unsafe
  - L186-193: **T51 deep_mode auto-detection** with try/except → False fallback
  - L196: `_scan_count = 300 if deep_mode else 100` — operator-readable scaling
  - L197-206: 8 step calls
  - L209-218: emit `nightly_brain_run` event with structured summary (ok/fail counts + per-step result)
  - L220-221: ok_count + fail_count for caller
- NC2-17 BUG (L181): Naive datetime.
- NC2-18 BUG (L217-218): Silent `except Exception: pass` — learning_journal failure invisible.
- NC2-19 GOOD (L225-236): `format_summary_text` — operator-readable plain-text with emoji prefixes.
- NC2-20 BUG-INFO: **11 inline imports** total (L74, L75, L88, L96, L104, L105, L125, L140, L148, L162, L188, L210). Likely circular-dep avoidance, undocumented.

---

## src/paper_trader.py (25 lines) — LINE BY LINE

- PT-1 GOOD (L1): Tiny docstring.
- PT-2 BUG-MINOR (L7): `os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)` — module side effect via call-time mkdir. Fine for write helper.
- PT-3 BUG-CRITICAL (L9): `with open(csv_path, "a", ...)` — append mode NOT atomic. Crash mid-row corrupts CSV. Same risk class as `pick_logger.py`.
- PT-4 BUG (L15): `datetime.now().isoformat(...)` — naive datetime.
- PT-5 BUG-CRITICAL (L17-22): **Direct nested access** `pick["scores"]["composite"]` and `pick["plan"].get(...)`. **L17 will KeyError** if `pick.scores` missing. **L18-22 use `.get()` on plan but assume plan exists**. Theme T183 — undefensive nested access risk.
- PT-6 GOOD (L11-13): Header-on-new-file pattern is correct.
- PT-7 GOOD (L23): `"paper"` mode literal — no live-trading possible from this module ✅.

---

## src/position_monitor.py (131 lines) — LINE BY LINE

- PM-1 GOOD (L1-17): **17-line docstring with explicit MAX_HOLD-per-trade-type table** + Single-source-of-truth declaration ("no positions.json to avoid sync bugs").
- PM-2 GOOD (L24-29): MAX_HOLD_DAYS dict + DEFAULT_MAX_HOLD=14.
- PM-3 GOOD (L32-38): `_parse_date` with try/except → None.
- PM-4 BUG-MINOR (L37): Bare `except: return None` — silent date-parse failure.
- PM-5 GOOD (L41-42): `_max_hold_for` case-insensitive lookup with default fallback.
- PM-6 GOOD (L45-112): `scan_open_positions` master:
  - L60-61: today defaults to `date.today()` — naive, but `date.today()` is OK (no time component to TZ-localize)
  - L62-63: empty-defense
  - L65-66: load CSV
  - L69-83: per-row filter (status=pending) + date parse + days_open + severity ladder (over / near / continue)
  - L80: `near = days_open == max_hold - 1` — exactly 1-day-before-max
  - L85-88: defensive entry float coerce
  - L91-97: HTML-formatted Telegram message with emoji prefix per severity
  - L99-108: alert dict with 8 fields
  - L111: **sort by overdue-amount descending** — most-urgent first
- PM-7 BUG-MINOR (L87): Bare `except: entry = 0.0` — silent.
- PM-8 GOOD (L115-130): `format_telegram_summary` — splits over/near, emoji-formatted bullet lists.

---

## src/trailing_stop.py (66 lines) — LINE BY LINE

- TS-1 GOOD (L1-5): Phase 2B.2 docstring with **state-machine contract** (activates at +activation_pct, SL = peak × (1 - trail_pct/100), SL only moves up).
- TS-2 GOOD (L9-13): `compute_trailing_sl` signature with **2 tunable thresholds** (activation_pct=3.0, trail_pct=2.0).
- TS-3 GOOD (L14-26): **26-line docstring with explicit Args/Returns including did_raise tuple semantics**.
- TS-4 GOOD (L28-29): Defensive `entry <= 0 or peak_price <= 0` early-return.
- TS-5 GOOD (L31-34): Activation threshold check — peak must exceed entry × (1 + activation_pct/100).
- TS-6 GOOD (L37): Candidate SL = peak × (1 - trail_pct/100) rounded to 2.
- TS-7 GOOD (L39-42): **SL ratchet — only moves UP** (`if candidate_sl > current_sl: return candidate_sl, True`).
- TS-8 GOOD (L45-65): `trail_status` 4-field result dict for telemetry:
  - L57: peak_gain_pct (entry-relative high)
  - L58: locked_gain_pct (current_sl-vs-entry)
  - L59: sl_raised_pct (current_sl vs original_sl)
  - L61: `active = current_sl > original_sl` (boolean derived state)
- TS-9 GOOD (L57-59): All 3 ratios protect against zero-division via `if entry > 0` / `if original_sl > 0` ternaries.
- **TS-10: 0 BUG findings. Theme T57 (PERFECT MODULE) — 46th cumulative perfect.** ✅

---

## CONSOLIDATED CROSS-CUTTING (THIS BATCH)

### NEW Themes T181-T183 (3 new)

- **T181 (FAIL-CLOSED SAFETY HEADER + 4-state FSM):** PSG-X1 — multi-bullet docstring header + state-machine constants. Used by 3 other gates this batch.
- **T182 (TYPED CONTRACT WITH SAFETY-FLAG IDENTITY VALIDATION):** PDC-X1 — `is not False` strict identity check.
- **T183 (UNDEFENSIVE NESTED ACCESS — risk pattern):** PT-X1 — anti-pattern documented.

### Theme T57 (PERFECT MODULES) NOW 46 cumulative
- +3 this batch: PDC + MDG + TS. (PSG/PRG/PRG2 have minor issues, not perfect.)

### Theme T6 (atomic writes) UPDATE
- **0 atomic this batch.**
- **+1 unsafe** (PT-X1 paper_trader append).
- Running tally: ~18 safe / ~134 unsafe.

### Cross-cutting tally summary (this batch only)

| Metric | Count this batch |
|---|---:|
| Files actually fetched & line-audited | 10/10 ✅ |
| Total lines audited | 1,693 |
| Bare `except:` | 3 (PM-X1 ×2, NC2-X1 ×2, PRG2-X1 ×1, PSG-X1 ×1) |
| Silent `except Exception` (no log) | 4 (NC2 ×2, PRG2 ×1, PT none) |
| Naive datetime usage | 3 (NC2 ×2, PT ×1) |
| TZ-aware UTC | 0 |
| Atomic writers | 0 |
| Unsafe writers | 1 (PT-X1) |
| Inline imports | 11 (NC2-X1) |
| Module-level side effects | 1 (PT-X1 makedirs at call-time, not import-time) |
| Dataclasses | 0 |
| `__main__` smoke tests | 0 |
| 0-BUG perfect modules | 3 (PDC, MDG, TS) |
| Operator-readable archaeology | 4 (T50, T51, T6 prevention, "no positions.json to avoid sync bugs") |
| Fail-closed gates | 5 (PSG, PRG, PDC, PRG2, MDG) |
| Fail-open gates | 1 (PF — anomaly) |

---

## SUMMARY (Batch 97 — 10-FILE)

| File | Critical | Bug | Code smell | Good | Total findings |
|---|---:|---:|---:|---:|---:|
| premarket_filter | 0 | 1 | 0 | 5 | 6 |
| premarket_sanity_gate | 0 | 2 | 0 | 12 | 14 |
| premarket_readiness_gate | 0 | 0 | 0 | 8 | 8 |
| premarket_decision_contract | 0 | 0 | 0 | 18 | 18 |
| portfolio_risk_gate | 0 | 1 | 0 | 16 | 17 |
| missing_data_gate | 0 | 0 | 0 | 7 | 7 |
| nightly_conductor | 0 | 4 | 1 | 14 | 19 |
| paper_trader | 2 | 2 | 0 | 2 | 6 |
| position_monitor | 0 | 2 | 0 | 6 | 8 |
| trailing_stop | 0 | 0 | 0 | 9 | 9 |
| **TOTAL** | **2** | **12** | **1** | **97** | **112** |

---

## TOP 10 PRIORITY FIXES FROM BATCH 97

1. **PT-X1 undefensive nested access (L17-22)** — `.get()` chain. **15 min.**
2. **PT-X1 atomic CSV append** — tmp+rename. **15 min.**
3. **PT-X1 + NC2-X1 naive datetime (3 places)** — TZ-aware UTC. **15 min.**
4. **PF-X1 fail-open inconsistency** — add fail-closed flag. **15 min.**
5. **PM-X1 2 bare except** — log via stderr. **15 min.**
6. **NC2-X1 11 inline imports** — document with circular-dep comments. **30 min.**
7. **PSG-X1 7 sequential yfinance calls in fetch_market_snapshot** — parallelize. **30 min.**
8. **PRG2-X1 silent except L104** — log csv parse errors. **10 min.**
9. **PSG-X1 fetch_latest_price silent except** — log exception type. **10 min.**
10. **NC2-X1 silent except for learning_journal write** — log via stderr. **10 min.**

---

## COVERAGE TRACKER (HONEST)

| Phase | Files in `src/` | Verifiably audited (this convo, line-by-line) |
|---|---:|---:|
| Pre-batch-97 | 92 | 56 |
| **Post-batch-97** | **92** | **66** |
| Remaining `src/` top-level | — | **26 files (~28%)** |

Plus subdirectories: `src/backtester/` (5), `src/market_data_providers/` (2), `src/patterns/` (10) — all unverified.

End of Batch 97.
