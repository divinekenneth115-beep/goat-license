from flask import Flask, request, jsonify
from datetime import datetime, timezone
import time
import os
import requests

app = Flask(__name__)

# --- YOUR KEYS (We go connect Whop later) ---
VALID_KEYS = {
    "GOAT-PRO-12345": "pro",
    "GOAT-PRO-99999": "pro",
    "GOAT-BEGINNER-6789": "beginner"
}

users_db = {}

# Telegram Token go come from Render Env, so deploy no go fail
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None

@app.route('/')
def home():
    return "GoatMaster API is Live - License + Telegram Ready"

@app.route('/check-key')
def check_key():
    key = request.args.get('key','').strip()
    if key not in VALID_KEYS:
        return jsonify({"status":"Invalid key","allowed":False,"ai_allowed":False}),403

    plan = VALID_KEYS[key]
    now_server = time.time()
    today_server = datetime.now(timezone.utc).date().isoformat()

    if key not in users_db:
        users_db[key] = {"last_trade":0,"today":today_server,"count":0}

    user = users_db[key]
    if user["today"]!= today_server:
        user["today"] = today_server
        user["count"] = 0

    if plan == "pro":
        if now_server - user["last_trade"] < 60:
            wait = int(60 - (now_server - user["last_trade"]))
            return jsonify({"status":f"Pro: Wait {wait}s","allowed":False,"ai_allowed":True,"plan":"pro"}),429
        if user["count"] >= 35:
            return jsonify({"status":"Daily 35 reached","allowed":False,"ai_allowed":True,"plan":"pro"}),429
    else:
        if now_server - user["last_trade"] < 300:
            wait = int(300 - (now_server - user["last_trade"]))
            return jsonify({"status":f"Beginner: Wait {wait}s - No AI","allowed":False,"ai_allowed":False,"plan":"beginner"}),429
        if user["count"] >= 10:
            return jsonify({"status":"Beginner limit 10 reached","allowed":False,"ai_allowed":False,"plan":"beginner"}),429

    user["last_trade"] = now_server
    user["count"] += 1

    if plan == "pro":
        return jsonify({"status":"Pro - AI Enabled","allowed":True,"ai_allowed":True,"plan":"pro","trades_left":35-user["count"]})
    else:
        return jsonify({"status":"Beginner - No AI, Simple only","allowed":True,"ai_allowed":False,"plan":"beginner","trades_left":10-user["count"]})

# --- TELEGRAM PART - Ready for anytime you add Token ---
@app.route('/telegram', methods=['POST'])
def telegram_webhook():
    if not TELEGRAM_TOKEN:
        return jsonify({"status":"Telegram not configured yet - add TELEGRAM_TOKEN in Render"}),200

    data = request.get_json()
    # Here later we go add AI logic for Pro only
    # For now e go just reply
    try:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text","")
        reply = f"GoatMaster received: {text} - AI check coming soon"
        requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id":chat_id,"text":reply})
    except:
        pass
    return jsonify({"ok":True})

if __name__ == '__main__':
    app.run()
