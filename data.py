"""
A bunch of classes to make JSON into. Classes. But also let them still go back to being JSON
Note that none of these mirror their chances from modifying a var/key's value to the other, and
thus they are meant to be constant. But this is python, so.
Copyright (C) 2024 Romayne (Contact @ https://github.com/MyNameIsRomayne)
"""
from json import JSONEncoder

def init_json_objs(l:list, t:type):
    """Just simple behavior to init all elements in a list as a new type with param obj"""
    new_l = []
    for o in l:
        new_l.append(t(o))
    return new_l

"""Encoder class so JSON loads/dumps can be used sometimes if the toJSON 'conversion' isnt enough"""
class HypixelEncoder(JSONEncoder):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def default(self, o):
        return o.toJSON()

"""Base class of other hypixel data for use"""
class HypixelData():
    
    def __init__(self, json:dict):
        self.original_json:dict = json

    def default(self):
        return self.toJSON()
    
    def toJSON(self):
        return self.original_json
    
class SkyblockAuctionBidData(HypixelData):
    
    def __init__(self, json:dict):
        super().__init__(json)
        self.auction_id:str = json["auction_id"]
        self.bidder:str = json["bidder"]
        self.profile_id:str = json["profile_id"]
        self.amount:int = json["amount"]
        self.timestamp:int = json["timestamp"]

"""Not intended to be edited unless you change original_json var along with the actual vars"""
class SkyblockAuctionData(HypixelData):
    
    def __init__(self, json:dict):
        super().__init__(json)
        self.uuid:str = json["uuid"]
        self.auctioneer:str = json["auctioneer"]
        self.profile_id:str = json["profile_id"]
        self.coop:list[str] = json["coop"]
        self.start:int = json["start"]
        self.end:int = json["end"]
        self.item_name:str = json["item_name"]
        self.item_lore:str = json["item_lore"]
        self.extra:str = json["extra"]
        self.category:str = json["category"]
        self.tier:str = json["tier"]
        self.starting_bid:int = json["starting_bid"]
        self.item_bytes:str = json["item_bytes"]
        self.claimed:bool = json["claimed"]
        self.claimed_bidders:list = json["claimed_bidders"]
        self.highest_bid_amount:int = json["highest_bid_amount"]
        self.bids:list[SkyblockAuctionBidData] = init_json_objs(json["bids"], SkyblockAuctionBidData)

class SkyblockAuctionPage(HypixelData):
    
    def __init__(self, json:dict):
        super().__init__(json)
        self.success:bool = json["success"]
        self.page:int = json["page"]
        self.totalPages:int = json["totalPages"]
        self.totalAuctions:int = json["totalAuctions"]
        self.lastUpdated:int = json["lastUpdated"]
        self.auctions:list[SkyblockAuctionData] = init_json_objs(json["auctions"], SkyblockAuctionData)
