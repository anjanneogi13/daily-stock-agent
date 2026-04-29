#!/usr/bin/env python3
"""Intraday Monitor — runs every 30 min during US market hours."""
import os, sys, json, csv as _csv
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent))

from intraday_news import fetch_recent_news, classify_material
from intraday_scanner import scan_for_new_opportunities, get_live_quote

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
PICKS_CSV = DATA_DIR / "picks_log.csv"
ALERTS_FILE = DATA_DIR / f"intraday_alerts_{TODAY}.json"
OUT_FILE = DATA_DIR / f"intraday_alert_{TODAY}.md"

def load_sent_alerts() -> set:
    if not ALERTS_FILE.exists():
        return set()
    try:
        return set(json.loads(ALERTS_FILE.read_text()))
    except Exception:
        return set()

def save_sent_alerts(alerts: set):
    ALERTS_FILE.write_text(json.dumps(sorted(alerts)))

def load_todays_picks() -> list:
    """Load picks from picks_log.csv. Falls back to most recent date if today's missing."""
    if not PICKS_CSV.exists():
        print("[monitor] No picks_log.csv — nothing to monitor.")
        return []
    rows = list(_csv.DictReader(PICKS_CSV.open()))
    if not rows:
        return []
    today_rows = [r for r in rows if r.get("pick_date", "").strip() == TODAY]
    if not today_rows:
        all_dates = sorted({r.get("pick_date", "") for r in rows if r.get("pick_date")})
        if not all_dates:
            return []
        last_date = all_dates[-1]
        print(f"[monitor] No picks for {TODAY} — using last available date {last_date}")
        today_rows = [r for r in rows if r.get("pick_date", "") == last_date]
    picks = []
    for r in today_rows:
        status = (r.get("evaluation_status", "") or "").strip().lower()
        if status not in ("pending", "open", ""):
            continue
        ticker = (r.get("ticker") or "").strip()
        if not ticker:
            continue
        try:
            picks.append({
                "ticker": ticker,
                "entry":       float(r.get("entry") or 0),
                "stop_loss":   float(r.get("stop_loss") or 0),
                "take_profit": float(r.get("take_profit") or 0),
            })
        except ValueError:
            continue
    return picks

def monitor_existing_picks(picks: list, sent_alerts: set) -> list:
    alerts = []
    for p in picks:
        ticker = p["ticker"]
        entry, sl, tp = p["entry"], p["stop_loss"], p["take_profit"]
        live = get_live_quote(ticker)
        if not live or live.get("price") is None:
            continue
        price = live["price"]
        flags = []
        if sl > 0 and price <= sl * 1.01 and price > sl:
            flags.append(("near_sl", f"Within 1% of SL (${sl:.2f})"))
        if sl > 0 and price <= sl:
            flags.append(("hit_sl", f"Hit Stop-Loss (${sl:.2f})"))
        if tp > 0 and entry > 0:
            halfway = entry + 0.5 * (tp - entry)
            if price >= halfway and price < tp:
                flags.append(("halfway_tp", f"Halfway to TP (${tp:.2f})"))
            if price >= tp:
                flags.append(("hit_tp", f"Hit Take-Profit (${tp:.2f})"))
        if live.get("vol_ratio", 0) >= 3.0:
            flags.append(("vol_spike", f"Volume spike ({live['vol_ratio']:.1f}x avg)"))
        news = fetch_recent_news(ticker, lookback_min=45)
        material_news = []
        for n in news:
            cat = classify_material(n.get("headline", ""))
            if cat:
                material_news.append((cat, n.get("headline", "")[:120], n.get("url", "")))
        if not flags and not material_news:
            continue
        change_pct = ((price - entry) / entry * 100) if entry else 0.0
        fp_parts = [ticker] + sorted([f[0] for f in flags])
        if material_news:
            fp_parts.append(material_news[0][1][:60])
        fingerprint = "|".join(fp_parts)
        if fingerprint in sent_alerts:
            continue
        sent_alerts.add(fingerprint)
        alerts.append({"ticker": ticker, "price": price, "entry": entry,
                       "change_pct": change_pct, "flags": flags, "news": material_news})
    return alerts

def build_message(monitor_alerts: list, new_opps: list) -> str:
    if not monitor_alerts and not new_opps:
        return ""
    et_now = datetime.now(timezone.utc) - timedelta(hours=5)
    lines = [f"*INTRADAY UPDATE* — {et_now.strftime('%H:%M')} ET\n"]
    if monitor_alerts:
        lines.append("*Pick Status*\n")
        for a in monitor_alerts:
            arrow = "UP" if a["change_pct"] >= 0 else "DOWN"
            lines.append(f"{arrow} *{a['ticker']}* @ ${a['price']:.2f} "
                         f"(entry ${a['entry']:.2f}, {a['change_pct']:+.1f}%)")
            for _, msg in a["flags"]:
                lines.append(f"   - {msg}")
            for cat, headline, url in a["news"][:2]:
                lines.append(f"   - [{cat}] {headline}")
            lines.append("")
    if new_opps:
        lines.append("*New Opportunities Detected*\n")
        for o in new_opps:
            lines.append(f"*{o['ticker']}* @ ${o['price']:.2f}\n"
                         f"   Score: {o['score']:.1f}\n"
                         f"   Entry ${o['entry']:.2f} | SL ${o['sl']:.2f} | TP ${o['tp']:.2f}\n"
                         f"   {o.get('reason','Live momentum')}\n")
    lines.append("_Educational only. Not financial advice._")
    msg = "\n".join(lines)
    return msg[:3950] + "\n\n_(truncated)_" if len(msg) > 4000 else msg

def main():
    picks = load_todays_picks()
    if not picks:
        print("[monitor] No picks to monitor — exiting.")
        return
    sent_alerts = load_sent_alerts()
    print(f"[monitor] Monitoring {len(picks)} picks. {len(sent_alerts)} alerts already sent.")
    monitor_alerts = monitor_existing_picks(picks, sent_alerts)
    print(f"[monitor] {len(monitor_alerts)} new alerts on existing picks.")
    existing_tickers = {p["ticker"] for p in picks}
    new_opps = scan_for_new_opportunities(exclude=existing_tickers,
                                          sent_alerts=sent_alerts, max_results=3)
    print(f"[monitor] {len(new_opps)} new opportunities found.")
    msg = build_message(monitor_alerts, new_opps)
    if not msg:
        print("[monitor] Nothing material — no message sent.")
        return
    OUT_FILE.write_text(msg)
    save_sent_alerts(sent_alerts)
    print(f"[monitor] Alert written to {OUT_FILE} ({len(msg)} chars)")

if __name__ == "__main__":
    main()
