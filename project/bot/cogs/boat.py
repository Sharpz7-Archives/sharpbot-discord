import asyncio

from random import randint

from discord.ext import commands

from bot.classes import boats, creatures, items
from bot.constants import SWAMP_COLOUR, WALKING, Emoji, CONFIRM_REACTION_TIMEOUT
from bot.database import modify, query
from bot.utils import create_embed, utility_search, utility_return


class BoatCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="ship")
    async def ship(self, ctx):
        """
        All commands for controlling your ship!

        You can find them at towns, do /help towns!

        /ship sail - sets your boat down to be boarded
        /ship board - lets your get on your boat
        /ship unboard - lets you get off your boat
        """
        if ctx.invoked_subcommand is None:
            title = "BOAT HELP"
            text = (
                "```\n"
                "All commands for controlling your ship!\n\n"
                "You can find them at towns, do /help towns!\n\n"
                "/ship sail - sets your boat down to be boarded\n"
                "/ship board - lets your get on your boat\n"
                "/ship unboard - lets you get off your boat```\n\n")

            text += "Looking for a ship? Try a town with /places"

            embed = await create_embed(ctx, title, text)
            await ctx.send(embed=embed)

    @ship.command(name="sail")
    async def sail(self, ctx, boat_name="Rowboat"):
        """
        Get on a boat that lets you travel
        in water!"
        """
        boat_name = boat_name.capitalize()
        preposition = boat_name[0].lower() in "aeiou" and "an" or "a"
        inv, coords, clan, in_boat = await query.user(
            ctx.author.id, "inventory", "coords", "clan", "in_boat")
        title = "You do not have any boats!"
        text = "Go and find somewhere you can trade a boat!"
        inv, coords, clan = await query.user(ctx.author.id, "inventory", "coords", "clan")
        pixel = await query.pixel(coords)

        #  If you are not in swampland...
        if pixel != SWAMP_COLOUR:
            return await ctx.send("You need to be closer to the sea!")

        has_boat = inv.get(boat_name, 0) > 0
        boat_exists = utility_return(boats, key=boat_name)
        boat_placed = await query.boat(ctx.author.id)

        if not boat_exists:
            title = f"{boat_name} is not a boat!"
            text = ("It won't find itself, better find one!")
        elif not has_boat:
            title = f"You do not own {preposition} {boat_name}!"
            text = ("It needs a new owner, go get one!")
        elif in_boat:
            title = "You are already in a boat!"
            text = "Now get sailing!"
        elif boat_placed:
            title = "Your boat has already been placed!"
            text = "Go and find it, I bet it misses you."
        else:
            await modify.place_boat(ctx.author.id, coords, clan,
                                    boat_exists)
            title = f"Your {boat_name} was placed at {coords}"
            text = "Use it with /board!"

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @ship.command(name="info")
    async def infomation(self, ctx):
        """See your boat's stats!"""

        coords, level, name = await query.boat(
            ctx.author.id, "coords", "level", "name")

        boat = boats.get(name)

        title = f"**Your {boat}**"
        text = f"**Boat located at:**: {coords[0]} {coords[1]}\n**Level**: {level}\n"

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @commands.command(name="strip")
    async def strip(self, ctx):
        """
        Strip your boat into spare parts!

        This cannot be undone!
        """

        name = await query.boat(ctx.author.id, "name")

        title = f"**Are you sure you want to strip your {name}?**"
        text = "You cannot bring it back!"

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
                'reaction_add',
                timeout=CONFIRM_REACTION_TIMEOUT,
                check=checker)

        except asyncio.TimeoutError:
            return
        else:
            if str(reaction.emoji) == Emoji.confirm:
                title = "**Your boat was stripped!**"
                text = "Get another boat with a sailor!"
                await modify.destroy_boat(ctx.author.id)

                embed = await create_embed(ctx, title, text)
                await response.edit(embed=embed)

    @commands.command(name="board")
    async def board(self, ctx):
        """
        Get on your boat!

        Lets you travel the sea in your boat.
        """
        await query.boat(ctx.author.id)

        boat_coords = await query.boat(ctx.author.id, "coords")
        coords, in_boat = await query.user(ctx.author.id, "coords", "in_boat")
        if boat_coords != coords:
            title = "You do not have a boat here!"
            text = "Try and find a boat at a trader!"

        elif in_boat:
            title = "You are already in your boat!"
            text = "Now get sailing!"

        else:
            await modify.set_boat(ctx.author.id, True)
            title = "You have got on your boat!"
            text = "You can now travel on water!"
        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @ship.command(name="unboard")
    async def unboard(self, ctx):
        """
        Lets you leave your boat and travel on land!

        Your boat stays where you leave it, so be careful!
        """

        in_boat, coords = await query.user(ctx.author.id, "in_boat", "coords")
        pixel = await query.pixel(coords)

        if not in_boat:
            title = "You are not on a boat silly!"
            text = "Go to a town and try and find one!"

        elif ctx.author.id in WALKING:
            title = "You are currently moving!"
            text = "Do /stop to get of!"

        elif pixel != SWAMP_COLOUR:
            title = "You cannot get off in the middle of the sea!"
            text = "Get closer to land!"

        else:
            await modify.set_boat(ctx.author.id, False)
            title = "You left your boat!"
            text = "It will stay here until you set sail again!"
        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @commands.command(name="fish")
    async def fish(self, ctx, rod_name="Rod"):
        """
        Try and fish for a fish! (duh)

        Can only be used when on a boat
        """
        rod_name = rod_name.capitalize()
        preposition = rod_name[0].lower() in "aeiou" and "an" or "a"

        inv, in_boat = await query.user(ctx.author.id, "inventory", "in_boat")
        rod = utility_return(items, key=rod_name)

        if not rod:
            title = f"{rod_name} is an invalid fishing rod!"
            text = "Good attempt, needs more rod!"

        elif not in_boat:
            title = "You cannot fish without being in a boat!"
            text = "Get a boat with /trade!"

        elif ctx.author.id in WALKING:
            title = "You can't sail and fish at the same time!"
            text = "What are you? Superman?"

        elif rod.name not in inv:
            title = f"You do not own {preposition} {rod}!"
            text = "You better go and find one!"

        else:
            fish = await self.get_fish()

            if fish is None:
                title = "You did not catch a fish!"
                text = "Maybe get some lessons..."

            else:
                title = f"You caught a {fish}!"
                text = "Fish for another with `/fish`!"
                await modify.inv(ctx.author.id, fish.name, 1)

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    async def get_fish(self):
        """
        Finds a fish by random chance
        """

        for fish in utility_search(creatures, key="fish"):
            chance = randint(1, fish.rarity)
            if chance == 1:
                return fish

        return None


def setup(bot):
    bot.add_cog(BoatCommands(bot))
