from ._shared import *


class Ping(Rule):
    """Prints pong"""

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

    def __call__(self, serv, author, args):
        if len(args) > 0:
            if args[0] == "ping":
                self.bot.say(serv, "{}: pong".format(author))

    def close(self):
        pass
