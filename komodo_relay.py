from flask import Flask, request, jsonify
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"
SOURCE_NAME = ""


container_status_cache = {}

# Time Format
def parse_timestamp(ts):
    try:
        ts = float(ts)
        if ts > 1e12:  # milidetik
            ts /= 1000
        utc_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        local_dt = utc_dt.astimezone(ZoneInfo("Asia/Jakarta"))
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        now = datetime.now(ZoneInfo("Asia/Jakarta"))
        return now.strftime("%Y-%m-%d %H:%M:%S")

# Telegram Message 
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"[ERROR] Gagal kirim Telegram: {e}")

# Container status
def determine_container_status(container_name, event_status):
    prev_status = container_status_cache.get(container_name, "Unknown")

    if event_status.lower() in ["active", "down", "stopped"]:
        new_status = "Down"
    elif event_status.lower() in ["resolved", "up", "running"]:
        new_status = "Up"
    else:
        new_status = "Unknown"

    if prev_status == "Down" and new_status == "Up":
        new_status = "Restart"

    container_status_cache[container_name] = new_status
    return new_status

# Format alert
def format_alert(data):
    alert_type = data.get("type", "Unknown")
    target = data.get("target", {})
    severity = data.get("severity", "INFO")
    event_status = data.get("status", "Unknown")
    ts = data.get("timestamp") or data.get("time") or datetime.now().timestamp()
    parsed_time = parse_timestamp(ts)

    if isinstance(target, dict):
        target_name = target.get("name") or target.get("id") or "Unknown"
    else:
        target_name = str(target)

    if alert_type.lower() == "containerstatechange":
        status_label = determine_container_status(target_name, event_status)
    else:
        status_label = event_status.capitalize()

    if severity.lower() == "critical":
        icon = "🚨"
    elif severity.lower() == "warning":
        icon = "⚠️"
    elif severity.lower() == "ok":
        icon = "✅"
    else:
        icon = "ℹ️"

    # Format pesan
    message = (
        f"{icon} <b>Komodo Alert ({severity.upper()})</b>\n"
        f" <b>Time:</b> {parsed_time}\n"
        f" <b>Type:</b> {alert_type}\n"
        f" <b>Target:</b> {target_name}\n"
        f" <b>Status:</b> {status_label}\n"
        f" <b>Source:</b> {SOURCE_NAME}"
    )

    print(f"[DEBUG] New Alert: {target_name} | Status: {status_label}")  # log tambahan
    return message

# Endpoint
@app.route("/komodo-alert", methods=["POST"])
def komodo_alert():
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    text = format_alert(data)
    send_telegram_message(text)
    return jsonify({"status": "ok", "received": data}), 200

# Main
if __name__ == "__main__":
    print("[INFO] Komodo Relay Advanced running on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)
