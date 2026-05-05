"""Coverage for src.market_news without real Finnhub/LLM calls."""

import json
import os
import time

from src import market_news as mn


def test_cache_paths_include_current_hour(tmp_path, monkeypatch):
    monkeypatch.setattr(mn, "_CACHE_DIR", tmp_path)

    assert mn._cache_path("general").parent == tmp_path
    assert mn._cache_path("general").name.startswith("market_general_")
    assert mn._sentiment_cache_path().name.startswith("sentiment_")


def test_fetch_market_news_returns_empty_without_key(monkeypatch):
    monkeypatch.setattr(mn, "_KEY", "")

    called = {"requests": False}

    def fake_get(*args, **kwargs):
        called["requests"] = True
        raise AssertionError("should not call requests without key")

    monkeypatch.setattr(mn.requests, "get", fake_get)

    assert mn.fetch_market_news() == []
    assert called["requests"] is False


def test_fetch_market_news_uses_fresh_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(mn, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(mn, "_KEY", "token")

    cache = mn._cache_path("general")
    cache.write_text(json.dumps([
        {"headline": "newer", "datetime": 20},
        {"headline": "older", "datetime": 10},
    ]))

    assert mn.fetch_market_news(limit=1) == [{"headline": "newer", "datetime": 20}]


def test_fetch_market_news_fetches_sorts_and_caches(monkeypatch, tmp_path):
    monkeypatch.setattr(mn, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(mn, "_KEY", "token")

    class Response:
        status_code = 200

        def json(self):
            return [
                {"headline": "older", "datetime": 10},
                {"headline": "newer", "datetime": 20},
            ]

    calls = []

    def fake_get(url, params=None, timeout=15):
        calls.append((url, params, timeout))
        return Response()

    monkeypatch.setattr(mn.requests, "get", fake_get)

    result = mn.fetch_market_news(limit=2)

    assert [item["headline"] for item in result] == ["newer", "older"]
    assert calls[0][1] == {"category": "general", "token": "token"}
    assert json.loads(mn._cache_path("general").read_text())[0]["headline"] == "newer"


def test_fetch_market_news_handles_non_200_and_exception(monkeypatch, tmp_path):
    monkeypatch.setattr(mn, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(mn, "_KEY", "token")

    class Response:
        status_code = 500

        def json(self):
            raise AssertionError("should not parse non-200")

    monkeypatch.setattr(mn.requests, "get", lambda *a, **k: Response())
    assert mn.fetch_market_news() == []

    monkeypatch.setattr(mn.requests, "get", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    assert mn.fetch_market_news() == []


def test_build_sentiment_prompt_limits_to_30_headlines():
    headlines = [{"source": "SRC", "headline": f"headline {i}"} for i in range(35)]

    prompt = mn._build_sentiment_prompt(headlines)

    assert "Analyze these 30 top market headlines" in prompt
    assert "headline 0" in prompt
    assert "headline 29" in prompt
    assert "headline 30" not in prompt
    assert "STRICT JSON only" in prompt


def test_strip_markdown_fences_handles_json_and_plain_text():
    assert mn._strip_markdown_fences('```json\n{"sentiment":"bullish"}\n```') == '{"sentiment":"bullish"}'
    assert mn._strip_markdown_fences('{"sentiment":"neutral"}') == '{"sentiment":"neutral"}'


def test_gemini_sentiment_posts_expected_payload(monkeypatch):
    monkeypatch.setattr(mn, "_GEMINI_KEY", "gem-key")

    class Response:
        status_code = 200
        text = "ok"

        def json(self):
            return {
                "candidates": [
                    {"content": {"parts": [{"text": "  {\"sentiment\":\"neutral\"}  "}]}}
                ]
            }

    calls = []

    def fake_post(url, timeout=30, json=None):
        calls.append((url, timeout, json))
        return Response()

    monkeypatch.setattr(mn.requests, "post", fake_post)

    assert mn._gemini_sentiment("prompt", model="gemini-test") == '{"sentiment":"neutral"}'
    assert "gemini-test:generateContent?key=gem-key" in calls[0][0]
    assert calls[0][2]["contents"][0]["parts"][0]["text"] == "prompt"


def test_analyze_market_sentiment_returns_default_for_no_headlines():
    result = mn.analyze_market_sentiment([])

    assert result == {
        "sentiment": "neutral",
        "score": 0.5,
        "narratives": [],
        "key_risks": [],
        "key_catalysts": [],
        "summary": "Unable to analyze.",
    }


def test_analyze_market_sentiment_uses_fresh_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(mn, "_CACHE_DIR", tmp_path)
    cached = {
        "sentiment": "bullish",
        "score": 0.8,
        "narratives": ["AI"],
        "key_risks": [],
        "key_catalysts": [],
        "summary": "cached",
    }
    mn._sentiment_cache_path().write_text(json.dumps(cached))

    monkeypatch.setattr(mn, "_ANTHROPIC_KEY", "anthropic")
    monkeypatch.setattr(mn, "_claude_sentiment", lambda prompt: (_ for _ in ()).throw(AssertionError("cache should win")))

    assert mn.analyze_market_sentiment([{"headline": "x"}]) == cached


def test_analyze_market_sentiment_claude_success_caches_and_defaults_missing_keys(tmp_path, monkeypatch):
    monkeypatch.setattr(mn, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(mn, "_ANTHROPIC_KEY", "anthropic")
    monkeypatch.setattr(mn, "_GEMINI_KEY", "")

    monkeypatch.setattr(
        mn,
        "_claude_sentiment",
        lambda prompt: '```json\n{"sentiment":"bearish","score":0.2,"summary":"risk off"}\n```',
    )

    result = mn.analyze_market_sentiment([{"source": "SRC", "headline": "stocks fall"}])

    assert result["sentiment"] == "bearish"
    assert result["score"] == 0.2
    assert result["summary"] == "risk off"
    assert result["narratives"] == []
    assert json.loads(mn._sentiment_cache_path().read_text())["sentiment"] == "bearish"


def test_analyze_market_sentiment_gemini_fallback_after_claude_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(mn, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(mn, "_ANTHROPIC_KEY", "anthropic")
    monkeypatch.setattr(mn, "_GEMINI_KEY", "gemini")

    monkeypatch.setattr(mn, "_claude_sentiment", lambda prompt: (_ for _ in ()).throw(RuntimeError("claude down")))
    monkeypatch.setattr(
        mn,
        "_gemini_sentiment",
        lambda prompt: '{"sentiment":"bullish","score":0.9,"summary":"risk on","narratives":["Fed"],"key_risks":[],"key_catalysts":["cut"]}',
    )

    result = mn.analyze_market_sentiment([{"headline": "stocks rise"}])

    assert result["sentiment"] == "bullish"
    assert result["score"] == 0.9
    assert result["key_catalysts"] == ["cut"]


def test_analyze_market_sentiment_bad_json_returns_default(tmp_path, monkeypatch):
    monkeypatch.setattr(mn, "_CACHE_DIR", tmp_path)
    monkeypatch.setattr(mn, "_ANTHROPIC_KEY", "anthropic")
    monkeypatch.setattr(mn, "_GEMINI_KEY", "")

    monkeypatch.setattr(mn, "_claude_sentiment", lambda prompt: "not json")

    result = mn.analyze_market_sentiment([{"headline": "x"}])

    assert result["sentiment"] == "neutral"
    assert result["score"] == 0.5
    assert result["summary"] == "Unable to analyze."


def test_get_market_briefing_combines_headline_count_top_headlines_and_sentiment(monkeypatch):
    monkeypatch.setattr(
        mn,
        "fetch_market_news",
        lambda limit=40: [
            {"headline": "A" * 130},
            {"headline": "B"},
            {"headline": "C"},
            {"headline": "D"},
            {"headline": "E"},
            {"headline": "F"},
        ],
    )
    monkeypatch.setattr(
        mn,
        "analyze_market_sentiment",
        lambda headlines: {
            "sentiment": "neutral",
            "score": 0.5,
            "narratives": ["theme"],
            "key_risks": ["risk"],
            "key_catalysts": ["cat"],
            "summary": "summary",
        },
    )

    result = mn.get_market_briefing()

    assert result["headlines_count"] == 6
    assert len(result["top_headlines"]) == 5
    assert result["top_headlines"][0] == "A" * 120
    assert result["sentiment"] == "neutral"
    assert result["narratives"] == ["theme"]
