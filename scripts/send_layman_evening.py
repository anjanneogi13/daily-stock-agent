"""T52 — Evening Performance → Telegram in plain English.

REPLACES send_dashboard_telegram.py + send_exec_telegram.py in evaluate.yml.
"""
import csv, json, os, sys, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.layman_translator import (
    outcome_to_layman, verdict_line, beat_market_line,
    money, pct, header, footer_explainer
)
from src.dedup_sender import should_send, mark_sent
from src.performance_source_separation import LAYMAN_PERFORMANCE_SOURCE_NOTE, is_watch_only_row

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHATS = [c for c in [os.environ.get("TELEGRAM_CHAT_ID"),
                      os.environ.get("TELEGRAM_GROUP_CHAT_ID")] if c]


def _today_outcomes():
    """Return picks that CLOSED today (sl_hit/tp_hit/expired/day_close),
    regardless of when they were originally picked. Bug fix 2026-05-05:
      (1) was reading 'status' column — CSV uses 'evaluation_status'
      (2) was filtering on pick_date == today — should be evaluated_on == today
          so that a pick made yesterday and closed today actually shows up."""
    p = Path("data/picks_log.csv")
    if not p.exists(): return []
    today = os.environ.get("PICK_DATE") or datetime.now().strftime("%Y-%m-%d")
    # day_close = day trades force-closed at the bell (was missing, so day
    # trades never appeared in the evening report at all).
    CLOSED = ("tp_hit", "sl_hit", "expired", "unreachable_entry", "day_close")
    from datetime import timedelta
    cutoff = (datetime.strptime(today, "%Y-%m-%d") - timedelta(days=3)).strftime("%Y-%m-%d")
    out = []
    with p.open() as f:
        for r in csv.DictReader(f):
            evaluated_on = (r.get("evaluated_on") or "")[:10]
            status = (r.get("evaluation_status") or "").lower()
            # Lookback 3 days so trades closed Fri/Sat get shown in Mon's report,
            # AND so a same-day intraday SL hit (evaluated_on=yesterday because
            # eval cron runs after market close UTC = next morning SGT) shows up.
            if status in CLOSED and evaluated_on >= cutoff and not is_watch_only_row(r):
                out.append(r)
    return out


def _spy_change_today():
    p = Path(f"data/exec_report_{datetime.now().strftime('%Y-%m-%d')}.json")
    if not p.exists(): return None
    try:
        return json.loads(p.read_text()).get("market", {}).get("spy_change_pct")
    except Exception: return None


def build_message(outcomes):
    today = datetime.now().strftime("%A, %B %d %Y")
    if not outcomes:
        return (header("🌆", "Today's Performance", today) +
                "📭 *No closed trades to report yet.*\n"
                "_(Either no picks today, or picks are still open and will close tomorrow.)_\n\n" +
                LAYMAN_PERFORMANCE_SOURCE_NOTE)

    # Compute pnl per row from CSV fields first, so wins/losses below are
    # counted by ACTUAL money made, not by which exit label was recorded.
    for o in outcomes:
        if not o.get("pnl_dollar"):
            ret = _safe_f(o.get("actual_return_pct"))
            ent = _safe_f(o.get("entry"))
            qty = _safe_f(o.get("qty")) or _safe_f(o.get("position_size"))
            o["pnl_dollar"] = ent * qty * ret / 100

    # unreachable_entry = no position was ever taken → not a win or a loss.
    no_fills = [o for o in outcomes
                if (o.get("evaluation_status", "") or "").lower() == "unreachable_entry"]
    trades = [o for o in outcomes if o not in no_fills]

    # Fix (issue: 'agent couldn't count any wins'): a trade that made money
    # counts as a WIN whatever its exit label (tp_hit, day_close, expired).
    # Previously only tp_hit counted, so profitable exits showed as losses.
    wins = sum(1 for o in trades if _safe_f(o.get("pnl_dollar")) > 0)
    losses = len(trades) - wins
    total_pnl = sum(_safe_f(o.get("pnl_dollar")) for o in trades)
    cost_basis = sum(_safe_f(o.get("entry",0)) * _safe_f(o.get("qty",0)) for o in trades)
    agent_pct = (total_pnl / max(1, cost_basis)) * 100 if cost_basis else 0
    spy = _spy_change_today()

    lines = [header("🌆", "Today's Performance", today)]
    lines.append(verdict_line(wins, losses, total_pnl))
    lines.append("")
    results = f"📊 *Results:* {wins} wins · {losses} losses · *Total: {money(total_pnl)}* ({pct(agent_pct)})"
    if no_fills:
        results += f" · {len(no_fills)} not filled"
    lines.append(results)
    bm = beat_market_line(agent_pct, spy)
    if bm: lines.append(bm)
    lines.append("")
    lines.append("━━━━━ *What happened with each pick* ━━━━━")
    lines.append("")
    for o in outcomes:
        lines.append(outcome_to_layman(o))
    lines.append("")
    lines.append("_Tomorrow morning the agent will use today's results to refine its picks._")
    lines.append(LAYMAN_PERFORMANCE_SOURCE_NOTE)
    lines.append(footer_explainer())
    return "\n".join(lines)


def _safe_f(x):
    try: return float(x) if x not in (None,"") else 0
    except: return 0


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
                    if r.status == 200:
                        print(f"[telegram] {chat[:6]}… OK"); break
            except Exception as e:
                print(f"[telegram] {pm} failed: {e}")


def main():
    outcomes = _today_outcomes()
    msg = build_message(outcomes)
    print(msg); print("")
    if not should_send(msg):
        print("[dedup] already sent"); return 0
    _send(msg)
    mark_sent(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
