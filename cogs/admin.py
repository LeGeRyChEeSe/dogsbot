import asyncio
from datetime import datetime, timezone
from traceback import format_exception
from io import BytesIO

import discord
from discord.colour import Colour
from discord.ext import commands

from events.functions import *


class Admin(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client

    def not_command(self, message):
        return message.content.startswith(str(self.client.command_prefix))

    def check_author(self, *args):
        def inner(message):
            ctx = args[0]
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
        emoji = payload.emoji

        guild: discord.Guild = discord.utils.find(
            lambda g: g.id == guild_id, self.client.guilds)
        channel = discord.utils.find(
            lambda g: g.id == channel_id, guild.channels)
        message = await channel.fetch_message(message_id)
        member = guild.get_member(user_id)

        if message.author.bot and message.pinned:

            for field in message.embeds[0].fields:
                message_reaction = field.name
                message_role_id = int(field.value.replace(
                    "<@&", "").replace(">", ""))
                if str(emoji) == str(message_reaction) or emoji.name == message_reaction:
                    role = discord.utils.get(
                        guild.roles, id=message_role_id)
                    await member.add_roles(role)
        else:
            message_reaction = read_file(
                "assets/Data/message_reactions.json", is_json=True)

            try:
                reaction = message_reaction[str(guild_id)][str(message_id)][0]
            except KeyError:
                return

            if str(reaction) != str(emoji):
                return

            role = guild.get_role(
                int(message_reaction[str(guild_id)][str(message_id)][1]))

            await member.add_roles(role)

        msg = f"{member.display_name}#{member.discriminator} s'est attribué le rôle {role.name}!"
        write_file(
            set_file_logs(guild_id), msg, is_log=True)
        await get_log_channel(self.client, payload, msg)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        user_id = payload.user_id
        message_id = payload.message_id
        guild_id = payload.guild_id
        channel_id = payload.channel_id
        emoji = payload.emoji

        guild = discord.utils.find(
            lambda g: g.id == guild_id, self.client.guilds)
        channel = discord.utils.find(
            lambda g: g.id == channel_id, guild.channels)
        message = await channel.fetch_message(message_id)
        member = guild.get_member(user_id)

        if message.author.bot and message.pinned:
            for embed in message.embeds:
                for field in embed.fields:
                    message_reaction = field.name
                    message_role_id = int(field.value.replace(
                        "<@&", "").replace(">", ""))
                    if str(emoji) == str(message_reaction) or emoji.name == message_reaction:
                        role = discord.utils.get(
                            guild.roles, id=message_role_id)
                        await member.remove_roles(role)
        else:
            message_reaction = read_file(
                "assets/Data/message_reactions.json", is_json=True)

            try:
                reaction = message_reaction[str(guild_id)][str(message_id)][0]
            except KeyError:
                return

            if str(reaction) != str(emoji):
                return

            role = guild.get_role(
                int(message_reaction[str(guild_id)][str(message_id)][1]))

            await member.remove_roles(role)

        msg = f"{member.display_name}#{member.discriminator} s'est retiré le rôle {role.name}!"
        write_file(set_file_logs(
            guild_id), msg, is_log=True)
        await get_log_channel(self.client, payload, msg)

    # Commands

    @ commands.command(name="clear", brief="Effacer des messages",
                       description="Permet de supprimer un nombre défini de messages dans un salon.",
                       usage="<nombre_de_messages>", aliases=["purge", "erase", "delete"])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, amount=5):
        sure = await ctx.reply(
            "Etes-vous bien sûr de vouloir effacer {amount} messages de ce canal (**o**/**n**)?")
        try:
            message = await self.client.wait_for("message", check=self.check_author(ctx), timeout=60.0)
        except asyncio.TimeoutError:
            await sure.edit(content="Temps écoulé!", delete_after=5.0)
            await ctx.message.delete()
        else:
            if message.content.lower() == "o":
                await ctx.channel.purge(limit=amount + 3)
                msg = f"{ctx.author.display_name} a effacé {amount} messages du salon {ctx.channel.name}!"
                write_file(set_file_logs(
                    ctx.guild.id), msg, is_log=True)
                await get_log_channel(self.client, ctx, msg)

            else:
                await sure.delete()
                await message.delete()
                await ctx.message.delete()

    @commands.command(name="kick", brief="Expulser un membre du serveur", description="Mentionnez le membre à expulser du serveur.", usage="<@membre>")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.reply(f"{member.mention} a été expulsé!")
        msg = f"L'utilisateur {member.display_name}#{member.discriminator} a été expulsé par {ctx.author.name}!"
        write_file(
            set_file_logs(ctx.guild.id), msg, is_log=True)
        await get_log_channel(self.client, ctx, msg)

    @commands.command(name="ban", brief="Bannir un membre du serveur", description="Mentionnez le membre à bannir du serveur et précisez ou non la raison.", usage="<@membre> <raison>")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason=None):
        await member.ban(reason=reason)
        await ctx.reply(f"{member.mention} a été banni! \n*Raison: {reason}")
        msg = f"L'utilisateur {member.display_name}#{member.discriminator} a été banni par {ctx.author.name} pour la raison suivante: {reason}"
        write_file(
            set_file_logs(ctx.guild.id), msg, is_log=True)
        await get_log_channel(self.client, ctx, msg)

    @commands.command(name="unban", brief="Débannir un membre du serveur", description="Indiquez le membre à débannir du serveur.", usage="<membre#1234>")
    @ commands.has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, *, member):
        banned_users = await ctx.guild.bans()
        member_name, member_discriminator = member.split('#')

        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await ctx.guild.unban(user)
                msg = f"{user.name}#{user.discriminator} a été débanni!"
                write_file(set_file_logs(
                    ctx.guild.id), msg, is_log=True)
                await get_log_channel(self.client, ctx, msg)
                await ctx.reply(msg)
                return

        await ctx.reply(f"{member_name}#{member_discriminator} n'est pas un utilisateur banni du serveur.")

    @ commands.command(hidden=True, name="bot", brief="Indique l'id du bot")
    @ commands.check(team_dev)
    async def bot(self, ctx: commands.Context):
        await ctx.reply(self.client.user.id)

    @ commands.command(name="changeprefix", brief="Modifier le prefix de commande",
                       description="Modifier le prefix de commande. Par défaut le prefix est `!`",
                       usage="<nouveau_prefix>", aliases=["prefix", "pfx"])
    @ commands.has_permissions(manage_guild=True)
    async def changeprefix(self, ctx: commands.Context, prefix):

        async with self.client.pool.acquire() as con:
            await con.execute('''
            UPDATE global_config SET guild_prefix = $1 WHERE guild_id = $2
            ''', prefix, ctx.guild.id)

        await ctx.send(f"||@everyone|| Le préfix a été changé: `{prefix}`")
        msg = f"Nouveau prefix '{prefix}'!"
        write_file(
            set_file_logs(ctx.guild.id), msg, is_log=True)
        await get_log_channel(self.client, ctx, msg)

    @ commands.group(name="roles", brief="Ajouter des rôles avec des réactions", usage="<titre_du_message>",
                     description="Renvoie un embed contenant l'attribution de chaque réaction à un rôle spécifique. "
                     "Ne peut pas contenir une même réaction pour 2 rôles à la fois.", aliases=["addr", "ar"], invoke_without_command=True)
    @ commands.has_permissions(manage_roles=True)
    async def roles(self, ctx: commands.Context, *args):

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
        embed_sender.description = "__**Veuillez entrer des rôles (20 max) séparés d'un espace entre chaque**__ *(Ex: @admin @nitro @helper ...)*"
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

        if len(roles.role_mentions) > 20:
            warning = await ctx.send(":warning: **Trop de rôles indiqués** *(seuls les 20 premiers on été pris en compte)* :warning:")

        roles.role_mentions.sort(reverse=True)

        for role in roles.role_mentions:
            if roles.role_mentions.index(role) >= 20:
                roles.role_mentions.pop(roles.role_mentions.index(role))

            embed_sender.colour = Colour.green()
            embed_sender.title = f":white_check_mark: {role.name} :white_check_mark:"
            embed_sender.description = f"Ajoutez une réaction à ce message pour le rôle **{role.name}**"
            embed_sender.clear_fields()
            embed_sender.add_field(name="Rôle", value=role.mention)
            embed_sender.timestamp = datetime.utcnow()
            embed_sender.set_footer(
                text=f"{roles.role_mentions.index(role)}/{len(roles.role_mentions[:20])}")
            await sender.edit(embed=embed_sender)

            done, pending = await asyncio.wait([self.client.wait_for("message", check=check_exit), self.client.wait_for("raw_reaction_add", check=check_emoji)], return_when=asyncio.FIRST_COMPLETED)

            try:
                stuff = done.pop().result()
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
        try:
            await warning.delete()
        except:
            pass
        await sender.delete()

        embed.title = " ".join(args) or "Attribution des Rôles"
        embed.description = "Cliquez sur l'une des réactions à ce message pour obtenir le rôle associé."
        embed.colour = discord.Colour(126)
        embed.set_author(name=ctx.message.guild.name)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.timestamp = datetime.now(timezone.utc)

        for key, value in receivers.items():
            embed.add_field(name=value.emoji,
                            value=key.mention, inline=True)

        message = await ctx.send(embed=embed)
        await message.pin(reason="Roles Attribution")

        await ctx.channel.purge(limit=1)

        for emoji in receivers.values():
            await message.add_reaction(emoji.emoji)

    @ roles.command(name="id", brief="Ajouter une réaction à un message donné (indiquer l'id du message) pour avoir un rôle donné")
    @commands.has_permissions(manage_roles=True)
    async def id(self, ctx: commands.Context):

        details = []

        id = ""

        def check_role(msg: discord.Message):
            return msg.author.id is ctx.author.id and (msg.content.strip().startswith("<@&") and msg.content.strip()
                                                       .endswith(">")) or (msg.content == "exit")

        def check_emoji(payload: discord.RawReactionActionEvent):
            return payload.member.id is ctx.author.id and payload.message_id == message.id

        embed = discord.Embed(timestamp=datetime.utcnow()).set_author(name=ctx.author.display_name,
                                                                      icon_url=ctx.author.avatar_url)
        embed.description = f"{ctx.author.mention}, Veuillez indiquer l'__**ID**__ du message. Pour cela faites un clic droit sur le message puis tout en bas de la liste, cliquez sur **Copier l'identifiant**\n*Si vous ne voyez pas ce bouton, veuillez activer le mode développeur (`Paramètres utilisateur` -> `Apparence` -> `Mode développeur`)*"
        message = await ctx.send(embed=embed)

        try:
            id: discord.Message = await self.client.wait_for("message", check=self.check_author, timeout=120.0)
        except asyncio.TimeoutError:
            embed.description = f"Temps écoulé {ctx.author.mention}"
            return await message.edit(embed=embed)
        else:
            await id.delete()
            id = id.content

        while id != "exit":
            try:
                int(id)
            except ValueError:
                embed.description = "Veuillez indiquer l'identifiant du message **uniquement**"
                await message.edit(embed=embed)
                try:
                    id: discord.Message = await self.client.wait_for("message", check=self.check_author, timeout=120.0)
                except asyncio.TimeoutError:
                    embed.description = f"Temps écoulé {ctx.author.mention}"
                    return await message.edit(embed=embed)
                else:
                    await id.delete()
                    id = id.content
            else:
                break

        details.append(id)

        message_fetched = await ctx.fetch_message(id)

        embed.description = "Veuillez indiquer le rôle que vous voulez attribuer"
        await message.edit(embed=embed)

        try:
            role: discord.Message = await self.client.wait_for(
                "message", check=check_role, timeout=120.0)
        except asyncio.TimeoutError:
            embed.description = f"Temps écoulé {ctx.author.mention}"
            return await message.edit(embed=embed)
        else:
            await role.delete()
            role: discord.Role = role.role_mentions[0]

        details.append(role)

        embed.description = "Veuillez ajouter une réaction à __**ce**__ message pour l'ajouter au message sélectionné"
        await message.edit(embed=embed)

        try:
            reaction: discord.RawReactionActionEvent = await self.client.wait_for(
                "raw_reaction_add", check=check_emoji, timeout=120.0)
        except asyncio.TimeoutError:
            embed.description = f"Temps écoulé {ctx.author.mention}"
            return await message.edit(embed=embed)

        details.append(reaction.emoji)

        await message_fetched.add_reaction(reaction.emoji)

        message_reactions_file = read_file(
            "assets/Data/message_reactions.json", is_json=True)
        exists = False
        for i in message_reactions_file.keys():
            if i == str(ctx.guild.id):
                exists = True
        if not exists:
            message_reactions_file[str(ctx.guild.id)] = {}

        message_reactions_file[str(ctx.guild.id)][message_fetched.id] = [
            str(reaction.emoji), str(role.id)]

        embed.description = "Effectué. Veuillez retrouver ci-dessous les informations de la commande."
        embed.add_field(name="ID du message", value=details[0], inline=False)
        embed.add_field(name="Rôle à attribuer",
                        value=details[1].mention, inline=False)
        embed.add_field(name="Réaction associée",
                        value=details[2], inline=False)
        await message.edit(embed=embed)
        await message.clear_reactions()

        write_file("assets/Data/message_reactions.json",
                   message_reactions_file, is_json=True, mode="w")

    @ commands.command(name="eval", hidden=True)
    @ commands.check(team_dev)
    async def eval(self, ctx: commands.Context):
        try:
            message_to_execute = await self.client.wait_for("message", check=self.check_author(ctx), timeout=300)
        except asyncio.TimeoutError:
            return
        message_executed = eval(message_to_execute.content)
        await message_to_execute.delete()
        await ctx.send(f"> {message_to_execute.content}\n{message_executed}")

    @ commands.group(name="log", hidden=False, aliases=["logs"], brief="Envoie un fichier de log du serveur en message privé", invoke_without_command=True)
    @ commands.has_permissions(manage_guild=True)
    async def log(self, ctx: commands.Context):
        async with ctx.channel.typing():
            _log_file = discord.File(
                set_file_logs(ctx.guild.id), filename=f"logs_{ctx.guild.id}_{datetime.utcnow()}.log")
            await ctx.author.send(file=_log_file)
            await ctx.send(f"Regarde tes MP {ctx.author.mention}!")
            msg = f"Fichier de log du serveur {ctx.guild.name} généré par {ctx.author.display_name}#{ctx.author.discriminator}(id: {ctx.guild.id})"
            write_file(
                log_file, msg, is_log=True)
            await get_log_channel(self.client, ctx, msg)

    @ log.command(name="bot", brief="Envoie un fichier de log du bot en message privé", check=team_dev)
    async def bot(self, ctx: commands.Context):
        async with ctx.channel.typing():
            _log_file = discord.File(
                log_file, filename=f"logs_{self.client.user.id}_{datetime.utcnow()}.log")
            await ctx.author.send(file=_log_file)
            await ctx.send(f"Regarde tes MP {ctx.author.mention}!")
            write_file(
                log_file, f"Fichier de log du bot généré par {ctx.author.display_name}#{ctx.author.discriminator}(id: {ctx.guild.id})", is_log=True)

    @ log.command(name="salon", brief="Définir un salon où tous les logs seront postés", usage="<id_du_salon>")
    async def salon(self, ctx: commands.Context, *, args=None):
        if not args:
            message = await ctx.send(f"Quel est le salon qui va accueillir les logs {ctx.author.mention}?")
            try:
                channel: discord.Message = await self.client.wait_for("message", check=self.check_author(ctx), timeout=120.0)
            except asyncio.TimeoutError:
                await message.edit(f"Temps écoulé {ctx.author.mention}!")
                return
            else:
                channel = channel.channel_mentions[0].id
        else:
            channel = args

        channel = await self.client.fetch_channel(channel)

        async with self.client.pool.acquire() as con:
            await con.execute('''
            INSERT INTO logs_channel
            VALUES($1, $2)
            ON CONFLICT (guild_id)
            DO UPDATE
            SET channel_id = $2
            WHERE logs_channel.guild_id = $1
            ''', ctx.guild.id, channel.id)

        msg = f"Le salon des logs a été défini sur {self.client.get_channel(channel.id).mention}."
        write_file(set_file_logs(ctx.guild.id),
                   msg, is_log=True)
        await get_log_channel(self.client, ctx, msg)

        await ctx.send(f"Le salon des logs est le salon {self.client.get_channel(channel.id).mention} !")

    @ commands.group(name="welcome", invoke_without_command=True, brief="Définir un salon/message de bienvenue", description="Permet de définir un salon de bienvenue, ainsi que le message d'accueil.\nPar défaut le nom du nouveau membre est affiché au début de votre message suivis d'une virgule. Vous pouvez choisir l'emplacement du nom du nouveau membre où vous voulez simplement en écrivant $member à l'emplacement souhaité.\nPar exemple: `Bienvenue parmi nous $member !`", usage="message|channel")
    @ commands.has_permissions(manage_guild=True)
    async def welcome(self, ctx: commands.Context):
        await ctx.reply(f"Pour choisir un salon d'accueil, tapez `{ctx.prefix}welcome channel <#id_du_salon>`\nPour choisir un message de bienvenue, tapez `{ctx.prefix}welcome message <votre_message>`")

    @ welcome.command(name="channel")
    async def channel(self, ctx: commands.Context):
        welcome_channel_id = ctx.message.channel_mentions[0].id

        async with self.client.pool.acquire() as con:
            await con.execute('''
            INSERT INTO welcome(guild_id, welcome_channel_id)
            VALUES($1, $2)
            ON CONFLICT (guild_id)
            DO UPDATE
            SET welcome_channel_id = $2
            WHERE welcome.guild_id = $1
            ''', ctx.guild.id, welcome_channel_id)

        msg = f"Le salon de bienvenue a été défini sur {self.client.get_channel(welcome_channel_id).mention}."
        write_file(set_file_logs(ctx.guild.id),
                   msg, is_log=True)
        await get_log_channel(self.client, ctx, msg)

        await ctx.reply(f"Le salon de bienvenue est le salon {self.client.get_channel(welcome_channel_id).mention} !")

    @ welcome.command(name="message")
    async def message(self, ctx: commands.Context, *, args):
        welcome_message = args

        async with self.client.pool.acquire() as con:
            await con.execute('''
            INSERT INTO welcome(guild_id, welcome_message)
            VALUES($1, $2)
            ON CONFLICT (guild_id)
            DO UPDATE
            SET welcome_message = $2
            WHERE welcome.guild_id = $1
            ''', ctx.guild.id, welcome_message)

        msg = f"Le message de bienvenue a été définis sur '{welcome_message}'."
        write_file(set_file_logs(ctx.guild.id),
                   msg, is_log=True)
        await get_log_channel(self.client, ctx, msg)

        await ctx.reply(f"Le message de bienvenue est:\n\n\"{welcome_message}\"\n\nIl sera posté dans le salon de bienvenue à chaque arrivée d'un membre dans le serveur!")

    @ bot.error
    async def bot_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.reply("Vous n'êtes pas <@!440141443877830656>!")

    @ unban.error
    async def unban_error(self, ctx, error):
        if ValueError(error):
            await ctx.reply("L'utilisateur doit être écrit de la forme `nom#XXXX`.")


def setup(client):
    client.add_cog(Admin(client))
