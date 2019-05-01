import asyncio
import math
import os
import random
from contextlib import suppress

import discord
from fuzzywuzzy import fuzz
from PIL import Image
from rethinkdb import RethinkDB
from rethinkdb.errors import ReqlOpFailedError

from bot.classes import Place, Vector, craft_upgraderate
from bot.constants import (BOAT_TABLE, BUILD_TABLE, DATABASE_NAME, HOST,
                           LAND_COLOUR, SEA_FILE, SHORE, SHORE_FILE,
                           SWAMP_COLOUR, TOWNSIZE, USER_TABLE, WATER_COLOUR)

r = RethinkDB()


async def create_embed(ctx, title, text):
    """
    Get a fancy embed for the bot.

    Takes a title and text, adds a nice owner footer.
    """

    try:
        color = ctx.author.colour
    except Exception:
        color = discord.Color.dark_gold()

    suggestion = await suggestions(ctx)

    text += f"\n\n{suggestion}\n"
    embed = discord.Embed(
        title=title,
        description=text,
        colour=color)
    embed.set_footer(text="Created by the Sharpbot Dev Team (/about)")

    return embed


async def suggestions(ctx):
    """
    Returns a suggestion based off of the command used.

    If no suggestion is made for that command, a random
    suggestion is used.
    """

    planned_suggestions = {
        "start": "Why don't you try `/mine` or `/chop` to get resources!",
        "mine": "Explore the world! Do `/help move`!",
        "chop": "Explore the world! Do `/help move`!",
        "move": "Check out the map with `/map`!",
        "pet": "Try feeding your pet with `/feed`!",
        "sail": "Try getting in your boat with `/board`",
        "build": "Try storing your items in your building. Do `/build store`!",
        "inv": "Take a look at crafting with `/craft`!"
    }

    random_suggestions = [
        "Try out Towns and Places with `/help towns`!",
        "Try building your first building with `/help build`!",
        "Checkout bot info with `/about!`",
        "Why don't you try fishing? Do `/fish` in a boat!",
        "Create your dueling gear with `/help fight`!",
        "Get bot annoucements by doing `/announce`!",
        "Do you hate maths? Try `/help calc`!",
        "Wanna hunt for some nice gear? Try `/find`!"
    ]

    try:
        command_name = str(ctx.command).split(" ")[0]

    # Triggers if edits are made, like in /f duel
    except AttributeError:
        suggest = None
    else:
        suggest = planned_suggestions.get(command_name)

    if not suggest:
        suggest = random.choice(random_suggestions)

    return suggest


async def get_coords(ctx, arg1, arg2, coords):
    """Gets cords based of the args provided."""

    current_x, current_y = coords

    directional = str(arg1).lower() in ["left", "right", "up", "down", "shore"]

    if directional:
        if arg2 is None:
            arg2 = 1
        arg2 = int(arg2)
        x, y = await move_direction(arg1, arg2, current_x, current_y)
        return x, y

    # Or if they choose a cordinate...
    elif arg1.isdigit():
        x, y = int(arg1), int(arg2)
        return x, y

    # They must've chosen a place!
    else:
        arg_place = (f"{arg1} {arg2}").lower()
        for place in Place.lookup.values():
            # If the name is spelt close to right...
            if fuzz.ratio(place.name.lower(), arg_place) > 60:
                x, y = place.coords
                return x, y
        # If no matching place was found, let them know.
        else:
            print("Sorry, that is not a valid place.")
            await ctx.send("Sorry, that is not a valid place.")
            return


async def move_direction(direction, amount, x, y):
    # Calculate all the offsets, then choose the right one.
    solve = {
        "left": (x - amount, y),
        "right": (x + amount, y),
        "down": (x, y + amount),
        "up": (x, y - amount),
        "shore": (await nearest_shore_point(x, y))
    }
    try:
        return solve[direction]

    except KeyError:
        return None


async def nearest_shore_point(x, y):
    """
    Checks which shore point is closest to the coords given
    """
    checker = {}
    distances = []
    for pixel in SHORE:
        pixelx, pixely = pixel
        # Calculates distance.
        dist = int(await distance([x, y, pixelx, pixely]))
        checker[dist] = pixelx, pixely
        distances.append(dist)

    # Chooses lowest distance
    minimum = min(distances)

    return checker[minimum]


