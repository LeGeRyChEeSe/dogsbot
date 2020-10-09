import discord
from discord.ext import commands
import json
from datetime import datetime, timezone
import asyncio
import sqlite3
from traceback import format_exception

jonction = None
db_path = "./assets/Data/pairs.db"


class Admin(commands.Cog):

    def __init__(self, client):
        self.client = client

    def not_command(self, message):
        return message.content.startswith(str(self.client.command_prefix))

    def check_author(self, *args):
        def inner(message):
            ctx = args[0]
            print(ctx.author.name)
            return str(message.author.id) == str(ctx.author.id) and message.channel == ctx.message.channel and self.not_command(message) == False
        return inner

    def check_remove_or_update(self, *args):
        def inner(message):
            if not self.check_author(message):
                return False
            if message.content == "exit":
                return True
            for i in args:
                if message.content == i:
                    return True
            return False
        return inner

    def check_if_int(self, id):
        try:
            int(id.content)
        except ValueError:
            if id.content == "exit":
                return True
            else:
                return False
        else:
            if self.check_author(id):
                return True
            else:
                return False

    def db_connect(self, db=db_path):
        connection = sqlite3.connect(db)
        cursor = connection.cursor()
        return connection, cursor

    def db_close(self, connection):
        connection.close()

    # Events

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        user_id = payload.user_id
        if user_id == self.client.user.id:
            return
        message_id = payload.message_id
        guild_id = payload.guild_id
        channel_id = payload.channel_id
        emoji = payload.emoji.name

        guild = discord.utils.find(
            lambda g: g.id == guild_id, self.client.guilds)
        channel = discord.utils.find(
            lambda g: g.id == channel_id, guild.channels)
        message = await channel.fetch_message(message_id)

        if (message.author.bot and message.pinned):
            reactions = message.reactions
            roles = message.role_mentions

            for embed in message.embeds:
                for field in embed.fields:
                    message_reaction = field.name
                    message_role_id = int(field.value.replace(
                        "<@&", "").replace(">", ""))
                    if (emoji == message_reaction):
                        role = discord.utils.get(
                            guild.roles, id=message_role_id)
                        member = guild.get_member(user_id)
                        await member.add_roles(role)
                        return print(f"{member.display_name}#{member.discriminator} s'est attribué le rôle {role.name}!")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        user_id = payload.user_id
        message_id = payload.message_id
        guild_id = payload.guild_id
        channel_id = payload.channel_id
        emoji = payload.emoji.name

        guild = discord.utils.find(
            lambda g: g.id == guild_id, self.client.guilds)
        channel = discord.utils.find(
            lambda g: g.id == channel_id, guild.channels)
        message = await channel.fetch_message(message_id)

        if (message.author.bot and message.pinned):
            reactions = message.reactions
            roles = message.role_mentions

            for embed in message.embeds:
                for field in embed.fields:
                    message_reaction = field.name
                    message_role_id = int(field.value.replace(
                        "<@&", "").replace(">", ""))
                    if (emoji == message_reaction):
                        role = discord.utils.get(
                            guild.roles, id=message_role_id)
                        member = guild.get_member(user_id)
                        await member.remove_roles(role)
                        return print(f"{member.display_name}#{member.discriminator} s'est destitué du rôle {role.name}!")

    # Commands

    @commands.command(name="ping", brief="Bot latency", description="Réponds par 'Pong!' en indiquant la latence du bot.")
    @commands.has_permissions(manage_messages=True)
    async def ping(self, ctx):
        await ctx.send(f"Pong! (Latence du bot: {round(self.client.latency * 1000)}ms)")

    @commands.command(name="clear", brief="Effacer des messages", description="Permet de supprimer un nombre défini de messages dans un salon.", usage="<nombre_de_messages>", aliases=["purge", "erase", "delete"])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount=5):
        sure = await ctx.send(f"Etes-vous bien sûr de vouloir effacer {amount} messages de ce canal (**o**/**n**)?")
        message = ""
        try:
            message = await self.client.wait_for("message", check=self.check_author(ctx), timeout=60.0)
        except asyncio.TimeoutError:
            await ctx.send("Temps écoulé!")
            await message.delete()
        else:
            if message.content == "o":
                await ctx.channel.purge(limit=amount + 3)
                print(f"{amount} messages ont été effacé du salon {ctx.channel.name}")
            else:
                await sure.delete()
                await message.delete()
                await ctx.message.delete()

    @commands.command(name="kick", brief="Expulser un membre du serveur")
    @commands.has_permissions(manage_messages=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(f"{member.mention} a été expulsé!")

    @commands.command(name="ban", brief="Bannir un membre du serveur")
    @commands.has_permissions(manage_messages=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await member.ban(reason=reason)
        await ctx.send(f"{member.mention} a été banni!")

    @commands.command(name="unban", brief="Débannir un membre du serveur")
    @commands.has_permissions(manage_messages=True)
    async def unban(self, ctx, *, member):
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                return await ctx.send(f"{user.name}#{user.discriminator} a été débanni!")

        await ctx.send(f"{member_name}#{member_discriminator} n'est pas un utilisateur banni du serveur.")

    def team_dev(ctx):
        return ctx.author.id == 440141443877830656

    @commands.command(hidden=True)
    @commands.check(team_dev)
    async def bot(self, ctx):
        await ctx.send(self.client.user.id)

    @commands.command(name="changeprefix", brief="Modifier le prefix de commande", description="Modifier le prefix de commande. Par défaut le prefix est !\n\n", usage="<new_prefix>")
    @commands.check(team_dev)
    async def changeprefix(self, ctx, prefix):
        file = ".\\assets\\prefixes.json"

        with open(file, "r") as f:
            prefixes = json.load(f)

        prefixes[str(ctx.guild.id)] = prefix

        with open(file, "w") as f:
            json.dump(prefixes, f, indent=4)
        await ctx.send(f"Le préfix a été changé: `{prefix}`")

    @commands.command(brief="Ajouter des rôles avec des réactions", usage="<reaction1>;<role1>,<reactionN>;<roleN>", description="Renvoie un embed contenant l'attribution de chaque réaction à un rôle spécifique. Ne peut pas contenir une même réaction pour 2 rôles à la fois.")
    @commands.check(team_dev)
    async def addroles(self, ctx, *, content):
        await ctx.message.delete()
        reactions = list()
        roles = ctx.message.role_mentions
        lines = 0
        content_split = content.split(",")

        embed = discord.Embed()

        for i in content_split:
            both = i.split(";")
            reactions.append(both[0].strip())
            embed.add_field(name=reactions[lines],
                            value=roles[lines].mention, inline=True)
            lines += 1

        lines = 0
        global jonction
        jonction = dict()
        for i in reactions:
            jonction[i] = roles[lines]
            lines += 1

        embed.title = "Attribution des Rôles"
        embed.description = "Cliquez sur l'une des réactions à ce message pour obtenir le rôle associé."
        embed.colour = discord.Colour(126)
        embed.set_author(name=ctx.message.guild.name)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.timestamp = datetime.now(timezone.utc)

        message = await ctx.send(embed=embed)
        await message.pin(reason="Roles Attribution")
        await ctx.channel.purge(limit=1)

        for emoji in reactions:
            await message.add_reaction(emoji)

        print(jonction)

    @commands.command(aliases=["pairs", "prs", "sp"])
    @commands.check(team_dev)
    async def see_pairs(self, ctx):
        connection, cursor = self.db_connect()
        cursor.execute("""
         SELECT * FROM pairs
         """)
        await ctx.send(cursor.fetchall())
        self.db_close(connection)

    @commands.command(hidden=True, aliases=["rmp", "rmpairs", "upp", "upairs"])
    @commands.check(team_dev)
    async def update_pairs(self, ctx):

        def update_questions_pairs(connection, cursor, id: int, questions: str):
            cursor.execute(
                "UPDATE pairs SET questions = ? WHERE id = ?", (questions, id))
            cursor.close()
            connection.commit()

        def update_responses_pairs(connection, cursor, id: int, responses: str):
            cursor.execute(
                "UPDATE pairs SET responses = ? WHERE id = ?", (responses, id))
            cursor.close()
            connection.commit()

        def select_from_pairs(cursor, *id: int):
            if not id:
                return cursor.execute("SELECT id, questions, responses FROM pairs").fetchall()
            else:
                return cursor.execute("SELECT id, questions, responses FROM pairs WHERE id = ?", (id[0]),).fetchall()

        def delete_from_pairs(connection, cursor, id: int):
            cursor.execute("DELETE FROM pairs WHERE id = ?", (id,))
            cursor.close(connection)
            connection.commit()

        connection, cursor = self.db_connect()
        questions = select_from_pairs(cursor)
        list_pairs = ""

        for question in questions:
            list_pairs += "`" + str(question[0]) + \
                "`" + ": \"" + question[1] + "\" -> " + \
                str(question[2].split("|")) + "\"\n"

        await ctx.send(f"**Voici la liste des questions associées à leurs réponses actuellement dans le chatbot:**\n{list_pairs}\nVeuillez sélectionner un `numéro` pour la modifier ou la supprimer.")
        try:
            id = await self.client.wait_for("message", check=check_if_int, timeout=120.0)
        except asyncio.TimeoutError:
            self.db_close(connection)
            await ctx.send("Vous avez mis trop de temps à répondre, je mets donc fin à notre échange.")
        else:
            if id.content == "exit":
                self.db_close(connection)
                return await ctx.send("Commande annulée.")
            await ctx.send("Voulez-vous modifier ou supprimer la ligne ? (`m` ou `s`)")

            try:
                ask_modify_db = await self.client.wait_for("message", check=check_remove_or_update("m", "s"), timeout=120.0)
            except asyncio.TimeoutError:
                self.db_close(connection)
                await ctx.send("Vous avez mis trop de temps à répondre, je mets donc fin à notre échange.")
            else:
                if ask_modify_db.content == "exit":
                    self.db_close(connection)
                    return await ctx.send("Commande annulée.")
                elif ask_modify_db.content == "m":
                    select_line = select_from_pairs(cursor, id.content)
                    response = f"`{select_line[0][0]}`: \"{select_line[0][1]}\" -> \"{select_line[0][2].split('|')}\""
                    await ctx.send(f"Voici la ligne que vous avez sélectionné:\n{response}\n\nVoulez-vous modifier les `q`uestions, les `r`éponses ou `t`out à la fois ? (`q`, `r`, `t`)")

                    try:
                        update_choice = await self.client.wait_for("message", check=check_remove_or_update("q", "r", "t"), timeout=120.0)
                    except asyncio.TimeoutError:
                        self.db_close()
                        await ctx.send("Vous avez mis trop de temps à répondre, je mets donc fin à notre échange.")
                    else:
                        if update_choice.content == "exit":
                            self.db_close()
                            return await ctx.send("Commande annulée.")
                        elif update_choice.content == "q":
                            await ctx.send("Veuillez écrire les nouvelles questions pour cette ligne en respectant la syntaxe suivante:\n`question_1|question_2|question_n|...`")
                            try:
                                update_question = await self.client.wait_for("message", check=self.check_author, timeout=300.0)
                            except asyncio.TimeoutError:
                                self.db_close()
                                await ctx.send("Vous avez mis trop de temps à répondre, je mets donc fin à notre échange.")
                            else:
                                if update_question.content == "exit":
                                    self.db_close()
                                    return await ctx.send("Commande annulée.")
                                update_questions_pairs(connection, cursor,
                                    id.content, update_question.content)
                                await ctx.send(f"Voici la nouvelle ligne:\n{select_from_pairs(cursor, id.content)}")
                                self.db_close()
                                return
                        elif update_choice.content == "r":
                            await ctx.send("Veuillez écrire les nouvelles réponses pour cette ligne en respectant la syntaxe suivante:\n`réponse_1|réponse_2|réponse_n|...`")
                            try:
                                update_responses = await self.client.wait_for("message", check=self.check_author, timeout=300.0)
                            except asyncio.TimeoutError:
                                self.db_close()
                                await ctx.send("Vous avez mis trop de temps à répondre, je mets donc fin à notre échange.")
                            else:
                                if update_responses.content == "exit":
                                    self.db_close()
                                    return await ctx.send("Commande annulée.")
                                update_responses_pairs(connection, cursor,
                                    id.content, update_responses.content)
                                await ctx.send(f"Voici la nouvelle ligne:\n{select_from_pairs(cursor, id.content)}")
                                self.db_close()
                                return
                        elif update_choice.content == "t":
                            await ctx.send("Veuillez écrire les nouvelles questions pour cette ligne en respectant la syntaxe suivante:\n`question_1|question_2|question_n|...`")
                            try:
                                update_question = await self.client.wait_for("message", check=self.check_author, timeout=300.0)
                            except asyncio.TimeoutError:
                                self.db_close()
                                await ctx.send("Vous avez mis trop de temps à répondre, je mets donc fin à notre échange.")
                            else:
                                if update_question.content == "exit":
                                    self.db_close()
                                    return await ctx.send("Commande annulée.")
                                update_questions_pairs(connection, cursor,
                                    id.content, update_question.content)
                            await ctx.send("Veuillez écrire les nouvelles réponses pour cette ligne en respectant la syntaxe suivante:\n`réponse_1|réponse_2|réponse_n|...`")
                            try:
                                update_responses = await self.client.wait_for("message", check=self.check_author, timeout=300.0)
                            except asyncio.TimeoutError:
                                self.db_close()
                                await ctx.send("Vous avez mis trop de temps à répondre, je mets donc fin à notre échange.")
                            else:
                                if update_responses.content == "exit":
                                    self.db_close()
                                    return await ctx.send("Commande annulée.")
                                update_responses_pairs(connection, cursor,
                                    id.content, update_responses.content)
                                await ctx.send(f"Voici la nouvelle ligne:\n{select_from_pairs(cursor, id.content)}")
                                self.db_close()
                                return
                elif ask_modify_db.content == "s":
                    delete_from_pairs(connection, cursor, id.content)
                    self.db_close(connection)
                    return await ctx.send(f"La ligne `{id.content}` a bien été supprimée de la table!")

    @commands.command()
    async def owner(self, ctx):
        owner = ctx.guild.owner_id
        await ctx.send(f"Le propriétaire de {ctx.guild.name} est <@{owner}>!")
    # Commands Error

    @commands.command(aliases=["dpt", "dt"])
    @commands.check(team_dev)
    async def drop_table(self, ctx, table):
        connection, cursor = self.db_connect()
        cursor.execute(f"""
        DROP TABLE {table}
        """)
        connection.commit()
        print(f"{table} a été supprimé!")
        await ctx.send(f"{table} a été supprimé!")
        self.db_close(connection)

    @commands.command(aliases=["dll", "dl"])
    @commands.check(team_dev)
    async def delete_line(self, ctx, name, value, table):
        connection, cursor = self.db_connect()
        cursor.execute(f"""
        DELETE FROM {table} WHERE {name}={value}
        """)
        connection.commit()
        print(f"{table}: {name} -> {value} a été supprimé!")
        await ctx.send(f"`{table}: {name} -> {value}` a été supprimé!")
        self.db_close(connection)

    @commands.command(aliases=["select", "sl"])
    async def select_from_table(self, ctx, select, _from):
        connection, cursor = self.db_connect()
        selection = cursor.execute(f"""
        SELECT {select} FROM {_from}
        """).fetchall()
        await ctx.send(str(selection))
        self.db_close(connection)

    @bot.error
    async def bot_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Vous n'êtes pas <@!440141443877830656>!")

    @unban.error
    async def unban_error(self, ctx, error):
        if ValueError(error):
            print(error)
            await ctx.send("L'utilisateur doit être écrit de la forme `nom#XXXX`.")

    @update_pairs.error
    async def update_pairs_error(self, ctx, error):
        etype = type(error)
        trace = error.__traceback__
        verbosity = 4
        lines = format_exception(etype, error, trace, verbosity)
        traceback_text = ''.join(lines)
        print(traceback_text)


def setup(client):
    client.add_cog(Admin(client))
