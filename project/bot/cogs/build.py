import asyncio

from discord.ext import commands
from bot.classes import Building, materials, b_upgraderate

from bot.constants import Emoji, CONFIRM_REACTION_TIMEOUT, BATTLING
from bot.database import query, modify
from bot.utils import create_embed


class BuildingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="build", aliases=["b"])
    async def build(self, ctx):
        """All the build commands. Do /help build"""

        # If the user just invokes `/build` on it's own...
        if ctx.invoked_subcommand is None:
            title = "BUILD COMMAND HELP"
            text = (
                "```"
                "/build list - Shows all your class buildings\n"
                "/build create <name> - creates a building where you are standing\n"
                "/build info - shows stats about your current building.\n"
                "/build upgrade - upgrade your building to the next level\n"
                "/build destroy - Destroy your building\n"
                "/build store <amount> <material> - store materials in your building.\n"
                "/build withdraw <amount> <material> - take mats out of your building\n\n"
                "**PLEASE NOTE** Type `private` at the end of the /b store command to keep items in"
                "your personal vault!```\n\n"
            )

            # Make a list of buildings for the user's convenience.
            buildings = []
            for b in Building.lookup.values():
                buildings.append(f"{b} - {b.hp} {b.mat}")
            title2 = "**All buildings you can build.**\n\n"
            text = text + title2 + "\n".join(buildings)

            embed = await create_embed(ctx, title, text)
            await ctx.send(embed=embed)

    @build.command(name="list", aliases=["castles"])
    async def show(self, ctx):
        """List all your clan's buildings"""

        clan = await query.user(ctx.author.id, "clan")
        buildings = await query.all_buildings("clan", clan, forcelist=True)

        # Construct a list of all buildings in the clan.
        clan_buildings = []
        for doc in buildings:
            b = Building.lookup[doc["name"]]
            text = f"{b} - {doc['coords']} - Lvl {doc['level']}"
            clan_buildings.append(text)

        # Now send a lovely little embed with them all listed.
        title = f"**{clan.upper()}'S BUILDINGS**"
        text = "\n".join(clan_buildings)
        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @build.command(name="create")
    async def create(self, ctx, name=None):
        """Creates a building at your current coords"""

        if name is None:
            # Make a list of buildings for the user's convenience.
            buildings = []
            for b in Building.lookup.values():
                buildings.append(f"{b} - {b.hp} {b.mat}")
            title = "**All buildings you can build.**\n\n"
            text = "\n".join(buildings)

            embed = await create_embed(ctx, title, text)
            return await ctx.send(embed=embed)

        name = name.capitalize()

        inv, coords, clan, in_boat = await query.user(
            ctx.author.id, "inventory", "coords", "clan", "in_boat"
        )

        current_building = await query.building(ctx.author.id)
        building_here = await query.all_buildings("coords", coords)

        building = Building.lookup.get(name)

        if building is None:
            return ctx.send("That building doesn't exist!")

        mat = building.mat
        enough_material = inv.get(mat.name, 0) >= building.hp

        if current_building is not None:
            title = "You already have a building!"
            text = "Destory it with /b destroy!"

        elif in_boat:
            title = "You can not build in water!"
            text = "Head for shore with /move shore!"

        elif not enough_material:
            title = f"You don't have enough {mat}!"
            text = "Get more with /mine!"

        elif building_here:
            title = "There is already a building here!"
            text = "Try do build somewhere else!"

        else:
            await modify.building(ctx.author.id, building, clan, coords)
            title = f"You have successfully built a {name} for {building.hp} {mat}"
            text = "Now look at your building with /b list"

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @build.command(name="info")
    async def info(self, ctx):
        """Lets you travel to your home building!"""

        building = await query.building(ctx.author.id)
        if building is None:
            title = "You don't have a home!"
            text = "To get a home, do /help build!"

        else:
            coords, level, name = await query.building(
                ctx.author.id, "coords", "level", "name"
            )

            b = Building.lookup[name]
            cost = b.hp * b_upgraderate.at(level)

            # Get the contents about the building's vaults.
            private = "\n".join(await query.building_parse(ctx.author.id, "private"))
            public = "\n".join(await query.building_parse(ctx.author.id, "public"))

            title = f"**Your {b}**"
            text = (
                f"**Base coords**: {coords[0]} {coords[1]}\n"
                f"**Base Level**: {level}\n"
                f"**Cost to upgrade to Lvl {level+1}**: {cost} {b.mat}\n"
                f"**Public Vault**: \n{public}\n"
                f"**Private Vault**: \n{private}\n"
            )

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @build.command(name="upgrade")
    async def upgrade(self, ctx):
        """
        Upgrade the building to the next level!
        """

        # Get some information about the user and the building.
        name, level = await query.building(ctx.author.id, "name", "level")
        b = Building.lookup[name]
        inv = await query.user(ctx.author.id, "inventory")
        cost = b.hp * b_upgraderate.at(level)

        no_material = b.mat.name not in inv
        enough_material = inv.get(b.mat.name, 0) >= cost

        if no_material or not enough_material:
            title = f"You dont have enough {b.mat}!"
            text = "Get more with /mine!"

        else:
            await modify.upgrade(ctx.author.id, b.name, cost)
            title = f"Upgraded your {b}!"
            text = f"**Current Level** - {level + 1}\n" f"Do /help build for more info!"

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @build.command(name="destroy")
    async def destroy(self, ctx):
        """
        Destroy your current building so you can get a new one!

        Note: destroyed buildings can not be returned
        """

        building = await query.building(ctx.author.id)

        if building is None:
            title = "You do not have a building!"
            text = "You can't destroy nothing dummy!"
            show_easter_egg = True

        else:
            title = "**Are you sure you want to destroy your building?**"
            text = "You cannot bring it back!"
            show_easter_egg = False

        # We'll add a confirmation emoji to this message.
        embed = await create_embed(ctx, title, text)
        response = await ctx.send(embed=embed)

        await response.add_reaction(Emoji.confirm)

        def checker(reaction, user):
            correct_msg = reaction.message.id == response.id
            correct_user = user == ctx.author

            return correct_msg and correct_user

        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add", timeout=CONFIRM_REACTION_TIMEOUT, check=checker
            )

        except asyncio.TimeoutError:
            return
        else:
            if str(reaction.emoji) == Emoji.confirm:
                if show_easter_egg:
                    title = "You should never find this error!!!"
                    text = "Please report to https://mcadesigns.co.uk/report/"
                else:
                    title = "**Your building was removed!**"
                    text = "Build another building with /help b!"
                    await modify.destroy_building(ctx.author.id)
                embed = await create_embed(ctx, title, text)
                await response.edit(embed=embed)

    @build.command(name="store")
    async def store(self, ctx, amount: int = 1, mat_name=None, location="public"):
        """
        Store items in your building!
        """

        # Get the building at this point, and the user's inventory.
        amount = abs(amount)
        mat_name = mat_name.capitalize()
        coords, inv, clan = await query.user(
            ctx.author.id, "coords", "inventory", "clan"
        )
        building = await query.all_buildings("coords", coords)
        mat = materials.get(mat_name)
        enough_material = inv.get(mat.name, 0) > 0

        if not building:
            title = "There is not a building here!"
            text = "Find your clans buildings with /b list!"

        elif not mat:
            title = "You can only store Ores!"
            text = "Make sure your item is a Ore!"

        elif not enough_material:
            title = f"Sorry, you do not have this much {mat}!"
            text = "Get some more with /mine!"

        elif clan != building["clan"]:
            title = f"You are not in clan {building['clan']}!"
            text = "You must be in the persons clan to use it!"

        else:
            if location != "private":
                title = f"**Stored {amount} {mat}!**"
                text = "To withdraw, do /b withdraw!"
                await modify.store(ctx.author.id, mat.name, amount)
            else:
                title = f"**Stored {amount} {mat}!**"
                text = "To withdraw, do /b withdraw!"
                await modify.store(ctx.author.id, mat.name, amount, "private")

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @build.command(name="withdraw")
    async def take(self, ctx, amount: int = 1, mat_name=None, location="public"):
        """
        Withdraw items in your building!
        """

        # Gather information about the building and stuff.
        amount = abs(amount)
        mat_name = mat_name.capitalize()
        coords = await query.user(ctx.author.id, "coords")
        b = await query.all_buildings("coords", coords)
        mat = materials.get(mat_name)

        if not b:
            title = "There is not a building here!"
            text = "Find your clans buildings with /b list!"

        elif not mat:
            title = "You can only store materials!!"
            text = "Make sure your item is a material!"

        else:
            owner, public, private = (b["id"], b["public"], b["private"])

            # Choose which vault to withdraw from
            if location != "private":
                if public.get(mat.name, 0) < amount:
                    title = f"Sorry, you do not have this much {mat}!"
                    text = "Get some more with /mine!"

                else:
                    title = f"**Withdrew {amount} {mat}!**"
                    text = "To store, do /b store!"
                    await modify.withdraw(ctx.author.id, mat.name, amount)
            else:
                if owner != str(ctx.author.id):
                    title = "You do not own this building!"
                    text = "Use the public vault!"

                elif private.get(mat.name, 0) < amount:
                    title = f"Sorry, you do not have this much {mat}!"
                    text = "Get some more with /mine!"

                else:
                    title = f"**Withdrew {amount} {mat}!**"
                    text = "To store, do /b store!"
                    await modify.withdraw(ctx.author.id, mat.name, amount, "private")

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @build.command(name="defend", hidden=True)
    async def defend(self, ctx):
        """
        Defend your clans buildings from being attacked
        """

        coords, clan = await query.user(ctx.author.id, "coords", "clan")
        coords = tuple(coords)
        building = await query.all_buildings("coords", coords)

        if ctx.author.id in BATTLING[coords].users:
            title = "You are already in a battle!"
            text = "How am I going to fix this? :thinking:"

        elif coords not in BATTLING:
            title = "There is no battle going on here!"
            text = "Try doing /f duel to do 1v1 battles!"

        elif building["clan"] != clan:
            title = "This is not one of your clan's buildings!"
            text = "To attack it do /f attack!"

        else:
            # Add the user to the defenders list.
            await BATTLING[coords].add_user(ctx.author.id, BATTLING[coords].defenders)

            title = f"You have joined the battle at {coords}"
            text = "Try and help defend the castle!"
        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @build.command(name="attack", hidden=True)
    async def attack(self, ctx):
        """
        Start an attack on a building!
        """

        coords, clan = await query.user(ctx.author.id, "coords", "clan")
        coords = tuple(coords)
        building = await query.all_buildings("coords", coords)

        if ctx.author.id in BATTLING:
            title = "You are already in a battle!"
            text = "How am I going to fix this? :thinking:"

        elif building["clan"] == clan:
            title = "You can not attack your own clan!"
            text = "To defend your clan, do /f defend"

        elif coords in BATTLING:
            # Add the user to the attackers list if a battle is here.
            await BATTLING[coords].add_user(ctx.author.id, BATTLING[coords].attackers)

            title = f"You have joined the battle at {coords}"
            text = "Try and help beat the castle!"

        # Otherwise, start a battle if one isn't here already.
        else:
            title = f"A battle against the castle has started at {coords}"
            text = "Try and get more of your clanmates to help you!"
            embed = await create_embed(ctx, title, text)
            response = await ctx.send(embed=embed)

            # Add the battle to the battle list.
            battle = Battle(coords, response, self.bot)
            await battle.add_user(ctx.author.id, battle.attackers)
            BATTLING[coords] = battle
            self.bot.loop.create_task(battle.loop())
            return

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)


class Battle:
    def __init__(self, coords, response, bot):
        self.users = []
        self.attackers = []
        self.defenders = []
        self.coords = coords
        self.response = response
        self.bot = bot
        self.looping = True

    async def loop(self):
        while self.looping:
            await asyncio.sleep(4)
            title = "Testing..."
            text = f"List: {self.users}"
            embed = await create_embed(self.response, title, text)
            await self.response.edit(embed=embed)

    async def add_user(self, author, mode):
        self.users.append(author)
        mode.append(author)


def setup(bot):
    bot.add_cog(BuildingCommands(bot))
