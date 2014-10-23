from ._shared import *
import subprocess


class Dis(Rule):
    """Say something"""

    def __init__(self, bot):
        self.bot = bot

    def dis(self, something):
        try:
            return subprocess.call(["espeak",
                                    "-vfrench+m5",
                                    "-p 5",
                                    "-s 50",
                                    "-a 200",
                                    something])
        except FileNotFoundError:
            return False

    def __call__(self, serv, author, args):
        """Say something"""
        if len(args) > 1:
            for something in args[1:]:
                returncode = self.dis(something)
                if returncode is not False and returncode == 0:
                    self.bot.ans(serv, author, something)
                else:
                    self.bot.ans(serv, author, "Je n'arrive plus à parler…")
        else:
            raise InvalidArgs

    def close(self):
        pass
