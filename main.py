import asyncio
import os
import traceback
from itertools import cycle
from math import floor

import discord
from discord.ext import commands

from events.functions import *


async def get_prefixes(client: commands.Bot, message: discord.Message):
    connection, cursor = await db_connect()

    try:
        prefix = await select(cursor, _select=[
            "prefix"], _from="prefix", _where=f"guild={message.guild.id}")
    except:
        pass

    if prefix:
        return str(prefix[0])
    else:
        return "!"


intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix=get_prefixes, intents=intents)
status = cycle(['Status 1', 'Status 2'])


def team_dev(ctx: commands.Context):
    return ctx.author.id == 440141443877830656


# Events


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game("Wouaf | !help"))
    connection, cursor = await db_connect()

    try:
        await cursor.execute("DROP TABLE chat_table")
    except sqlite3.OperationalError:
        pass
    else:
        await connection.commit()
    await create(connection, cursor, "dragonball", _names=[
        "guild_id", "user_id", "player_infos"], _type=["INT", "INT", "TEXT"])
    await db_close(connection)
    print(f"{client.user.display_name.title()}#{client.user.discriminator} est prêt.")
    write_file(log_file, "Le bot est prêt.", is_log=True)


@client.event
async def on_member_join(member: discord.Member):
    connection, cursor = await db_connect()
    welcome = await(await cursor.execute(
        "SELECT welcome_channel_id, welcome_message FROM welcome WHERE guild_id = ?", (member.guild.id,))).fetchone()

    if welcome:
        welcome_channel_id = welcome[0]
        welcome_message = welcome[1]
        welcome_channel = client.get_channel(int(welcome_channel_id))
        embed = discord.Embed()
        embed.title = f"Bienvenue {member.display_name}#{member.discriminator}!"
        embed.color = discord.Color.green()
        embed.set_thumbnail(url=member.avatar_url)
        embed.set_footer(text=member.guild.name,
                         icon_url=member.guild.icon_url)
        embed.description = welcome_message.replace("$member", member.mention)
        embed.timestamp = datetime.utcnow()
        await welcome_channel.send(embed=embed)

    await db_close(connection)

    write_file(
        set_file_logs(member.guild.id), f"{member} a rejoint le serveur!", is_log=True)
    await get_log_channel(client, member, f"{member} a rejoint le serveur!")


@client.event
async def on_member_remove(member: discord.Member):
    write_file(
        set_file_logs(member.guild.id), f'{member} a quitté le serveur!', is_log=True)
    await get_log_channel(client, member, f'{member} a quitté le serveur!')


@client.event
async def on_guild_join(guild: discord.Guild):
    connection, cursor = await db_connect()
    await cursor.execute(
        "INSERT INTO prefix(guild, prefix) VALUES(?, ?)", (guild.id, "!"))
    insert(connection, cursor, _into="prefix", _names=[
           "guild", "prefix"], _values=[guild.id, "!"])
    await db_close(connection)
    write_file(log_file,
               f"J'ai rejoint le serveur {guild.name}!", is_log=True)


@client.event
async def on_guild_remove(guild: discord.Guild):
    connection, cursor = await db_connect()
    delete(connection, cursor, _from="prefix", _where=f"guild={guild.id}")
    write_file(log_file,
               f"J'ai quitté le serveur {guild.name}!", is_log=True)


# Commands Error


@client.event
async def on_command_error(ctx: commands.Context, error):
    write_file(
        log_file, f"'{error}' dans le serveur {ctx.guild.name} par {ctx.author.display_name}#{ctx.author.discriminator}(id: {ctx.author.id})(channel: {ctx.channel.name})", is_log=True)

    def check_author(reaction):
        return reaction.user_id == ctx.author.id and reaction.emoji.name == "\U0001f197"

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Veuillez entrer le nombre d'arguments nécessaires à la commande `{ctx.prefix}{ctx.command.qualified_name}`, {ctx.author.mention}")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f"La commande `{ctx.message.content}` n'existe pas {ctx.author.mention}")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(f"Vous n'avez pas les permissions nécessaires pour éxecuter la commande `{ctx.prefix}{ctx.command.qualified_name}`, {ctx.author.mention}")
    elif isinstance(error, discord.errors.Forbidden):
        await ctx.send(f"Je n'ai pas les permissions nécessaires pour exécuter la commande `{ctx.prefix}{ctx.command.qualified_name}`, {ctx.author.mention}")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"Veuillez patienter encore {round(error.retry_after)} secondes avant de pouvoir utiliser la commande `{ctx.prefix}{ctx.command.qualified_name}`, {ctx.author.mention}")
    else:
        etype = type(error)
        trace = error.__traceback__
        verbosity = 4
        lines = traceback.format_exception(etype, error, trace, verbosity)
        traceback_text = ''.join(lines)
        print(traceback_text)
        message_error = await ctx.send(error)
        await message_error.add_reaction("\U0001f197")
        try:
            await client.wait_for("raw_reaction_add", check=check_author, timeout=120.0)
        except asyncio.TimeoutError:
            await message_error.delete()
        else:
            await message_error.delete()

# Commands


@client.command(aliases=["ld"], hidden=True)
@commands.check(team_dev)
async def load(ctx: commands.Context, extension):
    try:
        client.load_extension(f'cogs.{extension}')
        await ctx.send(f"Chargement de la catégorie {extension} terminée.")

    except discord.DiscordException as err:
        return await ctx.send(err)
    else:
        write_file(
            log_file, f"Chargement de la catégorie {extension} par {ctx.author.display_name}#{ctx.author.discriminator} terminée.", is_log=True)


@client.command(aliases=["ul"], hidden=True)
@commands.check(team_dev)
async def unload(ctx: commands.Context, extension):
    try:
        client.unload_extension(f'cogs.{extension}')
    except discord.DiscordException as err:
        return await ctx.send(err)
    else:
        await ctx.send(f"Déchargement de la catégorie {extension} terminée.")
        write_file(
            log_file, f"Déchargement de la catégorie {extension} par {ctx.author.display_name}#{ctx.author.discriminator}terminée.", is_log=True)


@client.command(aliases=["rl"], hidden=True)
@commands.check(team_dev)
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

client.run("NzQ4Njg5MDc1ODU4NDQwMzQz.X0hFCQ.4T_UE1BeM2UgVpTXZg7lTstdhsY")
