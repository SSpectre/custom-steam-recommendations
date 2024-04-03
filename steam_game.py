import json

class SteamGame:
    tag_cache = { }
    with open('tags.json') as json_file:
        tag_cache = json.load(json_file)
    
    def __init__(self, id, name):
        self.game_id = id
        self.game_name = name
        
        #Steam API only supports icon URL, so we grab the logo URL directly
        self.game_logo_url = "https://cdn.cloudflare.steamstatic.com/steam/apps/" + str(self.game_id) + "/capsule_184x69.jpg"
        
        #Some games aren't present in the tag cache; usually means they have no store listing
        try:
            self.tags = SteamGame.tag_cache[str(self.game_id)]
        except KeyError:
            pass
        
        self.rating = None