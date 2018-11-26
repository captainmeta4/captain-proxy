from flask import *
import os
import psycopg2
import secrets
import requests

db=psycopg2.connect(os.environ.get("DATABASE_URL"))
c=db.cursor()
c.execute("PREPARE AddDevice(text, text) AS INSERT INTO Devices (device_name, token) VALUES ($1, $2)")
c.execute("PREPARE CheckDevice(text) AS SELECT * FROM Devices WHERE token=$1")
c.execute("PREPARE DropDevice(text) AS DELETE FROM Devices WHERE token=$1")

app=Flask(__name__)

@app.route("/api/login", methods=["POST"])
def api_login():
    key=request.form.get("key")
    
    if key==os.environ.get("key"):
        url=request.form.get("url")
        resp=make_response(redirect("/proxy?url="+url))
        token=secrets.token_hex(32)
        resp.set_cookie("token", token)
        return resp

@app.route("/logout")
def logout():    
    resp=make_response(redirect("/login"))
    resp.set_cookie("token","")
    return resp

@app.route("/")
@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/proxy")
def proxy():
    
    token=request.cookies.get("token")
    if not token:
        return redirect("/login")
    
    c.execute("EXECUTE CheckDevice(%s)",(token,))
    entry=c.fetchone()
    if not entry:
        return redirect("/login")
    
    url=request.args.get("url")
    if not url:
        return redirect("/login")
    
    x=requests.get(url)
    return x.content
