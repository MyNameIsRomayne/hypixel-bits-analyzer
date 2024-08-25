"""
Script to setup the Bazaar class for interfacing with the Skyblock Bazaar.
Copyright (C) 2024 Romayne (Contact @ https://github.com/MyNameIsRomayne)
"""

from config import *
from api import HypixelAPI
from util import get_request_url
import time
import json

class Bazaar():

    def __init__(self, api:HypixelAPI):
        self.api = api
        self.whole_bazaar_data = None
        self.update()
    
    def get_bazaar_data(self):
        """Gets bazaar data from bazaar.json if not outdated (>5min old), else requests new data"""
        file_contents_raw = read_file_contents(api_bazaar_data_file)

        # Determine if we need new data, request and return the result if we do
        if file_contents_raw == None:
            result = self.request_new_data()
            return result
        else:
            file_json = json.loads(file_contents_raw)
            time_since_query = time.time() - file_json["lastUpdated"]
            if time_since_query > 300:
                result = self.request_new_data()
                return result
        
        # We didn't need new data, so just load the file and return that result instead
        self.whole_bazaar_data = json.loads(file_contents_raw)
        return self.whole_bazaar_data
    
    def request_new_data(self):
        """CALL SPARINGLY. REQUESTS LOTS OF DATA"""
        request_result = self.api.do_request(get_request_url("bazaar"), save_temporarily=False)
        if request_result["success"]:
            self.whole_bazaar_data = request_result
            write_file_contents(api_bazaar_data_file, json.dumps(self.whole_bazaar_data))
        return request_result
            
    def update(self):
        """Gets bazaar data if the current data is over 5 minutes old"""
        self.whole_bazaar_data = self.get_bazaar_data()
