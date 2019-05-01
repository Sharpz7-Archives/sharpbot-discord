import asyncio
from random import randint

from discord.errors import Forbidden
from discord.ext import commands

from bot.classes import materials
from bot.constants import EXHAUST_MINE_CHANCE, MAX_MINE_AMOUNT, MINE_REACTION_TIMEOUT, WALKING, Emoji
from bot.database import modify, query
from bot.utils import create_embed, utility_search


class MineCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.mined = []

    @commands.command(name='mine')
    async def mine(self, ctx):
        """Looks for ores to build and trade with!"""
        await self.gather_api(ctx, Emoji.pickaxe, "mineable")

    @commands.command(name='chop')
    async def chop(self, ctx):
        """Find wood and other things to get started!"""
        await self.gather_api(ctx, Emoji.axe, "chopable")

    async def gather_api(self, ctx, emoji, mat_type):
        """Collect resources to build and trade with!"""

        if ctx.author.id in WALKING:
            return await ctx.send("Sorry, you are moving right now!")

        embed = await self.do_gather(ctx, mat_type)
        response = await ctx.send(embed=embed)
        await response.add_reaction(emoji)

        def checker(reaction, user):
            correct_msg = reaction.message.id == response.id
            correct_user = user == ctx.author

            return correct_msg and correct_user

        async def re_run():
            try:
                reaction, _ = await self.bot.wait_for(
                    'reaction_add',
                    timeout=MINE_REACTION_TIMEOUT,
                    check=checker)

            # If the user doesn't mine for a while, give up.
            except asyncio.TimeoutError:
                return

            else:
                if str(reaction.emoji) == emoji:
                    embed = await self.do_gather(ctx, mat_type)
                    try:
                        await response.remove_reaction(emoji, ctx.author)
                    # The bot may not have permission to remove the reaction.
                    except Forbidden:
                        pass  # Oh well.

                await response.edit(embed=embed)
                await re_run()

        await re_run()

    async def do_gather(self, ctx, mat_type):
        """Gather a material and construct an embed based on it."""

        coords = await query.user(ctx.author.id, "coords")

        # If the mine is or has become empty, stop here.
        if randint(0, EXHAUST_MINE_CHANCE) == 0 or coords in self.mined:
            title = 'There are no more materials here!'
            text = "Try /move [direction] !"
            if coords not in self.mined:
                self.mined.append(coords)
        else:
            found = "nothing!"
            for ore in utility_search(materials, key=mat_type):
                if randint(0, ore.rarity) == 0:
                    # Calculate the yield based on rarity.
                    amount = randint(1, MAX_MINE_AMOUNT) - ore.rarity
                    if amount < 1:
                        amount = 1

                    # Add the materials to the user's inventory.
                    found = f"{amount} {ore}"
                    await modify.inv(ctx.author.id, ore.name, amount)
                    break

            title = f'Looked for materials and found {found}'
            text = ("Find more materials with /mine! or /chop!\n"
                    "*Click the reaction button below to mine again!*")

        embed = await create_embed(ctx, title, text)
        return embed


def setup(bot):
    bot.add_cog(MineCommands(bot))
