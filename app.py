from flask import Flask, redirect, request, url_for, render_template, g
from urllib.parse import urlencode
from multipledispatch import dispatch

from steam_user import SteamUser
from db import get_db, query_db, close_db

app = Flask(__name__)
app.debug = True
app.teardown_appcontext(close_db)

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"
USER_GAMES_TABLE = "user_games"

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
      'openid.return_to': 'http://localhost:5000/user',
      'openid.realm': 'http://localhost:5000'
      }
  
    query_string = urlencode(params)
    login_url = STEAM_OPENID_URL + "?" + query_string
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
        games_list = steam_user.user_games.values()
        user_exists = does_record_exist(steam_user.user_id)
        
        if user_exists:
            #existing user; add new games to db and retrieve stored ratings
            for game in games_list:
                game_exists = does_record_exist(steam_user.user_id, game.game_id)
                
                if game_exists:
                    rating = query_db("""SELECT rating
                                        FROM """ + USER_GAMES_TABLE +
                                        """ WHERE user_id = ?
                                        AND game_id = ?""",
                                        [steam_user.user_id, game.game_id], True)['rating']
                    game.rating = rating if rating != "NULL" else None
                else:
                    add_game_to_db(steam_user.user_id, game.game_id)
                
        else:
            #new user; add all their games to db with no scores
            for game in games_list:
                add_game_to_db(steam_user.user_id, game.game_id)
        
        return render_template("owned_games.html", games = sorted(games_list, key=lambda game: game.game_name.casefold()))
    except KeyError:
        return '<a href="/login">Login with steam</a>'
    
@app.route("/assign_rating", methods=['POST'])
def assign_rating():
    data = request.get_json()
    rating = data['rating']
    
    global steam_user
    update_rating(rating, steam_user, data['id'])
    
    return "nothing"

@dispatch(str)
def does_record_exist(user_id):
    result = query_db("""SELECT COUNT(1)
                      FROM """ + USER_GAMES_TABLE +
                      " WHERE user_id = ?",
                      [user_id], True)['COUNT(1)']
    return result

@dispatch(str, int)
def does_record_exist(user_id, game_id):
    result = query_db("""SELECT COUNT(1)
                      FROM """ + USER_GAMES_TABLE +
                      """ WHERE user_id = ?
                      AND game_id = ?""",
                      [user_id, game_id], True)['COUNT(1)']
    return result

def add_game_to_db(user_id, game_id):
    connection = get_db()
    connection.execute("INSERT INTO " + USER_GAMES_TABLE +
                       " VALUES (?, ?, ?)",
                       [user_id, game_id, "NULL"])
    connection.commit()

def update_rating(rating, user, game_id):
    user.user_games[game_id].rating = rating if rating != "exclude" else None
    connection = get_db()
    connection.execute("UPDATE " + USER_GAMES_TABLE +
                       """ SET rating = ?
                       WHERE user_id = ?
                       AND game_id = ?""",
                       [rating if rating != "exclude" else "NULL", user.user_id, game_id])
    connection.commit()

if __name__ == "__main__":
    app.run()