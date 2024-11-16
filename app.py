import requests
import json

from flask import Flask, redirect, request, url_for, render_template, session, make_response
from flask_cors import CORS
from flask_session import Session
from urllib.parse import urlencode
from multipledispatch import dispatch

import db
import secret_keys

from steam_user import SteamUser
from steam_game import SteamGame

app = Flask(__name__)
app.teardown_appcontext(db.close_db)
app.secret_key = secret_keys.SECRET_KEY

SESSION_PERMANENT = False
SESSION_TYPE = "filesystem"
app.config.from_object(__name__)
Session(app)

cors = CORS(app)

URL_ROOT = "/custom-steam-recommendations/"
STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"
USER_GAMES_TABLE = "user_games"
USER_FILTER_PREFS_TABLE = "user_filter_prefs"
DEFAULT_LIST_SIZE = 100

@app.route(URL_ROOT)
def begin():
    """"Entry point for the Flask application. Displays login page."""
    session.permanent = False
    return render_template("login.html")

@app.route(URL_ROOT + "login/")
def login_with_steam():
    """Sends an OpenID request to Steam. Needs to be called from a new tab/window to work from within an iframe."""
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
    """Creates Steam User as a session variable and closes the new tab/window created during the login attempt."""
    identity = request.args["openid.identity"]
    last_slash = identity.rindex('/')
    id_number = identity[last_slash+1:]
    
    session["steam_user"] = SteamUser(id_number)
    session["list_size"] = DEFAULT_LIST_SIZE
    
    return "<script> close() </script>"

@app.route(URL_ROOT + "confirm/")
def confirm_login():
    """In response to an HTTP request from the client, returns the user's Steam ID if one exists or empty JSON if not."""
    try:
        return json.dumps({"user_id": session["steam_user"].user_id})
    except (KeyError, AttributeError):
        return {}

@app.route(URL_ROOT + "user/")
def get_user_id():
    """Redirects to the main page if a user exists."""
    try:
        return redirect(url_for("list_owned_games", user_id = session["steam_user"].user_id))
    except (KeyError, AttributeError):
        return redirect(url_for("begin"))

@app.route(URL_ROOT + "user/<user_id>/")
def list_owned_games(user_id):
    """Creates user's library and displays the main page. The user_id parameter is needed for the URL."""
    #if user tries to bypass login by directly entering Steam id, display login screen
    try:
        steam_user = session["steam_user"]
        owned_games = steam_user.owned_games.values()
    except (KeyError, AttributeError):
        return redirect(url_for("begin"))
    
    user_exists = does_user_record_exist(USER_GAMES_TABLE)
    if user_exists:
        #add new games to db and retrieve stored ratings
        for game in owned_games:
            game_exists = does_game_record_exist(game.game_id)
            if game_exists:
                rating = db.query_db("""SELECT rating
                                    FROM """ + USER_GAMES_TABLE +
                                    """ WHERE user_id = ?
                                    AND game_id = ?""",
                                    [steam_user.user_id, game.game_id], True)['rating']
                game.rating = rating if rating != "NULL" else None
                
                game_is_owned = db.query_db("""SELECT owned
                                            FROM """ + USER_GAMES_TABLE +
                                            """ WHERE user_id = ?
                                            AND game_id = ?""",
                                            [steam_user.user_id, game.game_id], True)['owned']
                
                #if "owned" is null, it was added to the database prior to the addition of rating unowned games and must be owned
                #if it is 0, the game was previously played on another platform before being bought on Steam
                if game_is_owned is None or game_is_owned == 0:
                    connection = db.get_db()
                    connection.execute("UPDATE " + USER_GAMES_TABLE +
                                        """ SET owned = 1
                                        WHERE user_id = ?
                                        AND game_id = ?""",
                                        [session["steam_user"].user_id, game.game_id])
                    connection.commit()
                    
            else:
                add_game_to_db(game.game_id, 1)
                
        #non-Steam games can't be found with an API call and require a database query
        other_games = db.query_db("""SELECT game_id, rating
                                  FROM """ + USER_GAMES_TABLE +
                                  """ WHERE user_id = ?
                                  AND owned = ?""",
                                  [steam_user.user_id, 0])
        
        for game in other_games:
            game_id = game['game_id']
            rating = game['rating']
            
            other_game = SteamGame(game_id)
            other_game.rating = rating if rating != "NULL" else None
            steam_user.other_games[game_id] = other_game
               
        #in case the user doesn't have existing filter preferences
        filters_exist = does_user_record_exist(USER_FILTER_PREFS_TABLE)
        if filters_exist:
            #retrieve user's content filter preferences 
            for i in range(1, 6):
                column = "include_flag_" + str(i)
                include_flag = db.query_db("SELECT " + column +
                                        " FROM " + USER_FILTER_PREFS_TABLE +
                                        " WHERE user_id = ?",
                                        [steam_user.user_id], True)[column]
                steam_user.content_filters[i] = include_flag
        else:
            #set content filter preferences to default
            add_filter_prefs()
            
    else:
        #new user; add all their games to db with no scores
        for game in owned_games:
            add_game_to_db(game.game_id, 1)
            
        #set content filter preferences to default
        add_filter_prefs()
    
    return render_template("owned_games.html", user_name = steam_user.user_name, owned_games = sorted(owned_games, key=lambda game: game.game_name.casefold()),
                           other_games = sorted(steam_user.other_games.values(), key=lambda game: game.game_name.casefold()),
                           list_size = session["list_size"] if "list_size" in session.keys() else DEFAULT_LIST_SIZE, filter_prefs = steam_user.content_filters)
    
