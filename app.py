from flask import Flask, request, jsonify
import sqlite3, secrets, string, os
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
def init_db():
 c=sqlite3.connect("licenses.db")
 c.execute("CREATE TABLE IF NOT EXISTS licenses (key TEXT PRIMARY KEY, account INTEGER DEFAULT 0)")
 c.commit()
 c.close()
init_db()
def gen_code():
 return "GOAT-"+ "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
@app.route("/")
def home():
 return {"status":"GoatMaster Running"}
@app.route("/whop-webhook",methods=["POST"])
def whop():
 code=gen_code()
 con=sqlite3.connect("licenses.db")
 con.execute("INSERT INTO licenses VALUES (?,0)",(code,))
 con.commit()
 con.close()
 return jsonify({"code":code})
@app.route("/verify",methods=["GET","POST"])
@app.route("/check-license")
def verify():
 data=request.get_json(silent=True) or {}
 code=(request.args.get("code") or data.get("key") or data.get("code") or "").strip()
 if not code:
  return jsonify({"valid":False})
 con=sqlite3.connect("licenses.db")
 cur=con.cursor()
 cur.execute("SELECT account FROM licenses WHERE key=?",(code,))
 r=cur.fetchone()
 if not r:
  con.close()
  return jsonify({"valid":False})
 if r[0]==0:
  cur.execute("UPDATE licenses SET account=1 WHERE key=?",(code,))
  con.commit()
  con.close()
  return jsonify({"valid":True})
 con.close()
 return jsonify({"valid":True})
if __name__=="__main__":
 app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
