import asyncio
import random as ran

from discord.ext import commands

from bot.classes import items, creatures, Fist, shield_boostrate, damage_boostrate, animal_boostrate
from bot.database import query, modify
from bot.utils import create_embed


class FightCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="fight", aliases=["f"])
    async def fight(self, ctx):
        """See all fight commands."""

        if ctx.invoked_subcommand is None:
            title = "FIGHT HELP COMMANDS"
            text = (
                "```"
                "/f duel - Duel a nearby player\n"
                "/f info - See your current fighting gear\n"
                "/f assign [item] [place] - add a item to your gear!\n"
                "/f remove [place] - remove a item\n"
                "```"
            )
            embed = await create_embed(ctx, title, text)
            await ctx.send(embed=embed)

    @fight.command(name="duel")
    async def duel(self, ctx):
        """Start a duel with another User"""

        users, coords = await query.coords(ctx.author.id)
        if len(users) < 2:
            title = "No one is here to fight!"
            text = "Keep looking!"
            embed = await create_embed(ctx, title, text)
            await ctx.send(embed=embed)
        else:
            # Select the two users who will participate
            users = users[:2]
            if users[0] == str(ctx.author.id):
                user = users[1]
            else:
                user = users[0]

            user_data = self.bot.get_user(int(user))
            p1 = await query.user(users[0])
            p2 = await query.user(users[1])

            title = f"You are now in a duel with {user_data}!!"
            text = "Let the fun begin!"

            title1 = "**Player1's items:**"
            text1 = await self.fight_parse(p1['fight'])
            title2 = "**Player2's items:**"
            text2 = await self.fight_parse(p2['fight'])

            embed = await create_embed(ctx, title, text)
            embed.add_field(name=title1, value=text1, inline=False)
            embed.add_field(name=title2, value=text2, inline=False)

            response = await ctx.send(embed=embed)

            fight = Duel([p1, p2], coords, response, self.bot)
            self.bot.loop.create_task(fight.start_loop())

    @fight.command(aliases=['i'])
    async def info(self, ctx):
        """See your fighting info"""

        slots = await query.user(ctx.author.id, 'fight')
        text = await self.fight_parse(slots)
        title = "Your items for battle:"
        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @fight.command(name='assign')
    async def assign(self, ctx, name, place: int = 1):
        """Assign an item to a slot in your fighting inventory"""

        text = "Use your items in battle with `/help duel!`"
        slots, inventory = await query.user(ctx.author.id, 'fight', 'inventory')
        name = name.capitalize()

        item = items.get(name)
        if item is None:
            return ctx.send("You can not put this item here!")

        if place not in range(1, 4):
            title = "You can only have 3 slots!"

        elif name in slots:
            title = f"You already have a {item} in your slots!"

        elif name not in inventory:
            title = f"You do not have a {item}!"

        elif item.damage is None and item.health is None:
            title = f"You can't put a non-fighting item here!"

        else:
            await modify.fight(ctx.author.id, slots, name, place)
            title = f"**Assigned {item} to place {place}**"

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @fight.command(name="remove")
    async def remove(self, ctx, place: int):
        """
        Removes a item from your fight slots.
        """

        text = "Use your items in battle with `/help duel!`"
        slots = await query.user(ctx.author.id, 'fight')
        name = slots[place-1]

        if name == "Empty":
            title = f"You have nothing in this slot!"

        else:
            await modify.fight(ctx.author.id, slots, name, -place)
            title = f"**Removed {name} from place {place}**"

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @commands.command(name='sleep')
    async def sleep(self, ctx):
        """
        Sends you to sleep!
        """

        await modify.sleep(ctx.author.id, True)
        title = f"You are now sleeping!"
        text = "Type /help sleep for more info!"

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    @commands.command(aliases=["get-up", "awake"])
    async def wake(self, ctx):
        """
        Wakes you up from your terrible nightmares!
        """

        await modify.sleep(ctx.author.id, False)
        title = f"You are now awake!"
        text = "Type /help sleep for more info!"

        embed = await create_embed(ctx, title, text)
        await ctx.send(embed=embed)

    async def fight_parse(self, slots):
        """
        Helper method for converting a list of slots into a nice string.
        """

        # Construct a list of pretty strings, then join 'em.
        slot_list = []
        for i, weapon in enumerate(slots, 1):
            slot_list.append(f"**Slot {i}** - {weapon}")

        return "\n".join(slot_list)


