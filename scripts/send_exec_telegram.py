"""Sends today's execution X-ray report to Telegram."""
import os, sys, json, subprocess, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_IDS = [c for c in [os.environ.get("TELEGRAM_CHAT_ID"), os.environ.get("TELEGRAM_GROUP_CHAT_ID")] if c]
if not TOKEN or not CHAT_IDS:
    print("[telegram] Missing creds"); sys.exit(0)

# Phase 2A.3: Load current watchlist tickers to mark news-driven picks
def _load_watchlist_tickers():
    try:
        wl = json.loads(Path("data/watchlist.json").read_text())
        return {it["ticker"] for it in wl.get("items", []) if it.get("sentiment") == "bullish"}
    except Exception:
        return set()

WL_TICKERS = _load_watchlist_tickers()
def _wl_emoji(t):
    return "🔔 " if t in WL_TICKERS else ""

date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
jp = Path(f"data/exec_report_{date}.json")
if not jp.exists():
    print(f"[telegram] No exec report for {date}"); sys.exit(0)

data = json.loads(jp.read_text())
picks = data.get("picks", [])
if not picks:
    print("[telegram] No picks in report"); sys.exit(0)

tp = [r for r in picks if r["status"]=="TP_HIT"]
sl = [r for r in picks if r["status"]=="SL_HIT"]
op = [r for r in picks if r["status"]=="OPEN"]
nf = [r for r in picks if r["status"]=="NOT_FILLED"]
nd = [r for r in picks if r["status"]=="NO_DATA"]

header_extra = f"\n🔔 = news-driven (watchlist)" if WL_TICKERS else ""
lines = [f"📊 *Execution Report — {date}*{header_extra}\n",
         f"✅ TP: {len(tp)} | 🛑 SL: {len(sl)} | ⏳ Open: {len(op)} | ⚠️ Unfilled: {len(nf)}\n"]

for r in picks:
    t = r["ticker"]; s = r["status"]
    if s == "NO_DATA":
        lines.append(f"{_wl_emoji(t)}*{t}* — _no data_"); continue
    if s == "NOT_FILLED":
        lines.append(f"⚠️ {_wl_emoji(t)}*{t}* — limit not hit (missed by {r['missed_by_pct']:+.2f}%)"); continue
    if s == "TP_HIT":
        lines.append(
            f"✅ {_wl_emoji(t)}*{t}* TP +{r['tp_pct']:.2f}% • left {r['further_after_tp_pct']:+.2f}% on table\n"
            f"   _no-TP close: {r['no_tp_close_pct']:+.2f}%_")
    elif s == "SL_HIT":
        lines.append(
            f"🛑 {_wl_emoji(t)}*{t}* SL {r['sl_pct']:.2f}% • dropped {r['further_after_sl_pct']:+.2f}% more\n"
            f"   _no-SL worst: {r['no_sl_worst_pct']:.2f}%, close: {r['no_sl_close_pct']:+.2f}%_")
    else:  # OPEN
        lines.append(
            f"⏳ {_wl_emoji(t)}*{t}* close {r['close_ret_pct']:+.2f}% • MFE {r['mfe_pct']:+.2f}% MAE {r['mae_pct']:+.2f}%")

filled = [r for r in picks if r["status"] not in ("NOT_FILLED","NO_DATA")]
if filled:
    avg_mfe = sum(r["mfe_pct"] for r in filled)/len(filled)
    avg_mae = sum(r["mae_pct"] for r in filled)/len(filled)
    lines.append(f"\n📈 Avg MFE {avg_mfe:+.2f}% • Avg MAE {avg_mae:+.2f}%")

msg = "\n".join(lines)
if len(msg) > 4000: msg = msg[:3950] + "\n_(truncated)_"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
for _cid in CHAT_IDS:
    body = urllib.parse.urlencode({
        "chat_id": _cid, "text": msg,
        "parse_mode": "Markdown", "disable_web_page_preview": "true",
    }).encode()
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=10)
        res = json.loads(resp.read())
        print(f"[telegram] {'✅ Sent exec report' if res.get('ok') else '❌ '+str(res)}")
    except Exception as e:
        print(f"[telegram] ❌ {e}"); sys.exit(1)
