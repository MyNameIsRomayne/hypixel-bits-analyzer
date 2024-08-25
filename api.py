"""
Script which handles setting up the API to hypixel.
Handles requests, ensures a valid API key, respects rate limits, etc.
Copyright (C) 2024 Romayne (Contact @ https://github.com/MyNameIsRomayne)
"""

import json
from config import *

class HypixelAPI():

    def __init__(self):
        # Must reflect [json_file_key_defaults] in config.py
        self.api_key = None
        self.valid_key = None
        self.api_last_queried = None
        self.api_total_queries = None
        self.update()
        # Some things that arent peristent in hypixel_api_persistent.json but elsewhere
        self.items = self.get_all_items()
        # Boo, sorry, but key should always be validated
        if always_revalidate_key:
            self.valid_key = False
        # Do a few extra things that only deserve to be done once. Valid api keys and whatnot (requires burning a query or two)
        self.ensure_valid_api_key()

    def update(self):
        """
        Updates the JSON keys file as needed.
        """
        api_json_file_contents_raw = read_file_contents(api_json_file)
        # Setup JSON with default keys
        self.api_json:dict = json.loads(api_json_file_contents_raw) if api_json_file_contents_raw != None else {}
        self.ensure_json_has_keys()
        # Setup API key metadata from [json_file_key_defaults]
        for key in json_file_key_defaults:
            setattr(self, key, self.api_json[key] if key in self.api_json.keys() else None)

    def ensure_json_has_keys(self):
        """
        Simple script on startup to ensure all keys are in the JSON. Adds any keys that aren't.
        """
        had_missing_keys = False
        current_keys = self.api_json.keys()
        for key in json_file_key_defaults.keys():
            if key not in current_keys:
                print(f"Adding {key} as {json_file_key_defaults[key]} to api_key.json")
                had_missing_keys = True
                self.api_json[key] = json_file_key_defaults[key]
                setattr(self, key, json_file_key_defaults[key])

        if (had_missing_keys):
            self.save_local_json()

    def ensure_valid_api_key(self):
        """
        Ensure there is a valid API key to use in the program. Uses a test query in api_key_is_valid
        """
        # Shortcut: If we already validated this key, no need to re-auth
        if self.valid_key:
            return

        key_valid = False
        if self.api_key != None:
            new_key = self.api_key
            key_valid = self.api_key_is_valid(new_key)
            if key_valid:
                self.valid_key = True
                self.save_local_json()
                return

        while not key_valid:
            print("API key not defined. Please enter your Hypixel API key. Note that this will be saved within this program, and is EXTREMELY private to you. Handle with care!")
            new_key = input()
            key_valid = self.api_key_is_valid(new_key)
        
        self.valid_key = True
        self.update_api_key(new_key)

    # note: this runs on avg once per 1s, doesnt really need to be optimal (yay python)
    def do_request(self, url, save_temporarily = True, ignore_cooldown = False, params:dict={}):
        """
        Handle sending a request and returning contents with an assumed response as JSON.
        Raises a ConnectionRefusedError if the returned success argument is not true.
        Saves the output to the api_request_output_file, overwriting existing data, so long as save_temporarily is true.
        Returns false if the time since the last request (governed by api_key.json) is below the cooldown rate limit.
        Ignores the cooldown if ignore_cooldown is True. USE SPARINGLY, as this can net over the rate limit.
        Note you do NOT need to supply the api key param, it is added within the function. Adding it will override the setting done here
        """
        if "key" not in params.keys():
            params["key"] = self.api_key
        if announce_queries:
            print(f"Making query to {url} with params {params}")
        # Handle cooldown time
        if (not ignore_cooldown and (time.time() - self.api_last_queried) < cooldown_request_seconds):
            delay = cooldown_request_seconds - (time.time() - self.api_last_queried)
            if announce_queries:
                print(f"Waiting {format_seconds_to_times(delay)} for next query...")
            time.sleep(delay)
        # Handle actual request
        contents, status_code = make_request(url, save_temporarily, outfile=api_request_output_file, method="w", params=params)
        # Hypixel requests are returned as JSON, so. jsonify it
        contents = json.loads(contents)
        if contents["success"] == False:
            print(f"Request to {url} with params {params} failed with error code {status_code}: {contents['cause']} ({error_codes[str(status_code)]})")
            contents["status_code"] = status_code
            return contents
        # Handle updating last request time (since we succeeded)
        self.api_last_queried = time.time()
        # also total requests ;p
        self.api_total_queries += 1
        self.save_local_json()
        return contents

    def get_player_online(self, uuid:str):
        """
        (UNUSED) get if a specific UUID is online.
        """
        auth_params = {"key": self.api_key, "uuid": uuid}
        test_query = get_request_url("player_online_status")
        return self.do_request(test_query, save_temporarily=False, params=auth_params)

    def api_key_is_valid(self, api_key:str):
        """
        Get whether the given API Key is valid.
        """
        # has to be done differently from get_player_online to insert the new api_key
        auth_params = {"key": api_key, "uuid": test_user_uuid}
        test_query = get_request_url("player_online_status")
        response = self.do_request(test_query, save_temporarily=False, ignore_cooldown=True, params=auth_params)
        return response["success"]

    def update_api_key(self, new_key):
        """
        Set the current API key to some new key.
        """
        self.api_key = new_key
        self.save_local_json()

    def save_local_json(self):
        """
        Save the current variables to JSON
        """
        for key in json_file_key_defaults:
            self.api_json[key] = getattr(self, key)
        write_file_contents(api_json_file, json.dumps(self.api_json))
        self.update()

    def info(self):
        """
        Gets some basic information about the program state, and outputs it to the console.
        - Time since last query
        """
        readable_time_last_queried = format_seconds_to_times(time.time() - self.api_last_queried)
        if (not readable_time_last_queried or readable_time_last_queried == 0):
            readable_time_last_queried = "now"
        else:
            readable_time_last_queried += " ago"
        print(f"Last Queried: {readable_time_last_queried}")

    def generic_get_request_or_cache(self, request_url_key, request_cache_file, cache_valid_time = -1):
        """
        Gets the request from the server, or local if it's still cache_valid_time seconds old.
        """
        if ensure_file_exists(request_cache_file, create=True):
            if cache_valid_time == -1:
                return json.loads(read_file_contents(request_cache_file))
            else:
                raise NotImplementedError("Non-Infinite cache times NYI")

        request_url = get_request_url(request_url_key)
        response_contents = self.do_request(request_url, save_temporarily=False)
        if response_contents:
            write_file_contents(request_cache_file, json.dumps(response_contents))
        return response_contents

    def get_all_games(self):
        """Get all games on Hypixel. Writes the response to api_response_games_file if it doesn't exist yet, and returns the response from that file instead if it does."""
        return self.generic_get_request_or_cache("resource_games", api_response_games_file)

    def get_all_items(self):
        """Get all items in Hypixel Skyblock."""
        return self.generic_get_request_or_cache("skyblock_items", api_response_items_file)
    
    def get_item_by_field(self, field:str, item_match:str):
        """Get items which match in skyblock to a particular field. Specifically if item[field] == item_match."""
        # mhm
        for item in self.items["items"]:
            if item[field] == item_match:
                return item
        return None