async def at_town(coords):
    """Checks if the coordinate specified is on a town."""

    # Creates a border using `TOWNSIZE` constant
    testx = range(coords[0]-TOWNSIZE, coords[0]+TOWNSIZE)
    testy = range(coords[1]-TOWNSIZE, coords[1]+TOWNSIZE)

    for town in Place.lookup.values():
        if town.coords[0] in testx:
            if town.coords[1] in testy:
                return town
    town = Wilderness
    return town


async def find_trade(town, amount):
    """
    Get a trade instance if there is the trade
    at the town specified
    """

    town = Place.lookup[town]
    return town.trades[amount-1]


async def pixel(coords):
    """
    Checks if the coordinate specified is on water, swamp or land
    """

    rgb = rgb_data.sea(coords)
    if rgb == WATER_COLOUR:
        return WATER_COLOUR

    elif rgb == SWAMP_COLOUR:
        return SWAMP_COLOUR

    else:
        return LAND_COLOUR


async def linear(coords, distance):
    """
    Tells you your location after moving "s" distance
    from the first set of coords towards the second
    """

    x1, y1, x2, y2 = coords
    # Converts the coords to Vectors
    u = Vector(x1, y1)
    v = Vector(x2, y2)

    # Best formula ever
    final = (v - u).scale(distance / abs(v - u)) + u

    return tuple(final)


async def distance(coords):
    """
    Calculated the distance between 2 points using
    a nice little formula
    """
    x1, y1, x2, y2 = coords
    answer = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    return int(answer)


async def is_owner(ctx):
    """Checks to see if user is a owner"""
    if ctx.author.id in (ctx.bot.appinfo.owner.id, HOST):
        return True
    else:
        title = "You do not have permission to run this command!"
        text = "If you believe this is a error, please contact us on Github."
        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)


async def upgrade_text(recipe, inv, times=None):
    """Displays craft upgrade values instead of normal values"""
    selling_list = []
    upgrade_item = recipe.selling[0]
    # Exclude Initial item (the upgraded item)
    selling_list.append(f"{upgrade_item[0]}")
    for item, price in recipe.selling[1:]:
        lvl = inv.get(upgrade_item[0].name, 1)
        cost = craft_upgraderate.at(lvl)
        selling_list.append(f"{price * cost} {item}")
    desc = recipe.crafttext.replace("xxx", ' and '.join(selling_list))
    if times:
        desc += f" {times} times!"
    return desc


def utility_search(*args, key=None):
    """
    Searches for all instance in a class that meet
    the utility requirements.
    """

    instances = []
    for instance in args:
        for item in instance:
            if key in item.utilities:
                instances.append(item)
    return instances


def utility_return(*args, key=None):
    """Returns the item class based off of the key"""
    for instances in args:
        for item in instances:
            if key == item.name:
                return item


class Wilderness:
    name = "Wilderness"


class RGB:
    """
    All the images as RGB arrays
    """

    def __init__(self):
        with Image.open(SEA_FILE) as im:
            rgb_im = im.convert('RGB')
            self.seawidth, _ = im.size
            self.sea_data = list(rgb_im.getdata())

        with Image.open(SHORE_FILE) as im:
            rgb_im = im.convert('RGB')
            self.shorewidth, _ = im.size
            self.shore_data = list(rgb_im.getdata())

    def shore(self, coords):
        x, y = coords
        return tuple(self.shore_data[self.shorewidth*y+x])

    def sea(self, coords):
        x, y = coords
        return tuple(self.sea_data[self.seawidth*y+x])


rgb_data = RGB()

# Checks if user does not want to use docker.
if os.environ.get("NO_DOCKER", "FALSE") == "TRUE":
    conn_name = "localhost"
else:
    conn_name = "rdb"

# Startup Checks

print("Loading database connection...")
conn = r.connect(conn_name, 28015)

with suppress(ReqlOpFailedError):
    r.db_create(DATABASE_NAME).run(conn)
with suppress(ReqlOpFailedError):
    r.db(DATABASE_NAME).table_create(USER_TABLE).run(conn)
with suppress(ReqlOpFailedError):
    r.db(DATABASE_NAME).table_create(BUILD_TABLE).run(conn)
with suppress(ReqlOpFailedError):
    r.db(DATABASE_NAME).table_create(BOAT_TABLE).run(conn)

loop = asyncio.get_event_loop()
r.set_loop_type("asyncio")

bot_conn = loop.run_until_complete(r.connect(conn_name, db=DATABASE_NAME))
