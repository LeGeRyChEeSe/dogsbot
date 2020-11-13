from math import log
from events.functions import write_file
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError, MissingRequiredArgument
from googlesearch import search
from discord import Embed, Colour
import datetime
import requests
from bs4 import BeautifulSoup
from googletrans import Translator, LANGUAGES

from events.functions import *


class Common(commands.Cog):
    def __init__(self, client):
        commands.Cog.__init__(self)
        self.client = client

    translator = Translator(
        service_urls=["translate.google.com", "translate.google.fr"])

    # Commands

    @commands.command()
    async def owner(self, ctx: commands.Context):
        owner = ctx.guild.owner_id
        await ctx.send(f"Le propriétaire de {ctx.guild.name} est <@{owner}>!")

    @commands.command(brief="Envoyer un message", usage="<message>",
                      description=f"Permet d'envoyer un message par l'intermédiaire du bot")
    async def me(self, ctx: commands.Context, *,
                 message="Veuillez entrer du texte et/ou un(e) fichier/photo pour que je puisse le répéter !"):
        try:
            file = await ctx.message.attachments[0].to_file()
        except IndexError:
            await ctx.message.delete()
            await ctx.send(message)
        else:
            await ctx.send(message, file=file)
            await ctx.message.delete()
        write_file(
            log_file, f"{ctx.author.display_name}#{ctx.author.discriminator} a écrit quelque chose via le bot dans le serveur {ctx.guild.name}")

    @commands.command(name="ping", brief="Bot latency",
                      description="Réponds par 'Pong!' en indiquant la latence du bot.")
    async def ping(self, ctx: commands.Context):
        await ctx.send(f"Pong! (Latence du bot: {round(self.client.latency * 1000)}ms)")

    @commands.command(name="google", brief="Recherches Googles",
                      description="Obtenez des réponses à vos recherches google!", usage="<recherche>")
    async def google(self, ctx: commands.Context, *request):
        if not request:
            raise MissingRequiredArgument()

        r = " ".join(list(request))
        async with ctx.channel.typing():
            google = search(r, tld="fr", num=10, stop=5, pause=2, lang="fr")
            links = []
            search_embed = Embed(color=Colour.green(),
                                 timestamp=datetime.datetime.utcnow())
            search_embed.set_author(name=r.title())
            titles = []

            for link in google:
                links.append(link)
                requete = requests.get(link)
                page = requete.content
                soup = BeautifulSoup(page)
                h1 = soup.find("title")
                h1 = h1.string.strip()
                titles.append(h1)

            values = []
            for i in range(len(links)):
                values.append(f"[{titles[i]}]({links[i]})")

            search_embed.add_field(name="Liens", value="\n".join(values))

        await ctx.send(embed=search_embed)

    @commands.command(name="invite",
                      description="Créez une invitation vers le salon de votre choix, ou par défaut dans le salon "
                                  "actuel.\nVous pouvez définir les paramètres d'une invitation habituelle.",
                      usage="<channel(<#0123456789>)> <durée_en_secondes(60)> <nb_max_d'utilisation(15)> <temporaire("
                            "False ou True)> <unique(False ou True)> <raison>")
    @commands.has_permissions(create_instant_invite=True)
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
        write_file(
            log_file, f"{ctx.author.display_name}#{ctx.author.discriminator} a créé un lien d'invitation dans le serveur {ctx.guild.name}(canal: {choose_channel})")

    @commands.command(name="translate", aliases=["tr", "googletr", "traduction", "googletranslate", "googletraduction"])
    async def translate(self, ctx: commands.Context, *, content: str):
        await ctx.message.delete()

        try:
            language = self.translator.detect(content)
        except AttributeError as err:
            write_file(log_file, err)
            return await ctx.send("Service de traduction indisponible.")

        if language.lang == "fr":
            return await ctx.send(f"> {LANGUAGES[language.lang].title()}: `{content}`\n{LANGUAGES['en'].title()}: `{self.translator.translate(content, dest='en').text}`")
        elif language.lang == "en":
            return await ctx.send(f"> {LANGUAGES[language.lang].title()}: `{content}`\n{LANGUAGES['fr'].title()}: `{self.translator.translate(content, dest='fr').text}`")
        else:
            return await ctx.send(f"> {LANGUAGES[language.lang].title()}: `{content}`\n{LANGUAGES['fr'].title()}: `{self.translator.translate(content, dest='fr').text}`")


def setup(client):
    client.add_cog(Common(client))
