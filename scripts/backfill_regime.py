"""Backfill `regime` column for picks_log rows where it's missing/unknown.

Background (May 4 2026): early picks (Apr 28) were logged before the regime
detector was wired into the pick_logger flow, leaving `regime=''` or
`regime='unknown'`. They DO have spy_close recorded, so we can reconstruct
regime by comparing to SPY 200d SMA on the pick_date.

Usage:
    python scripts/backfill_regime.py            # dry run
    python scripts/backfill_regime.py --apply    # write changes

Idempotent: only fills missing/unknown rows. Won't overwrite existing values.
"""
import csv
import sys
from pathlib import Path

import yfinance as yf
import pandas as pd


PICKS_LOG = Path("data/picks_log.csv")


def _classify(spy_close: float, sma200: float) -> str:
    """Same 4-state logic as src/regime.py (E3a)."""
    if not spy_close or not sma200:
        return "unknown"
    pct = (spy_close - sma200) / sma200 * 100
    if pct >= 5.0:
        return "bull"
    if pct >= 0.0:
        return "transition"
    if pct >= -5.0:
        return "chop"
    return "bear"


def _spy_sma_lookup(needed_dates: set[str]) -> dict[str, float]:
    """Fetch SPY history once; compute 200d SMA per date we need."""
    if not needed_dates:
        return {}
    earliest = min(needed_dates)
    # Need ≥200 trading days BEFORE the earliest date
    start = (pd.to_datetime(earliest) - pd.Timedelta(days=320)).strftime("%Y-%m-%d")
    end   = (pd.to_datetime(max(needed_dates)) + pd.Timedelta(days=2)).strftime("%Y-%m-%d")
    print(f"  Fetching SPY {start} → {end}...")
    df = yf.download("SPY", start=start, end=end, progress=False, auto_adjust=False)
    if df.empty:
        print("  ⚠ SPY fetch returned empty")
        return {}
    df["sma200"] = df["Close"].rolling(200).mean()
    out = {}
    for d in needed_dates:
        ts = pd.Timestamp(d)
        # Use most recent trading day <= target
        sub = df.loc[df.index <= ts]
        if sub.empty:
            continue
        sma = sub["sma200"].iloc[-1]
        if pd.notna(sma):
            out[d] = float(sma.iloc[0]) if hasattr(sma, "iloc") else float(sma)
    return out


def backfill(apply: bool = False) -> dict:
    rows = list(csv.DictReader(open(PICKS_LOG)))
    headers = rows[0].keys() if rows else []

    needs_fix = [r for r in rows if (r.get("regime") or "").strip() in ("", "unknown")]
    print(f"  Total rows:           {len(rows)}")
    print(f"  Rows needing regime:  {len(needs_fix)}")

    if not needs_fix:
        print("  ✅ Nothing to backfill")
        return {"updated": 0, "skipped": 0}

    needed_dates = {r["pick_date"] for r in needs_fix if r.get("pick_date")}
    sma_by_date = _spy_sma_lookup(needed_dates)
    print(f"  SMA lookup successful for {len(sma_by_date)}/{len(needed_dates)} date(s)")

    updated = 0
    skipped = 0
    for r in needs_fix:
        d = r.get("pick_date")
        spy_close_str = (r.get("spy_close") or "").strip()
        sma = sma_by_date.get(d)
        try:
            spy_close = float(spy_close_str) if spy_close_str else None
        except ValueError:
            spy_close = None
        if not spy_close or not sma:
            skipped += 1
            continue
        regime = _classify(spy_close, sma)
        pct = (spy_close - sma) / sma * 100
        print(f"    {r['ticker']:6}  {d}  spy={spy_close:.2f}  sma200={sma:.2f}  pct={pct:+.2f}%  → regime={regime}")
        r["regime"] = regime
        updated += 1

    if apply and updated:
        with open(PICKS_LOG, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(headers))
            w.writeheader()
            w.writerows(rows)
        print(f"\n  ✅ WROTE {PICKS_LOG} — {updated} rows updated, {skipped} skipped")
    else:
        mode = "DRY-RUN" if not apply else "NOTHING TO WRITE"
        print(f"\n  [{mode}] would update {updated}, skip {skipped}")

    return {"updated": updated, "skipped": skipped}


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    backfill(apply=apply)
