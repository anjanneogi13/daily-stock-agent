import csv
import json
from pathlib import Path

from scripts.discover_themes import (
    build_theme_discovery,
    extract_theme_terms,
    format_markdown,
    write_outputs,
)


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj))


def write_picks(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({k for row in rows for k in row})
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_extract_theme_terms_derives_terms_from_evidence_not_fixed_answer():
    terms = extract_theme_terms({
        "ticker": "ADBE",
        "category": "product_launch",
        "headline": "Adobe launches productivity agent for generative AI images and text",
        "rationale": "Creative cloud model innovation and content workflow automation",
    })

    assert "ai" in terms
    assert "agent" in terms
    assert "generative ai" in terms or "ai images" in terms
    assert "product launch" in terms or "product" in terms


def test_theme_discovery_outputs_observe_only_artifact(tmp_path):
    write_json(tmp_path / "watchlist.json", {
        "items": [
            {
                "ticker": "ADBE",
                "company_name": "Adobe",
                "category": "product_launch",
                "headline": "Adobe launches productivity agent for generative AI images and text",
                "rationale": "Generative AI creative cloud workflow automation",
                "sentiment": "bullish",
                "tradeable_score": 0.68,
            },
            {
                "ticker": "MSFT",
                "company_name": "Microsoft",
                "category": "product_launch",
                "headline": "Microsoft expands AI agent tools for cloud productivity",
                "rationale": "AI agent demand supports cloud productivity workflow",
                "sentiment": "bullish",
                "tradeable_score": 0.82,
            },
            {
                "ticker": "NVDA",
                "company_name": "NVIDIA",
                "category": "earnings_beat",
                "headline": "NVIDIA data center AI chip demand beats expectations",
                "rationale": "Accelerator demand remains strong",
                "sentiment": "bullish",
                "tradeable_score": 0.9,
            },
        ]
    })

    write_json(tmp_path / "news_signals.json", {
        "AMD": {
            "ticker": "AMD",
            "headline": "AMD AI accelerator demand rises after analyst upgrade",
            "sentiment": "bullish",
            "tradeable_score": 0.74,
            "score_delta": 0.05,
        }
    })

    write_picks(tmp_path / "picks_log.csv", [
        {
            "pick_date": "2026-05-08",
            "ticker": "SMCI",
            "company": "Super Micro Computer",
            "tag": "AI infrastructure",
            "evaluation_status": "tp_hit",
            "actual_return_pct": "4.2",
            "watch_only": "false",
        }
    ])

    report = build_theme_discovery(date_str="2026-05-09", data_dir=tmp_path, min_evidence=2)

    assert report["artifact"] == "theme_discovery"
    assert report["observe_only"] is True
    assert report["official_score_boost_enabled"] is False
    assert report["production_scoring_effect"] is False
    assert report["paper_trading_enabled"] is False
    assert report["live_trading_enabled"] is False
    assert report["buy_instructions_enabled"] is False
    assert report["theme_count"] > 0

    theme_names = {t["theme"] for t in report["themes"]}
    assert "ai" in theme_names

    ai_theme = next(t for t in report["themes"] if t["theme"] == "ai")
    assert ai_theme["breadth"] >= 4
    assert ai_theme["lifecycle_state"] in {
        "emerging_theme",
        "confirmed_leadership",
        "crowded_momentum",
    }
    assert "observe_only_theme" in ai_theme["risk_flags"]
    assert "price_relative_strength_unavailable_v0" in ai_theme["risk_flags"]


def test_theme_discovery_marks_news_hype_unconfirmed_for_low_breadth(tmp_path):
    write_json(tmp_path / "watchlist.json", {
        "items": [
            {
                "ticker": "ONE",
                "headline": "One company mentions quantum battery platform",
                "rationale": "Quantum battery platform receives attention",
                "sentiment": "bullish",
                "tradeable_score": 0.9,
            },
            {
                "ticker": "ONE",
                "headline": "One company expands quantum battery platform",
                "rationale": "Quantum battery platform expands",
                "sentiment": "bullish",
                "tradeable_score": 0.88,
            },
        ]
    })
    write_json(tmp_path / "news_signals.json", {})
    write_picks(tmp_path / "picks_log.csv", [])

    report = build_theme_discovery(date_str="2026-05-09", data_dir=tmp_path, min_evidence=2)

    quantum = next(t for t in report["themes"] if t["theme"] == "quantum")
    assert quantum["breadth"] == 1
    assert quantum["lifecycle_state"] == "news_hype_unconfirmed"
    assert "low_breadth" in quantum["risk_flags"]


def test_theme_discovery_writes_json_and_markdown(tmp_path):
    write_json(tmp_path / "watchlist.json", {
        "items": [
            {
                "ticker": "A",
                "headline": "Cloud security demand rises",
                "rationale": "Cloud security demand rises",
                "sentiment": "bullish",
                "tradeable_score": 0.7,
            },
            {
                "ticker": "B",
                "headline": "Cloud security vendor raises guidance",
                "rationale": "Cloud security vendor raises guidance",
                "sentiment": "bullish",
                "tradeable_score": 0.75,
            },
        ]
    })
    write_json(tmp_path / "news_signals.json", {})
    write_picks(tmp_path / "picks_log.csv", [])

    report = build_theme_discovery(date_str="2026-05-09", data_dir=tmp_path, min_evidence=2)
    json_path, md_path = write_outputs(report, data_dir=tmp_path)

    assert json_path.name == "theme_discovery_2026-05-09.json"
    assert md_path.name == "theme_discovery_2026-05-09.md"

    saved = json.loads(json_path.read_text())
    assert saved["observe_only"] is True

    body = md_path.read_text()
    assert "Dynamic Theme Discovery Radar" in body
    assert "Observe-only" in body
    assert "Does not change official scoring" in body
    assert "cloud" in body

def test_theme_discovery_reports_missing_market_evidence_not_guessed(tmp_path):
    write_json(tmp_path / "watchlist.json", {
        "items": [
            {
                "ticker": "A",
                "headline": "Cloud security demand rises",
                "rationale": "Cloud security demand rises",
                "sentiment": "bullish",
                "tradeable_score": 0.7,
            },
            {
                "ticker": "B",
                "headline": "Cloud security vendor raises guidance",
                "rationale": "Cloud security vendor raises guidance",
                "sentiment": "bullish",
                "tradeable_score": 0.75,
            },
        ]
    })
    write_json(tmp_path / "news_signals.json", {})
    write_picks(tmp_path / "picks_log.csv", [])

    report = build_theme_discovery(date_str="2026-05-09", data_dir=tmp_path, min_evidence=2)
    cloud = next(t for t in report["themes"] if t["theme"] == "cloud")

    assert cloud["market_evidence"]["market_evidence_status"] == "unavailable_missing_market_evidence_fields"
    assert cloud["market_evidence"]["market_quality_score_adjustment"] == 0.0
    assert cloud["market_evidence"]["one_day_return_pct"] is None
    assert "price_relative_strength_unavailable_v0" in cloud["risk_flags"]


def test_theme_discovery_uses_existing_market_evidence_fields_observe_only(tmp_path):
    base_items = [
        {
            "ticker": "A",
            "headline": "Cloud security demand rises",
            "rationale": "Cloud security demand rises",
            "sentiment": "bullish",
            "tradeable_score": 0.7,
        },
        {
            "ticker": "B",
            "headline": "Cloud security vendor raises guidance",
            "rationale": "Cloud security vendor raises guidance",
            "sentiment": "bullish",
            "tradeable_score": 0.75,
        },
    ]

    write_json(tmp_path / "watchlist.json", {"items": base_items})
    write_json(tmp_path / "news_signals.json", {})
    write_picks(tmp_path / "picks_log.csv", [])
    baseline = build_theme_discovery(date_str="2026-05-09", data_dir=tmp_path, min_evidence=2)
    baseline_cloud = next(t for t in baseline["themes"] if t["theme"] == "cloud")

    enriched_items = [
        {
            **base_items[0],
            "return_1d_pct": 2.0,
            "return_5d_pct": 5.0,
            "return_20d_pct": 11.0,
            "relative_strength_vs_spy_pct": 3.5,
            "breakout": True,
            "new_high": True,
        },
        {
            **base_items[1],
            "return_1d_pct": 1.0,
            "return_5d_pct": 4.0,
            "return_20d_pct": 8.0,
            "relative_strength_vs_spy_pct": 2.5,
            "breakout": True,
        },
    ]
    write_json(tmp_path / "watchlist.json", {"items": enriched_items})

    enriched = build_theme_discovery(date_str="2026-05-09", data_dir=tmp_path, min_evidence=2)
    cloud = next(t for t in enriched["themes"] if t["theme"] == "cloud")

    assert enriched["production_scoring_effect"] is False
    assert cloud["market_evidence"]["market_evidence_status"] == "available_from_existing_evidence_fields"
    assert cloud["market_evidence"]["tickers_with_return_evidence"] == 2
    assert cloud["market_evidence"]["one_day_return_pct"] == 1.5
    assert cloud["market_evidence"]["five_day_return_pct"] == 4.5
    assert cloud["market_evidence"]["twenty_day_return_pct"] == 9.5
    assert cloud["market_evidence"]["relative_strength_vs_spy_pct"] == 3.0
    assert cloud["market_evidence"]["breakout_count"] == 2
    assert cloud["market_evidence"]["new_high_count"] == 1
    assert cloud["market_evidence"]["market_quality_score_adjustment"] > 0
    assert cloud["theme_score"] > baseline_cloud["theme_score"]
    assert "market_evidence_available" in cloud["risk_flags"]
    assert "price_relative_strength_unavailable_v0" not in cloud["risk_flags"]


def test_theme_discovery_provider_evidence_uses_readiness_and_market_health(tmp_path):
    write_json(tmp_path / "watchlist.json", {
        "items": [
            {
                "ticker": "A",
                "headline": "AI chip breakout",
                "rationale": "AI chip breakout",
                "sentiment": "bullish",
                "tradeable_score": 0.8,
                "return_1d_pct": 2.0,
            },
            {
                "ticker": "B",
                "headline": "AI chip new high",
                "rationale": "AI chip new high",
                "sentiment": "bullish",
                "tradeable_score": 0.85,
                "return_1d_pct": 3.0,
            },
        ]
    })
    write_json(tmp_path / "news_signals.json", {})
    write_picks(tmp_path / "picks_log.csv", [])
    write_json(tmp_path / "data_readiness_2026-05-09.json", {
        "data_provider_status": "provider_or_market_data_failure_evidence_detected",
        "official_pick_readiness_status": "not_ready_data_provider_failure",
    })
    write_json(tmp_path / "market_data_health_2026-05-09.json", {
        "providers": {
            "yfinance": {
                "failure_types": {
                    "rate_limited": 2,
                    "missing_history": 1,
                }
            }
        }
    })

    report = build_theme_discovery(date_str="2026-05-09", data_dir=tmp_path, min_evidence=2)
    ai = next(t for t in report["themes"] if t["theme"] == "ai")

    provider = ai["market_evidence"]["provider_evidence"]
    assert provider["data_readiness_available"] is True
    assert provider["market_data_health_available"] is True
    assert provider["data_provider_status"] == "provider_or_market_data_failure_evidence_detected"
    assert provider["failure_type_totals"]["rate_limited"] == 2
    assert provider["failure_type_totals"]["missing_history"] == 1
