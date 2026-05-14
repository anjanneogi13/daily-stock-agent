# Batch 98 — 10-FILE BATCH — TRUE LINE-BY-LINE — OFFICIAL ARTIFACTS + PROVIDER TAXONOMY + MONSTER + ORNG + UNIVERSE/WATCHLIST + MARKET GUARD

**Date:** 2026-05-14  
**Commit ref:** 37565c4d757a9f819a3ddd2059f73a51bb98af49  
**Files (10):** official_pick_artifact (327) + official_artifact_loader (147) + provider_failure_taxonomy (252) + monster_data (57) + monster_hunt (141) + opening_range_scanner (278) + picks_csv (47) + universe (103) + watchlist_manager (191) + market_guard (116)  
**Phase:** H continuation — OFFICIAL ARTIFACT WRITER + LOADER + PROVIDER TAXONOMY + MONSTER LANE + ORNG + UNIVERSE/WATCHLIST  
**Total LOC audited this batch:** ~1,659 lines  
**Reliability:** ✅ All 10 files actually fetched at the listed commit and audited line-by-line.

---

## TOP HEADLINE FINDINGS

1. **OPA-X1: official_pick_artifact.py** (327) — **THE LANE 1 ARTIFACT WRITER** with full **TZ-AWARE ET conversion** (L34 `ET = ZoneInfo("America/New_York")` + L182/L262 `datetime.now(timezone.utc).astimezone(ET)`). **`_safe_ticker`** alphanumeric-plus-`_-` filename sanitization (L38-39 — prevents path-traversal attacks). **3 ID/path generators** with 12-char short SHA. **`_json_safe`** truncating recursive serializer (lists capped at 25, dicts at 75, drops `df`/`dataframe`/`history` keys). **`build_official_pick_artifact`** assembles 28-field contract-aligned payload. **`write_official_pick_artifacts`** master with **per-pick validation gate** (skip + record errors) + **summary artifact** with `validation_errors` dict. **0 critical bugs.** Theme T57 candidate but slight-miss due to L77/L81 magic numbers (25, 75).
2. **OAL-X1: official_artifact_loader.py** (147) — **THE READER for downstream Telegram/GitHub formatters**. **Reporting-only declaration** (L6-9 explicit). **`enrich_pick_row_with_artifact`** mutates output dict with **15 `official_*` prefixed fields** + 9 `_merge_non_empty` overrides for canonical CSV-compat keys. **`validate_official_artifacts_for_rows`** — **FAIL-CLOSED GUARD** for user-facing output (L110-115 docstring: "Telegram/GitHub issue output must not proceed unless each row is backed by a validated official artifact"). NEW Theme T184 (READ-SIDE FAIL-CLOSED GUARD with cross-validation against PDC contract). Detects extra-tickers (artifacts without CSV rows) too.
3. **PFT-X1: provider_failure_taxonomy.py** (252) — **CANONICAL FAILURE CLASSIFIER** with **11-type closed enum** (`CANONICAL_FAILURE_TYPES`) + **bidirectional legacy bucket maps** + **`@dataclass(frozen=True) ProviderFailureClassification`** (L55-61). **`classify_provider_failure`** is a **9-stage cascading lower-case substring match** with explicit ordering (rate_limited → timeout → market_closed → stale_data → symbol_not_found → missing_quote → missing_intraday_bars → missing_history → empty → provider_exception → unknown). **`classify_legacy_provider_error`** preserves backward-compat by detecting unauthorized BEFORE delegating to canonical. **0 critical bugs. Theme T57 (PERFECT MODULE).** ✅
4. **MD-X1: monster_data.py** (57) — **TINIEST module this batch.** Yfinance `.info` short-float fetcher with **24h disk cache + structured market_data_health event recording** (L51 success / L53 error with classify_provider_error). **CRITICAL:** L24 naive `datetime.fromtimestamp` for cache mtime check + L25 naive `datetime.now()`. L13 mkdir at import time (T118).
5. **MH-X1: monster_hunt.py** (141) — **PILLAR 3 MONSTER SCORING** with **7-component additive scorer** (earnings ≤7d=+0.20, short>15%=+0.20, float<50M=+0.15, RVOL>1.5=+0.15, bullish_news=+0.15, composite≥0.85=+0.10, catalyst_combo=+0.05). **All inputs Optional, missing=0 (no penalty)** L38. **`apply_monster_treatment`** mutates pick with **5% wider SL + 25% TP + lottery-sized 1.5% position** for is_monster (L116). **Stashes 3 `*_pre_monster` audit fields** L131-133 for traceability. **0 critical bugs.** ✅
6. **ORS-X1: opening_range_scanner.py** (278) — **MONITORING-ONLY ORB DETECTOR** with **TZ-aware ET handling** (L27 ET constant, L46-47 `replace(tzinfo=ET)` for naive timestamps). **15-min default range** (`DEFAULT_RANGE_MINUTES=15`). **5-stage breakout validation** (range ready → post-range bar → price > OR high → breakout_pct ≥ min → volume ratio + extension + gap checks). **`watch_only=True` always** (L189 docstring: "monitoring-only until there is enough evidence to promote it into actionable planning"). **`risk_reward=1.5` fixed** (L254/L275). **0 critical bugs.** ✅ NEW Theme T185 (MONITORING-ONLY MODE WITH PROMOTE-LATER CONTRACT).
7. **PCV-X1: picks_csv.py** (47) — **TINIEST mutable-CSV updater.** `read_open_picks(today)` filters to today+pending. **`update_pick_row` REWRITES WHOLE CSV** (L42-45) — better than append, but **NOT ATOMIC** (no tmp+rename). Crash mid-write corrupts. **CRITICAL:** Same risk class as PT-X1 from batch 97.
8. **UN-X1: universe.py** (103) — **UNIVERSE SELECTOR** with **curl_cffi chrome-impersonation session** for Wiki scraping (L7-11 with try/except → None fallback to plain requests). **3 sources** (sp500/nasdaq100/custom) + **always-include semis** + **PR #68 always-include watchlist (bullish_only)**. **`dict.fromkeys`** dedup pattern (L85, L92). **`.` → `-` ticker normalization** for S&P (L28 — handles BRK.B → BRK-B). **CRITICAL:** L29-31/L43-45/L63-65 silent excepts with print only (no structured log). NEW Theme T186 (CURL_CFFI BROWSER-IMPERSONATION FALLBACK pattern).
9. **WM-X1: watchlist_manager.py** (191) — **PR #68 FRESHNESS-WEIGHTED WATCHLIST**. **72h TTL pruning on load**. **`_freshness_multiplier`** 5-tier ladder (<4h=2.0×, <8h=1.5×, <24h=1.0×, <48h=0.6×, ≥48h=0.3×). **`add_from_news`** dedup-by-ticker with **score-monotonic update** (only overwrite if higher). **`watchlist_score_boost`** signed boost capped at ±0.30 + bearish negation. **`_hours_old` returns 999 on parse failure** ("treat as ancient"). NEW Theme T187 (FRESHNESS-WEIGHTED SIGNAL DECAY ladder). **TZ-aware UTC throughout** ✅. **0 critical bugs.** ✅
10. **MG-X1: market_guard.py** (116) — **MARKET-WIDE GATES + TRADE TYPE CLASSIFIER**. `vix_level` / `spy_trend` / `sector_strength` (12 sector ETFs default) — all yfinance with except→safe-default. **`classify_trade_type`** with **PR #67 archaeology** ("Old logic required momentum>0.75 AND volume>0.7 which was IMPOSSIBLY HIGH... 28 picks tagged 'swing', causing -6% losses"). **NEW LOGIC: 4-condition AND for day** (momentum≥0.65 + volume≥0.55 + atr_ratio≤0.035 + |gap|<0.04). **`classify_with_day_score`** dual-gate (day_score≥0.65 AND |gap|<0.04). **CRITICAL:** L18/L26 fail-OPEN to "above_50dma=True" defaults — pretends bull when data missing. Same anti-pattern as PF-X1 in batch 97.

