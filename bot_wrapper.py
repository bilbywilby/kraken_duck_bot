"""Long-running loop for Docker/systemd: cycle every 5 minutes."""
import time

from duckbot.cli import main
from duckbot.safety_controls import is_kill_switch_active

INTERVAL_SECONDS = 300

if __name__ == "__main__":
    while True:
        try:
            if is_kill_switch_active():
                print("Kill switch active — idling.")
            else:
                main(["cycle"])
        except Exception as e:
            print(f"Cycle error (will retry): {e}")
        time.sleep(INTERVAL_SECONDS)
