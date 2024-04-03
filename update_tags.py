import requests
import json
import time

game_tag_dict = { }
game_ids = []

end_of_pages = False
page = 0

while end_of_pages == False:
    try:
        all_resp = requests.get("https://steamspy.com/api.php?request=all&page=" + str(page))
        all_json = all_resp.json()
        game_ids.extend(list(all_json.keys()))
    except Exception:
        end_of_pages = True
    page = page + 1

for id in game_ids:
    resp = requests.get("https://steamspy.com/api.php?request=appdetails&appid=" + id)
    local_json = resp.json()
    
    tags = local_json['tags']
    game_tag_dict[id] = tags

with open('tags.json', 'w') as tags_file:
    json.dump(game_tag_dict, tags_file)