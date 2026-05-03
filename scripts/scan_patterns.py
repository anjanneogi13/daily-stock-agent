"""T47: Scan one ticker or a watchlist for patterns.

Usage:
    python scripts/scan_patterns.py --ticker NVDA
    python scripts/scan_patterns.py --watchlist data/watchlist.json
    python scripts/scan_patterns.py --watchlist data/watchlist.json --persist
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pattern_engine import scan_ticker, persist


def _load_watchlist(p: Path):
    data = json.loads(p.read_text())
    if isinstance(data, list):
        return [str(x) for x in data]
    if isinstance(data, dict):
        # Try common shapes
        if "tickers" in data:
            return list(data["tickers"])
        return list(data.keys())
    return []


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--ticker", type=str)
    g.add_argument("--watchlist", type=str)
    ap.add_argument("--persist", action="store_true")
    ap.add_argument("--regime",  type=str, default=None)
    args = ap.parse_args(argv)

    tickers = [args.ticker] if args.ticker else _load_watchlist(Path(args.watchlist))
    print(f"📊 scanning {len(tickers)} ticker(s)...")
    all_matches = []
    for t in tickers:
        ms = scan_ticker(t, regime=args.regime)
        for m in ms:
            print(f"  • {t:6s} {m['pattern']:14s} "
                  f"conf={m['confidence']:.2f}  {m.get('notes','')}")
        all_matches.extend(ms)

    if args.persist and all_matches:
        n = persist(all_matches)
        print(f"💾 wrote {n} matches → data/patterns.jsonl")
    print(f"✅ done: {len(all_matches)} pattern(s) found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
