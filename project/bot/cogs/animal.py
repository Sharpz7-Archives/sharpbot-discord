import random

from discord.ext import commands

from bot.classes import plants, creatures, petlevelrate
from bot.constants import MAX_FEED_AMOUNT
from bot.database import modify, query
from bot.utils import create_embed, utility_return


class AnimalCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="pet")
    async def pet(self, ctx):
        """
        All commands related to pets!
        Pets will fight in battle for you, find other players, and some have extra features!

        /pet create - choose one of your pets
        /pet feed - Feed your pet giving it a chance to level up!
        /pet scavenge - Find a player in the world!
        """

        # If the user just invokes `/pet` on it's own...
        if ctx.invoked_subcommand is None:
            title = "PET COMMAND HELP"
            text = (
                "```"
                "/pet create - choose one of your pets\n"
                "/pet feed - Feed your pet giving it a chance to level up!\n"
                "/pet scavenge - Find a player in the world!```\n")

            embed = await create_embed(ctx, title, text)
            await ctx.send(embed=embed)

    @pet.command(name="create")
    async def create(self, ctx, name):
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

    @pet.command(name="feed")
    async def feed(self, ctx, item, amount: int = 1):
        """
        Feed your pet to revive it or have a chance to level it up!
        Different plants have different chances of doing each
        """

        item = item.capitalize()
        amount = min(abs(amount), MAX_FEED_AMOUNT)  # Cap the amount to feed.

        inv, pet = await query.user(ctx.author.id, "inventory", "pet")
        inv_amount = inv.get(item, 0)

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

        elif not pet:
            title = f"You do not have a pet to use this command!"
            text = f"Try and get a pet by finding it with /find!"

        else:
            # Calculate the chance of having the pet level up
            lvl_chance = petlevelrate.at(pet["lvl"]) + food.pet_multiplyer

            # See if their pet levels up! How exciting.
            for _ in range(amount):
                if 1 == random.randint(1, lvl_chance):
                    title = f"Your pet took {food}'s' and your pet leveled to lvl {pet['lvl']+ 1}"
                    await modify.pet_lvl(ctx.author.id)
                    break

            # Aww damn, the pet didn't level up. That's a shame.
            else:
                title = f"Your pet took a {food}, but nothing happend!"

            text = f"Do /find to get more plants!"
            await modify.inv(ctx.author.id, item, -amount)

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @pet.command(name="scavenge")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def scavenge(self, ctx):
        """
        Send your pet on a mission to find a player!

        This command as a 2 hr cooldown
        """

        pet = await query.user(ctx.author.id, "pet")
        found = await query.pet_ranuser(pet, ctx.author.id)

        if not pet:
            title = "You do not have a pet!"
            text = "Try getting one with /find!"

        elif not found:
            title = "Your pet did not find anything!"
            text = "Better luck next time mate!"

        else:
            title = f"Your pet found a player! at `{found.get('coords')}`"
            text = f"You should go and get him with `/move` and `/f duel`!"

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(AnimalCommands(bot))