@app.route(URL_ROOT + "assign_rating", methods=['POST'])
def assign_rating():
    """Changes the rating for a specified game in response to an HTTP request from the client."""
    data = request.get_json()
    rating = data['rating']
    game_id = data['id']
    user = session["steam_user"]
    
    if game_id in user.owned_games:
        user.owned_games[game_id].rating = int(rating) if rating != "exclude" else None
    elif game_id in user.other_games:
        user.other_games[game_id].rating = int(rating) if rating != "exclude" else None
        
    connection = db.get_db()
    connection.execute("UPDATE " + USER_GAMES_TABLE +
                       """ SET rating = ?
                       WHERE user_id = ?
                       AND game_id = ?""",
                       [rating if rating != "exclude" else "NULL", user.user_id, game_id])
    connection.commit()
    
    return "{}"

@app.route(URL_ROOT + "update_filter_pref", methods=['POST'])
def update_filter_pref():
    """Changes one of the user's mature content filter preferences in response to an HTTP request from the client."""
    data = request.get_json()
    filter_id = data['filterID']
    value = data['value']
    column = "include_flag_" + str(filter_id)
    user = session["steam_user"]
    
    user.content_filters[filter_id] = int(value)
    connection = db.get_db()
    connection.execute("UPDATE " + USER_FILTER_PREFS_TABLE +
                       " SET " + column + """ = ?
                       WHERE user_id = ?""",
                       [value, session["steam_user"].user_id])
    connection.commit()
    
    return "{}"

@app.route(URL_ROOT + "clear_ratings")
def clear_ratings():
    user = session["steam_user"]
    for game_id in user.owned_games:
        user.owned_games[game_id].rating = None
    for game_id in user.other_games:
        user.other_games[game_id].rating = None
        
    connection = db.get_db()
    connection.execute("UPDATE " + USER_GAMES_TABLE +
                       """ SET rating = NULL
                       WHERE user_id = ?""",
                       [user.user_id])
    connection.commit()
    
    return "{}"

@app.route(URL_ROOT + "change_list_size", methods=['POST'])
def change_list_size():
    """Changes the number of recommendations based on an HTTP request from the client. Returns the old size so the client knows whether to shrink or expand."""
    data = request.get_json()
    old_size = session["list_size"]
    session["list_size"] = int(data['size'])
    
    response = {}
    response["old_size"] = old_size
    
    return response

@app.route(URL_ROOT + "add_other_game", methods=['POST'])
def add_other_game():
    """Associates a non-Steam game with the user. Returns the added game object as JSON."""
    user = session["steam_user"]
    data = request.get_json()
    app_id = int(data['appID'])
    
    if app_id in user.owned_games.keys():
        response = {"error_message": "You already own that game!"}
        return make_response(json.dumps(response), 500)
    elif app_id in user.other_games.keys():
        response = {"error_message": "You've already added that game!"}
        return make_response(json.dumps(response), 500)
    elif str(app_id) in list(SteamGame.tag_cache.keys()):
        other_game = SteamGame(app_id)
        user.other_games[app_id] = other_game
        add_game_to_db(app_id, 0)
        
        game_json = other_game.to_json()
        return json.dumps(game_json)
    else:
        response = {"error_message": "App IDs must be for valid standalone games."}
        return make_response(json.dumps(response), 500)

