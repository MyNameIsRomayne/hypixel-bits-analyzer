"""
Basically a buncha' defines when stuff is needed to be accessed programatically but otherwise is constant
Copyright (C) 2024 Romayne (Contact @ https://github.com/MyNameIsRomayne)
"""
import time
from util import *

# Base values
test_user_uuid = "3889f854-8595-4ac5-aaaa-6c2871c9446c" # this is my UUID (Meggal). Used to test against given API keys for whether or not an auth error is returned
api_request_output_file = "saved_output.txt" # debug output file. try to remove the reasons this exists

# Setup file paths
project_dir             = Path(os.path.dirname(os.path.realpath(__file__)))
data_dir                = project_dir + Path("data")

api_json_file           = data_dir + Path("hypixel_api_persistent.json")
api_response_games_file = data_dir + Path("hypixel_games.json")
api_response_items_file = data_dir + Path("hypixel_skyblock_items.json")
api_auctions_data_file  = data_dir + Path("auctions.json")
api_bazaar_data_file    = data_dir + Path("bazaar.json")

api_url = "https://api.hypixel.net/v2"

always_revalidate_key    = False # use this if you expect your keys to be invalidated a lot
announce_queries         = False # debug option, print on each query to debug query optimizaiton
cooldown_request_seconds = 1 # 300 per 5mins is listed via API, so 1 per second is compliant

json_key_api_key            = "api_key"
json_key_api_key_validated  = "valid_key"
json_key_api_last_request   = "api_last_queried"
json_key_api_total_requests = "api_total_queries"

# Define the default config of api_key.json
json_file_key_defaults = {
    json_key_api_key            : None,
    json_key_api_key_validated  : False,
    json_key_api_last_request   : time.time() - cooldown_request_seconds, # Allow first request to go thru alwayz
    json_key_api_total_requests : 0,
}

error_codes = {
    "400": "Data Missing",
    "403": "Access Forbidden",
    "404": "Page does not exist, responded with no result",
    "422": "Data Invalid",
    "429": "Request limit reached",
    "503": "Data not populated",
}

# All the request URLs a la https://api.hypixel.net/ documentation
# Wrapped like this so only this dict has to be changed in case of any renamings (unlikely) or whatnot
request_urls = {
    "player_data"           : "/player",
    "player_online_status"  : "/status",
    "resource_games"        : "/resources/games",
    "bazaar"                : "/skyblock/bazaar",
    "skyblock_items"        : "/resources/skyblock/items",
    "auctions"              : "/skyblock/auctions",
}
