"""
Daily observation logger.
Reads today's execution X-ray + premarket tags, extracts plain-English
lessons, appends to data/learning/observations.jsonl.
Each observation is one JSON line: {date, ticker, type, observation, evidence}.
"""
import csv, json, sys
from datetime import datetime
from pathlib import Path

date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
print(f"[observe] {date}")

# Load exec report
xp = Path(f"data/exec_report_{date}.json")
if not xp.exists():
    print("[observe] No exec report — skipping"); sys.exit(0)
xray = json.loads(xp.read_text())

# Load premarket tags (if present)
pm_path = Path("data/premarket_check.json")
pm = json.loads(pm_path.read_text()) if pm_path.exists() else {"picks":[]}
pm_tags = {p["ticker"]: p for p in pm.get("picks", [])}
mkt = pm.get("market", {})

# Load picks for plan context
picks = {p["ticker"]: p for p in csv.DictReader(Path("data/picks_log.csv").open())
         if p.get("pick_date") == date}

observations = []

def add(ticker, otype, text, evidence):
    observations.append({
        "date": date, "ticker": ticker, "type": otype,
        "observation": text, "evidence": evidence
    })

# Market-level observation
if mkt:
    if mkt.get("global_action") == "skip_all":
        add("MARKET", "regime",
            f"Premarket flagged SKIP_ALL ({', '.join(mkt.get('warnings', []))}). "
            f"Day result: {sum(1 for p in xray['picks'] if p['status']=='SL_HIT')} SL hits "
            f"out of {len(xray['picks'])} picks.",
            {"spy": mkt.get("spy_change_pct"), "vix": mkt.get("vix"), "soxx": mkt.get("soxx_change_pct")})
    elif mkt.get("soxx_change_pct", 0) <= -2.0:
        sl_count = sum(1 for p in xray['picks'] if p['status']=='SL_HIT')
        add("MARKET", "sector_warning",
            f"Semiconductor sector down {mkt['soxx_change_pct']:.2f}% in premarket. "
            f"Result: {sl_count}/{len(xray['picks'])} picks hit SL. "
            f"Lesson: when SOXX is -2% or worse premarket, semis picks are very risky.",
            {"soxx_chg": mkt["soxx_change_pct"], "sl_hits": sl_count})

# Per-pick observations
for p in xray["picks"]:
    t = p["ticker"]; s = p["status"]
    pm_tag = pm_tags.get(t, {}).get("tag", "")

    if s == "SL_HIT":
        further = p.get("further_after_sl_pct", 0)
        no_sl_close = p.get("no_sl_close_pct", 0)
        no_sl_worst = p.get("no_sl_worst_pct", 0)
        if further < -3:  # SL saved a lot
            add(t, "sl_well_placed",
                f"{t}: SL hit, then dropped another {further:.2f}%. SL was excellent — saved major loss. "
                f"Without SL would have closed at {no_sl_close:.2f}%, worst {no_sl_worst:.2f}%.",
                {"sl_pct": p["sl_pct"], "further": further, "no_sl_close": no_sl_close})
        elif further > -0.5:  # SL hit at the bottom
            add(t, "sl_too_tight",
                f"{t}: SL hit, but price barely dropped after ({further:.2f}%). "
                f"SL might be too tight — got stopped out near the low.",
                {"sl_pct": p["sl_pct"], "further": further, "mae": p["mae_pct"]})
        if "🚫 SKIP" in pm_tag:
            add(t, "premarket_correct",
                f"{t}: Premarket tagged SKIP TODAY and indeed hit SL. Premarket filter worked.",
                {"premarket_tag": pm_tag, "outcome": "SL_HIT"})

    elif s == "TP_HIT":
        further = p.get("further_after_tp_pct", 0)
        if further > 2:
            add(t, "tp_too_early",
                f"{t}: TP hit, but price ran another {further:.2f}% afterwards. "
                f"Consider a wider TP or trailing stop on strong momentum names.",
                {"tp_pct": p["tp_pct"], "further": further})
        else:
            add(t, "tp_well_placed",
                f"{t}: TP hit cleanly, only {further:.2f}% more upside left. Good target placement.",
                {"tp_pct": p["tp_pct"], "further": further})
        if "🚫 SKIP" in pm_tag:
            add(t, "premarket_overcautious",
                f"{t}: Premarket tagged SKIP TODAY but pick reached TP. "
                f"Premarket filter may be too conservative on this pattern.",
                {"premarket_tag": pm_tag, "outcome": "TP_HIT"})

    elif s == "OPEN":
        ret = p.get("close_ret_pct", 0)
        mae = p.get("mae_pct", 0)
        mfe = p.get("mfe_pct", 0)
        if ret < -3 and mae < -5:
            add(t, "weak_pick",
                f"{t}: Filled at open, never recovered. Closed {ret:.2f}%, worst {mae:.2f}%. "
                f"MFE was only {mfe:.2f}% — never showed strength. Entry was likely chasing a falling knife.",
                {"ret": ret, "mae": mae, "mfe": mfe})
        elif ret > 1:
            add(t, "promising",
                f"{t}: Closed {ret:.2f}% — neither hit but trending favorably. Worth holding/monitoring.",
                {"ret": ret, "mfe": mfe})

    elif s == "NOT_FILLED":
        miss = p.get("missed_by_pct", 0)
        if miss > 1:
            add(t, "missed_opportunity",
                f"{t}: Limit order never filled (missed by {miss:+.2f}%). "
                f"Entry price may have been too low / too pessimistic.",
                {"missed_by": miss})

# Append to journal
out = Path("data/learning/observations.jsonl")
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("a") as f:
    for o in observations:
        f.write(json.dumps(o) + "\n")

print(f"[observe] ✅ Logged {len(observations)} observations")
for o in observations[:5]:
    print(f"  • [{o['type']}] {o['ticker']}: {o['observation'][:100]}...")