---

## TOP-LEVEL CRITICAL FIXES (priority order)

1. **PCV-X1 + WM-X1: non-atomic CSV/JSON writes.** PCV-X1 L42-45 rewrites picks_log.csv without tmp+rename; WM-X1 L29 same for watchlist.json. **Fix: tmp+rename pattern.** **30 min total.**
2. **MG-X1: fail-open defaults in spy_trend (L18, L26)** — returns `above_50dma=True` on data failure. Strategy treats this as bullish go-ahead when actually data is missing. **Fix: return None or explicit `data_unavailable=True` flag, treat as fail-closed in callers.** **30 min.**
3. **MD-X1: 2 naive datetime calls** (L24, L25) for cache freshness. **Fix: TZ-aware UTC.** **15 min.**
4. **OPA-X1: magic numbers in `_json_safe`** (25 list cap, 75 dict cap). **Fix: extract to module constants for tunability.** **10 min.**
5. **UN-X1: 3 silent except with print only** (L29, L43, L63). **Fix: log via structured channel.** **15 min.**
6. **ORS-X1: `_session_date` raises ValueError on empty bars (L71)** — most callers wrap in try/except already, but should be documented as raising. **Fix: docstring update.** **5 min.**
7. **MH-X1: `apply_monster_treatment` overwrites pick fields without versioning** — only stashes `*_pre_monster` fields, no `monster_overridden_at` timestamp. **Fix: add audit timestamp.** **10 min.**
8. **OAL-X1: `_load_json` swallows all exceptions (L25-26)** — corrupted JSON → empty dict silently. Should log corruption events. **Fix: structured log.** **10 min.**

