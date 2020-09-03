import discord
from discord.ext import commands
import env
import os

client = commands.Bot(command_prefix="!")


@client.event
async def on_member_join(member):
    print(f'{member} a rejoint le serveur.')


@client.event
async def on_member_remove(member):
    print(f'{member} a quitté le serveur.')


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


for filename in os.listdir('./cogs/'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

client.run(env.TOKEN)
