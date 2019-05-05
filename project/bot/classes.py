import math
import os
import yaml

from unicodedata import lookup as lookup_emoji
from bot.constants import CLASSES_FILE, DEFAULT_CLASSES_FILE, Emoji
import random


try:
    with open(CLASSES_FILE, "r") as f:
        data = yaml.safe_load(f)

except FileNotFoundError:
    with open(DEFAULT_CLASSES_FILE, "r") as f:
        data = yaml.safe_load(f)

if os.environ.get("CICD", "FALSE") == "TRUE":
    with open(DEFAULT_CLASSES_FILE, "r") as f:
        data = yaml.safe_load(f)


class Mats:
    """
    All the materials you can mine.

    They all stack in your inventory
    """

    lookup = {}

    def __init__(self, name, rarity, emoji, utilities=None):
        self.name = name
        self.rarity = rarity
        self.emoji = lookup_emoji(emoji)
        self.single = False
        if utilities is None:
            utilities = []
        self.utilities = utilities

    def __repr__(self):
        text = f"{self.emoji} {self.name}"
        return text


mats_data = data.get("mats")

for key, values in mats_data.items():
    Mats.lookup[key] = Mats(**values)


class Items:
    """
    All the items you can fight with / event items

    Does not stack in your inventory.
    """

    lookup = {}

    def __init__(
        self, name, emoji, rarity=None, damage=None, health=None, utilities=None
    ):
        self.name = name
        self.emoji = lookup_emoji(emoji)
        self.damage = damage
        self.health = health
        self.single = True
        self.rarity = rarity
        if utilities is None:
            utilities = []
        self.utilities = utilities

    def __repr__(self):
        text = f"{self.emoji} {self.name}"
        return text


items_data = data.get("items")

for key, values in items_data.items():
    Items.lookup[key] = Items(**values)


class Fist:
    def __init__(self):
        self.damage = 1
        self.emoji = Emoji.fist
        self.name = "Fist"
        self.health = None

    def __repr__(self):
        return f"{self.emoji} {self.name}"


class Creatures:
    """
    All the animals you can get in the world

    Does not stack in your inventory
    """

    lookup = {}

    def __init__(
        self,
        name,
        emoji,
        rarity=None,
        single=True,
        damage=None,
        health=None,
        utilities=False,
    ):
        self.name = name.capitalize()
        self.emoji = lookup_emoji(emoji)
        self.damage = damage
        self.health = health
        self.single = single
        self.rarity = rarity
        self.utilities = utilities

    def __repr__(self):
        text = f"{self.emoji} {self.name}"
        return text


creature_data = data.get("creatures")

for key, values in creature_data.items():
    Creatures.lookup[key] = Creatures(**values)


class Plants:
    """
    All the plants you can collect

    These can be stacked
    """

    lookup = {}

    def __init__(self, name, emoji, rarity, level_up_boost):
        self.name = name.capitalize()
        self.emoji = lookup_emoji(emoji)
        self.rarity = rarity
        self.single = False
        self.pet_multiplyer = level_up_boost
        self.utilities = ["food"]

    def __repr__(self):
        text = f"{self.emoji} {self.name}"
        return text


plant_data = data.get("plants")

for key, values in plant_data.items():
    Plants.lookup[key] = Plants(**values)


class Boats:
    """
    All the boats you can get.

    Get destroyed in your Inv after use.
    """

    lookup = {}

    def __init__(self, name, emoji, speed, rarity=None):
        self.name = name.capitalize()
        self.emoji = lookup_emoji(emoji)
        self.speed = speed
        self.single = True
        self.rarity = rarity

    def __repr__(self):
        text = f"{self.emoji} {self.name}"
        return text


boat_data = data.get("boats")

for key, values in boat_data.items():
    Boats.lookup[key] = Boats(**values)


class Inv:
    """
    Allows the inv parser to do its job.

    All new inv classes MUST be made into a Inv instance to show up

    The self.single var determines whether they level up or stack.

    All of these can be traded

    ALL INV CLASSES MUST HAVE A RARITY OPTION

    Rarities should be a value between 1 and 10.
    """

    all_instances = []

    def __init__(self, item):
        self.item = item
        Inv.all_instances.append([item.__name__, item.lookup])

    def __iter__(self):
        for item in self.item.lookup.values():
            yield item

    def get(self, name):
        """Returns the name if found from the Inv instance."""

        return self.item.lookup.get(name)


def inv_find(name):
    """Returns the first inv object that has the same key"""

    for _, lookup in Inv.all_instances:
        for key, value in lookup.items():
            if key.upper() == name.upper():
                return value


materials = Inv(Mats)
items = Inv(Items)
creatures = Inv(Creatures)
boats = Inv(Boats)
plants = Inv(Plants)


