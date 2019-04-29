from rethinkdb import RethinkDB

from bot.classes import Building, craft_upgraderate
from bot.constants import BUILD_TABLE, USER_TABLE, BOAT_TABLE
from bot.utils import bot_conn, upgrade_text


r = RethinkDB()


async def inv(author, name, total):
    """
    Edit a item in a user's inventory
    """

    author = str(author)
    data = {
            "inventory": {name: (r.row["inventory"][name]+total).default(total)}
        }
    await r.table(USER_TABLE).get(author).update(data).run(bot_conn)


async def coord(author, coords):
    """
    Change a user's position
    """

    author = str(author)
    data = {"coords": coords}
    await r.table(USER_TABLE).get(author).update(data).run(bot_conn)


async def trade(author, trade, times, inventory):
    """
    Remove and add items to a user's inventory,
    depending on the trade specified
    """

    author = str(author)
    buying, bp = trade.buying
    selling = trade.selling

    # Does upgrade item seperately
    if trade.upgrade:
        selling = trade.selling[1:]
        await inv(author, trade.selling[0][0].name, -(1 * times))

    for item, price in selling:
        cost = price * times
        # If item is an upgrade...
        if trade.upgrade:
            # Make sure upgraded costs are used.
            lvl = inventory.get(trade.selling[0][0].name)
            cost = cost * craft_upgraderate.at(lvl)
        await inv(author, item.name, -(cost))

    await inv(author, buying.name, (bp * times))

    if trade.upgrade:
        title = await upgrade_text(trade, inventory, times)
    else:
        title = f"Traded {trade} {times} *times*!"

    # Returns a nice text message explaining what they traded.
    return title


async def building(author, building, clan, coords):
    """
    Creates a user's building.

    Removes the items used up afterwards.
    """

    author = str(author)
    data = {
        "id": author,
        "clan": clan,
        "coords": coords,
        "name": building.name,
        "level": 1,
        "public": {},
        "private": {}
    }
    await inv(author, building.mat.name, -building.hp)
    await r.table(BUILD_TABLE).insert(data).run(bot_conn)


async def upgrade(author, name, cost):
    """Upgrades the user's building to the next level."""

    author = str(author)
    building = Building.lookup[name]
    data = {"level": r.row["level"]+1}
    await inv(author, building.mat.name, -(cost))
    await r.table(BUILD_TABLE).get(author).update(data).run(bot_conn)


async def destroy_building(author):
    """Removes a user's building entirely"""

    author = str(author)
    await r.table(BUILD_TABLE).get(author).delete().run(bot_conn)


async def destroy_boat(author):
    """Removes a user's boat entirely"""

    author = str(author)
    await r.table(BOAT_TABLE).get(author).delete().run(bot_conn)


async def store(author, mat, amount, location="public"):
    """
    Store some of the user's items inside
    there clan's buildings
    """

    author = str(author)
    data = {location: {mat: (r.row[location][mat]+amount).default(amount)}}
    await inv(author, mat, -amount)
    await r.table(BUILD_TABLE).get(author).update(data).run(bot_conn)


async def withdraw(author, mat, amount, location="public"):
    """
    Withdraw some items from inside your own clan's buildings.

    If you own the building you can withdraw from the private vault.
    """

    author = str(author)
    data = {location: {mat: (r.row[location][mat]-amount).default(amount)}}
    await inv(author, mat, amount)
    await r.table(BUILD_TABLE).get(author).update(data).run(bot_conn)


async def sleep(author, state):
    """Change the user's database status to "asleep" """

    author = str(author)
    data = {"asleep": state}
    await r.table(USER_TABLE).get(author).update(data).run(bot_conn)


async def fight(author, slots, name, place):
    """
    Add's or remove's one of the user's
    items from their fighting slots.
    """

    author = str(author)

    # If an item is being added
    if place > 0:
        slots[place-1] = name
        data = {"fight": slots}
        await r.table(USER_TABLE).get(author).update(data).run(bot_conn)

    # If not, remove it
    else:
        slots[abs(place)-1] = "Empty"
        data = {"fight": slots}
        await r.table(USER_TABLE).get(author).update(data).run(bot_conn)


async def pet(author, name, level):
    """Create's a pet."""

    author = str(author)
    data = {"pet": {
        "name": name,
        "lvl": level}}
    await r.table(USER_TABLE).get(author).update(data).run(bot_conn)


async def pet_lvl(author):
    """Level's up your pet"""

    author = str(author)
    data = {"pet": {
        "lvl": (r.row["pet"]["lvl"]+1)}}
    await r.table(USER_TABLE).get(author).update(data).run(bot_conn)


async def place_boat(author, coords, clan, boat):
    """
    Creates a boat in the world.

    Adds a boat document in the boats table.
    """

    author = str(author)
    data = {
        "id": author,
        "clan": clan,
        "coords": coords,
        "name": boat.name,
        "level": 1
    }
    await inv(author, boat.name, -1)
    await r.table(BOAT_TABLE).insert(data).run(bot_conn)


async def set_boat(author, status):
    """
    Allows the player to sail on water.

    Adds a "on_boat" tag to user table.
    """

    author = str(author)
    data = {"in_boat": status}
    await r.table(USER_TABLE).get(author).update(data).run(bot_conn)


async def move_boat(author, coords):
    """Moves boat to players location"""

    author = str(author)
    data = {"coords": coords}
    await r.table(BOAT_TABLE).get(author).update(data).run(bot_conn)

# For Admins


async def purge(author):
    """Remove's a user entirely from the database"""

    author = str(author)
    await r.table(USER_TABLE).get(author).delete().run(bot_conn)
    await r.table(BUILD_TABLE).get(author).delete().run(bot_conn)
    await r.table(BOAT_TABLE).get(author).delete().run(bot_conn)


async def merge(key, *value):
    """
    Add a new value to all users in the table

    Understands to convert "{}" to {}
    """

    value = " ".join(value)

    if value == "{}":
        value = {}

    elif value == "True":
        value = True

    elif value == "False":
        value = False

    cursor = await r.table(USER_TABLE).run(bot_conn)
    async for doc in cursor:
        doc[key] = value
        await r.table(USER_TABLE).replace(doc).run(bot_conn)


async def delete(key):
    """Remove a key in all the users docs"""

    cursor = await r.table(USER_TABLE).run(bot_conn)
    async for doc in cursor:
        del doc[key]
        await r.table(USER_TABLE).replace(doc).run(bot_conn)
