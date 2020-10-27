from discord.ext import commands
from googlesearch import search
from discord import Embed, Colour
import datetime


class Common(commands.Cog):
    def __init__(self, client):
        commands.Cog.__init__(self)
        self.client = client

    # Commands

    @commands.command()
    async def owner(self, ctx: commands.Context):
        owner = ctx.guild.owner_id
        await ctx.send(f"Le propriétaire de {ctx.guild.name} est <@{owner}>!")

    @commands.command(brief="Envoyer un message", usage="<message>",
                      description=f"Permet d'envoyer un message par l'intermédiaire du bot")
    async def me(self, ctx: commands.Context, *,
                 message="Veuillez entrer du texte et/ou un fichier/photo pour que je puisse le répéter !"):
        try:
            file = await ctx.message.attachments[0].to_file()
        except IndexError:
            await ctx.message.delete()
            await ctx.send(message)
        else:
            await ctx.send(message, file=file)
            await ctx.message.delete()

    @commands.command(name="ping", brief="Bot latency",
                      description="Réponds par 'Pong!' en indiquant la latence du bot.")
    async def ping(self, ctx: commands.Context):
        await ctx.send(f"Pong! (Latence du bot: {round(self.client.latency * 1000)}ms)")

    @commands.command(name="google", brief="Recherches Googles",
                      description="Obtenez des réponses à vos recherches google!", usage="<recherche>")
    async def google(self, ctx: commands.Context, *request):
        r = " ".join(list(request))
        async with ctx.channel.typing():
            google = search(r, tld="fr", num=10, stop=10, pause=2, lang="fr")
            links = []
            search_embed = Embed(color=Colour.green(), timestamp=datetime.datetime.utcnow())
            search_embed.set_author(name=r.title())

            for link in google:
                links.append(link)

            search_embed.add_field(name="Liens", value="\n".join(links))

        await ctx.send(embed=search_embed)

    @commands.command(name="invite",
                      description="Créez une invitation vers le salon de votre choix, ou par défaut dans le salon "
                                  "actuel.\nVous pouvez définir les paramètres d'une invitation habituelle.",
                      usage="<channel(<#0123456789>)> <durée_en_secondes(60)> <nb_max_d'utilisation(15)> <temporaire("
                            "False ou True)> <unique(False ou True)> <raison>")
    async def invite(self, ctx: commands.Context, choose_channel=None, max_age: int = 0, max_uses: int = 0,
                     temporary: bool = False,
                     unique: bool = False,
                     *reason: str):
        if choose_channel:
            channel = choose_channel.replace("<#", "").replace(">", "")
            channel = ctx.guild.get_channel(int(channel))
        else:
            channel = ctx.channel
        invite = await channel.create_invite(max_age=max_age, max_uses=max_uses, temporary=temporary,
                                             unique=unique, reason=" ".join(list(reason)))
        await ctx.send(invite)


def setup(client):
    client.add_cog(Common(client))
