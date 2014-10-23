from ._shared import *


class Aide(Rule):
    """Prints help"""

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

    def __call__(self, serv, author, args):
        """Prints help"""
        args = [i.lower() for i in args]
        # args[0] est toujours 'aide' (à priori)
        # args[1] est la commande pour laquelle on veut l'aide, ou vide
        serv.privmsg(author,
                     self.config.get("desc") + " Commandes disponibles :")
        if len(args) > 1:
            if args[1] in self.bot.rules:
                serv.privmsg(author, self.bot.rules[args[1]]['help'])
            else:
                serv.privmsg(author, "Je n'ai pas compris…")
        else:
            for rule in sorted(self.bot.rules):
                serv.privmsg(author, self.bot.rules[rule]['help'])

    def close(self):
        pass
