"""Monthly X-ray retrospective."""
import csv, json, os, subprocess
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

today = datetime.now()
today_str = today.strftime("%Y-%m-%d")
month_start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
print(f"[monthly] Range: {month_start} -> {today_str}")

picks_file = Path("data/picks_log.csv")
if not picks_file.exists():
    print("[monthly] No picks_log.csv yet — nothing to analyze. Skipping.")
    import sys; sys.exit(0)
picks = list(csv.DictReader(picks_file.open()))
month_picks = [p for p in picks if month_start <= p.get("pick_date", "") <= today_str]
evaluated = [p for p in month_picks if p.get("evaluation_status") in ("tp_hit", "sl_hit", "expired")]


def f(x, d=0.0):
    try:
        return float(x)
    except Exception:
        return d


def week_of(d):
    dt = datetime.strptime(d, "%Y-%m-%d")
    return (dt - timedelta(days=dt.weekday())).strftime("%Y-%m-%d")


weekly = defaultdict(lambda: {"picks": 0, "evaluated": 0, "tp": 0, "sl": 0, "r_sum": 0.0, "ret_sum": 0.0})
for p in month_picks:
    w = week_of(p["pick_date"])
    weekly[w]["picks"] += 1
    if p.get("evaluation_status") in ("tp_hit", "sl_hit", "expired"):
        weekly[w]["evaluated"] += 1
        if p["evaluation_status"] == "tp_hit":
            weekly[w]["tp"] += 1
        if p["evaluation_status"] == "sl_hit":
            weekly[w]["sl"] += 1
        weekly[w]["r_sum"] += f(p.get("r_multiple", 0))
        weekly[w]["ret_sum"] += f(p.get("actual_return_pct", 0))

weekly_summary = []
for w in sorted(weekly.keys()):
    d = weekly[w]
    wr = d["tp"] / d["evaluated"] * 100 if d["evaluated"] else 0
    avg_r = d["r_sum"] / d["evaluated"] if d["evaluated"] else 0
    avg_ret = d["ret_sum"] / d["evaluated"] if d["evaluated"] else 0
    weekly_summary.append({
        "week_starting": w,
        "picks": d["picks"],
        "evaluated": d["evaluated"],
        "tp": d["tp"],
        "sl": d["sl"],
        "win_rate_pct": round(wr, 1),
        "avg_r": round(avg_r, 3),
        "avg_return_pct": round(avg_ret, 2),
        "total_r": round(d["r_sum"], 2),
    })

trend = []
for i in range(1, len(weekly_summary)):
    prev, curr = weekly_summary[i - 1], weekly_summary[i]
    trend.append({
        "from_week": prev["week_starting"],
        "to_week": curr["week_starting"],
        "win_rate_delta_pp": round(curr["win_rate_pct"] - prev["win_rate_pct"], 1),
        "avg_r_delta": round(curr["avg_r"] - prev["avg_r"], 3),
        "verdict": "improved" if curr["avg_r"] > prev["avg_r"] else "degraded" if curr["avg_r"] < prev["avg_r"] else "flat",
    })


def git_changes():
    try:
        files = ["config/tuning.yaml", "scripts/score.py", "scripts/risk.py",
                 "scripts/main.py", "scripts/premarket_check.py"]
        cmd = ["git", "log", "--since=" + month_start, "--pretty=format:%ad|%s", "--date=short", "--"] + files
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        return [{"date": l.split("|", 1)[0], "msg": l.split("|", 1)[1]} for l in out.splitlines() if "|" in l]
    except Exception as e:
        return [{"error": str(e)}]


changes = git_changes()

obs_path = Path("data/learning/observations.jsonl")
month_obs = []
if obs_path.exists():
    for line in obs_path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            o = json.loads(line)
            if month_start <= o["date"] <= today_str:
                month_obs.append(o)
        except Exception:
            pass

obs_types = defaultdict(int)
for o in month_obs:
    obs_types[o["type"]] += 1


def stat_bucket(getter):
    d = defaultdict(lambda: {"n": 0, "wins": 0, "r_sum": 0.0})
    for p in evaluated:
        k = getter(p)
        d[k]["n"] += 1
        d[k]["wins"] += int(p["evaluation_status"] == "tp_hit")
        d[k]["r_sum"] += f(p.get("r_multiple", 0))
    return {k: {"n": v["n"], "win_rate": round(v["wins"] / v["n"] * 100, 1),
                "avg_r": round(v["r_sum"] / v["n"], 3)}
            for k, v in d.items() if v["n"]}


