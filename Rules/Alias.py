import json
import os

from ._shared import *


class Alias(Rule):
    """Handles aliases"""

    def __init__(self, bot, basepath):
        self.bot = bot
        self.basepath = basepath
        self.aliases = self.read_aliases()

    def __call__(self, serv, author, args):
        """Handles aliases"""
        args = [i.lower() for i in args]
        if len(args) > 4 and args[1] == "add":
            doublons = [i for i in self.aliases
                        if i["type"] == args[2] and i["name"] == args[3]]
            for d in doublons:
                self.aliases.remove(d)
            try:
                self.aliases.append({"type": args[2],
                                     "name": args[3],
                                     "value": json.loads(args[4])})
            except ValueError:
                self.bot.ans(serv, author, "Valeur JSON invalide.")
                return
            self.write_alias()
            self.bot.ans(serv, author,
                         "Nouvel alias ajouté : " +
                         "{" + args[2] + ", " + args[3] + ", " + args[4] + "}")
            return
        elif len(args) > 3 and args[1] == "del":
            self.aliases = [alias for alias in self.aliases if not (alias["type"] == args[2] and alias["name"] == args[3])]
            self.write_alias()
            self.bot.ans(serv, author,
                         "Alias supprimé.")
            return
        elif len(args) > 1:
            aliases = [i for i in self.aliases if i['type'] == args[1]]
        else:
            aliases = self.aliases
        if len(aliases) > 0:
            types = set([i['type'] for i in aliases])
            for i in types:
                self.bot.ans(serv, author,
                             "Liste des alias disponibles pour " + i + " :")
                to_say = ""
                for j in [k for k in self.aliases if k['type'] == i]:
                    to_say += "{" + j['name'] + ", " + json.dumps(j['value']) + "}, "
                to_say = to_say.strip(", ")
                self.bot.say(serv, to_say)
        else:
            self.bot.ans(serv, author, "Aucun alias défini.")

    def write_alias(self):
        with open(self.basepath + "data/aliases", "w+") as fh:
            json.dump(self.aliases, fh,
                      sort_keys=True,
                      indent=4, separators=(',', ': '))

    def read_aliases(self):
        aliases = []
        if os.path.isfile(self.basepath + "data/aliases"):
            with open(self.basepath + "data/aliases", 'r') as fh:
                try:
                    aliases = json.load(fh)
                except ValueError:
                    pass
        return sorted(aliases, key=lambda k: k['type'])

    def close(self):
        pass
