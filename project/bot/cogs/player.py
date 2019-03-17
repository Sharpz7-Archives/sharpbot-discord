from random import randint

import discord
from discord.errors import Forbidden
from discord.ext import commands

from bot.classes import craft_recipes, creatures, plants
from bot.constants import ALPHA_TO_NUM, NUM_TO_ALPHA, OFFICIAL_SERVERS, WALKING
from bot.database import modify, query
from bot.utils import at_town, create_embed, find_trade, utility_search


class PlayerCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['begin'])
    @commands.guild_only()
    async def start(self, ctx):
        """Start your journey in Sharpe!"""

        user = await query.user(ctx.author.id)

        if user is None:
            # Initialise the user in the database and get some initial info.
            await query.start(ctx.author, self.bot.width, self.bot.height)
            clan, coords = await query.user(ctx.author.id, "clan", "coords")

            title = f"You are in clan {clan} and have spawned at {coords}"
            text = "Do `/help` to see a list of commands!!!"

            # Add a clan role if the user is in one of our servers.
            if ctx.guild.id in OFFICIAL_SERVERS:
                role = discord.utils.get(ctx.guild.roles, name=clan)
                try:
                    await ctx.author.add_roles(role)
                except Forbidden:
                    pass
        else:
            title = "You have already started!"
            text = ""

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @commands.command(aliases=['inventory', 'items', 'collection'])
    async def inv(self, ctx):
        """Shows you your inventory!
        You can use items here at shops in towns
        /help towns"""

        # Get the user's information from the database and format it nicely.
        user_inv = await query.user_parse(ctx.author.id)
        pet_inv = await query.pet_parse(ctx.author.id)

        user_inv = '\n'.join(user_inv)
        pet_inv = '\n'.join(pet_inv)
        text = (f"__**Inventory**__\n\n"
                f"{user_inv}\n\n"
                f"__**Pet**__\n\n"
                f"{pet_inv}\n\n")

        title = '**Your Inventory:**'
        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @commands.command(name="trade")
    async def trade(self, ctx, letter=None, amount: int = 1):
        """Lets you trade materials at towns.

        /t info shows you the trades available
        /trade [trade letter] [number of trades], e.g
        /trade A 5 - will do "trade A" 5 times
        (YOU MUST BE IN A TOWN TO TRADE. /help towns)
        """

        amount = abs(amount)
        if ctx.author.id in WALKING:
            return await ctx.send("Sorry, you are moving right now!")

        coords, inv = await query.user(ctx.author.id, "coords", "inventory")
        town = await at_town(coords)

        if letter is not None:
            number = ALPHA_TO_NUM[letter.upper()]
            trade = await find_trade(town.name, number)

            # Makes sure you have all the trade items in your inv
            for item, price in trade.selling:
                if inv.get(item.name, 0) < price * amount:
                    title = f"You don't have enough {item}!"
                    text = "To trade again, do /trade!"
                    embed = await create_embed(ctx, title, text)
                    await ctx.send(embed=embed)
                    return

            buying, _ = trade.buying

            if buying.single and amount > 1:
                title = f"You can only trade one {buying}!"

            elif buying.single and inv.get(buying.name, 0) > 0:
                title = f"You already have a {buying}!"

            else:
                title = await modify.trade(ctx.author.id, trade, amount)

            text = "To trade again, do /trade!"
            embed = await create_embed(ctx, title, text)
            await ctx.send(embed=embed)

        else:
            title = "**TOWN TRADING**"
            text = (
                "/town info shows you the trades available\n"
                "/trade [trade number] [number of trades], e.g\n\n"
                "`/trade 1 5` will do the first trade 5 times\n\n"
                "```YOU MUST BE IN A TOWN TO TRADE. /help towns```")

            embed = await create_embed(ctx, title, text)
            await ctx.send(embed=embed)

    @commands.command(name="craft")
    async def craft(self, ctx, letter=None, amount: int = 1):
        """Lets you trade materials at towns.

        /craft shows you the trades available
        /craft [number] [number of time], e.g
        /craft 1 5 - will do the first craft 5 times
        """

        amount = abs(amount)

        inv = await query.user(ctx.author.id, "inventory")
        if letter is not None:
            letter = letter.upper()
            index = ALPHA_TO_NUM[letter] - 1
            recipe = craft_recipes[index]

            # Makes sure you have all the trade items in your inv
            for item, price in recipe.selling:
                if inv.get(item.name, 0) < price * amount:
                    title = f"You don't have enough {item}!"
                    text = "To craft again, do /craft!"
                    embed = await create_embed(ctx, title, text)
                    await ctx.send(embed=embed)
                    return

            buying, _ = recipe.buying
            if not any(item.single for item, _ in recipe.selling):

                if buying.single and amount > 1:
                    title = f"You can only trade one {buying}!"

                elif buying.single and buying.name in inv:
                    title = f"You already have a {buying}!"

                else:
                    title = await modify.trade(ctx.author.id, recipe, amount)

            else:
                title = await modify.trade(ctx.author.id, recipe, amount)

            text = "To craft again, do /t trade!"
            embed = await create_embed(ctx, title, text)
            await ctx.send(embed=embed)

        else:
            # Displays all of todays recipes
            title = "**TODAY'S RECIPES**"
            text = await self.display_recipes()

            embed = await create_embed(ctx, title, text)
            await ctx.send(embed=embed)

    async def display_recipes(self):
        display = []
        for counter, trade_desc in enumerate(craft_recipes):
            letter = NUM_TO_ALPHA[counter]
            display.append(f"**Recipe {letter} -** {trade_desc}")

        return "\n\n".join(display)

    @commands.command(aliases=["look"])
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def find(self, ctx):
        """Find your own pets!
        Has a 2 min cooldown!"""

        # Set the default embed content.
        title = "You found nothing!"
        text = ("Try again with /find\n"
                "*REMEMBER: There is a 2 min cooldown on this!*")

        in_boat, pet, inv = await query.user(
            ctx.author.id, "in_boat", "pet", "inventory")

        if in_boat:
            return await ctx.send("You can not look for stuff in the sea!")

        for item in utility_search(creatures, plants, key="Find"):
            # Deal with pets, animals and non-single items
            if randint(1, item.rarity + 1) == 1:
                if item.name == pet["name"]:
                    await modify.pet_lvl(ctx.author.id)
                    title = "You found a magic spell!"
                    text = f"It leveled up your {item}"

                elif item.single and inv.get(item.name, 0) > 0:
                    await modify.inv(ctx.author.id, item.name, 1)
                    title = "You found a magic spell!"
                    text = f"It leveled up your {item}"

                else:
                    await modify.inv(ctx.author.id, item.name, 1)
                    title = f"You found a {item}"
                    text = "Use this command again with /find!"

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(PlayerCommands(bot))
