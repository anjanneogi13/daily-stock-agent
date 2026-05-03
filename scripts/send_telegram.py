"""Sends today's picks to Telegram with DUAL-SECTION format (PR #69).

🌅 DAY TRADES section first (with max-hold time)
📈 SWING TRADES section below (multi-day hold)

PR #66: dedup_sender prevents duplicate messages (parallel cron runs)
PR #69: Dual-section format makes DAY vs SWING clear at a glance
"""
import csv, os, sys, json, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path

# Add repo root to path so we can import src/
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.dedup_sender import should_send, mark_sent
from src.auto_pause import compute_score as _pause_score, format_summary as _pause_fmt
from src.pause_state import is_paused as _is_paused, format_pause_alert as _pause_alert
from src.wisdom_base import get_kill_list as _get_kill, load_active_lessons as _get_lessons, load_active_patterns as _get_patterns

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_IDS = [c for c in [os.environ.get("TELEGRAM_CHAT_ID"),
                         os.environ.get("TELEGRAM_GROUP_CHAT_ID")] if c]
if not TOKEN or not CHAT_IDS:
    print("[telegram] Missing creds — skipping"); sys.exit(0)


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════
# ─── T24: per-pick wisdom hint (extracted to src/wisdom_hint.py) ───
try:
    from src.wisdom_hint import wisdom_hint
except Exception:
    def wisdom_hint(_t=None, **_k): return ""
# ───────────────────────────────────────────────────────────────────

def _load_watchlist_tickers():
    """Phase 2A.3: Load bullish-news tickers to mark with 🔔."""
    try:
        wl = json.loads(Path("data/watchlist.json").read_text())
        return {it["ticker"] for it in wl.get("items", []) if it.get("sentiment") == "bullish"}
    except Exception:
        return set()


WL_TICKERS = _load_watchlist_tickers()


def _wl_emoji(t):
    return "🔔 " if t in WL_TICKERS else ""


def _safe_float(val, default=0.0):
    try:
        return float(val) if val not in (None, "") else default
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=0):
    try:
        return int(float(val)) if val not in (None, "") else default
    except (ValueError, TypeError):
        return default


def _classify_pick(row):
    """PR #69: Determine if pick is DAY or SWING from CSV.
    Defaults to 'swing' for backward compat with old picks.
    """
    return (row.get("trade_type", "") or "swing").strip().lower()


# ═══════════════════════════════════════════════════════════════
# Per-pick formatters (compact day vs detailed swing)
# ═══════════════════════════════════════════════════════════════




def _format_day_pick(i, row, tag_info):
    """🌅 Day trade format — compact, emphasizes tight stop + max hold."""
    t = row["ticker"]
    entry = _safe_float(row["entry"])
    sl    = _safe_float(row["stop_loss"])
    tp    = _safe_float(row["take_profit"])
    risk_pct = (entry - sl) / entry * 100 if entry > 0 else 0
    rew_pct  = (tp - entry) / entry * 100 if entry > 0 else 0
    rr = row.get("risk_reward", "?")
    qty = row.get("qty", "?")
    score = _safe_float(row.get("score", 0))

    tag = tag_info.get("tag", "")
    reason = tag_info.get("reason", "")
    cur = tag_info.get("current_price")
    cur_str = f" → ${cur:.2f}" if cur else ""

    lines = [
        f"⚡ *{i}. {_wl_emoji(t)}{t}* — score {score:.2f} | day_score {_safe_float(row.get('day_score', 0)):.2f}"
    ]
    if tag:
        lines.append(f"   {tag} _{reason}_")
    _wh = wisdom_hint(t)
    if _wh:
        lines.append(_wh)

    lines.append(
        f"   🎯 `${entry:.2f}`{cur_str}  "
        f"🛑 `${sl:.2f}` (−{risk_pct:.2f}%)  "
        f"💰 `${tp:.2f}` (+{rew_pct:.2f}%)"
    )
    lines.append(
        f"   📦 {qty}sh · R:R {rr} · ⏱ Hold ≤4h (force EOD close)"
    )
    return "\n".join(lines) + "\n"


