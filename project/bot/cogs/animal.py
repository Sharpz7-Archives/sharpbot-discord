import math
import random

from discord.ext import commands

from bot.classes import plants, creatures
from bot.constants import MAX_FEED_AMOUNT
from bot.database import modify, query
from bot.utils import create_embed, utility_return


class AnimalCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pet")
    async def pet(self, ctx, name):
        """
        Choose one of your animals to be your pet!
        Your pet can do jobs for you, and fight with you!
        """

        name = name.capitalize()
        inv, pet = await query.user(ctx.author.id, "inventory", "pet")

        if name not in inv:
            title = "You don't have this animal!"  # Default title text.
            text = "Try doing /find!"

        else:
            if pet:
                await modify.inv(ctx.author.id, pet['name'], pet['lvl'])
            title = f"You now have a pet {name}!"
            text = "You can feed it here!"
            await modify.pet(ctx.author.id, name, inv[name])
            await modify.inv(ctx.author.id, name, -(inv[name]))

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @commands.command(name="feed")
    async def feed(self, ctx, item, amount: int = 1):
        """
        Feed your pet to revive it or have a chance to level it up!
        Different plants have different chances of doing each
        """

        item = item.capitalize()
        amount = min(abs(amount), MAX_FEED_AMOUNT)  # Cap the amount to feed.

        inv, pet = await query.user(ctx.author.id, "inventory", "pet")
        inv_amount = inv[item]

        food = utility_return(creatures, plants, key=item)

        if item not in inv or inv_amount <= 0:
            title = f"Sorry, you do not have a {item}"
            text = f"Do /find to get more items!"

        elif amount > inv_amount:
            title = f"You do not have {amount} {item}'s!"
            text = f"Do /find to get more items!"

        elif not food:
            title = f"You can only feed pets plants!"
            text = f"Do /find to get more plants!"

        elif pet == "None":
            title = f"You do not have a pet to use this command!"
            text = f"Try and get a pet by finding it with /find!"

        else:
            # Calculate the chance of having the pet level up
            lvl_chance = 9 - int(math.log(amount * 10) + food.level_up_boost)
            if lvl_chance <= 1:
                lvl_chance = 2

            # See if their pet levels up! How exciting.
            if 1 == random.randint(1, lvl_chance):
                title = f"Your pet took {food}'s' and your pet leveled to lvl {pet['lvl']+ 1}"

                await modify.pet_lvl(ctx.author.id)

            # Aww damn, the pet didn't level up. That's a shame.
            else:
                title = f"Your pet took a {food}, but nothing happend!"

            text = f"Do /find to get more plants!"
            await modify.inv(ctx.author.id, item, -amount)

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(AnimalCommands(bot))
