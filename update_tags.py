import requests
import json
import time
import sys
import datetime

class NotGameError(Exception):
    """Exception class for when an app is a DLC, tool, etc."""
    pass

app_ids = []
game_tag_dict = { }
tag_set = set()
content_flag_dict = { }
name_dict = { }
reviews_dict = { }
ea_dict = { }

#for determining overall time taken by the script
start_time = time.time()
#for determining how long to wait when encountering 429 responses
query_start_time = time.time()

end_of_pages = False
page = 0

def query_limited_api(url, id, threshold, vital):
    """Function to be used when repeatedly querying an API with a request limit.
    Will wait and continue querying once limit has reset"""
    result = None
    retry_counter = 0
    
    REQUIRED_API_FAILED_MESSAGE = "Required API call continued to fail."
    
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
            if len(url) > 1:
                response = requests.get(url[0] + str(id) + url[1], timeout = 60, headers={"Content-Type": "application/json"})
            else:
                response = requests.get(url[0] + str(id), timeout = 60, headers={"Content-Type": "application/json"})
        except requests.Timeout:
            #don't need to sleep since already waited for timeout
            if should_retry(5, 0): continue
            else:
                if vital:
                    sys.exit(REQUIRED_API_FAILED_MESSAGE)
                else:
                    break
        except Exception:
            if should_retry(5, 60): continue
            else:
                if vital:
                    sys.exit(REQUIRED_API_FAILED_MESSAGE)
                else:
                    break
        
        #this should happen when the end of Steam Spy pages has been reached, so we don't need to check if the query was vital
        if response.status_code == 200:
            try:
                result = response.json()
            except (json.JSONDecodeError, requests.exceptions.JSONDecodeError):
                if should_retry(5, 0): continue
                else:
                    break
        elif response.status_code == 429:
            print(str(datetime.datetime.now()) + " Waiting...")
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
            print(str(datetime.datetime.now()) + " Response: " + str(response.status_code))
            if should_retry(5, 60): continue
            else:
                if vital:
                    sys.exit(REQUIRED_API_FAILED_MESSAGE)
                else:
                    break
            
        if result is not None:
            break
        
    return result

#Steam Spy API retrieves all IDs separated into pages, so we need to add them to a single list
while end_of_pages == False:
    try:
        print(str(datetime.datetime.now()) + " Page: " + str(page + 1))
        all_json = query_limited_api(["https://steamspy.com/api.php?request=all&page="], page, 60, True)
        app_ids.extend(list(all_json.keys()))
    except AttributeError:
        end_of_pages = True
    page = page + 1
    
#filter out duplicate IDs that exist for some reason
id_set = set(app_ids)

request_number = 0

for id in id_set:
    request_number += 1
    print(str(datetime.datetime.now()) + " " + str(request_number) + ": " + str(id))
    
    try:
        #filter out non-game software from the set
        type_json = query_limited_api(["https://store.steampowered.com/api/appdetails?appids="], id, 300, False)
        type_data = type_json[str(id)]['data']
        
        if type_data['type'] == "game":
            #add game and its tags to cache
            tag_json = query_limited_api(["https://steamspy.com/api.php?request=appdetails&appid="], id, 1, False)
            tags = tag_json['tags'].keys()
            game_tag_dict[id] = list(tags)
            
            #add game's tags to the set of all tags
            tag_set = tag_set | set(tags)
            
            #add game and its content flags to cache
            content_flag_dict[id] = type_data['content_descriptors']['ids']
            
            #add game's name to cache
            name_dict[id] = tag_json['name']
            
            #add game's early access status to cache
            if "Early Access" in tag_json['genre']:
                ea_dict[id] = True
            else:
                ea_dict[id] = False
                
            #add game's user review info to cache
            review_json = query_limited_api(["https://store.steampowered.com/appreviews/", "?json=1&language=all&purchase_type=all"], id, 300, False)
            summary = review_json['query_summary']
            reviews = { }
            
            reviews['positive'] = summary['total_positive']
            reviews['negative'] = summary['total_negative']
            reviews['total'] = summary['total_reviews']
            reviews['recommended'] = 0
            if reviews['total'] > 0:
                reviews['recommended'] = round((reviews['positive'] / reviews['total'] * 100), 2)
            reviews_dict[id] = reviews
            
            print(str(datetime.datetime.now()) + ": " + str(reviews_dict[id]['recommended']) + " (" + str(reviews_dict[id]['total']) + "), " + str(ea_dict[id]) + ", Valid")
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
    
with open('names.json', 'w') as names_file:
    json.dump(name_dict, names_file)
    
with open ('reviews.json', 'w') as reviews_file:
    json.dump(reviews_dict, reviews_file)
    
with open ('ea.json', 'w') as ea_file:
    json.dump(ea_dict, ea_file)
    
elapsed_time = time.time() - start_time
    
print("Time: " + str(elapsed_time))
print("Valid Games: " + str(len(game_tag_dict.keys())))