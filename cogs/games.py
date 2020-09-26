import asyncio
from sqlite3.dbapi2 import connect
import discord
from discord.ext import commands
import random
from nltk.chat.util import Chat, reflections
import cse
import sqlite3
chat_tab = {}


class Games(commands.Cog):

    def __init__(self, client):
        self.client = client

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

    @commands.command(brief="Discuter en live avec DogsBot!", description="Discutez sans pression avec DogsBot, pour cela tapez simplement la COMMANDE 'chat'. Vous pouvez maintenant discuter avec lui sans avoir besoin de taper la commande à chaque début de phrase!\n\nSon interaction est pour le moment très limité à de simples bonjour|salut|hey|slt|coucou|wesh|bonsoir|bon matin|hello|hi|cc|hola.\n\nPour quitter la conversation tapez le MOT 'exit'", usage="")
    async def chat(self, ctx, *_input_):
        print(_input_)

        db_path = "./assets/Data/pairs.db"

        # Condition pour éviter de lancer plusieurs fils de discussion avec le chatbot
        if chat_tab and chat_tab[ctx.author.id]:
            return await ctx.send(f"Je suis déjà à votre écoute {ctx.author.mention} dans un autre canal!")

        # Définition des fonctions nécessaires au chatbot
        def check_author(message):
            return message.author.id == ctx.author.id and message.channel == ctx.message.channel

        def db_connect(db):
            connection = sqlite3.connect(db)
            return connection

        def db_create_table(connection, table: str):
            cursor = connection.cursor()
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table}(
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
                questions TEXT,
                responses TEXT
            )
            """)
            connection.commit()

        def db_delete_table(connection, table: str):
            cursor = connection.cursor()
            cursor.execute(f"""DROP TABLE {table}""")
            connection.commit()

        def db_insert(connection, table, questions, responses):
            cursor = connection.cursor()
            cursor.execute(f"""
            INSERT INTO {table}(questions, responses) VALUES(?, ?)
            """, (questions, responses))
            connection.commit()

        def db_select(connection, table, questions):
            cursor = connection.cursor()
            cursor.execute(f"""
            SELECT responses FROM {table} WHERE questions LIKE "%"?"%"
            """, (questions,))
            responses = cursor.fetchall().split("|")
            return responses

        def get_table(connection, table):
            cursor = connection.cursor()
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
            print(pairs)
            return pairs

        def db_close(connection):
            connection.close()

        # Définition de la base de données pour le chatbot

        async def modifier_db(self, ctx, connection, _input_):
            connection = db_connect(db_path)
            db_create_table(connection, "pairs")
            await ctx.send("Veuillez entrer une ou plusieurs questions (ou simples phrases) (Délimitez les phrases par des `|`)")
            msg = await self.client.wait_for("message", check=check_author, timeout=120.0)
            questions = msg.content
            await ctx.send("Veuillez entrer une ou plusieurs réponses (Délimitez les réponses par des `|`)")
            msg = await self.client.wait_for("message", check=check_author, timeout=120.0)
            responses = msg.content
            db_insert(connection, "pairs", questions, responses)
            message = ""
            for i in _input_:
                message += i
            responses = db_select(connection, "pairs", message)
            await ctx.send(connection.cursor().execute("""SELECT * FROM pairs""").fetchall())
            await ctx.send(responses)

        def chat_table(connection, ctx):
            cursor = connection.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_table(
                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
                user BIGINT
            )
            """)
            connection.commit()
            cursor.execute("""
            INSERT INTO chat_table(user) VALUES(?)
            """, (ctx.author.id))
            connection.commit()

        chat = Chat(get_table(db_connect(db_path), "pairs"))
        #chat_table(db_connect(db_path), ctx)
        # print(db_connect(db_path).cursor().execute(
        #    "SELECT * FROM chat_table").fetchall())
        chat_tab[ctx.author.id] = chat

        while _input_ != "exit":

            message = f"> {_input_}\n{ctx.author.mention} "

            if not _input_:
                await ctx.send(f"{self.client.user.name} à votre écoute, {ctx.author.mention}!")
            else:
                chat_response = chat_tab[ctx.author.id].respond(_input_)
                try:
                    message = message + chat_response
                    await ctx.send(message)
                except Exception:
                    await ctx.send(":person_shrugging_tone2:")

            try:
                _input_ = await self.client.wait_for("message", check=check_author, timeout=120.0)
            except asyncio.TimeoutError:
                del chat_tab[ctx.author.id]
                return await ctx.send(f"Bon, moi je me tire si tu dis rien {ctx.author.mention}!")
            else:
                _input_ = _input_.content

        await ctx.send(f"Merci {ctx.author.name}, à bientôt!")
        db_close(connection)
        del chat_tab[ctx.author.id]

    @ chat.error
    async def on_chat_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.CommandInvokeError):
            await ctx.send("*No Entry*")


def setup(client):
    client.add_cog(Games(client))
