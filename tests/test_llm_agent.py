"""Coverage for src.llm_agent without real provider calls."""

import json
import os
import time
from datetime import datetime, timedelta, timezone

from src import llm_agent as llm


BASE_SCORES = {
    "composite": 0.82,
    "momentum": 0.91,
    "quality": 0.73,
    "sentiment": 0.67,
    "sector_tag": "SEMI",
}
BASE_PLAN = {
    "entry": 100,
    "stop_loss": 95,
    "take_profit": 112,
    "risk_reward": 2.4,
    "trade_type": "swing",
}


def _clear_env(monkeypatch):
    for key in ["ANTHROPIC_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY"]:
        monkeypatch.delenv(key, raising=False)


def test_cache_key_is_stable_for_equivalent_payloads():
    key1 = llm._cache_key("AAPL", {"b": 2, "a": 1}, {"entry": 100})
    key2 = llm._cache_key("AAPL", {"a": 1, "b": 2}, {"entry": 100})

    assert key1 == key2
    assert len(key1) == 32


def test_cache_put_and_get_roundtrip_uses_timezone_aware_timestamp(tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "_CACHE_DIR", tmp_path)

    llm._cache_put("abc", "cached text")

    cache_file = tmp_path / "abc.json"
    payload = json.loads(cache_file.read_text())
    assert payload["text"] == "cached text"
    assert datetime.fromisoformat(payload["at"]).tzinfo is not None
    assert llm._cache_get("abc") == "cached text"


