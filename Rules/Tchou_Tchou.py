import random

from ._shared import *


class Tchou_Tchou(Rule):
    """Tchou Tchou action, poke Armavica"""

    def __init__(self, bot):
        self.bot = bot

    def __call__(self, serv):
        """Says tchou tchou"""
        self.bot.say(serv, "Tchou tchou !")
        self.bot.connection.execute_delayed(random.randrange(3600, 84600),
                                            self.bot.tchou_tchou, (serv,))

    def close(self):
        pass
