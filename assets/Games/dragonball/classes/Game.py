import os


class Game:

    def __init__(self, *players):
        self.is_running = False
        self.players = list(players)

    def play(self):
        print(self.players)
        self.is_running = True
        self.running()

    def is_over(self):
        for player in self.players:
            if player.hp <= 0:
                self.is_running = False
                print("Le jeu est finis!")
                quit()

    def load_ki(self, player):
        player.ki += player.ki_velocity

    def running(self):
        if len(self.players) < 2:
            return "Minimum 2 joueurs."

        _round = 0

        while self.is_running:
            os.system("cls")
            self.is_over()
            ennemies = []
            current_player = self.players[_round]
            for player in self.players:
                if player.name != current_player.name:
                    ennemies.append(player.name)
            os.system("cls")
            target = input(
                "{1}, choisissez une cible:\n{0}\nVotre choix: ".format("\n".join(ennemies), current_player.name))
            for player in self.players:
                print(target)
                if target.lower() in player.name.lower() and len(target) > 3:
                    target = player

            os.system("cls")
            self.players[_round].use_skill(target)
            os.system("pause")
            if _round < len(self.players) - 1:
                _round += 1
            else:
                _round = 0
