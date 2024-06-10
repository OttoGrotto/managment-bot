from pymongo import MongoClient
from datetime import datetime
from typing import Literal, Optional
from ....ClanDetails import DBURI

mongo = MongoClient(DBURI)
mongo_db = mongo['services']
mongo_collection = mongo_db['competitions']

class competition:
    def __init__(self, name: str, start: datetime, end: datetime, type: Literal['skill', 'boss', 'skow', 'botw'], description: str, url: Optional[str]) -> None:
        self.name = name if name else self.raiseerror("Name is required")
        self.start = start if start < end else self.raiseerror("Start date must be before end date")
        self.end = end if end > start else self.raiseerror("End date must be after start date")
        self.type = type if type in ['skill', 'boss', 'skow', 'botw'] else self.raiseerror("Type must be one of the following: skill, boss, skow, botw")
        self.description = description if description else self.raiseerror("Description is required")
        self.url = url if url else None

    def save(self):
        mongo_collection.insert_one({
            "name": self.name,
            "start": self.start,
            "end": self.end,
            "type": self.type,
            "description": self.description,
            "url": self.url
        })

    def delete(self):
        mongo_collection.delete_one({"name": self.name})

    def update(self, new_data):
        mongo_collection.update_one({"name": self.name}, {"$set": new_data})

    @staticmethod
    def get(name):
        return mongo_collection.find_one({"name": name})

    @staticmethod
    def get_all():
        return mongo_collection.find({})

    @staticmethod
    def delete_all():
        mongo_collection.delete_many({})

    @staticmethod
    def update_all(new_data):
        mongo_collection.update_many({}, {"$set": new_data})

    @staticmethod
    def raiseerror(msg):
        raise ValueError(msg)