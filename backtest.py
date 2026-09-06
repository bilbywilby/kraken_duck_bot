#!/usr/bin/env python3
"""Historical replay through the production decide_action()."""
import argparse, os, sys
from dataclasses import replace
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from duckbot import state as db_state
from duckbot.bot import decide_action
from duckbot.config import load_config

def load_candles(path):
    df = pd.read_csv(path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    ts = df["timestamp"]
    if pd.api.types.is_numeric_dtype(ts):
        ts = pd.to_datetime(ts, unit="ms" if float(ts.iloc[0]) > 1e12 else "s", utc=True)
    else:
        ts = pd.to_datetime(ts, utc=True)
    out = pd.DataFrame({"timestamp": ts, "open": df["open"].astype(float),
                        "high": df["high"].astype(float),
                        "low": df["low"].astype(float),
                        "close": df["close"].astype(float)})
    return out.dropna().drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)

def run_backtest(df, cfg, slippage, start_balance, stop_fill):
    sim = {"last_action": None, "last_action_date": None,
           "current_position": 0.0, "entry_price": None}
    clock = {"now": df["timestamp"].iloc[0].to_pydatetime()}
    db_state.load_state = lambda: dict(sim)
    db_state._today = lambda: clock["now"].astimezone(cfg.tz()).strftime("%Y-%m-%d")

    balance, open_trade, trades, equity = start_balance, None, [], []

    def close_exit(action, fill, ct):
        nonlocal balance, open_trade
        gross = open_trade["btc"] * fill
        fee = gross * cfg.trade_fee_pct
        balance = gross - fee
        pnl = balance - open_trade["invested"]
        trades.append({"buy_time": open_trade["entry_time"], "entry": open_trade["entry"],
                       "sell_time": ct, "exit": fill, "action": action,
                       "amount_btc": open_trade["btc"], "buy_fee": open_trade["buy_fee"],
                       "sell_fee": fee, "invested": open_trade["invested"],
                       "net_pnl": pnl, "net_pct": pnl / open_trade["invested"] * 100})
        sim.update(current_position=0.0, entry_price=None, last_action=action,
                   last_action_date=ct.strftime("%Y-%m-%d"))
        open_trade = None

    for row in df.itertuples(index=False):
        ct = row.timestamp.to_pydatetime().astimezone(cfg.tz())
        clock["now"] = ct
        close, low = float(row.close), float(row.low)

        if sim["current_position"] > 0 and sim["entry_price"]:
            stop_price = sim["entry_price"] * (1 - cfg.stop_loss_pct)
            if low <= stop_price:
                level = low if stop_fill == "low" else stop_price
                close_exit("STOP_LOSS", level * (1 - slippage), ct)
                equity.append({"timestamp": ct, "equity": balance})
                continue

        action = decide_action(close, dict(sim), cfg, now=ct)
        if action == "BUY":
            fill = close * (1 + slippage)
            fee = balance * cfg.trade_fee_pct
            btc = (balance - fee) / fill
            open_trade = {"entry_time": ct, "entry": fill, "btc": btc,
                          "buy_fee": fee, "invested": balance}
            balance = 0.0
            sim.update(current_position=btc, entry_price=fill,
                       last_action="BUY", last_action_date=ct.strftime("%Y-%m-%d"))
        elif action in ("SELL", "STOP_LOSS"):
            close_exit(action, close * (1 - slippage), ct)
        equity.append({"timestamp": ct,
                       "equity": balance + sim["current_position"] * close})
    return trades, pd.DataFrame(equity)

def summarize(trades, equity, df, cfg, start_balance):
    t = pd.DataFrame(trades)
    n = len(t)
    final_eq = float(equity["equity"].iloc[-1])
    entry = df["close"].iloc[0]
    units = (start_balance * (1 - cfg.trade_fee_pct)) / entry
    bh_final = units * df["close"].iloc[-1] * (1 - cfg.trade_fee_pct)
    print("\n=== BACKTEST SUMMARY ===")
    print(f"Candles:         {len(df)}")
    print(f"Round trips:     {n}")
    if n:
        wins = int((t["net_pnl"] > 0).sum())
        print(f"Win rate:        {wins/n*100:.1f}%")
        print(f"Fees (2 legs):   ${t['buy_fee'].sum()+t['sell_fee'].sum():,.2f}")
        print(f"Stop-loss exits: {int((t['action']=='STOP_LOSS').sum())}")
    print(f"BOT NET ROI:     {final_eq/start_balance*100-100:+.2f}%  (${final_eq:,.2f})")
    print(f"Buy & hold:      {bh_final/start_balance*100-100:+.2f}%  (${bh_final:,.2f})")

def plot_equity_curve(equity, df, cfg, start_balance, out_path="reports/equity_curve.png"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt, os
    units = (start_balance * (1 - cfg.trade_fee_pct)) / df["close"].iloc[0]
    bh = (units * df["close"]).tolist()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(equity["timestamp"], equity["equity"], label="DuckBot strategy",
            color="#6d4aff", linewidth=2)
    ax.plot(df["timestamp"], bh, label="Buy & hold (fee-adj.)",
            color="#888888", alpha=0.7)
    ax.axhline(start_balance, color="black", alpha=0.3, linewidth=0.8, linestyle=":")
    ax.set_title("Strategy vs Buy & Hold (fee-adjusted)")
    ax.set_ylabel("Balance ($)")
    ax.legend(); ax.grid(alpha=0.3, linestyle=":")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.tight_layout(); fig.savefig(out_path, dpi=130)
    print(f"Equity curve saved to {out_path}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--slippage", type=float, default=0.0005)
    ap.add_argument("--stop-fill", choices=["stop", "low"], default="stop")
    args = ap.parse_args()
    cfg = load_config()
    df = load_candles(args.csv)
    if len(df) < 24:
        raise SystemExit("Need at least 24 candles.")
    trades, equity = run_backtest(df, cfg, args.slippage, cfg.start_balance,
                                  args.stop_fill)
    summarize(trades, equity, df, cfg, cfg.start_balance)
    os.makedirs("reports", exist_ok=True)
    pd.DataFrame(trades).to_csv("reports/backtest_trades.csv", index=False)
    equity.to_csv("reports/backtest_equity.csv", index=False)
    plot_equity_curve(equity, df, cfg, cfg.start_balance)

if __name__ == "__main__":
    main()
