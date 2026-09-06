"""Env + state verification tick."""
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from duckbot import ledger
from duckbot.state import load_state

load_dotenv()

def main():
    tz = ZoneInfo(os.getenv("TIMEZONE", "US/Eastern"))
    ledger.init_db()
    st = load_state()
    local = datetime.now(tz)
    ledger.log_event("HEARTBEAT", f"ok at {local.isoformat(timespec='seconds')}")
    print(f"Ready to quack. local={local:%H:%M} tz={tz} "
          f"balance={ledger.get_meta('balance_usd') or 'n/a'} "
          f"last_act={st.get('last_action')}")

if __name__ == "__main__":
    main()
