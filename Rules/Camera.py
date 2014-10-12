from ._shared import *


class Camera(Rule):
    """Handles camera"""

    def __init__(self, bot, config):
        self.config = config
        self.bot = bot
        self.pos = "0°"

    def camera(angle):
        if angle < 0 or angle > 180:
            return False
        towrite = int(127+int(127*float(angle)/180))
        wiringpi2.pwmWrite(self.config.pin_cam, towrite)
        time.sleep(0.100)

    def __call__(self, serv, author, args):
        """Controls camera"""
        args = [i.lower() for i in args]
        if len(args) < 2:
            raise InvalidArgs
        try:
            angle = int(args[1])
            if angle < 0 or angle > 180:
                raise ValueError
            if self.camera(angle):
                self.pos = str(angle)+"°"
                self.bot.ans(serv,
                             author,
                             "Caméra réglée à "+angle+"°.")
            else:
                self.bot.ans(serv,
                             author,
                             "Je n'arrive pas à régler la caméra.")
        except ValueError:
            # Argument is not a valid angle, it may be an alias
            alias = args[1]
            angle = -1
            matchs = [i for i in self.bot.alias.aliases
                      if i["type"] == "camera" and i["name"] == alias]
            if len(matchs) == 0:
                raise InvalidArgs
            else:
                angle = int(matchs[0]["value"])
                if self.camera(angle):
                    self.pos = args[1]
                    self.bot.ans(serv, author, "Caméra réglée à "+angle+"°.")
                else:
                    self.bot.ans(serv,
                                 author,
                                 "Impossible de régler la caméra " +
                                 "à cette valeur.")
    def close(self):
        pass