class Building:
    """All the buildings you can build."""

    lookup = {}

    def __init__(self, name, emoji, hp, mat):
        Building.lookup[name] = self
        self.name = name.capitalize()
        self.emoji = lookup_emoji(emoji)
        self.hp = hp
        self.mat = inv_find(mat)

    def __repr__(self):
        text = f"{self.emoji} {self.name}"
        return text


build_data = data.get("building")

for key, values in build_data.items():
    Building.lookup[key] = Building(**values)


class Trade:
    """
    Defines the trades that can be made.

    You can use any item in Inv.lookup
    """

    all_trades = []

    def __init__(self, selling, buying, category="Traders"):
        self.selling_list = []

        for counter, sells in enumerate(selling):
            item, price = sells
            item = inv_find(item)
            self.selling_list.append(f"{price} {item}")
            selling[counter] = [item, price]

        self.buying = inv_find(buying[0]), buying[1]
        self.selling = selling
        self.category = category

        # Checks if a item is being upgraded
        if self.buying[0].single and self.buying[1] > 1:
            self.price = "an upgraded"
            self.upgrade = True
        else:
            self.price = self.buying[1]
            self.upgrade = False

        # So we can include upgrade cost.
        self.crafttext = f"xxx **for** {self.price} {self.buying[0]}"

    def __repr__(self):
        text = (
            f"{' and '.join(self.selling_list)} **for** {self.price} {self.buying[0]}"
        )
        return text


trade_data = data.get("trades")

for key, values in trade_data.items():
    Trade.all_trades.append(Trade(**values))


def trade_set(name, amount):
    """
    Gets all the trades for that catagory and
    chooses how many to show daily
    """
    allowed_trades = []

    # Gets all trades for that towns catagory
    for trade in Trade.all_trades:
        if trade.category == name:
            allowed_trades.append(trade)

    if len(allowed_trades) < amount:
        amount = len(allowed_trades)

    daily_trades = random.sample(allowed_trades, amount)

    return list(daily_trades)


craft_recipes = trade_set("Craft", 7)


class Place:
    """
    All the places you can travel to.

    These are dynamically added to the games map,
    so you don't need to worry about it!
    """

    lookup = {}

    def __init__(self, name, coords, typev, trade_name="Traders"):
        self.name = name
        self.coords = coords
        self.type = lookup_emoji(typev)
        self.trade_name = trade_name
        self.trades = trade_set(trade_name, 4)

    def __repr__(self):
        text = f"{self.type} {self.name}"
        return text


place_data = data.get("places")

for key, values in place_data.items():
    Place.lookup[key] = Place(**values)


class Vector:
    """
    Allows our code to use vectors.

    Supports addition, subtraction and multiplication.
    """

    def __init__(self, x, y):
        self.x = int(x)
        self.y = int(y)

    def __repr__(self):
        text = f"[{int(self.x)}]\n" f"[{int(self.y)}]"
        return text

    def __sub__(self, vector):
        x = self.x - vector.x
        y = self.y - vector.y
        return Vector(x, y)

    def __add__(self, vector):
        x = self.x + vector.x
        y = self.y + vector.y
        return Vector(x, y)

    def __mul__(self, vector):
        x = self.x * vector.x
        y = self.y * vector.y
        return Vector(x, y)

    def __abs__(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def __iter__(self):
        yield self.x
        yield self.y

    def scale(self, scalar):
        x = self.x * scalar
        y = self.y * scalar
        return Vector(x, y)


class GameItemRate:
    """
    Object that defines the rate at which something
    like feeding upgrades increases.
    """

    def __init__(self, ary, style=None):
        self.array = ary
        self.style = style

    def at(self, num):
        num = int(num)
        if num > len(self.array) - 1:
            if self.style == "linear":
                return int(max([self.array[-1], self.style * (num)]))
            else:
                return int(self.array[-1])
        else:
            return int(self.array[num - 1])


petlevelrate = GameItemRate([1, 1, 1, 2, 2, 3, 4, 5, 6, 7, 8])
b_upgraderate = GameItemRate([1, 1, 2, 2, 2, 2, 3, 4, 5, 6, 7, 8], 1)
craft_upgraderate = GameItemRate([1, 2, 2, 2, 3, 3, 3, 4, 5, 6, 7, 8])
shield_boostrate = GameItemRate([1, 2, 2.5, 3, 3.5, 3.5, 4, 4.5, 5, 5, 5.5, 6], 1 / 2)
damage_boostrate = GameItemRate([1, 2, 2.5, 3, 3.5, 3.5, 4, 4.5, 5, 5, 5.5, 6], 1 / 2)
animal_boostrate = GameItemRate([1, 2, 3, 3, 3.5, 3.5, 4, 4.5, 5, 5, 5.5, 6], 1)
pet_scavengerate = GameItemRate([10, 9, 9, 8, 8, 8, 7, 7, 7, 6, 6, 5])
