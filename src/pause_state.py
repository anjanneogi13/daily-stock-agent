"""Pause state machine — Pillar 4 enforce-mode helpers.

Stores active pause in data/pause_state.json:
{
  "active":     true/false,
  "until":      "YYYY-MM-DD",   ISO date the pause expires
  "since":      "YYYY-MM-DD",
  "score":      8,
  "reason":     ["..."],
  "manual":     false           true if owner-triggered
}
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List


CONFIG_PATH = Path("config/auto_pause.json")
STATE_PATH  = Path("data/pause_state.json")


def load_config() -> Dict:
    """Load enforce config. Defaults to safe (observe-mode) if missing."""
    if not CONFIG_PATH.exists():
        return {"enforced": False, "pause_threshold": 8, "pause_days": 3}
    try:
        return json.loads(CONFIG_PATH.read_text())
    except Exception:
        return {"enforced": False, "pause_threshold": 8, "pause_days": 3}


def load_state() -> Optional[Dict]:
    if not STATE_PATH.exists():
        return None
    try:
        return json.loads(STATE_PATH.read_text())
    except Exception:
        return None


def save_state(state: Dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))


def clear_state() -> None:
    if STATE_PATH.exists():
        STATE_PATH.unlink()


def is_paused(today: Optional[datetime] = None) -> Dict:
    """
    Return {'paused': bool, 'until': str|None, 'reason': str|None,
            'manual': bool, 'days_remaining': int}.
    """
    state = load_state()
    today = today or datetime.now()

    if not state or not state.get("active"):
        return {"paused": False, "until": None, "reason": None,
                "manual": False, "days_remaining": 0}

    try:
        until = datetime.strptime(state["until"], "%Y-%m-%d")
    except (KeyError, ValueError):
        return {"paused": False, "until": None, "reason": None,
                "manual": False, "days_remaining": 0}

    if today.date() > until.date():
        # Expired — auto-clear
        clear_state()
        return {"paused": False, "until": None, "reason": None,
                "manual": False, "days_remaining": 0}

    days_left = (until.date() - today.date()).days + 1
    reasons = state.get("reason") or []
    return {
        "paused": True,
        "until": state.get("until"),
        "reason": "; ".join(reasons) if isinstance(reasons, list) else str(reasons),
        "manual": bool(state.get("manual", False)),
        "days_remaining": days_left,
        "score": state.get("score"),
    }


def trigger_pause(score: int, reasons: List[str], days: int = 3,
                   manual: bool = False, today: Optional[datetime] = None) -> Dict:
    """Activate a pause. Refuses to extend an existing manual pause."""
    today = today or datetime.now()
    until = today + timedelta(days=days)
    state = {
        "active": True,
        "since": today.strftime("%Y-%m-%d"),
        "until": until.strftime("%Y-%m-%d"),
        "score": score,
        "reason": reasons,
        "manual": manual,
    }
    save_state(state)
    return state


def maybe_auto_pause(score_result: Dict,
                      config: Optional[Dict] = None) -> Optional[Dict]:
    """
    If config.enforced and score >= threshold AND not already paused, trigger.
    Returns the new state dict if a pause was triggered, else None.
    """
    config = config or load_config()
    if not config.get("enforced"):
        return None  # Observe-mode — never trigger
    threshold = int(config.get("pause_threshold", 8))
    if score_result["score"] < threshold:
        return None
    cur = is_paused()
    if cur["paused"]:
        return None  # Already paused — do not extend
    return trigger_pause(
        score=score_result["score"],
        reasons=score_result.get("reasons", []),
        days=int(config.get("pause_days", 3)),
        manual=False,
    )


def format_pause_alert(state: Dict) -> str:
    """Telegram-ready paused-day summary."""
    lines = [
        "🚨 *AGENT PAUSED — NO PICKS TODAY*",
        f"   Reason: {state['reason']}",
        f"   Until:  {state['until']} ({state['days_remaining']}d remaining)",
        f"   Score:  {state.get('score', '?')}/10",
    ]
    if state.get("manual"):
        lines.append("   Mode:   manual override")
    else:
        lines.append("   Mode:   auto-pause (Pillar 4)")
    lines.append("")
    lines.append("Override: `python scripts/unpause.py`")
    return "\n".join(lines)
