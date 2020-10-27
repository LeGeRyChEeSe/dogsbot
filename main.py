import asyncio
import os
import traceback
from itertools import cycle

import discord
from discord.ext import commands

from events.functions import *


def get_prefixes(client: commands.Bot, message: discord.Message):
    connection, cursor = db_connect()

    prefix = select(cursor, _select="prefix", _from="prefix", _where=f"guild={message.guild.id}")

    return str(prefix[0])


file = "assets/prefixes.json"
client = commands.Bot(command_prefix=get_prefixes)
status = cycle(['Status 1', 'Status 2'])


# Events


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game("Wouaf | !help"))
    connection, cursor = db_connect()

    try:
        cursor.execute("DROP TABLE chat_table")
    except sqlite3.OperationalError:
        pass
    else:
        connection.commit()
    connection.close()
    print("Le bot est prêt.")


@client.event
async def on_member_join(member: discord.Member):
    print(f"{member} a rejoint le serveur {member.guild.name}!")


@client.event
async def on_member_remove(member: discord.Member):
    print(f'{member} a quitté le serveur {member.guild.name}!')


@client.event
async def on_guild_join(guild: discord.Guild):
    connection, cursor = db_connect()
    insert(connection, cursor, _into="prefix", _names=["guild", "prefix"], _values=[guild.id, "!"])
    db_close(connection)


@client.event
async def on_guild_remove(guild: discord.Guild):
    connection, cursor = db_connect()
    delete(connection, cursor, _from="prefix", _where=f"guild={guild.id}")


# Commands Error


@client.event
async def on_command_error(ctx, error):
    def check_author(reaction):
        return reaction.user_id == ctx.author.id and reaction.emoji.name == "\U0001f197"

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Veuillez entrer le nombre d'arguments nécessaires à la commande `{ctx.message.content}`.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f"La commande `{ctx.message.content}` n'existe pas.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(f"Vous n'avez pas les permissions nécessaires pour éxecuter la commande `{ctx.message.content}`")
    else:
        etype = type(error)
        trace = error.__traceback__
        verbosity = 4
        lines = traceback.format_exception(etype, error, trace, verbosity)
        traceback_text = ''.join(lines)
        print(traceback_text)
        message_error = await ctx.send(traceback_text)
        await message_error.add_reaction("\U0001f197")
        try:
            reaction_to_delete_message = await client.wait_for("raw_reaction_add", check=check_author, timeout=120.0)
        except asyncio.TimeoutError:
            await message_error.delete()
        else:
            await message_error.delete()
            # Commands


@client.command(aliases=["ld"])
async def load(ctx, extension):
    try:
        client.load_extension(f'cogs.{extension}')
        await ctx.send(f"Chargement de la catégorie {extension} terminée.")

    except discord.DiscordException as err:
        return await ctx.send(err)


@client.command(aliases=["ul"])
async def unload(ctx, extension):
    try:
        client.unload_extension(f'cogs.{extension}')
        await ctx.send(f"Déchargement de la catégorie {extension} terminée.")

    except discord.DiscordException as err:
        return await ctx.send(err)


@client.command(aliases=["rl"])
async def reload(ctx, extension):
    await unload(ctx, extension)
    await load(ctx, extension)


# Tasks
"""
@tasks.loop(seconds=10,)
async def change_status():
    await client.change_presence(activity=discord.Game(next(status)))
"""

for filename in os.listdir('./cogs/'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

if not "TOKEN" in os.environ:
    env = open(".env.py", "r").readline()
    token = env.split("=")[1].replace(
        "\n", "").replace(" ", "").replace('"', "")
    os.environ["TOKEN"] = token

client.run(os.environ["TOKEN"])
