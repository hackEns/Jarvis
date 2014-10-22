from ._shared import *
import wiringpi2

class Atx(Rule):
    """Handles RepRap ATX"""

    def __init__(self, bot, config):
        self.config = config
        self.bot = bot
        self.status = "off"

    def atx(self, state):
        wiringpi2.digitalWrite(self.config.get("pin_atx"), state)

    def atx_status(self):
        return wiringpi2.digitalRead(self.config.get("pin_atx_status"))

    def __call__(self, serv, author, args):
        """Handles RepRap ATX"""
        args = [i.lower() for i in args]
        if len(args) > 1 and args[1] in ["on", "off"]:
            if args[1] == "on" and self.atx(1) and self.atx_status() == 1:
                self.status = args[1]
                self.bot.ans(author, "ATX allumée.")
            elif args[1] == "off" and self.atx(0) and self.atx_status() == 0:
                self.status = args[1]
                self.bot.ans(serv, author, "ATX éteinte.")
            else:
                self.bot.ans(serv, author, "L'ATX est devenue incontrôlable !")
        else:
            raise InvalidArgs

    def close(self):
        pass
