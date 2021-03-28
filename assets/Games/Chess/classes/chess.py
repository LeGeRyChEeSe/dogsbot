from collections import OrderedDict

from discord.ext import commands

from assets.Games.Chess.classes.player import Player


class Chess:

    def __init__(self, white_player, black_player, super, ctx: commands.Context):
        self.super = super
        self.ctx = ctx
        self.black = ":black_large_square:"
        self.white = ":white_large_square:"
        self.white_player = Player(white_player, "white", self.super, self.ctx)
        self.black_player = Player(black_player, "black", self.super, self.ctx)
        self.chess_board = []
        self.over = False
        self.set_default_chess_board()
        self.game()

    def set_default_chess_board(self):
        for i in range(8):
            self.chess_board.append([])
            for j in range(8):
                if i % 2 == 0:
                    if j % 2 == 0:
                        self.chess_board[i].append(self.black)
                    else:
                        self.chess_board[i].append(self.white)

                else:
                    if j % 2 == 0:
                        self.chess_board[i].append(self.white)
                    else:
                        self.chess_board[i].append(self.black)

    def set_chess_board(self):
        # White set

        self.chess_board[7][0] = self.white_player.rook
        self.chess_board[7][1] = self.white_player.knight
        self.chess_board[7][2] = self.white_player.bishop
        self.chess_board[7][3] = self.white_player.queen
        self.chess_board[7][4] = self.white_player.king
        self.chess_board[7][5] = self.white_player.bishop
        self.chess_board[7][6] = self.white_player.knight
        self.chess_board[7][7] = self.white_player.rook
        for i in range(8):
            self.chess_board[6][i] = self.white_player.pawn

        # Black set

        self.chess_board[0][0] = self.black_player.rook
        self.chess_board[0][1] = self.black_player.knight
        self.chess_board[0][2] = self.black_player.bishop
        self.chess_board[0][3] = self.black_player.queen
        self.chess_board[0][4] = self.black_player.king
        self.chess_board[0][5] = self.black_player.bishop
        self.chess_board[0][6] = self.black_player.knight
        self.chess_board[0][7] = self.black_player.rook
        for i in range(8):
            self.chess_board[1][i] = self.black_player.pawn

    def get_chess_board(self):
        chess_board = ""

        for i in self.chess_board:
            for j in i:
                chess_board += j
            chess_board += "\n"

        return chess_board

    async def game(self):
        self.black_player.set_color_pieces()
        self.set_chess_board()

        while not self.over:
            print("white turns")
            await self.white_player.play()
