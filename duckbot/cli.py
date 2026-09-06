"""Entrypoint: python main.py [cycle|health|price|status|stop|resume]"""
import argparse
import sys

from duckbot.bot import run_cycle, healthcheck
from duckbot.config import load_config
from duckbot.exchange import DuckExchange
from duckbot import safety_controls

def main(argv=None):
    p = argparse.ArgumentParser(prog="crypto-duck-bot")
    p.add_argument("command", nargs="?", default="cycle",
                   choices=["cycle", "health", "price", "status", "stop", "resume"])
    args = p.parse_args(argv)

    if args.command == "stop":
        safety_controls.set_kill_switch()
        print("Kill switch ENGAGED.")
        return 0
    if args.command == "resume":
        safety_controls.clear_kill_switch()
        print("Kill switch cleared.")
        return 0
    if args.command == "health":
        from duckbot.bot import healthcheck
        print(healthcheck())
        return 0

    cfg = load_config()
    if args.command == "price":
        print(f"BTC/USD: {DuckExchange(cfg).fetch_price():,.2f}")
        return 0
    if args.command == "status":
        print("Readiness:", safety_controls.verify_live_readiness())
        print("Kill switch:", safety_controls.is_kill_switch_active())
        print(f"Dry run: {cfg.dry_run}")
        return 0
    from duckbot.bot import run_cycle
    print(run_cycle(DuckExchange(cfg), cfg))
    return 0
