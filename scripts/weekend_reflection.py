"""
Weekend review. Reads observations from past 7 days, asks Gemini to write
a plain-English review with concrete suggestions. Saves Markdown for human.
"""
import json, os, sys, csv
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

today = datetime.now().strftime("%Y-%m-%d")
obs_file = Path("data/learning/observations.jsonl")
if not obs_file.exists():
    print("No observations yet"); sys.exit(0)

cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
all_obs = []
for line in obs_file.read_text().splitlines():
    if not line.strip(): continue
    try:
        o = json.loads(line)
        if o["date"] >= cutoff:
            all_obs.append(o)
    except Exception: pass

if not all_obs:
    print("No observations in last 7 days"); sys.exit(0)

# Aggregate stats from picks_log
picks = list(csv.DictReader(Path("data/picks_log.csv").open()))
recent = [p for p in picks if p.get("pick_date","") >= cutoff]
evaluated = [p for p in recent if p.get("evaluation_status") in ("tp_hit","sl_hit","expired")]
tp_count = sum(1 for p in evaluated if p["evaluation_status"]=="tp_hit")
sl_count = sum(1 for p in evaluated if p["evaluation_status"]=="sl_hit")
win_rate = tp_count/len(evaluated)*100 if evaluated else 0

obs_types = Counter(o["type"] for o in all_obs)

prompt = f"""You are a friendly trading coach reviewing a week of an automated stock-picking agent.
Write your response in PLAIN ENGLISH (no jargon) for a retail trader to read on Telegram/email.

# Data You Have

## Week of {cutoff} to {today}
- Total picks generated: {len(recent)}
- Evaluated (closed): {len(evaluated)}
- TP hits: {tp_count}
- SL hits: {sl_count}
- Win rate: {win_rate:.1f}%

## Observation type breakdown
{json.dumps(dict(obs_types), indent=2)}

## All observations from the week (raw)
{json.dumps(all_obs, indent=2)}

# Your Task

Write a Markdown review with this EXACT structure:

# 🧠 Weekend Review — {today}

## 📊 The Week in One Sentence
(One sentence summary of how the week went — be honest, not optimistic.)

## ✅ What's Working Well
- (2-3 bullets in plain English. Each must reference specific tickers/dates from the observations.)

## ❌ What Went Wrong
- (2-4 bullets. For each: what happened, why, and what we can learn.)

## 🔧 Suggested Changes (For Your Review)
For each suggestion, use this format:

### Suggestion 1: <plain-English title>
**The problem:** <2 sentences explaining what's broken, with evidence>

**The fix:** <2 sentences in plain English — what to change>

**Where in the code:** <best guess at file/script — e.g. "scripts/premarket_check.py">

**How to test:** <how you'd verify the fix worked>

**Confidence:** <Low / Medium / High and why>

(Give 2-4 suggestions. NEVER suggest something without evidence from the observations above.)

## 🎓 Lesson of the Week
(One paragraph — what's the single most important thing this week taught us?)

## ⏭️ What I'd Watch For Next Week
- (2-3 things to monitor)

CRITICAL RULES:
1. If fewer than 20 evaluated trades exist, say "Not enough data yet — let's wait another week" and propose ZERO changes.
2. Be brutally honest — if the week was bad, say so.
3. NO buzzwords. Write like you're explaining to a friend at a coffee shop.
4. Every claim must reference a specific observation (e.g. "RMBS on 2026-04-28").
"""

print(f"[reflect] {len(all_obs)} observations, {len(evaluated)} evaluated trades")

import sys
sys.path.insert(0, str(Path(__file__).parent))
from claude_helper import call_gemini

text, err = call_gemini(prompt)
if text:
    md = text
else:
    from local_analyst import analyze
    local = analyze(period_days=7, label="Weekly")
    _err_short = "⚠️ Gemini free quota exhausted — using local analysis." if any(k in str(err) for k in ["RESOURCE_EXHAUSTED","429","quota","404","NOT_FOUND"]) else f"Gemini unavailable: {str(err).splitlines()[0][:150]}"
    md = f"# 🧠 Weekend Review — {today}\n\n_{_err_short}_\n\n---\n\n{local}\n\n---\n\nRaw observations: {len(all_obs)} this week."

out = Path(f"data/learning/weekly_review_{today}.md")
out.write_text(md)
print(f"[reflect] ✅ Saved {out}")
print("\n" + md[:1500])
