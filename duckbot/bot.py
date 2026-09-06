"""Pure decision + effectful execution. decide_action is clock-injectable."""
from datetime import datetime

from duckbot import ledger, state
from duckbot.notify import order_filled, stop_loss_hit
from duckbot.safety_controls import is_kill_switch_active, verify_live_readiness

def _hhmm(s):
    h, m = s.split(":")
    return (int(h), int(m))

def _in_window(window, now) -> bool:
    return _hhmm(window[0]) <= (now.hour, now.minute) <= _hhmm(window[1])

def decide_action(price: float, st: dict, cfg, now=None) -> str:
    """Priority: STOP_LOSS > SELL > BUY > HOLD. Pure; no IO."""
    if now is None:
        now = datetime.now(cfg.tz())
    holding = st.get("current_position", 0.0) > 0 and st.get("entry_price")
    if holding:
        drop = (st["entry_price"] - price) / st["entry_price"]
        if drop >= cfg.stop_loss_pct:
            return "STOP_LOSS"
        if _in_window(cfg.sell_window, now) and state.can_perform_action("SELL"):
            return "SELL"
    elif _in_window(cfg.buy_window, now) and not state.did_buy_today(st):
        return "BUY"
    return "HOLD"

def run_cycle(ex, cfg) -> dict:
    if is_kill_switch_active():
        ledger.init_db(); ledger.log_event("SKIP", "kill switch active")
        return {"executed": False, "action": "SKIPPED_KILL_SWITCH"}
    live_allowed = False
    if not cfg.dry_run:
        audit = verify_live_readiness()
        if not audit.get("ready"):
            ledger.init_db(); ledger.log_event("BLOCK", f"live gate: {audit['reason']}")
            return {"executed": False, "action": "BLOCKED_LIVE_GATE", "audit": audit}
        live_allowed = True

    ledger.init_db()
    price = ex.fetch_price()
    st = state.load_state()
    action = decide_action(price, st, cfg)

    if action == "HOLD":
        return {"executed": False, "action": "HOLD", "price": price}

    if action == "BUY":
        res = ex.market_buy(cfg.start_balance)
        ledger.log_trade("BUY", res["price"], res["btc"], res["fee"],
                         res["balance_usd"], cfg.dry_run)
        state.update_action("BUY", position=res["btc"], entry_price=res["price"])
        ledger.set_meta("balance_usd", f"{res['balance_usd']:.2f}")
        from duckbot.notify import order_filled
        order_filled("BUY", res["price"], res["btc"])
    else:
        res = ex.market_sell()
        ledger.log_trade(action, res["price"], res["btc_sold"], res["fee"],
                         res["balance_usd"], cfg.dry_run)
        state.update_action(action, position=0.0)
        ledger.set_meta("balance_usd", f"{res['balance_usd']:.2f}")
        if action == "STOP_LOSS":
            from duckbot.notify import stop_loss_hit
            stop_loss_hit(res["price"])
        else:
            from duckbot.notify import order_filled
            order_filled("SELL", res["price"], res["btc_sold"])

    ledger.log_event("EXEC", f"{action} @ {res['price']:.2f}")
    return {"executed": True, "action": action, "result": res}

def healthcheck() -> dict:
    return {"status": "ok", "kill_switch": is_kill_switch_active()}
