from dataclasses import dataclass
from .resources import Database as db
import logging

logging.basicConfig(level=logging.INFO)

class BaseModel:
    def __init__(self) -> None:
        self.DB = db()
        self.users = self.DB.users

    def get_user(self, user_id: int) -> dict:
        return self.DB.get_user(user_id)

    def add_user(self, user_id: int) -> bool:
        if self.get_user(user_id) == None:
            self.DB.add_user(user_id)
            return True
        else:
            return False

    def update_user_profile(self, user_id: int, profile: dict) -> bool:
        if self.users.find_one({"_id": user_id}) == None:
            self.DB.update_user_profile(user_id, profile)

    def delete_user(self, user_id: int):
        self.DB.delete_user(user_id)

    def get_user_profile(self, user_id: int):
        return self.DB.get_user(user_id)

    def get_user_profile_item(self, user_id: int, item: str):
        return self.DB.get_user(user_id)["inventory"][item]

    def get_user_profile_item_amount(self, user_id: int, item: str):
        return self.DB.get_user(user_id)["inventory"][item]["amount"]

    def get_user_profile_item_price(self, user_id: int, item: str):
        return self.DB.get_user(user_id)["inventory"][item]["price"]

    def get_user_profile_item_type(self, user_id: int, item: str):
        return self.DB.get_user(user_id)["inventory"][item]["type"]

    def get_user_profile_item_rarity(self, user_id: int, item: str):
        return self.DB.get_user(user_id)["inventory"][item]["rarity"]

    def get_user_profile_item_description(self, user_id: int, item: str):
        return self.DB.get_user(user_id)["inventory"][item]["description"]

    def get_user_profile_item_image(self, user_id: int, item: str):
        return self.DB.get_user(user_id)["inventory"][item]["image"]

    def get_user_profile_item_uses(self, user_id: int, item: str):
        return self.DB.get_user(user_id)["inventory"][item]["uses"]

    def get_user_profile_item_damage(self, user_id: int, item: str):
        return self.DB.get_user(user_id)["inventory"][item]["damage"]

    def get_user_profile_item_defense(self, user_id: int, item: str):
        return self.DB.get_user(user_id)["inventory"][item]["defense"]

@dataclass
class User(BaseModel):
    name: str
    user_id: int
    profile: dict
    inventory: dict
    coins: int
    bank: int
    level: int
    xp: int
    health: int
    max_health: int
    damage: int
    defense: int
    stamina: int
    max_stamina: int

    def __init__(self, user_id: int) -> None:
        super().__init__()
        self.user_id = user_id
        self.profile = self.get_user_profile(user_id)
        self.inventory = self.profile["inventory"]
        self.coins = self.profile["coins"]
        self.bank = self.profile["bank"]
        self.level = self.profile["level"]
        self.xp = self.profile["xp"]
        self.health = self.profile["health"]
        self.max_health = self.profile["max_health"]
        self.damage = self.profile["damage"]
        self.defense = self.profile["defense"]
        self.stamina = self.profile["stamina"]
        self.max_stamina = self.profile["max_stamina"]
        self.name = self.profile["name"]

    def get_user_profile(self, user_id: int):
        return self.DB.get_user(user_id)

@dataclass
class BaseItem(BaseModel):
    name: str
    price: int
    type: str
    description: str
    amount:int

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_str(cls, item: str):
        try:
            return cls(item)
        except Exception as e:
            logging.error(f"Failed to create item from string because of {e}.")
            return None

class Shop(BaseModel):
    def __init__(self) -> None:
        super().__init__()
        self.shop = self.DB.GetShop()

    def get_shop_item(self, item: str):
        return self.shop[item]

    def get_shop_item_price(self, item: str):
        return self.shop[item]["price"]

    def get_shop_item_type(self, item: str):
        return self.shop[item]["type"]

    def get_shop_item_description(self, item: str):
        return self.shop[item]["description"]

    def get_shop_item_uses(self, item: str):
        return self.shop[item]["uses"]

    def get_shop_item_damage(self, item: str):
        return self.shop[item]["damage"]

    def get_shop_item_defense(self, item: str):
        return self.shop[item]["defense"]

@dataclass
class Weapon(BaseItem):
    damage: int

@dataclass
class Tool(BaseItem):
    multiplier: int | float

@dataclass
class Armor(BaseItem):
    defense: int

@dataclass
class Potion(BaseItem):
    uses: int
    effect: str

@dataclass
class Food(BaseItem):
    uses: int

@dataclass
class Material(BaseItem):
    name: str

class ShopError(BaseException): ...