from ._shared import *

class Atx(Rule):
    """Handles RepRap ATX"""

    def __init__(self, bot, config, cmd):
        self.config = config
        self.bot = bot
        self.cmd = cmd
        self.status = "off"

    def __call__(self, serv, author, args):
        """Handles RepRap ATX"""
        args = [i.lower() for i in args]
        if len(args) > 1 and args[1] in ["on", "off"]:
            if args[1] == "on" and self.cmd.atx(1):
                self.status = args[1]
                self.bot.ans(author, "ATX allumée.")
            elif args[1] == "off" and self.cmd.atx(0):
                self.status = args[1]
                self.bot.ans(serv, author, "ATX éteinte.")
            else:
                self.bot.ans(serv, author, "L'ATX est devenue incontrôlable !")
        else:
            raise InvalidArgs

    def close(self):
        pass


