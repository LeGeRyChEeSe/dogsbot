import asyncio
import os
from asyncio import queues

from discord.ext import commands
from discord.utils import get


class Music(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Commands
    @commands.command()
    async def join(self, ctx):
        client = self.client
        global voice
        channel = ctx.author.voice.channel
        voice = get(client.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
        await ctx.send(f"J'ai rejoins le canal {channel}!")

    @commands.command()
    async def leave(self, ctx):
        client = self.client
        channel = ctx.author.voice.channel
        voice = get(client.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.disconnect()
            await ctx.send(f"J'ai quitté le canal {channel}!")

    @commands.command(aliases=["p", "pl", "pla"])
    async def play(self, ctx, url: str):
        client = self.client

        def check_queue():
            Queue_infile = os.path.isdir("./Queue")
            if Queue_infile is True:
                DIR = os.path.abspath(os.path.realpath("Queue"))
                length = len(os.listdir(DIR))
                still_q = length - 1
                try:
                    first_file = os.listdir(DIR)[0]
                except:
                    asyncio.run_coroutine_threadsafe(
                        ctx.send("La queue est vide!"), client.loop)
                    queues.clear()
                    return
                main_location = os.path.dirname(os.path.realpath(__file__))
                song_path = os.path.abspath(
                    os.path.realpath("Queue") + "\\" + first_file)
                if length != 0:
                    asyncio.run_coroutine_threadsafe(
                        ctx.send("La musique est finie, la prochaine va être jouée!"), client.loop)
                    asyncio.run_coroutine_threadsafe(
                        ctx.send(f"Liste des musiques restantes: {still_q}"), client.loop)
                    song_there = os.path.isfile("")


def setup(client):
    client.add_cog(Music(client))
