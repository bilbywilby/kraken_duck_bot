"""Rotating JSON-lines audit log."""
import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

def get_logger(name):
    logger = logging.getLogger(f"duckbot.{name}")
    if logger.handlers:
        return logger
    os.makedirs("logs", exist_ok=True)
    h = RotatingFileHandler(f"logs/{name}.log", maxBytes=5_000_000, backupCount=10)
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(h)
    logger.setLevel(logging.DEBUG)
    return logger

def log_api_response(endpoint, payload, response, ok=True):
    entry = {"ts": datetime.now(timezone.utc).isoformat(), "endpoint": endpoint,
             "request": payload, "response": response, "ok": ok}
    lg = get_logger("api_calls")
    (lg.info if ok else lg.error)(json.dumps(entry))
