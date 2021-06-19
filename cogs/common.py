import asyncio
from logging import error
from math import log
from discord.embeds import EmptyEmbed

from discord.errors import ClientException
from events.functions import *
from discord.ext import commands
from discord.ext.commands.errors import CommandInvokeError, MissingRequiredArgument
from googlesearch import search
from discord import Embed, Colour, Color
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from googletrans import Translator, LANGUAGES
import pythonping
import copy
import aiohttp


class Common(commands.Cog):
    def __init__(self, client: commands.Bot):
        commands.Cog.__init__(self)
        self.client = client

    translator = Translator(
        service_urls=["translate.google.com", "translate.google.fr"])

    def check_author(self, *args):
        def inner(message):
            ctx = args[0]
            return str(message.author.id) == str(
                ctx.author.id) and message.channel == ctx.message.channel and self.not_command(message) == False

    # Commands

    @commands.command(hidden=False, name="owner", brief="Qui est le propriétaire du serveur ?", description="Indique qui est le propriétaire du serveur.")
    async def owner(self, ctx: commands.Context):
        owner = ctx.guild.owner
        await ctx.reply(f"Le propriétaire de {ctx.guild.name} est **{owner.name}#{owner.discriminator}**")

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
        await ctx.reply(f"Pong! (Latence du bot: {round(self.client.latency * 1000)}ms)")

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
        await ctx.reply(invite)
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

    @commands.group(name="suggestion", brief="Soumettez vos suggestions et avis sur le serveur et/ou sur moi-même", description="Permet d'ajouter vos idées de fonctionnalités à ajouter au bot ou au serveur. Vous pouvez aussi soumettre toute idée/critique/suggestion valable.", aliases=["sug", "sugg", "suggest"], invoke_without_command=True)
    async def suggestion(self, ctx: commands.Context):       
        await ctx.reply(f"Pour plus d'informations, taper {ctx.prefix}help suggestion")

    @suggestion.command(name="list", brief="Affiche toutes les suggestions faites par les membres de ce serveur.", aliases=["liste", "l", "li"])
    @commands.cooldown(3, 60)
    async def _list(self, ctx: commands.Context):
        async with self.client.pool.acquire() as con:
            suggestions = await con.fetch('''
            SELECT suggestion, member_id, timestamp
            FROM suggestions
            WHERE guild_id = $1
            ''', ctx.guild.id)

        nb_embeds = (len(suggestions)-1)//25+1
        buttons = [u"\u23EA", u"\u25C0", u"\u25B6", u"\u23E9"]
        current = 0
        embeds = []

        for _ in range(nb_embeds):
            embed = Embed(title=f"Suggestions du serveur {ctx.guild.name}", timestamp=datetime.utcnow(), colour=Color.green())
            embed.set_footer(icon_url=ctx.guild.icon_url)

            for i in range(len(suggestions)):
                print(len(suggestions)-1,i)
                if i%25 == 0 and i != 0:
                    embeds.append(copy.deepcopy(embed))
                    embed.clear_fields()
                else:
                    date = suggestions[i].get('timestamp')
                    embed.add_field(name=f"{ctx.guild.get_member(suggestions[i].get('member_id')).name} le {date.day}/{date.month}/{date.year} à {date.hour}H{date.minute}", value=suggestions[i].get("suggestion"), inline=False)
            
            embeds.append(embed)

        response: discord.Message = await ctx.reply(embed=embeds[current])

        for button in buttons:
            await response.add_reaction(button)

        while True:
            try:
                reaction, user= await self.client.wait_for("reaction_add", check=lambda reaction, user: user == ctx.author and reaction.emoji in buttons, timeout=60.0)
            except asyncio.TimeoutError:
                embed:discord.Embed = embeds[current]
                embed.set_footer(text="Temps écoulé!")
                await response.clear_reactions()
                await response.edit(embed=embeds[current])
            else:
                previous_page = current

                if reaction.emoji == u"\u23EA":
                    current = 0
                elif reaction.emoji == u"\u25C0":
                    if current > 0:
                        current -= 1
                elif reaction.emoji == u"\u25B6":
                    if current < nb_embeds-1:
                        current += 1
                elif reaction.emoji == u"\u23E9":
                    current = nb_embeds-1

                for button in buttons:
                    await response.remove_reaction(button, ctx.author)

                if current != previous_page:
                    await response.edit(embed=embeds[current])
            

    @suggestion.command(name="add", brief="Ajouter une suggestion de fonctionnalité au Bot/Serveur", aliases=["a", "ad"], usage="<votre_suggestion>")
    async def add(self, ctx: commands.Context, *, args=None):
        if not args:
            message = await ctx.reply("Vous pouvez me soumettre votre suggestion, je vous écoute.")
            try:
                response: discord.Message = await self.client.wait_for("message", check=self.check_author(ctx), timeout=180.0)
            except asyncio.TimeoutError:
                await message.edit(f"Temps écoulé {ctx.author.mention}!")
                return
            else:
                args = response.content
        
        async with self.client.pool.acquire() as con:
            await con.execute('''
            INSERT INTO suggestions(guild_id, suggestion, member_id, timestamp)
            VALUES($1, $2, $3, $4)
            ''', ctx.guild.id, args, ctx.author.id, datetime.utcnow())
        
        await ctx.reply("Votre suggestion a bien été prise en compte !")

    @suggestion.command(name="delete", brief="Supprimez une suggestion que vous avez donné sur ce serveur", description="Liste vos suggestions actuelles ainsi que leur numéro et supprimez celles que vous souhaiter en indiquant leurs numéros.", aliases=["d", "de", "del"])
    async def delete(self, ctx: commands.Context, id: int=None):
        if not id:
            async with self.client.pool.acquire() as con:
                suggestions = await con.fetch('''
                SELECT id, suggestion, timestamp
                FROM suggestions
                WHERE guild_id = $1 AND member_id = $2
                ''', ctx.guild.id, ctx.author.id)

            embed = Embed(title=f"Vos suggestions dans le serveur {ctx.guild.name}", timestamp=datetime.utcnow(), colour=Color.orange())

            embed.set_footer(text="Taper exit pour annuler", icon_url=ctx.guild.icon_url)

            for message in suggestions:
                date = message.get('timestamp')
                embed.add_field(name=f"Vous, le {date.day}/{date.month}/{date.year} à {date.hour}H{date.minute}", value=f"{message.get('suggestion')}\n**ID = {message.get('id')}**", inline=False)

            await ctx.reply(embed=embed, content="Merci d'indiquer le numéro d'**ID** correspondant à la suggestion que vous voulez effacer.")

            try:
                message = await self.client.wait_for("message", check=self.check_author(ctx), timeout=120.0)
            except asyncio.TimeoutError:
                await message.edit(f"Temps écoulé {ctx.author.mention}!")
                return
            else:
                try:
                    id = int(message.content)
                except:
                    if message.content == "exit":
                        return

        
        async with self.client.pool.acquire() as con:
            await con.execute('''
            DELETE FROM suggestions
            WHERE member_id = $1 AND id = $2
            ''', ctx.author.id, id)

        await ctx.reply("Votre suggestion a bien été effacée!")


    @commands.group(name="lanplay", aliases=["lan"], brief="Afficher les serveurs Lan-Play", description=f"Indiquez le serveur dont vous voulez afficher les informations, par exemple lanplay.reboot.ms:11451\nPour afficher la liste des serveurs disponibles, tapez la commande `lanplay list`", usage="<url>", invoke_without_command=True)
    async def lanplay(self, ctx: commands.Context, *, url: str = "switch.lan-play.com:11451"):
        embed = Embed(
            title=url, timestamp=datetime.utcnow(), color=Color.red())

        if not url.startswith("http://"):
            url_formated = f"http://{url}/"
        else:
            url_formated = url
        
        if len(url_formated.split(":")) != 3:
            embed.title = None
            embed.description = f"Vous avez oublié d'indiquer le port d'écoute du serveur `{url}`, veuillez l'indiquer de la manière suivante (remplacer `11451` par le port du serveur):\n`{url}:11451`"
            return await ctx.send(embed=embed)


        ping_url = url_formated.replace("http://", "").replace("/", "").split(":")[0]
        try:
            ping = f"{pythonping.ping(ping_url, out=None).rtt_avg_ms} ms"
        except:
            ping = None
        async with ctx.channel.typing():
            try:
                lanplay_status = await getLanplayStatus(url_formated)
            except:
                embed.title = None
                embed.description = "Une erreur est survenue, veuillez réessayer plus tard ou vérifiez d'avoir correctement écrit le nom du serveur.\nPar exemple `switch.lan-play.com:11451` et pas `switch.lan-play.com`."
                embed.set_footer(
                    text=f"Ping: {ping}", icon_url=ctx.guild.icon_url)
                return await ctx.send(embed=embed)

            embed.description = f"{lanplay_status['serverInfo']['online']} :video_game: / {lanplay_status['serverInfo']['idle']} :zzz:"
            embed.set_footer(
                text=f"Ping: {ping}", icon_url=ctx.guild.icon_url)

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
        embed = Embed(title="Liste des serveurs Lan-Play",
                              color=Color.blue(), timestamp=datetime.utcnow())
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

        await ctx.reply(embed=embed)

    @commands.group(name="nsfw", description="Not Safe For Work!")
    async def nsfw(self, ctx: commands.Context):
        if ctx.channel.is_nsfw():
            embed = discord.Embed(color=discord.Color.red())  
            async with aiohttp.ClientSession() as cs:
                async with cs.get('https://www.reddit.com/r/nsfw/new.json?sort=hot') as r:
                    res = await r.json()
                    image = res['data']['children'] [random.randint(0, 25)]['data']
                    embed.title = image['title']
                    embed.description = image["url"]
                    embed.set_image(url=image['url'])
                    await ctx.send(embed=embed)
        else:
            await ctx.reply("Vous ne pouvez taper cette commande que dans un salon NSFW!")


def setup(client):
    client.add_cog(Common(client))
