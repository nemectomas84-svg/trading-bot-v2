import requests
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TELEGRAM_STATE_FILE = "telegram_enabled.txt"


def is_telegram_enabled():
    if not os.path.exists(TELEGRAM_STATE_FILE):
        return True

    with open(TELEGRAM_STATE_FILE, "r") as f:
        return f.read().strip() == "1"


def send_message(text):
    if not is_telegram_enabled():
        print("Telegram disabled:", text)
        return

    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram not configured")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": text
    }

    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram error:", e)
