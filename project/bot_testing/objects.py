import asyncio
import inspect
import random as ran
import traceback

import yaml
from PIL import Image, ImageDraw, ImageFont

from bot.classes import Place
from bot.cogs import (
    animal,
    boat,
    build,
    default,
    fight,
    gather,
    move,
    owner,
    place,
    player,
    error_handler,
)
from bot.constants import (
    FONT_FILE,
    MAP_FILE,
    SHORE,
    SHORE_COLOUR,
    TEMPLATE_FILE,
    ARTIFACT_FOLDER,
)
from bot.errors import TestFailError
from bot.utils import rgb_data


class Author:
    """Copy of the discord `author` object"""

    def __init__(self):
        self.id = ran.randint(1, 1000)

    def __repr__(self):
        return f"Test user {self.id}"

    async def add_roles(self, role):
        """Placeholder function"""
        pass


class Roles:
    """Roles from discord context object"""

    def __init__(self, name):
        self.name = name


class Guild:
    """Guild for context"""

    def __init__(self):
        self.id = 101
        self.roles = [Roles("Announcement")]


class Bot:
    """Copy of the discord `bot` object"""

    def __init__(self):
        # Adds place names
        with Image.open(TEMPLATE_FILE) as im:
            draw = ImageDraw.Draw(im)

            font = ImageFont.truetype(font=FONT_FILE, size=30)
            for town in Place.lookup.values():
                x1, y1 = town.coords

                draw.text((x1, y1), town.name, font=font, fill="white")

            im.save(MAP_FILE)

            #  Sets world border
            self.width, self.height = im.size
            # Ensures pixel is in image at all times
            self.width -= 1
            self.height -= 1

        # Creates shore points
        for y in range(im.height):
            for x in range(im.width):
                if rgb_data.shore((x, y)) == SHORE_COLOUR:
                    SHORE.append([x, y])

        self.loop = asyncio.get_event_loop()
        self.latency = 0
        self.current_user = None

    def get_user(self, user):
        """Returns the context that was sent in"""
        return bot.current_test


bot = Bot()


class Command:
    def __init__(self):
        self.name = None

    def __repr__(self):
        return self.name


class Context:
    """Copy of the `ctx` discord object"""

    def __init__(self):
        self.author = Author()
        self.guild = Guild()
        self.command = Command()
        self.name = None
        self.invoked_subcommand = None
        self.stage = "default"
        self.artifacts = {}
        self.typing = TypingManager
        bot.current_test = self

    async def send(self, content=None, embed=None, file=None):
        """Prints and logs events"""
        if embed:
            await self.log(embed.title)
            await self.log(embed.description)
        if content:
            await self.log(content)
        if file:
            await self.log(f"File was sent! ({file.filename})")

    async def log(self, message):
        """
        Logs all of a tests events

        Also checks if the command had any fail requirements
        """

        if self.stage not in self.artifacts:
            self.artifacts[self.stage] = []
        self.artifacts[self.stage].append(message)

        self.message_sent = True
        self.last_log = message

    async def check_for_message(self):
        """Checks if the command has not sent a message"""
        if not self.message_sent:
            raise TestFailError("No message was sent!")


class TypingManager:
    """Placeholder for ctx.typing()"""

    async def __aenter__(self):
        pass

    async def __aexit__(self, exc_type, exc, tb):
        pass


def cog_find(name):
    """
    All cogs that meet the requirements for testing.

    Other cogs must be tested before being added to this list.
    """

    data = {
        "animal": animal.AnimalCommands,
        "boat": boat.BoatCommands,
        "build": build.BuildingCommands,
        "default": default.DefaultCommands,
        "fight": fight.FightCommands,
        "gather": gather.MineCommands,
        "move": move.MoveCommands,
        "owner": owner.OwnerCommands,
        "place": place.PlaceCommands,
        "player": player.PlayerCommands,
    }
    return data.get(name)