class Duel:

    TURN_DURATION = 4

    def __init__(self, player_doc, coords, response, bot):
        self.coords = coords
        self.looping = True
        self.response = response
        self.bot = bot
        self.player1 = Player(player_doc[0], self.bot.get_user(int(player_doc[0]["id"])).name)
        self.player2 = Player(player_doc[1], self.bot.get_user(int(player_doc[1]["id"])).name)

    async def start_loop(self):
        """Begin the fight! Turns are played until someone dies."""
        counter = 0
        while self.looping:
            # Choose a random player to make a move
            attack = ran.choice([self.player1, self.player2])
            # Make sure other player is the defender.
            defend = (self.player1 if attack != self.player1 else self.player2)

            # Get all move values.
            damage, animal_dmg, weapon, animal = await self.do_move(attack, defend)

            # Sleep so discord doesn't get angry.
            await asyncio.sleep(self.TURN_DURATION)
            counter += 1

            # Nice little display!
            if animal_dmg != 0:
                animal = (f"{defend.name} took an extra {animal_dmg} damage from a {animal}\n")
            else:
                animal = ""

            if damage != 0:
                damage = f"{defend.name} took {damage} damage from a {weapon}!\n"

            else:
                damage = ""

            title = f"You are now in a duel!!"
            text = (f"Let the fun begin!\n\n"
                    f"**{self.player1.name}:**\n"
                    f"**Health**: {self.player1.health}\n\n"
                    f"**{self.player2.name}:**\n"
                    f"**Health**: {self.player2.health}\n\n"

                    f"**LIVE FEED**\n"
                    f"{damage}"
                    f"{animal}")

            embed = await create_embed(self.response, title, text)
            await self.response.edit(embed=embed)

            # If defender is dead, trigger end sequence.
            if defend.health <= 0:
                await self.death(defend, winner=attack)

    async def do_move(self, attack, defend):
        """Let one player make their strike."""

        # If all elements are empty.
        if (await self.check_equal(attack.weapons)):
            # Make sure default "fist" item is used.
            weapon = Fist()
        else:
            # choose weapon
            weapon = await self.weapon_find(attack.weapons)
        # If the weapon isn't a damage item...
        if weapon.damage is None:
            damage = 0
        else:
            damage = await self.damage(attack, weapon)

        # Get animal damage
        animal, animal_dmg = await self.animal(attack)

        # Remove all damage
        defend.health -= (damage + animal_dmg)
        return damage, animal_dmg, weapon, animal

    async def death(self, loser, winner):
        """Oops, someone died. Stop the duel, and clean up the embed."""

        self.looping = False
        title = f"{loser.name} died!"
        text = (f"{loser.name} was sent to sleep, and {winner.name} collected their winnings!")
        embed = await create_embed(self.response, title, text)
        # Divide up the losers inv.
        for key, value in loser.inv.items():
            if value != 0:
                lost = int(value - value / ran.randint(3, 7))
                await modify.inv(loser.id, key, -lost)
                await modify.inv(winner.id, key, lost)

        await self.response.edit(embed=embed)

    async def weapon_find(self, weapons):
        """Choose a random weapon to use in the fight."""

        while "Empty" in weapons:
            weapons.remove("Empty")

        weapon_name = ran.choice(weapons)
        return items.get(weapon_name)

    async def damage(self, player, weapon):
        """
        Add damage, including weapon level.
        """
        if weapon.name == "Fist":
            lvl = 1
        else:
            lvl = player.inv.get(weapon.name)
        return (weapon.damage * damage_boostrate.at(lvl)) + ran.randint(0, 5)

    async def animal(self, player):
        """Get a player's pet name and damage (if they have one)."""
        if not player.pet:
            animal = None
            damage = 0
        else:
            animal = creatures.get(player.pet.get("name"))
            lvl = player.pet.get("lvl")
            damage = animal.damage * animal_boostrate.at(lvl) + ran.randint(0, 5)
        return animal, damage

    async def check_equal(self, lst):
        """
        Checks if all items in a list are the same.
        """
        if len(lst) == 1:
            return False
        return lst[1:] == lst[:-1]


class Player:

    DEFAULT_HEALTH = 40

    def __init__(self, data, name):
        self.data = data
        self.name = name
        self.health = self.DEFAULT_HEALTH
        self.weapons = self.data.get("fight")
        self.pet = self.data.get('pet')
        self.id = self.data.get("id")
        self.inv = self.data.get('inventory')
        self.killed = []
        # Add any shield health
        for counter, name in enumerate(self.weapons):
            item = items.get(name)
            if item is not None and item.health:
                # Include Level Boost.
                lvl = self.inv.get(item.name)
                self.health += item.health * shield_boostrate.at(lvl)
                self.weapons[counter] = "Empty"


def setup(bot):
    bot.add_cog(FightCommands(bot))
