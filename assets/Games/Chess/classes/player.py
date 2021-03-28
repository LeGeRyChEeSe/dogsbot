import discord
from discord.ext import commands


class Player:

    def __init__(self, player: discord.Member, color, super, ctx: commands.Context):
        self.super = super
        self.ctx = ctx
        self.pieces = 16
        self.player = player
        self.color = color
        self.knights_counter = 2
        self.knight = " ♘ "
        self.bishops_counter = 2
        self.bishop = " ♗ "
        self.rooks_counter = 2
        self.rook = " ♖ "
        self.queens_counter = 1
        self.queen = " ♕ "
        self.pawns_counter = 8
        self.pawn = " ♙ "
        self.king = " ♔ "
        self.king_is_checked = False

    def set_color_pieces(self):
        if self.color == "black":
            self.knight = " ♞ "
            self.bishop = " ♝ "
            self.rook = " ♜ "
            self.queen = " ♛ "
            self.pawn = "♟"
            self.king = " ♚ "

    async def select(self):
        await self.ctx.send(f"{self.player.mention} c'est à ton tour de jouer! Choisis le pion que tu veux déplacer ainsi que la position à laquelle tu veux le déplacer, de la façon suivante, par exemple la tour en A1 jusqu'à A4, tape: `a1a4`")
        selection = await self.super.client.wait_for("message", timeout=120)
        print(selection)

    async def play(self):
        await self.select()
