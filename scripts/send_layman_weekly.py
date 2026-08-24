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
from src.trade_state import (
    load_ledger, closed_between, summarize, pnl_dollar,
    OUTCOME_WIN, OUTCOME_LOSS, OUTCOME_FLAT,
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHATS = [c for c in [os.environ.get("TELEGRAM_CHAT_ID"),
                      os.environ.get("TELEGRAM_GROUP_CHAT_ID")] if c]


def _last_week_outcomes():
    """Official positions whose terminal transition happened in the last 7
    days — a pure projection of the ledger (§7).

    Bug fixes (Cluster D / §7 "52 vs 0 vs 14" contradiction):
      (1) was reading a nonexistent 'status' column (CSV uses
          'evaluation_status'), so this report ALWAYS said "No closed trades
          this week" even when trades closed;
      (2) was scoping by pick_date — a week view must scope by CLOSE date
          (evaluated_on), same axis as the daily view, so daily sums and the
          weekly total reconcile.
    """
    end = datetime.now().date()
    start = end - timedelta(days=7)
    rows = load_ledger()
    return [r for r in closed_between(rows, start.isoformat(), end.isoformat())
            if not is_watch_only_row(r)]


def _safe_f(x):
    try: return float(x) if x not in (None,"") else 0
    except: return 0


def build_message(outcomes):
    period = f"{(datetime.now()-timedelta(days=7)).strftime('%b %d')} → {datetime.now().strftime('%b %d')}"
    if not outcomes:
        return (header("📅", "This Week's Performance", period) +
                "📭 *No closed trades this week.*\n\n" +
                LAYMAN_PERFORMANCE_SOURCE_NOTE)

    for o in outcomes:
        if not o.get("pnl_dollar"):
            o["pnl_dollar"] = pnl_dollar(o)

    # §7: same bucket taxonomy as the daily view (flat ≠ loss) so
    # daily sums, this weekly view, and the hypothesis review agree.
    s = summarize(outcomes)
    wins, losses, flats = s["wins"], s["losses"], s["flats"]
    pnl = s["total_pnl"]
    realized = s["buckets"][OUTCOME_WIN] + s["buckets"][OUTCOME_LOSS] + s["buckets"][OUTCOME_FLAT]

    lines = [header("📅", "This Week's Performance", period)]
    lines.append(verdict_line(wins, losses, pnl))
    lines.append("")
    summary = (f"📊 *Week summary:* {s['closed']} trades closed · "
               f"{wins}W/{losses}L/{flats}F · *{money(pnl)}*")
    if s["no_trades"]:
        summary += f" · {s['no_trades']} not filled"
    if s["unverified"]:
        summary += f" · {s['unverified']} settled unverified"
    lines.append(summary)
    lines.append("")
    if realized:
        sorted_o = sorted(realized, key=lambda x: _safe_f(x.get("pnl_dollar")), reverse=True)
        best, worst = sorted_o[0], sorted_o[-1]
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
