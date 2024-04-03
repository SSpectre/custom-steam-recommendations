import requests
import json

class SteamGame:
    game_id = None
    game_name = ""
    game_logo_url = ""
    tags = []
    rating = None
    
    def __init__(self, id, name):
        self.game_id = id
        self.game_name = name
        
        #Steam API only supports icon URL, so we grab the logo URL directly
        self.game_logo_url = "https://cdn.cloudflare.steamstatic.com/steam/apps/" + str(self.game_id) + "/capsule_184x69.jpg"
        
    def get_tags(self):
        with open('tags.json') as json_file:
            tags_json = json.load(json_file)
            #Some games aren't present in the tag cache; usually means they have no store listing
            try:
                self.tags = tags_json[str(self.game_id)]
            except KeyError:
                pass
            
            print(self.game_id)