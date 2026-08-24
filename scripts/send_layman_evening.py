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
from src.trade_state import (
    load_ledger, closed_on, summarize, pnl_dollar,
    OUTCOME_WIN, OUTCOME_LOSS, OUTCOME_FLAT, OUTCOME_NO_TRADE, OUTCOME_UNVERIFIED,
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHATS = [c for c in [os.environ.get("TELEGRAM_CHAT_ID"),
                      os.environ.get("TELEGRAM_GROUP_CHAT_ID")] if c]


def _report_date() -> str:
    return os.environ.get("PICK_DATE") or datetime.now().strftime("%Y-%m-%d")


def _today_outcomes():
    """Official (non-watch-only) positions whose terminal transition happened
    exactly on the report date — a pure projection of the ledger (§7).

    STRICT DAILY SCOPING (Cluster D): the old 3-day lookback re-listed every
    stale close for days and let mass-expired legacy rows (the recurring
    CDNS…BZH block) dump into every "today" report. Daily = closed today.
    """
    today = _report_date()
    rows = load_ledger()
    return [r for r in closed_on(rows, today) if not is_watch_only_row(r)]


def _today_research_outcomes():
    """Watch-only reference rows closed on the report date — surfaced in a
    separate labeled section (never blended into the headline counts)."""
    today = _report_date()
    rows = load_ledger()
    return [r for r in closed_on(rows, today) if is_watch_only_row(r)]


def _spy_change_today():
    p = Path(f"data/exec_report_{datetime.now().strftime('%Y-%m-%d')}.json")
    if not p.exists(): return None
    try:
        return json.loads(p.read_text()).get("market", {}).get("spy_change_pct")
    except Exception: return None


def build_message(outcomes, research_outcomes=None):
    today = datetime.now().strftime("%A, %B %d %Y")
    research_outcomes = research_outcomes or []
    if not outcomes and not research_outcomes:
        return (header("🌆", "Today's Performance", today) +
                "📭 *No closed trades to report yet.*\n"
                "_(Either no picks today, or picks are still open and will close tomorrow.)_\n\n" +
                LAYMAN_PERFORMANCE_SOURCE_NOTE)

    # §7: buckets come from the single source of truth (trade_state), which
    # classifies by realized return — a ≈$0 time-exit is FLAT, never a loss,
    # and a profitable exit is a WIN whatever its exit label.
    for o in outcomes:
        if not o.get("pnl_dollar"):
            o["pnl_dollar"] = pnl_dollar(o)

    s = summarize(outcomes)
    wins, losses, flats = s["wins"], s["losses"], s["flats"]
    no_fills, unverified = s["no_trades"], s["unverified"]
    total_pnl = s["total_pnl"]
    realized = s["buckets"][OUTCOME_WIN] + s["buckets"][OUTCOME_LOSS] + s["buckets"][OUTCOME_FLAT]
    cost_basis = sum(_safe_f(o.get("entry",0)) * _safe_f(o.get("qty",0)) for o in realized)
    agent_pct = (total_pnl / max(1, cost_basis)) * 100 if cost_basis else 0
    spy = _spy_change_today()

    lines = [header("🌆", "Today's Performance", today)]
    lines.append(verdict_line(wins, losses, total_pnl))
    lines.append("")
    results = (f"📊 *Results:* {wins} wins · {losses} losses · {flats} flat · "
               f"*Total: {money(total_pnl)}* ({pct(agent_pct)})")
    if no_fills:
        results += f" · {len(s['buckets'][OUTCOME_NO_TRADE])} not filled"
    if unverified:
        results += f" · {unverified} settled unverified (no price data)"
    lines.append(results)
    bm = beat_market_line(agent_pct, spy)
    if bm: lines.append(bm)
    lines.append("")
    if outcomes:
        lines.append("━━━━━ *What happened with each pick* ━━━━━")
        lines.append("")
        for o in outcomes:
            lines.append(outcome_to_layman(o))
        lines.append("")
    if research_outcomes:
        lines.append("━━━━━ *Watch-only research outcomes* ━━━━━")
        lines.append("_Reference levels only — no position was actionable. "
                     "Not counted in the headline results above._")
        for o in research_outcomes:
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
    research = _today_research_outcomes()
    msg = build_message(outcomes, research)
    print(msg); print("")
    if not should_send(msg):
        print("[dedup] already sent"); return 0
    _send(msg)
    mark_sent(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
