# Lane 1 Final Production Hardening Plan

**Date:** 2026-05-09
**Status:** Pending implementation
**Mode:** Monitoring-only
**Paper trading:** Disabled
**Live trading:** Disabled

## Purpose

Lane 1 is the official premarket daily stock-pick lane.

The product goal is:

> Premarket official daily stock pick before market open, with clear rationale, risk/reward, entry/stop/take-profit, and no-pick handling when data is not ready.

Priorities 1-14 established the core official decision lane:

- official pick contract,
- official no-pick contract,
- data-readiness gate,
- premarket sanity gate,
- portfolio risk gate,
- missing-data fail-closed gate,
- official pick artifacts,
- official no-pick artifacts,
- artifact validation,
- Telegram/GitHub output from official artifacts,
- synthetic official pick dry-run,
- synthetic official no-pick dry-run,
- workflow summary observability,
- production-readiness audit gate.

This document covers the remaining hardening work that should be completed before relying on Monday's scheduled market run as production validation.

Monday's live run should validate production behavior, not reveal known architectural gaps.

---

## Current Lane 1 Status

Completed:

- Priority 1 — production plan documented.
- Priority 2 — official premarket decision contract.
- Priority 3 — valid no-pick treated as successful outcome.
- Priority 4 — premarket data-readiness gate.
- Priority 5 — premarket sanity before official logging.
- Priority 6 — candidate diagnostics.
- Priority 7 — portfolio risk gate.
- Priority 8 — missing-data fail-closed gate.
- Priority 9 — official decision artifact validation/upload.
- Priority 10 — Telegram/GitHub output consumes official artifacts.
- Priority 11 — synthetic official pick dry-run.
- Priority 12 — synthetic no-pick dry-run for all allowed causes.
- Priority 13 — workflow summary observability.
- Priority 14 — production-readiness audit gate.

Remaining before production certification:

- Priority 15 — fail user-facing sends when official artifacts are missing.
- Priority 16 — add official decision/artifact ID traceability.
- Priority 17 — formal no-pick artifacts for market-closed/missed-window guard skips.
- Priority 18 — add workflow/run/artifact links to outputs.
- Priority 19 — live scheduled-run production certification.

---

## Co-Founder Product Position

The key product risk is not whether the model picks the best possible stock on a single day.

The key product risk is whether the system can reliably:

1. make one official decision before market open,
2. explain the decision clearly,
3. avoid forcing picks when data is poor,
4. publish only decisions that passed official validation,
5. leave an audit trail we trust.

Therefore, all known structural safeguards should be implemented before Monday.

The Monday scheduled run should answer:

- Did the real workflow pass?
- Did providers behave under live cron conditions?
- Did the system produce either a valid official pick or valid official no-pick?
- Did Telegram/GitHub output match official artifacts?
- Were artifacts uploaded?
- Was the workflow summary clear?
- Did the audit gate pass?

It should not be used to discover missing fail-closed behavior or missing traceability.

---

# Priority 15 — Fail User-Facing Sends When Official Artifacts Are Missing

## Problem

Telegram and GitHub issue output currently consume official artifacts, but during migration they still retain fallback behavior.

In production, fallback output is risky.

If `picks_log.csv` has rows for today but matching official pick artifacts are missing, the system must not send normal user-facing pick alerts.

## Desired Behavior

If today's CSV has official pick rows:

- matching `data/premarket_official_pick_<date>_<ticker>.json` artifacts must exist,
- artifact count must match CSV row count,
- artifacts must pass the official pick validator,
- Telegram send should fail if artifacts are missing/invalid,
- GitHub issue formatting should fail if artifacts are missing/invalid.

If today has zero CSV rows:

- a valid `data/daily_picks_no_pick_report_<date>.json` must exist,
- no-pick output may proceed only if that artifact validates.

## Acceptance Criteria

- Add strict artifact validation before Telegram output.
- Add strict artifact validation before GitHub issue output.
- Preserve local dry-run/test ergonomics via explicit test fixtures, not silent production fallback.
- Add tests proving:
  - missing pick artifact blocks output,
  - invalid pick artifact blocks output,
  - valid no-pick artifact allows no-pick output,
  - missing no-pick artifact blocks no-pick output.
- Paper/live trading remain disabled.

## Safety Rule

No user-facing official pick alert may be sent unless it can be traced to a validated official decision artifact.

---

# Priority 16 — Add Official Decision / Artifact ID Traceability

## Problem

Official artifacts are the source of truth, but `picks_log.csv`, Telegram, and GitHub issue output should trace directly back to the official decision artifact.

## Desired Behavior

Each official pick artifact should include a stable decision identifier.

Suggested fields:

- `decision_id`
- `artifact_id`
- `artifact_filename`
- `artifact_path`
- `workflow_run_id`
- `commit_sha`
- `contract_version`

CSV rows should include at least:

- `official_decision_id`
- `official_artifact_path`
- `official_contract_version`

User-facing output should display a compact trace reference.

## Acceptance Criteria

- Official pick artifacts include deterministic decision/artifact IDs.
- Pick CSV rows include official decision trace fields.
- Telegram output includes official decision ID or short trace.
- GitHub issue output includes official decision ID/artifact path.
- Tests cover artifact-to-CSV-to-output traceability.
- Existing historical CSV behavior remains backward-compatible.

