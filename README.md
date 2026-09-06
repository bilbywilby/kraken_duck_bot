# crypto-duck-bot

Window-based BTC/USD trading bot for Kraken Pro. Dry-run first, always.
Keep this repo PRIVATE.

    cp .env.example .env   # fill secrets (Kraken key: trade-only, NO withdrawals)
    make test && make fetch-history && make backtest && make mc

Commands: make run | status | stop | resume | analyze | heartbeat
Deploy:   docker compose up -d --build   (or install/duckbot.service)
Going live: 30+ passing dry days via make status, then DRY_RUN=false locally only.
