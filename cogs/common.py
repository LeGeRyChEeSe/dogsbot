import asyncio
from math import log
from discord.embeds import EmptyEmbed

from discord.errors import ClientException
from events.functions import write_file
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError, MissingRequiredArgument
from googlesearch import search
from discord import Embed, Colour
import datetime
import requests
from bs4 import BeautifulSoup
from googletrans import Translator, LANGUAGES
import pythonping

from events.functions import *


class Common(commands.Cog):
    def __init__(self, client: commands.Bot):
        commands.Cog.__init__(self)
        self.client = client

    translator = Translator(
        service_urls=["translate.google.com", "translate.google.fr"])

    # Commands

    @commands.command(hidden=False, name="owner", brief="Qui est le propriétaire du serveur ?", description="Indique qui est le propriétaire du serveur.")
    async def owner(self, ctx: commands.Context):
        owner = ctx.guild.owner
        await ctx.send(f"Le propriétaire de {ctx.guild.name} est **{owner.name}#{owner.discriminator}**")

    @commands.command(brief="Envoyer un message", usage="<message> [attachment]",
                      description=f"Permet d'envoyer un message et des photos/fichiers par l'intermédiaire du bot")
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
            set_file_logs(ctx.guild.id), f"{ctx.author.display_name}#{ctx.author.discriminator} a écrit quelque chose via le bot dans le salon {ctx.channel.name}!", is_log=True)

    @commands.command(name="ping", brief="Latence du Bot",
                      description="Répond par 'Pong!' en indiquant la latence du bot.")
    async def ping(self, ctx: commands.Context):
        await ctx.send(f"Pong! (Latence du bot: {round(self.client.latency * 1000)}ms)")

    @commands.command(name="google", brief="Recherches Google",
                      description="Obtenez des réponses à vos recherches google!", usage="<recherche>")
    async def google(self, ctx: commands.Context, *request):
        if not request:
            return await ctx.send(f"Veuillez entrer la commande `{ctx.prefix}help {ctx.command.name}` pour obtenir plus d'informations sur la commande")

        r = " ".join(list(request))
        async with ctx.channel.typing():
            google = search(r, tld="fr", num=10, stop=5, pause=2, lang="fr")
            links = []
            search_embed = Embed(color=Colour.green(),
                                 timestamp=datetime.utcnow())
            search_embed.set_author(name=r.title())
            titles = []

            for link in google:
                links.append(link)
                requete = requests.get(link)
                page = requete.content
                soup = BeautifulSoup(page, features="html.parser")
                h1 = soup.find("title")
                h1 = h1.string.strip()
                titles.append(h1)

            values = []
            for i in range(len(links)):
                values.append(f"[{titles[i]}]({links[i]})")

            search_embed.add_field(name="Liens", value="\n".join(values))

        await ctx.send(embed=search_embed)

    @commands.command(name="invite", brief="Créer une invitation du serveur",
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
            set_file_logs(ctx.guild.id), f"{ctx.author.display_name}#{ctx.author.discriminator} a créé un lien d'invitation dans le salon {choose_channel})", is_log=True)

    @commands.group(name="translate", aliases=["tr"], brief="Traduire des messages", usage="<language> <message>", description=f'Traduire un message donné en précisant la langue de destination.', invoke_without_command=True)
    async def translate(self, ctx: commands.Context, *content: str):
        def check_author(reaction):
            return reaction.user_id == ctx.author.id and reaction.emoji.name == "\U0001f197"

        if not content:
            message_error = await ctx.send(f"Veuillez utiliser le format suivant pour cette commande: `{ctx.prefix}{ctx.command} {ctx.command.usage}`\nPour avoir la liste complète des langues disponibles, tapez la commande `{ctx.prefix}{ctx.command} lang` et je vous enverrai la liste en message privé.")
            await message_error.add_reaction("\U0001f197")
            try:
                await self.client.wait_for("raw_reaction_add", check=check_author, timeout=120.0)
            except asyncio.TimeoutError:
                await message_error.delete()
            else:
                await message_error.delete()
            return

        lang = content[0]
        if lang not in LANGUAGES.keys():
            message_error = await ctx.send(f"Veuillez entrer une langue de destination valide. Par exemple pour traduire un message du Français à l'Anglais, écrivez `{ctx.prefix}{ctx.command} en <votre message>` ou inversement de l'Anglais au Français `{ctx.prefix}{ctx.command} fr <your message>`\nPour avoir la liste complète des langues disponibles, tapez la commande `{ctx.prefix}{ctx.command} lang` et je vous enverrai la liste en message privé.")
            await message_error.add_reaction("\U0001f197")
            try:
                await self.client.wait_for("raw_reaction_add", check=check_author, timeout=120.0)
            except asyncio.TimeoutError:
                await message_error.delete()
            else:
                await message_error.delete()
            return

        message = " ".join(content[1:])
        if not message:
            message_error = await ctx.send(f"Veuillez entrer un message après avoir indiqué la langue. Par exemple pour traduire un message du Français à l'Anglais, écrivez `{ctx.prefix}{ctx.command} en <votre message>` ou inversement de l'Anglais au Français `{ctx.prefix}{ctx.command} fr <your message>`\nPour avoir la liste complète des langues disponibles, tapez la commande `{ctx.prefix}{ctx.command} lang` et je vous enverrai la liste en message privé.")
            await message_error.add_reaction("\U0001f197")
            try:
                await self.client.wait_for("raw_reaction_add", check=check_author, timeout=120.0)
            except asyncio.TimeoutError:
                await message_error.delete()
            else:
                await message_error.delete()
            return

        try:
            language = self.translator.detect(message)
        except AttributeError as err:
            write_file(set_file_logs(ctx.guild.id), err, is_log=True)
            self.translator = Translator(
                service_urls=["translate.google.com", "translate.google.fr"])
            return await ctx.send("Une erreur est survenue. Veuillez réessayer.")

        embed = Embed(color=ctx.author.top_role.color,
                      timestamp=datetime.utcnow())
        embed.set_author(name=f"{ctx.author.display_name}#{ctx.author.discriminator}",
                         icon_url=ctx.author.avatar_url)
        embed.add_field(
            name="Say", value=f"{self.translator.translate(message, dest=lang.lower()).text}")
        embed.set_footer(
            text=f"{LANGUAGES[language.lang].title()} to {LANGUAGES[lang.lower()].title()}")

        await ctx.send(embed=embed)

    @translate.command(name="lang", brief="Donne la liste de toutes les langues et leur abréviation", description="Donne la liste de toutes les langues et leur abréviation")
    async def lang(self, ctx: commands.Context):
        langs = {}
        i = 0
        taille = 0
        for key, value in LANGUAGES.items():
            languages = f"**`{key}`**: *{value}*"
            taille += len(languages)
            if taille > 1300:
                i += 1
                taille = 0

            if not i in langs:
                langs[i] = []

            langs[i].append(languages)

        await ctx.author.send("**Voici la liste de toutes les langues disponibles:**")
        for j in range(i+1):
            await ctx.author.send("\n".join(langs[j]))

        await ctx.author.send(f"__**Veuillez utiliser l'abréviation pour traduire une phrase dans le serveur.**__ Par exemple pour traduire 'Bonjour' en anglais je vais écrire `{ctx.prefix}{self.translate.name} en Bonjour` et la phrase sera traduite en anglais.")

    @commands.group(name="incoming", brief="Liste des fonctionnalités avenirs du Bot", description="Affiche la liste des futurs ajouts de fonctionnalités au bot, ainsi que les fonctionnalités du serveur/bot que les membres du serveur suggèrent.", invoke_without_command=True)
    async def incoming(self, ctx: commands.Context):
        incoming_file = read_file("assets/Data/incoming.json", is_json=True)
        final_message = ""
        for category, values in incoming_file.items():
            if category == "Bientôt":
                final_message += "__**" + category + \
                    " à votre disposition**__ *Dépend uniquement de la motivation/du temps des devs...*\n"
                for key, value in values.items():
                    final_message += "\n__" + key + \
                        ":__\n" + '\n'.join(value) + ""
                final_message += "\n"
            elif category == "Suggestions":
                final_message += "\n" + f"__**{category}**__" + "\n"
                for key, value in values.items():
                    if int(key) == ctx.guild.id:
                        final_message += "\n" + '\n'.join(value)
                final_message += "\n\n" + \
                    f"*Ajoutez vos suggestions avec la commande `{ctx.prefix}{ctx.command.name} add \"Votre suggestion\"` !*"

        await ctx.send(final_message)

    @incoming.command(name="add", brief="Ajouter une suggestion de fonctionnalité au Bot")
    async def add(self, ctx: commands.Context, *args):
        incoming_file_suggestions = read_file(
            "assets/Data/incoming.json", is_json=True)
        exists = False
        for i in incoming_file_suggestions["Suggestions"].keys():
            if i == str(ctx.guild.id):
                exists = True
        if not exists:
            incoming_file_suggestions["Suggestions"][str(ctx.guild.id)] = []
        incoming_file_suggestions["Suggestions"][str(ctx.guild.id)].append(
            f"**{ctx.author.display_name}#{ctx.author.discriminator}** suggère: *{' '.join(args)}*")
        try:
            write_file("assets/Data/incoming.json",
                       incoming_file_suggestions, is_json=True, mode="w")
        except:
            await ctx.send("Une erreur est survenue, veuillez réessayer plus tard. |<@440141443877830656>|")
        else:
            write_file(set_file_logs(
                ctx.guild.id), f"Nouvelle suggestion par {ctx.author.display_name}#{ctx.author.discriminator}!", is_log=True)
            await ctx.send(":partying_face:  Votre suggestion a bien été enregistrée! Merci pour votre contribution, je suis toujours à votre écoute concernant vos idées de fonctionnalités à ajouter au bot/serveur! :partying_face: ")

    @commands.group(name="lanplay", aliases=["lan"], brief="Afficher les serveurs Lan-Play", description=f"Indiquez le serveur dont vous voulez afficher les informations, par exemple lanplay.reboot.ms:11451\nPour afficher la liste des serveurs disponibles, tapez la commande `lanplay list`", usage="<url>", invoke_without_command=True)
    async def lanplay(self, ctx: commands.Context, *, url: str = "switch.lan-play.com:11451"):
        embed = discord.Embed(
            title=url, timestamp=datetime.utcnow(), color=discord.Color.red())

        if not url.startswith("http://"):
            url = f"http://{url}/"

        url_formated = url.replace(
            "http://", "").replace("/", "").split(":")[0]

        ping = pythonping.ping(url_formated, out=None)

        async with ctx.channel.typing():
            try:
                lanplay_status = await getLanplayStatus(url)
            except:
                embed.title = None
                embed.set_thumbnail(url=EmptyEmbed)
                embed.description = "Une erreur est survenue, merci de réessayer plus tard."
                return await ctx.send(embed=embed)

            embed.description = f"{lanplay_status['serverInfo']['online']} :video_game: / {lanplay_status['serverInfo']['idle']} :zzz:"
            embed.set_footer(
                text=f"Ping: {ping.rtt_avg_ms} ms", icon_url=ctx.guild.icon_url)

            for room in lanplay_status["room"]:
                nb_players_room = f"{room['nodeCount']}/{room['nodeCountMax']}"
                if room['nodeCount'] == room['nodeCountMax']:
                    nb_players_room += " :x:"
                else:
                    nb_players_room += " :white_check_mark:"
                # Contenu à ajouter dans embed(value) avant le Joueurs:
                # __**Jeu**__: {room['contentId']}\n
                embed.add_field(
                    name=f"{room['hostPlayerName']} | {nb_players_room}",
                    value="**Joueurs**:\n" + ',\n'.join(player['playerName'] for player in room['nodes']), inline=True)

            if not embed.fields:
                embed.add_field(name="Parties en cours", value="Aucune")

            await ctx.send(embed=embed)

    @ lanplay.command(name="list", aliases=["liste"], brief="Liste des serveurs Lan-Play", description="Envoie en message privé la liste des serveurs disponibles")
    @commands.cooldown(rate=1, per=10.0)
    async def list(self, ctx: commands.Context):
        embed = discord.Embed(title="Liste des serveurs Lan-Play",
                              color=discord.Color.blue(), timestamp=datetime.utcnow())
        embed.description = f"Copiez le nom du serveur dont vous souhaitez obtenir des infos puis tapez la commande `{ctx.prefix}{ctx.command.root_parent} <nom_du_serveur>` (en remplacant \"<nom_du_serveur>\" par un des noms ci-dessous) pour obtenir les infos de ce serveur. *Voir l'exemple tout en bas*"

        servers_list = [
            "switch.lan-play.com:11451",
            "frog-skins.com:11451",
            "joinsg.net:11453",
            "lan-play.tk:11451",
            "lanplay.reboot.ms:11451",
            "badswitchlanplay.tk:11451",
            "badps4lanplay.tk:22451",
            "animal--crossing.tk:11452",
            "localhorst.guru:11451",
            "switch.servegame.com:11451",
            "switch-lanyplay-de.ddns.net:11451",
            "cajuina.ddns.net:11451",
            "lanplay.verdandi.icu:11451",
            "stain.ddns.net:11451"
        ]

        for server in servers_list:
            embed.add_field(name=server.split(
                ".")[0].title(), value=f"`{server}`", inline=False)

        embed.set_footer(
            text=f"Ex: {ctx.prefix}{ctx.command.root_parent} lanplay.reboot.ms:11451", icon_url=ctx.guild.icon_url)

        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Common(client))
