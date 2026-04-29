"""Claude (Sonnet 4.5) helper — drop-in replacement for gemini_helper.
Auto-falls back to Gemini if ANTHROPIC_API_KEY missing or API fails.
"""
import os, sys
from pathlib import Path

CLAUDE_MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 4000

def _try_claude(prompt: str, system: str = None) -> str | None:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None
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
        return resp.content[0].text
    except Exception as e:
        print(f"[claude] error: {e} — falling back to Gemini", file=sys.stderr)
        return None

def _try_gemini(prompt: str) -> str:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from gemini_helper import call_gemini
        return call_gemini(prompt)
    except Exception as e:
        return f"[ERROR: both Claude and Gemini failed: {e}]"

def call_llm(prompt: str, system: str = None) -> str:
    out = _try_claude(prompt, system=system)
    if out is not None:
        print(f"[llm] used Claude ({CLAUDE_MODEL})")
        return out
    print("[llm] using Gemini fallback")
    return _try_gemini(prompt)

# Backwards-compatible aliases
call_gemini = call_llm
generate = call_llm

if __name__ == "__main__":
    print(call_llm("Say 'Claude online' in 5 words or less."))
