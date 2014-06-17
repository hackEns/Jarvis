#!/usr/bin/env python3

import config
import irclib
import irc.bot as ircbot
import jarvis_cmd
import os


class InvalidArgs(Exception):
    pass


class JarvisBot(ircbot.SingleServerIRCBot):
    def __init__(self):
        ircbot.SingleServerIRCBot.__init__(self, [(config.server,
                                                   config.port)],
                                           config.nick,
                                           config.desc)
        self.version = "0.2"
        self.basepath = os.path.dirname(os.path.realpath(__file__))
        self.history = self.read_history()
        self.rules = {}
        self.add_rule("aide", self.aide)
        self.add_rule("alias", self.alias)
        self.add_rule("atx", self.atx)
        self.add_rule("camera", self.camera)
        self.add_rule("dis", self.dis)
        self.add_rule("disclaimer", self.disclaimer)
        self.add_rule("historique", self.historique)
        self.add_rule("info", self.info)
        self.add_rule("jeu", self.jeu)
        self.add_rule("log", self.log)
        self.add_rule("lumiere", self.lumiere)
        self.add_rule("stream", self.stream)
        self.add_rule("update", self.update)
        self.nickserved = False

    def add_rule(self, name, action, help_msg=""):
        name = name.lower()
        if name not in self.rules:
            self.rules[name] = {}
        self.rules[name]['action'] = action
        self.rules[name]['help'] = help_msg

    def on_welcome(self, serv, ev):
        """Upon server connection"""
        self.privmsg(self, "nickserv", "identify "+config.password)
        serv.join(config.channel)

    def on_privmsg(self, serv, ev):
        """Handles queries"""
        if(irclib.nm_to_n(ev.source()).lower() == 'nickserv' and
           "You are now identified" in ev.arguments()[0]):
            self.nickserved = True

    def on_pubmsg(self, serv, ev):
        """Handles the queries on the chan"""
        author = irclib.nm_to_n(ev.source())
        msg = ev.arguments()[0].strip().lower()
        if msg.startswith('jarvis') and msg[6] in [':', ' ']:
            msg = [i for i in msg[7:].strip(': ').split(' ') if i]
            if msg[0] in self.rules:
                try:
                    self.rules[msg[0]]['action'](serv, author, msg)
                except InvalidArgs:
                    self.aide(serv, author, msg[0])
            else:
                self.ans(serv, author, "Je n'ai pas compris…")

    def ans(self, serv, user, message):
        """Answers to specified user"""
        serv.privmsg(config.channel, user+": "+message)

    def say(self, serv, message):
        """Say something on the channel"""
        serv.privmsg(config.channel, message)

    def add_history(self, author, cmd):
        """Adds something to history"""
        self.history.append({"author": author, "cmd": cmd})
        while len(self.history) > config.history_length:
            self.history.popleft()
        self.write_history()

    def write_history(self):
        write = ''
        for hist in self.history:
            write += hist["author"]+"\t"+hist["cmd"]+"\n"
        with open(self.basepath+"data/history", 'w+') as fh:
            fh.write(write)

    def read_history(self):
        history = []
        if os.path.isfile(self.basepath+"data/history"):
            with open(self.basepath+"data/history", 'r') as fh:
                for line in fh.readlines():
                    line = [i.strip() for i in line.split('\t')]
                    insert = {'author': line[0], 'cmd': line[1]}
                    if config.history_no_doublons and history[-1] != insert:
                        history.append(history)
        return history

    def get_version(self):
        """Returns the bot version"""
        return "Jarvis Bot version "+self.version+" by hackEns"

    def aide(self, serv, author, cmd=""):
        """Prints help"""
        self.ans(serv, "Jarvis au rapport ! Commandes disponibles :")
        for rule in self.rules:
            self.say(serv, self.rules[rule]['help'])

    def info(self, serv, author, args):
        """Prints infos"""
        # TODO

    def camera(self, serv, author, args):
        """Controls camera"""
        try:
            angle = int(args[1])
            if angle < 0 or angle > 180:
                raise ValueError
            self.add_history("camera "+str(angle))
            if jarvis_cmd.camera(angle):
                self.ans(serv, author, "Caméra réglée à "+angle+"°.")
            else:
                self.ans(serv, author, "Je n'arrive pas à régler la caméra.")
        except ValueError:
            alias = args[1].lower()
            angle = -1
            with open(self.basepath+"/data/camera.alias", 'r') as fh:
                matchs = [i for i in fh.readlines if i.startswith(alias)]
                if len(matchs) == 0:
                    raise InvalidArgs
                else:
                    angle = int((matchs[0].split(":"))[1].strip())
                    self.add_history("camera "+alias)
                    if jarvis_cmd.camera(angle):
                        self.ans(serv, author, "Caméra réglée à "+angle+"°.")
                    else:
                        self.ans(serv, author,
                                 "Je n'arrive pas à régler la caméra.")

    def alias(self, serv, author, args):
        """Handles aliases"""
        # TODO

    def lumiere(self, serv, author, args):
        """Handles light"""
        # TODO

    def dis(self, serv, author, args):
        """Say something"""
        if len(args) > 1:
            something = " ".join(args[1:]).strip('" ')
            self.add_history("dis "+something)
            if jarvis_cmd.dis(something):
                self.ans(serv, author, something)
            else:
                self.ans(serv, author, "Je n'arrive plus à parler…")
        else:
            raise InvalidArgs

    def atx(self, serv, author, args):
        """Handles RepRap ATX"""
        if args[1] in ["on", "off"]:
            self.add_history("atx "+args[1])
            if args[1] == "on" and jarvis_cmd.atx(1):
                self.ans(author, "ATX allumée.")
            elif args[1] == "off" and jarvis_cmd.atx(0):
                self.ans(serv, author, "ATX éteinte.")
            else:
                self.ans(serv, author, "L'ATX est devenue incontrôlable !")
        else:
            raise InvalidArgs

    def historique(self, serv, author, args):
        """Handles history"""
        try:
            if(len(args) == 3 and
               int(args[2]) < len(self.history) and
               int(args[3]) < len(self.history)):
                start = int(args[2])
                end = int(args[3])
            elif len(args) == 2:
                start = -int(args[1])
                end = None
            else:
                start = -config.hist_lines_to_show
                end = None
        except ValueError:
            raise InvalidArgs
        self.ans(serv, "Historique :")
        if len(self.history[start:end]) == 0:
            self.say(serv, "Pas d'historique disponible.")
        else:
            for hist in self.history[start:end]:
                self.say(serv, hist['cmd']+" par "+hist['author'])

    def jeu(self, serv, author, args):
        """Handles game"""
        self.ans(serv, author, "J'ai perdu le jeu…")

    def disclaimer(self, serv, author, args):
        """Handles disclaimer"""
        self.ans(serv, author, "Jarvis est un bot doté de capacités " +
                 "dépassant à la fois l'entendement et les limites d'irc. " +
                 "Prenez donc garde a toujours rester poli avec lui car " +
                 "bien qu'aucune intention malsaine ne lui a été " +
                 "volontairement inculquée,")
        self.say(serv, author, "JARVIS IS PROVIDED \"AS IS\", WITHOUT " +
                 "WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT " +
                 "NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS " +
                 "FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.")

    def log(self, serv, author, args):
        """Handles logging"""
        # TODO
        pass

    def update(self, serv, author, args):
        """Handles bot updating"""
        # TODO
        pass

    def tchou_tchou(self, serv):
        """Says tchou tchou"""
        self.say(serv, "Tchou tchou !")

    def stream(self, serv):
        # TODO
        pass

if __name__ == '__main__':
    JarvisBot().start()
