import asyncio
import random
import traceback

import discord
from discord.ext import commands
from nltk.chat.util import Chat
from events.functions import *

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

    @commands.command(hidden=False, brief="Discuter en live avec DogsBot!",
                      description="Discutez sans pression avec DogsBot, pour cela tapez simplement la COMMANDE 'chat'. Vous pouvez maintenant discuter avec lui sans avoir besoin de taper la commande à chaque début de phrase!\n\nSon interaction est pour le moment très limité à de simples bonjour|salut|hey|slt|coucou|wesh|bonsoir|bon matin|hello|hi|cc|hola.\n\nPour quitter la conversation tapez le MOT 'exit'",
                      usage="")
    async def chat(self, ctx: commands.Context, *_input_):

        # Condition pour éviter de lancer plusieurs fils de discussion avec le chatbot
        connection, cursor = db_connect()
        create(connection, cursor, "chat_table", _names=["user"], _type=["INT"])
        user = select(cursor, _select=["user"], _from="chat_table", _where=f"user={str(ctx.author.id)}")

        if user:
            return await ctx.send(f"Je suis déjà à votre écoute {ctx.author.mention} dans un autre canal!")

        # Définition de la base de données pour le chatbot

        selection = select(cursor, _select=["questions", "responses"], _from="pairs", _fetchall=True)
        pairs = []
        for pair in selection:
            element = [pair[0]]
            pair_pop = pair[1].split("|")
            pair_pop.pop()
            element.append(
                pair_pop)
            pairs.append(element)

        chat = Chat(pairs)
        insert(connection, cursor, _into="chat_table", _names=["user"], _values=[str(ctx.author.id)])

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
                        delete(connection, cursor, _from="chat_table", _where=f"user={str(ctx.author.id)}")
                        db_close(connection)
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
                                insert(connection, cursor, _into="pairs", _names=["questions", "responses"], _values=[_input_, msg_to_edit.content])
                                await ctx.send(
                                    f"Les réponses suivantes ont été ajouté au(x) message(s) *\"{_input_}\"*:\n{str(msg_to_edit.content.split('|'))}")
                        elif msg_to_confirm.content == "non":
                            await ctx.send("Ok.")

                else:
                    await ctx.send(message)

            try:
                _input_ = await self.client.wait_for("message", check=self.check_author(ctx), timeout=120.0)
            except asyncio.TimeoutError:
                delete(connection, cursor, _from="chat_table", _where=f"user={str(ctx.author.id)}")
                connection.commit()
                db_close(connection)
                return await ctx.send(f"Bon, moi je me tire si tu dis rien {ctx.author.mention}!")
            else:
                _input_ = _input_.content

        await ctx.send(f"Merci {ctx.author.name}, à bientôt!")
        delete(connection, cursor, _from="chat_table", _where=f"user={str(ctx.author.id)}")
        db_close(connection)

    @commands.command(hidden=True, name="dragonball", aliases=["db", "dragon"])
    async def dragonball(self, ctx, name=None, race=None, *, skill_name: str = None):
        pass

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

        connection, cursor = db_connect()

        if len(add_word) > 0:
            if add_word[0] == "add":
                if insert_into_pendu(connection, cursor, add_word[1].lower()):
                    await ctx.send(f"{ctx.author.mention} Le mot `{add_word[1]}` a bien été ajouté parmis tous les autres mots!")
                else:
                    await ctx.send(f"{ctx.author.mention} Le mot {add_word[1]} existe déjà dans ma base de données!")
                return db_close(connection)
            elif add_word[0] == "del" and ctx.channel.permissions_for(ctx.author).administrator:
                if delete_from_pendu(connection, cursor, add_word[1].lower()):
                    await ctx.send(f"{ctx.author.mention} Le mot {add_word[1]} a bien été supprimé!")
                    return db_close(connection)
                else:
                    await ctx.send(
                        f"Le mot {add_word[1]} n'est pas présent dans ma base de données, je ne peux donc pas le supprimer!")
                    return db_close(connection)

        set_pendu(self, ctx, connection, cursor)
        user_pendu = self.game_user[ctx.author.id]
        set_taille_message = None

        if len(add_word) > 0:
            if add_word[0] == "taille" and int(add_word[1]) in range(3, 26, 1):
                user_pendu.taille_mot = int(add_word[1])
                set_taille_message = await ctx.send(f"{ctx.author.mention}Taille choisie: {int(add_word[1])}")
                user_pendu.mot = word_init(connection, cursor, user_pendu.taille_mot)
                user_pendu.chances = len(user_pendu.mot)
            elif add_word[0] == "taille" and not int(add_word[1]) in range(3, 26, 1):
                set_taille_message = await ctx.send(
                    f"""{ctx.author.mention}`Taille invalide` (doit se situer entre 3 et 25)\nTaille du mot par défaut: `8`""")

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
                    if len(add_word) > 0:
                        if add_word[0] == "taille" and int(add_word[1]) in range(3, 26, 1):
                            user_pendu.taille_mot = int(add_word[1])
                elif retry == "n":
                    await user_pendu.message_to_delete.delete()
                    await user_quit.delete()

        db_close(connection)
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
