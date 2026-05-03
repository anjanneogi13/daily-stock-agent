"""T52 — Monthly recap → Telegram in plain English (replaces send_monthly_telegram)."""
import csv, os, sys, urllib.request, urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.layman_translator import (
    money, pct, header, footer_explainer
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHATS = [c for c in [os.environ.get("TELEGRAM_CHAT_ID"),
                      os.environ.get("TELEGRAM_GROUP_CHAT_ID")] if c]


def _safe_f(x):
    try: return float(x) if x not in (None,"") else 0
    except: return 0


def _last_month_outcomes():
    p = Path("data/picks_log.csv")
    if not p.exists(): return []
    cutoff = datetime.now().date() - timedelta(days=30)
    out = []
    with p.open() as f:
        for r in csv.DictReader(f):
            d = (r.get("pick_date") or "")[:10]
            try:
                dd = datetime.fromisoformat(d).date()
            except: continue
            if dd >= cutoff and r.get("status") not in (None,"","OPEN"):
                out.append(r)
    return out


def build_message(outcomes):
    month = datetime.now().strftime("%B %Y")
    if not outcomes:
        return (header("📆", f"{month} Recap", "monthly performance") +
                "📭 *No closed trades this month.*")

    wins = sum(1 for o in outcomes if _safe_f(o.get("pnl_dollar")) > 0)
    losses = len(outcomes) - wins
    pnl = sum(_safe_f(o.get("pnl_dollar")) for o in outcomes)
    wr = wins / len(outcomes) * 100 if outcomes else 0

    # Best/worst
    s = sorted(outcomes, key=lambda x: _safe_f(x.get("pnl_dollar")), reverse=True)
    winners = [o for o in s if _safe_f(o.get("pnl_dollar")) > 0]
    losers  = [o for o in s if _safe_f(o.get("pnl_dollar")) < 0]
    best5   = winners[:3]
    worst5  = losers[:3] if losers else []

    lines = [header("📆", f"{month} Recap", "how the agent did this month")]
    lines.append(f"📊 *{len(outcomes)} trades · {wins}W/{losses}L · win rate {wr:.0f}%*")
    lines.append(f"💰 *Net profit/loss:* {money(pnl)}")
    lines.append("")
    lines.append("🏆 *Best 3 trades:*")
    for o in best5:
        lines.append(f"  • {o.get('ticker','?')} → {money(_safe_f(o.get('pnl_dollar')))}")
    lines.append("")
    if worst5:
        lines.append("💔 *Toughest 3 trades:*")
        for o in worst5:
            lines.append(f"  • {o.get('ticker','?')} → {money(_safe_f(o.get('pnl_dollar')))}")
    else:
        lines.append("💔 *No losing trades this month* — clean sheet 🌟")
    lines.append("")
    lines.append("*🧠 Is the agent improving?*")
    if wr >= 55: lines.append("✅ Win rate is healthy — the brain is finding edges.")
    elif wr >= 45: lines.append("🟡 Win rate is okay — agent is tuning itself nightly.")
    else: lines.append("🔴 Win rate is low this month — agent has auto-paused weak strategies and will retry.")
    lines.append("")
    lines.append(footer_explainer())
    return "\n".join(lines)


def _send(text):
    if not TOKEN or not CHATS:
        print(text); return
    for chat in CHATS:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        for pm in ("Markdown", None):
            payload = {"chat_id": chat, "text": text}
            if pm: payload["parse_mode"] = pm
            try:
                data = urllib.parse.urlencode(payload).encode()
                with urllib.request.urlopen(url, data=data, timeout=20) as r:
                    if r.status == 200: print("[telegram] OK"); break
            except Exception as e:
                print(f"[telegram] {pm} failed: {e}")


def main():
    out = _last_month_outcomes()
    msg = build_message(out)
    print(msg); print("")
    _send(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
