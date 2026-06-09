from flask import Flask, jsonify, request
import subprocess
import os
import json

app = Flask(__name__)

TELEGRAM_STATE_FILE = "telegram_enabled.txt"
API_KEY = "change-this-secret-key"
TRADER_STATE_FILE = "data/trader_state.json"
BOT_SERVICE_NAME = "btc-bot"


def check_auth():
    key = request.headers.get("X-API-KEY")
    return key == API_KEY


def run_command(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
        )

        return {
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        }
    except Exception as e:
        return {
            "returncode": 1,
            "stdout": "",
            "stderr": str(e),
        }


def is_bot_running():
    result = run_command(["systemctl", "is-active", BOT_SERVICE_NAME])
    return result["stdout"] == "active"


def telegram_enabled():
    if not os.path.exists(TELEGRAM_STATE_FILE):
        return True

    with open(TELEGRAM_STATE_FILE, "r") as f:
        return f.read().strip() == "1"


def get_trader_state():
    if not os.path.exists(TRADER_STATE_FILE):
        return None

    try:
        with open(TRADER_STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return None


@app.route("/status", methods=["GET"])
def status():
    if not check_auth():
        return jsonify({"error": "unauthorized"}), 401

    return jsonify({
        "bot_running": is_bot_running(),
        "telegram_enabled": telegram_enabled(),
        "trader": get_trader_state()
    })


@app.route("/start", methods=["POST"])
def start_bot():
    if not check_auth():
        return jsonify({"error": "unauthorized"}), 401

    if is_bot_running():
        return jsonify({"status": "already_running"})

    result = run_command(["systemctl", "start", BOT_SERVICE_NAME])

    if result["returncode"] != 0:
        return jsonify({
            "status": "error",
            "message": result["stderr"],
            "command_output": result,
        }), 500

    return jsonify({
        "status": "started",
        "bot_running": is_bot_running()
    })


@app.route("/stop", methods=["POST"])
def stop_bot():
    if not check_auth():
        return jsonify({"error": "unauthorized"}), 401

    if not is_bot_running():
        return jsonify({"status": "not_running"})

    result = run_command(["systemctl", "stop", BOT_SERVICE_NAME])

    if result["returncode"] != 0:
        return jsonify({
            "status": "error",
            "message": result["stderr"],
            "command_output": result,
        }), 500

    return jsonify({
        "status": "stopped",
        "bot_running": is_bot_running()
    })


@app.route("/telegram", methods=["POST"])
def toggle_telegram():
    if not check_auth():
        return jsonify({"error": "unauthorized"}), 401

    data = request.json
    enabled = data.get("enabled", True)

    with open(TELEGRAM_STATE_FILE, "w") as f:
        f.write("1" if enabled else "0")

    return jsonify({"telegram_enabled": enabled})


@app.route("/logs", methods=["GET"])
def logs():
    if not check_auth():
        return jsonify({"error": "unauthorized"}), 401

    if not os.path.exists("logs/bot_output.log"):
        return jsonify({"logs": ""})

    with open("logs/bot_output.log", "r") as f:
        lines = f.readlines()[-150:]

    return jsonify({"logs": "".join(lines)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
