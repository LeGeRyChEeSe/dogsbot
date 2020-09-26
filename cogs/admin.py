import discord
from discord.ext import commands
import json
from datetime import datetime, timezone
import cse
import env
import asyncio
import sqlite3

jonction = None


class Admin(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Events

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
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
                        await member.add_roles(role)
                        return print(f"{member.mention} s'est attribué le rôle {role.name}!")

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
                        return print(f"{member.mention} s'est destitué du rôle {role.name}!")

    # Commands

    @commands.command(brief="Bot latency", description="Réponds par 'Pong!' en indiquant la latence du bot.")
    @commands.has_permissions(manage_messages=True)
    async def ping(self, ctx):
        await ctx.send(f"Pong! (Latence du bot: {round(self.client.latency * 1000)}ms)")

    @commands.command(brief="Effacer des messages", description="Permet de supprimer un nombre défini de messages dans un salon.", usage="<nombre de messages>", aliases=["purge", "erase", "delete"])
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount=5):
        await ctx.channel.purge(limit=amount + 1)
        print(f"{amount} messages ont été effacé du salon {ctx.channel.name}")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(f"{member.mention} a été expulsé!")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await member.ban(reason=reason)
        await ctx.send(f"{member.mention} a été banni!")

    @commands.command()
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

    @commands.command(name="changeprefix")
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

    @commands.command()
    async def search(self, query):
        search = cse.Search(env.API_KEY)
        results = await search.search(query)
        print(results[0].title)

    @commands.command(hidden=True)
    @commands.check(team_dev)
    async def bdd(self, ctx, *table):
        connection = sqlite3.connect("./assets/Data/pairs.db")
        cursor = connection.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS pairs(
            id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            questions TEXT,
            responses TEXT
        );
        """)
        connection.commit()

        pairs = [
                ["test", ["Réussi!"]],
                ["(bonjour|salut|hey|slt|coucou|wesh|bonsoir|bon matin|hello|hi|cc|hola)",
                 ["Coucou toi ", f"Hey!", "Yo, la forme ? ", "Salut ça va ? ", "\**Bâille* \* Coucou... :yawning_face: "]]
        ]

        for questions, responses in pairs:
            str_response = ""
            for response in responses:
                str_response += f"{response}"
            cursor.execute("""
            INSERT INTO pairs(questions, responses) VALUES(?, ?)
            """, (questions, str_response))
        connection.commit()

        cursor.execute("""
         SELECT responses FROM pairs WHERE questions LIKE "%cc%"
         """)
        question1 = cursor.fetchall()
        await ctx.send(question1)
    # Commands Error

    @bot.error
    async def bot_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("Vous n'êtes pas <@!440141443877830656>!")

    @unban.error
    async def unban_error(self, ctx, error):
        if ValueError(error):
            print(error)
            await ctx.send("L'utilisateur doit être écrit de la forme `nom#XXXX`.")


def setup(client):
    client.add_cog(Admin(client))
