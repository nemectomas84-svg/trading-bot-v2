import requests

BOT_TOKEN = "8764608057:AAGkxxNSFVWKDYmCeP6L-_FG5Dq-NFa0-lk"
CHAT_ID = "1950077580"


def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": text
    }

    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram error:", e)
