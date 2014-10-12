import os
from ._shared import *


class Historique(Rule):
    """Handles history"""

    def __init__(self, bot, config, basepath):
        self.config = config
        self.bot = bot
        self.basepath = basepath
        self.history = self.read()

    def __call__(self, serv, author, args):
        """Handles history"""
        try:
            if(len(args) == 3 and
               int(args[1]) < len(self.history) and
               int(args[2]) < len(self.history)):
                start = int(args[1])
                end = int(args[2])
            elif len(args) == 2:
                start = -int(args[1])
                end = None
            else:
                start = -self.config.get("history_lines_to_show")
                end = None
        except ValueError:
            raise InvalidArgs
        self.bot.ans(serv, author, "Historique :")
        if len(self.history[start:end]) == 0:
            self.bot.say(serv, "Pas d'historique disponible.")
        else:
            for hist in self.history[start:end]:
                self.bot.say(serv, hist['cmd']+" par "+hist['author'])

    def add(self, author, cmd):
        """Adds something to history"""
        insert = {"author": author, "cmd": cmd}
        if(self.config.get("history_no_doublons") and
           (len(self.history) == 0 or self.history[-1] != insert)):
            self.history.append(insert)
            while len(self.history) > self.config.get("history_length"):
                self.history.popleft()
                self.write_history()

    def write(self):
        write = ''
        for hist in self.history:
            write += hist["author"]+"\t"+hist["cmd"]+"\n"
        with open(self.basepath+"data/history", 'w+') as fh:
            fh.write(write)

    def read(self):
        history = []
        if os.path.isfile(self.basepath+"data/history"):
            with open(self.basepath+"data/history", 'r') as fh:
                for line in fh.readlines():
                    line = [i.strip() for i in line.split('\t')]
                    history.append({'author': line[0], 'cmd': line[1]})
        return history

    def close(self):
        pass
