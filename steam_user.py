import requests
import json

import secret_keys
from steam_game import SteamGame

class SteamUser:
    """Stores information relating to a single Steam user"""
    tag_set = set()
    with open('tag_set.json') as json_file:
        tag_set = json.load(json_file)
    
    def __init__(self, id):
        self.user_id = id
        self.user_name = ""
        self.user_games = {}
        self.tag_scores = {}
        
        self.get_name()
        self.get_owned_games()

    def get_name(self):
        """Returns account name from ID."""
        response = requests.get("https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key=" + secret_keys.STEAM_API_KEY + "&steamids=" + str(self.user_id))
        if response.status_code == 200:
            json = response.json()
            
        self.user_name = json['response']['players'][0]['personaname']
        
    def get_owned_games(self):
        """Creates a dictionary of games owned by the user, with app IDs as keys."""
        response = requests.get("https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=" + secret_keys.STEAM_API_KEY + "&steamid=" + str(self.user_id) + "&include_appinfo=true&include_played_free_games=true&format=json")
        if response.status_code == 200:
            json = response.json()
            
        for game in json['response']['games']:
            new_game = SteamGame(game['appid'], game['name'])
            self.user_games[game['appid']] = new_game
            
    def calculate_tag_scores(self):
        """Creates a dictionary of scores for each tag based on the user's ratings of their games."""
        #create a dictionary with tags for keys and empty lists for values
        scores = {tag: [] for tag in SteamUser.tag_set}
        
        #add to the list of ratings given to each game with a given tag
        for game_id in self.user_games:
            game = self.user_games[game_id]
            if game.rating != None:
                for tag in game.tags:
                    scores[tag].append(game.rating)
                   
        score_sum = 0
        number_of_scores = 0
        
        for tag in scores:
            if len(scores[tag]) > 0:
                #calculate the average rating given to each game with the given tag to get the tag score
                self.tag_scores[tag] = round(sum(scores[tag]) / len(scores[tag]), 4)
                score_sum += self.tag_scores[tag]
                number_of_scores += 1
                
        #calculate the average tag score
        score_avg = round(score_sum / number_of_scores, 4)
        
        #apply the average tag score to tags with no representation, since we have no data on them
        for tag in scores:
            if len(scores[tag]) == 0:
                self.tag_scores[tag] = score_avg