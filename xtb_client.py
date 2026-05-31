import websocket
import json
import ssl

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
        print(self.ws.recv())

    def get_price(self, symbol="US100"):
        cmd = {
            "command": "getSymbol",
            "arguments": {"symbol": symbol}
        }

        self.ws.send(json.dumps(cmd))
        return json.loads(self.ws.recv())

    def keep_alive(self):
        cmd = {"command": "ping"}
        self.ws.send(json.dumps(cmd))
        return self.ws.recv()
