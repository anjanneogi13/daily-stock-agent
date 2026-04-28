"""Sends today's picks to Telegram. Reads bot token + chat ID from env."""
import csv, os, sys, urllib.request, urllib.parse, json
from datetime import datetime
from pathlib import Path

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

if not TOKEN or not CHAT_ID:
    print("[telegram] Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID — skipping")
    sys.exit(0)

today = datetime.now().strftime("%Y-%m-%d")
rows = []
p = Path("data/picks_log.csv")
if p.exists():
    with p.open() as f:
        for r in csv.DictReader(f):
            if r.get("pick_date") == today:
                rows.append(r)

if not rows:
    msg = f"📭 *Daily Stock Picks — {today}*\n\n_No picks today (filters too strict or earnings season)._"
else:
    lines = [f"📈 *Daily Stock Picks — {today}*",
             f"_{len(rows)} picks • Regime: {rows[0].get('regime','?')} • CAPE: {rows[0].get('cape','?')}_",
             ""]
    for i, r in enumerate(rows, 1):
        try:
            entry = float(r["entry"]); sl = float(r["stop_loss"]); tp = float(r["take_profit"])
            risk = (entry - sl) / entry * 100
            reward = (tp - entry) / entry * 100
        except Exception:
            entry = sl = tp = 0; risk = reward = 0
        d2e = r.get("days_to_earnings","")
        earn = f" • 📅 {d2e}d" if d2e else ""
        lines.append(
            f"*{i}. {r['ticker']}* — score {float(r['score']):.2f}{earn}\n"
            f"   🎯 Entry: `${entry:.2f}`\n"
            f"   🛑 SL: `${sl:.2f}` (−{risk:.1f}%)\n"
            f"   💰 TP: `${tp:.2f}` (+{reward:.1f}%)\n"
            f"   📦 Qty: {r.get('qty','-')} • R:R {r.get('risk_reward','2.0')}\n"
        )
    lines.append("⚠️ _Educational only. Not financial advice._")
    msg = "\n".join(lines)

# Telegram caps messages at 4096 chars
if len(msg) > 4000:
    msg = msg[:3950] + "\n\n_(truncated)_"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
data = urllib.parse.urlencode({
    "chat_id": CHAT_ID,
    "text": msg,
    "parse_mode": "Markdown",
    "disable_web_page_preview": "true",
}).encode()

try:
    resp = urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10)
    result = json.loads(resp.read())
    if result.get("ok"):
        print(f"[telegram] ✅ Sent {len(rows)} picks to chat {CHAT_ID}")
    else:
        print(f"[telegram] ❌ API error: {result}")
        sys.exit(1)
except Exception as e:
    print(f"[telegram] ❌ Failed: {e}")
    sys.exit(1)