@app.route(URL_ROOT + "recommend_games")
def recommend_games():
    """Constructs the recommendation list."""
    steam_user = session["steam_user"]
    
    try:
        steam_user.calculate_tag_scores()
    except steam_user.NoRatingsError as e:
        print(str(e))
        response = {"error_message": str(e)}
        return make_response(json.dumps(response), 500)

    all_response = requests.get("https://api.steampowered.com/IStoreService/GetAppList/v1/?key=" + secret_keys.STEAM_API_KEY + "&max_results=50000")
    all_json = all_response.json()
    
    all_apps = {}
    for app in all_json['response']['apps']:
        all_apps[str(app['appid'])] = app['name']

    #API call only returns max 50000 results but gives the location where it stopped, so we continue until all games are found
    while "have_more_results" in all_json['response']:
        all_response = requests.get("https://api.steampowered.com/IStoreService/GetAppList/v1/?key=" + secret_keys.STEAM_API_KEY + "&last_appid=" + str(all_json['response']['last_appid']) + "&max_results=50000")
        all_json = all_response.json()
        
        for app in all_json['response']['apps']:
            all_apps[str(app['appid'])] = app['name']
        
    #filter out possible duplicates
    app_set = set(all_apps.keys())
    
    cache_list = list(SteamGame.tag_cache.keys())
    cache_set = set(cache_list)
    
    #cache_set filters out non-games, app_set filters out games that are no longer available for sale
    valid_ids = cache_set.intersection(app_set)
    
    #filter out already owned games
    owned_set = set(str(key) for key in steam_user.owned_games.keys())
    unplayed_games = valid_ids.difference(owned_set)
    
    #filter out added non-Steam games
    other_set = set(str(key) for key in steam_user.other_games.keys())
    unplayed_games = unplayed_games.difference(other_set)

    valid_games = [SteamGame(id, all_apps[id]) for id in unplayed_games]
    rec_list = []
    
    for game in valid_games:
        #apply mature content filters
        allowed = True
        for flag in game.content_flags:
            if steam_user.content_filters[flag] == 0:
                allowed = False
                break
            
        if allowed:
            #construct recommendation list 
            game.calculate_rec_score(steam_user.tag_scores)
            add_to_rec_list(game, rec_list)
                
    #send recommendation list to client as JSON
    json_list = [rec.to_json() for rec in rec_list]
    for rec in rec_list:
        print(str(rec_list.index(rec) + 1) + ". " + rec.game_name + ": " + str(rec.rec_score))

    return json_list

@app.route(URL_ROOT + "delete_user")
def delete_user():
    """Deletes the user's data from the database."""
    user_id = session["steam_user"].user_id
    connection = db.get_db()
    
    #delete ratings
    connection.execute("DELETE FROM " + USER_GAMES_TABLE +
                       " WHERE user_id = ?",
                       [user_id])
    
    #delete filter preferences
    connection.execute("DELETE FROM " + USER_FILTER_PREFS_TABLE +
                       " WHERE user_id = ?",
                       [user_id])
    
    connection.commit()
    
    return "{}"

@app.route(URL_ROOT + "logout/")
def logout():
    """Clears the current users and returns to the login screen."""
    session.clear()
    return redirect(url_for("begin"))

def does_user_record_exist(table):
    """Checks whether the current user exists in the specified database table."""
    result = db.query_db("""SELECT COUNT(1)
                      FROM """ + table +
                      " WHERE user_id = ?",
                      [session["steam_user"].user_id], True)['COUNT(1)']
    return result

def does_game_record_exist(game_id):
    """Checks whether the database has a record for the specified game associated with the current user."""
    result = db.query_db("""SELECT COUNT(1)
                      FROM """ + USER_GAMES_TABLE +
                      """ WHERE user_id = ?
                      AND game_id = ?""",
                      [session["steam_user"].user_id, game_id], True)['COUNT(1)']
    return result

def add_game_to_db(game_id, owned):
    """Adds a record for the specified game associated with the current user to the database."""
    connection = db.get_db()
    connection.execute("INSERT INTO " + USER_GAMES_TABLE +
                       " VALUES (?, ?, ?, ?)",
                       [session["steam_user"].user_id, game_id, owned, "NULL"])
    connection.commit()
    
def add_filter_prefs():
    """Associates mature content filters with default values with the user, and adds them to the database."""
    user = session["steam_user"]
    
    connection = db.get_db()
    connection.execute("INSERT INTO " + USER_FILTER_PREFS_TABLE +
                       " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       [user.user_id, "Some Nudity or Sexual Content", user.content_filters[1], "Frequent Violence or Gore", user.content_filters[2],
                        "Adult Only Sexual Content", user.content_filters[3], "Frequent Nudity or Sexual Content", user.content_filters[4],
                        "General Mature Content", user.content_filters[5]])
    connection.commit()
    
def add_to_rec_list(game, rec_list):
    """Determines if the specified game should be placed in the recommendation list and inserts it if so."""
    rec_iter = iter(rec_list)

    #can't iterate over list directly since it might be empty
    for i in range(session["list_size"]):
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
                if len(rec_list) > session["list_size"]:
                    rec_list.pop()
                break
    
    rec_iter = iter(rec_list)

if __name__ == "__main__":
    app.run()