#!/usr/bin/env python3
"""Fetch 1h OHLCV candles from Kraken public API (paginated)."""
import argparse, csv, os, time
from datetime import datetime, timedelta, timezone
import ccxt

PAIR, TIMEFRAME, PER_REQUEST = "BTC/USD", "1d", 720

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--out", default="data/backtest/BTC_USD_1h.csv")
    args = ap.parse_args()

    ex = ccxt.kraken()
    now_ms = int(__import__("time").time() * 1000)
    from datetime import timedelta
    cursor = now_ms - int(timedelta(days=args.days).total_seconds() * 1000)
    candles, prev = [], object()
    while cursor < now_ms and cursor != prev:
        prev = cursor
        batch = ex.fetch_ohlcv("BTC/USD", timeframe="1h", since=cursor, limit=PER_REQUEST)
        if not batch:
            break
        candles.extend(batch)
        cursor = batch[-1][0] + 1
        print(f"  {len(candles)} candles...")
        if len(batch) < PER_REQUEST:
            break
        import time as t
        t.sleep(ex.rateLimit / 1000)

    seen, unique = set(), []
    for c in sorted(candles):
        if c[0] not in seen:
            seen.add(c[0]); unique.append(c)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "open", "high", "low", "close", "volume"])
        for ts, o, h, l, cl, v in unique:
            w.writerow([datetime.fromtimestamp(ts / 1000, timezone.utc).isoformat(),
                        o, h, l, cl, v])
    print(f"Wrote {len(unique)} candles to {args.out}")

if __name__ == "__main__":
    main()
