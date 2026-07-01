import json
import requests

class SteamGame:
    """Stores information relating to a single Steam game and provides access to the tag cache."""
    tag_cache = { }
    with open('tags.json') as tag_file:
        tag_cache = json.load(tag_file)
        
    flag_cache = { }
    with open('content_flags.json') as flag_file:
        flag_cache = json.load(flag_file)
        
    name_cache = { }
    with open('names.json') as names_file:
        name_cache = json.load(names_file)
        
    reviews_cache = { }
    with open('reviews.json') as reviews_file:
        reviews_cache = json.load(reviews_file)
        
    ea_cache = { }
    with open('ea.json') as ea_file:
        ea_cache = json.load(ea_file)
        
    TARGET_TAGS = 20
    
    def __init__(self, id, name = None):
        self.game_id = id
        self.tags = []
        self.content_flags = []
        self.reviews = []
        self.ea = []
        self.game_name = ""
        
        #Steam API only supports icon URL, so we grab the logo URL directly
        self.game_logo_url = "https://cdn.cloudflare.steamstatic.com/steam/apps/" + str(self.game_id) + "/capsule_184x69.jpg"
        self.store_url = "https://store.steampowered.com/app/" + str(self.game_id)
        
        #Some games aren't present in the tag cache; usually means they have no store listing
        try:
            self.tags = SteamGame.tag_cache[str(self.game_id)]
        except KeyError:
            pass
        
        try:
            self.content_flags = SteamGame.flag_cache[str(self.game_id)]
        except KeyError:
            pass
        
        #if the initializing id was found via API call, the name is already known
        #if it was found in the database, need to check name cache
        #if not in name cache, check API
        if name is None:
            try:
                self.game_name = SteamGame.name_cache[str(self.game_id)]
            except KeyError:
                response = requests.get("https://steamspy.com/api.php?request=appdetails&appid=" + str(self.game_id))
                if response.status_code == 200:
                    #Steam Spy API occasionally returns a "too many connections" error with a 200 status
                    #it's out of my control when this happens, but it seems to be temporary
                    try:
                        response_json = response.json()
                        self.game_name = response_json['name']
                    except requests.exceptions.JSONDecodeError:
                        self.game_name = "[Name not found]"
                else:
                    self.game_name = "[Name not found]"
        else:
            self.game_name = name
        
        try:
            self.reviews = SteamGame.reviews_cache[str(self.game_id)]
        except KeyError:
            pass
        
        try:
            self.ea = SteamGame.ea_cache[str(self.game_id)]
        except KeyError:
            pass
        
        self.rating = None
        self.rec_score = 0

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)
        
    def calculate_rec_score(self, tag_scores):
        """
        Calculates the game's recommendation score based on its tags and the user's tag scores
        
        :param tag_scores: The user's scores for each tag based on their ratings
        """
        for tag in self.tags:
            self.rec_score += tag_scores[tag]
            
        #adjust score for games that don't reach the target number of tags, based on a confidence value
        tag_num = len(self.tags)
        if tag_num < SteamGame.TARGET_TAGS:
            confidence = tag_num / ((SteamGame.TARGET_TAGS - 1) * 2) + 0.4737
            self.rec_score *= (SteamGame.TARGET_TAGS / tag_num * confidence)
            
        #adjust score for games that have too many tags
        #this shouldn't happen at all but appears to be an issue with Steam Spy API
        if tag_num > SteamGame.TARGET_TAGS:
            self.rec_score *= (SteamGame.TARGET_TAGS / tag_num)

        self.rec_score = round(self.rec_score, 4)