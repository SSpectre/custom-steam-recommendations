import json

class SteamGame:
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
        
        #Some games aren't present in the tag cache; usually means they have no store listing
        try:
            self.tags = SteamGame.tag_cache[str(self.game_id)]
        except KeyError:
            pass
        
        self.rating = None
        self.rec_score = 0
        
    def calculate_rec_score(self, tag_scores):
        for tag in self.tags:
            self.rec_score += tag_scores[tag]
            
        tag_num = len(self.tags)
        if tag_num < SteamGame.TARGET_TAGS:
            self.rec_score *= (SteamGame.TARGET_TAGS / tag_num)