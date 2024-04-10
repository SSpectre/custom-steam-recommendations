import requests
import json
import time

from json import JSONDecodeError

game_tag_dict = { }
game_ids = []
tag_set = set()

end_of_pages = False
page = 0

while end_of_pages == False:
    try:
        all_resp = requests.get("https://steamspy.com/api.php?request=all&page=" + str(page))
        all_json = all_resp.json()
    except JSONDecodeError:
        end_of_pages = True
    else:
        game_ids.extend(list(all_json.keys()))
        page += 1
    

for id in game_ids:
    try:
        resp = requests.get("https://steamspy.com/api.php?request=appdetails&appid=" + id)
        local_json = resp.json()
    
        tags = local_json['tags'].keys()
        game_tag_dict[id] = list(tags)
        tag_set = tag_set | set(tags)
    except Exception:
        pass

with open('tags.json', 'w') as tags_file:
    json.dump(game_tag_dict, tags_file)
    
with open('tag_set.json', 'w') as set_file:
    json.dump(list(tag_set), set_file)