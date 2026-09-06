#!/usr/bin/env python3
"""Monte Carlo over daily open->close round trips (long-sample variant).

Uses the 2-year daily CSV (data/backtest/BTC_USD_1d.csv) — one honest
round trip per day, fee+slippage both sides, no stop-loss (daily candles
cannot see intraday lows). Complements the 30-day hourly MC.
"""
import os

import numpy as np
import pandas as pd

from duckbot.config import load_config

SLIPPAGE = 0.0005
CSV = "data/backtest/BTC_USD_1d.csv"

def main():
    cfg = load_config()
    start = cfg.start_balance

    df = pd.read_csv(CSV)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Daily round trip: buy at open + slip, sell at close - slip, fee both legs
    entry = df["open"].astype(float) * (1 + SLIPPAGE)
    exit_ = df["close"].astype(float) * (1 - SLIPPAGE)
    f = cfg.trade_fee_pct
    factors = ((1 - f) * (exit_ / entry) * (1 - f)).to_numpy()

    rng = np.random.default_rng(42)
    n_sim, horizon = 10_000, 365
    idx = rng.integers(0, len(factors), size=(n_sim, horizon))
    finals = start * np.prod(factors[idx], axis=1)

    pct = np.percentile(finals, [1, 5, 25, 50, 75, 95, 99])
    print("=== MONTE CARLO (daily sample, 1 round trip/day) ===")
    print(f"Sample:           {len(factors)} daily round trips "
          f"({df.timestamp.iloc[0]:%Y-%m-%d} -> {df.timestamp.iloc[-1]:%Y-%m-%d})")
    print(f"Mean daily net:   {(factors.mean() - 1) * 100:+.4f}%")
    print(f"Median final:     ${pct[3]:,.2f} ({pct[3] / start * 100 - 100:+.1f}%)")
    print(f"5th percentile:   ${pct[1]:,.2f}")
    print(f"95th percentile:  ${pct[5]:,.2f}")
    print(f"P(loss):          {(finals < start).mean() * 100:.1f}%")
    print(f"P(ruin < half):   {(finals < start / 2).mean() * 100:.2f}%")

    os.makedirs("reports", exist_ok=True)
    np.savetxt("reports/mc_finals_daily_sample.csv", finals, fmt="%.2f")
    print("Saved reports/mc_finals_yearly.csv")

if __name__ == "__main__":
    main()
