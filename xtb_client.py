import websocket
import json
import ssl

class XTBClient:
    def __init__(self, login, password, demo=True):
        self.login = login
        self.password = password
        self.ws = None

        if demo:
            self.url = "wss://ws.xtb.com/demo"
        else:
            self.url = "wss://ws.xtb.com/real"

    def connect(self):
        try:
            print("🔌 Pripájam sa na:", self.url)

            self.ws = websocket.create_connection(
                self.url,
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
            response = self.ws.recv()

            print("✅ LOGIN RESPONSE:", response)

            return True

        except Exception as e:
            print("❌ CONNECTION ERROR:", e)
            self.ws = None
            return False

    def get_price(self, symbol="US100"):
        if not self.ws:
            print("❌ Not connected")
            return None

        try:
            cmd = {
                "command": "getSymbol",
                "arguments": {"symbol": symbol}
            }

            self.ws.send(json.dumps(cmd))
            return json.loads(self.ws.recv())

        except Exception as e:
            print("❌ GET PRICE ERROR:", e)
            return None

    def keep_alive(self):
        if not self.ws:
            return

        try:
            self.ws.send(json.dumps({"command": "ping"}))
            return self.ws.recv()
        except:
            pass
