from flask import Flask, jsonify
import os
from xtb_client import XTBClient

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot V2 + XTB beží 🚀"


@app.route("/price")
def price():
    login = os.getenv("XTB_LOGIN")
    password = os.getenv("XTB_PASSWORD")

    xtb = XTBClient(login, password)
    xtb.connect()

    us100 = xtb.get_price("US100")
    gold = xtb.get_price("GOLD")

    xtb.close()

    return jsonify({
        "US100": us100,
        "GOLD": gold
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
