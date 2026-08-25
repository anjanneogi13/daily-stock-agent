#!/usr/bin/env python3
"""Intraday Monitor — runs every 30 min during US market hours."""
import os, sys, json, csv as _csv
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))           # for sibling scripts (intraday_news, intraday_scanner)
sys.path.insert(0, str(_HERE.parent))    # for src.* (repo root)

from intraday_news import fetch_recent_news, classify_material
from intraday_scanner import (
    scan_for_new_opportunities,
    get_live_quote,
    append_opening_range_observations,
    append_intraday_momentum_observations,
    append_opening_range_run_status,
    refresh_opening_range_bar_artifacts_for_observations,
)
from src.trailing_stop import compute_trailing_sl, trail_status
from src.picks_csv import update_pick_row
from src.adaptive_tp import should_raise_tp, append_raise_audit, last_raise_ts
from src.adaptive_sl import should_tighten_sl, append_tighten_audit, last_tighten_ts
from src.price_sanity import validate_quote, log_quarantine
from src.trade_state import (
    is_open as _row_is_open,
    max_hold_days as _max_hold_days,
    provenance_label as _provenance_label,
)

# 🗓 T51 — Market calendar guard
try:
    from src.market_calendar import is_trading_day as _is_td, reason_market_closed as _why
    from datetime import datetime
    import zoneinfo
    _now_et = datetime.now(zoneinfo.ZoneInfo("America/New_York"))
    if not _is_td(_now_et):
        print(f"🗓 US market CLOSED ({_why(_now_et)}) — intraday monitor skipping")
        if __name__ == "__main__":
            import sys; sys.exit(0)
except ImportError:
    pass  # zoneinfo missing, proceed
except Exception as _e:
    print(f"[market-calendar] guard failed: {_e} — proceeding")


ET = ZoneInfo("America/New_York")
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
PICKS_CSV = DATA_DIR / "picks_log.csv"
ALERTS_FILE = DATA_DIR / f"intraday_alerts_{TODAY}.json"
OUT_FILE = DATA_DIR / f"intraday_alert_{TODAY}.md"

def load_sent_alerts() -> set:
    if not ALERTS_FILE.exists():
        return set()
    try:
        return set(json.loads(ALERTS_FILE.read_text()))
    except Exception:
        return set()

def save_sent_alerts(alerts: set):
    ALERTS_FILE.write_text(json.dumps(sorted(alerts)))

def load_todays_picks() -> list:
    """Load the monitored set from picks_log.csv (Cluster C — deterministic,
    complete coverage).

    Monitored set = EVERY open (non-terminal) position with an established
    entry whose hold horizon has not been exceeded — today's picks AND
    carryovers from prior days. Positions past their horizon belong to the
    end-of-day evaluator's force-close path, not intraday monitoring.

    Each pick carries `pick_date` (so closes update the correct row —
    position identity = ticker + open_date + source) and a `provenance`
    label ("official pick 2026-08-17 · carryover") for the report.
    """
    if not PICKS_CSV.exists():
        print("[monitor] No picks_log.csv — nothing to monitor.")
        return []
    rows = list(_csv.DictReader(PICKS_CSV.open()))
    if not rows:
        return []
    picks = []
    for r in rows:
        if not _row_is_open(r):
            continue
        ticker = (r.get("ticker") or "").strip()
        pick_date = (r.get("pick_date") or "").strip()
        if not ticker or not pick_date or pick_date > TODAY:
            continue
        try:
            age_days = (datetime.strptime(TODAY, "%Y-%m-%d").date()
                        - datetime.strptime(pick_date, "%Y-%m-%d").date()).days
        except ValueError:
            continue
        if age_days > _max_hold_days(r.get("trade_type", "")):
            # Overdue → handled by the evaluator's EXPIRED_OVERDUE force-close.
            continue
        try:
            entry = float(r.get("entry") or 0)
            if entry <= 0:
                continue  # no established entry → informational only, not a position
            picks.append({
                "ticker": ticker,
                "pick_date":   pick_date,
                "provenance":  _provenance_label(r, today=TODAY),
                "entry":       entry,
                "stop_loss":   float(r.get("stop_loss") or 0),
                "take_profit": float(r.get("take_profit") or 0),
                # Persisted trailing/adaptive state (informational levels).
                # Without these, every 30-min run restarted trailing from
                # scratch because p.get(...) always returned None.
                "original_sl":  r.get("original_sl") or "",
                "current_sl":   r.get("current_sl") or "",
                "current_tp":   r.get("current_tp") or "",
                "peak_price":   r.get("peak_price") or "",
                "peak_rsi":     r.get("peak_rsi") or "",
                "tp_raises":    r.get("tp_raises") or "",
                "sl_tightens":  r.get("sl_tightens") or "",
            })
        except ValueError:
            continue
    return picks

