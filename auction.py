"""
Script which handles setting up the class/helper functions for the auction house.
Copyright (C) 2024 Romayne (Contact @ https://github.com/MyNameIsRomayne)
"""

from config import *
from api import HypixelAPI
from util import get_request_url
import time
import json
from data import SkyblockAuctionPage, SkyblockAuctionData
import progressbar
from math import floor

def get_profits_fee(coins:int):
    """Get the percentage fee for profits on the AH"""
    TEN_MILLION = 10000000
    HUNDRED_MILLION = TEN_MILLION * 10
    if coins < TEN_MILLION:
        return round( 0.01 * coins )
    elif coins < HUNDRED_MILLION:
        return round( 0.02 * coins )
    else:
        return round( 0.025 * coins )

def get_time_fee(seconds:int):
    """terrible but so is w/e hypixel's BS is. wellp"""
    # Some defines so my quick maths doesnt upset ppl
    FIVE_MINUTES = 300
    ONE_HOUR = 3600
    ONE_DAY = ONE_HOUR * 24
    TWO_WEEKS = ONE_DAY * 14
    # Some default times net special amts. Check if its one of those cases
    preset_hours_to_coins = {
        "1": 20,
        "6": 45,
        "12": 100,
        "24": 350,
        "36": 720,
        "48": 1200,
        "60": 1800,
        "72": 3000,
        "84": 4800,
        "336": 55200, # not really a preset value but i need an endpoint here
    }
    as_hours = int(seconds / ONE_HOUR)
    if str(as_hours) in preset_hours_to_coins.keys():
        return preset_hours_to_coins[str(as_hours)]
    # Not a preset, return some function value
    # At most 14 days
    seconds = min(seconds, TWO_WEEKS)
    # At least 5 minutes
    seconds = max(seconds, FIVE_MINUTES)
    # Values below an hour are 50 coins
    if seconds < ONE_HOUR:
        return 50
    # Ok base cases are over, now we have to do the fun stuff
    # Floor to last hour
    as_hours = floor(as_hours)
    # Get bounds
    slope_bounds = {
        "1": 5, # 1-6
        "6": 10, # 6-12
        "12": 20, # 12-24
        "24": 30, # 24-48
        "36": 40,
        "48": 50, # 48-336
        "60": 100,
        "72": 150,
        "84": 200,
        "336": 200,
    }
    m = 0
    x1, y1 = 0, 0
    prev_key = 1
    for key in slope_bounds.keys():
        if int(key) > as_hours:
            m = slope_bounds[prev_key]
            x1 = int(prev_key)
            y1 = preset_hours_to_coins[prev_key]
            break
        prev_key = key

    return int(m * (as_hours-x1) + y1)

