import asyncio
import io

import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont

from bot.classes import Place
from bot.constants import (FONT_FILE, LAND_COLOUR, MAP_FILE, SEA_CHECKS, TEMPLATE_FILE, WALKING,
                           WATER_COLOUR, SHORE_COLOUR, SHORE)
from bot.database import modify, query
from bot.utils import at_town, create_embed, distance, linear, get_coords, rgb_data


class MoveCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['where', "m"])
    async def map(self, ctx):
        """Open the map view, see where you are.
        Shows you your current coordinates and the whole map"""

        if ctx.author.id in WALKING:
            coords, line = await WALKING[ctx.author.id].where()
            current_pos = (coords, line)
            time = WALKING[ctx.author.id].time // 60
            time_text = f"**Time until destination: {time} mins**\n\n"

        else:
            coords = await query.user(ctx.author.id, "coords")
            current_pos = (coords,)
            time_text = ""

        async with ctx.typing():
            # Run the map creation function in a way that isn't blocking.
            output = await self.bot.loop.run_in_executor(None, self.create_map, *current_pos)

        town = await at_town(coords)

        # Create an embed for the user telling them where they are.
        file = discord.File(output, filename="Map.png")
        title = f"**You are currently in {town.name} {coords}**"
        text = f"{time_text}Move with /move ! (`/help move`)"

        embed = await create_embed(ctx, title, text)
        await ctx.send(file=file, embed=embed)

    @commands.command(aliases=['teleport', 'tele', 'tp'])
    async def move(self, ctx, arg1, arg2=None):
        """Move across the map.
        There a lots of ways to use this command: e.g

        /move 400 400 - Move by coordinate
        /move saint python - Move by location
        /move left/up/right/down - Move by direction.
        /move shore - Takes you to the nearst shoreline

        For more info on locations do /help places"""

        if ctx.author.id in WALKING:
            await ctx.send("Sorry, you are moving right now!")
            return

        coords, in_boat = await query.user(ctx.author.id, "coords", "in_boat")

        # Chooses coords based of user choices.
        x, y = await get_coords(ctx, arg1, arg2, coords)

        chosen = [x, y]
        if coords == chosen:
            await ctx.send(f"You cant move to where you are! `{coords}`")
            return

        all_coords = coords + chosen
        dist = await distance(all_coords)

        # Make some checks and send an error message if necessary.
        boundary_msg = await self.border(chosen)
        if boundary_msg is not None:
            return await ctx.send(boundary_msg)

        water_msg = await self.all_pixel(dist, all_coords)
        if water_msg is not None and not in_boat:
            return await ctx.send(water_msg)

        land_msg = await self.all_pixel(dist, all_coords, color=LAND_COLOUR)
        if land_msg is not None and in_boat:
            return await ctx.send(land_msg)

        # Create an informational embed for the user.
        time = await self.do_move(ctx, all_coords, in_boat)
        title = f"Moving to {chosen}."
        text = f"Distance - {dist} miles Time - {time}"
        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @commands.command(aliases=['pause'])
    async def stop(self, ctx):
        """Stop yourself from moving."""

        if ctx.author.id in WALKING:
            WALKING[ctx.author.id].end = True
            title = "You have stopped moving!"
        else:
            title = "You are not moving right now!"

        text = "Move again with /move! (`/help move`)"
        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    def create_map(self, coords, line=None):
        """
        Generate a map given the user's current coordinates
        and, optionally, the point they are moving towards.
        """

        with Image.open(MAP_FILE) as im:
            x, y = coords
            draw = ImageDraw.Draw(im)

            if line is not None:
                place1, place2, place3, place4 = line
                draw.line(
                    [(place1, place2), (place3, place4)],
                    fill="white",
                    width=3)

            # Draw a little orange marker at the user's position.
            # A "you are here" sort of label for this is added below.
            draw.rectangle(
                [(x - 3), (y - 3), (x + 3), (y + 3)],
                fill="red",
                outline="orange")

            # Position of the label relative to the marker itself.
            label_y = 10
            label_x = 0

            # Make sure the marker label doesn't go over the edge of the map.
            if y > self.bot.height - (self.bot.height * 0.07):
                label_y = -30
            if x > self.bot.width - (self.bot.height * 0.1):
                label_x = 70

            # Now we can draw the label text near the marker.
            font = ImageFont.truetype(font=FONT_FILE, size=25)
            draw.text(
                (x - label_x, y + label_y),
                "Position",
                font=font,
                fill="orange")

            # Save the image in memory rather than to disk for added speed.
            output = io.BytesIO()
            im.save(output, "PNG")
            output.seek(0)
            return output

    async def border(self, coords):
        """
        Check if a pair of co-ordinates fit in the boundaries of the map.
        If the position is erroneous, a relevant error response is returned.
        """

        x, y = coords
        if x > self.bot.width or y > self.bot.height:
            return (f"You can't go further than ({self.bot.width}, {self.bot.height})!")

        elif x < 0 or y < 0:
            return ("You can't go further than (0, 0)!")
        return None

    async def all_pixel(self, dist, coords, color=WATER_COLOUR):
        """
        Checks if any of a set number of points are a certain color.
        """

        path_points = []
        dist = int(dist)
        step = dist // SEA_CHECKS

        if step <= 0:
            step = 1

        for num in range(0, dist, step):
            # Get the points to check using a linear function.
            coord = tuple(await linear(coords, num))
            path_points.append(coord)

        rgb = []
        # Get the colour of all points on the path.
        for coord in path_points:
            rgb.append(rgb_data.sea(coord))

        if color in rgb:
            return "You cannot cross over here!"

        return None

    async def do_move(self, ctx, coords, in_boat):
        """
        Move a user slowly towards a pair of coordinates (walking).
        """

        dist = await distance(coords)

        # Make the user start walking, and keep track of it.
        WALKING[ctx.author.id] = Walk(ctx, dist, coords, in_boat, self.bot)

        self.bot.loop.create_task(WALKING[ctx.author.id].time_count())

        # Calculate the amount of time they'll be walking for.
        if dist < 60:
            time = str(dist) + " seconds"
        else:
            hours = round(dist / 60, 0)
            time = str(hours) + "mins"

        return time


