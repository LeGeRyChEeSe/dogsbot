from os import error
import asyncio
import asyncpg
from random import choice
import traceback

import discord
from discord.ext import commands
from events.functions import *


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

    async def check_authorized_starters(self, ctx: commands.Context, tournament_id: int):

        async with self.client.pool.acquire() as con:
            authorized_starters = await con.fetch('''
            SELECT id_starter, is_role
            FROM authorized_starters
            WHERE tournament_id = $1
            ''', tournament_id)

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

        await ctx.send(f"{choice(responses)}")

    @commands.group(name="pendu", brief="Jouez au Pendu!", description="Jouez simplement au célèbre jeu du Pendu!", invoke_without_command=True)
    async def pendu(self, ctx: commands.Context):
        await ctx.reply(f"Pour jouer au Pendu, tapez `{ctx.prefix}pendu play`\nPour ajouter un mot à la base de données du Pendu, tapez `{ctx.prefix}pendu add` suivis de votre mot, par exemple: `{ctx.prefix}pendu add corde`")

    @pendu.command(name="play", aliases=["jouer", "p"])
    async def play(self, ctx: commands.Context):
        async with self.client.pool.acquire() as con:
            word = await con.fetch('''
            SELECT word
            FROM pendu
            ORDER BY random()
            LIMIT 1
            ''')

        word = word[0].get("word")
        hidden_word = ""
        is_word_found = False
        is_over = False
        used_letters = []
        tentatives = 8

        for _ in word:
            hidden_word += "_"

        hidden_word = " ".join(letter for letter in hidden_word)

        embed = discord.Embed(colour=discord.Color.magenta(), timestamp=datetime.utcnow())
        embed.set_footer(text=ctx.author, icon_url=ctx.guild.icon_url)
        embed.set_author(name=hidden_word.upper())
        embed.add_field(name="Tentatives restantes", value=8)
        embed.add_field(name="Lettres utilisées", value="Aucune")


        pendu_message: discord.Message = await ctx.reply(embed=embed)

        while not is_word_found and not is_over:
            try:
                letter: discord.Message = await self.client.wait_for("message", check=self.check_author, timeout=120.0)
            except asyncio.TimeoutError:
                await pendu_message.delete()
                is_over = True
                break
            else:
                letter_content = letter.content.strip().lower()
                if len(letter_content) != 1:
                    await letter.delete()
                    continue
            
            if letter_content in word:
                hidden_word = ""

                if letter_content not in used_letters:
                    used_letters.append(letter_content)
                    embed.set_field_at(1, name="Lettres utilisées", value=", ".join(used_letters).upper())
                else:
                    tentatives -= 1
                    embed.set_field_at(0, name="Tentatives restantes", value=tentatives)

                for word_letter in word:
                    if word_letter in used_letters:
                        hidden_word += word_letter.upper()
                    else:
                        hidden_word += "_"
                hidden_word = " ".join(letter_content for letter_content in hidden_word)
                
                embed.set_author(name=hidden_word)
            else:
                if letter_content not in used_letters:
                    used_letters.append(letter_content)
                    embed.set_field_at(1, name="Lettres utilisées", value=", ".join(used_letters).upper())
                tentatives -= 1
                embed.set_field_at(0, name="Tentatives restantes", value=tentatives)

            await pendu_message.edit(embed=embed)
            await letter.delete()

            if tentatives == 0:
                is_over = True
            elif word.upper() == hidden_word.replace(" ", ""):
                is_word_found = True
        
        if is_over:
            embed.colour = discord.Colour.red()
            embed.title = f"Dommage! Tu n'as pas trouvé le mot {word.upper()} malgré les 8 tentatives données! Retente ta chance!"
        elif is_word_found:
            embed.colour = discord.Colour.green()
            embed.title = f"Bravo! tu viens de trouver le mot {word.upper()} en {8-tentatives+1} tentatives!"
        
        embed.set_author(name=word.upper())
        await pendu_message.edit(embed=embed)

    @pendu.command(name="add", aliases=["a", "ad"])
    async def _add(self, ctx: commands.Context, word):
        async with self.client.pool.acquire() as con:
            try:
                await con.execute('''
                INSERT INTO pendu(word)
                VALUES($1)
                ''', word)
            except asyncpg.exceptions.UniqueViolationError:
                await ctx.reply("Ce mot a déjà été ajouté à ma base de données!")
            except asyncpg.exceptions.StringDataRightTruncationError:
                await ctx.reply("Le mot est plus long que 26 lettres, veuillez en entrer un avec moins de lettres!")
            except error as e:
                print(e)
                await ctx.reply("Une erreur est survenue!")
            else:
                await ctx.reply("Votre mot à bien été ajouté!")

    @ commands.group(name="tournoi", aliases=["tournois", "tounrois", "tounroi", "tournament", "competition"], brief="Lister les tournois disponibles", invoke_without_command=True)
    async def tournoi(self, ctx: commands.Context):
        await ctx.reply("Restructuration en cours...")


def setup(client):
    client.add_cog(Games(client))
