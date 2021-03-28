from os import error
from assets.Games.dragonball.classes.Skill import Skill
from assets.Games.dragonball.classes.Saiyan import Saiyan
import asyncio
import random
import traceback

import discord
from discord import embeds
from discord.ext import commands
from nltk.chat.util import Chat
from events.functions import *

from assets.Games.Pendu.pendu import *
from assets.Games.Chess.classes.chess import Chess


class Games(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client
        self.game_user = {}
        self.db_path = "./assets/Data/pairs.db"

    def not_command(self, message):
        return message.content.startswith(str(self.client.command_prefix))

    def check_author(self, *args):
        def inner(message):
            ctx = args[0]
            return str(message.author.id) == str(
                ctx.author.id) and message.channel == ctx.message.channel and self.not_command(message) == False

        return inner

    def check_confirm(self, *args):
        def inner(message):
            ctx = args[0]
            return (message.content == "oui" or message.content == "non") and self.check_author(message, ctx)

        return inner

    def check_mention_number(self, *args):
        def inner(message):
            mention_number: int = args[0]
            if len(message.mentions) == mention_number:
                return True
            else:
                return False
        return inner

    async def check_authorized_starters(self, ctx: commands.Context, id_tournament: int):
        connection, cursor = await db_connect()
        authorized_starters = await cursor.execute("SELECT id_starter, is_role FROM authorized_starters WHERE id_tournament = ?", (id_tournament,))
        authorized_starters = await authorized_starters.fetchall()
        await db_close(connection)

        if authorized_starters:
            for id in authorized_starters:
                id_starter = id[0]
                is_role = id[1]
                if is_role == 0 and id_starter == ctx.author.id:
                    return True
                elif is_role == 1 and id_starter in (r.id for r in ctx.author.roles):
                    return True
        return False

    @ commands.command(aliases=['eightball', 'game'], name="8ball", brief="Jouez au célèbre jeu de la boule magique!", description="Tapez la commande suivi de votre question.", usage="<question>")
    async def _8ball(self, ctx, *, question):
        responses = ["Bien sûr!",
                     "Mais oui, t'a cru toi...",
                     "Effectivement.",
                     "Je ne te le fais pas dire!",
                     "Ca m'étonnerait!",
                     "T'es irrécupérable... :facepalm:",
                     "Je te le donne dans le mille Émile!",
                     "Faut arrêter la drogue mon vieux.",
                     "Peut-être que oui, peut-être que non",
                     "Et moi j'ai une question : Quelle est la différence entre un hamburger? :thinking:",
                     "C'est la faute à Philou ça, j'y peux rien !",
                     "Encore et toujours la même réponse: c'est la faute à Philou...",
                     "C'est la faute à Philou!",
                     "Je peux mentir ?",
                     "T'a du cran de poser cette question gamin, aller retourne trier tes cailloux.",
                     "Ah, ça je sais pas! Faut voir ça avec mon supérieur! <@!705704133877039124>"]

        await ctx.send(f"{random.choice(responses)}")

    @ commands.command(hidden=True, brief="Discuter en live avec DogsBot!",
                       description="Discutez sans pression avec DogsBot, pour cela tapez simplement la COMMANDE 'chat'. Vous pouvez maintenant discuter avec lui sans avoir besoin de taper la commande à chaque début de phrase!\n\nSon interaction est pour le moment très limité à de simples bonjour|salut|hey|slt|coucou|wesh|bonsoir|bon matin|hello|hi|cc|hola.\n\nPour quitter la conversation tapez le MOT 'exit'",
                       usage="")
    async def chat(self, ctx: commands.Context, *_input_):

        # Condition pour éviter de lancer plusieurs fils de discussion avec le chatbot
        connection, cursor = await db_connect()
        create(connection, cursor, "chat_table",
               _names=["user"], _type=["INT"])
        user = select(cursor, _select=[
                      "user"], _from="chat_table", _where=f"user={str(ctx.author.id)}")

        if user:
            return await ctx.send(f"Je suis déjà à votre écoute {ctx.author.mention} dans un autre canal!")

        # Définition de la base de données pour le chatbot

        selection = select(
            cursor, _select=["questions", "responses"], _from="pairs", _fetchall=True)
        pairs = []
        for pair in selection:
            element = [pair[0]]
            pair_pop = pair[1].split("|")
            pair_pop.pop()
            element.append(
                pair_pop)
            pairs.append(element)

        chat = Chat(pairs)
        insert(connection, cursor, _into="chat_table",
               _names=["user"], _values=[str(ctx.author.id)])

        while _input_ != "exit":

            message = f"> {_input_}\n{ctx.author.mention} "

            if not _input_:
                await ctx.send(f"{self.client.user.name} à votre écoute, {ctx.author.mention}!")
            else:
                chat_response = chat.respond(str(_input_))
                try:
                    message = message + chat_response
                except Exception as e:
                    await ctx.send(
                        "Je n'ai pas de réponses à votre message, voulez-vous définir une/plusieurs réponses ? *("
                        "**oui**/**non**)*")
                    try:
                        msg_to_confirm = await self.client.wait_for("message", check=self.check_confirm, timeout=120.0)
                    except asyncio.TimeoutError:
                        delete(connection, cursor, _from="chat_table",
                               _where=f"user={str(ctx.author.id)}")
                        await db_close(connection)
                        return await ctx.send(f"Bon, moi je me tire si tu dis rien {ctx.author.mention}!")
                    else:
                        if msg_to_confirm.content == "oui":
                            await ctx.send(
                                f"Veuillez donc entrer une ou plusieurs réponses au message *\"{_input_}\"* avec la syntaxe suivante: `\nréponse_1|réponse_2|réponse_n|...`")
                            msg_to_edit = await self.client.wait_for("message", check=self.check_author(ctx),
                                                                     timeout=300.0)
                            if msg_to_edit.content == "exit":
                                await ctx.send("On verra donc une prochaine fois!")
                            else:
                                insert(connection, cursor, _into="pairs", _names=[
                                       "questions", "responses"], _values=[_input_, msg_to_edit.content])
                                await ctx.send(
                                    f"Les réponses suivantes ont été ajouté au(x) message(s) *\"{_input_}\"*:\n{str(msg_to_edit.content.split('|'))}")
                        elif msg_to_confirm.content == "non":
                            await ctx.send("Ok.")

                else:
                    await ctx.send(message)

            try:
                _input_ = await self.client.wait_for("message", check=self.check_author(ctx), timeout=120.0)
            except asyncio.TimeoutError:
                delete(connection, cursor, _from="chat_table",
                       _where=f"user={str(ctx.author.id)}")
                connection.commit()
                await db_close(connection)
                return await ctx.send(f"Bon, moi je me tire si tu dis rien {ctx.author.mention}!")
            else:
                _input_ = _input_.content

        await ctx.send(f"Merci {ctx.author.name}, à bientôt!")
        delete(connection, cursor, _from="chat_table",
               _where=f"user={str(ctx.author.id)}")
        await db_close(connection)

    @commands.group(hidden=True, name="dragonball", invoke_without_command=True, aliases=["db", "dg", "dragongrall", "dgl", "dbl"])
    async def dragonball(self, ctx: commands.Context):

        welcome_embed = discord.Embed(color=discord.Colour.dark_blue(
        ), title=f"Bienvenue dans Dragon Grall, {ctx.author.display_name}!", timestamp=datetime.datetime.utcnow(), description=f"Tu es arrivé au bon endroit pour commencer à jouer au tout nouveau jeu Dragon Grall développé par Stain!\n(Tips: pour aller plus vite en tapant les commandes, au lieu d'écrire `{ctx.prefix}{ctx.command.name}` tu peux écrire `{ctx.prefix}{f'`, `{ctx.prefix}'.join(ctx.command.aliases[:-1])}` ou `{ctx.prefix}{ctx.command.aliases[-1]}` !)")

        welcome_embed.add_field(
            name="1ère Étape", value=f"Choisis ton personnage en tapant la commande `{ctx.prefix}{ctx.command.name} choice`", inline=False)
        welcome_embed.add_field(
            name="2ème Étape", value=f"Pour voir les caractéristiques de ton personnage tape la commande `{ctx.prefix}{ctx.command.name} player`", inline=False)
        welcome_embed.add_field(
            name="3ème Étape", value=f"Pour démarrer un combat avec un autre joueur du serveur, tape la commande `{ctx.prefix}{ctx.command.name} fight` suivi de ton adversaire. Par exemple si je veux me battre contre le joueur \@xXJeanMichelXx je tape alors la commande `{ctx.prefix}{ctx.command.name} fight @xXJeanMichelXx`")

        welcome_embed.set_author(
            name=f"{ctx.author.display_name}#{ctx.author.discriminator}", icon_url=ctx.author.avatar_url)

        dragon_ball_file = discord.File(
            "assets/Images/Dragonball-Goku.png", filename="dragon_ball.png")
        welcome_embed.set_thumbnail(url="attachment://dragon_ball.png")

        await ctx.send(embed=welcome_embed, file=dragon_ball_file)

    @dragonball.command()
    async def choice(self, ctx: commands.Context, *args):
        args = " ".join(list(args))
        file_characters = "assets/Games/dragonball/assets/characters.json"
        characters_json = read_file(file_characters, is_json=True)

        connection, cursor = await db_connect()
        try:
            player = select(cursor, _select="player_infos", _from="dragonball",
                            _where=f"guild_id = {ctx.guild.id} AND user_id = {ctx.author.id}")
        except:
            pass

        if not args:
            choice_player_embed = discord.Embed(color=discord.Colour.dark_gold(), title="Sélection du personnage",
                                                description="Choisis le personnage que tu veux! Il te suivra durant ton parcours sur Dragon Grall! (Tu pourras le modifier en cours de route)", timestamp=datetime.datetime.utcnow())

            for race in characters_json.values():
                for character in race.values():
                    name = character["name"]
                    skills = character["skills"]
                    character_skills = []
                    for skill_name, skill in skills.items():
                        character_skills.append(skill_name)
                    choice_player_embed.add_field(
                        name=name, value=character_skills, inline=False)

            choice_player_embed.set_author(
                name=f"{ctx.author.display_name}#{ctx.author.discriminator}", icon_url=ctx.author.avatar_url)

            choice_player_embed.set_footer(
                text=f"{ctx.prefix}{self.dragonball.name} {ctx.command.name} <Personnage>")

            dragon_ball_file = discord.File(
                "assets/Images/Dragonball-Goku.png", filename="dragon_ball.png")
            choice_player_embed.set_thumbnail(
                url="attachment://dragon_ball.png")

            await ctx.send(embed=choice_player_embed, file=dragon_ball_file)

        else:
            for race in characters_json.values():
                for character in race.values():
                    name = character["name"]
                    skills = character["skills"]
                    aliases = character["aliases"]
                    if args.lower() == name.lower() or args.lower() in aliases:
                        character_skills = []
                        for skill_name, skill in skills.items():
                            skill = Skill(
                                skill_name, skill["description"], skill["damage"], skill["cost"], skill["style"], skill["self_damage"])
                            character_skills.append(skill)
                        insert(connection, cursor, _into="dragonball", _names=["guild_id", "user_id", "player_infos"], _values=[
                               ctx.guild.id, ctx.author.id, str(Saiyan(ctx, name, character_skills))])
                        await db_close(connection)

    @dragonball.command(hidden=True)
    async def test(self, ctx: commands.Context):
        pass

    @commands.command(name="pendu", brief="Jouez au pendu!",
                      description="""Règles:
                      - Vous avez 8 chances pour trouver un mot pioché aléatoirement!
                      - Après avoir écrit la commande, tapez simplement la lettre que vous pensez qui est dans le mot.
                      - Pour quitter le jeu, écrivez simplement 'exit'.

                      - Optionnel:
                        - Vous pouvez ajouter plusieurs mots de votre choix (maximum 25 lettres dans un mot et sans espaces) avec la syntaxe 'pendu add <nouveau_mot_1> <nouveau_mot_2> <nouveau_mot_n> etc.'.
                        - Vous pouvez choisir la taille max du mot à deviner avec la syntaxe 'pendu taille <nombre_entre_3_et_25_inclus>'""",
                      usage='[add <nouveau_mot> | <nouveau_mot_1> <nouveau_mot_2> ... | taille <nombre_entre_3_et_25_inclus>]')
    async def pendu(self, ctx: commands.Context, *add_word):
        async with ctx.channel.typing():
            await ctx.message.delete()

            from assets.Games.Pendu.fonctions import insert_into_pendu

            connection, cursor = await db_connect()

            if len(add_word) > 0:
                if add_word[0] == "add" and len(add_word) == 2:
                    if await insert_into_pendu(connection, cursor, add_word[1].lower()):
                        await ctx.send(f"{ctx.author.mention} Le mot `{add_word[1]}` a bien été ajoutés parmis tous les autres mots!")
                        msg = f"{ctx.author.name}#{ctx.author.discriminator} a ajouté le mot {add_word[1]} dans la table pendu"
                        write_file(
                            set_file_logs(ctx.guild.id), msg, is_log=True)
                        await get_log_channel(self.client, ctx, msg)

                    else:
                        await ctx.send(f"{ctx.author.mention} Le mot `{add_word[1]}` existe déjà dans ma base de données!")

                    return await db_close(connection)

                elif add_word[0] == "add" and len(add_word) > 2:
                    words = []
                    words_already = []

                    for word in add_word[1:]:
                        if await insert_into_pendu(connection, cursor, word.lower()):
                            words.append(f"`{word}`")

                        else:
                            words_already.append(f"`{word}`")

                    if words_already:
                        if len(words_already) == 1:
                            await ctx.send(f"{ctx.author.mention} Le mot {words_already[0]} existe déjà dans ma base de données!")

                        else:
                            await ctx.send(f"{ctx.author.mention} Les mots {', '.join(words_already[0:-1])} et {words_already[-1]} existent déjà dans ma base de données!")

                    if words:
                        if len(words) == 1:
                            await ctx.send(f"{ctx.author.mention} Le mot {words[0]} a bien été ajouté parmis tous les autres mots!")

                        else:
                            await ctx.send(f"{ctx.author.mention} Les mots {', '.join(words[:-1])} et {words[-1]} ont bien été ajoutés parmis tous les autres mots!")

                        msg = f"{ctx.author.name}#{ctx.author.discriminator} a ajouté les mots {words} dans la table pendu"
                        write_file(
                            set_file_logs(ctx.guild.id), msg, is_log=True)
                        await get_log_channel(self.client, ctx, msg)

                    return await db_close(connection)

                elif add_word[0] == "del" and len(add_word) == 2 and ctx.channel.permissions_for(ctx.author).administrator:
                    if delete_from_pendu(connection, cursor, add_word[1].lower()):
                        await ctx.send(f"{ctx.author.mention} Le mot `{add_word[1]}` a bien été supprimé!")
                        msg = f"{ctx.author.name}#{ctx.author.discriminator} a retiré le mot {add_word[1]} dans la table pendu"
                        write_file(
                            set_file_logs(ctx.guild.id), msg, is_log=True)
                        await get_log_channel(self.client, ctx, msg)

                    else:
                        await ctx.send(
                            f"{ctx.author.mention} Le mot {add_word[1]} n'existe pas dans ma base de données! Je ne peux donc pas le supprimer!")

                    return await db_close(connection)

                elif add_word[0] == "del" and len(add_word) > 2 and ctx.channel.permissions_for(ctx.author).administrator:
                    words = []
                    words_not_exists = []

                    for word in add_word[1:]:
                        if delete_from_pendu(connection, cursor, word.lower()):
                            words.append(f"`{word}`")

                        else:
                            words_not_exists.append(f"`{word}`")

                    if words_not_exists:
                        if len(words_not_exists) == 1:
                            await ctx.send(f"{ctx.author.mention} Le mot {words_not_exists[0]} n'existe pas dans ma base de données! Je ne peux donc pas le supprimer!")

                        else:
                            await ctx.send(f"{ctx.author.mention} Les mots {', '.join(words_not_exists[0:-1])} et {words_not_exists[-1]} n'existent pas dans ma base de données! Je ne peux donc pas les supprimer!")

                    if words:
                        if len(words) == 1:
                            await ctx.send(f"{ctx.author.mention} Le mot {words[0]} a bien été supprimé de la liste des mots!")

                        else:
                            await ctx.send(f"{ctx.author.mention} Les mots {', '.join(words[:-1])} et {words[-1]} ont bien été supprimés de la liste des mots!")

                        msg = f"{ctx.author.name}#{ctx.author.discriminator} a ajouté les mots {words} dans la table pendu"
                        write_file(
                            set_file_logs(ctx.guild.id), msg, is_log=True)
                        await get_log_channel(self.client, ctx, msg)

                    return await db_close(connection)

        set_pendu(self, ctx, connection, cursor)
        user_pendu: Pendu = self.game_user[ctx.author.id]
        set_taille_message = None

        if len(add_word) > 0:
            if add_word[0] == "taille" and int(add_word[1]) in range(3, 26, 1):
                user_pendu.taille_mot = int(add_word[1])
                set_taille_message = await ctx.send(f"{ctx.author.mention}Taille choisie: {int(add_word[1])}")
                user_pendu.mot = word_init(
                    connection, cursor, user_pendu.taille_mot)
                user_pendu.chances = len(user_pendu.mot)

            elif add_word[0] == "taille" and not int(add_word[1]) in range(3, 26, 1):
                set_taille_message = await ctx.send(
                    f"""{ctx.author.mention}`Taille invalide` (doit se situer entre 3 et 25)\nTaille du mot par défaut: `8`""")

        await user_pendu.set_mot()

        while user_pendu.is_running:

            if not user_pendu.message_to_delete:
                user_pendu.message_to_delete = await ctx.send(f"Veuillez entrer une lettre {ctx.author.mention}")

            try:
                lettre = await self.client.wait_for("message", check=self.check_author(ctx), timeout=120.0)

            except asyncio.TimeoutError:
                await ctx.send(f"{ctx.author.mention} Temps écoulé!")
                break

            else:
                if set_taille_message:
                    await set_taille_message.delete()
                    set_taille_message = None

                if lettre.content == "exit":
                    await user_pendu.message_to_delete.delete()
                    await lettre.delete()
                    user_pendu.is_running = False
                    break

            await user_pendu.message_to_delete.delete()
            await lettre.delete()

            await user_pendu.running(lettre.content.lower())

            if user_pendu.is_find or user_pendu.is_over:
                try:
                    user_quit = await self.client.wait_for("message", check=self.check_author(ctx), timeout=120.0)

                except asyncio.TimeoutError:
                    await ctx.send(f"{ctx.author.mention} Temps écoulé!")
                    break

                retry = await user_pendu.retry(user_quit.content.lower())

                if retry == "o":
                    await user_pendu.message_to_delete.delete()
                    await user_quit.delete()
                    user_pendu.__init__(ctx, connection, cursor)
                    user_pendu.user_chances = 0
                    await user_pendu.set_mot()

                    if len(add_word) > 0:
                        if add_word[0] == "taille" and int(add_word[1]) in range(3, 26, 1):
                            user_pendu.taille_mot = int(add_word[1])

                elif retry == "n":
                    await user_pendu.message_to_delete.delete()
                    await user_quit.delete()

        await db_close(connection)
        self.game_user[ctx.author.id] = None
        msg = f"{ctx.author.display_name}#{ctx.author.discriminator} a joué au pendu dans le salon {ctx.channel.name}!"
        write_file(
            set_file_logs(ctx.guild.id), msg, is_log=True)
        await get_log_channel(self.client, ctx, msg)

    @commands.command(hidden=True, name="demineur", aliases=["mine", "minesweeper"])
    async def demineur(self, ctx: commands.Context, *args):
        pass

    @commands.group(hidden=True, name="echecs", aliases=["echec", "chess"])
    async def echecs(self, ctx: commands.Context, *args):
        try:
            chess = Chess(
                ctx.message.mentions[0], ctx.message.mentions[1], self, ctx)
        except error as er:
            print(er)
            return await ctx.send("Veuillez mentionner le premier et le second joueur.")
        await ctx.send(chess.get_chess_board())

    @ commands.group(name="tournoi", aliases=["tournois", "tounrois", "tounroi", "tournament", "competition"], brief="Lister les tournois disponibles", invoke_without_command=True)
    async def tournoi(self, ctx: commands.Context):

        """
        tournaments(
            id INTEGER PRIMARY KEY UNIQUE,
            guild_id INT,
            id_tournament TEXT,
            title TEXT,
            description TEXT,
            rules TEXT,
            reward TEXT,
            date TEXT,
            nb_max_participants INT,
            nb_participants INT,
            classement TEXT,
            start INT,
            finish INT,
            rounds INT
            )

        tournament_participants(
            id INTEGER PRIMARY KEY UNIQUE,
            id_tournament TEXT,
            id_participant INT,
            score INT
            )

        authorized_starters(
            id INTEGER PRIMARY KEY UNIQUE,
            id_tournament TEXT,
            id_starter INT,
            is_role INT
            )
        """

        embed = discord.Embed()
        embed.title = "Tournois en cours"
        embed.description = f"Liste des tournois en cours | `{ctx.prefix}tournoi more <ID_du_tournoi>` pour plus d'informations"
        embed.color = discord.Color.greyple()
        connection, cursor = await db_connect()

        await cursor.execute(f"""CREATE TABLE IF NOT EXISTS tournaments(
            id INTEGER PRIMARY KEY UNIQUE,
            guild_id INT,
            id_tournament TEXT,
            title TEXT,
            description TEXT,
            rules TEXT,
            reward TEXT,
            date TEXT,
            nb_max_participants INT,
            nb_participants INT,
            classement TEXT,
            start INT,
            finish INT,
            rounds INT
            )
            """)

        await cursor.execute(f"""CREATE TABLE IF NOT EXISTS tournament_participants(
            id INTEGER PRIMARY KEY UNIQUE,
            id_tournament TEXT,
            id_participant INT,
            score INT
            )
            """)

        await cursor.execute(f"""CREATE TABLE IF NOT EXISTS authorized_starters(
            id INTEGER PRIMARY KEY UNIQUE,
            id_tournament TEXT,
            id_starter INT,
            is_role INT
            )""")

        await connection.commit()

        write_file(log_file, "La table tournaments a été créée!", is_log=True)
        write_file(
            log_file, "La table tournament_participants a été créée!", is_log=True)
        write_file(
            log_file, "La table authorized_starters a été créée!", is_log=True)

        # List of tournaments
        tournaments = await cursor.execute(
            "SELECT id_tournament, title, date, nb_max_participants, nb_participants FROM tournaments WHERE guild_id = ?", (ctx.guild.id,))
        tournaments = await tournaments.fetchall()

        for tournament in tournaments:
            embed.add_field(
                name=tournament[1].title(), value=f"__**ID:**__ `{tournament[0]}`\n__**Date début:**__ {tournament[2]}")

        # Check if ctx.author is registered into a tournament
        into_tournament = await cursor.execute(
            "SELECT DISTINCT id_participant, id_tournament FROM tournament_participants WHERE id_participant = ?", (ctx.author.id,))
        into_tournament = await into_tournament.fetchone()

        if into_tournament:

            for i in tournaments:

                if into_tournament[1] == i[0]:
                    current_tournament = await cursor.execute(
                        "SELECT id_tournament, title FROM tournaments WHERE guild_id = ? AND id_tournament = ?", (ctx.guild.id, into_tournament[1]))
                    current_tournament = await current_tournament.fetchone()
                    embed.add_field(name=f":white_check_mark: Vous êtes inscrit au tournoi {current_tournament[1].title()} :white_check_mark: ",
                                    value=f"`{current_tournament[0]}`", inline=False)

        await db_close(connection)

        embed.timestamp = datetime.datetime.utcnow()
        embed.set_footer(
            text=f"Pour rejoindre un tournoi, veuillez simplement écrire l'id du tournoi souhaité. Si ça ne fonctionne pas, retapez la commande {ctx.prefix}tournoi pour afficher la liste puis entrez à nouveau l'id correspondant.", icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(url=ctx.guild.icon_url)

        message = await ctx.send(embed=embed)

        try:
            new_participant: discord.Message = await self.client.wait_for("message", check=self.check_author, timeout=120.0)
        except asyncio.TimeoutError:
            pass
        else:
            await new_participant.delete()
            connection, cursor = await db_connect()
            tournament = await cursor.execute(
                "SELECT DISTINCT id_tournament, title, nb_max_participants, nb_participants FROM tournaments WHERE guild_id = ? AND id_tournament = ?", (ctx.guild.id, new_participant.content))
            tournament = await tournament.fetchone()

            embed = discord.Embed(
                title="Inscription Tournoi", timestamp=datetime.datetime.utcnow(), color=discord.Color.green())
            embed.set_footer(
                text=f"Tapez la commande {ctx.prefix}tournoi pour voir les tournois créés.", icon_url=ctx.author.avatar_url)

            # If ctx.author is registered into a tournament
            if into_tournament:
                current_tournament = await cursor.execute(
                    "SELECT DISTINCT nb_participants FROM tournaments WHERE id_tournament = ?", (into_tournament[1],))
                current_tournament = await current_tournament.fetchone()

            if not tournament:
                await db_close(connection)
                return
            elif tournament[2] == tournament[3]:
                embed.color = discord.Color.red()
                embed.description = "Tournoi complet!"
                await db_close(connection)
                return await message.edit(embed=embed)

            elif await(await cursor.execute("SELECT DISTINCT id FROM tournament_participants WHERE id_tournament = ? AND id_participant = ?", (tournament[0], ctx.author.id))).fetchone() != None:
                embed.description = f"Vous êtes déjà inscrit au tournoi __**{tournament[1].title()}**__ {ctx.author.mention}!\n\n*Pour changer de tournoi, vous pouvez simplement taper l'id d'un autre tournoi (après avoir tapé la commande `{ctx.prefix}tournoi`) ou taper la commande `{ctx.prefix}tournoi leave` pour quitter le tournoi auquel vous êtes actuellement inscrit!*"

            elif into_tournament != None:
                await cursor.execute(
                    "UPDATE tournament_participants SET id_tournament = ?, score = 0 WHERE id_participant = ?", (tournament[0], ctx.author.id))
                await cursor.execute(
                    "UPDATE tournaments SET nb_participants = ? WHERE id_tournament = ?", (current_tournament[0]-1, into_tournament[1]))
                await cursor.execute(
                    "UPDATE tournaments SET nb_participants = ? WHERE id_tournament = ?", (tournament[3]+1, tournament[0]))
                await connection.commit()
                embed.description = f"Félicitations {ctx.author.mention}, vous vous êtes inscrit au tournoi __**{tournament[1].title()}**__\n\n*Pour changer de tournoi, vous pouvez simplement taper l'id d'un autre tournoi (après avoir tapé la commande `{ctx.prefix}tournoi`) ou taper la commande `{ctx.prefix}tournoi leave` pour quitter le tournoi auquel vous êtes actuellement inscrit!*"

            else:
                await cursor.execute("INSERT INTO tournament_participants(id_tournament, id_participant, score) VALUES(?, ?, 0)",
                                     (tournament[0], ctx.author.id))
                await cursor.execute(
                    "UPDATE tournaments SET nb_participants = ? WHERE id_tournament = ?", (tournament[3]+1, tournament[0]))
                embed.description = f"Félicitations {ctx.author.mention}, vous vous êtes inscrit au tournoi __**{tournament[1].title()}**__!\n\n*Pour changer de tournoi, vous pouvez simplement taper l'id d'un autre tournoi (après avoir tapé la commande `{ctx.prefix}tournoi`) ou taper la commande `{ctx.prefix}tournoi leave` pour quitter le tournoi auquel vous êtes actuellement inscrit!*"
                await connection.commit()

            await db_close(connection)

        await message.edit(embed=embed)

    @ tournoi.command(name="create", brief="Créer un tournoi", description="Indiquez tous les paramètres du tournoi après avoir tapé la commande tournoi create.\nParamètres disponibles:\n- Nom du tournoi\n- Description du tournoi *(par défaut: `NONE`)*\n- Récompense du tournoi *(par défaut: `NONE`)*\n- Nombre maximum de participants *(par défaut: `8`)*")
    @ commands.has_permissions(manage_messages=True)
    async def create(self, ctx: commands.Context):

        names = {"title": "Nom du tournoi", "description": "Description du tournoi *(par défaut: `NONE`)*", "rules": "Règles du tournoi", "reward": "Récompense du tournoi *(par défaut: `NONE`)*",
                 "date": "Date/Heure du début du tournoi *(Format de la date : `jj/mm/aa HH:MM` Ex: `25/06/21 15:00`)*", "nb_max_participants": "Nombre maximum de participants *(par défaut: `8`)*", "authorized_starters": f"Membres ou/et rôles autorisés à démarrer un tournoi, l'arrêter et modifier le classement *(par défaut: {ctx.author.mention})*", "rounds": "Nombre de manches du tournoi *(par défaut: `4`)*"}

        id_tournament = random_string(8)

        embed = discord.Embed(
            title="Tournoi créé", timestamp=datetime.datetime.utcnow(), color=discord.Color.greyple())

        temp_embed = discord.Embed(
            timestamp=datetime.datetime.utcnow(), color=discord.Color.greyple())

        connection, cursor = await db_connect()

        message = await ctx.send(embed=temp_embed)

        for key, value in names.items():

            temp_embed.description = f"{ctx.author.mention}, Veuillez indiquer le paramètre suivant: \n**{value}**"
            await message.edit(embed=temp_embed)
            try:
                name: discord.Message = await self.client.wait_for("message", check=self.check_author, timeout=120.0)
            except asyncio.TimeoutError:
                temp_embed.description = f"Temps écoulé {ctx.author.mention}!\nCommande annulée."
                await message.edit(embed=temp_embed)
                return
            else:
                await name.delete()
                temp_name = name
                name = name.content

                if key == "date":
                    try:
                        datetime.datetime.strptime(name, dateFormatter)
                    except:
                        temp_embed.description = f"Erreur de conversion, veuillez entrer une date du type `jj/mm/aa HH:MM` après avoir retapé la commande `{ctx.prefix}{ctx.command.qualified_name}`"
                        await message.edit(embed=temp_embed)
                        await db_close(connection)
                        return

                if key == "authorized_starters" and temp_name.mentions != None:
                    for autorized_starter in temp_name.mentions:
                        await cursor.execute("INSERT INTO authorized_starters(id_tournament, id_starter, is_role) VALUES(?, ?, 0)", (id_tournament, autorized_starter.id,))
                if key == "authorized_starters" and temp_name.role_mentions != None:
                    for autorized_starter in temp_name.role_mentions:
                        await cursor.execute("INSERT INTO authorized_starters(id_tournament, id_starter, is_role) VALUES(?, ?, 1)", (id_tournament, autorized_starter.id,))

                # Création du tournoi si celui-ci n'existe pas déjà
                elif await(await cursor.execute("SELECT DISTINCT id FROM tournaments WHERE id_tournament = ?", (id_tournament,))).fetchone() == None:
                    await cursor.execute(f"INSERT INTO tournaments(guild_id, id_tournament, nb_max_participants, nb_participants, start, finish, rounds, {key}) VALUES(?, ?, 8, 0, 0, 0, 1, ?)",
                                         (ctx.guild.id, id_tournament, name))
                else:
                    await cursor.execute(
                        f"UPDATE tournaments SET {key} = ? WHERE guild_id = ? AND id_tournament = ?", (name, ctx.guild.id, id_tournament))
                embed.add_field(
                    name=value, value=name, inline=False)
        await connection.commit()
        await db_close(connection)

        embed.set_footer(
            text=f"Tapez la commande {ctx.prefix}tournoi pour voir les tournois créés.", icon_url=ctx.author.avatar_url)

        await message.edit(embed=embed)

        write_file(
            log_file, "Des données ont été inséré dans la table tournaments!", is_log=True)

    @ tournoi.command(name="delete", brief="Supprimer un tournoi", usage="<id_du_tournoi>")
    async def delete(self, ctx: commands.Context):

        embed = discord.Embed(color=discord.Color.red(),
                              timestamp=datetime.datetime.utcnow())

        embed.description = f"Quel est l'id du tournoi à supprimer {ctx.author.mention} ?'"
        message = await ctx.send(embed=embed)
        try:
            id: discord.Message = await self.client.wait_for("message", check=self.check_author(ctx), timeout=120.0)
        except asyncio.TimeoutError:
            embed.description = f"Temps écoulé {ctx.author.mention} !"
            await message.edit(embed=embed)
            return
        else:
            await id.delete()
            id = id.content

        # Vérifie que l'auteur de l'appel de la commande peut supprimer le tournoi
        if not await self.check_authorized_starters(ctx, id):
            embed.description = f"Vous ne pouvez pas supprimer ce tournoi, {ctx.author.mention} !"
            await message.edit(embed=embed)
            return

        connection, cursor = await db_connect()
        tournament = await cursor.execute(
            "SELECT id_tournament, title FROM tournaments WHERE guild_id = ? AND id_tournament = ?", (ctx.guild.id, id))
        tournament = await tournament.fetchone()
        await cursor.execute(
            "DELETE FROM tournaments WHERE guild_id = ? AND id_tournament = ?", (ctx.guild.id, id))
        await connection.commit()
        await cursor.execute(
            "DELETE FROM tournament_participants WHERE id_tournament = ?", (id,))
        await cursor.execute("DELETE FROM authorized_starters WHERE id_tournament = ?", (id,))
        await connection.commit()
        await db_close(connection)

        embed = discord.Embed(
            title="Tournoi supprimé", timestamp=datetime.datetime.utcnow(), color=discord.Color.red())
        embed.add_field(
            name=tournament[1].title(), value=f"`{tournament[0]}`")
        embed.set_footer(
            text=f"Tapez la commande {ctx.prefix}tournoi pour voir les tournois créés.", icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

        write_file(
            log_file, "Des données ont été supprimé dans la table tournaments!", is_log=True)

    @ tournoi.command(name="leave", brief="Quitter un tournoi", usage="<id_du_tournoi>")
    async def leave(self, ctx: commands.Context):

        connection, cursor = await db_connect()

        embed = discord.Embed(
            title="Quitter un Tournoi", timestamp=datetime.datetime.utcnow(), color=discord.Color.orange())
        embed.set_footer(
            text=f"Tapez la commande {ctx.prefix}tournoi pour voir les tournois créés.", icon_url=ctx.author.avatar_url)

        current_tournament = await cursor.execute(
            "SELECT DISTINCT id_tournament, id_participant FROM tournament_participants WHERE id_participant = ?", (ctx.author.id,))
        current_tournament = await current_tournament.fetchone()

        if not current_tournament:
            embed.description = f"Vous n'êtes actuellement inscrit à aucun tournoi {ctx.author.mention}."

        await cursor.execute(
            "DELETE FROM tournament_participants WHERE id_participant = ?", (ctx.author.id,))
        await cursor.execute("UPDATE tournament_participants SET score = 0 WHERE id_participant = ?", (ctx.author.id,))
        await connection.commit()
        tournament = await cursor.execute(
            "SELECT title FROM tournaments WHERE id_tournament = ?", (current_tournament[0],))
        tournament = await tournament.fetchone()
        await db_close(connection)

        embed.description = f"Vous venez de quitter le tournoi __**{tournament[0].title()}**__ {ctx.author.mention}!"

        await ctx.send(embed=embed)

    @ tournoi.command(name="more", brief="Afficher plus de détails sur un tournoi")
    async def more(self, ctx: commands.Context):

        names = {"title": "Nom du tournoi", "description": "Description du tournoi", "date": "Date du début du tournoi", "rounds": "Nombre de manches avant de savoir qui a gagné le tournoi !", "reward": "Récompense du tournoi",
                 "nb_max_participants": "Nombre maximum de participants", "nb_participants": "Nombre actuel de participants", "start": "Tournoi commencé", "finish": "Tournoi terminé", "id_tournament": "Identifiant unique du tournoi"}

        embed = discord.Embed(timestamp=datetime.datetime.utcnow(),
                              color=discord.Color.greyple())
        embed.set_footer(
            text=f"Pour rejoindre le tournoi, tapez la commande {ctx.prefix}tournoi pour afficher la liste des tournois puis tapez l'id d'un tournoi", icon_url=ctx.author.avatar_url)

        embed.description = f"Quel est l'id du tournoi {ctx.author.mention}?"
        message = await ctx.send(embed=embed)
        try:
            id: discord.Message = await self.client.wait_for("message", check=self.check_author(ctx), timeout=120.0)
        except asyncio.TimeoutError:
            await message.edit(f"Temps écoulé {ctx.author.mention}!")
            return
        else:
            await id.delete()
            id = id.content
            embed.description = None

        connection, cursor = await db_connect()

        tournament_check = await cursor.execute(
            "SELECT DISTINCT title FROM tournaments WHERE guild_id = ? AND id_tournament = ?", (ctx.guild.id, id))
        tournament_check = await tournament_check.fetchone()

        if tournament_check == None:
            embed.description = f"Mauvais ID entré, ou tournoi inexistant, veuillez réessayer {ctx.author.mention}!"
            await db_close(connection)
            return await message.edit(embed=embed)

        embed.title = f"Détails du tournoi {tournament_check[0].title()}"

        for key, value in names.items():
            details_tournament = await cursor.execute(
                f"SELECT DISTINCT {key} FROM tournaments WHERE guild_id = ? AND id_tournament = ?", (ctx.guild.id, id))
            details_tournament = (await details_tournament.fetchone())[0]
            embed.add_field(
                name=value, value=details_tournament, inline=False)

        await db_close(connection)

        await message.edit(embed=embed)

    @ tournoi.command(name="start", brief="Démarrer un tournoi")
    async def start(self, ctx: commands.Context):

        embed = discord.Embed()
        embed.color = discord.Color.green()
        embed.timestamp = datetime.datetime.utcnow()

        embed.description = f"Quel est l'id du tournoi {ctx.author.mention}?"
        message = await ctx.send(embed=embed)
        try:
            id: discord.Message = await self.client.wait_for("message", check=self.check_author(ctx), timeout=120.0)
        except asyncio.TimeoutError:
            embed.description = f"Temps écoulé {ctx.author.mention}!"
            await message.edit(embed=embed)
            return
        else:
            await id.delete()
            id = id.content

        # Vérifie que l'auteur de l'appel de la commande peut démarrer le tournoi
        if not await self.check_authorized_starters(ctx, id):
            embed.description = f"Vous ne pouvez pas démarrer ce tournoi, {ctx.author.mention} !"
            await message.edit(embed=embed)
            return

        connection, cursor = await db_connect()

        # tournament = [id_tournament, title, description, reward, nb_participants, start, finish]
        tournament = await cursor.execute(
            "SELECT id_tournament, title, description, reward, nb_participants, start, finish, rounds FROM tournaments WHERE guild_id = ? AND id_tournament = ?", (ctx.guild.id, id))
        tournament = await tournament.fetchone()

        tournament_participants = await cursor.execute("SELECT id_participant FROM tournament_participants WHERE id_tournament = ?", (tournament[0],))
        tournament_participants = await tournament_participants.fetchall()

        await db_close(connection)

        if tournament == None:
            embed.description = f"Mauvais ID entré, ou tournoi inexistant, veuillez réessayer {ctx.author.mention}!"
            return await message.edit(embed=embed)

        elif tournament_participants == None:
            embed.description = f"Personne ne s'est inscrit au tournoi, {ctx.author.mention}!"
            return await message.edit(embed=embed)

        elif tournament[5] == 1:
            embed.description = f"Le tournoi a déjà commencé, {ctx.author.mention}!"
            return await message.edit(embed=embed)

        elif tournament[6] == 1:
            embed.description = f"Le tournoi est terminé, {ctx.author.mention}!"
            return await message.edit(embed=embed)

        embed.title = f"Le tournoi \"{tournament[1].title()}\" va commencer !"
        embed.description = tournament[2] + "\n\n**Attribution des points:** Le nombre de points max que vous pouvez gagner correspond au nombre de participants. Par exemple s'il y a 8 joueurs dans le tournoi, si vous arrivez 1er à la première manche alors vous obtiendrez 8 points, si vous arrivez 5e alors vous gagnerez 3 points, 8e vous obtiendrez 0 point."
        embed.set_footer(
            text=f"Score accessible via la commande {ctx.prefix}tournoi score {tournament[0]}")
        embed.add_field(name="Nombre de participants",
                        value=f"`{tournament[4]}`", inline=False)
        embed.add_field(
            name="Manches", value=f"`{tournament[7]}`", inline=False)
        embed.add_field(name="Participants", value="\n".join(
            f"<@{participant[0]}>" for participant in tournament_participants) or "Personne n'est inscrit !", inline=False)
        embed.add_field(name="Récompense",
                        value=f"`{tournament[3]}`", inline=False)

        connection, cursor = await db_connect()

        await cursor.execute("UPDATE tournaments SET start = 1 WHERE guild_id = ? AND id_tournament = ?", (ctx.guild.id, tournament[0]))
        await connection.commit()
        await db_close(connection)

        await message.edit(content=", ".join(
            f"<@{participant[0]}>" for participant in tournament_participants) + ", préparez-vous !", embed=embed)

        try:
            await ctx.author.send(f"Pour définir les points procédez de la manière suivante:\n- Tapez la commande `{ctx.prefix}tournoi score add`\n- Mentionnez les joueurs, du premier au dernier. Par exemple tapez `{ctx.prefix}tournoi score add @joueur1 @joueur2 @joueur3 ...`\n\nFaites attention à ne pas oublier un joueur! Sinon la commande n'aboutira pas!\n\n*A écrire dans le salon {ctx.channel.mention}*")
        except:
            await ctx.send(f"{ctx.author.mention}, pour définir les points procédez de la manière suivante:\n- Tapez la commande `{ctx.prefix}tournoi score add`\n- Mentionnez les joueurs, du premier au dernier. Par exemple tapez `{ctx.prefix}tournoi score add @joueur1 @joueur2 @joueur3 ...`\n\nFaites attention à ne pas oublier un joueur! Sinon la commande n'aboutira pas!")

    @tournoi.group(name="score", brief="Afficher le classement d'un tournoi", description="Indiquez l'id d'un tournoi qui a commencé afin d'afficher le classement des joueurs.\nSeul celui qui a lancé le tournoi peut modifier le classement.", aliases=["classement"], invoke_without_command=True)
    async def score(self, ctx: commands.Context):

        embed = discord.Embed()
        embed.color = discord.Color.green()
        embed.timestamp = datetime.datetime.utcnow()

        connection, cursor = await db_connect()
        embed.description = f"Quel est l'id du tournoi {ctx.author.mention}?"
        message = await ctx.send(embed=embed)
        try:
            id: discord.Message = await self.client.wait_for("message", check=self.check_author(ctx), timeout=120.0)
        except asyncio.TimeoutError:
            embed.description = f"Temps écoulé {ctx.author.mention}!"
            await message.edit(embed=embed)
            await db_close(connection)
            return
        else:
            await id.delete()
            id = id.content
            embed.description = None

        # tournament = [id_tournament, title, description, reward, nb_participants, start, finish]
        tournament = await cursor.execute(
            "SELECT id_tournament, title, description, reward, nb_participants, start, finish, rounds, classement FROM tournaments WHERE guild_id = ? AND id_tournament = ?", (ctx.guild.id, id))
        tournament = await tournament.fetchone()

        tournament_participants = await cursor.execute("SELECT id_participant, score FROM tournament_participants WHERE id_tournament = ?", (tournament[0],))
        tournament_participants = await tournament_participants.fetchall()

        if tournament == None:
            await db_close(connection)
            embed.description = f"Mauvais ID entré, ou tournoi inexistant, veuillez réessayer {ctx.author.mention}!"
            return await message.edit(embed=embed)

        elif tournament[5] == 0:
            await db_close(connection)
            embed.description = f"Le tournoi n'a pas encore commencé !"
            return await message.edit(embed=embed)

        elif tournament[6] == 1:
            await db_close(connection)
            embed.description = f"Le tournoi est terminé ! Voici le résultat final"

        embed.title = f"Voici le classement du tournoi \"{tournament[1].title()}\" !"
        if not embed.description:
            embed.description = tournament[2] + "\n\n**Attribution des points:** Le nombre de points max que vous pouvez gagner correspond au nombre de participants. Par exemple s'il y a 8 joueurs dans le tournoi, si vous arrivez 1er à la première manche alors vous obtiendrez 8 points, si vous arrivez 5e alors vous gagnerez 3 points, 8e vous obtiendrez 0 point."
        embed.set_footer(
            text=f"Ce message sera mis à jour à chaque fois qu'une manche sera terminée")
        embed.add_field(name="Nombre de participants",
                        value=f"`{tournament[4]}`", inline=False)
        embed.add_field(name="Participants", value="\n".join(
            f"<@{participant[0]}> (*score:* `{participant[1]}`)" for participant in tournament_participants) or "Personne n'est inscrit !", inline=False)
        embed.add_field(name="Manches", value=f"`{tournament[7]}`")
        embed.add_field(name="Récompense",
                        value=f"`{tournament[3]}`", inline=False)
        embed.add_field(
            name="Classement", value=tournament[8] or "Pas de classement pour le moment !", inline=False)

        await message.edit(embed=embed)
        await db_close(connection)

    @score.command(name="add", brief="Indiquer le classement par manche", usage="<id_du_tournoi>")
    async def add(self, ctx: commands.Context):

        embed = discord.Embed()
        embed.color = discord.Color.green()
        embed.timestamp = datetime.datetime.utcnow()

        embed.description = f"Quel est l'id du tournoi {ctx.author.mention}?"
        message = await ctx.send(embed=embed)
        try:
            id: discord.Message = await self.client.wait_for("message", check=self.check_author(ctx), timeout=120.0)
        except asyncio.TimeoutError:
            embed.description = f"Temps écoulé {ctx.author.mention}!"
            await message.edit(embed=embed)
            return
        else:
            await id.delete()
            id = id.content
            embed.description = None

        # Vérifie que l'auteur de l'appel de la commande peut mmodifier le tournoi
        if not await self.check_authorized_starters(ctx, id):
            embed.description = f"Vous ne pouvez pas modifier ce tournoi, {ctx.author.mention} !"
            await message.edit(embed=embed)
            return

        connection, cursor = await db_connect()

        # tournament = [id_tournament, title, description, reward, nb_participants, start, finish]
        tournament = await cursor.execute(
            "SELECT id_tournament, title, description, reward, nb_participants, start, finish, rounds FROM tournaments WHERE guild_id = ? AND id_tournament = ?", (ctx.guild.id, id))
        tournament = await tournament.fetchone()

        tournament_participants = await cursor.execute("SELECT id_participant FROM tournament_participants WHERE id_tournament = ?", (tournament[0],))
        tournament_participants = await tournament_participants.fetchall()
        await db_close(connection)

        if tournament == None:
            embed.description = f"Mauvais ID entré, ou tournoi inexistant, veuillez réessayer {ctx.author.mention}!"
            return await message.edit(embed=embed)

        elif tournament[5] == 0:
            embed.description = f"Le tournoi n'a pas encore commencé !"
            return await message.edit(embed=embed)

        elif tournament[6] == 1:
            embed.description = f"Le tournoi est terminé ! Pour voir le résultat final, tapez la commande `{ctx.prefix}tournoi score {tournament[0]}`"
            return await message.edit(embed=embed)

        for round in range(tournament[7]):
            embed.description = f"Veuillez indiquer le classement des joueurs pour la manche **{round+1}**"
            await message.edit(embed=embed)
            try:
                classement = await self.client.wait_for("message", check=self.check_author(ctx) and self.check_mention_number(tournament[4]))
            except:
                await message.edit(f"{ctx.author.mention}, une erreur est survenue! Pour pouvoir indiquer le classement à nouveau, merci d'écrire la commande `{ctx.prefix}tournoi score` puis vous pourrez ensuite écrire le classement des joueurs!")
                return
            else:
                await classement.delete()

            participants_mentions = classement.mentions

            connection, cursor = await db_connect()
            for participant in participants_mentions:
                await cursor.execute("UPDATE tournament_participants SET score = score + ? WHERE id_participant = ?", (tournament[4] - (participants_mentions.index(participant)), participant.id))
            await connection.commit()

            participants_scores = await cursor.execute("SELECT id_participant, score FROM tournament_participants WHERE id_tournament = ?", (tournament[0],))
            participants_scores = await participants_scores.fetchall()
            participants_scores = sorted(
                participants_scores, key=lambda x: x[1], reverse=True)

            await cursor.execute("UPDATE tournaments SET classement = ? WHERE guild_id = ? AND id_tournament = ?", ("\n".join(f"__**{participants_scores.index(p)+1} place:**__ <@{p[0]}> (*score:* `{p[1]}`" for p in participants_scores), ctx.guild.id, tournament[0]))
            await connection.commit()

            leaderboard = await cursor.execute("SELECT classement FROM tournaments WHERE guild_id = ? AND id_tournament = ?", (ctx.guild.id, tournament[0]))
            leaderboard = await leaderboard.fetchone()
            await db_close(connection)

            embed.clear_fields()
            embed.add_field(name="Classement", value=leaderboard[0])

            await message.edit(embed=embed)

        embed.description = f"Tapez la commande `{ctx.prefix}tournoi fin` puis entrez l'id du tournoi pour voir le score final !"
        embed.title = "Tournoi terminé !"
        await message.edit(embed=embed)

    @tournoi.command(name="fin", brief="Fin du tournoi", description="Arrête un tournoi et affiche le score final", usage="<id_du_tournoi>")
    async def fin(self, ctx: commands.Context):

        embed = discord.Embed()
        embed.color = discord.Color.orange()
        embed.timestamp = datetime.datetime.utcnow()

        embed.description = f"Quel est l'id du tournoi {ctx.author.mention}?"
        message = await ctx.send(embed=embed)
        try:
            id: discord.Message = await self.client.wait_for("message", check=self.check_author(ctx), timeout=120.0)
        except asyncio.TimeoutError:
            embed.description = f"Temps écoulé {ctx.author.mention}!"
            await message.edit(embed=embed)
            return
        else:
            await id.delete()
            id = id.content
            embed.description = None

        connection, cursor = await db_connect()

        tournament = await cursor.execute("SELECT id_tournament, title, reward, classement FROM tournaments WHERE guild_id = ? AND id_tournament = ?", (ctx.guild.id, id))
        tournament = await tournament.fetchone()

        await cursor.execute("UPDATE tournaments SET start = 0, finish = 1 WHERE guild_id = ? AND id_tournament = ?", (ctx.guild.id, id))
        await connection.commit()

        participants = await cursor.execute("SELECT id_participant, score FROM tournament_participants WHERE id_tournament = ?", (id,))
        participants = await participants.fetchall()
        await db_close(connection)

        if participants:
            winner = sorted(
                participants, key=lambda x: x[1], reverse=True)[0][0]
            embed.description = f"Le gagnant du tournoi {tournament[1]} est <@{winner}> avec un score de {winner[1]} ! Félicitations, tu viens de remporter la récompense suivante: `{tournament[2]}` !"
            embed.add_field(name="Classement Final", value=tournament[3])
        else:
            embed.description = "Il n'y a pas de gagnant comme il n'y avait aucun participant !"

        await message.edit(embed=embed)

    # Errors

    @chat.error
    async def on_chat_error(self, ctx: commands.Context, error):
        msg = f"{error} dans le serveur {ctx.guild.name}(salon: {ctx.channel.name})"
        write_file(
            log_file, msg, is_log=True)
        await get_log_channel(self.client, ctx, msg)
        if isinstance(error, discord.ext.commands.CommandInvokeError):
            await ctx.send("*No Entry*")
            etype = type(error)
            trace = error.__traceback__
            verbosity = 4
            lines = traceback.format_exception(etype, error, trace, verbosity)
            traceback_text = ''.join(lines)
            print(traceback_text)


def setup(client):
    client.add_cog(Games(client))
