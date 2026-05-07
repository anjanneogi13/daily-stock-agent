#!/usr/bin/env python3
"""Attribute news-signal outcomes to future price movement.

Monitoring-only scaffold. This script builds outcome evidence for news signals
without mutating official pick stats, signal journals, learning journals, paper
trading, or live trading state.

Reads:
- data/news_log.jsonl
- data/news_signals.json
- data/watchlist.json

Writes, unless --no-write:
- data/news_signal_outcomes_YYYY-MM-DD.jsonl
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


try:
    import yfinance as yf
except Exception:  # pragma: no cover - dependency may be unavailable locally
    yf = None


ET = ZoneInfo("America/New_York")
DATA_DIR = Path("data")
VALID_STATUSES = {
    "evaluated",
    "missing_price_data",
    "missing_future_data",
    "invalid_ticker",
    "quote_unavailable",
}


def _today_et() -> str:
    return datetime.now(timezone.utc).astimezone(ET).strftime("%Y-%m-%d")


def _parse_dt(value) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        pass
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            continue
    return None


def _safe_float(value, default=None):
    try:
        if value in (None, "", "None"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                rows.append(obj)
        except Exception:
            continue
    return rows


def is_valid_ticker(ticker: str) -> bool:
    if not ticker:
        return False
    ticker = ticker.strip().upper()
    if len(ticker) > 8:
        return False
    bad_chars = set(":/ ")
    if any(ch in ticker for ch in bad_chars):
        return False
    return ticker.replace(".", "").replace("-", "").isalnum()


def _evidence_from_news_log(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        cls = row.get("classification") or {}
        if not isinstance(cls, dict):
            continue
        ticker = (cls.get("primary_ticker") or (row.get("ticker_list") or [None])[0] or "")
        ticker = str(ticker).upper().strip()
        if not ticker:
            continue
        published = _parse_dt(row.get("published_at")) or _parse_dt(row.get("classified_at"))
        out.append({
            "source": "news_log",
            "ticker": ticker,
            "signal_timestamp": (published or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(),
            "headline": row.get("headline") or "",
            "url": row.get("url") or "",
            "sentiment": cls.get("sentiment") or "",
            "category": cls.get("category") or "",
            "tradeable_score": _safe_float(cls.get("tradeable_score"), 0.0),
            "score_delta": None,
            "action_window": cls.get("action_window") or "",
            "hard_block": False,
        })
    return out


def _evidence_from_signals(signals) -> list[dict]:
    if not isinstance(signals, dict):
        return []
    out = []
    for ticker, sig in signals.items():
        if not isinstance(sig, dict):
            continue
        tk = str(sig.get("ticker") or ticker or "").upper().strip()
        if not tk:
            continue
        ts = _parse_dt(sig.get("added_at")) or datetime.now(timezone.utc)
        out.append({
            "source": "news_signals",
            "ticker": tk,
            "signal_timestamp": ts.astimezone(timezone.utc).isoformat(),
            "headline": sig.get("headline") or "",
            "url": sig.get("url") or "",
            "sentiment": sig.get("sentiment") or "",
            "category": sig.get("catalyst") or "",
            "tradeable_score": _safe_float(sig.get("tradeable_score"), 0.0),
            "score_delta": _safe_float(sig.get("score_delta"), 0.0),
            "action_window": sig.get("action_window") or "",
            "hard_block": bool(sig.get("hard_block")),
        })
    return out


def _evidence_from_watchlist(watchlist) -> list[dict]:
    items = []
    if isinstance(watchlist, dict):
        raw = watchlist.get("items", [])
        if isinstance(raw, list):
            items = [x for x in raw if isinstance(x, dict)]
    elif isinstance(watchlist, list):
        items = [x for x in watchlist if isinstance(x, dict)]

    out = []
    for item in items:
        ticker = str(item.get("ticker") or "").upper().strip()
        if not ticker:
            continue
        ts = _parse_dt(item.get("added_at")) or _parse_dt(item.get("updated_at")) or datetime.now(timezone.utc)
        out.append({
            "source": "watchlist",
            "ticker": ticker,
            "signal_timestamp": ts.astimezone(timezone.utc).isoformat(),
            "headline": item.get("headline") or "",
            "url": item.get("url") or "",
            "sentiment": item.get("sentiment") or "",
            "category": item.get("category") or "",
            "tradeable_score": _safe_float(item.get("tradeable_score"), 0.0),
            "score_delta": None,
            "action_window": item.get("action_window") or "",
            "hard_block": False,
        })
    return out


def load_evidence(data_dir: Path = DATA_DIR, max_items: int = 250) -> list[dict]:
    rows = []
    rows.extend(_evidence_from_signals(load_json(data_dir / "news_signals.json", {})))
    rows.extend(_evidence_from_watchlist(load_json(data_dir / "watchlist.json", {})))
    rows.extend(_evidence_from_news_log(load_jsonl(data_dir / "news_log.jsonl")))

    # Deduplicate by source/ticker/headline/timestamp prefix.
    seen = set()
    out = []
    for row in rows:
        key = (
            row.get("source"),
            row.get("ticker"),
            str(row.get("headline") or "")[:120],
            str(row.get("signal_timestamp") or "")[:10],
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(row)

    out.sort(
        key=lambda x: (
            str(x.get("signal_timestamp") or ""),
            str(x.get("source") or ""),
            str(x.get("ticker") or ""),
        ),
        reverse=True,
    )
    return out[:max_items]


def _history_for_ticker(ticker: str, signal_dt: datetime, horizon_days: int):
    if yf is None:
        return None

    # Add enough calendar days to cover weekends/holidays.
    start = (signal_dt - timedelta(days=1)).date().isoformat()
    end = (signal_dt + timedelta(days=horizon_days + 8)).date().isoformat()
    try:
        hist = yf.Ticker(ticker).history(start=start, end=end, interval="1d", auto_adjust=False)
    except Exception:
        return None
    if hist is None or getattr(hist, "empty", True):
        return None
    return hist


def _close_at_or_after(hist, signal_dt: datetime):
    if hist is None or getattr(hist, "empty", True):
        return None, None

    signal_date = signal_dt.date()
    for idx, row in hist.iterrows():
        idx_date = idx.date() if hasattr(idx, "date") else None
        if idx_date and idx_date >= signal_date:
            close = _safe_float(row.get("Close"))
            if close and close > 0:
                return idx_date.isoformat(), close
    return None, None


def _future_close(hist, signal_dt: datetime, trading_days: int):
    if hist is None or getattr(hist, "empty", True):
        return None, None

    signal_date = signal_dt.date()
    future = []
    for idx, row in hist.iterrows():
        idx_date = idx.date() if hasattr(idx, "date") else None
        if idx_date and idx_date >= signal_date:
            close = _safe_float(row.get("Close"))
            if close and close > 0:
                future.append((idx_date.isoformat(), close))
    if len(future) <= trading_days:
        return None, None
    return future[trading_days]


def evaluate_evidence_item(item: dict, *, horizon_days: int = 3) -> dict:
    ticker = str(item.get("ticker") or "").upper().strip()
    signal_dt = _parse_dt(item.get("signal_timestamp"))

    base = {
        **item,
        "outcome_schema": "news_signal_outcome_v1",
        "evaluated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "horizon_days": horizon_days,
        "mode": "monitoring_only",
        "read_only": True,
        "official_pick_stats_mutated": False,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
    }

    if not is_valid_ticker(ticker):
        return {**base, "status": "invalid_ticker", "reason": "ticker failed validation"}

    if signal_dt is None:
        return {**base, "status": "missing_price_data", "reason": "missing/invalid signal timestamp"}

    hist = _history_for_ticker(ticker, signal_dt, horizon_days)
    if hist is None:
        return {**base, "status": "quote_unavailable", "reason": "price history unavailable"}

    start_date, start_close = _close_at_or_after(hist, signal_dt)
    if start_close is None:
        return {**base, "status": "missing_price_data", "reason": "no close at/after signal date"}

    one_d_date, one_d_close = _future_close(hist, signal_dt, 1)
    h_date, h_close = _future_close(hist, signal_dt, horizon_days)

    if one_d_close is None and h_close is None:
        return {
            **base,
            "status": "missing_future_data",
            "reason": "future close unavailable yet",
            "start_date": start_date,
            "start_close": round(start_close, 4),
        }

    one_d_return = None
    if one_d_close is not None:
        one_d_return = round((one_d_close - start_close) / start_close * 100.0, 4)

    horizon_return = None
    if h_close is not None:
        horizon_return = round((h_close - start_close) / start_close * 100.0, 4)

    return {
        **base,
        "status": "evaluated",
        "reason": "",
        "start_date": start_date,
        "start_close": round(start_close, 4),
        "one_d_date": one_d_date,
        "one_d_close": round(one_d_close, 4) if one_d_close is not None else None,
        "one_d_return_pct": one_d_return,
        "horizon_date": h_date,
        "horizon_close": round(h_close, 4) if h_close is not None else None,
        "horizon_return_pct": horizon_return,
    }


def build_outcomes(
    *,
    data_dir: Path = DATA_DIR,
    max_items: int = 250,
    horizon_days: int = 3,
) -> list[dict]:
    evidence = load_evidence(data_dir=data_dir, max_items=max_items)
    return [evaluate_evidence_item(item, horizon_days=horizon_days) for item in evidence]


def outcomes_path(date_str: str, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"news_signal_outcomes_{date_str}.jsonl"


def write_outcomes(outcomes: list[dict], *, date_str: str, data_dir: Path = DATA_DIR) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    path = outcomes_path(date_str, data_dir=data_dir)
    with path.open("w", encoding="utf-8") as f:
        for row in outcomes:
            f.write(json.dumps(row, sort_keys=True) + "\n")
    return path


def summarize_outcomes(outcomes: list[dict]) -> dict:
    by_status = {}
    evaluated = []
    for row in outcomes:
        status = row.get("status") or "unknown"
        by_status[status] = by_status.get(status, 0) + 1
        if status == "evaluated":
            evaluated.append(row)

    avg_1d = None
    one_d_vals = [r.get("one_d_return_pct") for r in evaluated if isinstance(r.get("one_d_return_pct"), (int, float))]
    if one_d_vals:
        avg_1d = round(sum(one_d_vals) / len(one_d_vals), 4)

    avg_h = None
    h_vals = [r.get("horizon_return_pct") for r in evaluated if isinstance(r.get("horizon_return_pct"), (int, float))]
    if h_vals:
        avg_h = round(sum(h_vals) / len(h_vals), 4)

    return {
        "count": len(outcomes),
        "by_status": dict(sorted(by_status.items())),
        "evaluated_count": len(evaluated),
        "avg_one_d_return_pct": avg_1d,
        "avg_horizon_return_pct": avg_h,
        "paper_trading_enabled": False,
        "live_trading_enabled": False,
        "official_pick_stats_mutated": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=_today_et())
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    parser.add_argument("--max-items", type=int, default=250)
    parser.add_argument("--horizon-days", type=int, default=3)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    outcomes = build_outcomes(
        data_dir=Path(args.data_dir),
        max_items=args.max_items,
        horizon_days=args.horizon_days,
    )
    summary = summarize_outcomes(outcomes)

    if args.no_write:
        print(json.dumps({"summary": summary, "outcomes": outcomes}, indent=2, sort_keys=True))
        return 0

    path = write_outcomes(outcomes, date_str=args.date, data_dir=Path(args.data_dir))
    print(f"[news-outcomes] wrote {len(outcomes)} row(s) to {path}")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
