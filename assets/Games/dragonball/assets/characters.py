from assets.Games.dragonball.classes.Saiyan import Saiyan
from assets.Games.dragonball.assets.skills import *
from events.functions import *

characters_file = "assets/Games/dragonball/assets/characters.json"

characters = read_file(
    characters_file, is_json=True)


def get_characters():
    return characters


goku = Saiyan("ctx", "Son Goku", [kamehameha.get_skill(
), shunkan_ido.get_skill(), kikoha.get_skill()])
vegeta = Saiyan("ctx", "Vegeta", [
                canon_garric.get_skill(), kikoha.get_skill()])
sangohan = Saiyan("ctx", "Son Gohan", [
                  kamehameha.get_skill(), kikoha.get_skill()])
broly = Saiyan("ctx", "Broly", [kikoha.get_skill()])
sangoten = Saiyan("ctx", "Son Goten", [
                  kamehameha.get_skill(), kikoha.get_skill()])
all_characters = [goku, vegeta, sangohan, broly, sangoten]

for player in all_characters:
    character = characters[player.race][player.name]
    character["name"] = player.name
    character["hp"] = player.hp
    character["ki"] = player.ki
    character["ki_velocity"] = player.ki_velocity
    character["damage"] = player.damage
    character["skills"] = {}
    for skill in player.skills:
        character["skills"][skill.skill_name] = {
            "description": skill.skill_description,
            "cost": skill.skill_cost,
            "damage": skill.skill_damage,
            "style": skill.style,
            "self_damage": skill.skill_self_damage
        }

write_file(characters_file, characters, is_json=True, mode="w")
