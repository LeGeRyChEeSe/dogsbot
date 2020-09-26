import discord
from discord.ext import commands
import youtube_dl
import asyncio

musics = {}
ytdl = youtube_dl.YoutubeDL()


class Song:
    def __init__(self, link):
        song = ytdl.extract_info(link, download=False)
        song_format = song["formats"][0]
        self.url = song["webpage_url"]
        self.stream_url = song_format["url"]
        self.title = song["title"]
        self.duration = song["duration"]


def play_song(self, ctx, client, song, queue):
    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(song.stream_url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"))

    def next(_):
        if len(queue) > 0:
            new_song = queue[0]
            del queue[0]
            play_song(self, ctx, client, new_song, queue)
            embed = discord.Embed(
                title=f"{new_song.title} ({new_song.duration}s)", url=new_song.url, description="Cette musique va être lancée.")
            asyncio.run_coroutine_threadsafe(
                ctx.send(embed=embed), self.loop)

        else:
            asyncio.run_coroutine_threadsafe(
                client.disconnect(), self.loop)
    client.play(source, after=next)


class Music(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Commands
    @ commands.command()
    async def join(self, ctx):
        channel = ctx.author.voice.channel
        await channel.connect()

    @ commands.command()
    async def leave(self, ctx):
        channel = ctx.author.voice.channel
        await ctx.voice_client.disconnect()

    @ commands.command()
    async def p(self, ctx, url):
        client = ctx.guild.voice_client
        if client and client.channel:
            song = Song(url)
            musics[ctx.guild].append(song)
        else:
            channel = ctx.author.voice.channel
            song = Song(url)
            musics[ctx.guild] = []
            client = await channel.connect()
            embed = discord.Embed(
                title=f"{song.title} ({song.duration}s)", url=song.url, description="Cette musique va être lancée.")
            await ctx.send(embed=embed)
            play_song(self.client, ctx, client, song, musics[ctx.guild])
        await ctx.message.delete()


def setup(client):
    client.add_cog(Music(client))
