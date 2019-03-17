import discord
from discord.ext import commands
from discord.errors import Forbidden

from bot.utils import create_embed


class DefaultCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['calculate'])
    async def calc(self, ctx, first: int, operator, second: int):
        """A simple command which does calculations.
        Examples:
        /calc 6 * 4 -- multiply
        /calc 6 + 5 -- add
        /calc 8 / 2 -- divide
        /calc 6 - 4 -- subtract"""
        answer = 0

        if operator == "/" and second == 0:
            answer = "Cannot divide by 0"
        else:
            solve = {
                "*": first * second,
                "+": first + second,
                "-": first - second,
                "/": first // second
            }

            answer = solve[operator]

        # added commas to result if answer > 1000 - 1000 becomes 1,000
        title = f"Answer = **{answer:,}**"
        text = "Do another calc with `/help calc`!"
        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @commands.command(aliases=['latency'])
    async def ping(self, ctx):
        """Get the bot's latency"""

        latency = round(self.bot.latency, 4)
        latency = latency * 1000
        title = "PONG!"
        text = f"Latency = {latency}ms"
        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @commands.command(name='announce')
    @commands.guild_only()
    async def annoucements(self, ctx):
        """Gives you the annoucement role"""

        try:
            role = discord.utils.get(ctx.guild.roles, name="Announcement")
            await ctx.author.add_roles(role)
            await ctx.send("Enabled successfully!")

        except Forbidden:
            await ctx.send("I am not allowed to add the role!")

        # We may get this error if `discord.utils.get` can't find the role.
        except AttributeError:
            await ctx.send("I could not find a role called `Announcement`.")

    @commands.command(name="invite", aliases=["about"])
    async def invite(self, ctx):
        """Gives you a message showing all invite links!"""

        user = self.bot.get_user(ctx.author.id)
        title = "Credits"
        text = ("Major thanks to the developers of Sharpbot, if you would like "
                "to support us here are links to invite Sharpbot to your "
                "server, Sharpbot's server and to everyone that helped "
                "contribute! :heart:")

        embed = await create_embed(ctx, title, text)
        embed.add_field(name="Server", value="[Server](https://discord.gg/djfDeQe)")
        embed.add_field(name="Invite", value="[Invite](https://discordapp.com/oauth2/authorize?client_id="
                                             "404251984892526593&permissions=85056&scope=bot)")
        embed.add_field(name="Contributers / Devs",
                        value="[Sharp](https://github.com/Sharpz7)\n"
                              "[Kingsley McDonald](https://github.com/kingdom5500)\n"
                              "[issuemeaname](https://gitlab.com/issuemeaname)")

        await user.send(embed=embed)


def setup(bot):
    bot.add_cog(DefaultCommands(bot))
