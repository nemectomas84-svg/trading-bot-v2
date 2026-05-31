import websocket
import json
import ssl
import time


class XTBClient:
    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.ws = None

    def connect(self):
        try:
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

            if response.get("status"):
                print("✅ XTB LOGIN OK")
            else:
                print("❌ LOGIN FAILED:", response)

        except Exception as e:
            print("❌ CONNECTION ERROR:", e)

    def get_price(self, symbol="US100"):
        try:
            cmd = {
                "command": "getSymbol",
                "arguments": {"symbol": symbol}
            }

            self.ws.send(json.dumps(cmd))
            response = json.loads(self.ws.recv())

            if response.get("status"):
                return response["returnData"]
            else:
                print("❌ PRICE ERROR:", response)
                return None

        except Exception as e:
            print("❌ GET PRICE ERROR:", e)
            return None

    def keep_alive(self):
        try:
            self.ws.send(json.dumps({"command": "ping"}))
            return self.ws.recv()
        except:
            print("⚠️ Keep alive failed")

    def reconnect(self):
        print("🔄 Reconnecting...")
        time.sleep(3)
        self.connect()
