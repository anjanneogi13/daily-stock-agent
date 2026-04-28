"""LLM rationale generation. Supports Gemini (free) + OpenAI."""
import os, time, random, json, hashlib
from pathlib import Path
from datetime import datetime, timedelta

_CACHE_DIR = Path("data/llm_cache")
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_CACHE_TTL = timedelta(hours=12)


def _cache_key(ticker, scores, plan):
    payload = json.dumps({"t": ticker, "s": scores, "p": plan}, sort_keys=True, default=str)
    return hashlib.md5(payload.encode()).hexdigest()


def _cache_get(key):
    p = _CACHE_DIR / f"{key}.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text())
        if datetime.now() - datetime.fromisoformat(d["at"]) < _CACHE_TTL:
            return d["text"]
    except Exception:
        pass
    return None


def _cache_put(key, text):
    try:
        (_CACHE_DIR / f"{key}.json").write_text(json.dumps({"at": datetime.now().isoformat(), "text": text}))
    except Exception:
        pass


_QUOTA_EXHAUSTED = [False]   # module flag — once tripped, skip remaining LLM calls
_LAST_CALL = [0.0]
_MIN_INTERVAL = 5.0


def _rule_based(ticker: str, scores: dict, plan: dict) -> str:
    skip = {"composite", "raw_composite", "sector_mult", "sector_tag"}
    numeric = [(k, v) for k, v in scores.items()
               if k not in skip and isinstance(v, (int, float))]
    top = sorted(numeric, key=lambda x: x[1], reverse=True)[:3]
    factor_str = ", ".join(f"{k}={v:.2f}" for k, v in top) if top else "n/a"
    return (f"{ticker} composite score {scores.get('composite', 0):.2f}. "
            f"Top factors: {factor_str}. "
            f"Plan: entry ${plan.get('entry')}, SL ${plan.get('stop_loss')}, "
            f"TP ${plan.get('take_profit')} (R:R {plan.get('risk_reward')}). "
            f"Confirm independently. No certainty implied.")


def _build_prompt(ticker: str, scores: dict, plan: dict, news: list) -> str:
    headlines = "\n".join(f"- {n.get('title','')}" for n in (news or [])[:5]) or "None"
    return f"""You are a cautious equity research analyst. Write a 3-4 sentence rationale for buying {ticker}.

Scores (0-1): {scores}
Plan: {plan}
Headlines:
{headlines}

Rules:
- Lead with strongest factor.
- Mention one concrete risk.
- Reference entry/stop/target with R:R.
- End with: "Not financial advice."
- Plain prose only, no bullets/markdown.
- Keep under 100 words. Complete every sentence."""


def _gemini(prompt: str, model: str) -> str:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    resp = client.models.generate_content(
        model=model, contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.4,
            max_output_tokens=1200,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    )
    return (resp.text or "").strip()


def _openai(prompt: str, model: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=model, temperature=0.4, max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()


def _throttle():
    elapsed = time.time() - _LAST_CALL[0]
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _LAST_CALL[0] = time.time()


def _is_daily_quota_error(e: Exception) -> bool:
    msg = str(e)
    return "PerDay" in msg or "GenerateRequestsPerDay" in msg or (
        "RESOURCE_EXHAUSTED" in msg and "PerMinute" not in msg
    )


def _gemini_with_retry(prompt: str, model: str, max_retries: int = 1) -> str:
    """Retry only on transient errors. Trip flag on daily-quota errors."""
    if _QUOTA_EXHAUSTED[0]:
        raise RuntimeError("Daily quota exhausted — skipping remaining LLM calls")
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            _throttle()
            return _gemini(prompt, model)
        except Exception as e:
            last_err = e
            msg = str(e)
            if _is_daily_quota_error(e):
                _QUOTA_EXHAUSTED[0] = True
                print("[llm] daily quota exhausted — falling back to rule-based for remaining picks")
                raise
            if "429" in msg or "503" in msg or "UNAVAILABLE" in msg:
                wait = 15 + random.uniform(0, 3)
                print(f"[llm] transient error, waiting {wait:.0f}s before retry...")
                time.sleep(wait)
                continue
            raise
    raise last_err


def _explain_uncached(ticker: str, scores: dict, plan: dict,
                 news: list = None, model: str = "gemini-2.5-flash-lite") -> str:
    prompt = _build_prompt(ticker, scores, plan, news or [])
    try:
        if "gemini" in model.lower() and os.getenv("GEMINI_API_KEY"):
            return _gemini_with_retry(prompt, model)
        if "gpt" in model.lower() and os.getenv("OPENAI_API_KEY"):
            return _openai(prompt, model)
        if os.getenv("GEMINI_API_KEY"):
            return _gemini_with_retry(prompt, "gemini-2.5-flash-lite")
        if os.getenv("OPENAI_API_KEY"):
            return _openai(prompt, "gpt-4o-mini")
    except Exception as e:
        msg = str(e)[:120]
        print(f"[llm] {ticker} failed ({type(e).__name__}: {msg}) — using rule-based")
    return _rule_based(ticker, scores, plan)



def explain_pick(ticker: str, scores: dict, plan: dict,
                 news: list = None, model: str = "gemini-2.5-flash-lite") -> str:
    key = _cache_key(ticker, scores, plan)
    cached = _cache_get(key)
    if cached:
        return cached
    text = _explain_uncached(ticker, scores, plan, news, model)
    _cache_put(key, text)
    return text