class AuctionHouse():
    
    def __init__(self, api:HypixelAPI):
        """Setup the AH vars and update the data from local"""
        self.api = api
        self.total_pages = 0
        self.total_auctions = 0
        self.last_updated = 0
        self.auctions:list[SkyblockAuctionPage] = None
        self.update(do_printout=False)
    
    def get_page(self, pageNum:int) -> SkyblockAuctionPage:
        """Request a specific page from the API. If response fails (likely 404), returns error response"""
        ahparams = {
            "page": pageNum,
        }
        response = self.api.do_request(get_request_url("auctions"), save_temporarily=False, params=ahparams)
        if not response["success"]:
            return response
        # Update own metadata based off response
        self.total_pages = response["totalPages"]
        self.total_auctions = response["totalAuctions"]
        obj_response = SkyblockAuctionPage(response)
        self.store_auction_page(pageNum, obj_response)
        return obj_response

    def load_from_local(self):
        """Load the data from the local JSON file. Returns True/False on whether it succeeded."""
        raw_auction_data = read_file_contents(api_auctions_data_file)
        if raw_auction_data == None:
            return False
        auction_data:dict = json.loads(raw_auction_data)
        self.total_pages = auction_data["total_pages"]
        self.total_auctions = auction_data["total_auctions"]
        self.last_updated = auction_data["last_updated"]
        for key in auction_data["auction_pages"].keys():
            if str(key).isnumeric():
                page = SkyblockAuctionPage(auction_data["auction_pages"][key])
                self.store_auction_page(int(key), page)
        return True
    
    def save_to_local(self):
        """Save the current vars to the local JSON file."""
        file_json = {}
        # Load pages into dict
        pageNum = 0
        file_json["auction_pages"] = {}
        for auction_page in self.auctions:
            # Reconvert objs to JSON
            auction_page_json = auction_page
            if isinstance(auction_page_json, SkyblockAuctionPage):
                auction_page_json = auction_page.toJSON()
            file_json["auction_pages"][str(pageNum)] = auction_page_json
            pageNum += 1
        # Load metadata into dict
        file_json["total_pages"] = self.total_pages
        file_json["total_auctions"] = self.total_auctions
        file_json["last_updated"] = time.time()
        # Finally, save as json
        write_file_contents(api_auctions_data_file, json.dumps(file_json))

    def store_auction_page(self, pageNum:int, response:SkyblockAuctionPage):
        """Store some SkyblockAuctionPage to the given pageNum. Makes more pages in self.auctions as needed"""
        # Ensure we have a list of length n which will hold our paginated data
        if self.auctions == None:
            self.auctions = [None] * self.total_pages
        elif pageNum >= len(self.auctions):
            self.total_pages = pageNum + 1
            pages_to_add = self.total_pages - len(self.auctions)
            for _ in range(pages_to_add):
                self.auctions.append(None)
        # Actually insert the response into our array
        self.auctions[pageNum] = response
    
    def is_recent(self, printout=False, threshold_seconds = 600):
        """Get whether the data currently part of the object is recent (within 10 minutes)"""
        seconds_since_last_updated = time.time() - self.last_updated
        if printout:
            print(f"It has been {format_seconds_to_times(seconds_since_last_updated)} since last update to auction house data.")
            print(f"Auction house data will update when data is over {format_seconds_to_times(threshold_seconds)} old.")
        return seconds_since_last_updated < threshold_seconds

    def update(self, refresh_seconds = 600, do_printout=True):
        """Load from local, or if older than 10 minutes, request all pages from remote source."""
        start_page = 0 # control first page to load. used to avoid loading page 0 twice
        # We might have just loaded the data, implement cooldown here to avoid stuffs
        if self.is_recent(printout=False, threshold_seconds=refresh_seconds):
            self.is_recent(printout=do_printout)
            return
        # No local file data, load page 0 to get info
        if not self.load_from_local():
            response = self.get_page(0)
            start_page += 1
            if not response.success:
                raise NotImplementedError("No handling for failed bootstrap request in AuctionHouse update()")
            self.save_to_local()
        else:
            # Dont reload if local is recent enough (arbitrary threshold)
            # We check here also as load_from_local would have a diff time
            if self.is_recent(printout=do_printout, threshold_seconds=refresh_seconds):
                return
        # We now have at least something in auctiondata, including total pages and stuff
        print("Updating auction pages. Please do not interrupt the program, retrieved data is only stored upon completion.")
        pbar = progressbar.ProgressBar(maxval=self.total_pages).start()
        for pageNum in range(start_page, self.total_pages):
            pbar.update(pageNum + 1)
            self.get_page(pageNum)
        self.save_to_local()
    
    def get_auctions_as_list(self) -> list[SkyblockAuctionData]:
        """Get all the auction data as one big list."""
        auction_list = []
        for page in self.auctions:
            if page == None:
                continue
            for auction in page.auctions:
                auction_list.append(auction)
        return auction_list

    def get_items_keyed_by(self, key) -> dict[list[SkyblockAuctionData]]:
        """
        Get all the auction items keyed by a particular value of SkyblockAuctionData.
        All matches of a key are added to a list in that key's value.
        """
        auction_dict = {}
        for page in self.auctions:
            if page == None:
                continue
            for auction in page.auctions:
                # fukshit way to create new entires that dont exist yet but i dont care
                try:
                    auction_dict[auction.original_json[key]]
                except KeyError:
                    auction_dict[auction.original_json[key]] = []
                auction_dict[auction.original_json[key]].append(auction)

        return auction_dict