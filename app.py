from flask import Flask, request, jsonify
import sqlite3, secrets, string, time, os
app = Flask(__name__)
def init_db():
    c=sqlite3.connect("licenses.db")
    c.execute("CREATE TABLE IF NOT EXISTS licenses (code TEXT PRIMARY KEY, account INTEGER, plan TEXT, created INTEGER)")
    c.commit()
    c.close()
init_db()
def gen_code():
    return "GOAT-"+"".join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(12))
@app.route("/")
def home():
    return jsonify({"status":"GoatMaster Running","ok":True})
@app.route("/whop-webhook",methods=["POST"])
def whop():
    code=gen_code()
    con=sqlite3.connect("licenses.db")
    con.execute("INSERT INTO licenses VALUES (?,?,?,?)",(code,0,"starter",int(time.time())))
    con.commit()
    con.close()
    return jsonify({"code":code})
@app.route("/check-license")
def check():
    code=request.args.get("code","")
    acc=int(request.args.get("account",0) or 0)
    con=sqlite3.connect("licenses.db")
    cur=con.cursor()
    cur.execute("SELECT account FROM licenses WHERE code=?",(code,))
    r=cur.fetchone()
    if not r:
        con.close()
        return jsonify({"valid":False})
    if r[0]==0:
        cur.execute("UPDATE licenses SET account=? WHERE code=?",(acc,code))
        con.commit()
        con.close()
        return jsonify({"valid":True})
    con.close()
    return jsonify({"valid":r[0]==acc})
if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
