from random import choice

from assets.Games.Pendu.donnees import *


def word_init():
    mot = choice(mots)
    while len(mot) > 8:
        mot = choice(mots)
    return mot


async def user_choice(self):
    last_word_hidden = self.word_hidden
    self.word_hidden = ""

    for l in self.mot:
        if l in self.letters_list:
            self.word_hidden += l
        else:
            self.word_hidden += "\*"

    if self.word_hidden == last_word_hidden:
        self.user_chances += 1

    return self.word_hidden, self.user_chances
