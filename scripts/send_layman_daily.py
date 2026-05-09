"""T52 — Daily Picks → Telegram in plain English.

REPLACES scripts/send_telegram.py (technical version) in daily-picks.yml.

Reads data/picks_log.csv for today's picks → outputs one Telegram message
per amateur user. Keeps ALL actionable data (entry/SL/TP/qty/hold time)
but wraps it in plain English.
"""
import csv, json, os, sys, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.layman_translator import (
    pick_to_layman, header, footer_explainer, score_to_words
)
from src.dedup_sender import should_send, mark_sent
from scripts.validate_daily_no_pick import validate_no_pick_report
from src.official_artifact_loader import (
    enrich_pick_rows_with_artifacts,
    official_pick_summary_for_date,
    validate_official_artifacts_for_rows,
)
from src.smell_faculty import sniff as _sniff, has_blocking_smell, format_for_telegram as _smell_fmt


def _today_date() -> str:
    return os.environ.get("PICK_DATE") or datetime.now().strftime("%Y-%m-%d")


def validate_official_user_output_state(picks: list[dict], no_pick_report: dict | None = None) -> list[str]:
    """Fail-closed validation before any user-facing Telegram output.

    If picks exist, every pick must have a matching valid official artifact.
    If no picks exist, a valid official no-pick artifact must exist.
    """
    date_str = _today_date()
    no_pick_report = no_pick_report or {}

    if picks:
        return validate_official_artifacts_for_rows(picks, date_str)

    if not no_pick_report:
        return [f"no picks logged and no valid official no-pick artifact found for {date_str}"]

    return validate_no_pick_report(no_pick_report)


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
    
    # SMELL GATE — block on CRITICAL+blocking smells (earnings tomorrow, RSI 85+, etc).
    # Priority 10: official-artifact rows have already passed the official
    # production gates before artifact creation. Keep numeric sanity checks above,
    # but do not let legacy output-only smell checks suppress a validated artifact.
    if not pick.get("official_artifact_present"):
        blocker = has_blocking_smell(pick, {})
        if blocker:
            return False, f"SMELL: {blocker.code} ({blocker.message})"
    
    return True, "ok"



def _is_watch_only(pick: dict) -> bool:
    tag = str(pick.get("premarket_tag") or "").upper()
    actionable = pick.get("premarket_actionable")
    actionable_false = actionable is False or str(actionable).strip().lower() == "false"
    row_watch_only = str(pick.get("watch_only") or "").strip().lower() in {"1", "true", "yes"}
    return "WATCH ONLY" in tag or actionable_false or row_watch_only


def _watch_only_message(pick: dict, idx: int) -> str:
    ticker = pick.get("ticker", "?")
    reason = (
        pick.get("watch_only_reason")
        or pick.get("premarket_reason")
        or "fresh quote unavailable"
    )
    return (
        f"*{idx}. {ticker}* — 👀 *WATCH ONLY*\n"
        f"Reason: {reason}.\n"
        "No buy price is actionable from this alert. "
        "Require a fresh live quote before considering entry."
    )


TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHATS = [c for c in [os.environ.get("TELEGRAM_CHAT_ID"),
                      os.environ.get("TELEGRAM_GROUP_CHAT_ID")] if c]


def _premarket_tags() -> dict:
    """Return premarket-check metadata keyed by ticker."""
    path = Path("data/premarket_check.json")
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except Exception:
        return {}
    return {
        (p.get("ticker") or "").strip(): p
        for p in data.get("picks", [])
        if (p.get("ticker") or "").strip()
    }


def _today_picks():
    path = Path("data/picks_log.csv")
    if not path.exists(): return []
    today = _today_date()
    tags = _premarket_tags()
    rows = []
    with path.open() as f:
        for r in csv.DictReader(f):
            d = (r.get("pick_date") or "")[:10]
            if d == today:
                meta = tags.get((r.get("ticker") or "").strip())
                if meta:
                    r["premarket_tag"] = meta.get("tag", "")
                    r["premarket_reason"] = meta.get("reason", "")
                    r["premarket_current_price"] = meta.get("current_price")
                    r["premarket_actionable"] = meta.get("actionable")
                rows.append(r)
    return enrich_pick_rows_with_artifacts(rows, today)


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


