"""Typed .env configuration."""
import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    api_key: str
    api_secret: str
    start_balance: float
    buy_window: tuple
    sell_window: tuple
    stop_loss_pct: float
    trade_fee_pct: float
    dry_run: bool
    timezone: str

    def tz(self):
        return ZoneInfo(self.timezone)

    def secrets_ready(self) -> bool:
        return bool(self.api_key and self.api_secret)

def load_config() -> Config:
    return Config(
        api_key=os.getenv("KRAKEN_API_KEY", ""),
        api_secret=os.getenv("KRAKEN_PRIVATE_KEY", ""),
        start_balance=float(os.getenv("START_BALANCE", "1000")),
        buy_window=(os.getenv("BUY_START", "03:00"), os.getenv("BUY_END", "06:00")),
        sell_window=(os.getenv("SELL_START", "11:00"), os.getenv("SELL_END", "12:00")),
        stop_loss_pct=float(os.getenv("STOP_LOSS_PCT", "0.02")),
        trade_fee_pct=float(os.getenv("TRADE_FEE_PCT", "0.0026")),
        dry_run=os.getenv("DRY_RUN", "true").lower() != "false",
        timezone=os.getenv("TIMEZONE", "US/Eastern"),
    )
