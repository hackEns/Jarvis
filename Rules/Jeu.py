from ._shared import *


class Jeu(Rule):
    """Jeu action, I lost the game."""

    def __init__(self, bot):
        self.bot = bot

    def __call__(self, serv, author=None, args=None):
        """Handles game"""
        if author is not None:
            self.bot.ans(serv, author, "J'ai perdu le jeu…")
        else:
            self.bot.say(serv, "J'ai perdu le jeu…")

    def close(self):
        pass
