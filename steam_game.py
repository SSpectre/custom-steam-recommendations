import requests

class SteamGame:
    game_id = None
    game_name = ""
    game_logo_url = ""
    tags = []
    rating = None
    
    def __init__(self, id):
        self.game_id = id
        #Steam API only supports icon URL, so we grab the logo URL directly
        self.game_logo_url = "https://cdn.cloudflare.steamstatic.com/steam/apps/" + str(self.game_id) + "/capsule_184x69.jpg"
        
        resp = requests.get("https://steamspy.com/api.php?request=appdetails&appid=" + str(self.game_id))
        json = resp.json()
        
        self.game_name = json['name']
        self.tags = json['tags']