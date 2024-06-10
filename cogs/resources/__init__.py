from pymongo import MongoClient, collection
from cogs import ClanDetails as details
import os
from .loadenv import LoadENV
from typing import Literal

class Database:
    # Connect to the database
    def __init__(self):
        LoadENV()
        try:
            client = MongoClient(details.DBURI.replace("<password>", os.environ.get("DBPASS")))
        except Exception as e:
            print(e)
        db = client["management-bot"]
        itemdb = client["store"]
        eventcoll = client["events"]
        self.events = eventcoll["events"]
        self.shop = itemdb["store"]
        self.items = itemdb["items"]
        self.guilds = db["guilds"]
        self.users = db["users"]
        self.invites = db["invite_links"]

## DO NOT TOUCH THIS CODE

    # Get the guilds collection
    def get_guilds(self, guild_id: int):
        return self.guilds.find_one({"_id": guild_id})

    # Get the users collection
    def get_user(self, user_id: int) -> dict:
        if self.users.find_one({"_id": user_id}) != None:
            return self.users.find_one({"_id": user_id})
        else:
            return None

    # Add a guild to the database
    def add_guild(self, guild_id: int):
        self.guilds.insert_one({"_id": guild_id, "prefix": details.PREFIX})

    # Add a user to the database
    def add_user(self, user_id: int):
        self.users.insert_one({"_id": user_id, "inventory": {}, "gear": {"armor": {}, "sword": {}, "tools": []}, "stats": {"attack": 0, "defense": 0, "health": 100, "level": 1, "xp": 0, "maxxp": 100, "gold": 0}})

    # Update a user's profile
    def update_user_profile(self, user_id: int, value: dict):
        self.users.update_one({"_id": user_id}, value, upsert=True)

    # Update a guild's prefix
    def update_guild_prefix(self, guild_id: int, prefix: str):
        self.guilds.update_one({"_id": guild_id}, {"$set": {"prefix": prefix}})
    
    # Get a guild's prefix
    def get_guild_prefix(self, guild_id: int):
        return self.guilds.find_one({"_id": guild_id})["prefix"]

    # Delete a guild from the database
    def delete_guild(self, guild_id: int):
        self.guilds.delete_one({"_id": guild_id})

    # Delete a user from the database
    def delete_user(self, user_id: int):
        self.users.delete_one({"_id": user_id})

    # Get an item from the shop collection
    def GetShop(self, item: str) -> dict:
        return self.shop.find_one({"name": item})

    # Get an item from the item collection
    def GetItem(self, item: int | str, keytype: Literal["id", "name"]) -> dict:
        match keytype:
            case "id":
                found_item = self.items.find_one({"_id": item})
                return found_item if found_item != None else None
            case "name":
                found_item = self.items.find_one({"name": item})
                return found_item if found_item != None else None