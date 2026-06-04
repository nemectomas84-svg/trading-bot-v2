import os
import requests
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram not configured")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": text
    }

    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Telegram error:", e)
        
