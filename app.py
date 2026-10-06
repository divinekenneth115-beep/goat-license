import os
import time
from datetime import datetime, timezone
from flask import Flask, request, jsonify
app = Flask(__name__)
VALID_KEYS = {"GOAT-PRO-12345": "pro","GOAT-BEGINNER-6789": "beginner"}
db = {}
@app.route('/')
def home():
    return "GoatMaster API is Live"
@app.route('/check-key')
def check_key():
    key = request.args.get('key','').strip()
    if key not in VALID_KEYS:
        return jsonify(allowed=False, ai_allowed=False, status="Invalid Key"), 403
    plan = VALID_KEYS[key]
    now = time.time()
    today = datetime.now(timezone.utc).date().isoformat()
    if key not in db:
        db[key] = {"last": 0, "today": today, "count": 0}
    user = db[key]
    if user["today"]!= today:
        user["today"] = today
        user["count"] = 0
    if plan == "pro":
        if now - user["last"] < 60:
            return jsonify(allowed=False, ai_allowed=True, plan=plan, status="Wait 60s"), 429
        if user["count"] >= 35:
            return jsonify(allowed=False, ai_allowed=True, plan=plan, status="Daily Limit 35 Reached"), 429
    else:
        if now - user["last"] < 300:
            return jsonify(allowed=False, ai_allowed=False, plan=plan, status="Wait 5min - No AI"), 429
        if user["count"] >= 10:
            return jsonify(allowed=False, ai_allowed=False, plan=plan, status="Daily Limit 10 Reached"), 429
    user["last"] = now
    user["count"] += 1
    left = (35 if plan == "pro" else 10) - user["count"]
    ai_allowed = True if plan == "pro" else False
    return jsonify(allowed=True, ai_allowed=ai_allowed, plan=plan, trades_left=left, status="Pro AI Enabled" if ai_allowed else "Beginner No AI")
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
