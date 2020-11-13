from assets.Games.dragonball.Character import Character


class Namek(Character):

    def __init__(self, name: str, skills: list = None):
        Character.__init__(self, name, self.__module__, skills)

    def get_Character(self):
        return self.__dict__
