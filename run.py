"""
Main script that makes all the rules. -Romayne
Copyright (C) 2024 Romayne (Contact @ https://github.com/MyNameIsRomayne)
"""

from config import *
from api import HypixelAPI
from auction import AuctionHouse, SkyblockAuctionData, get_time_fee, get_profits_fee
from bazaar import Bazaar
from bits import *
from statistics import median

def get_item_ah_price(item_name:str, ah_item_dict:dict):
    """Get the median price of an item on the auction house."""
    if item_name not in ah_item_dict.keys():
        return 0
    prices = []
    for item in ah_item_dict[item_name]:
        item:SkyblockAuctionData = item
        prices.append(item.starting_bid)
    return median(prices)

def get_item_bz_price(product_data):
    summary = product_data["buy_summary"]
    return summary[0]['pricePerUnit']

if __name__ == "__main__":

    ONE_DAY = 24 * 3600
    AUCTION_LISTING_TIME = ONE_DAY
    AUCTION_HOUSE_FEE = get_time_fee(AUCTION_LISTING_TIME)
    BAZAAR_TAX = 0.01125
    print(f"Auction house fee ({format_seconds_to_times(AUCTION_LISTING_TIME)}): {AUCTION_HOUSE_FEE} coins")

    start = time.time()

    api = HypixelAPI()

    api.info()

    bz = Bazaar(api)

    ah = AuctionHouse(api)

    ah_items = ah.get_items_keyed_by("item_name")

    item_data = []

    for item_key in bit_items:
        product_id = bit_items[item_key]["product_id"]
        # bz handling
        coins_for_product = 0
        coins_per_bit = 0
        ah_entries = 0
        if product_id != None:
            coins_for_product = get_item_bz_price(bz.whole_bazaar_data["products"][product_id])
            coins_for_product *= (1 - BAZAAR_TAX)
        elif (item_key in ah_items.keys()):
            ah_entries = len(ah_items[item_key])
            coins_for_product = get_item_ah_price(item_key, ah_items)
            # Fees (Listing BIN)
            coins_for_product -= get_profits_fee(coins_for_product)
            # Fees (Duration)
            coins_for_product -= AUCTION_HOUSE_FEE

        coins_per_bit = coins_for_product / bit_items[item_key]["cost_bits"]

        item_data.append({
            "item_name": item_key,
            "coins_per_bit": round(coins_per_bit, 2),
            "coins_for_product": round(coins_for_product, 2),
            "on_ah": product_id == None,
            "ah_entries": ah_entries
        })

    item_data.sort(key=(lambda s: s["coins_per_bit"]), reverse=True)

    rank = 1
    for entry in item_data:
        print('')
        print(f"{entry["item_name"]} (#{rank}):")
        sold_on = "auction house" if entry["on_ah"] else "bazaar"
        print(f"Sold on {sold_on}")
        if (entry["on_ah"]):
            print(f"{entry["ah_entries"]} entries")
        print(f"{entry["coins_for_product"]} coins per item")
        print(f"{entry["coins_per_bit"]} coins/bit")
        rank += 1
    
# 6 -> 45
# 7 -> 50
# 8 -> 60