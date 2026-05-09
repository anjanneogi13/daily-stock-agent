import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.generate_late_daily_ideas import (
    build_late_ideas,
    compute_display_score,
    detect_risk_flags,
    format_markdown,
    late_ideas_markdown_path,
    late_ideas_path,
    write_outputs,
)


ET = ZoneInfo("America/New_York")


def test_late_ideas_paths_are_date_scoped(tmp_path):
    assert late_ideas_path("2026-05-06", data_dir=tmp_path) == tmp_path / "late_daily_ideas_2026-05-06.jsonl"
    assert late_ideas_markdown_path("2026-05-06", data_dir=tmp_path) == tmp_path / "late_daily_ideas_2026-05-06.md"


def test_build_late_ideas_uses_news_and_watchlist_without_official_picks(tmp_path):
    news = tmp_path / "news_signals.json"
    watch = tmp_path / "watchlist.json"

    news.write_text(json.dumps({
        "ALAB": {
            "ticker": "ALAB",
            "tradeable_score": 0.48,
            "score_delta": 0.034,
            "sentiment": "bullish",
            "action_window": "intraday",
            "headline": "RBC raises price target",
            "company_name": "Astera Labs",
        },
        "BAD": {
            "ticker": "A",
            "tradeable_score": 1.0,
            "sentiment": "bullish",
            "action_window": "intraday",
            "headline": "h",
        },
        "IGN": {
            "ticker": "IGN",
            "tradeable_score": 0.80,
            "sentiment": "bullish",
            "action_window": "ignore",
            "headline": "Should be ignored",
        },
        "BEAR": {
            "ticker": "BEAR",
            "tradeable_score": 0.80,
            "sentiment": "bearish",
            "headline": "No short architecture yet",
        },
    }))

    watch.write_text(json.dumps({
        "items": [
            {
                "ticker": "ERNA",
                "tradeable_score": 0.75,
                "sentiment": "bullish",
                "action_window": "intraday",
                "headline": "Breakthrough preclinical data",
                "company_name": "Ernexa Therapeutics",
            }
        ]
    }))

    ideas = build_late_ideas(
        news_signals_path=news,
        watchlist_path=watch,
        now=datetime(2026, 5, 6, 11, 30, tzinfo=ET),
        max_results=5,
    )

    tickers = [i["ticker"] for i in ideas]
    assert tickers == ["ERNA", "ALAB"]
    assert all(i["watch_only"] is True for i in ideas)
    assert all(i["official_premarket_pick"] is False for i in ideas)
    assert all(i["paper_trading_enabled"] is False for i in ideas)
    assert all(i["live_trading_enabled"] is False for i in ideas)


def test_write_outputs_writes_jsonl_and_markdown(tmp_path):
    ideas = [{
        "date": "2026-05-06",
        "generated_at_et": "2026-05-06T11:30:00-04:00",
        "idea_type": "late_daily_watch_only",
        "mode": "monitoring_only",
        "watch_only": True,
        "official_premarket_pick": False,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "ticker": "ERNA",
        "company_name": "Ernexa Therapeutics",
        "source": "watchlist",
        "score": 75.0,
        "tradeable_score": 0.75,
        "score_delta": 0,
        "score_explanation": "base=75.0 from tradeable_score=0.750; positive_score_delta_boost=0.0; raw=75.0; cap=95.0 (standard late-news cap prevents news-only 100/100 display); display_score=75.0",
        "risk_flags": ["news_only_no_breadth_confirmation"],
        "sentiment": "bullish",
        "action_window": "intraday",
        "headline": "Breakthrough data",
        "reason": "Breakthrough data",
        "url": "",
        "current_price": 10.0,
        "watch_buy_price": 10.0,
        "watch_stop_loss": 9.85,
        "watch_take_profit": 10.3,
        "risk_reward": 2.0,
        "warning": "Monitoring-only.",
    }]

    jsonl, md = write_outputs(ideas, data_dir=tmp_path, now=datetime(2026, 5, 6, 11, 30, tzinfo=ET))

    rows = [json.loads(line) for line in jsonl.read_text().splitlines()]
    assert rows[0]["ticker"] == "ERNA"
    body = md.read_text()
    assert "PREMARKET WINDOW MISSED — LATE WATCH-ONLY DAILY IDEAS" in body
    assert "Official daily picks were NOT sent" in body
    assert "not official premarket picks" in body
    assert "ERNA — Ernexa Therapeutics" in body
    assert "Score note:" in body
    assert "Risk flags:" in body
    assert "news_only_no_breadth_confirmation" in body
    assert "Watch-only reference level: $10.00" in body
    assert "BUY/Entry" not in body
    assert "Watch-only SL: $9.85" in body
    assert "Watch-only TP: $10.30" in body
    assert "WATCH ONLY" in body


