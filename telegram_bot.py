import requests

BOT_TOKEN = "SEM_DAJ_TOKEN"
CHAT_ID = "SEM_DAJ_CHAT_ID"


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
