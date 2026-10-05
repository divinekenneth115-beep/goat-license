from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3, secrets, string, os, requests

app = Flask(__name__)
CORS(app)

# === PASTE YOUR KEYS HERE ===
FINNHUB_KEY = db1rsc1r01qrufhdrflgdb1rsc1r01qrufhdrfm0
OPENROUTER_KEY = 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

def init_db():
    c=sqlite3.connect("licenses.db")
    c.execute("CREATE TABLE IF NOT EXISTS licenses (code TEXT PRIMARY KEY, account TEXT)")
    c.commit()
    c.close()
init_db()

def gen():
    return "GOAT-"+ "".join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(12))

@app.route("/")
def home():
    return {"status":"GoatMaster Running - AI + License Active"}

@app.route("/whop-webhook",methods=["POST"])
def whop():
    k=gen()
    con=sqlite3.connect("licenses.db")
    con.execute("INSERT INTO licenses VALUES (?,?)",(k,None))
    con.commit()
    con.close()
    return jsonify({"code":k})

@app.route("/verify",methods=["GET","POST"])
@app.route("/check-license",methods=["GET","POST"])
def verify():
    j=request.get_json(silent=True) or {}
    code=(request.args.get("code") or j.get("key") or "").strip()
    account=str(request.args.get("account") or j.get("account") or "").strip()
    if not code:
        return jsonify({"valid":False})
    con=sqlite3.connect("licenses.db")
    cur=con.cursor()
    cur.execute("SELECT account FROM licenses WHERE code=?",(code,))
    r=cur.fetchone()
    if not r:
        con.close()
        return jsonify({"valid":False})
    saved_account=r[0]
    # First time - lock to account
    if saved_account is None or saved_account=="":
        if account:
            cur.execute("UPDATE licenses SET account=? WHERE code=?",(account,code))
            con.commit()
            con.close()
            return jsonify({"valid":True, "msg":"Account locked"})
        con.close()
        return jsonify({"valid":True})
    # Check if account matches
    if saved_account==account:
        con.close()
        return jsonify({"valid":True})
    else:
        con.close()
        return jsonify({"valid":False, "reason":"Account mismatch"})

@app.route("/ai-signal")
def ai_signal():
    symbol=request.args.get("symbol","XAUUSD")
    # 1. Get news from Finnhub
    news_text="No news"
    try:
        url=f"https://finnhub.io/api/v1/news?category=forex&token={FINNHUB_KEY}"
        resp=requests.get(url,timeout=10).json()
        headlines=[f"{n.get('headline','')}: {n.get('summary','')[:100]}" for n in resp[:5]]
        news_text=" | ".join(headlines)
    except Exception as e:
        news_text=f"Finnhub error: {e}"

    # 2. Ask OpenRouter AI
    try:
        prompt=f"You are a professional Gold trader. Symbol {symbol}. News: {news_text}. Decide BUY, SELL or NO_TRADE. Give reason in 1 short line. Format: DECISION: BUY/SELL/NO_TRADE | REASON:..."
        headers={"Authorization":f"Bearer {OPENROUTER_KEY}","Content-Type":"application/json"}
        data={"model":"openai/gpt-4o-mini","messages":[{"role":"user","content":prompt}]}
        r=requests.post("https://openrouter.ai/api/v1/chat/completions",headers=headers,json=data,timeout=20)
        ai_answer=r.json()["choices"][0]["message"]["content"]
        return jsonify({"symbol":symbol,"news":news_text,"ai":ai_answer})
    except Exception as e:
        return jsonify({"error":str(e),"news":news_text})

@app.route("/reset-license")
def reset_license():
    code=request.args.get("code","").strip()
    if not code: return "Add?code=GOAT-XXX"
    con=sqlite3.connect("licenses.db")
    con.execute("UPDATE licenses SET account=NULL WHERE code=?",(code,))
    con.commit()
    con.close()
    return f"License {code} reset - buyer can use new account"

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