def _format_swing_pick(i, row, tag_info):
    """📈 Swing trade format — detailed, multi-day hold."""
    t = row["ticker"]
    entry = _safe_float(row["entry"])
    sl    = _safe_float(row["stop_loss"])
    tp    = _safe_float(row["take_profit"])
    risk_pct = (entry - sl) / entry * 100 if entry > 0 else 0
    rew_pct  = (tp - entry) / entry * 100 if entry > 0 else 0
    rr = row.get("risk_reward", "2.0")
    qty = row.get("qty", "-")
    score = _safe_float(row.get("score", 0))
    d2e = row.get("days_to_earnings", "")
    earn = f" • 📅 {d2e}d" if d2e else ""

    tag = tag_info.get("tag", "")
    reason = tag_info.get("reason", "")
    cur = tag_info.get("current_price")
    cur_str = f" (now ${cur:.2f})" if cur else ""

    lines = [f"📊 *{i}. {_wl_emoji(t)}{t}* — score {score:.2f}{earn}"]
    if tag:
        lines.append(f"   {tag} _{reason}_")
    _wh = wisdom_hint(t)
    if _wh:
        lines.append(_wh)

    lines.extend([
        f"   🎯 Entry: `${entry:.2f}`{cur_str}",
        f"   🛑 SL: `${sl:.2f}` (−{risk_pct:.1f}%)",
        f"   💰 TP: `${tp:.2f}` (+{rew_pct:.1f}%)",
        f"   📦 Qty: {qty} • R:R {rr}",
    ])

    # 3-tier scale-out display (Phase 2B.4)
    tp1 = _safe_float(row.get("tp1"))
    tp2 = _safe_float(row.get("tp2"))
    qt1 = _safe_int(row.get("qty_t1"))
    qt2 = _safe_int(row.get("qty_t2"))
    qt3 = _safe_int(row.get("qty_t3"))
    if tp1 > 0 and tp2 > 0 and (qt1 + qt2 + qt3) > 0 and entry > 0:
        tp1_pct = (tp1 - entry) / entry * 100
        tp2_pct = (tp2 - entry) / entry * 100
        lines.extend([
            f"   ├ T1 `${tp1:.2f}` (+{tp1_pct:.1f}%) × {qt1}sh — early lock",
            f"   ├ T2 `${tp2:.2f}` (+{tp2_pct:.1f}%) × {qt2}sh — bulk",
            f"   └ T3 trail × {qt3}sh — runner 🚀",
        ])

    return "\n".join(lines) + "\n"


# ═══════════════════════════════════════════════════════════════
# Build the message
# ═══════════════════════════════════════════════════════════════


def _format_monster_pick(i, row, tag_info):
    """💎 Format a monster pick — emphasize lottery sizing + wide stop."""
    ticker = row["ticker"]
    score = _safe_float(row.get("monster_score"))
    entry = _safe_float(row.get("entry"))
    sl = _safe_float(row.get("stop_loss"))
    tp = _safe_float(row.get("take_profit"))
    qty = _safe_int(row.get("qty"))
    rr = _safe_float(row.get("risk_reward"))
    sl_pct = ((sl - entry) / entry * 100) if entry else 0
    tp_pct = ((tp - entry) / entry * 100) if entry else 0
    return (
        f"💎 *{i}. {ticker}* · monster={score:.2f} · {row.get('tag','')[:18]}\n"
        f"   Entry ${entry:.2f} · SL ${sl:.2f} ({sl_pct:+.1f}%) · TP ${tp:.2f} ({tp_pct:+.1f}%)\n"
        f"   R:R {rr:.1f} · Qty {qty} (lottery sizing)"
    )


