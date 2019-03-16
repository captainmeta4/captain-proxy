from flask import *
import os
import requests
import praw
from urllib.parse import urlparse
from bs4 import BeautifulSoup

r=praw.Reddit(client_id=os.environ.get("client_id"),
              client_secret=os.environ.get("client_secret"),
              redirect_uri="https://proxy.captainmeta4.me/oauth",
              user_agent="captain's personal authenticator by captainmeta4")

HEADERS={"User-Agent": "Captain Metaphor's personal redirection toolkit"}
DOMAIN=os.environ.get("domain")
BASE="https://"+DOMAIN+"/web/?url="

tokens=[]

app=Flask(__name__)

@app.route("/login")
def login():
    return redirect(r.auth.url(["identity"],"x"))


@app.route("/oauth")
def oauth():
    code = request.args.get("code")
    token=r.auth.authorize(code)
    
    u=r.user.me()
    if not u.name=="captainmeta4":
        return "You are not authorized to use this application", 401
    
    resp=make_response(redirect("/web?url=https://reddit.com"))
    resp.set_cookie("token",token,domain=os.environ.get("domain"))
    
    TOKENS.append(token)
    
   
    return resp
    
@app.route("/web/", methods=["GET"])
def web_url_get():
    
    token=request.cookies.get("token")
    
    if not token:
        return redirect("/login")
    
    if token not in TOKENS:
        try:
            r=praw.Reddit(client_id=CLIENT_ID,
                     client_secret=CLIENT_SECRET,
                     refresh_token=token,
                     user_agent="captain's personal authenticator by captainmeta4")
            u=r.user.me()
            if not u.name=="captainmeta4":
                return redirect("/login")
            TOKENS.append(token)
        except:
            return redirect("/login")
      
    
    url=request.args.get("url")
    x= requests.get(url, headers=HEADERS)
    
    #get master data for modifying hrefs and src attributes
    o=urlparse(url)
    
    if x.headers["Content-Type"].startswith("text/html"):
        soup=BeautifulSoup(x.content, features="html.parser")
        
        
        for tag in soup.find_all(href=True):
            p=urlparse(tag['href'])
            tag['href']=BASE+(p.scheme if p.scheme else o.scheme) + "://" + (p.netloc if p.netloc else o.netloc)+p.path+p.query+p.fragment
            
        for tag in soup.find_all(src=True):
            p=urlparse(tag['src'])
            tag['src']=BASE+(p.scheme if p.scheme else o.scheme) + "://" + (p.netloc if p.netloc else o.netloc)+p.path+p.query+p.fragment
            
        resp=make_response(str(soup), x.status_code)
    else:
        resp=make_response(x.content, x.status_code)
    
    resp.headers["Content-Type"]=x.headers["Content-Type"]

    return resp
