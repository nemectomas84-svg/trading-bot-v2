import websocket
import json
import ssl
import os
import time
import requests
from flask import Flask

app = Flask(__name__)

# =========================
# TELEGRAM
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except Exception as e:
        print("Telegram error:", e)

# =========================
# XTB CLIENT
# =========================
class XTBClient:
    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.ws = None

    def connect(self):
        self.ws = websocket.create_connection(
            "wss://ws.xtb.com/real",
            sslopt={"cert_reqs": ssl.CERT_NONE}
        )

        login_cmd = {
            "command": "login",
            "arguments": {
                "userId": self.login,
                "password": self.password
            }
        }

        self.ws.send(json.dumps(login_cmd))
        response = json.loads(self.ws.recv())
        print("Login response:", response)

    def get_price(self, symbol="US100"):
        cmd = {
            "command": "getSymbol",
            "arguments": {"symbol": symbol}
        }

        self.ws.send(json.dumps(cmd))
        return json.loads(self.ws.recv())

# =========================
# STRATEGY
# =========================
prices = []
MAX_CANDLES = 100

def update_price(xtb):
    global prices

    data = xtb.get_price("US100")
    price = data["returnData"]["ask"]

    prices.append(price)

    if len(prices) > MAX_CANDLES:
        prices.pop(0)

    return price

def calculate_ema(period=20):
    if len(prices) < period:
        return None

    k = 2 / (period + 1)
    ema = prices[0]

    for p in prices[1:]:
        ema = p * k + ema * (1 - k)

    return ema

def get_signal(price, ema):
    if ema is None:
        return None

    if price > ema:
        return "LONG"
    elif price < ema:
        return "SHORT"

    return None

# =========================
# MAIN BOT LOOP
# =========================
xtb = None

@app.route("/")
def home():
    return "XTB BOT V2 beží 🚀"

@app.route("/start")
def start():
    global xtb

    login = os.getenv("XTB_LOGIN")
    password = os.getenv("XTB_PASSWORD")

    xtb = XTBClient(login, password)
    xtb.connect()

    trade = None
    trailing_distance = 40

    send("🤖 BOT STARTED")

    while True:
        try:
            price = update_price(xtb)
            ema = calculate_ema()
            signal = get_signal(price, ema)

            print(f"Price: {price}, EMA: {ema}, Signal: {signal}")

            # =====================
            # NEW TRADE
            # =====================
            if trade is None and signal:
                if signal == "LONG":
                    trail = price - trailing_distance
                else:
                    trail = price + trailing_distance

                trade = {
                    "direction": signal,
                    "entry": price,
                    "trail": trail
                }

                send(f"📈 NEW TRADE\n{signal}\nEntry: {price:.2f}\nTrail: {trail:.2f}")

            # =====================
            # EXISTING TRADE
            # =====================
            if trade:
                if trade["direction"] == "LONG":
                    new_trail = price - trailing_distance

                    if new_trail > trade["trail"]:
                        trade["trail"] = new_trail
                        send(f"🔄 TRAIL LONG: {new_trail:.2f}")

                    if price <= trade["trail"]:
                        send(f"❌ EXIT LONG: {price:.2f}")
                        trade = None

                elif trade["direction"] == "SHORT":
                    new_trail = price + trailing_distance

                    if new_trail < trade["trail"]:
                        trade["trail"] = new_trail
                        send(f"🔄 TRAIL SHORT: {new_trail:.2f}")

                    if price >= trade["trail"]:
                        send(f"❌ EXIT SHORT: {price:.2f}")
                        trade = None

            time.sleep(5)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
