"""Markdown formatter for GitHub issue (email)."""
import csv, json
from datetime import datetime
from pathlib import Path

today = datetime.now().strftime("%Y-%m-%d")
rows = []
p = Path("data/picks_log.csv")
if p.exists():
    rows = [r for r in csv.DictReader(p.open()) if r.get("pick_date") == today]

pm = {}
pmp = Path("data/premarket_check.json")
if pmp.exists():
    try: pm = json.loads(pmp.read_text())
    except Exception: pm = {}
tags = {x["ticker"]: x for x in pm.get("picks", [])}
mkt = pm.get("market", {})

print(f"# 📈 Daily Stock Picks — {today}\n")
if not rows:
    print("_No picks today._"); raise SystemExit

print(f"**{len(rows)} picks** • Regime: `{rows[0].get('regime','?')}` • CAPE: `{rows[0].get('cape','?')}`\n")

if mkt:
    print(f"## 🌐 Market Conditions\n")
    print(f"| Index | Change |")
    print(f"|-------|--------|")
    print(f"| SPY (S&P 500) | {mkt.get('spy_change_pct',0):+.2f}% |")
    print(f"| QQQ (Nasdaq) | {mkt.get('qqq_change_pct',0):+.2f}% |")
    print(f"| SOXX (Semis) | {mkt.get('soxx_change_pct',0):+.2f}% |")
    print(f"| VIX | {mkt.get('vix','?')} |\n")
    for w in mkt.get("warnings", []):
        print(f"- {w}")
    if mkt.get("global_action") == "skip_all":
        print(f"\n### 🚫 RECOMMENDATION: SKIP ALL TRADES TODAY\n")
    elif mkt.get("global_action") == "half":
        print(f"\n### ⚠️ RECOMMENDATION: Reduce all positions by 50% today\n")

print(f"\n## 🎯 Picks\n")
print("| # | Ticker | Tag | Score | Entry | Now | SL | TP | R:R | Qty | Note |")
print("|---|--------|-----|-------|-------|-----|----|----|-----|-----|------|")

for i, r in enumerate(rows, 1):
    try:
        entry = float(r["entry"]); sl = float(r["stop_loss"]); tp = float(r["take_profit"])
        risk = (entry - sl) / entry * 100; reward = (tp - entry) / entry * 100
    except Exception: entry=sl=tp=0; risk=reward=0
    t = tags.get(r["ticker"], {})
    tag = t.get("tag", "—")
    cur = t.get("current_price")
    cur_str = f"${cur:.2f}" if cur else "—"
    note = t.get("reason", "")[:40]
    print(f"| {i} | **{r['ticker']}** | {tag} | {float(r['score']):.2f} | "
          f"${entry:.2f} | {cur_str} | ${sl:.2f} (−{risk:.1f}%) | ${tp:.2f} (+{reward:.1f}%) | "
          f"{r.get('risk_reward','2.0')} | {r.get('qty','-')} | {note} |")

print(f"\n## 📋 Tag Legend")
print("- ✅ **SAFE** — proceed normally with planned size")
print("- ⚠️ **HALF SIZE** — reduce position by 50%")
print("- 🚫 **SKIP TODAY** — don't enter, gap risk too high\n")
print("> ⚠️ Educational only. Not financial advice. Always use limit orders.")
