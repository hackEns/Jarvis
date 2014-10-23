from ._shared import *


class Version(Rule):
    """Prints current version"""

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

    def get_version(self):
        """Returns the bot version"""
        return (self.config.get("nick") + "Bot version " +
                self.config.get("version") + " by " +
                self.config.get("author"))

    def __call__(self, serv, author, args):
        """Prints current version"""
        self.bot.ans(serv, author, self.get_version())

    def close(self):
        pass
