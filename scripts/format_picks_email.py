"""Markdown formatter for GitHub issue (email).

Priority 10: enrich user-facing output from validated official pick artifacts.
CSV remains the fallback row source, but official artifacts are preferred for
official decision details.
"""
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.validate_daily_no_pick import validate_no_pick_report
from src.official_artifact_loader import (
    enrich_pick_rows_with_artifacts,
    official_pick_summary_for_date,
    validate_official_artifacts_for_rows,
)


# Honor PICK_DATE override so tests / backfills / replays can format a specific
# ET date rather than always defaulting to "today". Mirrors the same pattern
# already used by scripts/send_layman_daily.py.
today = (os.getenv("PICK_DATE") or datetime.now().strftime("%Y-%m-%d")).strip()
rows = []
p = Path("data/picks_log.csv")
if p.exists():
    rows = [r for r in csv.DictReader(p.open()) if r.get("pick_date") == today]
rows = enrich_pick_rows_with_artifacts(rows, today)
official_summary = official_pick_summary_for_date(today)


def _load_no_pick_report():
    report_path = Path(f"data/daily_picks_no_pick_report_{today}.json")
    if not report_path.exists():
        return {}
    try:
        data = json.loads(report_path.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


no_pick_report = _load_no_pick_report()


def _fail_user_output(errors):
    print("# Daily Stock Picks — blocked\n", file=sys.stderr)
    print("Official decision artifact validation failed; user-facing output is blocked.", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    raise SystemExit(1)


if rows:
    artifact_errors = validate_official_artifacts_for_rows(rows, today)
    if artifact_errors:
        _fail_user_output(artifact_errors)
elif no_pick_report:
    no_pick_errors = validate_no_pick_report(no_pick_report)
    if no_pick_errors:
        _fail_user_output(no_pick_errors)
else:
    _fail_user_output([f"no picks logged and no valid official no-pick artifact found for {today}"])

pm = {}
pmp = Path("data/premarket_check.json")
if pmp.exists():
    try:
        pm = json.loads(pmp.read_text())
    except Exception:
        pm = {}

tags = {x["ticker"]: x for x in pm.get("picks", [])}
mkt = pm.get("market", {})

print(f"# 📈 Daily Stock Picks — {today}\n")

if not rows:
    if no_pick_report:
        print("## 📭 Official No-Pick Decision\n")
        print(
            f"**Reason:** "
            f"{no_pick_report.get('human_readable_summary') or no_pick_report.get('reason') or 'No qualified official pick today.'}\n"
        )
        print(f"- Primary cause: `{no_pick_report.get('primary_no_pick_cause', 'unknown')}`")
        print(f"- Data readiness: `{no_pick_report.get('data_readiness_status', 'unknown')}`")
        print(f"- Provider status: `{no_pick_report.get('provider_status', 'unknown')}`")
        if no_pick_report.get("decision_id") or no_pick_report.get("artifact_id"):
            print(f"- Official trace: `{no_pick_report.get('decision_id') or no_pick_report.get('artifact_id')}`")
        if no_pick_report.get("workflow_run_url"):
            print(f"- Workflow run: {no_pick_report.get('workflow_run_url')}")
        if no_pick_report.get("artifact_bundle_name"):
            print(f"- Artifact bundle: `{no_pick_report.get('artifact_bundle_name')}`")
        if no_pick_report.get("artifact_path"):
            print(f"- Artifact path: `{no_pick_report.get('artifact_path')}`")
        print(f"- Next action: {no_pick_report.get('next_action', 'Do not fabricate official picks.')}\n")
        print("_No official premarket pick was generated. This is a valid safety outcome, not a buy instruction._")
    raise SystemExit

artifact_count = official_summary.get("official_pick_count")
artifact_note = (
    f" • Official artifacts: `{artifact_count}`"
    if artifact_count not in (None, "")
    else ""
)
print(
    f"**{len(rows)} picks** • Regime: `{rows[0].get('regime','?')}` "
    f"• CAPE: `{rows[0].get('cape','?')}`{artifact_note}\n"
)

if mkt:
    print("## 🌐 Market Conditions\n")
    print("| Index | Change |")
    print("|-------|--------|")
    print(f"| SPY (S&P 500) | {mkt.get('spy_change_pct',0):+.2f}% |")
    print(f"| QQQ (Nasdaq) | {mkt.get('qqq_change_pct',0):+.2f}% |")
    print(f"| SOXX (Semis) | {mkt.get('soxx_change_pct',0):+.2f}% |")
    print(f"| VIX | {mkt.get('vix','?')} |\n")
    for w in mkt.get("warnings", []):
        print(f"- {w}")
    if mkt.get("global_action") == "skip_all":
        print("\n### 🚫 RECOMMENDATION: SKIP ALL TRADES TODAY\n")
    elif mkt.get("global_action") == "half":
        print("\n### ⚠️ RECOMMENDATION: Reduce all positions by 50% today\n")

print("\n## 🎯 Picks\n")
print("| # | Type | Ticker | Tag | Score | Entry | Now | SL | TP | R:R | Qty | Official | Note |")
print("|---|------|--------|-----|-------|-------|-----|----|----|-----|-----|----------|------|")

for i, r in enumerate(rows, 1):
    try:
        entry = float(r["entry"])
        sl = float(r["stop_loss"])
        tp = float(r["take_profit"])
        risk = (entry - sl) / entry * 100
        reward = (tp - entry) / entry * 100
    except Exception:
        entry = sl = tp = 0
        risk = reward = 0

    ticker = r.get("ticker", "")
    t = tags.get(ticker, {})
    tag = t.get("tag", "—")
    cur = t.get("current_price")
    cur_str = f"${cur:.2f}" if cur else "—"
    note = (r.get("official_selection_reason") or t.get("reason", ""))[:80]
    official = "✅ artifact" if r.get("official_artifact_present") else "⚠️ missing"
    tt = r.get("trade_type", "swing")
    type_emoji = "🔥 DAY" if tt == "day" else "⚡ SWG"

    print(
        f"| {i} | {type_emoji} | **{ticker}** | {tag} | {float(r['score']):.2f} | "
        f"${entry:.2f} | {cur_str} | ${sl:.2f} (−{risk:.1f}%) | ${tp:.2f} (+{reward:.1f}%) | "
        f"{r.get('risk_reward','2.0')} | {r.get('qty','-')} | {official} | {note} |"
    )

if any(r.get("official_artifact_present") for r in rows):
    print("\n## 🧾 Official Decision Artifacts")
    print("- This issue is generated from validated official pick artifacts plus the CSV log.")
    for r in rows:
        if r.get("official_artifact_present"):
            trace = r.get("official_decision_id") or r.get("official_artifact_id") or "trace unavailable"
            run_ref = r.get("official_workflow_run_url") or "run URL unavailable"
            bundle_ref = r.get("official_artifact_bundle_name") or "artifact bundle unavailable"
            print(
                f"- **{r.get('ticker')}**: `{r.get('official_contract_version')}` — "
                f"`{trace}` — {r.get('official_artifact_path')} — "
                f"run: {run_ref} — bundle: `{bundle_ref}`"
            )

print("\n## 📋 Tag Legend")
print("- ✅ **SAFE** — proceed normally with planned size")
print("- ⚠️ **HALF SIZE** — reduce position by 50%")
print("- 🚫 **SKIP TODAY** — don't enter, gap risk too high")
print("- 👀 **WATCH ONLY** — no actionable entry until a fresh quote is verified\n")
print("> ⚠️ Educational only. Not financial advice. Always use limit orders.")