def _today_no_pick_report() -> dict:
    today = _today_date()
    path = Path(f"data/daily_picks_no_pick_report_{today}.json")
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def build_message(picks, no_pick_report=None):
    no_pick_report = no_pick_report or {}
    today = datetime.now().strftime("%A, %B %d %Y")
    if not picks:
        if no_pick_report:
            summary = (
                no_pick_report.get("human_readable_summary")
                or no_pick_report.get("reason")
                or "No qualified official pick today."
            )
            cause = no_pick_report.get("primary_no_pick_cause", "unknown")
            readiness = no_pick_report.get("data_readiness_status", "unknown")
            provider = no_pick_report.get("provider_status", "unknown")
            return (
                header("🌅", "Today's Stock Picks", today)
                + "📭 *Official no-pick today.*\n"
                + f"Reason: {summary}\n"
                + f"Primary cause: `{cause}`\n"
                + f"Data readiness: `{readiness}`\n"
                + f"Provider status: `{provider}`\n\n"
                + "_This is a valid safety outcome. The agent prefers no trade over a forced bad trade._"
            )
        return (header("🌅", "Today's Stock Picks", today) +
                "📭 *No picks today.* The agent didn't find anything worth recommending.\n"
                "_(This is normal on quiet market days or after losing streaks — "
                "the agent prefers to skip rather than force bad trades.)_")

    day_picks   = [p for p in picks if (p.get("trade_type","") or "").lower() == "day"]
    swing_picks = [p for p in picks if (p.get("trade_type","") or "").lower() != "day"]

    lines = [header("🌅", "Today's Stock Picks", today)]
    official_count = sum(1 for p in picks if p.get("official_artifact_present"))
    summary = official_pick_summary_for_date(os.environ.get("PICK_DATE") or datetime.now().strftime("%Y-%m-%d"))
    if official_count:
        lines.append(
            f"The agent found *{len(picks)} official stock pick(s)* today. "
            f"All shown picks have validated official decision artifacts."
        )
        if summary.get("contract_version"):
            lines.append(f"Decision contract: `{summary.get('contract_version')}`")
    else:
        lines.append(f"The agent found *{len(picks)} stock(s)* worth watching today.")
        lines.append("⚠️ Official pick artifacts were not found for these rows.")
    lines.append("")

    idx = 1
    if day_picks:
        lines.append("━━━━━ 🌤 *DAY TRADES* (sell before market closes) ━━━━━")
        lines.append("")
        for p in day_picks:
            if _is_watch_only(p):
                lines.append(_watch_only_message(p, idx))
                idx += 1; lines.append("")
                continue
            _sane, _why = _is_pick_sane(p)
            if not _sane:
                print(f"[SANITY GATE] BLOCKED pick {p.get('ticker','?')}: {_why}")
                continue
            lines.append(pick_to_layman(p, idx))
            if p.get("official_selection_reason"):
                lines.append(f"🧾 *Official reason:* {p.get('official_selection_reason')}")
            if p.get("official_decision_id") or p.get("official_artifact_id"):
                lines.append(f"🔎 *Official trace:* `{p.get('official_decision_id') or p.get('official_artifact_id')}`")
            if p.get("official_risk_flags"):
                lines.append("⚠️ *Official risk flags:* " + ", ".join(map(str, p.get("official_risk_flags") or [])))
            _warns = _sniff(p, {})
            if _warns:
                lines.append(_smell_fmt(_warns))
            idx += 1; lines.append("")

    if swing_picks:
        lines.append("━━━━━ 📈 *SWING TRADES* (hold a few days/weeks) ━━━━━")
        lines.append("")
        for p in swing_picks:
            if _is_watch_only(p):
                lines.append(_watch_only_message(p, idx))
                idx += 1; lines.append("")
                continue
            _sane, _why = _is_pick_sane(p)
            if not _sane:
                print(f"[SANITY GATE] BLOCKED pick {p.get('ticker','?')}: {_why}")
                continue
            lines.append(pick_to_layman(p, idx))
            if p.get("official_selection_reason"):
                lines.append(f"🧾 *Official reason:* {p.get('official_selection_reason')}")
            if p.get("official_decision_id") or p.get("official_artifact_id"):
                lines.append(f"🔎 *Official trace:* `{p.get('official_decision_id') or p.get('official_artifact_id')}`")
            if p.get("official_risk_flags"):
                lines.append("⚠️ *Official risk flags:* " + ", ".join(map(str, p.get("official_risk_flags") or [])))
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
    no_pick_report = _today_no_pick_report()
    validation_errors = validate_official_user_output_state(picks, no_pick_report=no_pick_report)
    if validation_errors:
        print("[official-output] ❌ blocked user-facing Telegram output")
        for error in validation_errors:
            print(f"- {error}")
        return 1

    msg = build_message(picks, no_pick_report=no_pick_report)
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
