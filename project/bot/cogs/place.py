from discord.ext import commands

from bot.classes import Place
from bot.utils import at_town, create_embed
from bot.database import query
from bot.constants import NUM_TO_ALPHA


class PlaceCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='town', aliases=['towns', "t", "places"])
    async def places(self, ctx):
        """
        All the commands for towns and places!

        /town find - Lists and the towns
        /town info - Tells you about the town you are currently in
        """

        if ctx.invoked_subcommand is None:
            title = 'PLACE HELP'
            text = (
                "```"
                "All the commands for towns and places!\n"
                "/town find - Lists and the towns\n"
                "/town info - Tells you about the town you are currently in\n"
                "```"
            )
            embed = await create_embed(ctx, title, text)
            await ctx.send(embed=embed)

    @places.command(name='list', aliases=['find'])
    async def find(self, ctx):
        """Shows you all the places you can travel to.
        Copy and paste one of these locations and do:
        /move `location`

        You can trade at towns, /help town"""

        # Construct a list of all named locations.
        places = []
        for place in Place.lookup.values():
            places.append(f"{place.name} - {place.type} - {place.coords}")

        title = 'Current Places:'
        text = "\n".join(places)
        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @places.command(aliases=["i"])
    async def info(self, ctx):
        coords = await query.user(ctx.author.id, "coords")
        town = await at_town(coords)
        text = "To go to a town, try /help towns"
        title = f"Currently in {town.name} {coords}"

        # If there are trades going on here, list them.
        if hasattr(town, "trades"):
            if town.trades is not None:
                # Create a list of active trades.
                trades = []
                for counter, item in enumerate(town.trades):
                    letter = NUM_TO_ALPHA[counter]
                    trades.append(f"**Trade {letter}** - {item.name}")

                text = ",\n".join(trades)
                text = (f"**You can trade with the {town.trade_name}**:\n\n"
                        f"{text}")

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(PlaceCommands(bot))
