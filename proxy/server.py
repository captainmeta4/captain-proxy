from flask import *
import os
import psycopg2
import secrets
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

db=psycopg2.connect(os.environ.get("DATABASE_URL"))
c=db.cursor()
c.execute("PREPARE AddDevice(text, text) AS INSERT INTO Devices (device_name, token) VALUES ($1, $2)")
c.execute("PREPARE CheckDevice(text) AS SELECT * FROM Devices WHERE token=$1")
c.execute("PREPARE DropDevice(text) AS DELETE FROM Devices WHERE token=$1")

app=Flask(__name__)

@app.route("/api/login", methods=["POST"])
def api_login():
    key=request.form.get("key")
    print(key)
    
    if key==os.environ.get("key"):
        url=request.form.get("url")
        name=request.form.get("device_name")
        token=secrets.token_hex(32)
        c.execute("EXECUTE AddDevice(%s,%s)", (name,token))
        db.commit()
        resp=make_response(redirect("/proxy?url="+url))
        resp.set_cookie("token", token)
        return resp
    else:
        abort(401)

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
        print('no token')
        return redirect("/login")
    
    c.execute("EXECUTE CheckDevice(%s)",(token,))
    entry=c.fetchone()
    if not entry:
        print('token not found')
        return redirect("/login")

    
    url=request.args.get("url")
    if not url:
        print('url not provided')
        return redirect("/login")
    else:
        print(url)

 
    x=requests.get(url, headers={"User-Agent":"Captain's Redirection service"})
    print(x.status_code)
    
    if x.headers["Content-Type"].startswith("text/html"):
        soup=BeautifulSoup(x.content, features="html.parser")
        o=urlparse(url)

        #replace src and href tags with http(s) notation
        for tag in soup.find_all(href=re.compile("^http")):
            tag['href']="/proxy?url="+tag['href']
        for tag in soup.find_all(src=re.compile("^http")):
            tag['src']="/proxy?url="+tag['src']

        #replace src and href tags using / notation to indicate a file on same domain
        for tag in soup.find_all(href=re.compile("^/[^/]")):
            tag['href']="/proxy?url="+o.scheme+"://"+o.netloc+tag['href']
        for tag in soup.find_all(src=re.compile("^/[^/]")):
            tag['src']="/proxy?url="+o.scheme+"://"+o.netloc+tag['src']

        #replace src and href tags using // notation to indicate a file on another domain
        for tag in soup.find_all(href=re.compile("^//")):
            tag['href']="/proxy?url="+o.scheme+":"+tag['href']
        for tag in soup.find_all(src=re.compile("^//")):
            tag['src']="/proxy?url="+o.scheme+":"+tag['src']
        resp=make_response(str(soup), x.status_code)
    else:
        resp=make_response(x.content, x.status_code)

    resp.headers["Content-Type"]=x.headers["Content-Type"]

    return resp
