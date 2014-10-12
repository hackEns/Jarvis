import subprocess
from ._shared import *


class Lumiere(Rule):
    """Controls the LED"""

    def __init__(self, bot, config):
        self.config = config
        self.bot = bot
        self.leds = None
        self.current_leds = "off"

    def lumiere(r, v, b):
        msg = [0x80]
        for c in [r, v, b]:
            if c < 0 or c > 255:
                return False
            else:
                msg.append(int(c/2))

        ser = wiringpi2.serialOpen(self.config.get("pin_led"), 115200)
        for j in msg:
            wiringpi2.serialPuts(ser, struct.pack("I", j))
        wiringpi2.serialClose(ser)

    def __call__(self, serv, author, args):
        if self.leds is not None:
            try:
                if isinstance(self.leds, subprocess.Popen):
                    self.leds.terminate()
            except ProcessLookupError:
                pass
            self.leds = None
            self.current_leds = "off"
        if len(args) == 4:
            try:
                R = int(args[1])
                G = int(args[2])
                B = int(args[3])

                assert(R >= 0 and R <= 255)
                assert(G >= 0 and G <= 255)
                assert(B >= 0 and B <= 255)

                if self.lumiere(R, G, B):
                    self.current_leds = ("(" + str(R) + ", " +
                                         str(G) + ", " +
                                         str(B) + ")")
                    self.ans(serv,
                             author,
                             "LED réglée sur " + self.current_leds)
                else:
                    self.ans(serv,
                             author,
                             "Impossible de régler les LEDs à cette valeur.")
            except (AssertionError, ValueError):
                raise InvalidArgs
        elif len(args) == 2:
            script = os.path.join(self.basepath + "data/leds", args[1]) + ".py"
            if os.path.isfile(script):
                self.leds = subprocess.Popen(['python', script],
                                             stdout=subprocess.DEVNULL)
                self.current_leds = args[1]
        else:
            raise InvalidArgs

    def close(self):
        if self.leds is not None:
            try:
                self.leds.terminate()
            except ProcessLookupError:
                pass
            self.leds = None
            self.current_leds = "off"
