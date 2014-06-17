#!/usr/bin/env python2

import config
import irclib
import ircbot
import jarvis_cmd
import os

class InvalidArgs(Exception):
    pass

class JarvisBot(ircbot.SingleServerIRCBot):
    def __init__(self):
        ircbot.SingleServerIRCBot.__init__(self, [(config.server, config.port)],
                                           config.nick,
                                           config.desc)
        self.version = "0.2"
        self.basepath = os.path.dirname(os.path.realpath(__file__))
        self.history = self.read_history()
        self.rules = {}
        add_rule("aide", self.aide)
        add_rule("alias", self.alias)
        add_rule("atx", self.atx)
        add_rule("camera", self.camera)
        add_rule("dis", self.dis)
        add_rule("disclaimer", self.disclaimer)
        add_rule("historique", self.historique)
        add_rule("info", self.info)
        add_rule("jeu", self.jeu)
        add_rule("log", self.log)
        add_rule("lumiere", self.lumiere)
        add_rule("stream", self.stream)
        add_rule("update", self.update)
        self.nickserved = False

    def add_rule(self, name, action, help_msg=""):
        name = name.lower()
        if not name in self.rules:
            self.rules[name] = {}
        self.rules[name]['action'] = action
        self.rules[name]['help'] = help_msg

    def on_welcome(self, serv, ev):
        """Upon server connection"""
        self.privmsg(self, "nickserv", "identify "+config.password)
        serv.join(config.channel)

    def on_privmsg(self, serv, ev):
        """Handles queries"""
        if(nm_to_n(ev.source()).lower() == 'nickserv' and
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
                    self.rules[msg[0]]['action'](author, msg)
                except InvalidCommand:
                    aide(author, msg[0])
            else:
                self.ans(author, "Je n'ai pas compris…")

    def ans(self, user, message):
        """Answers to specified user"""
        serv.privmsg(config.channel, user+": "+message)

    def say(self, message):
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
        with open(basepath+"data/history", 'w+') as fh:
            fh.write(write)

    def read_history(self):
        history = []
        if os.path.isfile(self.basepath+"data/history"):
            with open(basepath+"data/history", 'r') as fh:
                for line in fh.readlines():
                    line = [i.strip() for i in line.split('\t')]
                    insert = {'author': line[0], 'cmd': line[1]}
                    if config.history_no_doublons and history[-1] != insert:
                        history.append(history)
        return history

    def get_version(self):
        """Returns the bot version"""
        return "Jarvis Bot version "+version+" by hackEns"

    def aide(self, author, cmd=""):
        """Prints help"""
        self.ans("Jarvis au rapport ! Commandes disponibles :")
        for rule in self.rules:
            self.say(self.rules[rule]['help'])

    def info(self, author, args):
        """Prints infos"""
        # TODO

    def camera(self, author, args):
        """Controls camera"""
        try:
            angle = int(msg[1])
            if angle < 0 or angle > 180:
                raise ValueError
            add_history("camera "+str(angle))
            if jarvis_cmd.camera(angle):
                self.ans(author, "Caméra réglée à "+angle+"°.")
            else:
                self.ans("Je n'arrive pas à régler la caméra.")
        except ValueError:
            alias = msg[1].lower()
            angle = -1
            with open(self.basepath+"/data/camera.alias", 'r') as fh:
                matchs = [i for i in fh.readlines if i.startswith(alias)]
                if len(matchs) == 0:
                    raise InvalidArgs
                else:
                    angle = int((matchs[0].split(":"))[1].strip())
                    add_history("camera "+alias)
                    if jarvis_cmd.camera(angle):
                        self.ans(author, "Caméra réglée à "+angle+"°.")
                    else:
                        self.ans(author, "Je n'arrive pas à régler la caméra.")

    def alias(self, author, args):
        """Handles aliases"""
        # TODO

    def lumiere(self, author, args):
        """Handles light"""
        # TODO

    def dis(self, author, args):
        """Say something"""
        if len(msg) > 1:
            something = " ".join(msg[1:]).strip('" ')
            add_history("dis "+something)
            if jarvis_cmd.dis(something):
                self.ans(author, something)
            else:
                self.ans(author, "Je n'arrive plus à parler…")
        else:
            raise InvalidArgs

    def atx(self, author, args):
        """Handles RepRap ATX"""
        if msg[1] in ["on", "off"]:
            add_history("atx "+msg[1])
            if msg[1] == "on" and jarvis_cmd.atx(1):
                self.ans(author, "ATX allumée.")
            elif msg[1] == "off" and jarvis_cmd.atx(0):
                self.ans(author, "ATX éteinte.")
            else:
                self.ans(author, "L'ATX est devenue incontrôlable !")
        else:
            raise InvalidArgs

    def historique(self, author, args):
        """Handles history"""
        try:
            if len(msg) == 1:
                start = -config.hist_lines_to_show
                end = None
            elif len(msg) == 2:
                start = -int(msg[1])
                end = None
            elif len(msg) == 3:
                start = int(msg[2])
                end = int(msg[3])
        except ValueError:
            raise InvalidArgs
        self.ans("Historique :")
        for hist in self.history[start:end]:
            self.say(hist['cmd']+" par "+hist['author'])

    def jeu(self, author, args):
        """Handles game"""
        self.ans(author, "J'ai perdu le jeu…")

    def disclaimer(self, author, args):
        """Handles disclaimer"""
        self.ans(author, "Jarvis est un bot doté de capacités dépassant à " +
                 "la fois l'entendement et les limites d'irc. Prenez donc " +
                 "garde a toujours rester poli avec lui car bien " +
                 "qu'aucune intention malsaine ne lui a été " +
                 "volontairement inculquée,")
        self.say(author, "JARVIS IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF " +
                 "ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED " +
                 "TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A " +
                 "PARTICULAR PURPOSE AND NONINFRINGEMENT.")

    def log(self, author, args):
        """Handles logging"""
        # TODO

    def update(self, author, args):
        """Handles bot updating"""
        # TODO

    def tchou_tchou(self):
        """Says tchou tchou"""
        self.say("Tchou tchou !")

    def stream(self):
        # TODO

if __name__ == '__main__':
    JarvisBot().start()