def _close_pick_in_csv(ticker: str, pick: dict, exit_price: float,
                       status: str, today_str: str) -> None:
    """Mark a pick CLOSED in picks_log.csv with same column shape as
    the end-of-day evaluator (src/pick_evaluator.evaluate_pending).

    Added 2026-05-05 to fix the bug where intraday_monitor detected SL/TP
    hits and alerted on Telegram but never wrote the close to CSV. Effect:
    the same pick alerted 4× the same day, and end-of-day was the only
    thing that ever closed a pick.

    Idempotency: caller MUST check pick is still pending before calling.
    load_todays_picks() already filters non-pending picks, providing the
    primary idempotency guard, and update_pick_row refuses to overwrite a
    terminal row (write-once), providing the second guard.

    Args:
      ticker:     stock ticker
      pick:       in-memory pick dict (needs entry, original_sl, pick_date)
      exit_price: SL or TP level (NOT live tick — matches evaluator semantics)
      status:     "sl_hit" or "tp_hit"
      today_str:  YYYY-MM-DD evaluation date (close date, NOT the row key)
    """
    entry = float(pick.get("entry") or 0)
    original_sl = float(pick.get("original_sl") or pick.get("stop_loss") or 0)
    if entry <= 0:
        print(f"[close] {ticker} entry={entry} invalid — skipping CSV write")
        return
    # Position identity fix (Cluster C): key the CSV update on the pick's OWN
    # pick_date, not today's date. Previously carryover positions (pick_date
    # < today) could never be closed intraday — update_pick_row silently
    # found no row, so TP hits (e.g. MRNA 2026-08-19) were alerted but never
    # booked, and the position kept printing all day.
    row_date = (pick.get("pick_date") or today_str).strip()
    actual_return_pct = (exit_price - entry) / entry * 100
    risk_per_share = entry - original_sl
    r_multiple = ((exit_price - entry) / risk_per_share) if risk_per_share > 0 else 0.0
    update_pick_row(row_date, ticker, {
        "evaluation_status":  status,
        "evaluated_on":       today_str,
        "exit_price":         round(exit_price, 4),
        "actual_return_pct":  round(actual_return_pct, 4),
        "r_multiple":         round(r_multiple, 4),
    })
    print(f"[close] {ticker} → {status} @ ${exit_price:.2f} "
          f"({actual_return_pct:+.2f}%, {r_multiple:+.2f}R)")



