"""Operational state: atomic writes, local-timezone aware."""
import json
import os
from datetime import datetime
from pathlib import Path

STATE_FILE = Path("data") / "state.json"
DEFAULT_STATE = {"last_action": None, "last_action_date": None,
                 "current_position": 0.0, "entry_price": None,
                 "bot_version": "2.0.0"}

def _today() -> str:
    from duckbot.config import load_config
    return datetime.now(load_config().tz()).strftime("%Y-%m-%d")

def load_state() -> dict:
    if not STATE_FILE.exists():
        return DEFAULT_STATE.copy()
    try:
        with open(STATE_FILE) as f:
            merged = DEFAULT_STATE.copy()
            merged.update(json.load(f))
            return merged
    except (json.JSONDecodeError, IOError):
        return DEFAULT_STATE.copy()

def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_FILE)

def update_action(action, position=None, entry_price=None):
    s = load_state()
    s["last_action"] = action
    s["last_action_date"] = _today()
    if position is not None:
        s["current_position"] = position
    if entry_price is not None:
        s["entry_price"] = entry_price
    elif action in ("SELL", "STOP_LOSS"):
        s["entry_price"] = None
    save_state(s)

def can_perform_action(action: str) -> bool:
    s = load_state()
    return not (s["last_action_date"] == _today() and s["last_action"] == action)

def did_buy_today(state=None) -> bool:
    s = state if state is not None else load_state()
    return s["last_action_date"] == _today() and s["last_action"] == "BUY"
