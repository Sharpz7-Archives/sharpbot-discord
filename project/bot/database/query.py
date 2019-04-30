import random

from rethinkdb import RethinkDB
from rethinkdb.errors import ReqlNonExistenceError

from bot.classes import Inv, materials, pet_scavengerate
from bot.constants import BOAT_TABLE, BUILD_TABLE, USER_TABLE, WATER_COLOUR
from bot.utils import bot_conn, pixel
from bot.errors import UserNotFoundError, BoatNotFoundError

r = RethinkDB()


async def user(author, *args):
    """
    Gets data of the user.

    The args allow for only certain parts of the database to be called.
    """

    author = str(author)
    # If there is no args return the whole document
    if not args:
        data = await r.table(USER_TABLE).get(author).run(bot_conn)
    else:
        data = []

        try:
            for item in args:
                data.append(await r.table(USER_TABLE).get(author)[item].run(bot_conn))

        except ReqlNonExistenceError:
            raise UserNotFoundError

    # Removes useless tuple
    if data is not None and len(data) == 1:
        data = data[0]

    return data


async def pet_ranuser(pet, author):
    """
    Try and find a user that the pet can find

    Chance increases as pet level increases
    """

    author = str(author)
    cursor = await r.table(USER_TABLE).run(bot_conn)
    lvl = pet.get("lvl")
    choice = pet_scavengerate.at(lvl)
    async for doc in cursor:
        user_not_pet_owner = (str(doc.get("id")) != author)
        if random.randint(1, choice) == 1 and user_not_pet_owner:
            return doc


async def coords(author):
    """
    Gets all user's that are on the coordinate of the user
    specified
    """
    author = str(author)
    users = []
    coords = await user(author, "coords")
    cursor = await r.table(USER_TABLE).filter({'coords': coords}).run(bot_conn)

    # Loop through all users
    async for doc in cursor:
        users.append(doc["id"])

    return users, coords


async def all_buildings(name, value, forcelist=False):
    """
    Get all buildings that match the name, value pair given.

    Useful for checking clans or coords.
    """

    data = []
    cursor = await r.table(
        BUILD_TABLE).filter({name: value}).run(bot_conn)

    # Loop through all users
    async for doc in cursor:
        data.append(doc)

    if data is not None and len(data) == 1 and not forcelist:
        data = data[0]
    return data


async def building(author, *args):
    """
    Get the data of a user's building.

    The same as Get.user, you can specify what data you
    want in the args
    """
    author = str(author)
    # If there is no args return the whole document
    if not args:
        data = await r.table(BUILD_TABLE).get(author).run(bot_conn)
    else:
        data = []
        for item in args:
            data.append(await r.table(BUILD_TABLE).get(author)[item].run(bot_conn))

    # Removes useless tuple
    if data is not None and len(data) == 1:
        data = data[0]
    return data


async def start(author, width, height):
    """
    Creates the initial user entry in the database
    """

    # list of XY co-ords - better to store instead of
    # constantly making new lists
    while True:
        rand_coords = [random.randint(1, width), random.randint(1, height)]
        if await pixel(rand_coords) != WATER_COLOUR:
            break

    # Chooses a random clan
    clan = random.choice([
        "Clan Tiene",
        "Clan Uisge",
        "Clan Ogsaidean",
        "Clan Talamh"])

    fight = ["Empty"]*3

    data = [
        {
            "id": str(author.id),
            "coords": rand_coords,
            "clan": clan,
            "fight": fight,
            "pet": {},
            "inventory": {},
            "asleep": True,
            "in_boat": False
        }
            ]

    await r.table(USER_TABLE).insert(data).run(bot_conn)
    return rand_coords, clan


async def boat(author, *args):
    """
    Get all of a users boats!

    Using args you can choose what parts of the data to take
    """

    author = str(author)
    # If there is no args return the whole document
    if not args:
        data = await r.table(BOAT_TABLE).get(author).run(bot_conn)
    else:
        data = []
        try:
            for item in args:
                data.append(await r.table(BOAT_TABLE).get(author)[item].run(bot_conn))
        except ReqlNonExistenceError:
            raise BoatNotFoundError

    # Removes useless tuple
    if data is not None and len(data) == 1:
        data = data[0]

    return data


async def user_parse(author):
    """
    Parses the users inventory into nice categories.

    Use for displaying this data
    """

    author = str(author)
    inv = await user(author, "inventory")
    if not inv:
        return []

    output, lvl = [], ""
    for cname, c in Inv.all_instances:
        output.append(f"**{cname}:**")
        for name, value in inv.items():
            lvl = ""
            item = c.get(name)
            if item:
                if item.single:
                    lvl = "lvl"
                if value != 0:
                    output.append(f"{item} - {lvl} {value}")
    return output


async def building_parse(author, value):
    """
    Parses the buildings info into nice categories.

    Use for displaying this data
    """

    author = str(author)
    inv = await building(author, value)
    output = []
    for name, value in inv.items():
        item = materials.get(name)
        if item:
            if value != 0:
                output.append(f"{item} - {value}")
    return output


async def pet_parse(author):
    """
    Display the pet data in a nice parsed format.
    """

    author = str(author)
    inv = await user(author, "pet")
    output = []
    for item in inv:
        output.append(f"{item.capitalize()}: {inv[item]}")

    return output
