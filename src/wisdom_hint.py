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



def _short_author(author: str) -> str:
    """Pull a short display name from a book author field.
    'Edwin Lefèvre / Jesse Livermore' → 'Livermore'
    'Peter Lynch'                     → 'Lynch'
    'William O\'Neil'                 → "O'Neil"
    """
    if not author:
        return ""
    # Prefer the last name after '/' if multi-author, else last token of name
    primary = author.split("/")[-1].strip()
    parts = primary.split()
    return parts[-1] if parts else primary


def _format_lesson(best: dict, max_len: int = 90) -> str:
    """Format a lesson dict as a Telegram hint line.
    T36: prepend book author if source startswith 'book:'.
    """
    text = str(best.get("text", "")).strip()
    if not text:
        return ""
    src = str(best.get("source", ""))
    if src.startswith("book:"):
        author = _short_author(str(best.get("author", "")))
        if author:
            # Reserve room for "Author: " prefix
            budget = max_len - len(author) - 2
            if len(text) > budget:
                text = text[: budget - 1] + "…"
            return f"   🧠 _{author}: {text}_"
    if len(text) > max_len:
        text = text[: max_len - 3] + "…"
    return f"   🧠 _{text}_"


def wisdom_hint(ticker: Optional[str],
                min_confidence: float = 0.7,
                sector: Optional[str] = None) -> str:
    """Return a one-line Telegram-ready hint for a ticker, or '' if none.

    T27: when `sector` is provided, also matches sector-wide lessons
    (e.g. a lesson tagged "semis" surfaces on every semi pick).
    """
    if not ticker and not sector:
        return ""
    try:
        ls = _lft(ticker, min_confidence=min_confidence, sector=sector)
    except TypeError:
        # Backward-compat with older wisdom_base
        ls = _lft(ticker, min_confidence=min_confidence)
    except Exception:
        return ""
    if not ls:
        return ""
    best = max(ls, key=lambda L: L.get("confidence", 0))
    return _format_lesson(best)


# ═══════════════════════════════════════════════════════════════
# T26: pattern-engine inline hints (empirical edge/drag from
# hypothesis_engine, surfaced per pick when row attributes match)
# ═══════════════════════════════════════════════════════════════
try:
    from src.wisdom_base import load_active_patterns as _lap
except Exception:
    _lap = lambda: []


# Pick-row attributes worth matching against patterns.signal
_PATTERN_SIGNALS = ("trade_type", "regime", "sector", "day_of_week")


def pattern_hint(row: dict,
                 min_sample: int = 20,
                 max_p: float = 0.05) -> str:
    """Return a one-line hint if a statistically-significant pattern
    matches any attribute of the given pick row. Empty string if none.

    Args:
        row: a pick dict (or anything with .get) with attrs like
             trade_type, regime, sector, day_of_week.
        min_sample: required sample_n threshold (default 20).
        max_p: required p_value ceiling (default 0.05).
    """
    if not row:
        return ""
    try:
        pats = _lap()
    except Exception:
        return ""
    if not pats:
        return ""

    # Score each match: prefer drag (risk warnings) over edge,
    # higher sample_n, lower p_value.
    matches = []
    for pat in pats:
        sig = pat.get("signal")
        if sig not in _PATTERN_SIGNALS:
            continue
        row_val = row.get(sig)
        if row_val is None:
            continue
        if str(row_val).lower() != str(pat.get("bucket", "")).lower():
            continue
        if int(pat.get("sample_n", 0)) < min_sample:
            continue
        if float(pat.get("p_value", 1.0)) > max_p:
            continue
        matches.append(pat)

    if not matches:
        return ""

    # Priority: drag first (warnings), then by largest sample_n
    drags = [m for m in matches if m.get("effect") == "drag"]
    edges = [m for m in matches if m.get("effect") == "edge"]
    chosen = (drags or edges)
    chosen.sort(key=lambda m: (-int(m.get("sample_n", 0)),
                                float(m.get("p_value", 1.0))))
    best = chosen[0]

    icon = "⚠" if best.get("effect") == "drag" else "✨"
    wr   = float(best.get("win_rate", 0)) * 100
    n    = int(best.get("sample_n", 0))
    sig  = best.get("signal", "?")
    bkt  = best.get("bucket", "?")
    return f"   {icon} _{sig}={bkt}: {wr:.0f}% win-rate over {n} trades_"


# ═══════════════════════════════════════════════════════════════
# T25: dry-run CLI — preview hints before market open
# ═══════════════════════════════════════════════════════════════
def _row_for_ticker(ticker: str) -> dict:
    """Best-effort: return latest pick row for ticker from picks_log.csv.
    Returns {} if not found — pattern_hint preview gracefully degrades."""
    import csv
    from pathlib import Path as _P
    path = _P("data/picks_log.csv")
    if not path.exists():
        return {}
    rows = []
    try:
        with path.open() as f:
            for r in csv.DictReader(f):
                if r.get("ticker", "").upper() == ticker.upper():
                    rows.append(r)
    except Exception:
        return {}
    return rows[-1] if rows else {}


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
            print(f"  {tk:6s}  → (no wisdom hint)")
        # T26: also preview pattern hint if row-context exists
        ph_row = _row_for_ticker(tk)
        if ph_row:
            ph = pattern_hint(ph_row)
            if ph:
                print(f"          {ph.lstrip()}")
    print("─" * 60)
    print(f"✅ {n_hits}/{len(tickers)} tickers have hints\n")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(_cli())

# ───────────────── T43/B4: trigger-context hints ─────────────────

try:
    from src.wisdom_base import lessons_for_context as _lfc
except Exception:
    _lfc = lambda ctx, min_confidence=0.7: []


def context_hint(ctx: dict, min_confidence: float = 0.8) -> str:
    """Surface the highest-confidence lesson whose triggers fire on ctx.

    ctx keys may include: drawdown_pct, regime, days_held, trade_type,
    rsi, atr, exit_status, r_multiple, etc.
    Returns '' if nothing fires.
    """
    if not ctx:
        return ""
    try:
        ls = _lfc(ctx, min_confidence=min_confidence)
    except Exception:
        return ""
    if not ls:
        return ""
    best = max(ls, key=lambda L: L.get("confidence", 0))
    return _format_lesson(best)

