"""Fire-and-forget Telegram/Discord push. Never raises."""
import os
import requests

_T = (os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID"))
_D = os.getenv("DISCORD_WEBHOOK_URL")

def send(message: str, urgent: bool = False) -> bool:
    ok = True
    token, chat = _T
    if token and chat:
        try:
            r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                              json={"chat_id": chat, "text": message,
                                    "parse_mode": "Markdown"}, timeout=10)
            ok &= r.ok
        except requests.RequestException:
            ok = False
    if _D:
        try:
            r = requests.post(_D, json={"username": "DuckBot",
                                        "content": message, "tts": urgent}, timeout=10)
            ok &= r.ok
        except requests.RequestException:
            ok = False
    return ok

def order_filled(side, price, amount):
    return send(f"*{side}* filled @ ${price:,.2f} — {amount:.8f} BTC")

def stop_loss_hit(price):
    return send(f"🚨 STOP LOSS @ ${price:,.2f} — position closed.", urgent=True)
