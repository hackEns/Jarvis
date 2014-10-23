import os

from ._shared import *


class Alias(Rule):
    """Handles aliases"""

    def __init__(self, bot, basepath):
        self.bot = bot
        self.basepath = basepath
        self.aliases = self.read_alias()

    def __call__(self, serv, author, args):
        """Handles aliases"""
        args = [i.lower() for i in args]
        if len(args) > 4 and args[1] == "add":
            doublons = [i for i in self.aliases
                        if i["type"] == args[2] and i["name"] == args[3]]
            for d in doublons:
                self.aliases.remove(d)
            self.aliases.append({"type": args[2],
                                 "name": args[3],
                                 "value": args[4]})
            self.write_alias()
            self.bot.ans(serv, author,
                         "Nouvel alias ajouté : " +
                         "{" + args[2] + ", " + args[3] + ", " + args[4] + "}")
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
                    to_say += "{" + j['name'] + ", " + j['value'] + "}, "
                to_say = to_say.strip(", ")
                self.bot.say(serv, to_say)
        else:
            self.bot.ans(serv, author, "Aucun alias défini.")

    def write_alias(self):
        write = {}
        for item in self.aliases:
            try:
                write[item['type']] += '{name}:{value}\n'.format(
                    name=item['name'],
                    value=item['value'],
                )
            except KeyError:
                write[item["type"]] = item["name"] + ":" + item["value"] + "\n"
        for type, aliases in write.items():
            with open(self.basepath + "data/" + type + ".alias", "w+") as fh:
                fh.write(aliases)

    def read_alias(self):
        alias = []
        if os.path.isfile(self.basepath + "data/camera.alias"):
            with open(self.basepath + "data/camera.alias", 'r') as fh:
                for line in fh.readlines():
                    line = [i.strip() for i in line.split(':')]
                    alias.append({"type": "camera",
                                  "name": line[0],
                                  "value": line[1]})
        return sorted(alias, key=lambda k: k['type'])

    def close(self):
        pass