---

## NEW THEMES INTRODUCED THIS BATCH

- **T184 (READ-SIDE FAIL-CLOSED GUARD with cross-validation against contract):** OAL-X1 — `validate_official_artifacts_for_rows` re-validates artifacts AND detects orphans (artifacts without rows, rows without artifacts). Multi-direction integrity check.
- **T185 (MONITORING-ONLY MODE WITH PROMOTE-LATER CONTRACT):** ORS-X1 — `watch_only=True` always; explicit "promote into actionable planning" contract documented in docstring.
- **T186 (CURL_CFFI BROWSER-IMPERSONATION FALLBACK):** UN-X1 — chrome-impersonation HTTP session as primary, plain `requests` as fallback. Defends against Wikipedia/Cloudflare bot detection.
- **T187 (FRESHNESS-WEIGHTED SIGNAL DECAY):** WM-X1 — 5-tier multiplier ladder for news boost decay. Explicit operator-readable thresholds.

---

## src/official_pick_artifact.py (327 lines) — LINE BY LINE

- OPA-1 GOOD (L1-11): **11-line docstring with 5-bullet `Safety:` header**.
- OPA-2 GOOD (L17): TZ-aware UTC + zoneinfo imports.
- OPA-3 GOOD (L20): `from .zoneinfo import ZoneInfo` — Python 3.9+ stdlib (no pytz dep).
- OPA-4 GOOD (L22): Cross-cuts to github_observability for run/commit URL stamping.
- OPA-5 GOOD (L24-31): 6-symbol import from PDC contract — strong coupling to single source of truth.
- OPA-6 GOOD (L34): `ET = ZoneInfo("America/New_York")` module constant.
- OPA-7 GOOD (L38-39): `_safe_ticker` strict alphanumeric+`_-` filter — **prevents path traversal** in filename construction.
- OPA-8 GOOD (L42-43): Filename includes date+ticker for natural ordering.
- OPA-9 GOOD (L46-47): Artifact ID format `premarket_official_pick:DATE:TICKER` — colon-separated for grep-friendliness.
- OPA-10 GOOD (L50-52): Decision ID composite includes 12-char short SHA via `commit_sha[:12]`.
- OPA-11 GOOD (L55-70): `_safe_float` and `_safe_int` defensive coercion with `(None, "")` defense.
- OPA-12 GOOD (L73-84): `_json_safe` recursive serializer with **3 truncation rules**:
  - L77: lists cap at 25 elements
  - L81: dicts cap at 75 keys
  - L82: drops 3 dataframe-shaped keys (`df`, `dataframe`, `history`)
- OPA-13 BUG-MINOR (L77/L81): Magic numbers 25/75 — should be module constants.
- OPA-14 GOOD (L87-99): `_score_components` extracts 8 known score keys with isinstance defense.
- OPA-15 GOOD (L102-107): `_risk_dollars` with **`max(0.0, ...)` non-negative guard** (handles SL > entry edge case).
- OPA-16 GOOD (L110-132): `_risk_flags` produces 4 flag types (WATCH_ONLY, EARNINGS_WITHIN_10_DAYS, SMELL_*, PREMARKET_*) with `sorted(set(...))` dedup at end.
- OPA-17 GOOD (L118): `int(days) < 10` for earnings flag — single-arg conversion with try/except.
- OPA-18 GOOD (L135-149): `_selection_reason` builds operator-readable concatenated explanation.
- OPA-19 GOOD (L152-165): `_invalidation_conditions` returns 3 standard conditions + 2 conditional (SL/TP).
- OPA-20 GOOD (L168-234): `build_official_pick_artifact` master:
  - L182-184: TZ-aware ET conversion
  - L191-192: env-var fallback for workflow_run_id and commit_sha
  - L194: github_observability metadata expansion via `**`
  - L196-232: 31-field payload with 5 nested helper calls + 2 hard-coded `False` safety flags
- OPA-21 GOOD (L230-231): `paper_trading_enabled: False` and `live_trading_enabled: False` HARD-CODED — cannot be flipped via config.
- OPA-22 GOOD (L237-238): Path helper for downstream callers.
- OPA-23 GOOD (L241-326): `write_official_pick_artifacts` master:
  - L261: mkdir parents=True at call time
  - L262-266: ET-relative date defaults
  - L271-287: per-pick build → validate → conditional skip-with-error-record
  - L289: **JSON write with `sort_keys=True`** ✅ for deterministic output
  - L290-305: per-artifact summary record
  - L307-322: daily summary aggregation with 13 fields
  - L324-325: write summary artifact
- OPA-24 GOOD (L289): `sort_keys=True` makes artifacts diff-friendly across runs.
- OPA-25 GOOD (L284): Validation errors per-ticker tracked; non-validating picks SKIP write but still appear in `validation_errors`.

---

## src/official_artifact_loader.py (147 lines) — LINE BY LINE

