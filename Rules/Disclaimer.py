from ._shared import *

class Disclaimer(Rule):
    """Display disclaimer"""

    def __init__(self, bot, config):
        self.config = config
        self.bot = bot

    def __call__(self, serv, author, args):
        """Display disclaimer"""
        self.bot.ans(serv, author, "Jarvis est un bot doté de capacités " +
                 "dépassant à la fois l'entendement et les limites d'irc. " +
                 "Prenez donc garde a toujours rester poli avec lui car " +
                 "bien qu'aucune intention malsaine ne lui a été " +
                 "volontairement inculquée,")
        self.bot.say(serv, "JARVIS IS PROVIDED \"AS IS\", WITHOUT " +
                 "WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT " +
                 "NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS " +
                 "FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.")

    def close(self):
        pass


