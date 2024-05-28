import requests
import json
import time
import sys

class NotGameError(Exception):
    """Exception class for when an app is a DLC, tool, etc."""
    pass

app_ids = []
game_tag_dict = { }
tag_set = set()
content_flag_dict = { }

#for determining overall time taken by the script
start_time = time.time()
#for determining how long to wait when encountering 429 responses
query_start_time = time.time()

end_of_pages = False
page = 0

def query_limited_api(url, id, threshold):
    """Function to be used when repeatedly querying an API with a request limit.
    Will wait and continue querying once limit has reset"""
    result = None
    retry_counter = 0
    
    def should_retry(tries, wait_time):
        """Inner function to be used when encountering exceptions from GET requests.
        Controls number of times a retry should be attempted before giving up and how long to wait between retries"""
        nonlocal retry_counter
        if retry_counter < tries:
            retry_counter += 1
            time.sleep(wait_time)
            return True
        else:
            return False
    
    #do-while loop
    while True:
        try:
            print("Requesting " + url, end = "")
            response = requests.get(url + str(id), timeout = 60)
            print("...Success")
        except requests.Timeout:
            #don't need to sleep since already waited for timeout
            if should_retry(5, 0): continue
            else: break
        except Exception:
            if should_retry(5, 60): continue
            else: break
        
        if response.status_code == 200:
            try:
                result = response.json()
            except json.JSONDecodeError:
                if should_retry(5, 0): continue
                else: break
        elif response.status_code == 429:
            print("Waiting...")
            global query_start_time
            
            #calculate time remaining until request limit is reset and wait until then
            #works even if API doesn't return a retry-after header *cough*Steam*cough*
            time_to_limit = time.time() - query_start_time
            time_to_wait = threshold - time_to_limit
            if time_to_wait > 0:
                time.sleep(time_to_wait)
            
            #reset time calculation for next query loop
            query_start_time = time.time()
        elif response.status_code == 403:
            #daily limit of queries has been hit; will need to try running script later
            sys.exit("403 error when updating tags")
        else:
            #for unexpected errors, try 5 times, then treat the id as invalid
            print("Response: " + str(response.status_code))
            if should_retry(5, 60): continue
            else: break
            
        if result is not None:
            break
        
    return result

#Steam Spy API retrieves all IDs separated into pages, so we need to add them to a single list
while end_of_pages == False:
    try:
        print("Page: " + str(page + 1))
        all_json = query_limited_api("https://steamspy.com/api.php?request=all&page=", page, 60)
        app_ids.extend(list(all_json.keys()))
    except AttributeError:
        end_of_pages = True
    page = page + 1
    
#filter out duplicate IDs that exist for some reason
id_set = set(app_ids)

request_number = 0

for id in id_set:
    request_number += 1
    print(str(request_number) + ": " + str(id))
    
    try:
        #filter out non-game software from the set
        type_json = query_limited_api("https://store.steampowered.com/api/appdetails?appids=", id, 300)
        type_data = type_json[str(id)]['data']
        
        if type_data['type'] == "game":
            #add game and its tags to cache
            tag_json = query_limited_api("https://steamspy.com/api.php?request=appdetails&appid=", id, 1)
            tags = tag_json['tags'].keys()
            game_tag_dict[id] = list(tags)
            
            #add game's tags to the set of all tags
            tag_set = tag_set | set(tags)
            
            #add game and its content flags to cache
            content_flag_dict[id] = type_data['content_descriptors']['ids']
            
            print("Valid")
        else:
            raise NotGameError("Not a game")
    except (TypeError, KeyError, NotGameError, AttributeError):
        print("Invalid")

with open('tags.json', 'w') as tags_file:
    json.dump(game_tag_dict, tags_file)
    
with open('tag_set.json', 'w') as set_file:
    json.dump(list(tag_set), set_file)
    
with open('content_flags.json', 'w') as flags_file:
    json.dump(content_flag_dict, flags_file)
    
elapsed_time = time.time() - start_time
    
print("Time: " + str(elapsed_time))
print("Valid Games: " + str(len(game_tag_dict.keys())))