# FINAL GoatMaster Server - Pro + Beginner
# Save as app.py or server.py
from flask import Flask, request, jsonify
from datetime import datetime, timezone
import time

app = Flask(__name__)

# --- CONFIG FOR YOUR 2 PLANS ---
# You go later connect this to Whop automatic, for now add keys manual
VALID_KEYS = {
    # Pro keys - $120
    "GOAT-PRO-12345": "pro",
    "GOAT-PRO-99999": "pro",
    # Beginner keys - $79
    "GOAT-BEGINNER-6789": "beginner",
}

# Memory - for real business use database, but this go work for now
users_db = {}

@app.route('/')
def home():
    return "GoatMaster API is Live 🐐"

@app.route('/check-key')
def check_key():
    key = request.args.get('key', '').strip()

    if key not in VALID_KEYS:
        return jsonify({"status": "This key is not correct", "allowed": False}), 403

    plan = VALID_KEYS[key] # pro or beginner

    # SERVER TIME - not phone time, so nobody fit cheat
    now_server = time.time()
    today_server = datetime.now(timezone.utc).date().isoformat()

    if key not in users_db:
        users_db[key] = {"last_trade": 0, "today": today_server, "count": 0}

    user = users_db[key]

    # Reset if new day (server day)
    if user["today"]!= today_server:
        user["today"] = today_server
        user["count"] = 0

    # --- RULES ---
    if plan == "pro":
        # Pro: 1 per MINUTE, 35 per DAY + AI allowed
        if now_server - user["last_trade"] < 60: # 60 sec = 1 min
            wait = int(60 - (now_server - user["last_trade"]))
            return jsonify({"status": f"Pro: Wait {wait}s (1 per minute)", "allowed": False}), 429
        if user["count"] >= 35:
            return jsonify({"status": "Daily limit 35 reached", "allowed": False}), 429

    else: # beginner
        # Beginner: 1 per 5 MINUTES, 10 per DAY, NO AI
        if now_server - user["last_trade"] < 300: # 300 sec = 5 min
            wait = int(300 - (now_server - user["last_trade"]))
            return jsonify({"status": f"Beginner: Wait {wait}s, upgrade to Pro for faster", "allowed": False}), 429
        if user["count"] >= 10:
            return jsonify({"status": "Beginner daily limit 10 reached - upgrade to Pro", "allowed": False}), 429

    # Allow trade
    user["last_trade"] = now_server
    user["count"] += 1

    return jsonify({
        "status": "Correct! Allow trade",
        "allowed": True,
        "plan": plan,
        "trades_left": (35 if plan == "pro" else 10) - user["count"],
        "server_time": datetime.now(timezone.utc).isoformat()
    })

if __name__ == '__main__':
    app.run()
