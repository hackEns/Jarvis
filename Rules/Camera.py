from ._shared import *
import wiringpi2
import time


class Camera(Rule):
    """Handles camera"""

    def __init__(self, bot, config):
        self.config = config
        self.bot = bot
        self.pos = (0, 0)

    def print_pos(self):
        return "(%d°, %d°)" % self.pos

    def camera(self, angle1, angle2):
        if angle1 < 0 or angle1 > 180 or angle2 < 0 or angle2 > 180:
            return False
        # TODO
        angle1 = int(127 + int(127 * float(angle1) / 180))
        angle2 = int(127 + int(127 * float(angle2) / 180))
        wiringpi2.pinMode(self.config.get("pin1_cam"), 1)
        wiringpi2.softPwmCreate(self.config.get("pin1_cam"), 0, 100)
        wiringpi2.softPwmWrite(self.config.get("pin1_cam"), angle1)
        wiringpi2.pinMode(self.config.get("pin2_cam"), 1)
        wiringpi2.softPwmCreate(self.config.get("pin2_cam"), 0, 100)
        wiringpi2.softPwmWrite(self.config.get("pin2_cam"), angle2)
        time.sleep(0.100)

    def __call__(self, serv, author, args):
        """Controls camera"""
        args = [i.lower() for i in args]
        if len(args) < 3:
            raise InvalidArgs
        try:
            angle1 = int(args[1])
            angle2 = int(args[2])
            if angle1 < 0 or angle1 > 180 or angle2 < 0 or angle2 > 180:
                raise ValueError
            if self.camera(angle1, angle2):
                self.pos = (angle1, angle2)
                self.bot.ans(serv,
                             author,
                             "Caméra réglée à " + print_pos() + ".")
            else:
                self.bot.ans(serv,
                             author,
                             "Je n'arrive pas à régler la caméra.")
        except ValueError:
            # Argument is not a valid angle, it may be an alias
            alias = args[1]
            angle1 = -1
            angle2 = -1
            matchs = [i for i in self.bot.alias.aliases
                      if i["type"] == "camera" and i["name"] == alias]
            if len(matchs) == 0:
                raise InvalidArgs
            else:
                angle1 = int(matchs[0]["value"][0])
                angle2 = int(matchs[0]["value"][1])
                if self.camera(angle1, angle2):
                    self.pos = (angle1, angle2)
                    self.bot.ans(serv, author,
                                 "Caméra réglée à " + print_pos() + ".")
                else:
                    self.bot.ans(serv,
                                 author,
                                 "Impossible de régler la caméra " +
                                 "à cette valeur.")

    def close(self):
        pass
