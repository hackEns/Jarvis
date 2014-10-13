import time

from ._shared import *


class Aide(Rule):
    """Prints help"""

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

    def __call__(self, serv, author, args):
        """Prints help"""
        args = [i.lower() for i in args]
        serv.privmsg(author,
                     self.config.get("desc") + " Commandes disponibles :")
        if len(args) > 1 and args[0] == "aide":
            if args[1] in self.bot.rules:
                serv.privmsg(author, self.bot.rules[args[1]]['help'])
            else:
                serv.privmsg(author, "Je n'ai pas compris…")
        elif args[0] != "aide" and args[0] in self.bot.rules:
            serv.privmsg(author, self.bot.rules[args[0]]['help'])
        else:
            for rule in sorted(self.bot.rules):
                serv.privmsg(author, self.bot.rules[rule]['help'])

    def close(self):
        pass