- OAL-1 GOOD (L1-10): **10-line docstring with 3-bullet `Reporting-only:` header**.
- OAL-2 GOOD (L18): Imports validate_official_pick from PDC contract.
- OAL-3 GOOD (L21-26): `_load_json` defensive try/except → empty dict + isinstance check.
- OAL-4 BUG-MINOR (L25-26): Silent `except Exception: return {}` — corrupted JSON files invisible.
- OAL-5 GOOD (L29-38): `official_pick_artifacts_for_date` glob-based discovery + uppercase ticker key.
- OAL-6 GOOD (L36): `payload["_artifact_path"] = str(path)` — underscore prefix marks loader-injected metadata.
- OAL-7 GOOD (L41-46): `official_pick_summary_for_date` returns dict (or empty) with `_artifact_path`.
- OAL-8 GOOD (L49-51): `_merge_non_empty` only writes if value not None/empty — prevents stomping.
- OAL-9 GOOD (L54-93): `enrich_pick_row_with_artifact` master:
  - L62-64: artifact-missing path returns row with `official_artifact_present: False`
  - L66-80: 14 explicit `official_*` prefix fields
  - L82-91: 9 canonical CSV-compat overrides (ticker/company/score/entry/SL/TP/R:R/qty/risk_dollars/regime)
- OAL-10 GOOD (L70): Falls back to `_artifact_path` (loader-injected) before `artifact_path` (artifact field) — sensible precedence.
- OAL-11 GOOD (L96-102): `enrich_pick_rows_with_artifacts` batch helper.
- OAL-12 GOOD (L105-146): `validate_official_artifacts_for_rows` master:
  - L116: errors list
  - L119-120: empty-rows-no-artifacts → single error
  - L122-129: per-row ticker presence check
  - L131-134: per-ticker artifact presence check
  - L136-137: per-ticker date match check
  - L139-140: per-ticker re-validation against PDC contract
  - L142-144: **detect orphan artifacts** (no matching row) — extra integrity check
- OAL-13 GOOD (L142-144): `extra_tickers = sorted(set(artifacts) - set(expected_tickers))` — bidirectional integrity check.
- **OAL-14: 1 minor (silent except L25), otherwise excellent. Theme T184 newly introduced.**

---

## src/provider_failure_taxonomy.py (252 lines) — LINE BY LINE

- PFT-1 GOOD (L1-7): **7-line docstring** with explicit "observe-only" + "does not fetch data" declaration.
- PFT-2 GOOD (L15-27): **`CANONICAL_FAILURE_TYPES` 11-type set** — closed enum.
- PFT-3 GOOD (L30-42): `LEGACY_ERROR_BUCKET_BY_FAILURE_TYPE` 11-key map (canonical → legacy).
- PFT-4 GOOD (L45-52): `FAILURE_TYPE_BY_LEGACY_ERROR_BUCKET` 6-key reverse map (legacy → canonical).
- PFT-5 GOOD (L55-61): `@dataclass(frozen=True) ProviderFailureClassification` with 3 fields — **frozen** prevents accidental mutation.
- PFT-6 GOOD (L64-67): `_raw_text` handles BaseException AND non-exception inputs.
- PFT-7 GOOD (L70-183): `classify_provider_failure` master:
  - L84-93: Joins 4 inputs (exc/result/stage/status) with space
  - L94: lower() for case-insensitive match
  - L96-97: empty-input → unknown
  - L99-106: rate_limited (5 sub-patterns including "yfratelimiterror" and HTTP 429)
  - L108-109: timeout
  - L111-117: market_closed (4 patterns including "weekend" and "holiday")
  - L119-125: stale_data (4 patterns including "previous trading day")
  - L127-136: symbol_not_found (7 patterns including "delisted" and "possibly delisted")
  - L138-146: missing_quote (6 patterns including "missing currentprice")
  - L148-156: missing_intraday_bars (6 patterns including "no opening-range bars")
  - L158-165: missing_history (5 patterns)
  - L167-168: empty_response (3 patterns)
  - L170-181: provider_exception (9 patterns including "ssl", "network", "401")
  - L183: unknown_provider_failure default
- PFT-8 GOOD (L99-181): **CASCADE ORDER MATTERS** — most-specific patterns first, generic last. Documented implicitly through ordering.
- PFT-9 GOOD (L186-191): `legacy_error_bucket_for_failure_type` lookup with safe default.
- PFT-10 GOOD (L194-199): `failure_type_for_legacy_error_bucket` lookup with safe default + None-defense.
- PFT-11 GOOD (L202-214): `classify_legacy_provider_error` — **detects unauthorized BEFORE delegating** to canonical (preserves test compat).
- PFT-12 GOOD (L217-247): `classify_provider_failure_detail` returns full ProviderFailureClassification dataclass with 240-char reason truncation.
- PFT-13 GOOD (L226-234): If legacy_error_bucket given AND maps to unknown, **falls through to canonical classification** (defense in depth).
- PFT-14 GOOD (L246): `reason=_raw_text(exc_or_message)[:240]` — bounded reason field for log size safety.
- PFT-15 GOOD (L250-251): `is_canonical_failure_type` simple set-membership test.
- **PFT-16: 0 BUG findings. Theme T57 (PERFECT MODULE) — 47th cumulative perfect.** ✅

