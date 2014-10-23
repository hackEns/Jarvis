from ._shared import *
import subprocess
import wiringpi2


class Info(Rule):
    """Display infos"""

    def __init__(self, bot):
        self.bot = bot

    def atx_status(self):
        return wiringpi2.digitalRead(self.bot.config.get("pin_atx_status"))

    def __call__(self, serv, author, args):
        """Display infos"""
        args = [i.lower() for i in args]
        all_items = ['atx', 'leds', 'stream', 'camera']
        greenc = "\x02\x0303"
        redc = "\x02\x0304"
        endc = "\x03\x02"
        if len(args) > 1:
            infos_items = [i for i in args[1:] if i in all_items]
        else:
            infos_items = all_items
        if len(infos_items) == 0:
            raise InvalidArgs
        to_say = "Statut : "

        if 'atx' in infos_items:
            if self.atx_status == 0:
                to_say += "ATX : " + redc + "off" + endc + ", "
            else:
                to_say += "ATX : " + greenc + "on" + endc + ", "

        if 'leds' in infos_items:
            if isinstance(self.bot.leds, subprocess.Popen):
                poll = self.bot.leds.poll()
                if poll is not None and poll != 0:
                    self.bot.leds = None
                    self.bot.current_leds = "off"
            if self.bot.current_leds is not None:
                if self.bot.current_leds == "off":
                    to_say += "LEDs : " + redc + "off" + endc + ", "
                else:
                    to_say += ("LEDs : " +
                               greenc + self.bot.current_leds + endc + ", ")
            else:
                to_say += "LEDs : " + redc + "off" + endc + ", "

        if 'stream' in infos_items:
            if(self.bot.oggfwd is not None and
               self.bot.streamh is not None and
               self.bot.oggfwd.poll() is None and
               self.bot.streamh.poll() is None):
                to_say += "Stream : " + greenc + "Actif" + endc + ", "
            else:
                to_say += "Stream : " + redc + "HS" + endc + ", "

        if 'camera' in infos_items:
            to_say += "Caméra : " + self.bot.camera.pos + ", "
        to_say = to_say.strip(", ")
        self.bot.ans(serv, author, to_say)

    def close(self):
        pass
