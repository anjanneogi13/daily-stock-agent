import csv
import json
from pathlib import Path

from scripts.build_theme_pick_bridge import (
    build_theme_pick_bridge,
    format_markdown,
    write_outputs,
)


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj))


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = sorted({k for row in rows for k in row})
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_theme_pick_bridge_compares_official_rejected_and_watch_only(tmp_path):
    write_json(tmp_path / "theme_discovery_2026-05-09.json", {
        "artifact": "theme_discovery",
        "themes": [
            {
                "theme": "ai",
                "theme_id": "ai",
                "lifecycle_state": "emerging_theme",
                "theme_score": 99.0,
                "tickers": ["NVDA", "MSFT", "ADBE", "TSM", "ARM"],
            }
        ],
    })
    write_csv(tmp_path / "picks_log.csv", [
        {
            "pick_date": "2026-05-09",
            "ticker": "NVDA",
            "company": "NVIDIA",
            "tag": "SEMI / AI",
            "evaluation_status": "pending",
            "watch_only": "",
        }
    ])
    write_json(tmp_path / "daily_picks_candidate_rejections_2026-05-09.json", {
        "diagnostics": {
            "rejected_candidates": [
                {
                    "candidate": {
                        "ticker": "MSFT",
                        "company": "Microsoft",
                        "scores": {"composite": 0.71, "sector_tag": "AI"},
                    },
                    "reason": "filtered: overextended",
                }
            ],
            "hard_blocked_candidates": [
                {
                    "candidate": {
                        "ticker": "ARM",
                        "company": "Arm",
                        "scores": {"composite": 0.68, "sector_tag": "SEMI / AI"},
                    },
                    "block_reason": "weak sector block",
                }
            ],
        }
    })
    write_jsonl(tmp_path / "late_daily_ideas_2026-05-09.jsonl", [
        {
            "ticker": "ADBE",
            "watch_only": True,
            "score": 95,
            "reason": "late AI product news",
        }
    ])

    report = build_theme_pick_bridge(date_str="2026-05-09", data_dir=tmp_path)

    assert report["artifact"] == "theme_pick_bridge"
    assert report["observe_only"] is True
    assert report["official_score_boost_enabled"] is False
    assert report["production_scoring_effect"] is False
    assert report["paper_trading_enabled"] is False
    assert report["live_trading_enabled"] is False
    assert report["buy_instructions_enabled"] is False

    ai = report["themes"][0]
    assert ai["official_pick_match_count"] == 1
    assert ai["official_pick_matches"][0]["ticker"] == "NVDA"
    assert ai["rejected_match_count"] == 1
    assert ai["rejected_matches"][0]["ticker"] == "MSFT"
    assert ai["hard_blocked_match_count"] == 1
    assert ai["hard_blocked_matches"][0]["ticker"] == "ARM"
    assert ai["watch_only_match_count"] == 1
    assert ai["watch_only_matches"][0]["ticker"] == "ADBE"
    assert ai["missing_from_official_and_watch_only"] == ["TSM"]
    assert "official_pick_included" in ai["likely_gap_reasons"]
    assert "filtered_or_rejected" in ai["likely_gap_reasons"]
    assert "hard_blocked" in ai["likely_gap_reasons"]
    assert "missing_from_official_and_watch_only" in ai["likely_gap_reasons"]


def test_theme_pick_bridge_marks_missing_when_no_rejection_artifact(tmp_path):
    write_json(tmp_path / "theme_discovery_2026-05-09.json", {
        "artifact": "theme_discovery",
        "themes": [
            {
                "theme": "security",
                "theme_id": "security",
                "lifecycle_state": "news_hype_unconfirmed",
                "theme_score": 30.0,
                "tickers": ["KTOS", "ODTX"],
            }
        ],
    })
    write_csv(tmp_path / "picks_log.csv", [])

    report = build_theme_pick_bridge(date_str="2026-05-09", data_dir=tmp_path)
    sec = report["themes"][0]

    assert sec["official_pick_match_count"] == 0
    assert sec["watch_only_match_count"] == 0
    assert sec["missing_from_official_and_watch_only"] == ["KTOS", "ODTX"]
    assert "no_daily_rejection_artifact_available" in sec["likely_gap_reasons"]


def test_theme_pick_bridge_writes_outputs(tmp_path):
    write_json(tmp_path / "theme_discovery_2026-05-09.json", {
        "artifact": "theme_discovery",
        "themes": [
            {
                "theme": "ai",
                "theme_id": "ai",
                "lifecycle_state": "emerging_theme",
                "theme_score": 100.0,
                "tickers": ["NVDA"],
            }
        ],
    })
    write_csv(tmp_path / "picks_log.csv", [
        {"pick_date": "2026-05-09", "ticker": "NVDA", "company": "NVIDIA", "tag": "AI"}
    ])

    report = build_theme_pick_bridge(date_str="2026-05-09", data_dir=tmp_path)
    json_path, md_path = write_outputs(report, data_dir=tmp_path)

    assert json_path.name == "theme_pick_bridge_2026-05-09.json"
    assert md_path.name == "theme_pick_bridge_2026-05-09.md"

    saved = json.loads(json_path.read_text())
    assert saved["observe_only"] is True

    md = md_path.read_text()
    assert "Theme-to-Pick Bridge Report" in md
    assert "Observe-only bridge" in md
    assert "ai" in md
    assert "NVDA" in md

def test_theme_pick_bridge_preserves_theme_market_evidence(tmp_path):
    import json
    from scripts.build_theme_pick_bridge import build_theme_pick_bridge, format_markdown

    theme_path = tmp_path / "theme_discovery_2026-05-09.json"
    theme_path.write_text(json.dumps({
        "artifact": "theme_discovery",
        "date": "2026-05-09",
        "themes": [
            {
                "theme": "ai",
                "theme_id": "ai",
                "lifecycle_state": "emerging_theme",
                "theme_score": 99.0,
                "tickers": ["AAPL", "NVDA"],
                "risk_flags": ["observe_only_theme", "market_evidence_available"],
                "market_evidence": {
                    "market_evidence_status": "available_from_existing_evidence_fields",
                    "relative_strength_vs_spy_pct": 3.2,
                    "market_quality_score_adjustment": 1.4,
                },
            }
        ],
    }))

    report = build_theme_pick_bridge(
        date_str="2026-05-09",
        data_dir=tmp_path,
        theme_path=theme_path,
    )

    theme = report["themes"][0]
    assert theme["theme"] == "ai"
    assert theme["market_evidence"]["market_evidence_status"] == "available_from_existing_evidence_fields"
    assert theme["market_evidence"]["relative_strength_vs_spy_pct"] == 3.2
    assert "market_evidence_available" in theme["risk_flags"]

    md = format_markdown(report)
    assert "Market evidence" in md
    assert "available_from_existing_evidence_fields" in md
