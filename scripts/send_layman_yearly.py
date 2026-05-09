"""T52 — Yearly recap → Telegram in plain English.

NEW. Fires Jan 1 each year via yearly_recap.yml.
"""
import csv, os, sys, urllib.request, urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.layman_translator import money, pct, header, footer_explainer
from src.performance_source_separation import LAYMAN_PERFORMANCE_SOURCE_NOTE, is_watch_only_row

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHATS = [c for c in [os.environ.get("TELEGRAM_CHAT_ID"),
                      os.environ.get("TELEGRAM_GROUP_CHAT_ID")] if c]


def _safe_f(x):
    try: return float(x) if x not in (None,"") else 0
    except: return 0


def _year_outcomes(year: int):
    p = Path("data/picks_log.csv")
    if not p.exists(): return []
    out = []
    with p.open() as f:
        for r in csv.DictReader(f):
            d = (r.get("pick_date") or "")[:10]
            if d.startswith(str(year)) and r.get("status") not in (None,"","OPEN") and not is_watch_only_row(r):
                out.append(r)
    return out


def _count_brain_mutations(year: int) -> int:
    p = Path("data/learning_journal.jsonl")
    if not p.exists(): return 0
    import json
    n = 0
    for line in p.read_text().splitlines():
        if not line.strip(): continue
        try:
            e = json.loads(line)
            if str(e.get("ts","")).startswith(str(year)): n += 1
        except: pass
    return n


def build_message(year: int):
    outcomes = _year_outcomes(year)
    mutations = _count_brain_mutations(year)
    if not outcomes:
        return (header("🎊", f"{year} Year-in-Review", "first full year of the agent") +
                f"📭 No trades to recap for {year}.\n\n" +
                LAYMAN_PERFORMANCE_SOURCE_NOTE)

    wins = sum(1 for o in outcomes if _safe_f(o.get("pnl_dollar")) > 0)
    losses = len(outcomes) - wins
    pnl = sum(_safe_f(o.get("pnl_dollar")) for o in outcomes)
    wr = wins / len(outcomes) * 100

    s = sorted(outcomes, key=lambda x: _safe_f(x.get("pnl_dollar")), reverse=True)
    winners = [o for o in s if _safe_f(o.get("pnl_dollar")) > 0]
    losers  = [o for o in s if _safe_f(o.get("pnl_dollar")) < 0]

    lines = [header("🎊", f"{year} Year-in-Review", "the full annual story")]
    lines.append(f"📊 *Total trades:* {len(outcomes)}")
    lines.append(f"🏆 *Wins:* {wins}  ·  💔 *Losses:* {losses}  ·  *Win rate:* {wr:.0f}%")
    lines.append(f"💰 *Net profit/loss:* {money(pnl)}")
    lines.append("")
    lines.append(f"🧠 *Brain self-improvements made this year:* {mutations}")
    lines.append("")
    lines.append("🌟 *Top 5 winning picks:*")
    if winners:
        for o in winners[:5]:
            lines.append(f"  • {o.get('ticker','?')} → {money(_safe_f(o.get('pnl_dollar')))}")
    else:
        lines.append("  _(no winners this year)_")
    lines.append("")
    lines.append("📉 *Toughest 5 losing picks (lessons learned):*")
    if losers:
        for o in losers[:5]:
            lines.append(f"  • {o.get('ticker','?')} → {money(_safe_f(o.get('pnl_dollar')))}")
    else:
        lines.append("  _(no losses this year — clean sheet!)_")
    lines.append("")
    if wr >= 55 and pnl > 0:
        verdict = "✅ A strong year. The agent learned from every trade and made real progress."
    elif pnl > 0:
        verdict = "🟢 A profitable year despite mixed wins. Risk management did its job."
    else:
        verdict = "🔴 A tough year. The agent has auto-disabled losing strategies and rebuilt."
    lines.append(f"*Verdict:* {verdict}")
    lines.append("")
    lines.append(f"_Onwards to {year+1} — the brain is smarter than it was last January._")
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
                    if r.status == 200: print("[telegram] OK"); break
            except Exception as e:
                print(f"[telegram] {pm} failed: {e}")


def main():
    year = int(os.environ.get("RECAP_YEAR") or (datetime.now().year - 1))
    msg = build_message(year)
    print(msg); print("")
    _send(msg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