def test_cache_get_handles_legacy_naive_timestamp(tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "_CACHE_DIR", tmp_path)
    (tmp_path / "legacy.json").write_text(
        json.dumps({"at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(), "text": "legacy text"})
    )

    assert llm._cache_get("legacy") == "legacy text"


def test_cache_get_ignores_stale_corrupt_and_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "_CACHE_DIR", tmp_path)

    stale_at = datetime.now(timezone.utc) - llm._CACHE_TTL - timedelta(minutes=1)
    (tmp_path / "stale.json").write_text(json.dumps({"at": stale_at.isoformat(), "text": "old"}))
    (tmp_path / "bad.json").write_text("{not-json")

    assert llm._cache_get("missing") is None
    assert llm._cache_get("stale") is None
    assert llm._cache_get("bad") is None


def test_rule_based_lists_top_numeric_factors_and_plan():
    text = llm._rule_based(
        "NVDA",
        {
            "composite": 0.8,
            "raw_composite": 99,
            "sector_mult": 3,
            "sector_tag": "SEMI",
            "momentum": 0.9,
            "quality": 0.7,
            "sentiment": 0.6,
            "label": "ignore",
        },
        BASE_PLAN,
    )

    assert "NVDA composite score 0.80" in text
    assert "momentum=0.90, quality=0.70, sentiment=0.60" in text
    assert "entry $100" in text
    assert "No certainty implied" in text
    assert "raw_composite" not in text


def test_build_prompt_day_trade_limits_headlines_and_exit_rule():
    news = [{"title": f"headline {i}"} for i in range(7)]
    plan = {**BASE_PLAN, "trade_type": "day"}

    prompt = llm._build_prompt("TSLA", BASE_SCORES, plan, news)

    assert "DAY trade rationale for TSLA" in prompt
    assert "intraday only — exit by 3:55 PM ET" in prompt
    assert "headline 0" in prompt
    assert "headline 4" in prompt
    assert "headline 5" not in prompt
    assert "Not financial advice." in prompt


def test_build_prompt_swing_without_news_uses_none():
    prompt = llm._build_prompt("MSFT", BASE_SCORES, BASE_PLAN, [])

    assert "SWING trade rationale for MSFT" in prompt
    assert "2-10 trading days" in prompt
    assert "TODAY'S HEADLINES:\nNone" in prompt


def test_is_quota_error_matches_common_provider_messages():
    for message in ["RESOURCE_EXHAUSTED", "quota exceeded", "rate_limit", "HTTP 429", "insufficient credit"]:
        assert llm._is_quota_error(Exception(message)) is True

    assert llm._is_quota_error(Exception("temporary network error")) is False


def test_try_provider_returns_text_empty_or_error(monkeypatch):
    monkeypatch.setattr(llm, "_throttle", lambda: None)

    assert llm._try_provider("ok", lambda: "text") == ("text", None)
    assert llm._try_provider("empty", lambda: "") == (None, "empty response")

    text, err = llm._try_provider("boom", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert text is None
    assert err.startswith("RuntimeError: boom")


def test_explain_uncached_uses_claude_when_configured(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic")
    monkeypatch.setattr(llm, "_CLAUDE_QUOTA_EXHAUSTED", [False])
    monkeypatch.setattr(llm, "_GEMINI_QUOTA_EXHAUSTED", [False])
    monkeypatch.setattr(llm, "_try_provider", lambda name, fn, *args: ("claude text", None))

    assert llm._explain_uncached("AAPL", BASE_SCORES, BASE_PLAN) == "claude text"


def test_explain_uncached_sets_claude_quota_and_falls_back_to_gemini(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini")
    monkeypatch.setattr(llm, "_CLAUDE_QUOTA_EXHAUSTED", [False])
    monkeypatch.setattr(llm, "_GEMINI_QUOTA_EXHAUSTED", [False])

    calls = []

    def fake_try_provider(name, fn, *args):
        calls.append((name, args))
        if name == "claude":
            return None, "RuntimeError: quota exceeded"
        return "gemini text", None

    monkeypatch.setattr(llm, "_try_provider", fake_try_provider)

    assert llm._explain_uncached("AAPL", BASE_SCORES, BASE_PLAN, model="claude-sonnet-4-5") == "gemini text"
    assert llm._CLAUDE_QUOTA_EXHAUSTED[0] is True
    assert calls[0][0] == "claude"
    assert calls[1][0] == "gemini"
    assert calls[1][1][-1] == "gemini-2.5-flash-lite"


def test_explain_uncached_uses_openai_after_gemini_failure(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini")
    monkeypatch.setenv("OPENAI_API_KEY", "openai")
    monkeypatch.setattr(llm, "_CLAUDE_QUOTA_EXHAUSTED", [False])
    monkeypatch.setattr(llm, "_GEMINI_QUOTA_EXHAUSTED", [False])

    calls = []

    def fake_try_provider(name, fn, *args):
        calls.append(name)
        if name == "gemini":
            return None, "empty response"
        return "openai text", None

    monkeypatch.setattr(llm, "_try_provider", fake_try_provider)

    assert llm._explain_uncached("AAPL", BASE_SCORES, BASE_PLAN, model="gemini-custom") == "openai text"
    assert calls == ["gemini", "openai"]


def test_explain_uncached_rule_based_when_no_provider_keys(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setattr(llm, "_CLAUDE_QUOTA_EXHAUSTED", [False])
    monkeypatch.setattr(llm, "_GEMINI_QUOTA_EXHAUSTED", [False])
    monkeypatch.setattr(llm, "_try_provider", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no provider expected")))

    text = llm._explain_uncached("AAPL", BASE_SCORES, BASE_PLAN)

    assert text.startswith("AAPL composite score")
    assert "rule-based" not in text.lower()


def test_explain_pick_uses_cache_and_writes_uncached_result(tmp_path, monkeypatch):
    monkeypatch.setattr(llm, "_CACHE_DIR", tmp_path)

    key = llm._cache_key("AAPL", BASE_SCORES, BASE_PLAN)
    (tmp_path / f"{key}.json").write_text(
        json.dumps({"at": datetime.now(timezone.utc).isoformat(), "text": "cached rationale"})
    )

    monkeypatch.setattr(
        llm,
        "_explain_uncached",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("cache should win")),
    )
    assert llm.explain_pick("AAPL", BASE_SCORES, BASE_PLAN) == "cached rationale"

    monkeypatch.setattr(llm, "_explain_uncached", lambda *a, **k: "fresh rationale")
    assert llm.explain_pick("MSFT", BASE_SCORES, BASE_PLAN) == "fresh rationale"
    msft_key = llm._cache_key("MSFT", BASE_SCORES, BASE_PLAN)
    assert json.loads((tmp_path / f"{msft_key}.json").read_text())["text"] == "fresh rationale"
