import traceback
import os

from discord.ext import commands

from bot.errors import BoatNotFoundError
from bot.errors import UserNotFoundError
from bot.utils import create_embed


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Command error parser."""

        # when using discord's builtin commands, "ctx.command" is not parsed
        if ctx.command is None:
            return

        name = ctx.command.name

        # get the original exception
        error = getattr(error, 'original', error)

        if isinstance(error, commands.errors.CommandNotFound):
            error_msg = error.args[0].replace("\"", "`")

            await ctx.send(f"{error_msg}. Try using `/help` to see the existing "
                           f"commands.")
            return True

        if isinstance(error, commands.errors.CommandOnCooldown):
            cooldown = round(error.retry_after)

            await ctx.send(f"`{name}` is on cooldown! You can try again in "
                           f"{cooldown}s.")
            return True

        if isinstance(error, commands.errors.MissingRequiredArgument):
            param = str(error.param).title()

            await ctx.send(f"`{param}` is missing from `{name}` - try `/help "
                           f"{name}` for more information.")
            return True

        if isinstance(error, commands.errors.BadArgument):
            await ctx.send(f"That is not how you use `{name}`. Try using "
                           f"`/help {name}` to see how to use it!")
            return True

        if isinstance(error, commands.errors.NoPrivateMessage):
            await ctx.send(f"You cannot use {name} in DMs; you must only use "
                           f"it within a server that we (you and me) are in!")
            return True

        if isinstance(error, UserNotFoundError):
            title = "You do not exist yet!"
            text = ("But we can change that. Use `/start` to create your "
                    "character.")
            embed = await create_embed(ctx, title, text)
            await ctx.send(embed=embed)
            return True

        if isinstance(error, BoatNotFoundError):
            title = "You do not have any boats!"
            text = "Go and find somewhere you can trade a boat!"
            embed = await create_embed(ctx, title, text)
            await ctx.send(embed=embed)
            return True

        message = [f"{type(error).__name__}: {error}"]
        error_tbs = traceback.format_tb(error.__traceback__) + message
        output = ("\n").join(error_tbs)
        # If Devmode is enabled
        if os.environ.get("DEVMODE", "FALSE") == "TRUE":
            await ctx.send(f"```py\n{output}\n```")
        else:
            print(output)


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