---

## src/monster_data.py (57 lines) — LINE BY LINE

- MD-1 GOOD (L1-4): Tiny docstring describing purpose + caching.
- MD-2 GOOD (L10): Cross-cut to market_data_health for structured event recording.
- MD-3 BUG-MINOR (L13): `CACHE_DIR.mkdir(parents=True, exist_ok=True)` at import time (T118 pattern).
- MD-4 GOOD (L17-18): `_cache_path` ticker-uppercase normalization.
- MD-5 GOOD (L21-25): `_is_fresh` 24h check.
- MD-6 BUG (L24-25): **2 naive datetime calls** — `datetime.fromtimestamp(p.stat().st_mtime)` and `datetime.now()`. TZ-unsafe across DST.
- MD-7 GOOD (L28-56): `get_monster_data` master:
  - L33-38: cache hit path with try/except → fall through
  - L40: default result with both fields None
  - L42: import yfinance inline (deferred — large dep)
  - L46-49: defensive None checks before float coerce
  - L50: cache write
  - L51: success event recording
  - L52-54: error path with structured event recording + classify_provider_error + truncated message
- MD-8 GOOD (L42-43): Inline import of yfinance — saves ~1s startup time when caller doesn't use this module.
- MD-9 GOOD (L51/L53): Both success and error paths record structured events — operator-friendly observability.

---

## src/monster_hunt.py (141 lines) — LINE BY LINE

- MH-1 GOOD (L1-22): **22-line docstring with full scoring table + threshold + design philosophy**.
- MH-2 GOOD (L21): Explicit "Designed to be ADDITIVE — never blocks normal picks" contract.
- MH-3 GOOD (L26-100): `score_monster` master:
  - L34-39: 39-line docstring with explicit "missing data contributes 0 (no penalty)" semantics
  - L40-41: `components` and `reasons` parallel data structures
  - L43-49: earnings ≤7d = +0.20
  - L50-55: short>15% = +0.20
  - L57-62: float<50M = +0.15
  - L64-69: RVOL>1.5 = +0.15
  - L71-76: bullish_news = +0.15
  - L78-83: composite≥0.85 = +0.10
  - L85-91: catalyst_combo (earnings≤14d AND vol>1.2) = +0.05
  - L93: `min(1.0, sum(...))` cap to 1.0
  - L99: is_monster threshold = 0.60
- MH-4 GOOD (L44/L51/L58/L65/L86): Each branch defends against None inputs with `is not None` check.
- MH-5 GOOD (L46/L53/L60/L67/L74/L81/L89): Per-component reason strings — operator-readable audit trail.
- MH-6 GOOD (L93): `round(min(1.0, ...), 3)` — cap before round.
- MH-7 GOOD (L103-140): `apply_monster_treatment` master:
  - L115-116: stamp monster_score and is_monster on pick
  - L118-119: early return if not monster (idempotent for non-monsters)
  - L122-124: defensive entry float coerce
  - L126-127: 5% wider SL, 25% TP — hard-coded
  - L128-129: lottery sizing — `max(1, int(...))` floor
  - L131-133: stash 3 `*_pre_monster` fields for audit
  - L135-138: overwrite SL/TP/qty + recompute risk_reward
- MH-8 GOOD (L129/L138): `max(entry - monster_sl, 0.01)` floor — prevents division by zero.
- MH-9 GOOD (L131-133): Audit-trail stash pattern — original values preserved.

---

## src/opening_range_scanner.py (278 lines) — LINE BY LINE

- ORS-1 GOOD (L1-18): **18-line docstring with bar-shape contract example**.
- ORS-2 GOOD (L27-29): 3 module constants — ET, MARKET_OPEN_ET=09:30, DEFAULT_RANGE_MINUTES=15.
- ORS-3 GOOD (L32-47): `_as_dt` normalizer — **handles datetime, str, raises on others** with explicit TypeError.
- ORS-4 GOOD (L45-47): **Naive datetimes interpreted as ET** (sensible default for intraday market data).
- ORS-5 GOOD (L50-57): `_num` defensive float coerce with `(None, "", "None")` defense.
- ORS-6 GOOD (L60-61): `_vol` thin wrapper.
- ORS-7 GOOD (L64-73): `_session_date` infers from first bar OR explicit input.
- ORS-8 BUG-MINOR (L70-71): Raises ValueError on empty bars — should be documented in docstring.
- ORS-9 GOOD (L76-88): `opening_range_bounds` returns [start, end) tuple.
- ORS-10 GOOD (L91-155): `calculate_opening_range` master:
  - L102: pre-sort by ts
  - L103-109: empty-defense with `ready=False, blockers=["no_intraday_bars"]`
  - L111-117: range filter via `start <= ts < end`
  - L119-121: bar-count blocker if < min_bars
  - L123-125: filtered highs/lows/closes with `> 0` defense
  - L127-128: missing-prices blocker
  - L130-138: blocker-bearing return
  - L140-142: high/low/width_pct computation with low > 0 defense
  - L144-155: ready return with 9 fields
