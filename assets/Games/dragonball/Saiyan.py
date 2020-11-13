from assets.Games.dragonball.Character import Character


class Saiyan(Character):

    def __init__(self, name: str, skills: list = None):
        self.nature = self.__module__
        Character.__init__(self, name, self.nature, skills)
        self.transformations = {"ssj1": "Super Saiyan", "ssj2": "Super Saiyan 2", "ssj3": "Super Saiyan 3",
                                "ssj4": "Super Saiyan 4", "ssjg": "Super Saiyan God", "ssjb": "Super Saiyan Blue",
                                "migatte": "Migatte No Gokui", "oozaru": "Oozaru"}
        self.is_transformed = False
        self._form = str(self.nature)

    def get_Character(self):
        return self.__dict__

    def _set_transformation(self, transformation: str):
        for key, value in self.transformations.items():
            if key == transformation:
                self.is_transformed = True
                self._form = value
                print(f"{self._name} se transforme en {self._form}!")
                break

    def _get_transformation(self):
        if self.is_transformed:
            return f"{self._name} est un {self.nature}, transformé en {self._form}."
        else:
            return f"{self._name} est un {self.nature}, non transformé."

    form = property(_get_transformation, _set_transformation)
