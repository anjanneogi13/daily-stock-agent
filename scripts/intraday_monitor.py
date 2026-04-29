#!/usr/bin/env python3
"""
Intraday Monitor — runs every 30 min during US market hours.
1. Monitors existing morning picks for material news / price levels.
2. Scans for NEW opportunities not in morning picks.
Sends consolidated Telegram alert ONLY if something material is found.
"""
import os, sys, json, glob
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Make sibling modules importable
sys.path.insert(0, str(Path(__file__).resolve().parent))

from intraday_news import fetch_recent_news, classify_material
from intraday_scanner import scan_for_new_opportunities, get_live_quote

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
PICKS_FILE = DATA_DIR / f"picks_{TODAY}.json"
ALERTS_FILE = DATA_DIR / f"intraday_alerts_{TODAY}.json"
OUT_FILE = DATA_DIR / f"intraday_alert_{TODAY}.md"

# ──────────────────────────────────────────────────────────────────
# Load previously-sent alert fingerprints (avoid spam across runs)
# ──────────────────────────────────────────────────────────────────
def load_sent_alerts() -> set:
    if not ALERTS_FILE.exists():
        return set()
    try:
        return set(json.loads(ALERTS_FILE.read_text()))
    except Exception:
        return set()

def save_sent_alerts(alerts: set):
    ALERTS_FILE.write_text(json.dumps(sorted(alerts)))

# ──────────────────────────────────────────────────────────────────
# Load this morning's picks
# ──────────────────────────────────────────────────────────────────
def load_todays_picks() -> list:
    if not PICKS_FILE.exists():
        # try fallback: most recent picks file
        files = sorted(glob.glob(str(DATA_DIR / "picks_*.json")), reverse=True)
        if not files:
            print("[monitor] No picks file found — nothing to monitor.")
            return []
        print(f"[monitor] ⚠️  No picks_{TODAY}.json — using {files[0]}")
        return json.loads(Path(files[0]).read_text())
    return json.loads(PICKS_FILE.read_text())

# ──────────────────────────────────────────────────────────────────
# Monitor existing picks
# ──────────────────────────────────────────────────────────────────
def monitor_existing_picks(picks: list, sent_alerts: set) -> list:
    """Returns list of alert dicts for picks needing attention."""
    alerts = []
    for p in picks:
        ticker = p.get("ticker") or p.get("symbol")
        if not ticker:
            continue

        entry = float(p.get("entry", 0) or 0)
        sl = float(p.get("stop_loss", 0) or p.get("sl", 0) or 0)
        tp = float(p.get("take_profit", 0) or p.get("tp", 0) or 0)

        live = get_live_quote(ticker)
        if not live or live.get("price") is None:
            continue
        price = live["price"]

        flags = []
        # Price-level checks
        if sl > 0 and price <= sl * 1.01 and price > sl:
            flags.append(("near_sl", f"⚠️  Within 1% of SL (${sl:.2f})"))
        if sl > 0 and price <= sl:
            flags.append(("hit_sl", f"🛑 Hit Stop-Loss (${sl:.2f})"))
        if tp > 0 and entry > 0:
            halfway = entry + 0.5 * (tp - entry)
            if price >= halfway and price < tp:
                flags.append(("halfway_tp", f"✅ Halfway to TP (${tp:.2f})"))
            if price >= tp:
                flags.append(("hit_tp", f"🎯 Hit Take-Profit (${tp:.2f})"))

        # Volume spike
        if live.get("vol_ratio", 0) >= 3.0:
            flags.append(("vol_spike", f"📊 Volume spike ({live['vol_ratio']:.1f}× avg)"))

        # News check
        news = fetch_recent_news(ticker, lookback_min=45)
        material_news = []
        for n in news:
            cat = classify_material(n.get("headline", ""))
            if cat:
                material_news.append((cat, n.get("headline", "")[:120], n.get("url", "")))

        # Build alert if anything material
        if not flags and not material_news:
            continue

        change_pct = ((price - entry) / entry * 100) if entry else 0.0
        # fingerprint = ticker + sorted flags + first material headline
        fp_parts = [ticker] + sorted([f[0] for f in flags])
        if material_news:
            fp_parts.append(material_news[0][1][:60])
        fingerprint = "|".join(fp_parts)
        if fingerprint in sent_alerts:
            continue
        sent_alerts.add(fingerprint)

        alerts.append({
            "ticker": ticker,
            "price": price,
            "entry": entry,
            "change_pct": change_pct,
            "flags": flags,
            "news": material_news,
        })
    return alerts

# ──────────────────────────────────────────────────────────────────
# Build Telegram message
# ──────────────────────────────────────────────────────────────────
def build_message(monitor_alerts: list, new_opps: list) -> str:
    if not monitor_alerts and not new_opps:
        return ""

    et_now = datetime.now(timezone.utc) - timedelta(hours=5)  # rough ET (display only)
    lines = [f"⚡ *INTRADAY UPDATE* — {et_now.strftime('%H:%M')} ET\n"]

    if monitor_alerts:
        lines.append("📍 *Pick Status*\n")
        for a in monitor_alerts:
            arrow = "🟢" if a["change_pct"] >= 0 else "🔴"
            lines.append(
                f"{arrow} *{a['ticker']}* @ ${a['price']:.2f} "
                f"(entry ${a['entry']:.2f}, {a['change_pct']:+.1f}%)"
            )
            for _, msg in a["flags"]:
                lines.append(f"   {msg}")
            for cat, headline, url in a["news"][:2]:
                emoji = {"downgrade":"📉","upgrade":"📈","earnings":"💰",
                         "lawsuit":"⚖️","ma":"🤝","guidance":"📊"}.get(cat,"📰")
                lines.append(f"   {emoji} {headline}")
            lines.append("")

    if new_opps:
        lines.append("🆕 *New Opportunities Detected*\n")
        for o in new_opps:
            lines.append(
                f"🔥 *{o['ticker']}* @ ${o['price']:.2f}\n"
                f"   📈 Score: {o['score']:.1f} (was {o.get('morning_score',0):.1f})\n"
                f"   🎯 Entry ${o['entry']:.2f} • SL ${o['sl']:.2f} • TP ${o['tp']:.2f}\n"
                f"   💡 {o.get('reason','Live momentum + catalyst')}\n"
            )

    lines.append("_⚠️  Educational only. Not financial advice._")
    msg = "\n".join(lines)
    return msg[:3950] + "\n\n_(truncated)_" if len(msg) > 4000 else msg

# ──────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────
def main():
    picks = load_todays_picks()
    if not picks:
        print("[monitor] No picks to monitor — exiting.")
        return

    sent_alerts = load_sent_alerts()
    print(f"[monitor] Monitoring {len(picks)} picks. {len(sent_alerts)} alerts already sent today.")

    monitor_alerts = monitor_existing_picks(picks, sent_alerts)
    print(f"[monitor] {len(monitor_alerts)} new alerts on existing picks.")

    existing_tickers = {p.get("ticker") or p.get("symbol") for p in picks}
    new_opps = scan_for_new_opportunities(
        exclude=existing_tickers,
        sent_alerts=sent_alerts,
        max_results=3,
    )
    print(f"[monitor] {len(new_opps)} new opportunities found.")

    msg = build_message(monitor_alerts, new_opps)
    if not msg:
        print("[monitor] Nothing material — no message sent. ✅")
        return

    OUT_FILE.write_text(msg)
    save_sent_alerts(sent_alerts)
    print(f"[monitor] ✅ Alert written to {OUT_FILE} ({len(msg)} chars)")

if __name__ == "__main__":
    main()
    