from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3, secrets, string, os, requests, time
from datetime import datetime
app = Flask(__name__)
CORS(app)
FINNHUB_KEY= "db1rsc1r01qrufhdrflgdb1rsc1r01qrufhdrfm0"
OPENROUTER_KEY = "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"

def init_db():
    c = sqlite3.connect("licenses.db")
    c.execute("CREATE TABLE IF NOT EXISTS licenses (code TEXT PRIMARY KEY, account TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS usage (code TEXT, date TEXT, count INTEGER, last_time REAL, PRIMARY KEY (code, date))")
    c.commit()
    c.close()
init_db()
def gen():
    return "GOAT-" + "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(12))
@app.route("/")
def home():
    return {"status": "GoatMaster LIVE - Go to /live"}
@app.route("/live")
def live_dashboard():
    return """<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>GoatMaster LIVE</title><style>body{background:#0a0a0a;color:white;font-family:Arial;text-align:center;padding:20px}.live{color:red;animation:blink 1s infinite;font-weight:bold}@keyframes blink{0%{opacity:1}50%{opacity:0.3}}.card{background:#1a1a1a;border:1px solid gold;border-radius:15px;padding:20px;margin:20px auto;max-width:500px}.price{font-size:36px;color:gold}</style></head><body><h2><span class="live">LIVE</span> GoatMaster AI</h2><p>Watching XAUUSD 24/7</p><div class="card"><div>Gold Price</div><div class="price" id="price">$---</div><div id="decision">AI Scanning...</div><div id="reason" style="color:#aaa;font-size:13px;margin-top:10px"></div><div id="next" style="color:gold;margin-top:15px">Next scan in 60s</div></div><script>let cd=60;async function up(){try{let p=await fetch('https://finnhub.io/api/v1/quote?symbol=OANDA:XAU_USD&token=PUT_YOUR_FINNHUB_KEY_HERE').then(r=>r.json());if(p.c)document.getElementById('price').innerText='$'+p.c.toFixed(2);}catch(e){}try{let a=await fetch('/ai-signal?code=DEMO-LIVE&symbol=XAUUSD').then(r=>r.json());if(a.ai)document.getElementById('decision').innerText=a.ai;if(a.news)document.getElementById('reason').innerText=a.news.substring(0,150);}catch(e){}cd=60;}setInterval(()=>{cd--;document.getElementById('next').innerText='Next scan in '+cd+'s';if(cd<=0)up();},1000);up();</script></body></html>"""
@app.route("/whop-webhook", methods=["POST"])
def whop():
    k = gen()
    con = sqlite3.connect("licenses.db")
    con.execute("INSERT INTO licenses VALUES (?,?)", (k, None))
    con.commit()
    con.close()
    return jsonify({"code": k})
@app.route("/verify", methods=["GET", "POST"])
@app.route("/check-license", methods=["GET", "POST"])
def verify():
    j = request.get_json(silent=True) or {}
    code = (request.args.get("code") or j.get("key") or "").strip()
    account = str(request.args.get("account") or j.get("account") or "").strip()
    if not code:
        return jsonify({"valid": False})
    con = sqlite3.connect("licenses.db")
    cur = con.cursor()
    cur.execute("SELECT account FROM licenses WHERE code=?", (code,))
    r = cur.fetchone()
    if not r:
        con.close()
        return jsonify({"valid": False})
    saved = r[0]
    if saved is None or saved == "":
        if account:
            cur.execute("UPDATE licenses SET account=? WHERE code=?", (account, code))
            con.commit()
            con.close()
            return jsonify({"valid": True})
        con.close()
        return jsonify({"valid": True})
    con.close()
    return jsonify({"valid": True}) if saved == account else jsonify({"valid": False, "reason": f"Locked to {saved}"})
@app.route("/ai-signal")
def ai_signal():
    code = request.args.get("code") or request.args.get("key") or "DEMO-LIVE"
    account = request.args.get("account", "").strip()
    symbol = request.args.get("symbol", "XAUUSD")
    con = sqlite3.connect("licenses.db")
    cur = con.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    now = time.time()
    if code!= "DEMO-LIVE":
        cur.execute("SELECT account FROM licenses WHERE code=?", (code,))
        r = cur.fetchone()
        if not r:
            con.close()
            return jsonify({"error": "Invalid license"}), 403
        saved = r[0]
        if saved and saved!= "" and saved!= account and account!= "":
            con.close()
            return jsonify({"error": f"Locked to {saved}", "DECISION": "NO_TRADE"}), 403
        if (saved is None or saved == "") and account!= "":
            cur.execute("UPDATE licenses SET account=? WHERE code=?", (account, code))
            con.commit()
        cur.execute("SELECT count, last_time FROM usage WHERE code=? AND date=?", (code, today))
        row = cur.fetchone()
        if row:
            count, last_time = row
            if now - last_time < 60:
                con.close()
                return jsonify({"error": f"Wait {int(60-(now-last_time))}s", "DECISION": "NO_TRADE"}), 429
            if count >= 35:
                con.close()
                return jsonify({"error": "35/day limit", "DECISION": "NO_TRADE"}), 429
            cur.execute("UPDATE usage SET count=count+1, last_time=? WHERE code=? AND date=?", (now, code, today))
        else:
            cur.execute("INSERT INTO usage VALUES (?,?,1,?)", (code, today, now))
        con.commit()
    con.close()
    news_text = "No major news"
    try:
        url = f"https://finnhub.io/api/v1/news?category=forex&token={FINNHUB_KEY}"
        resp = requests.get(url, timeout=8).json()
        news_text = " | ".join([n.get('headline', '') for n in resp[:3]])
    except:
        pass
    try:
        prompt = f"Gold trader {symbol}. News: {news_text}. Decision BUY/SELL/NO_TRADE. Short reason."
        headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
        data = {"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]}
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=15)
        ai_answer = r.json()["choices"][0]["message"]["content"]
        return jsonify({"ai": ai_answer, "news": news_text})
    except Exception as e:
        return jsonify({"error": str(e), "ai": "DECISION: NO_TRADE | API error"})
@app.route("/reset-license")
def reset_license():
    code = request.args.get("code", "").strip()
    con = sqlite3.connect("licenses.db")
    con.execute("UPDATE licenses SET account=NULL WHERE code=?", (code,))
    con.execute("DELETE FROM usage WHERE code=?", (code,))
    con.commit()
    con.close()
    return f"License {code} reset OK"
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
