import requests
import json
import time
import sys
import datetime


class NotGameError(Exception):
    """Exception class for when an app is a DLC, tool, etc."""
    pass

name_dict = { }

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
            response = requests.get(url + str(id), timeout = 60, headers={"Content-Type": "application/json"})
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
            except (json.JSONDecodeError, requests.exceptions.JSONDecodeError):
                if should_retry(5, 0): continue
                else: break
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
            else: break
            
        if result is not None:
            break
        
    return result

#Steam Spy API retrieves all IDs separated into pages, so we need to add them to a single list
while end_of_pages == False:
    try:
        print(str(datetime.datetime.now()) + " Page: " + str(page + 1))
        all_json = query_limited_api("https://steamspy.com/api.php?request=all&page=", page, 60)
        app_ids = all_json.keys()
        
        for id in app_ids:
            name_dict[id] = all_json[id]["name"]
    except AttributeError:
        end_of_pages = True
    page = page + 1
    
with open('names.json', 'w') as names_file:
    json.dump(name_dict, names_file)
    
elapsed_time = time.time() - start_time
    
print("Time: " + str(elapsed_time))