def monitor_existing_picks(picks: list, sent_alerts: set) -> list:
    alerts = []
    for p in picks:
        ticker = p["ticker"]
        entry, sl, tp = p["entry"], p["stop_loss"], p["take_profit"]
        live = get_live_quote(ticker)
        if not live or live.get("price") is None:
            continue
        price = live["price"]

        # ─── Cluster F: quote sanity gate on every consumed price ───
        # Reference = the position's own recent history (gated peak) or its
        # entry. An implausible print (e.g. MRNA quoted +86%…+176% intraday)
        # is quarantined: hold state, book nothing, fabricate no movement.
        peak_ref = float(p.get("peak_price") or 0)
        reference = peak_ref if peak_ref > 0 else entry
        q_check = validate_quote(price, reference)
        if not q_check["ok"]:
            log_quarantine(ticker, price, reference, q_check,
                           context="intraday_monitor", data_dir=DATA_DIR)
            fingerprint = f"{ticker}|quote_quarantined"
            print(f"[quarantine] {ticker}: ${price} vs ref ${reference} "
                  f"({q_check['reason']}, dev={q_check['deviation_pct']}%) — holding state")
            if fingerprint not in sent_alerts:
                sent_alerts.add(fingerprint)
                note = q_check.get("suspected_action") or "implausible print vs recent history"
                alerts.append({
                    "ticker": ticker, "price": price, "entry": entry,
                    "change_pct": 0.0, "provenance": p.get("provenance", ""),
                    "flags": [("quote_quarantined",
                               f"⚠️ Quote ${price:.2f} quarantined ({note}) — "
                               f"stale quote, unverified; position state held")],
                    "news": [],
                })
            continue

        # Phase 2B.2: update peak price + trailing SL per check
        # Use module TODAY, not wall-clock date, so tests/backfills/manual
        # monitoring runs update the same pick_date that load_todays_picks()
        # selected. Wall-clock date caused close writes to miss rows.
        today_str = TODAY
        original_sl = float(p.get("original_sl") or sl)
        current_sl = float(p.get("current_sl") or sl)
        peak_price = float(p.get("peak_price") or entry)
        new_peak = max(peak_price, price)
        new_sl, did_raise = compute_trailing_sl(entry, new_peak, current_sl)
        # Persist updates if peak rose or SL got raised
        updates = {}
        if new_peak > peak_price:
            updates["peak_price"] = new_peak
        if did_raise:
            updates["current_sl"] = new_sl
            updates["trail_active"] = "true"
        if updates:
            update_pick_row(today_str, ticker, updates)
        # Issue fix (wrong win/loss records): the trailed/tightened SL and
        # raised TP are INFORMATIONAL ONLY (current_sl/current_tp columns +
        # alert flags). Hit detection and CSV closes below always use the
        # ORIGINAL predicted SL/TP so recorded outcomes match the plan sent
        # in the morning — same semantics as src/pick_evaluator.py.
        # Previously `sl = new_sl` here made the monitor close picks at the
        # updated SL, so a pick that later hit the original TP was recorded
        # as an sl_hit loss and wins were never counted.
        informational_sl = new_sl

        flags = []
        if sl > 0 and price <= sl * 1.01 and price > sl:
            flags.append(("near_sl", f"Within 1% of SL (${sl:.2f})"))
        if sl > 0 and price <= sl:
            flags.append(("hit_sl", f"Hit Stop-Loss (${sl:.2f})"))
            _close_pick_in_csv(ticker, p, exit_price=sl,
                               status="sl_hit", today_str=today_str)
        if tp > 0 and entry > 0:
            halfway = entry + 0.5 * (tp - entry)
            if price >= halfway and price < tp:
                flags.append(("halfway_tp", f"Halfway to TP (${tp:.2f})"))
            if price >= tp:
                flags.append(("hit_tp", f"Hit Take-Profit (${tp:.2f})"))
                _close_pick_in_csv(ticker, p, exit_price=tp,
                                   status="tp_hit", today_str=today_str)
        if live.get("vol_ratio", 0) >= 3.0:
            flags.append(("vol_spike", f"Volume spike ({live['vol_ratio']:.1f}x avg)"))
        if did_raise:
            flags.append(("trail_raise", f"🔒 Trailing SL reference raised to ${new_sl:.2f} (locked +{((new_sl-entry)/entry*100):.1f}%) — official SL for records stays ${sl:.2f}"))

        # Phase 2B.3: adaptive TP raise (momentum-driven) — informational
        # only: updates current_tp column + alert, never the official TP
        # used for hit detection and outcome records.
        try:
            current_tp = float(p.get("current_tp") or tp)
            current_rsi = live.get("rsi")
            vol_ratio = live.get("vol_ratio")
            tp_raises_json = p.get("tp_raises") or "[]"
            should_r, new_tp, reason = should_raise_tp(
                entry=entry,
                current_price=price,
                current_tp=current_tp,
                current_rsi=current_rsi,
                vol_ratio=vol_ratio,
                last_raise_iso=last_raise_ts(tp_raises_json),
            )
            if should_r:
                updated_audit = append_raise_audit(tp_raises_json, new_tp, reason)
                update_pick_row(today_str, ticker, {
                    "current_tp": new_tp,
                    "tp_raises": updated_audit,
                })
                flags.append(("tp_raise", f"🚀 Stretch TP reference raised to ${new_tp:.2f} ({reason}) — official TP for records stays ${tp:.2f}"))
        except Exception as e:
            print(f"[adaptive_tp] {ticker} skipped: {e}")

        # Phase 2B.5: adaptive SL tighten (momentum-fading, profit-protect)
        # — informational only, same rule as the trailing SL above.
        try:
            current_rsi = live.get("rsi")
            vol_ratio = live.get("vol_ratio")
            stored_peak_rsi = float(p.get("peak_rsi") or 0)
            new_peak_rsi = max(stored_peak_rsi, current_rsi or 0)
            sl_tightens_json = p.get("sl_tightens") or "[]"
            should_t, new_sl_t, reason_t = should_tighten_sl(
                entry=entry,
                current_price=price,
                current_sl=informational_sl,
                current_rsi=current_rsi,
                peak_rsi=new_peak_rsi if new_peak_rsi > 0 else None,
                vol_ratio=vol_ratio,
                last_tighten_iso=last_tighten_ts(sl_tightens_json),
            )
            sl_updates = {}
            if new_peak_rsi > stored_peak_rsi:
                sl_updates["peak_rsi"] = round(new_peak_rsi, 1)
            if should_t:
                updated_audit_t = append_tighten_audit(sl_tightens_json, new_sl_t, reason_t)
                sl_updates["current_sl"] = new_sl_t
                sl_updates["sl_tightens"] = updated_audit_t
                flags.append(("sl_tighten", f"🛡️ SL reference tightened to ${new_sl_t:.2f} ({reason_t}) — official SL for records stays ${sl:.2f}"))
            if sl_updates:
                update_pick_row(today_str, ticker, sl_updates)
        except Exception as e:
            print(f"[adaptive_sl] {ticker} skipped: {e}")

        news = fetch_recent_news(ticker, lookback_min=45)
        material_news = []
        for n in news:
            cat = classify_material(n.get("headline", ""))
            if cat:
                material_news.append((cat, n.get("headline", "")[:120], n.get("url", "")))
        if not flags and not material_news:
            continue
        change_pct = ((price - entry) / entry * 100) if entry else 0.0
        fp_parts = [ticker] + sorted([f[0] for f in flags])
        if material_news:
            fp_parts.append(material_news[0][1][:60])
        fingerprint = "|".join(fp_parts)
        if fingerprint in sent_alerts:
            continue
        sent_alerts.add(fingerprint)
        alerts.append({"ticker": ticker, "price": price, "entry": entry,
                       "change_pct": change_pct, "flags": flags, "news": material_news,
                       "provenance": p.get("provenance", "")})
    return alerts

