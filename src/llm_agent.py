"""LLM rationale generation.
Priority: Claude Sonnet 4.5 (ANTHROPIC_API_KEY) → Gemini → OpenAI → rule-based.
Caches per (ticker, scores, plan) for 12h. Throttles + handles quota exhaustion.
"""
import os, time, random, json, hashlib
from pathlib import Path
from datetime import datetime, timedelta, timezone

_CACHE_DIR = Path("data/llm_cache")
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_CACHE_TTL = timedelta(hours=12)

CLAUDE_MODEL = "claude-sonnet-4-5"


# ─── Cache ──────────────────────────────────────────────────────────────
def _cache_key(ticker, scores, plan):
    payload = json.dumps({"t": ticker, "s": scores, "p": plan}, sort_keys=True, default=str)
    return hashlib.md5(payload.encode()).hexdigest()


def _cache_get(key):
    p = _CACHE_DIR / f"{key}.json"
    if not p.exists():
        return None
    try:
        d = json.loads(p.read_text())
        cached_at = datetime.fromisoformat(d["at"])
        if cached_at.tzinfo is None:
            # Backward-compatible with older naive cache files.
            cached_at = cached_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - cached_at < _CACHE_TTL:
            return d["text"]
    except Exception:
        pass
    return None


def _cache_put(key, text):
    try:
        (_CACHE_DIR / f"{key}.json").write_text(
            json.dumps({"at": datetime.now(timezone.utc).isoformat(), "text": text})
        )
    except Exception:
        pass


# ─── State flags + throttle ─────────────────────────────────────────────
_CLAUDE_QUOTA_EXHAUSTED = [False]
_GEMINI_QUOTA_EXHAUSTED = [False]
_LAST_CALL = [0.0]
_MIN_INTERVAL = 1.5   # seconds between LLM calls (Claude tier-1: 50 RPM, ~1.2s safe)


def _throttle():
    elapsed = time.time() - _LAST_CALL[0]
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _LAST_CALL[0] = time.time()


# ─── Rule-based fallback ────────────────────────────────────────────────
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


# ─── Prompt ─────────────────────────────────────────────────────────────
def _build_prompt(ticker: str, scores: dict, plan: dict, news: list) -> str:
    headlines = "\n".join(f"- {n.get('title','')}" for n in (news or [])[:5]) or "None"
    sector = scores.get("sector_tag", "Unknown")
    trade_type = plan.get("trade_type", "swing").upper()
    rr = plan.get("risk_reward", "?")
    hold_rule = "intraday only — exit by 3:55 PM ET" if trade_type == "DAY" else "2-10 trading days"
    return f"""You are a senior US equity analyst writing a {trade_type} trade rationale for {ticker} (sector: {sector}).

SCORES (0-1 scale): {scores}
TRADE PLAN: entry ${plan.get('entry')}, stop ${plan.get('stop_loss')}, target ${plan.get('take_profit')}, R:R {rr}
HOLDING: {hold_rule}
TODAY'S HEADLINES:
{headlines}

Write 4-5 sentences:
1. The strongest setup factor (with numeric evidence).
2. Why this fits a {trade_type} trade specifically.
3. One concrete risk to watch.
4. The trigger to exit early (besides hitting stop).
5. End with: "Not financial advice."

Plain prose only. No bullets. No markdown. Under 120 words. Complete every sentence."""

def _claude(prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    resp = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=400,
        temperature=0.4,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.content[0].text.strip()


# ─── Provider: Gemini (kept as fallback) ────────────────────────────────
def _gemini(prompt: str, model: str) -> str:
    from google import genai
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    # Note: removed thinking_config (broke in newer SDK). Use simple call.
    try:
        from google.genai import types
        cfg = types.GenerateContentConfig(temperature=0.4, max_output_tokens=400)
        resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
    except Exception:
        # Older SDK fallback
        resp = client.models.generate_content(model=model, contents=prompt)
    return (resp.text or "").strip()


# ─── Provider: OpenAI (last resort) ─────────────────────────────────────
def _openai(prompt: str, model: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=model, temperature=0.4, max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content.strip()


# ─── Error classification ───────────────────────────────────────────────
def _is_quota_error(e: Exception) -> bool:
    msg = str(e).lower()
    return any(k in msg for k in ["resource_exhausted", "quota", "rate_limit",
                                   "429", "insufficient", "credit"])


# ─── Main entry ─────────────────────────────────────────────────────────
def _try_provider(name: str, fn, *args) -> tuple:
    """Return (text, err_str). Returns (None, msg) on failure."""
    try:
        _throttle()
        text = fn(*args)
        if text:
            return text, None
        return None, "empty response"
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:120]}"


def _explain_uncached(ticker: str, scores: dict, plan: dict,
                      news: list = None, model: str = "claude-sonnet-4-5") -> str:
    prompt = _build_prompt(ticker, scores, plan, news or [])

    # 1) Claude (primary)
    if not _CLAUDE_QUOTA_EXHAUSTED[0] and os.getenv("ANTHROPIC_API_KEY"):
        text, err = _try_provider("claude", _claude, prompt)
        if text:
            print(f"[llm] {ticker} ✓ Claude")
            return text
        print(f"[llm] {ticker} Claude failed ({err})")
        if err and _is_quota_error(Exception(err)):
            _CLAUDE_QUOTA_EXHAUSTED[0] = True
            print("[llm] ⚠️ Claude quota/credit exhausted — falling back to Gemini for rest of run")

    # 2) Gemini (fallback)
    if not _GEMINI_QUOTA_EXHAUSTED[0] and os.getenv("GEMINI_API_KEY"):
        gem_model = "gemini-2.5-flash-lite" if "gemini" not in model.lower() else model
        text, err = _try_provider("gemini", _gemini, prompt, gem_model)
        if text:
            print(f"[llm] {ticker} ✓ Gemini ({gem_model})")
            return text
        print(f"[llm] {ticker} Gemini failed ({err})")
        if err and _is_quota_error(Exception(err)):
            _GEMINI_QUOTA_EXHAUSTED[0] = True
            print("[llm] ⚠️ Gemini quota exhausted — using rule-based for rest of run")

    # 3) OpenAI (if configured)
    if os.getenv("OPENAI_API_KEY"):
        text, err = _try_provider("openai", _openai, prompt, "gpt-4o-mini")
        if text:
            print(f"[llm] {ticker} ✓ OpenAI")
            return text
        print(f"[llm] {ticker} OpenAI failed ({err})")

    # 4) Rule-based final fallback
    print(f"[llm] {ticker} → rule-based fallback")
    return _rule_based(ticker, scores, plan)


def explain_pick(ticker: str, scores: dict, plan: dict,
                 news: list = None, model: str = "claude-sonnet-4-5") -> str:
    key = _cache_key(ticker, scores, plan)
    cached = _cache_get(key)
    if cached:
        return cached
    text = _explain_uncached(ticker, scores, plan, news, model)
    _cache_put(key, text)
    return text
