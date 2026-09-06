.PHONY: test run price health status stop resume analyze heartbeat \
        fetch-history backtest mc docker-up docker-down clean

test:
	python3 test_all.py
run:
	python3 main.py cycle
price:
	python3 main.py price
health:
	python3 main.py health
status:
	python3 main.py status
stop:
	python3 main.py stop
resume:
	python3 main.py resume
analyze:
	python3 analyze.py
heartbeat:
	python3 heartbeat.py
fetch-history:
	python3 fetch_data.py --days 365
backtest:
	python3 backtest.py data/backtest/BTC_USD_1h.csv
mc:
	python3 -m duckbot.monte_carlo
docker-up:
	docker compose up -d --build
docker-down:
	docker compose down
clean:
	rm -rf data logs reports __pycache__
