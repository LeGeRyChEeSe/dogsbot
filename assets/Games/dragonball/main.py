from assets.Games.dragonball.Game import Game
from assets.Games.dragonball.Saiyan import Saiyan
from assets.Games.dragonball.Namek import Namek
from assets.Games.dragonball.Skill import Skill

kamehameha = Skill("Kamehameha", "Lance un puissant kikoha chargé", 100, 50)
canon_garric = Skill(
    "Canon Garric", "Lance un puissant kikoha chargé", 100, 50)
makanko_sappo = Skill(
    "Makanko Sappo", "Lance un puissant kikoha chargé", 100, 50)
shunkan_ido = Skill(
    "Shunkan ido", "Le déplacement instantané permet d'esquiver l'attaque d'un ennemi", 0, 15, "esq")
genki_dama = Skill(
    "Genki-dama", "Boule d'énergie massive infligeant des dégâts colossaux", 300, 75)
kikoha = Skill("Kikoha", "Lance une salve de kikohas faibles", 50, 25)

goku = Saiyan("Son Goku", [kamehameha, shunkan_ido, kikoha])
vegeta = Saiyan("Vegeta", [canon_garric, kikoha])
game = Game(goku, vegeta)
game.play()
