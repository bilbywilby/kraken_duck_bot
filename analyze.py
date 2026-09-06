#!/usr/bin/env python3
"""Pair BUYs with exits; report ROI net of fees."""
import os, sqlite3
import pandas as pd

DB = "data/trading_history.db"

def analyze():
    if not os.path.exists(DB):
        print("No database found."); return
    df = pd.read_sql("SELECT * FROM trades ORDER BY timestamp, id",
                     sqlite3.connect(DB))
    if df.empty:
        print("No trades recorded."); return
    buys = df[df.action == "BUY"].reset_index(drop=True)
    sells = df[df.action.isin(["SELL", "STOP_LOSS"])].reset_index(drop=True)
    n = min(len(buys), len(sells))
    if n == 0:
        print(f"Incomplete: {len(buys)} BUYs, {len(sells)} exits."); return
    pairs = pd.DataFrame({
        "entry": buys["price"][:n], "exit": sells["price"][:n],
        "amount": buys["amount"][:n],
        "fees_usd": buys["fee"][:n] + sells["fee"][:n]})
    pairs["gross_usd"] = (pairs["exit"] - pairs["entry"]) * pairs["amount"]
    pairs["net_usd"] = pairs["gross_usd"] - pairs["fees_usd"]
    print(pairs.to_string(index=False))
    print(f"\nPairs: {n} | Win rate: {(pairs.net_usd > 0).mean()*100:.1f}% "
          f"| Fees: ${pairs.fees_usd.sum():.2f}")
    os.makedirs("reports", exist_ok=True)
    pairs.to_csv("reports/daily_roi.csv", index=False)

if __name__ == "__main__":
    analyze()
