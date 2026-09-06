"""Offline tests: no network, no secrets, injected clock."""
import os, unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from duckbot.bot import decide_action
from duckbot import ledger, state

class FakeCfg:
    buy_window = ("03:00", "06:00")
    sell_window = ("11:00", "12:00")
    stop_loss_pct = 0.02
    trade_fee_pct = 0.0026
    timezone = "US/Eastern"
    def tz(self):
        return ZoneInfo(self.timezone)

def et(h, m=0):
    return datetime(2026, 9, 5, h, m, tzinfo=ZoneInfo("US/Eastern"))

class TestDecide(unittest.TestCase):
    def cfg(self):
        return FakeCfg()

    def test_buy_inside_window(self):
        st = {"current_position": 0.0, "entry_price": None,
              "last_action": None, "last_action_date": None}
        self.assertEqual(decide_action(60000.0, st, self.cfg(), now=et(4, 30)), "BUY")

    def test_hold_outside_window(self):
        st = {"current_position": 0.0, "entry_price": None,
              "last_action": None, "last_action_date": None}
        self.assertEqual(decide_action(60000.0, st, self.cfg(), now=et(13, 0)), "HOLD")

    def test_sell_in_window(self):
        st = {"current_position": 0.015, "entry_price": 60000.0,
              "last_action": "BUY", "last_action_date": "2026-09-05"}
        self.assertEqual(decide_action(61000.0, st, self.cfg(), now=et(11, 30)), "SELL")

    def test_stop_loss_beats_window(self):
        st = {"current_position": 0.015, "entry_price": 60000.0,
              "last_action": "BUY", "last_action_date": "2026-09-05"}
        self.assertEqual(decide_action(57000.0, st, self.cfg(), now=et(9, 0)),
                         "STOP_LOSS")

class TestPersistence(unittest.TestCase):
    def test_state_roundtrip(self):
        state.STATE_FILE = state.Path("data/test_state.json")
        state.STATE_FILE.unlink(missing_ok=True)
        state.update_action("BUY", position=0.015, entry_price=60000.0)
        self.assertEqual(state.load_state()["current_position"], 0.015)
        state.update_action("SELL", position=0.0)
        self.assertIsNone(state.load_state()["entry_price"])
        state.STATE_FILE.unlink(missing_ok=True)

    def test_ledger(self):
        ledger.DB_PATH = "data/test_history.db"
        for s in ("", "-wal", "-shm"):
            try: os.remove(ledger.DB_PATH + s)
            except FileNotFoundError: pass
        ledger.init_db()
        ledger.log_trade("BUY", 60000.0, 0.015, 0.39, 999.61, dry_run=True)
        self.assertIsNotNone(ledger.open_position())
        os.remove(ledger.DB_PATH)

if __name__ == "__main__":
    unittest.main()
