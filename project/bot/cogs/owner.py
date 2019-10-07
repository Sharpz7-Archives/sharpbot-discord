import yaml
from pprint import pformat

import discord
from discord.ext import commands

from bot.constants import YML_FILE, COGS_FILE
from bot.database import modify, query
from bot.utils import create_embed, is_owner, get_coords


class OwnerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load(self, file):
        """Simply load the JSON file"""

        with open(file, "r") as ymlfile:
            return yaml.safe_load(ymlfile)

    def write(self, data, file):
        """Write some data to the JSON file"""

        with open(file, "w") as ymlfile:
            yaml.dump(data, ymlfile, default_flow_style=False)

    @commands.command(name="load", hidden=True)
    @commands.check(is_owner)
    async def loadc(self, ctx, name):
        """Load a module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.load_extension(f"bot.cogs.{name}")
            data = self.load(COGS_FILE)
            data["cogs"].append(f"bot.cogs.{name}")
            self.write(data, COGS_FILE)

        except Exception as e:
            await ctx.send(f"**`ERROR:`** {type(e).__name__} - {e}")
        else:
            await ctx.send("**`SUCCESS`**")

    @commands.command(name="unload", hidden=True)
    @commands.check(is_owner)
    async def unloadc(self, ctx, name):
        """Unload a module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.unload_extension(f"bot.cogs.{name}")

            data = self.load(COGS_FILE)
            data["cogs"].remove(f"bot.cogs.{name}")
            self.write(data, COGS_FILE)

        except Exception as e:
            await ctx.send(f"**`ERROR:`** {type(e).__name__} - {e}")
        else:
            await ctx.send("**`SUCCESS`**")

    @commands.command(name="reload", aliases=["r"], hidden=True)
    @commands.check(is_owner)
    async def reloadc(self, ctx, name):
        """Reload a module.
        Remember to use dot path. e.g: cogs.owner"""

        try:
            self.bot.unload_extension(f"bot.cogs.{name}")
            self.bot.load_extension(f"bot.cogs.{name}")
        except Exception as e:
            await ctx.send(f"**`ERROR:`** {type(e).__name__} - {e}")
        else:
            await ctx.send("**`SUCCESS`**")

    @commands.command(name="insta", hidden=True)
    @commands.check(is_owner)
    async def ins(self, ctx, opt, arg, arg2=None, user: discord.Member = None):
        """Instantly gives yourself resources"""

        if user is None:
            user = ctx.author

        await query.user(ctx.author.id)

        # Teleportation, spooky!
        if opt == "move":
            coords = await query.user(ctx.author.id, "coords")
            x, y = await get_coords(ctx, arg, arg2, coords)
            await modify.coord(user.id, [x, y])
            await ctx.send(content="`Done!`")

        # Conjure materials with magic!
        elif opt == "inv":
            await modify.inv(user.id, arg2.capitalize(), int(arg))
            await ctx.send(content="`Done!`")

    @commands.command(hidden=True)
    @commands.check(is_owner)
    async def create(self, ctx, member: discord.Member = None):
        """Creates a user"""

        if member is None:
            member = ctx.author
        await query.start(member, self.bot.width, self.bot.height)
        await ctx.send(content="`Done!`")

    @commands.command(hidden=True)
    @commands.check(is_owner)
    async def purge(self, ctx, member: discord.Member = None):
        """Removes a user"""

        if member is None:
            member = ctx.author
        await modify.purge(member.id)
        await ctx.send(content="`Done!`")

    @commands.command(name="show", hidden=True)
    @commands.check(is_owner)
    async def show(self, ctx, member: discord.Member = None):
        """Show all the data about a user."""

        if member is None:
            member = ctx.author
        user_data = await query.user(member.id)
        building_data = await query.building(member.id)
        boat_data = await query.boat(member.id)

        title = f"{member}'s' data:"
        text = (
            f"{pformat(user_data)}\n\n"
            f"{pformat(building_data)}\n\n"
            f"{pformat(boat_data)}\n\n"
        )
        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.check(is_owner)
    async def cia(self, ctx, user: discord.User = None):
        """Gather information about a specific user"""

        # Extract the ID from a mention if necessary.
        if user is None:
            user = ctx.author

        data = await self.bot.get_user_info(user.id)
        title = f"**All data on user {data.name}**"
        text = (
            f"**Full Name:** {data}\n"
            f"**Joined:** {str(data.created_at)[:-10]}\n"
            f"**Avatar Url:** {data.avatar_url}\n"
            f"**ID:** {data.id}\n"
            f"**Original Discord Avatar color:** {data.default_avatar.name}\n"
        )
        embed = await create_embed(ctx, title, text)
        embed.set_thumbnail(url=data.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.check(is_owner)
    async def merge(self, ctx, key, value):
        """
        Creates a new category in people's data

        FOR DEV USE ONLY
        """

        await modify.merge(key, value)
        await ctx.send("`DONE`")

    @commands.command(hidden=True)
    @commands.check(is_owner)
    async def delete(self, ctx, key):
        """
        Deletes a category in people's data

        FOR DEV USE ONLY
        """

        await modify.delete(key)
        await ctx.send("`DONE`")

    @commands.command(hidden=True)
    @commands.check(is_owner)
    async def restart(self, ctx):
        """
        Reloads all of the bot's code!

        Only for Production setups!!
        """

        data = self.load(YML_FILE)
        data["startup_channel"] = ctx.channel.id
        self.write(data, YML_FILE)
        await ctx.send("`restarting...`")
        exit(0)

    @commands.command(name="test", hidden=True)
    @commands.check(is_owner)
    async def test(self, ctx):
        """
        Dummy function that can be utilised for testing purposes
        """
        pass


def setup(bot):
    bot.add_cog(OwnerCommands(bot))
