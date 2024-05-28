import requests
import json

import secret_keys
from steam_game import SteamGame

class SteamUser:
    """Stores information relating to a single Steam user"""
    
    class NoRatingsError(Exception):
        """Exception class for when the user hasn't entered any ratings and tries to get a recommendation list"""
        pass
    
    tag_set = set()
    with open('tag_set.json') as json_file:
        tag_set = json.load(json_file)
    
    def __init__(self, id):
        self.user_id = id
        self.user_name = ""
        self.user_games = {}
        self.tag_scores = {}
        
        """0: unused, exists to align Steam's internal indexing with Python's lists
        1: Some Nudity or Sexual Content
        2: Frequent Violence or Gore
        3: Adult Only Sexual Content
        4: Frequent Nudity of Sexual Content
        5: General Mature Content"""
        self.content_filters = [0, 1, 1, 0, 0, 1]
        
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
        if len(self.user_games) == 0:
            raise self.NoRatingsError("Please add games to your Steam library.")
        
        #create a dictionary with tags for keys and empty lists for values
        scores = {tag: [] for tag in SteamUser.tag_set}
        
        number_of_ratings = 0
        
        #add to the list of ratings given to each game with a given tag
        for game_id in self.user_games:
            game = self.user_games[game_id]
            if game.rating != None:
                for tag in game.tags:
                    scores[tag].append(game.rating)
                number_of_ratings += 1
                
        if number_of_ratings < 2:
            raise self.NoRatingsError("At least two ratings are required to give recommendations.")
                   
        score_sum = 0
        number_of_scores = 0
        
        for tag in scores:
            if len(scores[tag]) > 0:
                #calculate the average rating given to each game with the given tag to get the tag score
                self.tag_scores[tag] = round(sum(scores[tag]) / len(scores[tag]), 4)
                score_sum += self.tag_scores[tag]
                number_of_scores += 1
                
        score_avg = self.apply_average_score_to_unknown_tags(score_sum, number_of_scores, scores)
                
        #reset sum, since average will need to be re-calculated
        score_sum = 0
        
        #calculate a confidence value for each tag score based on number of ratings, adjust tag scores
        for tag in scores:
            ratings = len(scores[tag])
            if ratings > 0:
                current_score = self.tag_scores[tag]
                
                #fraction exponent of a negative base isn't defined, so we use the absolute value of the base and multiply it by its sign to get the intended equation
                base = ratings - 1.7
                sign = base / abs(base)
                real_exp = sign * abs(base) ** 2.6
                confidence = -2.5 / (real_exp + 5.4) + 1
                
                #adjust low-confidence tag score up if it's below average and down if it's above average
                deviation = current_score - score_avg
                self.tag_scores[tag] = round(current_score - deviation * (1 - confidence), 4)
                score_sum += self.tag_scores[tag]
                
        #re-calculate and apply the average tag score using confidence-adjusted values
        self.apply_average_score_to_unknown_tags(score_sum, number_of_scores, scores)
        
        print(sorted(self.tag_scores.items(), key=lambda tag: tag[1]))
        
    def apply_average_score_to_unknown_tags(self, score_sum, number_of_scores, scores):
        """Calculate the average of existing scores and apply it to tags with no representation.
        Returns the average score."""
        #calculate the average tag score
        score_avg = round(score_sum / number_of_scores, 4)
        
        #apply the average tag score to tags with no representation, since we have no data on them
        for tag in scores:
            if len(scores[tag]) == 0:
                self.tag_scores[tag] = score_avg
                
        return score_avg