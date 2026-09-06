"""Exchange facade. Dry-run: live public prices, simulated fills with fee."""
import ccxt
from duckbot.audit_log import log_api_response

class DuckExchange:
    def __init__(self, cfg, live_allowed=False):
        self.cfg = cfg
        self.live_allowed = live_allowed
        self._client = None
        self.paper_usd = cfg.start_balance
        self.paper_btc = 0.0

    def _public(self):
        if self._client is None:
            self._client = ccxt.kraken()
        return self._client

    def fetch_price(self) -> float:
        t = self._public().fetch_ticker("BTC/USD")
        price = float(t["last"])
        log_api_response("fetch_ticker", {"pair": "BTC/USD"}, {"last": price})
        return price

    def market_buy(self, usd_amount: float) -> dict:
        price = self.fetch_price()
        if not self.cfg.dry_run:
            if not self.live_allowed or not self.cfg.secrets_ready():
                raise RuntimeError("Live buy blocked: readiness gate or secrets missing.")
            raise NotImplementedError("Attach keyed create_order here.")
        fee = usd_amount * self.cfg.trade_fee_pct
        btc = (usd_amount - fee) / price
        self.paper_usd -= usd_amount
        self.paper_btc += btc
        return {"side": "BUY", "price": price, "btc": btc, "fee": fee,
                "balance_usd": self.paper_usd, "dry_run": True}

    def market_sell(self) -> dict:
        price = self.fetch_price()
        if not self.cfg.dry_run:
            if not self.live_allowed or not self.cfg.secrets_ready():
                raise RuntimeError("Live sell blocked: readiness gate or secrets missing.")
            raise NotImplementedError("Attach keyed create_order here.")
        btc_sold = self.paper_btc
        gross = btc_sold * price
        fee = gross * self.cfg.trade_fee_pct
        self.paper_usd += gross - fee
        self.paper_btc = 0.0
        return {"side": "SELL", "price": price, "btc_sold": btc_sold, "fee": fee,
                "balance_usd": self.paper_usd, "dry_run": True}
