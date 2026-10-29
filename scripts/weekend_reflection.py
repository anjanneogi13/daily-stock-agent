"""
Weekend review. Reads observations from past 7 days, asks Gemini to write
a plain-English review with concrete suggestions. Saves Markdown for human.

All work happens inside main() so importing this module (e.g. the scripts
smoke-import test) never writes data/learning/weekly_review_*.md.
"""
import json, os, sys, csv
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

OBS_FILE = Path("data/learning/observations.jsonl")
OUT_DIR = Path("data/learning")


def _load_recent_observations(cutoff: str) -> list:
    all_obs = []
    if OBS_FILE.exists():
        for line in OBS_FILE.read_text().splitlines():
            if not line.strip():
                continue
            try:
                o = json.loads(line)
                if o["date"] >= cutoff:
                    all_obs.append(o)
            except Exception:
                pass
    return all_obs


def _build_prompt(*, today: str, cutoff: str, recent: list, evaluated: list,
                  ws: dict, win: dict, s30: dict, obs_types: Counter,
                  all_obs: list, win_rate: float, tp_count: int, sl_count: int) -> str:
    return f"""You are a friendly trading coach reviewing a week of an automated stock-picking agent.
Write your response in PLAIN ENGLISH (no jargon) for a retail trader to read on Telegram/email.

# Data You Have

## Week of {cutoff} to {today}
- Total picks generated (by pick_date): {len(recent)}
- Trades that CLOSED this week (by evaluated_on, incl. expired-at-horizon and day_close): {len(evaluated)}
- TP hits: {tp_count}
- SL hits: {sl_count}
- Expired at hold horizon / day_close: {ws["by_status"].get("expired", 0)} / {ws["by_status"].get("day_close", 0)}
- Win rate (R > 0): {win_rate:.1f}%
- Total R this week: {ws["total_r"]}  (avg R {ws["avg_r"]})
- Still pending: {win["pending_total"]}  ·  Unverified expired (lost outcomes): {win["unverified_expired_total"]}

## Rolling 30-day evidence base (closed by evaluated_on)
- Closed: {s30["n"]}  ·  Win rate: {(s30["win_rate"] or 0)*100:.1f}%  ·  Total R: {s30["total_r"]}  ·  Avg R: {s30["avg_r"]}
- By status: {json.dumps(s30["by_status"])}

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
1. Judge sample size on the ROLLING 30-DAY closed count above (not the single week). If it is below 20, say "Not enough data yet — let's wait another week" and propose ZERO changes; otherwise you MUST propose changes backed by the numbers.
2. Be brutally honest — if the week was bad, say so.
3. NO buzzwords. Write like you're explaining to a friend at a coffee shop.
4. Every claim must reference a specific observation (e.g. "RMBS on 2026-04-28").
"""


def main() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    all_obs = _load_recent_observations(cutoff)

    sys.path.insert(0, str(Path(__file__).parent))
    sys.path.insert(0, str(Path(__file__).parent.parent))

    if not all_obs:
        # Resilience fix (Sep 2026): the old early-exit here meant one upstream
        # gap (e.g. observations lost to the silent-push bug) cascaded into
        # "Weekly review not generated." on Telegram. The picks ledger is an
        # independent evidence source — ALWAYS write a review from it so the
        # weekend learning loop never goes dark.
        print("No observations in last 7 days — falling back to ledger-only local analysis")
        from local_analyst import analyze
        local = analyze(period_days=7, label="Weekly")
        md = (f"# 🧠 Weekend Review — {today}\n\n"
              f"_⚠️ No learning observations were recorded this week "
              f"(pipeline gap) — this review is computed directly from the "
              f"picks ledger._\n\n---\n\n{local}\n")
        out = OUT_DIR / f"weekly_review_{today}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md)
        print(f"[reflect] ✅ Saved {out} (ledger-only fallback)")
        return 0

    # Aggregate stats from picks_log — canonical window (src/outcome_window):
    # picks MADE this week by pick_date, outcomes LEARNED this week by
    # evaluated_on. The old pick_date-only filter saw ~1 closed swing per week
    # (10-session hold), so the coach said "not enough data" every week while
    # 100+ closed trades were never reviewed (audit 2026-10-29).
    from src.outcome_window import window_report, outcomes_in_window, summarize
    _end = datetime.now().date()
    _start = _end - timedelta(days=7)
    _win = window_report(_start, _end)
    recent = _win["picked"]
    evaluated = _win["closed"]
    _ws = _win["summary"]
    tp_count = _ws["by_status"].get("tp_hit", 0)
    sl_count = _ws["by_status"].get("sl_hit", 0)
    win_rate = (_ws["win_rate"] or 0) * 100
    # Rolling 30-day evidence base so the coach can reason beyond one week.
    _closed_30 = outcomes_in_window(_end - timedelta(days=30), _end)
    _s30 = summarize(_closed_30)

    obs_types = Counter(o["type"] for o in all_obs)

    prompt = _build_prompt(
        today=today, cutoff=cutoff, recent=recent, evaluated=evaluated,
        ws=_ws, win=_win, s30=_s30, obs_types=obs_types, all_obs=all_obs,
        win_rate=win_rate, tp_count=tp_count, sl_count=sl_count,
    )

    print(f"[reflect] {len(all_obs)} observations, {len(evaluated)} evaluated trades")

    from claude_helper import call_gemini

    text, err = call_gemini(prompt)
    if text:
        md = text
    else:
        from local_analyst import analyze
        local = analyze(period_days=7, label="Weekly")
        _err_short = "⚠️ Gemini free quota exhausted — using local analysis." if any(k in str(err) for k in ["RESOURCE_EXHAUSTED","429","quota","404","NOT_FOUND"]) else f"Gemini unavailable: {str(err).splitlines()[0][:150]}"
        md = f"# 🧠 Weekend Review — {today}\n\n_{_err_short}_\n\n---\n\n{local}\n\n---\n\nRaw observations: {len(all_obs)} this week."

    out = OUT_DIR / f"weekly_review_{today}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md)
    print(f"[reflect] ✅ Saved {out}")
    print("\n" + md[:1500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
