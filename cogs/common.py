import discord
from discord.ext import commands


class Common(commands.Cog):
    def __init__(self, client):
        self.client = client

    # Commands
    @commands.command(brief="Envoyer un message", usage="<message>", description=f"Permet d'envoyer un message par l'intermédiaire du bot")
    async def me(self, ctx, *, message="Veuillez entrer du texte pour que je puisse le répéter !"):
        await ctx.message.delete()
        await ctx.send(message)


def setup(client):
    client.add_cog(Common(client))
