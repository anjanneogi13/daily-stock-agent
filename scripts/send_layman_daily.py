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


def _send(text):
    if not TOKEN or not CHATS:
        print("[telegram] no creds — dry-run print only")
        print(text); return
    for chat in CHATS:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        for parse_mode in ("Markdown", None):
            payload = {"chat_id": chat, "text": text}
            if parse_mode: payload["parse_mode"] = parse_mode
            data = urllib.parse.urlencode(payload).encode()
            try:
                with urllib.request.urlopen(url, data=data, timeout=20) as r:
                    if r.status == 200:
                        print(f"[telegram] chat={chat[:6]}… OK ({parse_mode or 'plain'})")
                        break
            except Exception as e:
                print(f"[telegram] {parse_mode} failed: {e}")


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
            lines.append(pick_to_layman(p, idx)); idx += 1; lines.append("")

    if swing_picks:
        lines.append("━━━━━ 📈 *SWING TRADES* (hold a few days/weeks) ━━━━━")
        lines.append("")
        for p in swing_picks:
            lines.append(pick_to_layman(p, idx)); idx += 1; lines.append("")

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
    _send(msg)
    mark_sent(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
