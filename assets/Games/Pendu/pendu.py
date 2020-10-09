from assets.Games.Pendu.fonctions import *


def set_pendu(user, ctx, connection, cursor):
    user.game_user[ctx.author.id] = Pendu(ctx, connection, cursor)


class Pendu:

    def __init__(self, ctx, connection, cursor):
        self.ctx = ctx
        self.is_running = True
        self.is_find = False
        self.is_over = False
        self.connection = connection
        self.cursor = cursor
        self.taille_mot = 8
        self.mot = word_init(self.connection, self.cursor, self.taille_mot)
        self.letters_list = []
        self.user_chances = 0
        self.word_hidden = self.set_word_hidden()
        self.message_to_delete = None
        self.chances = len(self.mot)

    async def is_find_or_over(self):
        if not "\*" in self.word_hidden:
            self.is_find = True
        elif self.user_chances >= self.chances:
            self.is_over = True

        if self.is_find:
            if self.user_chances == 1:
                self.message_to_delete = await self.ctx.send(f"Bravo! Vous avez trouvé le mot {self.mot} en {self.user_chances} coup!\nVoulez-vous rejouer (o/n)?")
                return True
            else:
                self.message_to_delete = await self.ctx.send(
                    f"Bravo vous avez trouvé le mot {self.mot} en {self.user_chances} coups!\nVoulez-vous rejouer (o/n)?")
                return True

        elif self.is_over:
            self.message_to_delete = await self.ctx.send(f"Perdu! Le mot était {self.mot}!\nVoulez-vous rejouer (o/n)? ")
            return True

    async def retry(self, user_quit="o"):
        if user_quit == "o":
            return "o"
        if user_quit == "n":
            self.is_running = False
            return await self.ctx.send("Ok! A la prochaine!")

    async def check_letter(self, letter):
        return len(letter) > 1 or len(letter) < 1

    def set_word_hidden(self):
        word_hidden = ""
        for i in self.mot:
            word_hidden += "\*"
        return word_hidden

    async def running(self, letter):

        if await self.check_letter(letter):
            self.message_to_delete = await self.ctx.send("Veuillez entrer une lettre valide.")
            return

        self.letters_list.append(letter)

        self.word_hidden, self.user_chances = await user_choice(self)

        if not await self.is_find_or_over():
            self.message_to_delete = await self.ctx.send(self.word_hidden + f"\nNombre de chances restantes: {self.chances - self.user_chances}\n\nVeuillez entrer une lettre")
