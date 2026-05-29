
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot V2 beží 🚀"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    symbol = data.get("symbol")
    direction = data.get("direction")
    entry = data.get("entry")
    sl = data.get("sl")
    trailing = data.get("trailing")

    print(f"📈 SIGNAL: {symbol} {direction} ENTRY {entry}")

    return jsonify({"status": "ok"})
    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
