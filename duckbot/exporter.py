"""Prometheus exporter on :9100."""
import json
import sqlite3
import time
from pathlib import Path

from prometheus_client import start_http_server, Gauge, Counter

STATE_FILE = Path("data") / "state.json"
DB_FILE = Path("data") / "trading_history.db"

BALANCE = Gauge("duckbot_balance_usd", "Current USD balance")
HOLDINGS = Gauge("duckbot_holdings_btc", "Current BTC position")
BTC_PRICE = Gauge("duckbot_btc_price_usd", "Last BTC price")
FEES = Gauge("duckbot_fees_paid_usd_total", "Cumulative fees USD")

def update_metrics():
    if STATE_FILE.exists():
        try:
            st = json.loads(STATE_FILE.read_text())
            HOLDINGS.set(float(st.get("current_position", 0.0)))
        except (json.JSONDecodeError, ValueError):
            pass
    if DB_FILE.exists():
        try:
            conn = sqlite3.connect(DB_FILE)
            row = conn.execute("SELECT balance_usd, price FROM trades "
                               "ORDER BY id DESC LIMIT 1").fetchone()
            if row:
                row[0] is not None and BALANCE.set(float(row[0]))
                row[1] is not None and BTC_PRICE.set(float(row[1]))
            fee = conn.execute("SELECT SUM(fee) FROM trades").fetchone()[0]
            fee is not None and FEES.set(float(fee))
            conn.close()
        except sqlite3.Error:
            pass

def main():
    from prometheus_client import start_http_server
    start_http_server(9100)
    print("Metrics on :9100/metrics")
    import time
    while True:
        update_metrics()
        time.sleep(15)
