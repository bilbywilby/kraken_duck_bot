"""SQLite audit layer: trades, events, meta. WAL journaling."""
import os
import sqlite3
from datetime import datetime

DB_PATH = "data/trading_history.db"

def connect(db_path=None):
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db(conn=None):
    owns = conn is None
    conn = conn or connect()
    conn.execute("""CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        action TEXT CHECK(action IN ('BUY','SELL','STOP_LOSS')),
        pair TEXT DEFAULT 'BTC/USD',
        price REAL, amount REAL, fee REAL,
        balance_usd REAL, dry_run INTEGER DEFAULT 0)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL, kind TEXT, detail TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY, value TEXT)""")
    conn.commit()
    if owns:
        conn.close()

def log_trade(action, price, amount, fee, balance, dry_run=True, conn=None):
    owns = conn is None
    conn = conn or connect()
    with conn:
        conn.execute(
            "INSERT INTO trades (timestamp, action, price, amount, fee, balance_usd, dry_run) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), action, price, amount, fee, balance, int(dry_run)))
    if owns:
        conn.close()

def log_event(kind, detail, conn=None):
    owns = conn is None
    conn = conn or connect()
    with conn:
        conn.execute("INSERT INTO events (ts, kind, detail) VALUES (?, ?, ?)",
                     (datetime.now().isoformat(), kind, detail))
    if owns:
        conn.close()

def set_meta(key, value, conn=None):
    owns = conn is None
    conn = conn or connect()
    with conn:
        conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                     (str(key), str(value)))
    if owns:
        conn.close()

def get_meta(key, conn=None):
    owns = conn is None
    conn = conn or connect()
    row = conn.execute("SELECT value FROM meta WHERE key=?", (str(key),)).fetchone()
    if owns:
        conn.close()
    return row[0] if row else None

def open_position(conn=None):
    owns = conn is None
    conn = conn or connect()
    row = conn.execute(
        "SELECT * FROM trades WHERE action='BUY' AND date(timestamp)=date('now') "
        "ORDER BY id DESC LIMIT 1").fetchone()
    if owns:
        conn.close()
    return row