- ORS-11 GOOD (L142): `width_pct = ((high - low) / low * 100) if low > 0 else 0.0` — division-safe.
- ORS-12 GOOD (L158-171): `latest_post_range_bar` returns last bar after range end (or None).
- ORS-13 GOOD (L174-277): `detect_opening_range_breakout` master:
  - L186-191: 5-line docstring with "monitoring-only" contract
  - L194-199: compute opening range
  - L201-209: not-ready early return with `watch_only=True`
  - L211-220: no-post-range-bar return
  - L222-229: price/breakout/extension/volume_ratio computation
  - L231-233: gap_pct optional from prev_close
  - L235-248: 4-blocker accumulation (price-not-above-OR-high, breakout<min, volume<min, extension>max, |gap|>max)
  - L250-254: entry/stop/take_profit construction with risk-positive guard
  - L256-277: full result dict with `mode="monitoring_only"` literal + 13 fields
- ORS-14 GOOD (L260): `mode="monitoring_only"` literal ensures downstream filters can detect ORB picks for monitor-only handling.
- ORS-15 GOOD (L254): Take profit at fixed 1.5×risk — operator-readable conservative target.

---

## src/picks_csv.py (47 lines) — LINE BY LINE

- PCV-1 GOOD (L1-5): Tiny docstring describing usage by intraday_monitor.
- PCV-2 GOOD (L13-22): `read_open_picks(today)` filters to today+pending. Default `evaluation_status` to "pending" if missing.
- PCV-3 GOOD (L25-46): `update_pick_row` master:
  - L27-28: empty-file defense
  - L29-30: rows accumulator + found flag
  - L31-40: read all rows, mutating matching row in place
  - L37: `if k in fieldnames` defends against unknown keys
  - L41-45: rewrite full file if found
- PCV-4 BUG-CRITICAL (L42-45): `with LOG_PATH.open("w", ...)` — **NOT ATOMIC**. Crash mid-write corrupts entire picks_log.csv. Same risk class as PT-X1.
- PCV-5 GOOD (L43): `extrasaction="ignore"` prevents stray fields from raising.

---

## src/universe.py (103 lines) — LINE BY LINE

- UN-1 GOOD (L1): Tiny docstring + PR #68 reference.
- UN-2 GOOD (L7-11): **curl_cffi chrome-impersonation session** primary, fallback to None.
- UN-3 GOOD (L13-14): 2 wiki URL constants.
- UN-4 GOOD (L17-21): `_fetch_wiki` ternary — uses cf_requests if available, else plain requests with User-Agent.
- UN-5 GOOD (L24-31): `get_sp500_tickers` with `.` → `-` ticker normalization (BRK.B → BRK-B for yfinance compat).
- UN-6 BUG (L29-31): Silent except → fallback universe with print only.
- UN-7 GOOD (L34-45): `get_nasdaq100_tickers` with **multi-column-name fallback** (Ticker OR Symbol).
- UN-8 BUG (L43-45): Same silent except pattern.
- UN-9 GOOD (L48-50): `_fallback_universe` 12-ticker safe default (mega-caps + ETFs).
- UN-10 GOOD (L53-65): `_get_watchlist_additions` PR #68 — wraps `get_watchlist_tickers(bullish_only=True)` in try/except.
- UN-11 BUG (L63-65): Silent except with print only.
- UN-12 GOOD (L68-103): `get_universe` master:
  - L69-79: source dispatch with explicit ValueError on unknown
  - L82-85: always-include semis with `dict.fromkeys` dedup pattern
  - L88-95: PR #68 always-include watchlist with operator-readable diff print
  - L98-99: excluded_tickers filter with case-insensitive set
  - L101-102: operator summary print with semi-count
- UN-13 GOOD (L85, L92): `dict.fromkeys` dedup pattern preserves order — better than set().

---

## src/watchlist_manager.py (191 lines) — LINE BY LINE

