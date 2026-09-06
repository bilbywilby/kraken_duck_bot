#!/usr/bin/env python3
"""Append MC percentiles to risk_history/risk_drift.csv (committed)."""
import argparse, csv, os
from datetime import date
import numpy as np

CSV_PATH = "risk_history/risk_drift.csv"
FIELDS = ["run_date", "n_sims", "p5_final", "p50_final", "p95_final",
          "mean_final", "prob_loss_pct"]

def record(finals_csv="reports/mc_finals.csv", start_balance=1000.0):
    if not os.path.exists(finals_csv):
        raise SystemExit("Run the Monte Carlo first.")
    finals = np.loadtxt(finals_csv)
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    exists = os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if not exists:
            w.writeheader()
        w.writerow({"run_date": date.today().isoformat(), "n_sims": len(finals),
                    "p5_final": f"{np.percentile(finals,5):.2f}",
                    "p50_final": f"{np.percentile(finals,50):.2f}",
                    "p95_final": f"{np.percentile(finals,95):.2f}",
                    "mean_final": f"{finals.mean():.2f}",
                    "prob_loss_pct": f"{(finals < start_balance).mean()*100:.2f}"})
    print(f"Appended snapshot to {CSV_PATH}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--finals", default="reports/mc_finals.csv")
    a = ap.parse_args()
    from duckbot.config import load_config
    record(args.finals, load_config().start_balance)
