class Skill:
    styles = {"att": "Attaque", "def": "Défense", "esq": "Esquive", "soin": "Guérison"}

    def __init__(self, name, description, damage, cost, style="att", self_damage=0):
        self.style = self.styles["att"]
        self._skill_name = name
        self._skill_description = description
        self._skill_damage = damage
        self._skill_cost = cost
        self._skill_self_damage = self_damage
        self.set_style(style)

    def __str__(self):
        if self._skill_self_damage == 0:
            return f"{self._skill_name} : {self._skill_description}. Inflige {self._skill_damage} PV à l'adversaire et coûte {self._skill_cost} de Ki."
        else:
            return f"{self._skill_name} : {self._skill_description}. Inflige {self._skill_damage} PV à l'adversaire, fait subir {self._skill_self_damage} PV à soi-même et coûte {self._skill_cost} de Ki."

    def _get_skill_name(self):
        return self._skill_name

    def _get_skill_description(self):
        return self._skill_description

    def _get_skill_damage(self):
        return self._skill_damage

    def _get_skill_cost(self):
        return self._skill_cost

    def _get_skill_self_damage(self):
        return self._skill_self_damage

    def set_style(self, new_style: str):
        if new_style in self.styles.keys():
            self.style = self.styles[new_style]
        else:
            raise SyntaxError(
                f"'{new_style}' est invalide. Veuillez entrer une chaine de caractères identique à un des éléments de cette liste: {self.styles.keys()}")

    skill_name = property(_get_skill_name)
    skill_description = property(_get_skill_description)
    skill_cost = property(_get_skill_cost)
    skill_damage = property(_get_skill_damage)
