"""T24: per-pick wisdom hint formatter (used by Telegram pick blocks).

Kept standalone so tests can import it without triggering the
top-level sys.exit() that scripts/send_telegram.py performs when
TELEGRAM_BOT_TOKEN is unset.
"""
from typing import Optional

try:
    from src.wisdom_base import lessons_for_ticker as _lft
except Exception:
    _lft = lambda *a, **k: []


def wisdom_hint(ticker: Optional[str], min_confidence: float = 0.7) -> str:
    """Return a one-line Telegram-ready hint for a ticker, or '' if none."""
    if not ticker:
        return ""
    try:
        ls = _lft(ticker, min_confidence=min_confidence)
    except Exception:
        return ""
    if not ls:
        return ""
    best = max(ls, key=lambda L: L.get("confidence", 0))
    text = str(best.get("text", "")).strip()
    if not text:
        return ""
    if len(text) > 90:
        text = text[:87] + "…"
    return f"   🧠 _{text}_"


# ═══════════════════════════════════════════════════════════════
# T25: dry-run CLI — preview hints before market open
# ═══════════════════════════════════════════════════════════════
def _cli(argv=None):
    """python -m src.wisdom_hint TICKER [TICKER ...]
       python -m src.wisdom_hint --from-csv path/to/picks_log.csv [--date YYYY-MM-DD]
       python -m src.wisdom_hint --min-confidence 0.7 AAPL
    """
    import argparse, csv, sys
    from datetime import datetime
    from pathlib import Path as _P

    ap = argparse.ArgumentParser(prog="wisdom_hint",
        description="Preview per-pick wisdom hints for given tickers.")
    ap.add_argument("tickers", nargs="*", help="Tickers to preview")
    ap.add_argument("--from-csv", help="Read tickers from a picks CSV")
    ap.add_argument("--date", help="Filter CSV rows to pick_date=YYYY-MM-DD (default: today)")
    ap.add_argument("--min-confidence", type=float, default=0.7,
                    help="Minimum lesson confidence (default 0.7)")
    args = ap.parse_args(argv)

    tickers = list(args.tickers)
    if args.from_csv:
        path = _P(args.from_csv)
        if not path.exists():
            print(f"❌ CSV not found: {path}", file=sys.stderr); return 2
        target_date = args.date or datetime.now().strftime("%Y-%m-%d")
        with path.open() as f:
            for row in csv.DictReader(f):
                if row.get("pick_date") == target_date and row.get("ticker"):
                    tickers.append(row["ticker"])
        print(f"📄 Loaded {len(tickers)} ticker(s) from {path} for {target_date}")

    if not tickers:
        print("ℹ No tickers provided. Use args or --from-csv.")
        return 0

    print(f"\n🧠 Wisdom-hint preview (min_confidence={args.min_confidence})")
    print("─" * 60)
    n_hits = 0
    for tk in tickers:
        h = wisdom_hint(tk, min_confidence=args.min_confidence)
        if h:
            n_hits += 1
            print(f"  {tk:6s}  →{h.lstrip()}")
        else:
            print(f"  {tk:6s}  → (no hint)")
    print("─" * 60)
    print(f"✅ {n_hits}/{len(tickers)} tickers have hints\n")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_cli())