class Test:
    """Holds all of a tests data and objects"""

    def __init__(self, name, commands, nopost=False):
        self.name = name
        self.commands = commands
        self.nopost = nopost
        self.artifacts = []
        self.error = None

    async def runner(self):
        """Runs all the tasks specified in the test_file"""

        self.ctx = Context()
        print(f"Context Created with id {self.ctx.author.id}...\n")

        print("Runnning commands...")

        # Runs all the commands specified
        try:
            for counter, task in enumerate(self.commands):
                self.ctx.stage = f"Stage {counter}"
                self.ctx.message_sent = False
                instance, command, *fails = task
                instance = cog_find(instance)

                if fails:
                    fails = Fail(fails, stage=self.ctx.stage)

                try:
                    func_name, *options = command.split()
                except ValueError:
                    options = None
                func, options = await self.find_func(func_name, options, instance)
                self.ctx.command.name = func.name
                if func is None:
                    raise KeyError

                if options:
                    await func.callback(instance(bot), self.ctx, *options)
                else:
                    await func.callback(instance(bot), self.ctx)
                await self.ctx.check_for_message()
                if fails:
                    fails.run_all(self.ctx.last_log)
            print("DONE!\n")

        except KeyboardInterrupt as e:
            print("Aborted. Skipping to post...")
            traceback.print_exc()
            self.error = e

        except Exception as e:
            handled = await error_handler.ErrorHandler.on_command_error(
                instance(bot), self.ctx, e
            )
            if not handled:
                print("\n====================")
                print(
                    f"ERROR @ {self.ctx.stage} of {self.name}! (Command: {self.ctx.command.name})\n"
                )
                print(f"Error: {e}")
                print("====================\n\n")
                print("Skipping to post.\n")
                self.error = e

        if self.error:
            self.ctx.stage = "Error"
            await self.ctx.log(
                f"{traceback.format_tb(self.error.__traceback__)}"
            )

        # Removes and logs the players data
        # This will be stored in its artifact
        if not self.nopost:
            print("Removing data-table...")
            self.ctx.stage = "Post"
            owner = cog_find("owner")
            await owner.show.callback(instance(bot), self.ctx)
            await owner.purge.callback(instance(bot), self.ctx)
            print("DONE!\n")

        print("Dumping artifacts...")
        with open(f"{ARTIFACT_FOLDER}/{self.name}.yml", "w+") as ymlFile:
            yaml.dump(self.ctx.artifacts, ymlFile, default_flow_style=False)

        if self.error:
            print("A test failed. Exiting...")
            exit(1)

    async def find_func(self, name, options, instance):
        """
        Finds the function from the name given.

        Also detects 1 level of subcommands and changes the command accordingly
        """

        if name.startswith("/"):
            name = name[1:]
        func = getattr(instance, name, None)

        # If the func name is not the name of the command...
        if not func:
            # Checks if any of the aliases match `name`
            for method in instance.__dict__.values():
                aliases = getattr(method, "aliases", None)
                func_name = getattr(method, "name", None)

                aliases_match = aliases and name in aliases
                name_match = func_name == name
                if name_match or aliases_match:
                    func = method

        group_command = getattr(func, "all_commands", None)
        # If the command is a group_command...
        if group_command and options:
            self.ctx.invoked_subcommand = True
            if options[0] in group_command:
                func, *options = options
                func = group_command[func]
                options = await self.convert_options(options, func)
                return func, options

        options = await self.convert_options(options, func)
        return func, options

    async def convert_options(self, options, func):
        """
        Makes sure all args are converted using simple discord conversions.
        Only basic python classes are supported
        """

        for counter, option in enumerate(options):
            params = list(func.clean_params.values())
            if len(params) > 2:
                instance = params[counter + 1].annotation
                if instance != inspect._empty:
                    options[counter] = instance(option)

        return options


class File:
    """
    Holds all the data on a file

    Allows for multiple tests in the same file.
    """

    def __init__(self):
        self.all_tests = []

    def create_test(self, name, commands, nopost=False):
        """Creates a test for the command"""
        test = Test(name, commands, nopost)
        self.all_tests.append(test)


class Fail:
    """
    Defines what should be a fail in a test.

    Also includes all possible fail options.
    """

    def __init__(self, fails, stage=None):
        self.all_fails = []
        if fails:
            for fail in fails:
                instance, *args = fail
                child = self.find_child(instance)
                self.all_fails.append(child(*args).run)

    def run_all(self, message):
        """
        Runs all fails defined in the instance.

        Look at subclasses of Fail for examples.
        """
        for method in self.all_fails:
            method(message)

    def find_child(self, name):
        """
        Finds the childclass of this method
        """
        for child in Fail.__subclasses__():
            if child.__name__.lower() == name:
                return child


class KeyInMessage(Fail):
    def __init__(self, *keys):
        self.keys = list(keys)

    def run(self, message):
        for key in self.keys:
            if key not in message:
                raise TestFailError(f"Not all keys were found in message! ({key})")


class KeyNotInMessage(Fail):
    def __init__(self, *keys):
        self.keys = list(keys)

    def run(self, message):
        for key in self.keys:
            if key in message:
                raise TestFailError(f"A banned key was found in message! ({key})")
