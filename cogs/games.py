import asyncio
import random
import sqlite3
import traceback

import discord
from discord.ext import commands
from nltk.chat.util import Chat

import assets.dragonball as dragonball
from assets.Games.Pendu.pendu import *


class Games(commands.Cog):

    def __init__(self, client):
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

    def db_connect(self):
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        return connection, cursor

    def create_pairs_table(self, connection, cursor, table: str):
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table}(
            id INTEGER PRIMARY KEY UNIQUE,
            questions TEXT,
            responses TEXT
        )
        """)
        connection.commit()

    def db_insert(self, connection, cursor, table, questions, responses):
        cursor.execute(f"""
        INSERT INTO {table}(questions, responses) VALUES(?, ?)
        """, (questions, responses))
        connection.commit()

    def db_select(self, cursor, table, questions):
        cursor.execute(f"""
        SELECT responses FROM {table} WHERE questions LIKE "%"?"%"
        """, (questions,))
        responses = cursor.fetchall().split("|")
        return responses

    def get_table(self, cursor):
        cursor.execute("""
        SELECT questions, responses FROM pairs
        """)
        str_pairs = cursor.fetchall()
        pairs = []
        for pair in str_pairs:
            element = [pair[0]]
            pair_pop = pair[1].split("|")
            pair_pop.pop()
            element.append(
                pair_pop)
            pairs.append(element)
        return pairs

    def db_close(self, connection):
        connection.close()

    def create_chat_table(self, connection, cursor):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_table(
            id INTEGER PRIMARY KEY UNIQUE,
            user INT
        )
        """)
        connection.commit()
        print("La table chat_table a bien été créée!")

    def insert_into_chat_table(self, connection, cursor, user):
        cursor.execute("""
        INSERT INTO chat_table(user) VALUES(?)
        """, (str(user),))
        connection.commit()
        print(f"<@{user}> a bien été ajouté à la conversation avec le chatbot!")

    def delete_from_chat_table(self, connection, cursor, user):
        cursor.execute("""
        DELETE FROM chat_table WHERE user = ?
        """, (str(user),))
        connection.commit()
        print(
            f"<@{user}> a bien été retiré de la conversation avec le chatbot!")

    def select_user_from_chat_table(self, cursor, user):
        cursor.execute("""
        SELECT user FROM chat_table WHERE user = ?
        """, (str(user),))
        return cursor.fetchone()

    @commands.command(aliases=['8ball', 'eightball', 'game'])
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

    @commands.command(brief="Discuter en live avec DogsBot!",
                      description="Discutez sans pression avec DogsBot, pour cela tapez simplement la COMMANDE 'chat'. Vous pouvez maintenant discuter avec lui sans avoir besoin de taper la commande à chaque début de phrase!\n\nSon interaction est pour le moment très limité à de simples bonjour|salut|hey|slt|coucou|wesh|bonsoir|bon matin|hello|hi|cc|hola.\n\nPour quitter la conversation tapez le MOT 'exit'",
                      usage="")
    async def chat(self, ctx, *_input_):

        # Condition pour éviter de lancer plusieurs fils de discussion avec le chatbot
        connection, cursor = self.db_connect()
        self.create_chat_table(connection, cursor)
        user = self.select_user_from_chat_table(cursor, ctx.author.id)
        if user:
            return await ctx.send(f"Je suis déjà à votre écoute {ctx.author.mention} dans un autre canal!")

        # Définition de la base de données pour le chatbot

        chat = Chat(self.get_table(cursor))
        self.insert_into_chat_table(connection, cursor, ctx.author.id)

        while _input_ != "exit":

            message = f"> {_input_}\n{ctx.author.mention} "

            if not _input_:
                await ctx.send(f"{self.client.user.name} à votre écoute, {ctx.author.mention}!")
            else:
                chat_response = chat.respond(_input_)
                try:
                    message = message + chat_response
                except Exception as e:
                    await ctx.send(
                        "Je n'ai pas de réponses à votre message, voulez-vous définir une/plusieurs réponses ? *("
                        "**oui**/**non**)*")
                    try:
                        msg_to_confirm = await self.client.wait_for("message", check=self.check_confirm, timeout=120.0)
                    except asyncio.TimeoutError:
                        self.delete_from_chat_table(connection, cursor, ctx.author.id)
                        self.db_close(connection)
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
                                self.db_insert(connection, cursor, "pairs", _input_,
                                               msg_to_edit.content)
                                await ctx.send(
                                    f"Les réponses suivantes ont été ajouté au(x) message(s) *\"{_input_}\"*:\n{str(msg_to_edit.content.split('|'))}")
                        elif msg_to_confirm.content == "non":
                            await ctx.send("Ok.")

                else:
                    await ctx.send(message)

            try:
                _input_ = await self.client.wait_for("message", check=self.check_author(ctx), timeout=120.0)
            except asyncio.TimeoutError:
                self.delete_from_chat_table(connection, cursor, ctx.author.id)
                connection.commit()
                self.db_close(connection)
                return await ctx.send(f"Bon, moi je me tire si tu dis rien {ctx.author.mention}!")
            else:
                _input_ = _input_.content

        await ctx.send(f"Merci {ctx.author.name}, à bientôt!")
        self.delete_from_chat_table(connection, cursor, ctx.author.id)
        self.db_close(connection)

    @commands.command(name="dragonball", aliases=["db", "dragon"])
    async def dragonball(self, ctx, name=None, race=None, *, skill_name: str = None):

        connection, cursor = self.db_connect()

        def create_users_table(connection, cursor):
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users(
                    id INTEGER PRIMARY KEY UNIQUE,
                    user_id INT,
                    name TEXT,
                    race TEXT,
                    skill TEXT
                    )
            """)
            connection.commit()

        def insert_into_users_table(connection, cursor, ctx, name, race, skill: str):
            cursor.execute("""
            INSERT INTO users(user_id, name, race, skill) VALUES(?,?,?,?)
            """, (ctx.author.mention, name, race, skill))
            connection.commit()

        def select_from_users_table(cursor, ctx, name):
            user_infos = cursor.execute("""
            SELECT user_id, name, race, skill FROM users WHERE user_id=? AND name=?
            """, (ctx.author.mention, name)).fetchall()[0]
            print(user_infos)
            user = dragonball.Character(
                user_infos[1], user_infos[2], user_infos[3])
            return user

        def create_skills_table(connection, cursor):
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills(
                    id INTEGER PRIMARY KEY UNIQUE,
                    name TEXT,
                    description TEXT,
                    damage INT,
                    cost INT
                    )
            """)
            connection.commit()

        def insert_into_skills_table(connection, cursor, skill: dragonball.Skills):
            cursor.execute("""
            INSERT INTO skills(name, description, damage, cost) VALUES(?,?,?,?)
            """, (skill.name, skill.description, skill.damage, skill.cost,))
            connection.commit()

        def select_from_skills_table(cursor, name: str):
            skill_infos = cursor.execute("""
            SELECT name, description, damage, cost FROM skills WHERE name=?
            """, (name,)).fetchall()[0]
            print(skill_infos)
            skill = dragonball.Skills(
                skill_infos[0], skill_infos[1], skill_infos[2], skill_infos[3])
            return skill

        def create_skill(name, description, damage=50, cost=25):
            skill = dragonball.Skills(name, description, damage, cost)
            return skill

        create_skills_table(connection, cursor)

        if name == "create_skill":
            skill_infos = []
            for arg in ["name", "description", "damage", "cost"]:
                await ctx.send(f"Veuillez entrer les informations demandées pour la variable `{arg}` du skill.")
                _input_ = await self.client.wait_for("message", check=self.check_author(ctx), timeout=300.0)
                skill_infos.append(_input_.content.replace(" ", "_"))
            skill = create_skill(skill_infos[0], skill_infos[1],
                                 skill_infos[2], skill_infos[3])
            insert_into_skills_table(connection, cursor, skill)
            self.db_close(connection)
            skill_embed = discord.Embed()
            skill_embed.set_author(name=skill.name.replace("_", " "))
            skill_embed.description = skill.description.replace("_", " ")
            skill_embed.add_field(name="Damage", value=skill.damage)
            skill_embed.add_field(name="Cost", value=skill.cost)
            await ctx.send(f"Le skill suivant a bien été créé:")
            return await ctx.send(embed=skill_embed)

        skill = select_from_skills_table(cursor, skill_name.replace(" ", "_"))
        create_users_table(connection, cursor)
        insert_into_users_table(connection, cursor, ctx, name, race, skill.name)
        user_character = select_from_users_table(cursor, ctx, name)
        self.db_close(connection)
        user = dragonball.Character(
            user_character.name, user_character.race, user_character.skills)
        skill_embed = discord.Embed()
        skill_embed.set_author(name=user.name)
        skill_embed.description = user.race
        skill_embed.add_field(name="Skill actif",
                              value=user.skills.replace("_", " "))
        return await ctx.send(embed=skill_embed)

    @commands.command(name="pendu", brief="Jouez au pendu!",
                      description="""Règles:
                      - Vous avez autant de chances que le nombre de lettre dans le mot pour découvrir ce mot pioché aléatoirement!
                      - Après avoir écrit la commande, tapez simplement la lettre que vous pensez qui est dans le mot.
                      - Pour quitter le jeu, écrivez simplement 'exit'.
                      
                      - Optionnel:
                        - Vous pouvez ajouter un mot de votre choix (maximum 25 lettres dans un mot et sans espaces) 
                          avec la syntaxe 'pendu add <nouveau_mot>'.
                        - Vous pouvez choisir la taille max du mot à deviner avec la syntaxe 
                          'pendu taille <nombre_entre_3_et_25_inclus>'""",
                      usage='[add <nouveau_mot> | taille <nombre_entre_3_et_25_inclus>]')
    async def pendu(self, ctx, *add_word):
        await ctx.message.delete()

        from assets.Games.Pendu.fonctions import insert_into_pendu

        connection, cursor = self.db_connect()

        if len(add_word) > 0:
            if add_word[0] == "add":
                if insert_into_pendu(connection, cursor, add_word[1]):
                    await ctx.send(f"Le mot `{add_word[1]}` a bien été ajouté parmis tous les autres mots!")
                else:
                    await ctx.send(f"Le mot {add_word[1]} existe déjà dans ma base de données!")
                return self.db_close(connection)
            elif add_word[0] == "del" and ctx.channel.permissions_for(ctx.author).administrator:
                if delete_from_pendu(connection, cursor, add_word[1]):
                    await ctx.send(f"Le mot {add_word[1]} a bien été supprimé!")
                    return self.db_close(connection)
                else:
                    await ctx.send(
                        f"Le mot {add_word[1]} n'est pas présent dans ma base de données, je ne peux donc pas le supprimer!")
                    return self.db_close(connection)

        set_pendu(self, ctx, connection, cursor)
        user_pendu = self.game_user[ctx.author.id]
        set_taille_message = None

        if len(add_word) > 0:
            if add_word[0] == "taille" and int(add_word[1]) in range(3, 26, 1):
                user_pendu.taille_mot = int(add_word[1])
                set_taille_message = await ctx.send(f"Taille choisie: {int(add_word[1])}")
                user_pendu.mot = word_init(connection, cursor, user_pendu.taille_mot)
                user_pendu.chances = len(user_pendu.mot)
            elif add_word[0] == "taille" and not int(add_word[1]) in range(3, 26, 1):
                set_taille_message = await ctx.send(
                    """`Taille invalide` (doit se situer entre 3 et 25)\nTaille du mot par défaut: `8`""")

        while user_pendu.is_running:

            if not user_pendu.message_to_delete:
                user_pendu.message_to_delete = await ctx.send(f"Veuillez entrer une lettre {ctx.author.mention}")

            try:
                lettre = await self.client.wait_for("message", check=self.check_author(ctx), timeout=120.0)
            except asyncio.TimeoutError:
                await ctx.send("Temps écoulé!")
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

            await user_pendu.running(lettre.content)

            if user_pendu.is_find or user_pendu.is_over:
                try:
                    user_quit = await self.client.wait_for("message", check=self.check_author(ctx), timeout=120.0)
                except asyncio.TimeoutError:
                    await ctx.send("Temps écoulé!")
                    break

                retry = await user_pendu.retry(user_quit.content)
                if retry == "o":
                    await user_pendu.message_to_delete.delete()
                    await user_quit.delete()
                    user_pendu.__init__(ctx, connection, cursor)
                    user_pendu.user_chances = 0
                    if len(add_word) > 0:
                        if add_word[0] == "taille" and int(add_word[1]) in range(3, 26, 1):
                            user_pendu.taille_mot = int(add_word[1])
                elif retry == "n":
                    await user_pendu.message_to_delete.delete()
                    await user_quit.delete()

        self.db_close(connection)
        self.game_user[ctx.author.id] = None

    # Errors

    @chat.error
    async def on_chat_error(self, ctx, error):
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