- WM-1 GOOD (L1-7): **7-line docstring with PR #68 freshness narrative**.
- WM-2 GOOD (L13-15): 3 module constants — WATCHLIST_PATH, TTL=72h, MIN_TRADEABLE_SCORE=0.5.
- WM-3 GOOD (L18-24): `_load` defensive try/except → empty items list.
- WM-4 BUG-MINOR (L27-29): `_save` non-atomic write (no tmp+rename).
- WM-5 GOOD (L32-42): `_prune_expired` with TZ-aware UTC + per-item try/except → drop bad records.
- WM-6 GOOD (L45-52): `_hours_old` returns **999 on parse failure** ("treat as ancient" L52) — sensible fail-old default.
- WM-7 GOOD (L55-68): `_freshness_multiplier` 5-tier ladder (`<4h=2.0`, `<8h=1.5`, `<24h=1.0`, `<48h=0.6`, `≥48h=0.3`). NEW Theme T187.
- WM-8 GOOD (L71-115): `add_from_news` master:
  - L73-74: load + prune in same call
  - L77-83: per-item validation (ticker AND score >= MIN_TRADEABLE_SCORE)
  - L85-97: existing-ticker path — **score-monotonic update** (only overwrite if higher)
  - L99-112: new-entry path with 10 fields including `added_at` TZ-aware UTC
- WM-9 GOOD (L118-122): `get_watchlist` returns sorted-by-score-desc list.
- WM-10 GOOD (L125-133): `get_watchlist_tickers(bullish_only=False)` with optional sentiment filter.
- WM-11 GOOD (L136-162): `watchlist_score_boost` master:
  - L150-151: hours_old + freshness_multiplier
  - L155: base = `tradeable_score * 0.15 * fresh_mult` — formula breakdown
  - L158: cap at ±0.30
  - L160-162: bearish negation
- WM-12 GOOD (L165-180): `watchlist_meta` rich diagnostic for display/debug with 8 fields.
- WM-13 GOOD (L183-190): `__main__` smoke test with operator-readable per-ticker formatted output.
- WM-14 GOOD (L131-132): `bullish_only` filter via list comprehension with `sentiment == "bullish"` string check.

---

## src/market_guard.py (116 lines) — LINE BY LINE

