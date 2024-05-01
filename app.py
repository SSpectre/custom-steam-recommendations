import requests
import json

from flask import Flask, redirect, request, url_for, render_template, session
from flask_cors import CORS
from flask_session import Session
from urllib.parse import urlencode
from multipledispatch import dispatch

import db

from steam_user import SteamUser
from steam_game import SteamGame

app = Flask(__name__)
app.teardown_appcontext(db.close_db)

SESSION_PERMANENT = False
SESSION_TYPE = "filesystem"
app.config.from_object(__name__)
Session(app)

cors = CORS(app)

URL_ROOT = "/custom-steam-recommendations/"
STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"
USER_GAMES_TABLE = "user_games"
RECOMMENDATION_LIST_SIZE = 500

@app.route(URL_ROOT)
def begin():
    session.permanent = False
    return render_template("login.html")

@app.route(URL_ROOT + "login/")
def login_with_steam():
    params = {
      'openid.ns': "http://specs.openid.net/auth/2.0",
      'openid.identity': "http://specs.openid.net/auth/2.0/identifier_select",
      'openid.claimed_id': "http://specs.openid.net/auth/2.0/identifier_select",
      'openid.mode': 'checkid_setup',
      'openid.return_to': request.url_root + url_for("authenticate"),
      'openid.realm': request.url_root
      }
  
    query_string = urlencode(params)
    login_url = STEAM_OPENID_URL + "?" + query_string
    
    return redirect(login_url)

@app.route(URL_ROOT + "authenticate/")
def authenticate():
    identity = request.args["openid.identity"]
    last_slash = identity.rindex('/')
    id_number = identity[last_slash+1:]
    
    session["steam_user"] = SteamUser(id_number)
    
    return "<script> close() </script>"

@app.route(URL_ROOT + "user/")
def get_user_id():
    try:
        return redirect(url_for("list_owned_games", user_id = session["steam_user"].user_id))
    except (KeyError, AttributeError):
        return redirect(url_for("begin"))

@app.route(URL_ROOT + "user/<user_id>/")
def list_owned_games(user_id):
    #if user tries to bypass login by directly entering Steam id, exception is thrown
    try:
        steam_user = session["steam_user"]
        games_list = steam_user.user_games.values()
    except (KeyError, AttributeError):
        return redirect(url_for("begin"))
    user_exists = does_record_exist(steam_user.user_id)
    
    if user_exists:
        #existing user; add new games to db and retrieve stored ratings
        for game in games_list:
            game_exists = does_record_exist(steam_user.user_id, game.game_id)
            
            if game_exists:
                rating = db.query_db("""SELECT rating
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
    
    return render_template("owned_games.html", user_name = steam_user.user_name, games = sorted(games_list, key=lambda game: game.game_name.casefold()),
                           list_size = RECOMMENDATION_LIST_SIZE)
    
@app.route(URL_ROOT + "confirm/")
def confirm_login():
    try:
        return json.dumps({"user_id": session["steam_user"].user_id})
    except (KeyError, AttributeError):
        return {}
    
@app.route(URL_ROOT + "assign_rating", methods=['POST'])
def assign_rating():
    data = request.get_json()
    rating = data['rating']
    update_rating(rating, session["steam_user"], data['id'])
    
    return "{}"

@app.route(URL_ROOT + "recommend_games")
def recommend_games():
    steam_user = session["steam_user"]
    steam_user.calculate_tag_scores()
    
    all_response = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2")
    all_json = all_response.json()
    
    all_apps = {}
    for app in all_json['applist']['apps']:
        all_apps[str(app['appid'])] = app['name']
        
    app_set = set(all_apps.keys())
    
    cache_list = list(SteamGame.tag_cache.keys())
    cache_set = set(cache_list)
    
    #cache_set filters out non-games, app_set filters out games that are no longer available for sale
    valid_ids = cache_set.intersection(app_set)
    valid_games = [SteamGame(id, all_apps[id]) for id in valid_ids]
           
    #construct recommendation list 
    rec_list = []
    for game in valid_games:
        game.calculate_rec_score(steam_user.tag_scores)
        add_to_rec_list(game, rec_list)
                
    #send recommendation list to HTML template as JSON
    json_list = [rec.to_json() for rec in rec_list]
    for rec in rec_list:
        print(str(rec_list.index(rec) + 1) + ". " + rec.game_name + ": " + str(rec.rec_score))

    return json_list

@app.route(URL_ROOT + "logout/")
def logout():
    session["steam_user"] = None
    return redirect(url_for("begin"))

@dispatch(str)
def does_record_exist(user_id):
    result = db.query_db("""SELECT COUNT(1)
                      FROM """ + USER_GAMES_TABLE +
                      " WHERE user_id = ?",
                      [user_id], True)['COUNT(1)']
    return result

@dispatch(str, int)
def does_record_exist(user_id, game_id):
    result = db.query_db("""SELECT COUNT(1)
                      FROM """ + USER_GAMES_TABLE +
                      """ WHERE user_id = ?
                      AND game_id = ?""",
                      [user_id, game_id], True)['COUNT(1)']
    return result

def add_game_to_db(user_id, game_id):
    connection = db.get_db()
    connection.execute("INSERT INTO " + USER_GAMES_TABLE +
                       " VALUES (?, ?, ?)",
                       [user_id, game_id, "NULL"])
    connection.commit()

def update_rating(rating, user, game_id):
    user.user_games[game_id].rating = int(rating) if rating != "exclude" else None
    connection = db.get_db()
    connection.execute("UPDATE " + USER_GAMES_TABLE +
                       """ SET rating = ?
                       WHERE user_id = ?
                       AND game_id = ?""",
                       [rating if rating != "exclude" else "NULL", user.user_id, game_id])
    connection.commit()
    
def add_to_rec_list(game, rec_list):
    rec_iter = iter(rec_list)

    #can't iterate over list directly since it might be empty
    for i in range(RECOMMENDATION_LIST_SIZE):
        try:
            comparison_game = next(rec_iter)
        except StopIteration:
            #reached the end of recommendation list that isn't full
            rec_list.append(game)
            break
        else:
            if game.rec_score > comparison_game.rec_score:
                rec_list.insert(i, game)
                
                #limit recommendation list size
                if len(rec_list) > RECOMMENDATION_LIST_SIZE:
                    rec_list.pop()
                break
    
    rec_iter = iter(rec_list)

if __name__ == "__main__":
    app.run()