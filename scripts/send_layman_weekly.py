"""T52 — Weekly recap → Telegram in plain English.

NEW — currently NO weekly Telegram message is sent (only GitHub issue).
Wired into weekly_report.yml.
"""
import csv, os, sys, urllib.request, urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.layman_translator import (
    money, pct, verdict_line, header, footer_explainer, outcome_to_layman
)
from src.performance_source_separation import LAYMAN_PERFORMANCE_SOURCE_NOTE, is_watch_only_row

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHATS = [c for c in [os.environ.get("TELEGRAM_CHAT_ID"),
                      os.environ.get("TELEGRAM_GROUP_CHAT_ID")] if c]


def _last_week_outcomes():
    p = Path("data/picks_log.csv")
    if not p.exists(): return []
    cutoff = datetime.now().date() - timedelta(days=7)
    out = []
    with p.open() as f:
        for r in csv.DictReader(f):
            d = (r.get("pick_date") or "")[:10]
            try:
                dd = datetime.fromisoformat(d).date()
            except: continue
            if dd >= cutoff and r.get("status") not in (None,"","OPEN") and not is_watch_only_row(r):
                out.append(r)
    return out


def _safe_f(x):
    try: return float(x) if x not in (None,"") else 0
    except: return 0


def build_message(outcomes):
    period = f"{(datetime.now()-timedelta(days=7)).strftime('%b %d')} → {datetime.now().strftime('%b %d')}"
    if not outcomes:
        return (header("📅", "This Week's Performance", period) +
                "📭 *No closed trades this week.*\n\n" +
                LAYMAN_PERFORMANCE_SOURCE_NOTE)

    wins = sum(1 for o in outcomes if _safe_f(o.get("pnl_dollar")) > 0)
    losses = len(outcomes) - wins
    pnl = sum(_safe_f(o.get("pnl_dollar")) for o in outcomes)

    # Best & worst
    sorted_o = sorted(outcomes, key=lambda x: _safe_f(x.get("pnl_dollar")), reverse=True)
    best, worst = sorted_o[0], sorted_o[-1]

    lines = [header("📅", "This Week's Performance", period)]
    lines.append(verdict_line(wins, losses, pnl))
    lines.append("")
    lines.append(f"📊 *Week summary:* {len(outcomes)} trades closed · {wins}W/{losses}L · *{money(pnl)}*")
    lines.append("")
    lines.append(f"🏆 *Best pick:* {best.get('ticker','?')} ({money(_safe_f(best.get('pnl_dollar')))})")
    lines.append(f"💔 *Worst pick:* {worst.get('ticker','?')} ({money(_safe_f(worst.get('pnl_dollar')))})")
    lines.append("")
    lines.append("_Over the weekend the agent will study this week's trades and quietly tune itself._")
    lines.append("_Sunday evening you'll get a separate 'Self-Improvement Report' in plain English._")
    lines.append(LAYMAN_PERFORMANCE_SOURCE_NOTE)
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
                    if r.status == 200: print(f"[telegram] OK"); break
            except Exception as e:
                print(f"[telegram] {pm} failed: {e}")


def main():
    out = _last_week_outcomes()
    msg = build_message(out)
    print(msg); print("")
    _send(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
