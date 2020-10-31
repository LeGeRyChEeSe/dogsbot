import asyncio
from datetime import datetime, timezone
from traceback import format_exception

import discord
from discord.colour import Colour
from discord.ext import commands
from discord.message import Message

from events.functions import *

jonction = None


class Admin(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client

    def not_command(self, message):
        return message.content.startswith(str(self.client.command_prefix))

    def check_author(self, *args):
        def inner(message):
            ctx = args[0]
            print(ctx.author.name)
            return str(message.author.id) == str(
                ctx.author.id) and message.channel == ctx.message.channel and self.not_command(message) == False

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

        guild: discord.Guild = discord.utils.find(
            lambda g: g.id == guild_id, self.client.guilds)
        channel = discord.utils.find(
            lambda g: g.id == channel_id, guild.channels)
        message = await channel.fetch_message(message_id)

        if message.author.bot and message.pinned:
            reactions = message.reactions
            roles = message.role_mentions

            for field in message.embeds[0].fields:
                message_reaction = field.name
                message_role_id = int(field.value.replace(
                    "<@&", "").replace(">", ""))
                if emoji == message_reaction:
                    role = discord.utils.get(
                        guild.roles, id=message_role_id)
                    member = guild.get_member(user_id)
                    await member.add_roles(role)
                    return print(
                        f"{member.display_name}#{member.discriminator} s'est attribué le rôle {role.name} dans le serveur {guild}!")

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

        if message.author.bot and message.pinned:
            for embed in message.embeds:
                for field in embed.fields:
                    message_reaction = field.name
                    message_role_id = int(field.value.replace(
                        "<@&", "").replace(">", ""))
                    if emoji == message_reaction:
                        role = discord.utils.get(
                            guild.roles, id=message_role_id)
                        member = guild.get_member(user_id)
                        await member.remove_roles(role)
                        return print(
                            f"{member.display_name}#{member.discriminator} s'est destitué du rôle {role.name} dans le serveur {guild}!")

    # Commands

    @commands.command(name="clear", brief="Effacer des messages",
                      description="Permet de supprimer un nombre défini de messages dans un salon.",
                      usage="<nombre_de_messages>", aliases=["purge", "erase", "delete"])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, amount=5):
        sure = await ctx.send(
            f"Etes-vous bien sûr de vouloir effacer {amount} messages de ce canal {ctx.author.mention}(**o**/**n**)?")
        try:
            message = await self.client.wait_for("message", check=self.check_author(ctx), timeout=60.0)
        except asyncio.TimeoutError:
            await ctx.send("Temps écoulé!")
            await ctx.message.delete()
            await sure.delete()
        else:
            if message.content == "o":
                await ctx.channel.purge(limit=amount + 3)
                print(
                    f"{ctx.author.display_name} a effacé {amount} messages du salon {ctx.channel.name} dans le serveur {ctx.guild.name}. Date: {datetime.utcnow()}")
            else:
                await sure.delete()
                await message.delete()
                await ctx.message.delete()

    @commands.command(name="kick", brief="Expulser un membre du serveur")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(f"{member.mention} a été expulsé!")

    @commands.command(name="ban", brief="Bannir un membre du serveur")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await member.ban(reason=reason)
        await ctx.send(f"{member.mention} a été banni!")

    @commands.command(name="unban", brief="Débannir un membre du serveur")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, member):
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                return await ctx.send(f"{user.name}#{user.discriminator} a été débanni!")

        await ctx.send(f"{member_name}#{member_discriminator} n'est pas un utilisateur banni du serveur.")

    def team_dev(ctx: commands.Context):
        return ctx.author.id == 440141443877830656

    @commands.command(hidden=True)
    @commands.check(team_dev)
    async def bot(self, ctx):
        await ctx.send(self.client.user.id)

    @commands.command(name="changeprefix", brief="Modifier le prefix de commande",
                      description="Modifier le prefix de commande. Par défaut le prefix est !\n\n",
                      usage="<new_prefix>", aliases=["prefix", "pfx"])
    @commands.has_permissions(manage_guild=True)
    async def changeprefix(self, ctx, prefix):

        connection, cursor = db_connect()

        def insert(connection, cursor, guild_id: discord.Guild.id, prefix_user: str):
            try:
                select(cursor, guild_id)
            except:
                cursor.execute(
                    "INSERT INTO prefix(guild, prefix) VALUES(?,?)", (guild_id, prefix_user))
            else:
                cursor.execute(
                    "UPDATE prefix SET prefix=? WHERE guild=?", (prefix_user, guild_id))
            connection.commit()

        def select(cursor, guild_id: discord.Guild.id):
            guild, prefix = cursor.execute(
                "SELECT guild, prefix FROM prefix WHERE guild=?", (guild_id,)).fetchone()
            return guild, prefix

        create(connection, cursor, "prefix", _names=[
               "guild", "prefix"], _type=["TEXT", "TEXT"])
        insert(connection, cursor, ctx.guild.id, prefix)
        guild, prefix = select(cursor, ctx.guild.id)
        db_close(connection)
        print(guild, prefix)
        await ctx.send(f"||@everyone|| Le préfix a été changé: `{prefix}`")

    @commands.command(brief="Ajouter des rôles avec des réactions", usage="",
                      description="Renvoie un embed contenant l'attribution de chaque réaction à un rôle spécifique. "
                                  "Ne peut pas contenir une même réaction pour 2 rôles à la fois.", aliases=["addr", "ar"])
    @commands.has_permissions(manage_roles=True)
    async def addroles(self, ctx: commands.Context):

        receivers = {}
        embed = discord.Embed()
        embed_sender = discord.Embed()
        roles = ctx.message

        await ctx.message.delete()

        def check_exit(msg: discord.Message):
            return msg.author.id is ctx.author.id and msg.content == "exit"

        def check_role(msg: discord.Message):
            return msg.author.id is ctx.author.id and (msg.content.strip().startswith("<@&") and msg.content.strip()
                                                       .endswith(">")) or (msg.content == "exit")

        def check_emoji(payload: discord.RawReactionActionEvent):
            return payload.member.id is ctx.author.id and payload.message_id == sender.id

        embed_sender.add_field(name="Tapez `exit`",
                               value="Pour annuler la commande")
        embed_sender.set_author(name=ctx.author.display_name,
                                icon_url=ctx.author.avatar_url)

        embed_sender.colour = Colour.orange()
        embed_sender.title = ":anger: Rôles :anger:"
        embed_sender.timestamp = datetime.utcnow()
        embed_sender.description = "__**Veuillez entrer des rôles séparés d'un espace entre chaque**__ *(Ex: @admin @nitro @helper ...)*"
        sender = await ctx.send(embed=embed_sender)

        try:
            roles = await self.client.wait_for("message", check=check_role, timeout=120.0)
        except asyncio.TimeoutError:
            embed_sender.colour = Colour.red()
            embed_sender.title = ":x: Temps expiré :x:"
            embed_sender.timestamp = datetime.utcnow()
            embed_sender.description = "Vous avez mis plus de 120 secondes pour me répondre. Commande annulée"
            embed_sender.clear_fields()
            return await sender.edit(embed=embed_sender)
        else:
            if roles.content.strip().lower() == "exit":
                return await ctx.send("Commande annulée")
            await roles.delete()

        for role in roles.role_mentions:

            embed_sender.colour = Colour.green()
            embed_sender.title = f":white_check_mark: {role.name} :white_check_mark:"
            embed_sender.description = f"Ajoutez une réaction à ce message pour le rôle **{role.name}**"
            embed_sender.clear_fields()
            embed_sender.add_field(name="Rôle", value=role.mention)
            embed_sender.timestamp = datetime.utcnow()
            embed_sender.set_footer(
                text=f"{roles.role_mentions.index(role)}/{len(roles.role_mentions)}")
            await sender.edit(embed=embed_sender)

            done, pending = await asyncio.wait([self.client.wait_for("message", check=check_exit), self.client.wait_for("raw_reaction_add", check=check_emoji)], return_when=asyncio.FIRST_COMPLETED)

            try:
                stuff = done.pop().result()
                print(f"\n\n{stuff}")
                if isinstance(stuff, discord.Message) and stuff.content == "exit":
                    return await ctx.send("Commande annulée")
                else:
                    receivers[role] = stuff
            except:
                return ctx.send("Une erreur s'est produite")
            for future in done:
                future.exception()
            for future in pending:
                future.cancel()

        await sender.delete()

        for key, value in receivers.items():
            embed.add_field(name=value.emoji,
                            value=key.mention, inline=True)

        embed.title = "Attribution des Rôles"
        embed.description = "Cliquez sur l'une des réactions à ce message pour obtenir le rôle associé."
        embed.colour = discord.Colour(126)
        embed.set_author(name=ctx.message.guild.name)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.timestamp = datetime.now(timezone.utc)

        message = await ctx.send(embed=embed)
        await message.pin(reason="Roles Attribution")
        await ctx.channel.purge(limit=1)

        for emoji in receivers.values():
            await message.add_reaction(emoji.emoji)

    @commands.command(aliases=["pairs", "prs", "sp"])
    @commands.check(team_dev)
    async def see_pairs(self, ctx):
        connection, cursor = db_connect()
        cursor.execute("""
             SELECT * FROM pairs
             """)
        await ctx.send(cursor.fetchall())
        db_close(connection)

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
                return cursor.execute("SELECT id, questions, responses FROM pairs WHERE id = ?", (id[0]), ).fetchall()

        def delete_from_pairs(connection, cursor, id: int):
            cursor.execute("DELETE FROM pairs WHERE id = ?", (id,))
            cursor.close(connection)
            connection.commit()

        connection, cursor = db_connect()
        questions = select_from_pairs(cursor)
        list_pairs = ""

        for question in questions:
            list_pairs += "`" + str(question[0]) + \
                          "`" + ": \"" + question[1] + "\" -> " + \
                          str(question[2].split("|")) + "\"\n"

        await ctx.send(
            f"**Voici la liste des questions associées à leurs réponses actuellement dans le chatbot:**\n{list_pairs}\nVeuillez sélectionner un `numéro` pour la modifier ou la supprimer.")
        try:
            id = await self.client.wait_for("message", check=self.check_if_int, timeout=120.0)
        except asyncio.TimeoutError:
            db_close(connection)
            await ctx.send("Vous avez mis trop de temps à répondre, je mets donc fin à notre échange.")
        else:
            if id.content == "exit":
                db_close(connection)
                return await ctx.send("Commande annulée.")
            await ctx.send("Voulez-vous modifier ou supprimer la ligne ? (`m` ou `s`)")

            try:
                ask_modify_db = await self.client.wait_for("message", check=self.check_remove_or_update("m", "s"),
                                                           timeout=120.0)
            except asyncio.TimeoutError:
                db_close(connection)
                await ctx.send("Vous avez mis trop de temps à répondre, je mets donc fin à notre échange.")
            else:
                if ask_modify_db.content == "exit":
                    db_close(connection)
                    return await ctx.send("Commande annulée.")
                elif ask_modify_db.content == "m":
                    select_line = select_from_pairs(cursor, id.content)
                    response = f"`{select_line[0][0]}`: \"{select_line[0][1]}\" -> \"{select_line[0][2].split('|')}\""
                    await ctx.send(
                        f"Voici la ligne que vous avez sélectionné:\n{response}\n\nVoulez-vous modifier les "
                        f"`q`uestions, les `r`éponses ou `t`out à la fois ? (`q`, `r`, `t`)")

                    try:
                        update_choice = await self.client.wait_for("message",
                                                                   check=self.check_remove_or_update(
                                                                       "q", "r", "t"),
                                                                   timeout=120.0)
                    except asyncio.TimeoutError:
                        db_close(connection)
                        await ctx.send("Vous avez mis trop de temps à répondre, je mets donc fin à notre échange.")
                    else:
                        if update_choice.content == "exit":
                            db_close(connection)
                            return await ctx.send("Commande annulée.")
                        elif update_choice.content == "q":
                            await ctx.send(
                                "Veuillez écrire les nouvelles questions pour cette ligne en respectant la syntaxe "
                                "suivante:\n`question_1|question_2|question_n|...`")
                            try:
                                update_question = await self.client.wait_for("message", check=self.check_author,
                                                                             timeout=300.0)
                            except asyncio.TimeoutError:
                                db_close(connection)
                                await ctx.send(
                                    "Vous avez mis trop de temps à répondre, je mets donc fin à notre échange.")
                            else:
                                if update_question.content == "exit":
                                    db_close(connection)
                                    return await ctx.send("Commande annulée.")
                                update_questions_pairs(connection, cursor,
                                                       id.content, update_question.content)
                                await ctx.send(f"Voici la nouvelle ligne:\n{select_from_pairs(cursor, id.content)}")
                                db_close(connection)
                                return
                        elif update_choice.content == "r":
                            await ctx.send(
                                "Veuillez écrire les nouvelles réponses pour cette ligne en respectant la syntaxe "
                                "suivante:\n`réponse_1|réponse_2|réponse_n|...`")
                            try:
                                update_responses = await self.client.wait_for("message", check=self.check_author,
                                                                              timeout=300.0)
                            except asyncio.TimeoutError:
                                db_close(connection)
                                await ctx.send(
                                    "Vous avez mis trop de temps à répondre, je mets donc fin à notre échange.")
                            else:
                                if update_responses.content == "exit":
                                    db_close(connection)
                                    return await ctx.send("Commande annulée.")
                                update_responses_pairs(connection, cursor,
                                                       id.content, update_responses.content)
                                await ctx.send(f"Voici la nouvelle ligne:\n{select_from_pairs(cursor, id.content)}")
                                db_close(connection)
                                return
                        elif update_choice.content == "t":
                            await ctx.send(
                                "Veuillez écrire les nouvelles questions pour cette ligne en respectant la syntaxe "
                                "suivante:\n`question_1|question_2|question_n|...`")
                            try:
                                update_question = await self.client.wait_for("message", check=self.check_author,
                                                                             timeout=300.0)
                            except asyncio.TimeoutError:
                                db_close(connection)
                                await ctx.send(
                                    "Vous avez mis trop de temps à répondre, je mets donc fin à notre échange.")
                            else:
                                if update_question.content == "exit":
                                    db_close(connection)
                                    return await ctx.send("Commande annulée.")
                                update_questions_pairs(connection, cursor,
                                                       id.content, update_question.content)
                            await ctx.send(
                                "Veuillez écrire les nouvelles réponses pour cette ligne en respectant la syntaxe "
                                "suivante:\n`réponse_1|réponse_2|réponse_n|...`")
                            try:
                                update_responses = await self.client.wait_for("message", check=self.check_author,
                                                                              timeout=300.0)
                            except asyncio.TimeoutError:
                                db_close(connection)
                                await ctx.send(
                                    "Vous avez mis trop de temps à répondre, je mets donc fin à notre échange.")
                            else:
                                if update_responses.content == "exit":
                                    db_close(connection)
                                    return await ctx.send("Commande annulée.")
                                update_responses_pairs(connection, cursor,
                                                       id.content, update_responses.content)
                                await ctx.send(f"Voici la nouvelle ligne:\n{select_from_pairs(cursor, id.content)}")
                                db_close(connection)
                                return
                elif ask_modify_db.content == "s":
                    delete_from_pairs(connection, cursor, id.content)
                    db_close(connection)
                    return await ctx.send(f"La ligne `{id.content}` a bien été supprimée de la table!")

    # Commands Error

    @commands.command(aliases=["dpt", "dt"])
    @commands.check(team_dev)
    async def drop_table(self, ctx, table):
        connection, cursor = db_connect()
        cursor.execute(f"""
            DROP TABLE {table}
            """)
        connection.commit()
        print(f"{table} a été supprimé!")
        await ctx.send(f"{table} a été supprimé!")
        db_close(connection)

    @commands.command(aliases=["dll", "dl"])
    @commands.check(team_dev)
    async def delete_line(self, ctx, name, value, table):
        connection, cursor = db_connect()
        cursor.execute(f"""
            DELETE FROM {table} WHERE {name}={value}
            """)
        connection.commit()
        print(f"{table}: {name} -> {value} a été supprimé!")
        await ctx.send(f"`{table}: {name} -> {value}` a été supprimé!")
        db_close(connection)

    @commands.command(aliases=["select", "sl"])
    async def select_from_table(self, ctx, select, _from):
        connection, cursor = db_connect()
        selection = cursor.execute(f"""
            SELECT {select} FROM {_from}
            """).fetchall()
        await ctx.send(str(selection))
        db_close(connection)

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
