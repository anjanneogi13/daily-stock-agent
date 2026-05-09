#!/usr/bin/env python3
"""End-to-end dry-run validation for Lane 1 official premarket picks.

This script uses a synthetic candidate and validates the local official-pick
production chain without calling market data providers, LLMs, Telegram, or GitHub.

It exercises:
- candidate diagnostics,
- portfolio risk gate,
- missing-data fail-closed gate,
- official pick artifact generation,
- official pick contract validation,
- workflow artifact validator.

Safety:
- no live data calls,
- no real picks,
- no alerts,
- no paper/live trading,
- writes only to an isolated dry-run directory unless explicitly configured.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.validate_official_pick_artifacts import validate_artifacts
from src.candidate_diagnostics import build_candidate_diagnostics
from src.missing_data_gate import apply_missing_data_gate
from src.official_pick_artifact import write_official_pick_artifacts
from src.portfolio_risk_gate import apply_portfolio_risk_gate
from src.premarket_decision_contract import validate_official_pick


ET = ZoneInfo("America/New_York")


def _default_date() -> str:
    return datetime.now(ET).strftime("%Y-%m-%d")


def _synthetic_candidate(ticker: str = "DRYRUN") -> dict:
    return {
        "ticker": ticker,
        "trade_type": "swing",
        "scores": {
            "composite": 0.82,
            "day_score": 0.41,
            "sector_tag": "DRYRUN",
            "sector_mult": 1.0,
            "vol_ratio": 1.4,
        },
        "plan": {
            "entry": 100.0,
            "stop_loss": 95.0,
            "take_profit": 112.0,
            "risk_reward": 2.4,
            "quantity": 10,
        },
        "info_short": {
            "name": "Dry Run Synthetic Candidate",
            "sector": "Technology",
        },
        "days_to_earnings": 30,
        "premarket_sanity": {
            "action": "SAFE",
            "actionable": True,
            "reason": "synthetic dry-run candidate with complete required fields",
        },
        "premarket_actionable": True,
        "premarket_action": "SAFE",
        "news": {},
        "risk_flags": [],
    }


def _risk_config() -> dict:
    return {
        "risk": {
            "account_size": 10000,
            "risk_per_trade_pct": 1.0,
            "max_positions": 5,
            "max_per_sector": 3,
            "max_per_tag": 3,
            "min_risk_reward": 1.0,
        }
    }


def _write_minimal_csv(path: Path, date_str: str, pick: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plan = pick.get("plan", {})
    scores = pick.get("scores", {})
    info = pick.get("info_short", {})

    fieldnames = [
        "pick_date",
        "ticker",
        "company",
        "trade_type",
        "score",
        "entry",
        "stop_loss",
        "take_profit",
        "risk_reward",
        "qty",
        "regime",
        "cape",
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({
            "pick_date": date_str,
            "ticker": pick.get("ticker"),
            "company": info.get("name", ""),
            "trade_type": pick.get("trade_type", "swing"),
            "score": scores.get("composite"),
            "entry": plan.get("entry"),
            "stop_loss": plan.get("stop_loss"),
            "take_profit": plan.get("take_profit"),
            "risk_reward": plan.get("risk_reward"),
            "qty": plan.get("quantity"),
            "regime": "dry_run",
            "cape": "",
        })


def run_dry_run(*, output_dir: Path, date_str: str, keep: bool = False, ticker: str = "DRYRUN") -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)

    candidate = _synthetic_candidate(ticker)
    pipeline = {
        "dry_run": True,
        "universe_count": 1,
        "fetched_count": 1,
        "scored_count": 1,
        "filtered_count": 1,
        "capped_count": 1,
        "pre_hard_block_pick_count": 1,
        "hard_blocked_count": 0,
        "post_hard_block_pick_count": 1,
        "pre_premarket_sanity_pick_count": 1,
        "premarket_sanity_blocked_count": 0,
        "post_premarket_sanity_pick_count": 1,
    }

    diagnostics = build_candidate_diagnostics(
        pipeline=pipeline,
        scored_candidates=[candidate],
        filtered_candidates=[candidate],
        capped_candidates=[candidate],
        pre_hard_block_candidates=[candidate],
        hard_blocked_candidates=[],
        post_hard_block_candidates=[candidate],
        pre_premarket_sanity_candidates=[candidate],
        premarket_sanity_blocked_candidates=[],
        selected_picks=[candidate],
        extra={"dry_run": True},
    )

    risk_allowed, risk_blocked, risk_summary = apply_portfolio_risk_gate(
        [candidate],
        _risk_config(),
        existing_positions=[],
    )
    if risk_blocked or len(risk_allowed) != 1:
        raise RuntimeError(f"synthetic candidate failed portfolio risk gate: {risk_blocked}")

    pipeline["portfolio_risk_blocked_count"] = len(risk_blocked)
    pipeline["post_portfolio_risk_pick_count"] = len(risk_allowed)

    complete, missing_blocked, missing_summary = apply_missing_data_gate(risk_allowed)
    if missing_blocked or len(complete) != 1:
        raise RuntimeError(f"synthetic candidate failed missing-data gate: {missing_blocked}")

    pipeline["missing_data_blocked_count"] = len(missing_blocked)
    pipeline["final_pick_count"] = len(complete)

    diagnostics = build_candidate_diagnostics(
        pipeline=pipeline,
        scored_candidates=[candidate],
        filtered_candidates=[candidate],
        capped_candidates=[candidate],
        pre_hard_block_candidates=[candidate],
        hard_blocked_candidates=[],
        post_hard_block_candidates=[candidate],
        pre_premarket_sanity_candidates=[candidate],
        premarket_sanity_blocked_candidates=[],
        portfolio_risk_blocked_candidates=[],
        missing_data_blocked_candidates=[],
        selected_picks=complete,
        extra={
            "dry_run": True,
            "portfolio_risk_summary": risk_summary,
            "missing_data_summary": missing_summary,
        },
    )

    csv_path = output_dir / "picks_log.csv"
    _write_minimal_csv(csv_path, date_str, complete[0])

    artifact_summary = write_official_pick_artifacts(
        complete,
        data_dir=output_dir,
        pipeline=pipeline,
        candidate_diagnostics=diagnostics,
        regime={"regime": "dry_run"},
        data_readiness_status="ready_dry_run",
        provider_status="healthy_dry_run",
        market_session_status="premarket_dry_run",
    )

    # write_official_pick_artifacts uses current ET date by design. The dry-run
    # defaults to current ET date too; fail loudly if a caller supplies a date
    # that does not match generated artifacts.
    artifact_errors = validate_artifacts(
        date_str,
        data_dir=output_dir,
        csv_path=csv_path,
        expected_count=1,
    )
    if artifact_errors:
        raise RuntimeError("official artifact validator failed: " + "; ".join(artifact_errors))

    artifact_paths = sorted(output_dir.glob(f"premarket_official_pick_{date_str}_*.json"))
    if len(artifact_paths) != 1:
        raise RuntimeError(f"expected exactly one official pick artifact, found {len(artifact_paths)}")

    payload = json.loads(artifact_paths[0].read_text(encoding="utf-8"))
    contract_errors = validate_official_pick(payload)
    if contract_errors:
        raise RuntimeError("official pick contract validation failed: " + "; ".join(contract_errors))

    result = {
        "dry_run": True,
        "date": date_str,
        "output_dir": str(output_dir),
        "ticker": ticker,
        "pipeline": pipeline,
        "candidate_diagnostics_available": bool(diagnostics),
        "artifact_summary": artifact_summary,
        "official_pick_artifact": str(artifact_paths[0]),
        "contract_validation_errors": contract_errors,
        "artifact_validation_errors": artifact_errors,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "kept_output": keep,
    }

    (output_dir / f"dry_run_official_premarket_pick_{date_str}.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=_default_date(), help="ET date for validation; defaults to today")
    parser.add_argument("--output-dir", default="", help="Directory for dry-run artifacts; defaults to a temporary directory")
    parser.add_argument("--keep", action="store_true", help="Keep temporary output directory")
    parser.add_argument("--ticker", default="DRYRUN", help="Synthetic ticker symbol")
    args = parser.parse_args()

    temp_dir = None
    if args.output_dir:
        output_dir = Path(args.output_dir)
        keep = True
    else:
        temp_dir = tempfile.mkdtemp(prefix="lane1-official-dry-run-")
        output_dir = Path(temp_dir)
        keep = args.keep

    try:
        result = run_dry_run(
            output_dir=output_dir,
            date_str=args.date,
            keep=keep,
            ticker=args.ticker,
        )
        print("✅ Lane 1 official premarket dry-run passed")
        print(f"- date: {result['date']}")
        print(f"- output_dir: {result['output_dir']}")
        print(f"- official_pick_artifact: {result['official_pick_artifact']}")
        print(f"- official_pick_count: {result['artifact_summary'].get('official_pick_count')}")
        print("- paper_trading_enabled: false")
        print("- live_trading_enabled: false")
        return 0
    except Exception as exc:
        print(f"❌ Lane 1 official premarket dry-run failed: {exc}")
        return 1
    finally:
        if temp_dir and not keep:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
