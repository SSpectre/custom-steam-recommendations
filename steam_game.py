import json

class SteamGame:
    """Stores information relating to a single Steam game and provides access to the tag cache."""
    tag_cache = { }
    with open('tags.json') as json_file:
        tag_cache = json.load(json_file)
        
    TARGET_TAGS = 20
    
    def __init__(self, id, name):
        self.game_id = id
        self.game_name = name
        self.tags = []
        
        #Steam API only supports icon URL, so we grab the logo URL directly
        self.game_logo_url = "https://cdn.cloudflare.steamstatic.com/steam/apps/" + str(self.game_id) + "/capsule_184x69.jpg"
        self.store_url = "https://store.steampowered.com/app/" + str(self.game_id)
        
        #Some games aren't present in the tag cache; usually means they have no store listing
        try:
            self.tags = SteamGame.tag_cache[str(self.game_id)]
        except KeyError:
            pass
        
        self.rating = None
        self.rec_score = 0

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)
        
    def calculate_rec_score(self, tag_scores):
        """Calculates the game's recommendation score based on its tags and the user's tag scores"""
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