def test_format_markdown_no_ideas_is_still_safe():
    msg = format_markdown([], now=datetime(2026, 5, 6, 11, 30, tzinfo=ET))

    assert "PREMARKET WINDOW MISSED — LATE WATCH-ONLY DAILY IDEAS" in msg
    assert "No qualified late watch-only ideas" in msg
    assert "Not buy instructions" in msg


def test_format_markdown_without_quote_warns_levels_unavailable():
    msg = format_markdown([{
        "ticker": "ALAB",
        "score": 48.0,
        "source": "news_signal",
        "action_window": "intraday",
        "headline": "RBC raises price target",
        "watch_only": True,
        "official_premarket_pick": False,
    }], now=datetime(2026, 5, 6, 11, 30, tzinfo=ET))

    assert "Source: news-signal" in msg
    assert "Price levels: unavailable" in msg
    assert "WATCH ONLY" in msg


def test_build_late_ideas_suppresses_unresolved_no_quote_identity(tmp_path):
    news = tmp_path / "news_signals.json"
    watch = tmp_path / "watchlist.json"
    watch.write_text(json.dumps({"items": []}))

    news.write_text(json.dumps({
        "X": {
            "ticker": "X",
            "tradeable_score": 0.95,
            "sentiment": "bullish",
            "headline": "TMX Group Q1 Adj. EPS beats estimates",
        }
    }))

    ideas = build_late_ideas(
        news_signals_path=news,
        watchlist_path=watch,
        now=datetime(2026, 5, 7, 11, 30, tzinfo=ET),
        max_results=5,
    )

    assert ideas == []


def test_build_late_ideas_skips_acquisition_event_arbitrage(tmp_path):
    news = tmp_path / "news_signals.json"
    watch = tmp_path / "watchlist.json"
    watch.write_text(json.dumps({"items": []}))

    news.write_text(json.dumps({
        "CCRN": {
            "ticker": "CCRN",
            "company_name": "Cross Country Healthcare, Inc.",
            "tradeable_score": 1.0,
            "sentiment": "bullish",
            "headline": "Knox Lane to acquire all outstanding shares for $13.25/shr in all-cash transaction",
        }
    }))

    ideas = build_late_ideas(
        news_signals_path=news,
        watchlist_path=watch,
        now=datetime(2026, 5, 7, 11, 30, tzinfo=ET),
        max_results=5,
    )

    assert ideas == []

def test_late_news_display_score_is_capped_below_100_for_standard_news():
    risk_flags = ["news_only_no_breadth_confirmation"]
    score, explanation = compute_display_score(
        tradeable_score=0.95,
        score_delta=0.10,
        risk_flags=risk_flags,
    )

    assert score == 95.0
    assert "raw=100.0" in explanation
    assert "cap=95.0" in explanation
    assert "display_score=95.0" in explanation


def test_gig_style_business_combination_gets_risk_flags_and_score_cap(tmp_path):
    news = tmp_path / "news_signals.json"
    watch = tmp_path / "watchlist.json"
    watch.write_text(json.dumps({"items": []}))

    headline = (
        "GigCapital7 Shareholders Approve Proposed Business Combination Between "
        "GigCapital7, Hadron Energy And MMR Merger Sub, As Well As All Other "
        "Proposals Related To Business Combination"
    )
    news.write_text(json.dumps({
        "GIG": {
            "ticker": "GIG",
            "company_name": "GigCapital7",
            "tradeable_score": 0.88,
            "score_delta": 0.20,
            "sentiment": "bullish",
            "action_window": "intraday",
            "headline": headline,
        }
    }))

    ideas = build_late_ideas(
        news_signals_path=news,
        watchlist_path=watch,
        now=datetime(2026, 5, 8, 11, 30, tzinfo=ET),
        max_results=5,
    )

    assert len(ideas) == 1
    idea = ideas[0]
    assert idea["ticker"] == "GIG"
    assert idea["score"] == 75.0
    assert idea["catalyst_type"] == "corporate_action_event_structure_uncertain"
    assert "business_combination" in idea["risk_flags"]
    assert "merger_sub" in idea["risk_flags"]
    assert "deal_vote" in idea["risk_flags"]
    assert "event_structure_uncertain" in idea["risk_flags"]
    assert "no_event_arb_model" in idea["risk_flags"]
    assert "news_only_no_breadth_confirmation" in idea["risk_flags"]
    assert "cap=75.0" in idea["score_explanation"]


def test_detect_risk_flags_for_takeover_bid_and_news_only():
    flags = detect_risk_flags(
        "Israeli $4.5 Billion Takeover Bid Beats Hapag-Lloyd's",
        source="news_signal",
    )

    assert "corporate_action" in flags
    assert "event_structure_uncertain" in flags
    assert "no_event_arb_model" in flags
    assert "news_only_no_breadth_confirmation" in flags