class Walk:

    def __init__(self, ctx, time, coords, in_boat, bot):
        self.bot = bot
        self.time = time
        self.ctx = ctx
        self.author = ctx.author.id
        self.coords = coords
        self.org_coords = [coords[0], coords[1]]
        self.final_coords = [coords[2], coords[3]]
        self.original = time
        self.move = round(self.original - self.time, 0)
        self.end = False
        self.in_boat = in_boat

    async def time_count(self):
        """
        Walk a user towards a point until they've reached their destination.
        """

        for _ in range(int(self.time) + 2):
            # Once the user has stopped moving, clean them from the list.
            if self.end:
                await self.where()
                del WALKING[self.author]
                break

            # If the user's walking time is over, set their final position.
            elif self.time <= 0:
                await modify.coord(self.author, self.final_coords)
                self.end = True

            # Wait one second, then advance the user's position.
            await asyncio.sleep(1)
            self.time -= 1
            self.move = round(self.original - self.time, 0)

    async def where(self):
        """
        Find the user's current position on their set path.
        """

        current_coords = await linear(self.coords, self.move)
        await modify.coord(self.author, current_coords)
        if self.in_boat:
            await modify.move_boat(self.author, current_coords)
        return current_coords, self.coords


def setup(bot):
    """
    Chooses shore points

    Loads and creates map.png

    Creates world border
    """

    # Adds place names
    with Image.open(TEMPLATE_FILE) as im:
        draw = ImageDraw.Draw(im)

        font = ImageFont.truetype(font=FONT_FILE, size=30)
        for place in Place.lookup.values():
            x1, y1 = place.coords

            draw.text(
                (x1, y1),
                place.name,
                font=font,
                fill="white")

        im.save(MAP_FILE)

        # Sets world border
        bot.width, bot.height = im.size
        # Ensures pixel is in image at all times
        bot.width -= 1
        bot.height -= 1

    # Creates shore points
    for y in range(im.height):
        for x in range(im.width):
            if rgb_data.shore((x, y)) == SHORE_COLOUR:
                SHORE.append([x, y])

    # Adds cog to the bot
    bot.add_cog(MoveCommands(bot))
