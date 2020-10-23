class Skills:

    def __init__(self, name: str, description: str, damage: int, cost: int):
        self.name = name
        self.description = description
        self.damage = damage
        self.cost = cost


class Character:

    def __init__(self, name: str, race: str, skills: Skills):
        self.name = name
        self.race = race
        self.skills = skills
