"""Hard safety gates: file kill-switch + paper-readiness audit."""
import sqlite3
from pathlib import Path

DATA_DIR = Path("data")
KILL_SWITCH = DATA_DIR / "STOP"
DB_FILE = DATA_DIR / "trading_history.db"

def is_kill_switch_active() -> bool:
    return KILL_SWITCH.exists()

def set_kill_switch():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    KILL_SWITCH.touch()

def clear_kill_switch():
    KILL_SWITCH.unlink(missing_ok=True)

def verify_live_readiness(min_days=30, min_win_rate=50.0) -> dict:
    if not DB_FILE.exists():
        return {"ready": False, "reason": "No database history found."}
    conn = sqlite3.connect(DB_FILE)
    try:
        rows = conn.execute(
            "SELECT timestamp, action, price, amount, fee FROM trades "
            "ORDER BY timestamp").fetchall()
    finally:
        conn.close()
    if not rows:
        return {"ready": False, "reason": "Trade history is empty."}
    from datetime import datetime
    ts = [datetime.fromisoformat(r[0]) for r in rows]
    days = (max(ts) - min(ts)).days
    if days < min_days:
        return {"ready": False, "reason": f"Only {days}/{min_days} days of history."}
    buys = [(r[2], r[3], r[4]) for r in rows if r[1] == "BUY"]
    sells = [(r[2], r[4]) for r in rows if r[1] in ("SELL", "STOP_LOSS")]
    n = min(len(buys), len(sells))
    if n == 0:
        return {"ready": False, "reason": "No completed trade pairs."}
    wins = sum((sells[i][0] - buys[i][0]) * buys[i][1] - buys[i][2] - sells[i][1] > 0
               for i in range(n))
    win_rate = wins / n * 100
    if win_rate < min_win_rate:
        return {"ready": False, "reason": f"Win rate {win_rate:.1f}% < {min_win_rate}%.",
                "days_tested": days, "pairs": n}
    return {"ready": True, "days_tested": days, "pairs": n, "win_rate": win_rate}
