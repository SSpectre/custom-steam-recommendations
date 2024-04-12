import requests
import json
import time

class NotGameError(Exception):
    """Exception class for when an app is a DLC, tool, etc."""
    pass

app_ids = []
game_tag_dict = { }
tag_set = set()

def query_limited_api(url, id):
    """Function to be used when repeatedly querying an API with a request limit.
    Continues querying API until limit resets."""
    result = None
    
    #do-while loop that continues querying API until the limit resets
    while True:
        response = requests.get(url + str(id))
        if response.status_code == 200:
            result = response.json()
            
        if result is not None:
            break
        
    return result
    
startTime = time.time()

all_resp = requests.get("https://api.steampowered.com/ISteamApps/GetAppList/v2")
if all_resp.status_code == 200:
    all_json = all_resp.json()
    
for app in all_json["applist"]["apps"]:
    app_ids.append(app["appid"])
    print("Initial: " + str(app["appid"]))

request_number = 0
for id in app_ids:
    print(id)
    type_json = query_limited_api("https://store.steampowered.com/api/appdetails?appids=", id)
    
    try:
        #only add games to dictionary, not DLC, tools, etc.
        if type_json[str(id)]['data']['type'] == "game":
            tag_json = query_limited_api("https://steamspy.com/api.php?request=appdetails&appid=", id)
                
            tags = tag_json['tags'].keys()
            game_tag_dict[id] = list(tags)
            
            #add game's tags to the set of all tags
            tag_set = tag_set | set(tags)
            
            print("Valid")
        else:
            raise NotGameError("Not a game")
    except (KeyError, NotGameError, AttributeError):
        print("Invalid")

with open('tags.json', 'w') as tags_file:
    json.dump(game_tag_dict, tags_file)
    
with open('tag_set.json', 'w') as set_file:
    json.dump(list(tag_set), set_file)
    
elapsedTime = time.time() - startTime
    
print("Time: " + str(elapsedTime))
print("App IDs: " + str(len(app_ids)))
print("Valid Games: " + str(len(game_tag_dict.keys())))