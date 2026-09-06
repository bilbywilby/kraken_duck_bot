"""Monte Carlo: bootstraps real window round trips from hourly data."""
import argparse, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from duckbot.config import load_config

def derive_round_trips(df, cfg, slippage):
    local = df["timestamp"].dt.tz_convert(cfg.timezone)
    df = df.assign(local_dt=local, local_t=local.dt.strftime("%H:%M"))
    buys = df[(df.local_t >= cfg.buy_window[0]) & (df.local_t < cfg.buy_window[1])]
    sells = df[(df.local_t >= cfg.sell_window[0]) & (df.local_t < cfg.sell_window[1])]
    rows = []
    for _, b in buys.iterrows():
        s = sells[(sells.local_dt >= b.local_dt) &
                  (sells.local_dt.dt.date == b.local_dt.date())]
        if s.empty:
            continue
        exit_row = s.iloc[0]
        seg = df[(df.local_dt >= b.local_dt) & (df.local_dt <= exit_row.local_dt)]
        entry_eff = float(b.close) * (1 + slippage)
        exit_eff = float(exit_row.close) * (1 - slippage)
        minlow = float(seg.low.min()) * (1 - slippage)
        stop_price = entry_eff * (1 - cfg.stop_loss_pct)
        stopped = minlow <= stop_price
        if stopped:
            exit_eff = min(stop_price, exit_eff)
        f = cfg.trade_fee_pct
        rows.append({"date": b.local_dt.date(), "stopped": stopped,
                     "gross_ret": exit_eff / entry_eff - 1,
                     "factor": (1 - f) * (exit_eff / entry_eff) * (1 - f)})
    return pd.DataFrame(rows)

def run_mc(rt, n_sim, horizon, start_balance, seed=None):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(rt), size=(n_sim, horizon))
    return start_balance * np.prod(rt["factor"].to_numpy()[idx], axis=1)

def summarize(finals, rt, start_balance, horizon):
    pct = np.percentile(finals, [1, 5, 25, 50, 75, 95, 99])
    print("\n=== MONTE CARLO SUMMARY ===")
    print(f"Simulations:      {len(finals):,} x {horizon} days")
    print(f"Sample:           {len(rt)} round trips "
          f"({rt.stopped.mean()*100:.1f}% stopped)")
    print(f"Median final:     ${pct[3]:,.2f} ({pct[3]/start_balance*100-100:+.1f}%)")
    print(f"5th percentile:   ${pct[1]:,.2f}")
    print(f"95th percentile:  ${pct[5]:,.2f}")
    print(f"P(loss):          {(finals < start_balance).mean()*100:.1f}%")

def plot_hist(finals, start_balance, out="reports/mc_distribution.png"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(finals, bins=60, edgecolor="black", alpha=0.75)
    ax.axvline(np.median(finals), linestyle="--", linewidth=2,
               label=f"median ${np.median(finals):,.0f}")
    ax.axvline(start_balance, color="crimson", linestyle=":",
               label=f"start ${start_balance:,.0f}")
    ax.set_title("Monte Carlo: final balance after 1 simulated year")
    ax.set_xlabel("Final balance ($)"); ax.set_ylabel("Frequency"); ax.legend()
    ax.grid(alpha=0.3, linestyle=":")
    fig.tight_layout(); fig.savefig(out, dpi=130)
    print(f"Histogram saved to {out}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--simulations", type=int, default=10_000)
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--slippage", type=float, default=0.0005)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--csv", default="data/backtest/BTC_USD_1h.csv")
    ap.add_argument("--no-plot", action="store_true")
    args = ap.parse_args()
    cfg = load_config()
    if not os.path.exists(args.csv):
        raise SystemExit("Run `make fetch-history` first.")
    df = pd.read_csv(args.csv)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    rt = derive_round_trips(df, cfg, args.slippage)
    if len(rt) < 30:
        raise SystemExit(f"Only {len(rt)} round trips — need more data.")
    finals = run_mc(rt, args.simulations, args.days, cfg.start_balance, args.seed)
    summarize(finals, rt, cfg.start_balance, args.days)
    os.makedirs("reports", exist_ok=True)
    np.savetxt("reports/mc_finals.csv", finals, fmt="%.2f")
    if not args.no_plot:
        plot_hist(finals, cfg.start_balance)

if __name__ == "__main__":
    main()
