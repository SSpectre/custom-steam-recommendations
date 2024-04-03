from flask import Flask, redirect, request, url_for, render_template
from urllib.parse import urlencode

from steam_user import SteamUser

import json

app = Flask(__name__)
app.debug = True

steam_openid_url = 'https://steamcommunity.com/openid/login'

steam_user: SteamUser

@app.route("/")
def hello():
    return '<a href="/login">Login with steam</a>'

@app.route("/login")
def login_with_steam():
    params = {
      'openid.ns': "http://specs.openid.net/auth/2.0",
      'openid.identity': "http://specs.openid.net/auth/2.0/identifier_select",
      'openid.claimed_id': "http://specs.openid.net/auth/2.0/identifier_select",
      'openid.mode': 'checkid_setup',
      'openid.return_to': 'http://127.0.0.1:5000/user',
      'openid.realm': 'http://127.0.0.1:5000'
      }
  
    query_string = urlencode(params)
    login_url = steam_openid_url + "?" + query_string
    return redirect(login_url)

@app.route("/user")
def get_user_id():
    identity = request.args["openid.identity"]
    last_slash = identity.rindex('/')
    id_number = identity[last_slash+1:]
    
    global steam_user
    steam_user = SteamUser(id_number)
    return redirect(url_for("list_owned_games", user_id = steam_user.user_id))

@app.route("/user/<user_id>")
def list_owned_games(user_id):
    #if user tries to bypass login by directly entering Steam id, exception is thrown
    try:
        global steam_user        
        return render_template("owned_games.html", games = steam_user.user_games)
    except Exception:
        return '<a href="/login">Login with steam</a>'

if __name__ == "__main__":
    app.run()