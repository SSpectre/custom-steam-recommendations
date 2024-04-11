import requests
import json
import time

game_tag_dict = { }
game_ids = []
tag_set = set()

all_resp = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2")
all_json = all_resp.json()
for app in all_json["applist"]["apps"]:
    game_ids.append(app["appid"])

for id in game_ids:
    try:
        resp = requests.get("https://steamspy.com/api.php?request=appdetails&appid=" + str(id))
        local_json = resp.json()
            
        tags = local_json['tags'].keys()
        game_tag_dict[id] = list(tags)
        tag_set = tag_set | set(tags)
        print(id)
    except AttributeError:
        pass

with open('tags.json', 'w') as tags_file:
    json.dump(game_tag_dict, tags_file)
    
with open('tag_set.json', 'w') as set_file:
    json.dump(list(tag_set), set_file)