- MG-1 GOOD (L1): Tiny docstring describing 3 guards.
- MG-2 GOOD (L5-11): `vix_level` — 2d history + close + 0.0 default.
- MG-3 BUG-MINOR (L10-11): Silent except → 0.0 fallback (callers can't distinguish "VIX is 0" from "data missing" — though VIX=0 is impossible in practice).
- MG-4 BUG-CRITICAL (L13-26): `spy_trend` **fail-OPEN to all-True defaults** — when data missing, returns `above_50dma=True, above_200dma=True`. Strategy treats this as bullish go-ahead. Should fail-closed (None or False) to be safe.
- MG-5 GOOD (L17-18): Insufficient-history early-return — but **uses fail-open defaults** L18.
- MG-6 GOOD (L20-24): Correct rolling-mean comparison with explicit bool() coerce.
- MG-7 GOOD (L28-51): `sector_strength` with **12-sector default ETF map** (XLK/SOXX/XLV/XLF/XLE/XLY/XLP/XLI/XLC/XLU/XLRE/XLB).
- MG-8 BUG (L49-50): Silent per-sector except continue — operator can't tell which sectors failed.
- MG-9 GOOD (L46-48): Day-over-day change with `weak: change < -0.02` threshold.
- MG-10 GOOD (L53-103): `classify_trade_type` with **PR #67 archaeology** ("Old logic required momentum>0.75 AND volume>0.7 which was IMPOSSIBLY HIGH... 28 picks tagged 'swing', causing -6% losses").
- MG-11 GOOD (L75-77): Score field defaults to 0.5 (neutral) when missing.
- MG-12 GOOD (L80-85): ATR/price ratio with 0.02 default + price>0 defense.
- MG-13 GOOD (L88-93): **4-condition AND for day classification** — momentum≥0.65 + volume≥0.55 + atr_ratio≤0.035 + |gap|<0.04. NEW Theme T188 (REALISTIC vs IMPOSSIBLY-HIGH thresholds — operator-archaeology pattern).
- MG-14 GOOD (L98-103): Trend-based swing classification with safe default.
- MG-15 GOOD (L106-116): `classify_with_day_score` enhanced classifier — **dual-gate (day_score≥0.65 AND |gap|<0.04)** falls through to base classifier on miss.
- MG-16 GOOD (L114): Same gap threshold (0.04) reused — consistent across both classifiers.

---

## CONSOLIDATED CROSS-CUTTING (THIS BATCH)

### NEW Themes T184-T188 (5 new)

- **T184 (READ-SIDE FAIL-CLOSED GUARD with cross-validation against contract):** OAL-X1 — `validate_official_artifacts_for_rows` re-validates artifacts AND detects orphans bidirectionally.
- **T185 (MONITORING-ONLY MODE WITH PROMOTE-LATER CONTRACT):** ORS-X1 — `watch_only=True` always; explicit "promote into actionable planning" contract.
- **T186 (CURL_CFFI BROWSER-IMPERSONATION FALLBACK):** UN-X1 — chrome-impersonation HTTP session as primary, plain `requests` as fallback.
- **T187 (FRESHNESS-WEIGHTED SIGNAL DECAY):** WM-X1 — 5-tier multiplier ladder for news boost decay.
- **T188 (REALISTIC vs IMPOSSIBLY-HIGH thresholds — operator-archaeology pattern):** MG-X1 — PR #67 archaeology preserves the original (broken) thresholds in docstring for posterity.

### Theme T57 (PERFECT MODULES) NOW 48 cumulative
- +1 this batch: PFT (provider_failure_taxonomy). (OPA has minor magic numbers; OAL has minor silent except; MD/MH/ORS/PCV/UN/WM/MG all have ≥1 finding.)

### Theme T6 (atomic writes) UPDATE
- **0 atomic this batch.**
- **+2 unsafe** (PCV-X1 picks_csv rewrite, WM-X1 watchlist_manager rewrite).
- Running tally: ~18 safe / ~136 unsafe.

### Cross-cutting tally summary (this batch only)

| Metric | Count this batch |
|---|---:|
| Files actually fetched & line-audited | 10/10 ✅ |
| Total lines audited | 1,659 |
| Bare `except:` | 0 |
| Silent `except Exception` (no log) | 6 (OAL ×1, UN ×3, MG ×2) |
| Silent `except` with `print()` only | 3 (UN-X1) |
| Silent except → safe-default | 4 (MG ×2 fail-open, WM ×1, MD ×1) |
| Naive datetime usage | 2 (MD-X1) |
| TZ-aware UTC | 8 (OPA ×2, OAL via OPA, ORS ×4 via ET, WM ×4) |
| Atomic writers | 0 |
| Unsafe writers | 2 (PCV, WM) |
| Inline imports | 4 (MD-X1 yf, UN-X1 requests + watchlist) |
| Module-level side effects | 1 (MD mkdir at import) |
| Dataclasses | 1 (PFT-X1 frozen) |
| `__main__` smoke tests | 1 (WM-X1) |
| 0-BUG perfect modules | 1 (PFT) |
| Operator-readable archaeology | 4 (PR #67, PR #68 ×2, "trade_type was IMPOSSIBLY HIGH") |
| Fail-closed gates | 1 (OAL-X1 validate) |
| Fail-open gates | 1 (MG-X1 spy_trend — anomaly!) |

---

## SUMMARY (Batch 98 — 10-FILE)

| File | Critical | Bug | Code smell | Good | Total findings |
|---|---:|---:|---:|---:|---:|
| official_pick_artifact | 0 | 0 | 1 | 24 | 25 |
| official_artifact_loader | 0 | 1 | 0 | 13 | 14 |
| provider_failure_taxonomy | 0 | 0 | 0 | 16 | 16 |
| monster_data | 0 | 2 | 0 | 7 | 9 |
| monster_hunt | 0 | 0 | 0 | 9 | 9 |
| opening_range_scanner | 0 | 1 | 0 | 14 | 15 |
| picks_csv | 1 | 0 | 0 | 4 | 5 |
| universe | 0 | 3 | 0 | 10 | 13 |
| watchlist_manager | 0 | 1 | 0 | 13 | 14 |
| market_guard | 1 | 3 | 0 | 12 | 16 |
| **TOTAL** | **2** | **11** | **1** | **122** | **136** |

---

## TOP 10 PRIORITY FIXES FROM BATCH 98

1. **MG-X1 spy_trend fail-open default (L18, L26)** — flip to fail-closed (None or `data_unavailable=True`). **30 min.**
2. **PCV-X1 atomic CSV rewrite** — tmp+rename. **15 min.**
3. **WM-X1 atomic JSON write** — tmp+rename. **15 min.**
4. **MD-X1 2 naive datetime calls** — TZ-aware UTC. **10 min.**
5. **UN-X1 3 silent except with print** — log via structured channel. **15 min.**
6. **OPA-X1 magic numbers in `_json_safe`** — extract to module constants. **10 min.**
7. **OAL-X1 silent except in `_load_json`** — log corruption events. **10 min.**
8. **ORS-X1 `_session_date` ValueError on empty** — document in docstring. **5 min.**
9. **MH-X1 add `monster_overridden_at` audit timestamp.** **10 min.**
10. **MG-X1 sector_strength silent per-sector except** — track failed-sectors set. **15 min.**

---

## COVERAGE TRACKER (HONEST)

| Phase | Files in `src/` | Verifiably audited (this convo, line-by-line) |
|---|---:|---:|
| Pre-batch-98 | 92 | 66 |
| **Post-batch-98** | **92** | **76** |
| Remaining `src/` top-level | — | **16 files (~17%)** |

Plus subdirectories: `src/backtester/` (5), `src/market_data_providers/` (2), `src/patterns/` (10) — all unverified.

End of Batch 98.
