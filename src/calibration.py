"""T37+T38: Calibration Brain (Pillar 3.5).

Reads backtest CSVs in data/backtest_results/<run_id>/picks.csv and
computes per-factor and per-timeframe attribution:

    For each factor bucket (e.g. trade_type=swing, rsi=30-50),
    report n, win_rate, mean_R, total_R.

Used by:
  - T39 weight-delta proposer (READ-ONLY)
  - T40 weekly Telegram footer
  - manual review (CLI)

CLI:
  python -m src.calibration latest                 # use newest run
  python -m src.calibration run RUN_ID
  python -m src.calibration factors                # by-factor table
  python -m src.calibration timeframes             # by-month table
  python -m src.calibration summary                # both, compact
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Optional, Tuple

RESULTS_ROOT = Path("data/backtest_results")


# ───────────────────────── data loading ─────────────────────────

def list_runs(root: Path = RESULTS_ROOT) -> List[Path]:
    """Return run directories sorted oldest→newest."""
    if not root.exists():
        return []
    return sorted([d for d in root.iterdir() if d.is_dir()])


def latest_run(root: Path = RESULTS_ROOT) -> Optional[Path]:
    runs = list_runs(root)
    return runs[-1] if runs else None


def load_picks(run_dir: Path) -> List[Dict]:
    """Load picks.csv from a run directory and coerce numeric fields."""
    csv_path = Path(run_dir) / "picks.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"no picks.csv in {run_dir}")
    rows: List[Dict] = []
    with csv_path.open() as f:
        for raw in csv.DictReader(f):
            # coerce numerics; leave non-numeric strings as-is
            for k in ("score", "entry", "stop_loss", "take_profit",
                      "rsi", "atr", "exit_price", "days_held",
                      "r_multiple", "return_pct"):
                v = raw.get(k)
                if v is None or v == "" or v == "None":
                    raw[k] = None
                else:
                    try:
                        raw[k] = float(v)
                    except (ValueError, TypeError):
                        raw[k] = None
            rows.append(raw)
    return rows


# ───────────────────────── bucketing ─────────────────────────

def _rsi_bucket(rsi: Optional[float]) -> str:
    if rsi is None:
        return "rsi_na"
    if rsi < 30:   return "rsi_oversold(<30)"
    if rsi < 50:   return "rsi_30-50"
    if rsi < 70:   return "rsi_50-70"
    return "rsi_overbought(>=70)"


def _score_bucket(s: Optional[float]) -> str:
    if s is None:  return "score_na"
    if s < 0.5:    return "score_<0.5"
    if s < 0.7:    return "score_0.5-0.7"
    if s < 0.85:   return "score_0.7-0.85"
    return "score_>=0.85"


def _atr_bucket(atr: Optional[float], entry: Optional[float]) -> str:
    """Volatility bucket as ATR % of entry price."""
    if not atr or not entry or entry <= 0:
        return "atrpct_na"
    pct = atr / entry * 100
    if pct < 1.5:  return "atrpct_<1.5"
    if pct < 3:    return "atrpct_1.5-3"
    if pct < 5:    return "atrpct_3-5"
    return "atrpct_>=5"


def _month_bucket(pick_date: Optional[str]) -> str:
    """YYYY-MM from a YYYY-MM-DD string."""
    if not pick_date or len(pick_date) < 7:
        return "date_na"
    return pick_date[:7]


# ───────────────────────── attribution stats ─────────────────────────

@dataclass
class BucketStat:
    bucket: str
    n: int
    wins: int
    win_rate: float
    mean_r: float
    total_r: float
    mean_return_pct: float

    def as_row(self) -> Dict:
        return {
            "bucket":          self.bucket,
            "n":               self.n,
            "wins":            self.wins,
            "win_rate":        round(self.win_rate, 3),
            "mean_r":          round(self.mean_r, 3),
            "total_r":         round(self.total_r, 2),
            "mean_return_pct": round(self.mean_return_pct, 3),
        }


def _is_win(row: Dict) -> bool:
    """A pick is a 'win' if its r_multiple > 0."""
    r = row.get("r_multiple")
    return r is not None and r > 0


def attribute_by(rows: List[Dict],
                 keyfunc,
                 min_n: int = 5) -> List[BucketStat]:
    """Group rows by keyfunc(row) → list of BucketStat (sorted by n desc).

    Buckets with fewer than min_n picks are dropped.
    """
    buckets: Dict[str, List[Dict]] = defaultdict(list)
    for r in rows:
        try:
            k = keyfunc(r)
        except Exception:
            continue
        if k is None:
            continue
        buckets[str(k)].append(r)

    out: List[BucketStat] = []
    for k, rs in buckets.items():
        if len(rs) < min_n:
            continue
        rmults  = [r.get("r_multiple") or 0.0 for r in rs]
        returns = [r.get("return_pct") or 0.0 for r in rs]
        wins    = sum(1 for r in rs if _is_win(r))
        out.append(BucketStat(
            bucket=k,
            n=len(rs),
            wins=wins,
            win_rate=wins / len(rs),
            mean_r=mean(rmults) if rmults else 0.0,
            total_r=sum(rmults),
            mean_return_pct=mean(returns) if returns else 0.0,
        ))
    return sorted(out, key=lambda b: -b.n)


# ───────────────────────── named factor reports ─────────────────────────

FACTOR_KEYS: Dict[str, callable] = {
    "trade_type": lambda r: r.get("trade_type") or "unknown",
    "rsi":        lambda r: _rsi_bucket(r.get("rsi")),
    "score":      lambda r: _score_bucket(r.get("score")),
    "atrpct":     lambda r: _atr_bucket(r.get("atr"), r.get("entry")),
    "exit_status": lambda r: r.get("exit_status") or "unknown",
}


def per_factor_report(rows: List[Dict],
                      min_n: int = 5) -> Dict[str, List[Dict]]:
    """Compute attribution for every named factor."""
    return {
        name: [b.as_row() for b in attribute_by(rows, fn, min_n=min_n)]
        for name, fn in FACTOR_KEYS.items()
    }


def per_timeframe_report(rows: List[Dict],
                         min_n: int = 5) -> List[Dict]:
    """T38: per-month attribution (chronologically sorted)."""
    stats = attribute_by(rows, lambda r: _month_bucket(r.get("pick_date")),
                         min_n=min_n)
    return [s.as_row() for s in sorted(stats, key=lambda b: b.bucket)]


def overall_summary(rows: List[Dict]) -> Dict:
    """Headline stats across all picks in the run."""
    if not rows:
        return {"n": 0, "wins": 0, "win_rate": 0.0,
                "mean_r": 0.0, "total_r": 0.0, "expectancy_R": 0.0}
    rmults = [r.get("r_multiple") or 0.0 for r in rows]
    wins   = sum(1 for r in rows if _is_win(r))
    return {
        "n":            len(rows),
        "wins":         wins,
        "win_rate":     round(wins / len(rows), 3),
        "mean_r":       round(mean(rmults), 3),
        "total_r":      round(sum(rmults), 2),
        "expectancy_R": round(mean(rmults), 3),
    }


# ───────────────────────── CLI ─────────────────────────

def _resolve_run(arg: str) -> Path:
    if arg == "latest":
        run = latest_run()
        if not run:
            raise SystemExit("❌ no backtest runs found in data/backtest_results/")
        return run
    p = Path(arg)
    if p.exists() and p.is_dir():
        return p
    p2 = RESULTS_ROOT / arg
    if p2.exists() and p2.is_dir():
        return p2
    raise SystemExit(f"❌ run not found: {arg}")


def _fmt_table(rows: List[Dict], cols: List[str]) -> str:
    if not rows:
        return "  (no buckets met min_n threshold)\n"
    widths = {c: max(len(c), max(len(str(r.get(c, ""))) for r in rows)) for c in cols}
    head = "  " + "  ".join(c.ljust(widths[c]) for c in cols)
    sep  = "  " + "  ".join("-" * widths[c] for c in cols)
    body = "\n".join(
        "  " + "  ".join(str(r.get(c, "")).ljust(widths[c]) for c in cols)
        for r in rows
    )
    return f"{head}\n{sep}\n{body}\n"


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="calibration",
                                 description="Calibration brain (T37+T38)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name in ("latest", "factors", "timeframes", "summary"):
        sp = sub.add_parser(name)
        sp.add_argument("--run", default="latest")
        sp.add_argument("--min-n", type=int, default=5)
        sp.add_argument("--json", action="store_true")

    sp_run = sub.add_parser("run", help="inspect a specific run id")
    sp_run.add_argument("run_id")
    sp_run.add_argument("--min-n", type=int, default=5)
    sp_run.add_argument("--json", action="store_true")

    args = ap.parse_args(argv)

    run_arg = getattr(args, "run", None) or getattr(args, "run_id", "latest")
    if args.cmd == "latest":
        run_arg = "latest"
    run_dir = _resolve_run(run_arg)
    rows = load_picks(run_dir)

    cols_factor = ["bucket", "n", "wins", "win_rate", "mean_r", "total_r", "mean_return_pct"]

    if args.cmd in ("latest", "summary"):
        summ = overall_summary(rows)
        if args.json:
            print(json.dumps({"run": run_dir.name, "summary": summ,
                              "factors": per_factor_report(rows, args.min_n),
                              "timeframes": per_timeframe_report(rows, args.min_n)}, indent=2))
            return 0
        print(f"\n📊 RUN: {run_dir.name}  ·  picks: {summ['n']}  ·  win_rate: {summ['win_rate']}  ·  total_R: {summ['total_r']}\n")
        for fname, table in per_factor_report(rows, args.min_n).items():
            print(f"── factor: {fname}")
            print(_fmt_table(table, cols_factor))
        print("── timeframe (per month)")
        print(_fmt_table(per_timeframe_report(rows, args.min_n), cols_factor))
        return 0

    if args.cmd == "factors":
        rep = per_factor_report(rows, args.min_n)
        if args.json:
            print(json.dumps(rep, indent=2)); return 0
        for fname, table in rep.items():
            print(f"\n── {fname}")
            print(_fmt_table(table, cols_factor))
        return 0

    if args.cmd == "timeframes":
        rep = per_timeframe_report(rows, args.min_n)
        if args.json:
            print(json.dumps(rep, indent=2)); return 0
        print("\n── per-month attribution")
        print(_fmt_table(rep, cols_factor))
        return 0

    if args.cmd == "run":
        # treat like summary for the named run
        args.cmd = "summary"
        return main(["summary", "--run", run_dir.name,
                     *(["--min-n", str(args.min_n)] if args.min_n else []),
                     *(["--json"] if args.json else [])])

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