def score_bucket(p):
    s = f(p.get("score", 0))
    return "0.85+" if s >= 0.85 else "0.80-0.85" if s >= 0.80 else "0.75-0.80" if s >= 0.75 else "<0.75"


stats = {
    "by_score": stat_bucket(score_bucket),
    "by_regime": stat_bucket(lambda p: p.get("regime", "unknown")),
}

ranked = sorted([p for p in evaluated if p.get("r_multiple")],
                key=lambda x: f(x["r_multiple"]), reverse=True)
best = [{"date": p["pick_date"], "ticker": p["ticker"],
         "r": round(f(p["r_multiple"]), 2),
         "return_pct": round(f(p.get("actual_return_pct", 0)), 2)} for p in ranked[:5]]
worst = [{"date": p["pick_date"], "ticker": p["ticker"],
          "r": round(f(p["r_multiple"]), 2),
          "return_pct": round(f(p.get("actual_return_pct", 0)), 2)} for p in ranked[-5:][::-1]]

data_blob = {
    "period": {"start": month_start, "end": today_str,
               "picks": len(month_picks), "evaluated": len(evaluated)},
    "weekly_summary": weekly_summary,
    "trend": trend,
    "code_changes": changes,
    "by_score": stats["by_score"],
    "by_regime": stats["by_regime"],
    "best": best,
    "worst": worst,
    "observation_types": dict(obs_types),
}

# Build prompt without f-strings to avoid triple-quote issues
data_json = json.dumps(data_blob, indent=2)

prompt_parts = [
    "You are a senior quantitative analyst writing a MONTHLY RETROSPECTIVE for an ",
    "automated trading agent. Be brutally honest, data-driven, and write in PLAIN ENGLISH.\n\n",
    "# DATA\n",
    "```json\n", data_json, "\n```\n\n",
    "# YOUR TASK\n",
    "Write a Markdown report with EXACTLY this structure:\n\n",
    "# Monthly X-Ray - ", today_str, "\n\n",
    "## The Bottom Line\n",
    "(One paragraph. Did the agent make money? Improve or get worse? Cite win rate and avg-R.)\n\n",
    "## Week-Over-Week Story\n",
    "For each transition: win rate delta, avg-R delta, verdict.\n",
    "Correlate with code changes. Was the change responsible? Or just market regime?\n\n",
    "## Did Our Tweaks Actually Work?\n",
    "For each code change in git history:\n",
    "- Change, Date, Performance BEFORE, Performance AFTER\n",
    "- Verdict: Helped / Hurt / No clear impact / Insufficient data\n",
    "- If hurt: should we REVERT?\n\n",
    "## What's Working (Keep Doing)\n",
    "## What's NOT Working (Stop or Fix)\n",
    "## Patterns the Agent Should Learn\n",
    "## Recommended Next Month's Experiments\n",
    "For each: Hypothesis, Change, Success metric, Rollback trigger, Confidence.\n\n",
    "## Reverts to Consider\n",
    "## The One Number That Matters\n\n",
    "CRITICAL RULES:\n",
    "1. If <30 evaluated trades, say 'DATA INSUFFICIENT' and skip experiments.\n",
    "2. Every claim cites specific data above.\n",
    "3. NO buzzwords. Be plain.\n",
    "4. If losing money, SAY SO and recommend pausing live trading.\n",
    "5. Acknowledge variance.\n",
]
prompt = "".join(prompt_parts)

print(f"[monthly] {len(month_picks)} picks, {len(evaluated)} closed, {len(weekly_summary)} weeks")

key = os.environ.get("GEMINI_API_KEY")
md = ""
if not key:
    md = "# Monthly X-Ray - " + today_str + "\n\n_GEMINI_API_KEY missing._\n\n```json\n" + data_json + "\n```"
else:
    try:
        from google import genai
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        md = resp.text
    except Exception as e:
        md = "# Monthly X-Ray - " + today_str + "\n\n_Gemini failed: " + str(e) + "_\n\n```json\n" + data_json + "\n```"

out_dir = Path("data/learning")
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / ("monthly_xray_" + today_str + ".md")
out_file.write_text(md)
print("[monthly] Saved " + str(out_file))
print()
print(md[:2500])