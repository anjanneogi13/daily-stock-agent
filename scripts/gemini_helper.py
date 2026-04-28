"""Gemini API wrapper with retry, backoff, and model fallback."""
import os, time

def call_gemini(prompt, primary_model="gemini-2.0-flash", fallback_models=None, max_retries=3):
    """Returns (text, error_str). text is None on failure."""
    if fallback_models is None:
        fallback_models = ["gemini-2.0-flash-lite", "gemini-1.5-flash"]
    
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return None, "GEMINI_API_KEY missing"
    
    try:
        from google import genai
    except ImportError:
        return None, "google-genai not installed"
    
    client = genai.Client(api_key=key)
    models_to_try = [primary_model] + fallback_models
    last_err = None
    
    for model in models_to_try:
        for attempt in range(max_retries):
            try:
                resp = client.models.generate_content(model=model, contents=prompt)
                return resp.text, None
            except Exception as e:
                err_str = str(e)
                last_err = f"{model} attempt {attempt+1}: {err_str[:200]}"
                # Quota exhausted? Try fallback model immediately, no retry
                if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                    if "PerDay" in err_str:
                        print(f"[gemini] Daily quota hit on {model}, trying next model")
                        break  # try next model
                    # Per-minute quota: wait and retry
                    wait = 30 * (attempt + 1)
                    print(f"[gemini] Rate limited on {model}, sleeping {wait}s")
                    time.sleep(wait)
                else:
                    # Other error, try next model
                    break
    return None, last_err
