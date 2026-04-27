"""Optional LLM rationale layer."""
import os
from typing import List, Dict
try:
    from openai import OpenAI
    _OPENAI_OK = True
except Exception:
    _OPENAI_OK = False

def explain_pick(ticker: str, scores: dict, plan: dict,
                 news: List[Dict], model: str = "gpt-4o-mini") -> str:
    if not _OPENAI_OK or not os.getenv("OPENAI_API_KEY"):
        return _rule_based(ticker, scores, plan)
    client = OpenAI()
    headlines = "\n".join(f"- {n['title']}" for n in news[:3]) or "No recent headlines."
    prompt = f"""You are a careful trading assistant. In 4 short sentences,
explain why {ticker} scored {scores['composite']:.2f} today plus the trade plan.
Mention 1 risk. Do NOT imply certainty.

Scores: {scores}
Plan: {plan}
Headlines:
{headlines}
"""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=300,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return _rule_based(ticker, scores, plan) + f"\n(LLM error: {e})"

def _rule_based(ticker, scores, plan):
    parts = [f"{ticker} composite score {scores['composite']:.2f}."]
    top = sorted([(k, v) for k, v in scores.items()
                  if isinstance(v, (int, float)) and k not in
                  ("composite", "raw_score", "sector_mult")],
                 key=lambda x: x[1], reverse=True)[:3]
    parts.append("Top factors: " + ", ".join(f"{k}={v:.2f}" for k, v in top) + ".")
    if plan:
        parts.append(f"Plan: entry ${plan['entry']}, SL ${plan['stop_loss']}, "
                     f"TP ${plan['take_profit']} (R:R {plan['risk_reward']}).")
    parts.append("Confirm independently. No certainty implied.")
    return " ".join(parts)
