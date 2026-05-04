"""Finding #3: Yahoo RSS parser must not silently fail on iterator slicing."""
from unittest.mock import patch, MagicMock
from src.news_engine import fetch_yahoo_rss

FAKE_RSS = """<?xml version="1.0"?>
<rss><channel>
<item><title><![CDATA[NVDA hits new all-time high]]></title>
<link>https://example.com/1</link><pubDate>Mon, 04 May 2026 12:00:00 GMT</pubDate>
<description><![CDATA[Strong earnings push NVDA up 4%]]></description></item>
<item><title><![CDATA[Analyst raises NVDA target]]></title>
<link>https://example.com/2</link><pubDate>Mon, 04 May 2026 13:00:00 GMT</pubDate>
<description><![CDATA[Goldman raises target to $1500]]></description></item>
<item><title><![CDATA[NVDA partners with Microsoft]]></title>
<link>https://example.com/3</link><pubDate>Mon, 04 May 2026 14:00:00 GMT</pubDate>
<description><![CDATA[New AI deal]]></description></item>
<item><title><![CDATA[Fourth — should be IGNORED]]></title>
<link>https://example.com/4</link><pubDate>Mon, 04 May 2026 15:00:00 GMT</pubDate>
<description><![CDATA[ignored]]></description></item>
</channel></rss>"""


def test_yahoo_rss_returns_items_not_typeerror():
    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.text = FAKE_RSS
    with patch("src.news_engine.requests.get", return_value=fake_resp), \
         patch("src.news_engine.time.sleep"):
        items = fetch_yahoo_rss(["NVDA"])
    assert len(items) == 3
    assert all(it["source"] == "yahoo" for it in items)
    assert items[0]["headline"] == "NVDA hits new all-time high"
    assert items[0]["ticker_list"] == ["NVDA"]
    assert "1500" in items[1]["summary"]


def test_yahoo_rss_handles_no_items():
    fake_resp = MagicMock()
    fake_resp.status_code = 200
    fake_resp.text = "<rss><channel></channel></rss>"
    with patch("src.news_engine.requests.get", return_value=fake_resp), \
         patch("src.news_engine.time.sleep"):
        items = fetch_yahoo_rss(["NVDA"])
    assert items == []