## Safety Rule

Any user-facing pick should be traceable to exactly one official artifact.

---

# Priority 17 — Formal No-Pick Artifacts for Guard Skips

## Problem

No-pick from `main.py` is first-class. But guard-level skips such as before-window, market-closed, missed-window, or duplicate run are mostly recorded as run-status artifacts.

This creates two classes of non-pick outcomes:

1. official no-pick artifacts from main selection flow,
2. workflow guard status records.

For production clarity, every official decision window should have a first-class decision artifact.

## Desired Behavior

Guard skips should write formal official no-pick artifacts when appropriate.

Relevant no-pick causes:

- `NO_PICK_MARKET_CLOSED`
- `NO_PICK_WINDOW_MISSED`
- possibly `NO_PICK_DUPLICATE_ALREADY_LOGGED`
- possibly `NO_PICK_BEFORE_WINDOW`

Need to decide whether duplicate/before-window are official no-pick decisions or operational skips.

## Acceptance Criteria

- Add helper script for writing guard-level official no-pick artifacts.
- Missed-window guard writes a valid official no-pick artifact.
- Market-closed guard writes a valid official no-pick artifact when workflow runs on closed market day.
- Artifacts validate with `scripts/validate_daily_no_pick.py`.
- Workflow uploads/commits these artifacts.
- Run-status artifacts remain unchanged for observability.
- Tests cover guard-level no-pick artifact generation.

## Safety Rule

If the official premarket decision cannot be made due to timing/session constraints, the system should record a formal no-pick decision instead of silently skipping.

---

# Priority 18 — Add Workflow / Run / Artifact Links to Outputs

## Problem

User-facing output currently says artifacts exist and can include paths, but it does not yet provide ideal clickable workflow/run/artifact links.

## Desired Behavior

Telegram/GitHub issue/workflow summary should include:

- GitHub Actions run URL,
- commit SHA,
- official decision artifact path,
- artifact bundle name,
- workflow summary reference.

Possible run URL format:

    https://github.com/<owner>/<repo>/actions/runs/<run_id>

## Acceptance Criteria

- Add run URL to official pick artifacts where GitHub env vars are available.
- Add run URL to official no-pick artifacts where GitHub env vars are available.
- GitHub issue output includes run URL.
- Telegram output includes a compact audit/run reference.
- Workflow summary includes run URL.
- Tests cover env-var based run URL construction.
- No secrets are printed.

## Safety Rule

Only non-sensitive observability metadata should be exposed.

---

# Priority 19 — Live Scheduled-Run Production Certification

## Problem

All structural readiness can be tested locally/synthetically, but production behavior still requires a real scheduled premarket run.

## Certification Event

Next scheduled premarket run during official window:

- 08:00-09:20 America/New_York

## Certification Checklist

The run is considered a green production validation if:

- workflow guard passes correctly,
- production-readiness audit passes,
- synthetic pick dry-run passes,
- synthetic no-pick dry-run passes,
- smoke tests pass,
- `main.py` completes,
- either:
  - official pick artifacts validate, or
  - official no-pick artifact validates,
- decision artifacts upload,
- workflow summary is clear,
- GitHub issue output matches official artifacts,
- Telegram output matches official artifacts,
- committed artifacts are pushed successfully,
- no paper/live trading artifacts are created.

## Post-Run Required Document Update

After the first green scheduled run, update:

- `docs/WORK_LOG.md`
- `docs/planning/PREMARKET_OFFICIAL_PICK_PRODUCTION_PLAN.md`
- optionally this document

with:

- workflow run URL,
- final decision type,
- artifact summary,
- validation result,
- known issues,
- production-readiness recommendation.

## Possible Outcomes

### Outcome A — Official Pick

Production can be certified if:

- pick artifact validates,
- CSV row traces to artifact,
- Telegram/GitHub issue match the artifact,
- run summary is clear.

### Outcome B — Official No-Pick

Production can still be certified if:

- no-pick artifact validates,
- reason is clear,
- no fake pick is sent,
- run summary is clear.

A no-pick day is not a failure if the artifact is valid and the reason is correct.

### Outcome C — Workflow Failure

Do not certify production readiness.

Open a repair task based on the failing step.

---

## Non-Goals Before Monday

Do not enable:

- paper trading,
- live trading,
- automatic broker execution,
- position sizing escalation,
- post-market trading,
- options trading.

Do not over-optimize scoring until production reliability is proven.

---

## Recommended Implementation Order

1. Priority 15 — fail user-facing sends when official artifacts are missing.
2. Priority 16 — add official decision/artifact ID traceability.
3. Priority 17 — formal no-pick artifacts for guard skips.
4. Priority 18 — add workflow/run/artifact links.
5. Priority 19 — certify after next green scheduled run.

---

## Final Readiness Principle

Lane 1 should be considered production-ready only when every user-facing official decision is:

- validated,
- traceable,
- auditable,
- safe to skip when data is not ready.

Until then:

- Monitoring-only.
- Paper trading disabled.
- Live trading disabled.
