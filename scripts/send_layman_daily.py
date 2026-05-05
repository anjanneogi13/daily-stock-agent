"""T52 — Daily Picks → Telegram in plain English.

REPLACES scripts/send_telegram.py (technical version) in daily-picks.yml.

Reads data/picks_log.csv for today's picks → outputs one Telegram message
per amateur user. Keeps ALL actionable data (entry/SL/TP/qty/hold time)
but wraps it in plain English.
"""
import csv, os, sys, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.layman_translator import (
    pick_to_layman, header, footer_explainer, score_to_words
)
from src.dedup_sender import should_send, mark_sent
from src.smell_faculty import sniff as _sniff, has_blocking_smell, format_for_telegram as _smell_fmt


def _is_pick_sane(pick: dict) -> tuple[bool, str]:
    """SANITY GATE — block any pick with malformed/zero financials.
    
    Returns (is_sane, reason_if_not). NEVER ship a pick that fails this.
    Last line of defense before user-facing Telegram.
    """
    def _f(k, default=0.0):
        try: return float(pick.get(k, default) or default)
        except (TypeError, ValueError): return default
    
    entry = _f("entry") or _f("buy_price")
    sl    = _f("sl")    or _f("stop_loss")
    tp    = _f("tp")    or _f("target_price") or _f("take_profit")
    
    if entry <= 0:                return False, f"entry price is {entry}"
    if sl <= 0:                   return False, f"stop_loss is {sl}"
    if tp <= 0:                   return False, f"take_profit is {tp}"
    if tp <= entry:               return False, f"tp ({tp}) <= entry ({entry})"
    if sl >= entry:               return False, f"sl ({sl}) >= entry ({entry})"
    
    risk_pct = (entry - sl) / entry * 100
    reward_pct = (tp - entry) / entry * 100
    if risk_pct <= 0:             return False, f"risk_pct is {risk_pct}"
    rr = reward_pct / risk_pct
    if rr < 1.0:                  return False, f"R/R too low ({rr:.2f}x < 1.0)"
    
    # SMELL GATE — block on CRITICAL+blocking smells (earnings tomorrow, RSI 85+, etc)
    blocker = has_blocking_smell(pick, {})
    if blocker:
        return False, f"SMELL: {blocker.code} ({blocker.message})"
    
    return True, "ok"



TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHATS = [c for c in [os.environ.get("TELEGRAM_CHAT_ID"),
                      os.environ.get("TELEGRAM_GROUP_CHAT_ID")] if c]


def _today_picks():
    path = Path("data/picks_log.csv")
    if not path.exists(): return []
    today = os.environ.get("PICK_DATE") or \
            datetime.now().strftime("%Y-%m-%d")
    rows = []
    with path.open() as f:
        for r in csv.DictReader(f):
            d = (r.get("pick_date") or "")[:10]
            if d == today:
                rows.append(r)
    return rows


def _send(text) -> bool:
    """Send text to Telegram.

    Returns True when at least one configured chat receives the message.
    Returns False only when credentials exist but every configured chat fails.

    No credentials is treated as a local dry-run success so tests/developer
    machines can render messages without failing.
    """
    if not TOKEN or not CHATS:
        print("[telegram] no creds — dry-run print only")
        print(text)
        return True

    sent_any = False
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    for chat in CHATS:
        chat_ok = False
        for parse_mode in ("Markdown", None):
            payload = {"chat_id": chat, "text": text}
            if parse_mode:
                payload["parse_mode"] = parse_mode
            data = urllib.parse.urlencode(payload).encode()
            try:
                with urllib.request.urlopen(url, data=data, timeout=20) as r:
                    if r.status == 200:
                        print(f"[telegram] chat={chat[:6]}… OK ({parse_mode or 'plain'})")
                        sent_any = True
                        chat_ok = True
                        break
                    print(f"[telegram] chat={chat[:6]}… HTTP status {r.status} ({parse_mode or 'plain'})")
            except Exception as e:
                print(f"[telegram] chat={chat[:6]}… {parse_mode or 'plain'} failed: {e}")
        if not chat_ok:
            print(f"[telegram] chat={chat[:6]}… FAILED all parse modes")
    return sent_any


def build_message(picks):
    today = datetime.now().strftime("%A, %B %d %Y")
    if not picks:
        return (header("🌅", "Today's Stock Picks", today) +
                "📭 *No picks today.* The agent didn't find anything worth recommending.\n"
                "_(This is normal on quiet market days or after losing streaks — "
                "the agent prefers to skip rather than force bad trades.)_")

    day_picks   = [p for p in picks if (p.get("trade_type","") or "").lower() == "day"]
    swing_picks = [p for p in picks if (p.get("trade_type","") or "").lower() != "day"]

    lines = [header("🌅", "Today's Stock Picks", today)]
    lines.append(f"The agent found *{len(picks)} stock(s)* worth watching today.")
    lines.append("")

    idx = 1
    if day_picks:
        lines.append("━━━━━ 🌤 *DAY TRADES* (sell before market closes) ━━━━━")
        lines.append("")
        for p in day_picks:
            _sane, _why = _is_pick_sane(p)
            if not _sane:
                print(f"[SANITY GATE] BLOCKED pick {p.get('ticker','?')}: {_why}")
                continue
            lines.append(pick_to_layman(p, idx))
            _warns = _sniff(p, {})
            if _warns:
                lines.append(_smell_fmt(_warns))
            idx += 1; lines.append("")

    if swing_picks:
        lines.append("━━━━━ 📈 *SWING TRADES* (hold a few days/weeks) ━━━━━")
        lines.append("")
        for p in swing_picks:
            _sane, _why = _is_pick_sane(p)
            if not _sane:
                print(f"[SANITY GATE] BLOCKED pick {p.get('ticker','?')}: {_why}")
                continue
            lines.append(pick_to_layman(p, idx))
            _warns = _sniff(p, {})
            if _warns:
                lines.append(_smell_fmt(_warns))
            idx += 1; lines.append("")

    lines.append(footer_explainer())
    lines.append("")
    lines.append("_Read the agent's reasoning in your evening report tonight._")
    return "\n".join(lines)


def main():
    picks = _today_picks()
    msg = build_message(picks)
    print(msg); print("")
    if not should_send(msg):
        print("[dedup] already sent — skipping")
        return 0
    if not _send(msg):
        print("[telegram] ❌ all configured chats failed — not marking sent")
        return 1

    mark_sent(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
