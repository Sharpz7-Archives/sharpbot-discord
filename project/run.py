import yaml
import os
import sys
import traceback
from rethinkdb.errors import ReqlNonExistenceError
from datetime import datetime

import discord
from bot_testing import manage
from discord.errors import Forbidden
from discord.ext import commands

from bot.constants import YML_FILE, COGS_FILE, OFFICIAL_SERVERS, PREFIXES
from bot.database import query


# If your running with CICD don't run the bot.
if os.environ.get("CICD", "FALSE") == "TRUE":
    manage.run_tests()
    sys.exit()


def get_prefix(bot, message):
    """Gets the prefixes"""
    return commands.when_mentioned_or(*PREFIXES)(bot, message)


bot = commands.Bot(command_prefix=get_prefix, description="SharpBot")

with open(COGS_FILE, "r") as ymlfile:
    cogs_data = yaml.safe_load(ymlfile)

initial_extensions = cogs_data.get("cogs")

# Load all extenstions in the cogs JSON file.
if __name__ == "__main__":
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
            print(f"Loaded {extension}...")
        except Exception:
            print(f"Failed to load extension {extension}.", file=sys.stderr)

            traceback.print_exc()


@bot.event
async def on_ready():
    print(
        f"\n\n"
        f"Logged in as: {bot.user.name} - {bot.user.id}\n"
        f"Discord Version: 1.0.0a\n"
        f"Sharpbot Version: 1.0.1a\n"
    )

    bot.appinfo = await bot.application_info()

    # Creates yml_file if its not there
    try:
        with open(YML_FILE, "x") as file:
            data = {"startup_channel": bot.appinfo.owner.id}
            yaml.dump(data, file, default_flow_style=False)

    except FileExistsError:
        pass

    # Change the bots status
    await bot.change_presence(activity=discord.Game(name="/start -- COME PLAY!"))

    # Sends a message to you where you typed /restart...
    with open(YML_FILE, "r") as ymlFile:
        channel_data = yaml.safe_load(ymlFile)

    startup_channel = channel_data.get("startup_channel")
    channel = bot.get_channel(startup_channel)

    # Or as a direct message...
    if channel is None:
        channel = bot.appinfo.owner

    channel_data["startup_channel"] = bot.appinfo.owner.id
    with open(YML_FILE, "w") as yml_file:
        yaml.dump(channel_data, yml_file, default_flow_style=False)

    text = f"```" f"Successfully Started\n" f"Time: {datetime.now()}" f"```"
    await channel.send(text)
    print("Successfully logged in...")


@bot.event
async def on_member_join(member):
    if member.guild.id in OFFICIAL_SERVERS:
        try:
            clan = await query.user(member.id, "clan")
            role = discord.utils.get(member.guild.roles, name=clan)
            await member.add_roles(role)
        except Forbidden:
            pass

        except ReqlNonExistenceError:
            pass


print("Logging in...")
bot.run(os.environ["SECRET"], bot=True, reconnect=True)