def build_message(rows, pm, today):
    """PR #69: Build dual-section message (DAY first, SWING below)."""
    # Premarket tags lookup
    tags = {x["ticker"]: x for x in pm.get("picks", [])}
    mkt = pm.get("market", {})

    if not rows:
        return f"📭 *Daily Stock Picks — {today}*\n\n_No picks today._"

    # Split picks by trade_type
    day_picks   = [r for r in rows if _classify_pick(r) == "day"]
    swing_picks = [r for r in rows if _classify_pick(r) != "day"]
    has_news = any(_wl_emoji(r["ticker"]) for r in rows)
    legend_bits = []
    if has_news: legend_bits.append("🔔 news-driven")
    legend_bits.append("⚡ DAY · 📊 SWING")
    legend = " • " + " • ".join(legend_bits)

    # Header
    lines = [
        f"📈 *Daily Stock Picks — {today}*",
        f"_{len(rows)} picks ({len(day_picks)} day · {len(swing_picks)} swing)"
        f" • Regime: {rows[0].get('regime','?')}"
        f" • CAPE: {rows[0].get('cape','?')}{legend}_",
        ""
    ]

    # Market summary (unchanged from before)
    if mkt:
        lines.append(
            f"🌐 *Market:* SPY {mkt.get('spy_change_pct',0):+.2f}% • "
            f"QQQ {mkt.get('qqq_change_pct',0):+.2f}% • "
            f"SOXX {mkt.get('soxx_change_pct',0):+.2f}% • "
            f"VIX {mkt.get('vix','?')}"
        )
        for w in mkt.get("warnings", []):
            lines.append(w)
        if mkt.get("global_action") == "skip_all":
            lines.append("\n🚫 *SKIP ALL TRADES TODAY* — high market risk\n")
        elif mkt.get("global_action") == "half":
            lines.append("\n⚠️ *Reduce all positions by 50% today*\n")
        lines.append("")

    # ═══ DAY TRADES SECTION ═══
    if day_picks:
        lines.append(f"🌅 *DAY TRADES ({len(day_picks)})* — Close by EOD")
        lines.append("─" * 30)
        for i, r in enumerate(day_picks, 1):
            lines.append(_format_day_pick(i, r, tags.get(r["ticker"], {})))
        lines.append("")

    # ═══ 💎 MONSTER HUNTS SECTION ═══
    monster_picks = [r for r in rows if str(r.get("is_monster","")).lower() == "true"]
    if monster_picks:
        lines.append(f"💎 *MONSTER HUNTS ({len(monster_picks)})* — Asymmetric setups, lottery sizing")
        lines.append("─" * 30)
        for i, r in enumerate(monster_picks, 1):
            lines.append(_format_monster_pick(i, r, tags.get(r["ticker"], {})))
        lines.append("")

    # ═══ SWING TRADES SECTION ═══
    if swing_picks:
        lines.append(f"📈 *SWING TRADES ({len(swing_picks)})* — Multi-day hold")
        lines.append("─" * 30)
        for i, r in enumerate(swing_picks, 1):
            lines.append(_format_swing_pick(i, r, tags.get(r["ticker"], {})))

    # Footer with news-driven recap
    if has_news:
        news_tickers = sorted({r["ticker"] for r in rows if r["ticker"] in WL_TICKERS})
        lines.append(f"📰 *News-driven:* {', '.join(news_tickers)}")

    # Pillar 4: active kill-list (auto-cooldown visibility)
    try:
        _kl = _get_kill()
        if _kl:
            from datetime import datetime as _dt
            _now = _dt.now()
            _items = []
            for _tk, _e in sorted(_kl.items()):
                try:
                    _exp = _dt.fromisoformat(_e.get("expires_at", ""))
                    _days = max(0, (_exp.date() - _now.date()).days)
                    _items.append(f"{_tk} ({_days}d)")
                except Exception:
                    _items.append(_tk)
            lines.append("")
            lines.append(f"🥶 *Cooled-off:* {', '.join(_items)}")
    except Exception:
        pass  # never block daily message

    # Pillar 2: top active wisdom lessons (high-confidence only)
    try:
        _lessons = _get_lessons(min_confidence=0.7)[:2]
        if _lessons:
            lines.append("")
            lines.append("🧠 *Wisdom in play:*")
            for _L in _lessons:
                _txt = _L.get("text", "")[:90]
                lines.append(f"  • {_txt}")
            _np = len(_get_patterns())
            if _np:
                lines.append(f"  _({_np} active pattern{'s' if _np != 1 else ''} informing scores)_")
    except Exception:
        pass

    # Pillar 4 prep: pause signal in daily summary (T13 May 3 2026)
    try:
        _ps = _pause_score()
        lines.append("")
        for _l in _pause_fmt(_ps).split("\n"):
            lines.append(_l)
        if _ps.get("enforced"):
            lines.append("🚨 _Enforce-mode active — agent may auto-pause_")
    except Exception as _pe:
        pass  # Never block the daily message on pause-signal failure

    lines.append("")
    lines.append("⚠️ _Educational only. Not financial advice._")
    lines.append("🔧 _PR #66+#67+#68+#69 active · pause v0.1_")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# Main execution
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    today = datetime.now().strftime("%Y-%m-%d")

    # ═══════════════════════════════════════════════════════════════
    # PAUSE-DAY: agent is paused → send pause alert instead of picks
    # ═══════════════════════════════════════════════════════════════
    _ps = _is_paused()
    if _ps["paused"]:
        pause_msg = (
            f"📭 *Daily Stock Picks — {today}*\n"
            f"\n"
            f"{_pause_alert(_ps)}"
        )
        # Reuse send loop below with this message
        msg = pause_msg
        if not should_send(msg, window_minutes=120):
            print("[telegram] ⏭ Pause alert already sent within 2h — skipping")
            sys.exit(0)
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        sent_any = False
        for _cid in CHAT_IDS:
            payload = {"chat_id": _cid, "text": msg, "parse_mode": "Markdown"}
            data = urllib.parse.urlencode(payload).encode()
            try:
                resp = urllib.request.urlopen(
                    urllib.request.Request(url, data=data), timeout=10)
                if json.loads(resp.read()).get("ok"):
                    print(f"[telegram] ✅ Pause alert sent to {_cid[:6]}...")
                    sent_any = True
            except Exception as _e:
                print(f"[telegram] ⚠ Pause alert failed: {_e}")
        if sent_any:
            mark_sent(msg, window_minutes=120)
        sys.exit(0)

    # Load picks
    rows = []
    p = Path("data/picks_log.csv")
    if p.exists():
        rows = [r for r in csv.DictReader(p.open()) if r.get("pick_date") == today]

    # Load premarket tags
    pm = {}
    pm_path = Path("data/premarket_check.json")
    if pm_path.exists():
        try:
            pm = json.loads(pm_path.read_text())
        except Exception:
            pm = {}

    msg = build_message(rows, pm, today)

    # Truncate if too long for Telegram
    if len(msg) > 4000:
        msg = msg[:3950] + "\n\n_(truncated)_"

    # 🚨 PR #66: Dedup check
    if not should_send(msg, window_minutes=60):
        print("[telegram] ⏭ Skipped — same content sent within last 60 min (dedup)")
        sys.exit(0)

    # Send to all chat IDs
    # FIX (2026-05-02): Telegram returns HTTP 400 when message contains
    # unescaped Markdown chars (_ * [ ] etc). Strategy: try Markdown first,
    # if that fails fall back to plain text so picks ALWAYS get delivered.
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    all_sent = True

    def _try_send(chat_id: str, text: str, parse_mode: str | None) -> tuple[bool, str]:
        payload = {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        data = urllib.parse.urlencode(payload).encode()
        try:
            resp = urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=10)
            result = json.loads(resp.read())
            if result.get("ok"):
                return True, "ok"
            return False, str(result)
        except urllib.error.HTTPError as he:
            try:
                body = he.read().decode()
            except Exception:
                body = ""
            return False, f"HTTP {he.code} {body[:200]}"
        except Exception as e:
            return False, str(e)

    for _cid in CHAT_IDS:
        # Attempt 1: Markdown (preferred — preserves formatting)
        ok, info = _try_send(_cid, msg, parse_mode="Markdown")
        if ok:
            print(f"[telegram] ✅ Sent to {_cid[:6]}... (Markdown)")
            continue
        # Attempt 2: Plain text fallback (NEVER fail silently)
        print(f"[telegram] ⚠ Markdown failed ({info[:120]}); retrying as plain text...")
        ok, info = _try_send(_cid, msg, parse_mode=None)
        if ok:
            print(f"[telegram] ✅ Sent to {_cid[:6]}... (plain text fallback)")
        else:
            print(f"[telegram] ❌ Plain text also failed: {info[:200]}")
            all_sent = False

    # Mark sent only if at least one chat received it
    if all_sent:
        mark_sent(msg, window_minutes=60)
        print("[telegram] ✅ Marked sent in dedup log")
    else:
        print("[telegram] ⚠ Not marking sent — some chats failed")
        sys.exit(1)