def build_message(monitor_alerts: list, new_opps: list) -> str:
    if not monitor_alerts and not new_opps:
        return ""
    et_now = datetime.now(timezone.utc).astimezone(ET)
    lines = [f"*INTRADAY UPDATE* — {et_now.strftime('%H:%M')} ET\n"]
    if monitor_alerts:
        lines.append("*Pick Status*\n")
        for a in monitor_alerts:
            arrow = "UP" if a["change_pct"] >= 0 else "DOWN"
            lines.append(f"{arrow} *{a['ticker']}* @ ${a['price']:.2f} "
                         f"(entry ${a['entry']:.2f}, {a['change_pct']:+.1f}%)")
            # Cluster C provenance: open-date + source + carryover flag, so no
            # position ever appears "from nowhere".
            if a.get("provenance"):
                lines.append(f"   - Source: {a['provenance']}")
            for _, msg in a["flags"]:
                lines.append(f"   - {msg}")
            for cat, headline, url in a["news"][:2]:
                lines.append(f"   - [{cat}] {headline}")
            lines.append("")
    if new_opps:
        lines.append("*New Opportunities Detected — WATCH ONLY*\n")
        for o in new_opps:
            prefix = "👀 WATCH ONLY — " if o.get("watch_only") else ""
            scanner = o.get("scanner", "intraday")
            lines.append(f"{prefix}*{o['ticker']}* @ ${o['price']:.2f}\n"
                         f"   Scanner: {scanner}\n"
                         f"   Score: {o['score']:.1f}\n"
                         f"   Reference levels: Observed ${o['entry']:.2f} | SL ref ${o['sl']:.2f} | TP ref ${o['tp']:.2f}\n"
                         f"   {o.get('reason','Live momentum')}\n"
                         f"   Informational — no position, no follow-up tracking.\n"
                         f"   Monitoring-only. Do not treat as a buy instruction.\n")
    # Task 9b (#3): prices come from get_live_quote() = last 5-min yfinance
    # bar (~15 min delayed), NOT a live tick. Disclose so the fresh "HH:MM ET"
    # header is not mistaken for real-time data.
    lines.append("⏱ _Prices are delayed ~15 min (free data) — verify live price before acting._")
    lines.append("_Educational only. Not financial advice._")
    msg = "\n".join(lines)
    return msg[:3950] + "\n\n_(truncated)_" if len(msg) > 4000 else msg

