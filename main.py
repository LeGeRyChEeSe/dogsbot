import discord
from discord.ext import commands, tasks
import env
import os
from itertools import cycle
import json


def get_prefixes(client, message):
    with open(file, "r") as f:
        prefixes = json.load(f)

    return prefixes[str(message.guild.id)]


file = "assets\\prefixes.json"
client = commands.Bot(command_prefix=get_prefixes)
status = cycle(['Status 1', 'Status 2'])


# Events


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.idle, activity=discord.Game("Wouaf | !help"))
    # change_status.start()
    print("Le bot est prêt.")


@client.event
async def on_member_join(member):
    print(f'{member} a rejoint le serveur.')

    role = member.guild.get_role(role_id=748858810105462884)

    await member.add_roles(role)


@client.event
async def on_member_remove(member):
    print(f'{member} a quitté le serveur.')


@client.event
async def on_guild_join(guild):
    with open(file, "r") as f:
        prefixes = json.load(f)

    prefixes[str(guild.id)] = "!"

    with open(file, "w") as f:
        json.dump(prefixes, f, indent=4)


@client.event
async def on_guild_remove(guild):
    with open(file, "r") as f:
        prefixes = json.load(f)

    prefixes.pop(str(guild.id))

    with open(file, "w") as f:
        json.dump(prefixes, f, indent=4)

# Commands Error


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Veuillez entrer le nombre d'arguments nécessaires à la commande `{ctx.message.content}`.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send(f"La commande `{ctx.message.content}` n'existe pas.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(f"Vous n'avez pas les permissions nécessaires pour éxecuter la commande `{ctx.message.content}`")
    else:
        print(error)

# Commands


@client.command()
async def load(ctx, extension):

    try:
        client.load_extension(f'cogs.{extension}')
        await ctx.send(f"Chargement de la catégorie {extension} terminée.")

    except discord.DiscordException as err:
        return await ctx.send(err)


@client.command()
async def unload(ctx, extension):

    try:
        client.unload_extension(f'cogs.{extension}')
        await ctx.send(f"Déchargement de la catégorie {extension} terminée.")

    except discord.DiscordException as err:
        return await ctx.send(err)


@client.command()
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

client.run(env.TOKEN)
