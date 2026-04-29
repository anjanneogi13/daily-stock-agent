"""Sends today's picks to Telegram with premarket tags."""
import csv, os, sys, json, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_IDS = [c for c in [os.environ.get("TELEGRAM_CHAT_ID"), os.environ.get("TELEGRAM_GROUP_CHAT_ID")] if c]
if not TOKEN or not CHAT_IDS:
    print("[telegram] Missing creds — skipping"); sys.exit(0)

today = datetime.now().strftime("%Y-%m-%d")

# Load picks
rows = []
p = Path("data/picks_log.csv")
if p.exists():
    rows = [r for r in csv.DictReader(p.open()) if r.get("pick_date") == today]

# Load premarket tags (optional)
pm = {}
pm_path = Path("data/premarket_check.json")
if pm_path.exists():
    try:
        pm = json.loads(pm_path.read_text())
    except Exception:
        pm = {}
tags = {x["ticker"]: x for x in pm.get("picks", [])}
mkt = pm.get("market", {})

if not rows:
    msg = f"📭 *Daily Stock Picks — {today}*\n\n_No picks today._"
else:
    lines = [f"📈 *Daily Stock Picks — {today}*",
             f"_{len(rows)} picks • Regime: {rows[0].get('regime','?')} • CAPE: {rows[0].get('cape','?')}_",
             ""]
    # Market summary
    if mkt:
        lines.append(f"🌐 *Market:* SPY {mkt.get('spy_change_pct',0):+.2f}% • QQQ {mkt.get('qqq_change_pct',0):+.2f}% • SOXX {mkt.get('soxx_change_pct',0):+.2f}% • VIX {mkt.get('vix','?')}")
        for w in mkt.get("warnings", []):
            lines.append(w)
        if mkt.get("global_action") == "skip_all":
            lines.append("\n🚫 *SKIP ALL TRADES TODAY* — high market risk\n")
        elif mkt.get("global_action") == "half":
            lines.append("\n⚠️ *Reduce all positions by 50% today*\n")
        lines.append("")

    # Per-pick
    for i, r in enumerate(rows, 1):
        try:
            entry = float(r["entry"]); sl = float(r["stop_loss"]); tp = float(r["take_profit"])
            risk = (entry - sl) / entry * 100
            reward = (tp - entry) / entry * 100
        except Exception:
            entry = sl = tp = 0; risk = reward = 0
        d2e = r.get("days_to_earnings","")
        earn = f" • 📅 {d2e}d" if d2e else ""
        t = tags.get(r["ticker"], {})
        tag = t.get("tag", "")
        reason = t.get("reason", "")
        cur = t.get("current_price")
        cur_str = f" (now ${cur:.2f})" if cur else ""

        lines.append(
            f"*{i}. {r['ticker']}* — score {float(r['score']):.2f}{earn}\n"
            f"   {tag} _{reason}_\n" if tag else f"*{i}. {r['ticker']}* — score {float(r['score']):.2f}{earn}\n"
        )
        lines.append(
            f"   🎯 Entry: `${entry:.2f}`{cur_str}\n"
            f"   🛑 SL: `${sl:.2f}` (−{risk:.1f}%)\n"
            f"   💰 TP: `${tp:.2f}` (+{reward:.1f}%)\n"
            f"   📦 Qty: {r.get('qty','-')} • R:R {r.get('risk_reward','2.0')}\n"
        )
    lines.append("⚠️ _Educational only. Not financial advice._")
    msg = "\n".join(lines)

if len(msg) > 4000:
    msg = msg[:3950] + "\n\n_(truncated)_"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
for _cid in CHAT_IDS:
    data = urllib.parse.urlencode({
        "chat_id": _cid, "text": msg,
        "parse_mode": "Markdown", "disable_web_page_preview": "true",
    }).encode()
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10)
        result = json.loads(resp.read())
        print(f"[telegram] {'✅ Sent' if result.get('ok') else '❌ '+str(result)}")
    except Exception as e:
        print(f"[telegram] ❌ {e}"); sys.exit(1)
