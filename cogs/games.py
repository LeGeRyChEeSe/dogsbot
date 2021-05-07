from os import error
import asyncio
import random
import traceback

import discord
from discord.ext import commands
from events.functions import *

from assets.Games.Pendu.pendu import *


class Games(commands.Cog):

    def __init__(self, client: commands.Bot):
        self.client = client
        self.game_user = {}

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

        async with self.client.pool.acquire() as con:
            authorized_starters = await con.fetch('''
            SELECT id_starter, is_role
            FROM authorized_starters
            WHERE id_tournament = $1
            ''', id_tournament)

        print(authorized_starters)

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

    @ commands.group(name="tournoi", aliases=["tournois", "tounrois", "tounroi", "tournament", "competition"], brief="Lister les tournois disponibles", invoke_without_command=True)
    async def tournoi(self, ctx: commands.Context):

        embed = discord.Embed()
        embed.title = "Tournois en cours"
        embed.description = f"Liste des tournois en cours | `{ctx.prefix}tournoi more <ID_du_tournoi>` pour plus d'informations"
        embed.color = discord.Color.greyple()

        # List of tournaments

        async with self.client.pool.acquire() as con:
            tournaments = await con.fetch('''
            SELECT id_tournament, title, date, nb_max_participants, nb_participants
            FROM tournaments
            WHERE guild_id = $1
            ''', ctx.guild.id)

        for tournament in tournaments:
            embed.add_field(
                name=tournament.get('title').title(), value=f"__**ID:**__ `{tournament.get('id_tournament')}`\n__**Date début:**__ {tournament.get('date')}")

        # Check if ctx.author is registered into a tournament

        async with self.client.pool.acquire() as con:
            into_tournament = await con.fetch('''
            SELECT DISTINCT id_participant, id_tournament
            FROM tournament_participants
            WHERE id_participant = $1
            ''', ctx.author.id)

        if into_tournament:

            for i in tournaments:

                if into_tournament[0].get('id_tournament') == i.get('id_tournament'):
                    # We fetch the current tournament were the member participate

                    async with self.client.pool.acquire() as con:
                        current_tournament = await con.fetch('''
                        SELECT id_tournament, title
                        FROM tournaments
                        WHERE guild_id = $1 AND id_tournament = $2
                        ''', ctx.guild.id, into_tournament[0].get('id_tournament'))

                    embed.add_field(name=f":white_check_mark: Vous êtes inscrit au tournoi {current_tournament[0].get('title').title()} :white_check_mark: ",
                                    value=f"`{current_tournament[0]}`", inline=False)

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
            # If the member wants to change tournament

            async with self.client.pool.acquire() as con:
                new_tournament = await con.fetch('''
                SELECT DISTINCT id_tournament, title, nb_max_participants, nb_participants
                FROM tournaments
                WHERE guild_id = $1 AND id_tournament = $2
                ''', ctx.guild.id, new_participant.content)

            if not new_tournament:
                return
            else:
                await new_participant.delete()

            embed = discord.Embed(
                title="Inscription Tournoi", timestamp=datetime.datetime.utcnow(), color=discord.Color.green())
            embed.set_footer(
                text=f"Tapez la commande {ctx.prefix}tournoi pour voir les tournois créés.", icon_url=ctx.author.avatar_url)

            async with self.client.pool.acquire() as con:
                already_registered = await con.fetch('''
                SELECT DISTINCT id FROM tournament_participants
                WHERE id_tournament = $1 AND id_participant = $2
                ''', new_tournament[0].get('id_tournament'), ctx.author.id)
            # If ctx.author is registered into a new_tournament
            if into_tournament:
                async with self.client.pool.acquire() as con:
                    current_tournament = await con.fetch('''
                    SELECT DISTINCT nb_participants
                    FROM tournaments
                    WHERE id_tournament = $1
                    ''', into_tournament[0].get('id_tournament'))

            elif new_tournament[0].get('nb_max_participants') == new_tournament[0].get('nb_participants'):
                embed.color = discord.Color.red()
                embed.description = "Tournoi complet!"
                return await message.edit(embed=embed)

            elif already_registered != None:
                embed.description = f"Vous êtes déjà inscrit au tournoi __**{new_tournament[0].get('title').title()}**__ {ctx.author.mention}!\n\n*Pour changer de tournoi, vous pouvez simplement taper l'id d'un autre tournoi (après avoir tapé la commande `{ctx.prefix}tournoi`) ou taper la commande `{ctx.prefix}tournoi leave` pour quitter le tournoi auquel vous êtes actuellement inscrit!*"

            async with self.client.pool.acquire() as con:
                await con.execute('''
                INSERT INTO tournament_participants(id_tournament, id_participant)
                VALUES($1, $2)
                ''', new_tournament[0].get('id_tournament'), ctx.author.id)

                await con.execute('''
                UPDATE tournaments
                SET nb_participants = $1
                WHERE id_tournament = $2
                ''', new_tournament[0].get('nb_participants')+1, new_tournament[0].get('id_tournament'))

                if into_tournament != None:
                    await con.execute('''
                    UPDATE tournaments
                    SET nb_participants = $1
                    WHERE id_tournament = $2
                    ''', current_tournament[0].get('nb_participants')-1, into_tournament[0].get('id_tournament'))
            embed.description = f"Félicitations {ctx.author.mention}, vous vous êtes inscrit au tournoi __**{new_tournament[1].title()}**__\n\n*Pour changer de tournoi, vous pouvez simplement taper l'id d'un autre tournoi (après avoir tapé la commande `{ctx.prefix}tournoi`) ou taper la commande `{ctx.prefix}tournoi leave` pour quitter le tournoi auquel vous êtes actuellement inscrit!*"

        await message.edit(embed=embed)

    @ tournoi.command(name="create", brief="Créer un tournoi", description="Indiquez tous les paramètres du tournoi après avoir tapé la commande tournoi create.\nParamètres disponibles:\n- Nom du tournoi\n- Description du tournoi *(par défaut: `NONE`)*\n- Récompense du tournoi *(par défaut: `NONE`)*\n- Nombre maximum de participants *(par défaut: `8`)*")
    @ commands.has_permissions(manage_messages=True)
    async def create(self, ctx: commands.Context):

        names = {"title": "Nom du tournoi", "description": "Description du tournoi *(par défaut: `NONE`)*", "rules": "Règles du tournoi", "reward": "Récompense du tournoi *(par défaut: `NONE`)*",
                 "date": "Date/Heure du début du tournoi *(Format de la date : `jj/mm/aa HH:MM` Ex: `25/06/21 15:00`)*", "nb_max_participants": "Nombre maximum de participants *(par défaut: `8`)*", "authorized_starters": f"Membres ou/et rôles autorisés à démarrer un tournoi, l'arrêter et modifier le classement *(par défaut: {ctx.author.mention})*", "rounds": "Nombre de manches du tournoi *(par défaut: `4`)*"}

        id_tournament = random_string(8)

        async with self.client.pool.acquire() as con:
            await con.execute('''
            INSERT INTO tournaments(guild_id, id_tournament)
            VALUES($1, $2)
            ''', ctx.guild.id, id_tournament)

        embed = discord.Embed(
            title="Tournoi créé", timestamp=datetime.datetime.utcnow(), color=discord.Color.greyple())

        temp_embed = discord.Embed(title="Création de tournoi",
                                   timestamp=datetime.datetime.utcnow(), color=discord.Color.greyple())

        temp_response = {}
        temp_response["authorized_starters"] = []

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

                if key == "date" and name != None:
                    try:
                        datetime.datetime.strptime(name, dateFormatter)
                    except:
                        temp_embed.description = f"Erreur de conversion, veuillez entrer une date du type `jj/mm/aa HH:MM` après avoir retapé la commande `{ctx.prefix}{ctx.command.qualified_name}`"
                        await message.edit(embed=temp_embed)
                        return
                    else:
                        temp_response[key] = datetime.datetime.strptime(
                            name, dateFormatter)

                elif key == "authorized_starters":

                    if temp_name.mentions != None:
                        for member in temp_name.mentions:
                            temp_response["authorized_starters"].append(
                                (member.id, False))

                    if temp_name.role_mentions != None:
                        for member in temp_name.role_mentions:
                            temp_response["authorized_starters"].append(
                                (member.id, True))

                else:
                    try:
                        int(name)
                    except:
                        temp_response[key] = name
                    else:
                        temp_response[key] = int(name)

                embed.add_field(
                    name=value, value=name, inline=False)

        async with self.client.pool.acquire() as con:
            # Création du tournoi si celui-ci n'existe pas déjà
            await con.execute('''
            INSERT INTO tournaments(guild_id, id_tournament, title, description, rules, reward, date, nb_max_participants, rounds)
            VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (title)
            DO UPDATE
            SET title = $3,
            description = $4,
            rules = $5,
            reward = $6,
            date = $7,
            nb_max_participants = $8,
            rounds = $9
            WHERE tournaments.guild_id = $1 AND tournaments.id_tournament = $2
            ''', ctx.guild.id, id_tournament, temp_response["title"], temp_response["description"], temp_response["rules"], temp_response["reward"], temp_response["date"], temp_response["nb_max_participants"], temp_response["rounds"])

            for mention in temp_response["authorized_starters"]:
                await con.execute('''
                INSERT INTO authorized_starters(id_tournament, id_starter, is_role) VALUES($1, $2, $3)
                ''', id_tournament, mention[0], mention[1])

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

        async with self.client.pool.acquire() as con:
            deleted_tournament = await con.fetch('''
            SELECT id_tournament, title FROM tournaments WHERE guild_id = $1 AND id_tournament = $2
            ''', ctx.guild.id, id)
            await con.execute('''
            DELETE FROM tournaments WHERE guild_id = $1 AND id_tournament = $2
            ''', ctx.guild.id, id)
            await con.execute('''
            DELETE FROM tournament_participants
            WHERE id_tournament = $1
            ''', id)
            await con.execute('''
            DELETE FROM authorized_starters
            WHERE id_tournament = $1
            ''', id)

        embed = discord.Embed(
            title="Tournoi supprimé", timestamp=datetime.datetime.utcnow(), color=discord.Color.red())
        embed.add_field(
            name=deleted_tournament[0].get('title').title(), value=f"`{deleted_tournament[0].get('id_tournament')}`")
        embed.set_footer(
            text=f"Tapez la commande {ctx.prefix}tournoi pour voir les tournois créés.", icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

        write_file(
            log_file, "Des données ont été supprimé dans la table tournaments!", is_log=True)

    @ tournoi.command(name="leave", brief="Quitter un tournoi", usage="<id_du_tournoi>")
    async def leave(self, ctx: commands.Context):

        embed = discord.Embed(
            title="Quitter un Tournoi", timestamp=datetime.datetime.utcnow(), color=discord.Color.orange())
        embed.set_footer(
            text=f"Tapez la commande {ctx.prefix}tournoi pour voir les tournois créés.", icon_url=ctx.author.avatar_url)

        async with self.client.pool.acquire() as con:

            current_tournament = await con.execute('''
            SELECT DISTINCT id_tournament, id_participant 
            FROM tournament_participants
            WHERE id_participant = $1
            ''', ctx.author.id)

            if not current_tournament:
                embed.description = f"Vous n'êtes actuellement inscrit à aucun tournoi {ctx.author.mention}."

            else:
                await con.execute('''
                DELETE FROM tournament_participants
                WHERE id_participant = $1
                ''', ctx.author.id)
                tournament = await con.execute('''
                SELECT title FROM tournaments
                WHERE id_tournament = $1
                ''', current_tournament[0].get('id_tournament'))

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


def setup(client):
    client.add_cog(Games(client))
