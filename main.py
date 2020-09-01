import discord
from discord.ext import commands
import env
import random

client = commands.Bot(command_prefix="!")


@client.event
async def on_ready():
    print("Le bot est prêt.")


@client.event
async def on_member_join(member):
    print(f'{member} a rejoins le serveur.')


@client.event
async def on_member_remove(member):
    print(f'{member} a quitté le serveur.')


@client.command()
async def ping(self):
    await self.send(f"Pong! {round(client.latency * 1000)}ms")


@client.command(aliases=['8ball', 'eightball'])
async def _8ball(self, *, question):
    responses = ["Bien sûr!", "Mais oui, t'a cru toi...", "Effectivement.", "Je ne te le fais pas dire!", "Ca m'étonnerait !", "T'es irrécupérable... :facepalm:", "Je te le donne dans le mille Émile !",
                 "Faut arrêter la drogue mon vieux.", "Peut-être que oui, peut-être que non", "Et moi j'ai une question : Quelle est la différence entre un hamburger ? :thinking:"]
    await self.send(f"{random.choice(responses)}")


@client.command(aliases=['purge', 'erase', 'delete'])
async def clear(self, amount=5):
    await self.channel.purge(limit=amount + 1)


@client.command()
async def kick(self, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)


@client.command()
async def ban(self, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)


@client.command()
async def me(self, *, message="Veuillez entrer du texte pour que je puisse le répéter !"):
    await self.message.delete()
    await self.send(f"{message}")

client.run(env.TOKEN)
