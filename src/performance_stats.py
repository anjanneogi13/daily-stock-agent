"""Computes performance statistics from picks_log.csv."""
import csv
from pathlib import Path
from collections import defaultdict
from rich.console import Console
from rich.table import Table

LOG_PATH = Path("data/picks_log.csv")


def compute_stats() -> dict:
    if not LOG_PATH.exists():
        return {"total": 0}

    with LOG_PATH.open() as f:
        rows = list(csv.DictReader(f))

    closed = [r for r in rows if r["evaluation_status"] in ("tp_hit", "sl_hit", "expired")
              and r["actual_return_pct"] not in ("", None)]

    if not closed:
        return {"total": len(rows), "closed": 0, "pending": len(rows)}

    tp = [r for r in closed if r["evaluation_status"] == "tp_hit"]
    sl = [r for r in closed if r["evaluation_status"] == "sl_hit"]
    exp = [r for r in closed if r["evaluation_status"] == "expired"]

    returns = [float(r["actual_return_pct"]) for r in closed]
    r_mults = [float(r["r_multiple"]) for r in closed if r["r_multiple"] not in ("", None)]
    wins = [x for x in r_mults if x > 0]
    losses = [x for x in r_mults if x <= 0]

    by_tag = defaultdict(lambda: {"n": 0, "wins": 0, "total_r": 0.0})
    for r in closed:
        tag = r.get("tag", "")
        by_tag[tag]["n"] += 1
        rm = float(r["r_multiple"]) if r["r_multiple"] not in ("", None) else 0
        if rm > 0:
            by_tag[tag]["wins"] += 1
        by_tag[tag]["total_r"] += rm

    return {
        "total": len(rows),
        "pending": len([r for r in rows if r["evaluation_status"] == "pending"]),
        "closed": len(closed),
        "tp_hits": len(tp),
        "sl_hits": len(sl),
        "expired": len(exp),
        "win_rate": round(len(wins) / len(closed) * 100, 1) if closed else 0,
        "avg_return_pct": round(sum(returns) / len(returns), 2),
        "best_return_pct": round(max(returns), 2),
        "worst_return_pct": round(min(returns), 2),
        "avg_r_multiple": round(sum(r_mults) / len(r_mults), 2) if r_mults else 0,
        "total_r_multiple": round(sum(r_mults), 2),
        "expectancy_per_trade": round(sum(r_mults) / len(r_mults), 2) if r_mults else 0,
        "by_tag": dict(by_tag),
        "best_picks": sorted(closed, key=lambda r: float(r["r_multiple"] or 0), reverse=True)[:5],
        "worst_picks": sorted(closed, key=lambda r: float(r["r_multiple"] or 0))[:5],
    }


def print_dashboard():
    s = compute_stats()
    console = Console()

    if s.get("total", 0) == 0:
        console.print("[yellow]No picks logged yet. Run main.py first.[/yellow]")
        return

    console.print("\n[bold cyan]📊 Performance Dashboard[/bold cyan]\n")

    if s.get("closed", 0) == 0:
        console.print(f"  Total picks: {s['total']} (all pending — wait for evaluation)")
        return

    # Summary table
    t = Table(title="Overall Statistics", show_header=True, header_style="bold magenta")
    t.add_column("Metric", style="cyan")
    t.add_column("Value", justify="right")
    t.add_row("Total picks", str(s["total"]))
    t.add_row("Closed (evaluated)", str(s["closed"]))
    t.add_row("Pending", str(s["pending"]))
    t.add_row("─" * 25, "─" * 15)
    t.add_row("✅ TP hits", f"[green]{s['tp_hits']}[/green]")
    t.add_row("❌ SL hits", f"[red]{s['sl_hits']}[/red]")
    t.add_row("⏰ Expired", str(s["expired"]))
    t.add_row("─" * 25, "─" * 15)
    color = "green" if s["win_rate"] >= 50 else "yellow" if s["win_rate"] >= 35 else "red"
    t.add_row("Win rate", f"[{color}]{s['win_rate']}%[/{color}]")
    t.add_row("Avg return", f"{s['avg_return_pct']:+.2f}%")
    t.add_row("Best pick", f"[green]{s['best_return_pct']:+.2f}%[/green]")
    t.add_row("Worst pick", f"[red]{s['worst_return_pct']:+.2f}%[/red]")
    t.add_row("─" * 25, "─" * 15)
    exp_color = "green" if s["expectancy_per_trade"] > 0 else "red"
    t.add_row("Avg R multiple", f"[{exp_color}]{s['avg_r_multiple']:+.2f}R[/{exp_color}]")
    t.add_row("Total R captured", f"[{exp_color}]{s['total_r_multiple']:+.2f}R[/{exp_color}]")
    t.add_row("Expectancy/trade", f"[{exp_color}]{s['expectancy_per_trade']:+.2f}R[/{exp_color}]")
    console.print(t)

    # By tag
    if s["by_tag"]:
        t2 = Table(title="\nPerformance by Tag", show_header=True, header_style="bold magenta")
        t2.add_column("Tag", style="cyan")
        t2.add_column("N", justify="right")
        t2.add_column("Win Rate", justify="right")
        t2.add_column("Total R", justify="right")
        for tag, data in sorted(s["by_tag"].items(), key=lambda x: -x[1]["total_r"]):
            wr = data["wins"] / data["n"] * 100 if data["n"] else 0
            t2.add_row(tag or "(none)", str(data["n"]), f"{wr:.0f}%", f"{data['total_r']:+.2f}R")
        console.print(t2)

    # Best & worst
    t3 = Table(title="\n🏆 Best Picks", show_header=True)
    t3.add_column("Date"); t3.add_column("Ticker"); t3.add_column("Status")
    t3.add_column("Return", justify="right"); t3.add_column("R", justify="right")
    for p in s["best_picks"]:
        t3.add_row(p["pick_date"], p["ticker"], p["evaluation_status"],
                   f"[green]{p['actual_return_pct']}%[/green]", f"{p['r_multiple']}R")
    console.print(t3)

    t4 = Table(title="\n💀 Worst Picks", show_header=True)
    t4.add_column("Date"); t4.add_column("Ticker"); t4.add_column("Status")
    t4.add_column("Return", justify="right"); t4.add_column("R", justify="right")
    for p in s["worst_picks"]:
        t4.add_row(p["pick_date"], p["ticker"], p["evaluation_status"],
                   f"[red]{p['actual_return_pct']}%[/red]", f"{p['r_multiple']}R")
    console.print(t4)
