import subprocess
import sys

from ._shared import *


class Update(Rule):
    """Handles bot updating"""

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

    def __call__(self, serv, author, args):
        """Handles bot updating"""
        if self.bot.has_admin_rights(serv, author):
            self.bot.ans(serv, author, "Starting update…")
            subprocess.call([self.bot.basepath + "updater.sh",
			    self.bot.basepath])
            self.bot.ans(serv, author, "I will now update myself.")
            self.bot.close()
            sys.exit()

    def close(self):
        pass
