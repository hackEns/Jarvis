from ._shared import *

class Dis(Rule):
    """Say something"""

    def __init__(self, bot, config, cmd):
        self.config = config
        self.bot = bot
        self.cmd = cmd

    def __call__(self, serv, author, args):
        """Say something"""
        if len(args) > 1:
            for something in args[1:]:
                returncode = self.cmd.dis(something)
                if returncode is not False and returncode == 0:
                    self.bot.ans(serv, author, something)
                else:
                    self.bot.ans(serv, author, "Je n'arrive plus à parler…")
        else:
            raise InvalidArgs

    def close(self):
        pass


