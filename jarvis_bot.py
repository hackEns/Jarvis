#!/usr/bin/env python3

import config
from import irc.client import NickMask
import irc.bot as ircbot
import jarvis_cmd
from multiprocessing import Process
import os
import random
import subprocess
import sys


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
        self.leds = None
        self.current_leds = ""
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
        self.alias = self.read_alias()
        self.nickserved = False
        self.camera_pos = "0°"
        self.atx_status = "off"
        self.stream = subprocess.Popen(["python", self.basepath + "/stream.py",
                                        "/dev/video*"],
                                       stdout=subprocess.PIPE)
        self.oggfwd = subprocess.Popen([config.oggfwd_path + "/oggfwd",
                                        config.stream_server,
                                        config.stream_port,
                                        config.stream_pass,
                                        config.stream_mount,
                                        "-n " + config.stream_name,
                                        "-d " + config.stream_desc,
                                        "-u " + config.stream_url,
                                        "-g " + config.stream_genre],
                                       stdin=self.stream.stdout)

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
        self.execute_delayed(random.randrange(3600, 604800), self.tchou_tchou)
        self.say(serv, "Retransmission opérationnelle !")

    def on_privmsg(self, serv, ev):
        """Handles queries"""
        if(NickMask(ev.source()).nick.lower() == 'nickserv' and
           "You are now identified" in ev.arguments()[0]):
            self.nickserved = True

    def on_pubmsg(self, serv, ev):
        """Handles the queries on the chan"""
        author = NickMask(ev.source()).nick
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
        insert = {"author": author, "cmd": cmd}
        if config.history_no_doublons and self.history[-1] != insert:
            self.history.append(insert)
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
                    history.append({'author': line[0], 'cmd': line[1]})
        return history

    def write_alias(self):
        write = {}
        for item in self.alias:
            try:
                write[item["type"]] += item["name"]+":"+item["value"]+"\n"
            except KeyError:
                write[item["type"]] = item["name"]+":"+item["value"]+"\n"
        for type in write:
            with open(self.basepath+"data/"+type+".alias", "w+") as fh:
                fh.write(write)

    def read_alias(self):
        alias = []
        if os.path.isfile(self.basepath+"data/camera.alias"):
            with open(self.basepath+"data/camera.alias", 'r') as fh:
                for line in fh.readlines():
                    line = [i.strip() for i in line.split(':')]
                    alias.append({"type": "camera",
                                  "name": line[0],
                                  "value": line[1]})
        return sorted(alias, key=lambda k: k['type'])

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
        all_items = ['atx', 'leds', 'stream', 'camera']
        greenc = "\033[92m"
        redc = "\033[91m"
        endc = "\033[0m"
        if len(args) > 1:
            infos_items = [i for i in args[1:] if i in all_items]
        else:
            infos_items = all_items
        to_say = "Statut : "
        if 'atx' in infos_items:
            if self.atx_status == "off":
                to_say += "ATX : "+redc+"off"+endc+", "
            else:
                to_say += "ATX : "+greenc+"on"+endc+", "
        if 'leds' in infos_items:
            if self.current_leds is not None and self.leds_alive():
                to_say += "LEDs : "+self.current_leds+", "
            else:
                to_say += "LEDs : "+redc+"off"+endc+", "
        if 'stream' in infos_items:
            if self.oggfwd.poll() is None and self.stream.poll() is None:
                to_say += "Stream : "+greenc+"Actif"+endc+", "
            else:
                to_say += "Stream : "+redc+"HS"+endc+", "
        if 'camera' in infos_items:
            to_say += "Caméra : "+self.camera_pos+", "
        to_say = to_say.strip(", ")
        self.ans(serv, author, to_say)

    def camera(self, serv, author, args):
        """Controls camera"""
        try:
            angle = int(args[1])
            if angle < 0 or angle > 180:
                raise ValueError
            self.add_history(author, "camera "+str(angle))
            if jarvis_cmd.camera(angle):
                self.camera_pos = str(angle)+"°"
                self.ans(serv, author, "Caméra réglée à "+angle+"°.")
            else:
                self.ans(serv, author, "Je n'arrive pas à régler la caméra.")
        except ValueError:
            alias = args[1].lower()
            angle = -1
            matchs = [i for i in self.alias
                      if i["type"] == "camera" and i["name"] == alias]
            if len(matchs) == 0:
                raise InvalidArgs
            else:
                angle = int(matchs[0]["value"])
                self.add_history(author, "camera "+alias)
                if jarvis_cmd.camera(angle):
                    self.camera_pos = args[1]
                    self.ans(serv, author, "Caméra réglée à "+angle+"°.")
                else:
                    self.ans(serv, author,
                             "Je n'arrive pas à régler la caméra.")

    def alias(self, serv, author, args):
        """Handles aliases"""
        if len(args) > 4 and args[1] == "add":
            doublons = [i for i in self.alias
                        if i["type"] == args[2] and i["name"] == args[3]]
            for d in doublons:
                self.alias.remove(d)
            self.alias.append({"type": args[2],
                               "name": args[3],
                               "value": args[4]})
            self.write_alias()
            self.ans(serv, author,
                     "Nouvel alias ajouté : " +
                     "{"+args[2]+", "+args[3]+", "+args[4]+"}")
            return
        elif len(args) > 1:
            aliases = [i for i in self.alias if i['type'] == args[1]]
        else:
            aliases = self.alias
        types = set([i['type'] for i in aliases])
        for i in types:
            self.ans(serv, author, "Liste des alias disponibles pour "+i)
            to_say = ""
            for j in [k for k in self.alias if k['type'] == i]:
                to_say += "{"+j['name']+", "+j['value']+"}, "
            to_say = to_say.strip(", ")
            self.say(serv, to_say)

    def lumiere(self, serv, author, args):
        """Handles light"""
        if self.leds is not None:
            self.leds.terminate()
        if len(args) == 4:
            try:
                R = int(args[1])
                G = int(args[2])
                B = int(args[3])

                if(R > 255 or R < 0 or
                   G > 255 or G < 0 or
                   B > 255 or B < 0):
                    raise ValueError

                self.leds = Process(target=jarvis_cmd.lumiere, args=(R, G, B))
                self.current_leds = "("+str(R)+", "+str(G)+", "+str(B)+")"
                self.leds.start()
            except ValueError:
                raise InvalidArgs
        elif len(args) == 2:
            script = os.path.join(self.basepath+"data/leds", args[1])
            if os.path.isfile(script):
                self.leds = subprocess.Popen(['python', script],
                                             stdout=subprocess.DEVNULL)
                self.current_leds = args[1]
        else:
            raise InvalidArgs

    def leds_alive(self):
        """Returns True if leds process is alive"""
        if isinstance(self.leds, subprocess.Popen):
            return self.leds.poll() is None
        elif isinstance(self.leds, Process):
            return self.leds.is_alive()
        else:
            return False

    def dis(self, serv, author, args):
        """Say something"""
        if len(args) > 1:
            something = " ".join(args[1:]).strip('" ')
            self.add_history(author, "dis "+something)
            if jarvis_cmd.dis(something):
                self.ans(serv, author, something)
            else:
                self.ans(serv, author, "Je n'arrive plus à parler…")
        else:
            raise InvalidArgs

    def atx(self, serv, author, args):
        """Handles RepRap ATX"""
        if args[1] in ["on", "off"]:
            self.add_history(author, "atx "+args[1])
            if args[1] == "on" and jarvis_cmd.atx(1):
                self.atx_status = args[1]
                self.ans(author, "ATX allumée.")
            elif args[1] == "off" and jarvis_cmd.atx(0):
                self.atx_status = args[1]
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
        self.add_history(author, " ".join(args))

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
        self.add_history("update")
        subprocess.Popen([self.basepath + "/updater.sh", self.basepath])
        self.ans(serv, author, "I will now update myself.")
        sys.exit()

    def tchou_tchou(self, serv):
        """Says tchou tchou"""
        self.say(serv, "Tchou tchou !")
        self.execute_delayed(random.randrange(3600, 604800), self.tchou_tchou)

    def stream(self, serv, author, args):
        """Handles stream transmission"""
        if args[1] == "on":
            self.add_history("stream on")
            if self.oggfwd is not None and self.stream is not None:
                self.ans(serv, author,
                         "La retransmission est déjà opérationnelle.")
                return
            if self.stream is None:
                self.stream = subprocess.Popen(["python", self.basepath +
                                                "/stream.py",
                                                "/dev/video*"],
                                               stdout=subprocess.PIPE)
            if self.oggfwd is None:
                self.oggfwd = subprocess.Popen([config.oggfwd_path + "/oggfwd",
                                                config.stream_server,
                                                config.stream_port,
                                                config.stream_pass,
                                                config.stream_mount,
                                                "-n " + config.stream_name,
                                                "-d " + config.stream_desc,
                                                "-u " + config.stream_url,
                                                "-g " + config.stream_genre],
                                               stdin=self.stream.stdout)
            self.ans(serv, author, "Retransmission opérationnelle !")
        elif args[1] == "off":
            self.add_history("stream off")
            if self.stream is not None:
                self.stream.terminate()
                self.stream = None
            if self.oggfwd is not None:
                self.oggfwd.terminate()
                self.oggfwd = None
            self.ans(serv, author, "Retransmission interrompue.")
        else:
            raise InvalidArgs

    def close(self):
        """Exits nicely"""
        if self.leds is not None:
            self.leds.terminate()


if __name__ == '__main__':
    try:
        bot = JarvisBot()
        bot.start()
    except:
        bot.close()
