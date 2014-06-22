from ._shared import *

class Camera(Rule):
    """Handles camera"""

    def __init__(self, bot, config, cmd):
        self.config = config
        self.bot = bot
        self.cmd = cmd
        self.camera_pos = "0°"

    def __call__(self, serv, author, args):
        """Controls camera"""
        args = [i.lower() for i in args]
        if len(args) < 2:
            raise InvalidArgs
        try:
            angle = int(args[1])
            if angle < 0 or angle > 180:
                raise ValueError
            if self.cmd.camera(angle):
                self.camera_pos = str(angle)+"°"
                self.bot.ans(serv, author, "Caméra réglée à "+angle+"°.")
            else:
                self.bot.ans(serv, author, "Je n'arrive pas à régler la caméra.")
        except ValueError:
            alias = args[1]
            angle = -1
            matchs = [i for i in self.bot.alias.aliases
                      if i["type"] == "camera" and i["name"] == alias]
            if len(matchs) == 0:
                raise InvalidArgs
            else:
                angle = int(matchs[0]["value"])
                if self.cmd.camera(angle):
                    self.camera_pos = args[1]
                    self.bot.ans(serv, author, "Caméra réglée à "+angle+"°.")
                else:
                    self.bot.ans(serv, author,
                             "Je n'arrive pas à régler la caméra.")

    def close(self):
        pass


