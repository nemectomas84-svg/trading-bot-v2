from flask import Flask, jsonify, request
import subprocess
import os
import signal

app = Flask(__name__)

BOT_PROCESS_FILE = "bot_process.pid"
TELEGRAM_STATE_FILE = "telegram_enabled.txt"
API_KEY = "change-this-secret-key"


def check_auth():
    key = request.headers.get("X-API-KEY")
    return key == API_KEY


def is_bot_running():
    if not os.path.exists(BOT_PROCESS_FILE):
        return False

    try:
        with open(BOT_PROCESS_FILE, "r") as f:
            pid = int(f.read().strip())

        os.kill(pid, 0)
        return True
    except:
        return False


def get_bot_pid():
    if not os.path.exists(BOT_PROCESS_FILE):
        return None

    with open(BOT_PROCESS_FILE, "r") as f:
        return int(f.read().strip())


def telegram_enabled():
    if not os.path.exists(TELEGRAM_STATE_FILE):
        return True

    with open(TELEGRAM_STATE_FILE, "r") as f:
        return f.read().strip() == "1"


@app.route("/status", methods=["GET"])
def status():
    if not check_auth():
        return jsonify({"error": "unauthorized"}), 401

    return jsonify({
        "bot_running": is_bot_running(),
        "telegram_enabled": telegram_enabled()
    })


@app.route("/start", methods=["POST"])
def start_bot():
    if not check_auth():
        return jsonify({"error": "unauthorized"}), 401

    if is_bot_running():
        return jsonify({"status": "already_running"})

    process = subprocess.Popen(
        ["python3", "app.py"],
        stdout=open("bot_output.log", "a"),
        stderr=open("bot_error.log", "a"),
        preexec_fn=os.setsid
    )

    with open(BOT_PROCESS_FILE, "w") as f:
        f.write(str(process.pid))

    return jsonify({"status": "started", "pid": process.pid})


@app.route("/stop", methods=["POST"])
def stop_bot():
    if not check_auth():
        return jsonify({"error": "unauthorized"}), 401

    if not is_bot_running():
        return jsonify({"status": "not_running"})

    pid = get_bot_pid()

    try:
        os.killpg(os.getpgid(pid), signal.SIGTERM)
    except:
        pass

    if os.path.exists(BOT_PROCESS_FILE):
        os.remove(BOT_PROCESS_FILE)

    return jsonify({"status": "stopped"})


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

    if not os.path.exists("bot_output.log"):
        return jsonify({"logs": ""})

    with open("bot_output.log", "r") as f:
        lines = f.readlines()[-150:]

    return jsonify({"logs": "".join(lines)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
