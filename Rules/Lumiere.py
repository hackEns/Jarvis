import subprocess
from ._shared import *


class Lumiere(Rule):
    """Controls the LED"""

    def __init__(self, bot, config):
        self.config = config
        self.bot = bot

    def lumiere(r, v, b):
        msg = [0x80]
        for c in [r, v, b]:
            if c < 0 or c > 255:
                return False
            else:
                msg.append(int(c/2))

        ser = wiringpi2.serialOpen(self.config.pin_led, 115200)
        for j in msg:
            wiringpi2.serialPuts(ser, struct.pack("I", j))
        wiringpi2.serialClose(ser)

    def __call__(self, serv, author, args):
        if self.bot.leds is not None:
            try:
                if isinstance(self.bot.leds, subprocess.Popen):
                    self.bot.leds.terminate()
            except ProcessLookupError:
                pass
            self.bot.leds = None
            self.bot.current_leds = "off"
        if len(args) == 4:
            try:
                R = int(args[1])
                G = int(args[2])
                B = int(args[3])

                assert(R >= 0 and R <= 255)
                assert(G >= 0 and G <= 255)
                assert(B >= 0 and B <= 255)

                if self.lumiere(R, G, B):
                    self.bot.current_leds = ("(" + str(R) + ", " +
                                             str(G) + ", " +
                                             str(B) + ")")
                    self.ans(serv,
                             author,
                             "LED réglée sur " + self.bot.current_leds)
                else:
                    self.ans(serv,
                             author,
                             "Impossible de régler les LEDs à cette valeur.")
            except (AssertionError, ValueError):
                raise InvalidArgs
        elif len(args) == 2:
            script = os.path.join(self.basepath + "data/leds", args[1]) + ".py"
            if os.path.isfile(script):
                self.bot.leds = subprocess.Popen(['python', script],
                                                 stdout=subprocess.DEVNULL)
                self.bot.current_leds = args[1]
        else:
            raise InvalidArgs
