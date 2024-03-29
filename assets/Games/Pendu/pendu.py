import datetime

from discord.ext import commands
from discord import Embed

from assets.Games.Pendu.fonctions import *


def set_pendu(user, ctx, connection, cursor):
    user.game_user[ctx.author.id] = Pendu(ctx, connection, cursor)


class Pendu:

    def __init__(self, ctx, connection, cursor):
        self.ctx: commands.Context = ctx
        self.is_running = True
        self.is_find = False
        self.is_over = False
        self.connection = connection
        self.cursor = cursor
        self.taille_mot = 25
        self.mot = ""
        self.letters_list = []
        self.user_chances = 0
        self.word_hidden = self.set_word_hidden()
        self.message_to_delete = None
        self.chances = 8

    async def set_mot(self):
        self.mot = await word_init(self.connection, self.cursor, self.taille_mot)

    async def is_find_or_over(self):
        if not "_" in self.word_hidden:
            self.is_find = True
        elif self.user_chances >= self.chances:
            self.is_over = True

        if self.is_find:
            if self.user_chances == 1:
                self.message_to_delete = await self.ctx.send(
                    f"Bravo {self.ctx.author.mention}! Vous avez trouvé le mot `{self.mot}` en {self.user_chances}/{self.chances} coup!\nVoulez-vous rejouer (**o**/**n**)?")
                return True
            else:
                self.message_to_delete = await self.ctx.send(
                    f"Bravo {self.ctx.author.mention}! Vous avez trouvé le mot `{self.mot}` en {self.user_chances}/{self.chances} coups!\nVoulez-vous rejouer (**o**/**n**)?")
                return True

        elif self.is_over:
            self.message_to_delete = await self.ctx.send(
                f"Perdu {self.ctx.author.mention}! Le mot était `{self.mot}`!\nVoulez-vous rejouer (**o**/**n**)? ")
            return True

    async def retry(self, user_quit="o"):
        if user_quit == "o":
            return "o"
        if user_quit == "n":
            self.is_running = False
            return "n"

    async def check_letter(self, letter):
        return len(letter) > 1 or len(letter) < 1

    def set_word_hidden(self):
        word_hidden = ""
        for i in self.mot:
            word_hidden += "_"
        return word_hidden

    def set_embed(self):
        embed = Embed()
        word_hidden_split = []
        for i in self.word_hidden:
            word_hidden_split.append(i)
        word_hidden_with_spaces = " ".join(word_hidden_split)
        embed.set_author(name=word_hidden_with_spaces.upper())
        embed.add_field(name="Chances restantes", value=str(
            self.chances - self.user_chances), inline=True)
        embed.add_field(name="Lettres utilisées", value=str(
            ", ".join(self.letters_list)).upper(), inline=False)
        embed.set_thumbnail(url=self.ctx.author.avatar_url)
        embed.set_footer(text=self.ctx.author.name)
        embed.timestamp = datetime.datetime.utcnow()
        return embed

    async def running(self, letter):

        if await self.check_letter(letter):
            self.message_to_delete = await self.ctx.send(f"{self.ctx.author.mention} Veuillez entrer une lettre valide.")
            return

        self.letters_list.append(letter)

        self.word_hidden, self.user_chances = user_choice(self)

        if not await self.is_find_or_over():
            embed = self.set_embed()

            self.message_to_delete = await self.ctx.send(embed=embed)