def main():
    append_opening_range_run_status(
        event="monitor_started",
        result="started",
        reason="intraday monitor workflow started",
    )

    picks = load_todays_picks()
    if not picks:
        print("[monitor] No picks to monitor — exiting.")
        append_opening_range_run_status(
            event="monitor_skipped",
            result="no_picks",
            reason="no picks available to monitor; opening-range scan skipped",
        )
        return
    sent_alerts = load_sent_alerts()
    print(f"[monitor] Monitoring {len(picks)} picks. {len(sent_alerts)} alerts already sent.")
    monitor_alerts = monitor_existing_picks(picks, sent_alerts)
    print(f"[monitor] {len(monitor_alerts)} new alerts on existing picks.")
    existing_tickers = {p["ticker"] for p in picks}
    new_opps = scan_for_new_opportunities(exclude=existing_tickers,
                                          sent_alerts=sent_alerts, max_results=3)
    print(f"[monitor] {len(new_opps)} new opportunities found.")
    opening_range_count = sum(1 for o in new_opps if o.get("scanner") == "opening_range")
    n_or_obs = append_opening_range_observations(new_opps)
    if n_or_obs:
        print(f"[monitor] {n_or_obs} opening-range observation(s) recorded.")

    # Refresh retained bars for previously recorded opening-range observations.
    # This is observe-only evidence retention; it does not create alerts/picks.
    or_retention = refresh_opening_range_bar_artifacts_for_observations()
    if or_retention.get("ticker_count"):
        print(
            "[monitor] opening-range bar retention refresh: "
            f"{or_retention.get('refreshed_count', 0)}/"
            f"{or_retention.get('ticker_count', 0)} ticker artifact(s) refreshed."
        )

    n_momentum_obs = append_intraday_momentum_observations(new_opps)
    if n_momentum_obs:
        print(f"[monitor] {n_momentum_obs} intraday momentum observation(s) recorded.")

    msg = build_message(monitor_alerts, new_opps)
    total_alert_count = len(monitor_alerts) + len(new_opps)
    append_opening_range_run_status(
        event="monitor_completed",
        result="alerts_ready" if msg else "no_alerts",
        reason="intraday monitor completed; Telegram sender records send/skipped result",
        candidate_count=opening_range_count,
        alert_count=total_alert_count,
        observation_count=n_or_obs,
        telegram_sent=None,
    )

    if not msg:
        print("[monitor] Nothing material — no message sent.")
        return
    OUT_FILE.write_text(msg)
    save_sent_alerts(sent_alerts)
    print(f"[monitor] Alert written to {OUT_FILE} ({len(msg)} chars)")

if __name__ == "__main__":
    main()
