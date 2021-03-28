from typing import List

from assets.Games.dragonball.classes.Skill import Skill
from discord.ext.commands import Context


class Character:
    nb_characters = 0
    characters = {}

    def __init__(self, ctx: Context, name, race, skills: List[Skill] = None):
        self.ctx = ctx
        self.nature = self.__module__
        self._name = name
        self.race = race
        self._skills = skills
        self.damage = 50
        self.hp = 1000
        self.ki = 100
        self.ki_velocity = 10
        Character.characters[self.nature] = self._name
        Character.nb_characters += 1

    def __str__(self):
        return str(self.__dict__)

    def get_character(self):
        return self.__dict__

    def _get_name(self):
        return self._name

    def _get_skills(self):
        return self._skills

    def get_skill(self, skill_name):
        for skill in self._skills:
            return skill

    def _add_skills(self, new_skill):
        if new_skill not in self._skills:
            self._skills += new_skill

    def use_skill(self, ennemy):
        if not ennemy:
            return "Cet ennemi n'existe pas."

        skill_name = self.ctx

        skill_name = input(
            f"""Veuillez choisir un skill parmis ceux disponibles:
------------------------------------------------------------------------------------------------
{self.skills}
------------------------------------------------------------------------------------------------
Votre choix: """)
        for skill in self._skills:
            if skill_name.lower() in skill.skill_name.lower():
                ennemy.hit(skill.skill_damage)
                print(
                    f"{ennemy.name} a été attaqué par {self._name} avec l'attaque {skill.skill_name}, {ennemy.name} perd {skill.skill_damage} PV!")
                self.remove_ki(skill.skill_cost)
                print(f"Votre ki est maintenant à {self.ki}")

    def hit(self, damages):
        self.hp -= damages

    def remove_ki(self, amount):
        self.ki -= amount

    def __delitem__(self, skill_name):
        for skill in self._skills:
            if skill_name.lower() == skill.skill_name.lower():
                return self._skills.remove(skill)

    def __getitem__(self, skill_name):
        skills = []
        for skill in self._skills:
            if skill_name.lower() in skill.skill_name.lower() and len(skill_name) >= 3:
                skills.append(str(skill))
        if not skills:
            return "Veuillez entrer un nom de technique valide."
        else:
            return "\n".join(skills)

    def load_ki_velocity(self):
        pass

    skills = property(_get_skills, _add_skills)
    name = property(_get_name)
