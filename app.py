from flask import Flask, request, jsonify
import time
from datetime import datetime, timezone
import os
import requests

app = Flask(__name__)

VALID_KEYS = {
  "GOAT-PRO-12345": "pro",
  "GOAT-BEGINNER-6789": "beginner"
}

db = {}

@app.route('/')
def home():
    return "GoatMaster API Live"

@app.route('/check-key')
def check():
    k = request.args.get('key','').strip()
    if k not in VALID_KEYS:
        return jsonify(allowed=False, ai_allowed=False, status="Invalid"),403
    plan = VALID_KEYS[k]
    now = time.time()
    today = datetime.now(timezone.utc).date().isoformat()
    if k not in db:
        db[k] = {"last":0,"today":today,"count":0}
    u = db[k]
    if u["today"]!= today:
        u["today"]=today
        u["count"]=0
    if plan=="pro":
        if now - u["last"] < 60:
            return jsonify(allowed=False, ai_allowed=True, plan=plan, status="Wait 60s"),429
        if u["count"] >= 35:
            return jsonify(allowed=False, ai_allowed=True, plan=plan, status="Limit 35"),429
    else:
        if now - u["last"] < 300:
            return jsonify(allowed=False, ai_allowed=False, plan=plan, status="Wait 5min No AI"),429
        if u["count"] >= 10:
            return jsonify(allowed=False, ai_allowed=False, plan=plan, status="Limit 10"),429
    u["last"]=now
    u["count"]+=1
    left = (35 if plan=="pro" else 10) - u["count"]
    ai = True if plan=="pro" else False
    msg = "Pro AI Enabled" if ai else "Beginner No AI"
    return jsonify(allowed=True, ai_allowed=ai, plan=plan, trades_left=left, status=msg)

if __name__ == '__main__':
    app.run()
