"""Claude (Sonnet 4.5) helper — drop-in replacement for gemini_helper.
Returns (text, err) tuple to match existing gemini_helper API.
Auto-falls back to Gemini if ANTHROPIC_API_KEY missing or API fails.
"""
import os, sys
from pathlib import Path

CLAUDE_MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 4000

def _try_claude(prompt: str, system: str = None):
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None, "ANTHROPIC_API_KEY missing"
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        kwargs = {
            "model": CLAUDE_MODEL,
            "max_tokens": MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        resp = client.messages.create(**kwargs)
        return resp.content[0].text, None
    except Exception as e:
        return None, f"Claude error: {e}"

def _try_gemini(prompt: str):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from gemini_helper import call_gemini as _g
        out = _g(prompt)
        # gemini_helper returns (text, err) tuple already
        if isinstance(out, tuple):
            return out
        return out, None
    except Exception as e:
        return None, f"Gemini error: {e}"

def call_llm(prompt: str, system: str = None):
    """Returns (text, err). text is None on failure."""
    text, err = _try_claude(prompt, system=system)
    if text is not None:
        print(f"[llm] used Claude ({CLAUDE_MODEL})")
        return text, None
    print(f"[llm] Claude unavailable ({err}) — using Gemini fallback")
    text2, err2 = _try_gemini(prompt)
    if text2 is not None:
        return text2, None
    return None, f"both LLMs failed: claude={err}, gemini={err2}"

# Backwards-compatible alias for any caller using call_gemini
call_gemini = call_llm
generate = call_llm

if __name__ == "__main__":
    text, err = call_llm("Say 'Claude online' in 5 words or less.")
    print(f"text={text!r}\nerr={err!r}")
