#!/usr/bin/env python3

import config
import datetime
from email.mime.text import MIMEText
import irc.bot as ircbot
import jarvis_cmd
import mysql.connector
import os
import random
import re
import requests
import shlex
import smtplib
import subprocess
import sys
from collections import deque # Fifo for log cache
from datetime import datetime


class InvalidArgs(Exception):
    pass


class JarvisBot(ircbot.SingleServerIRCBot):
    def __init__(self):
        ircbot.SingleServerIRCBot.__init__(self, [(config.server,
                                                   config.port)],
                                           config.nick,
                                           config.desc)
        self.version = "0.2"
        self.error = None
        self.basepath = os.path.dirname(os.path.realpath(__file__))+"/"
        self.history = self.read_history()
        self.leds = None
        self.current_leds = "off"
        self.rules = {}
        self.add_rule("aide",
                      self.aide,
                      help_msg="aide [commande]")
        self.add_rule("alias",
                      self.alias,
                      help_msg="alias [categorie]")
        self.add_rule("atx",
                      self.atx,
                      help_msg="atx on|off")
        self.add_rule("camera",
                      self.camera,
                      help_msg="camera ALIAS|ANGLE")
        self.add_rule("dis",
                      self.dis,
                      help_msg="dis \"quelque chose\"")
        self.add_rule("disclaimer",
                      self.disclaimer,
                      help_msg="disclaimer")
        self.add_rule("emprunt",
                      self.emprunt,
                      help_msg="emprunt outil \"jj/dd hh\" [email]")
        self.add_rule("historique",
                      self.historique,
                      help_msg="historique nb_lignes|(start end)")
        self.add_rule("info",
                      self.info,
                      help_msg="info [atx|camera|leds|stream]")
        self.add_rule("jeu",
                      self.jeu,
                      help_msg="jeu")
        self.add_rule("lien",
                      self.lien,
                      help_msg=("lien (dernier | " +
                                "(supprime|ignore|affiche) [id|permalien] | "))
        self.add_rule("log",
                      self.log,
                      help_msg="log debut ... fin")
        self.add_rule("lumiere",
                      self.lumiere,
                      help_msg="lumiere (R G B)|script")
        self.add_rule("stream",
                      self.stream,
                      help_msg="stream on|off")
        self.add_rule("update",
                      self.update,
                      help_msg="update")
        self.add_rule("version",
                      self.version,
                      help_msg="version")
        self.alias = self.read_alias()
        self.nickserved = False
        self.camera_pos = "0°"
        self.atx_status = "off"
        self.last_added_link = ""

        # Init Log
        self.log_cache = deque("", config.log_cache_size)
        self.log_save_buffer = ""
        self.log_save_buffer_count = 0

        # Init stream
        self.streamh = None
        self.oggfwd = None

        try:
            self.bdd = mysql.connector.connect(**config.mysql)
            self.bdd_cursor = self.bdd.cursor()
        except mysql.connector.Error as err:
            if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
                self.error = "Accès refusé à la BDD."
            elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.error = "La base MySQL n'existe pas."
            else:
                self.error = err
            self.bdd = None
            self.bdd_cursor = None

    def add_rule(self, name, action, help_msg=""):
        name = name.lower()
        if name not in self.rules:
            self.rules[name] = {}
        self.rules[name]['action'] = action
        self.rules[name]['help'] = help_msg

    def on_welcome(self, serv, ev):
        """Upon server connection"""
        serv.privmsg("nickserv", "identify "+config.password)
        serv.join(config.channel)

        #self.connection.execute_delayed(random.randrange(3600, 604800),
        #                                self.tchou_tchou, (serv))
        #self.connection.execute_every(3600, self.notifs_emprunts, (serv))
        if self.error is not None:
            self.say(serv, self.error)

    def on_privmsg(self, serv, ev):
        """Handles queries"""
        if(ev.source.nick.lower() == 'nickserv' and
           "You are now identified" in ev.arguments[0]):
            self.nickserved = True
        if(config.authorized_queries == [] or
           ev.source.nick in config.authorized_queries):
            self.on_pubmsg(self, serv, ev)

    def on_pubmsg(self, serv, ev):
        """Handles the queries on the chan"""
        author = ev.source.nick
        raw_msg = ev.arguments[0]
        msg = raw_msg.strip().lower()
        urls = re.findall("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                          msg)
        if len(urls) > 0:
            self.on_links(serv, author, urls)
        
        msg = msg.split(':', 1)
        if(msg[0].strip() == self.connection.get_nickname().lower() and
           (config.authorized == [] or author in config.authorized)):
            msg = shlex.split(msg[1])
            self.add_history(author, msg[0])
            if msg[0] in self.rules:
                try:
                    self.rules[msg[0]]['action'](serv, author, msg)
                except InvalidArgs:
                    self.aide(serv, author, msg)
            else:
                self.ans(serv, author, "Je n'ai pas compris…")

        self.add_log_cache(author, raw_msg) # Log each line

    def on_links(self, serv, author, urls):
        for url in set(urls):
            params = {"do": "api", "key": config.shaarli_key}
            post = {"url": url,
                    "description": "Posté par "+author+".",
                    "private": 0}
            r = requests.post(config.shaarli_url, params=params, data=post)
            if r.status_code != 200 and r.status_code != 201:
                self.ans(serv, author,
                         "Impossible d'ajouter le lien à shaarli. " +
                         "Status code : "+str(r.status_code))
            else:
                self.last_added_link = url

    def ans(self, serv, user, message):
        """Answers to specified user"""
        serv.privmsg(config.channel, user+": "+message)

    def say(self, serv, message):
        """Say something on the channel"""
        serv.privmsg(config.channel, message)

    def add_history(self, author, cmd):
        """Adds something to history"""
        insert = {"author": author, "cmd": cmd}
        if(config.history_no_doublons and
           (len(self.history) == 0 or self.history[-1] != insert)):
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
        return (config.nick + "Bot version " +
                self.version + " by " + config.author)

    def has_admin_rights(self, serv, author):
        """Checks that author is in admin users"""
        if len(config.admin) > 0 and author not in config.admin:
            self.ans(serv, author,
                     "Vous n'avez pas l'autorisation d'accéder à cette " +
                     "commande.")
            return False
        return True

    def add_log_cache(self, author, msg):
        """Add line to log cache. If cache is full, last line is append to save buffer which is on its turn flushed to disk if full"""
        if len(self.log_cache) >= config.log_cache_size:
            self.log_cache_to_buffer()
            if self.log_save_buffer_count > config.log_save_buffer_size:
                self.log_flush_buffer()

        self.log_cache.appendleft((datetime.now().hour, datetime.now().minute, author, msg))

    def log_cache_to_buffer(self):
        """Pop a line from log cache and append it to save buffer"""
        t = self.log_cache.pop()
        print(t)
        self.log_save_buffer += "%d:%d <%s> %s\n" % t
        self.log_save_buffer_count += 1

    def log_flush_buffer(self):
        """Flush log save buffer to disk"""
        with open(config.log_all_file, 'a') as f:
            f.write(self.log_save_buffer)
            self.log_save_buffer = ""
            self.log_save_buffer_count = 0

    def log_flush_all(self):
        for i in range(len(self.log_cache)):
            self.log_cache_to_buffer()
        self.log_flush_buffer()

    def aide(self, serv, author, args):
        """Prints help"""
        self.ans(serv, author, config.desc + " Commandes disponibles :")
        if len(args) > 1 and args[0] == "aide":
            self.say(serv, self.rules[args[1]]['help'])
        elif args[0] != "aide" and args[0] in self.rules:
            self.say(serv, self.rules[args[0]]['help'])
        else:
            for rule in sorted(self.rules):
                self.say(serv, self.rules[rule]['help'])

    def info(self, serv, author, args):
        """Prints infos"""
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
            if self.atx_status == "off":
                to_say += "ATX : "+redc+"off"+endc+", "
            else:
                to_say += "ATX : "+greenc+"on"+endc+", "
        if 'leds' in infos_items:
            if isinstance(self.leds, subprocess.Popen):
                poll = self.leds.poll()
                if poll is not None and poll != 0:
                    self.leds = None
                    self.current_leds = "off"
            if self.current_leds is not None:
                if self.current_leds == "off":
                    to_say += "LEDs : "+redc+"off"+endc+", "
                else:
                    to_say += "LEDs : "+greenc+self.current_leds+endc+", "
            else:
                to_say += "LEDs : "+redc+"off"+endc+", "
        if 'stream' in infos_items:
            if(self.oggfwd is not None and self.streamh is not None and
               self.oggfwd.poll() is None and self.streamh.poll() is None):
                to_say += "Stream : "+greenc+"Actif"+endc+", "
            else:
                to_say += "Stream : "+redc+"HS"+endc+", "
        if 'camera' in infos_items:
            to_say += "Caméra : "+self.camera_pos+", "
        to_say = to_say.strip(", ")
        self.ans(serv, author, to_say)

    def camera(self, serv, author, args):
        """Controls camera"""
        if len(args) < 2:
            raise InvalidArgs
        try:
            angle = int(args[1])
            if angle < 0 or angle > 180:
                raise ValueError
            if jarvis_cmd.camera(angle):
                self.camera_pos = str(angle)+"°"
                self.ans(serv, author, "Caméra réglée à "+angle+"°.")
            else:
                self.ans(serv, author, "Je n'arrive pas à régler la caméra.")
        except ValueError:
            alias = args[1]
            angle = -1
            matchs = [i for i in self.alias
                      if i["type"] == "camera" and i["name"] == alias]
            if len(matchs) == 0:
                raise InvalidArgs
            else:
                angle = int(matchs[0]["value"])
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
        if len(aliases) > 0:
            types = set([i['type'] for i in aliases])
            for i in types:
                self.ans(serv, author,
                         "Liste des alias disponibles pour "+i+" :")
                to_say = ""
                for j in [k for k in self.alias if k['type'] == i]:
                    to_say += "{"+j['name']+", "+j['value']+"}, "
                to_say = to_say.strip(", ")
                self.say(serv, to_say)
        else:
            self.ans(serv, author, "Aucun alias défini.")

    def lumiere(self, serv, author, args):
        """Handles light"""
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

                if jarvis_cmd.lumiere(R, G, B):
                    self.current_leds = "("+str(R)+", "+str(G)+", "+str(B)+")"
                    self.ans(serv, author, "LED réglée sur "+self.current_leds)
                else:
                    self.ans(serv, author, "Impossible de régler les LEDs.")
            except (AssertionError, ValueError):
                raise InvalidArgs
        elif len(args) == 2:
            script = os.path.join(self.basepath+"data/leds", args[1])+".py"
            if os.path.isfile(script):
                print("ok")
                self.leds = subprocess.Popen(['python', script],
                                             stdout=subprocess.DEVNULL)
                self.current_leds = args[1]
        else:
            raise InvalidArgs

    def dis(self, serv, author, args):
        """Say something"""
        if len(args) > 1:
            for something in args[1:]:
                if jarvis_cmd.dis(something):
                    self.ans(serv, author, something)
                else:
                    self.ans(serv, author, "Je n'arrive plus à parler…")
        else:
            raise InvalidArgs

    def atx(self, serv, author, args):
        """Handles RepRap ATX"""
        if len(args) > 1 and args[1] in ["on", "off"]:
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
            if(len(args) == 4 and
               int(args[2]) < len(self.history) and
               int(args[3]) < len(self.history)):
                start = int(args[2])
                end = int(args[3])
            elif len(args) == 2:
                start = -int(args[1])
                end = None
            else:
                start = -config.history_lines_to_show
                end = None
        except ValueError:
            raise InvalidArgs
        self.ans(serv, author, "Historique :")
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
        self.say(serv, "JARVIS IS PROVIDED \"AS IS\", WITHOUT " +
                 "WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT " +
                 "NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS " +
                 "FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.")

    def log(self, serv, author, args):
        """Handles logging"""
        if len(args) != 4 or args[2] != '...':
            raise InvalidArgs

        tmp = []
        start = args[1]
        end = args[3]
        found_end = False
        found_start = False
        for (h, m, auth, msg) in self.log_cache:
            end_index = msg.rfind(end)
            if not found_end and end_index >= 0:
                msg = msg[:end_index + len(end)]
                found_end = True
            if found_end:
                start_index = msg.find(start)
                if start_index >= 0:
                    msg = msg[start_index:]
                    tmp.append((h, m, auth, msg))
                    found_start = True
                    break
                tmp.append((h, m, auth, msg))

        if found_start:
            with open(config.log_file, 'a') as f:
                for i in range(len(tmp)):
                    f.write("%d:%d <%s> %s\n" % tmp.pop())
            self.ans(serv, author, "Loggé !")
        else:
            self.ans(serv, author, "Je n'ai pas trouvé")
            print("pas trouvé", found_end, found_start)




    def update(self, serv, author, args):
        """Handles bot updating"""
        if author in config.admins:
            subprocess.Popen([self.basepath+"updater.sh", self.basepath])
            self.ans(serv, author, "I will now update myself.")
            sys.exit()

    def tchou_tchou(self, serv):
        """Says tchou tchou"""
        self.say(serv, "Tchou tchou !")
        self.connection.execute_delayed(random.randrange(3600, 604800),
                                        self.tchou_tchou)

    def stream(self, serv, author, args):
        """Handles stream transmission"""
        if args[1] == "on":
            if self.oggfwd is not None and self.streamh is not None:
                self.ans(serv, author,
                         "La retransmission est déjà opérationnelle.")
                return
            try:
                if self.streamh is None:
                    self.streamh = subprocess.Popen(["python",
                                                    self.basepath +
                                                    "/stream.py",
                                                    "/dev/video*"],
                                                   stdout=subprocess.PIPE)
                if self.oggfwd is None:
                    self.oggfwd = subprocess.Popen([config.oggfwd_path +
                                                    "/oggfwd",
                                                    config.stream_server,
                                                    config.stream_port,
                                                    config.stream_pass,
                                                    config.stream_mount,
                                                    "-n "+config.stream_name,
                                                    "-d "+config.stream_desc,
                                                    "-u "+config.stream_url,
                                                    "-g "+config.stream_genre],
                                                   stdin=self.streamh.stdout)
                self.ans(serv, author, "Retransmission lancée !")
            except (IOError, ValueError):
                self.ans(serv,
                         author,
                         "Impossible de démarrer la retransmission.")
        elif args[1] == "off":
            if self.streamh is not None:
                try:
                    self.streamh.terminate()
                except ProcessLookupError:
                    pass
                self.streamh = None
            if self.oggfwd is not None:
                try:
                    self.oggfwd.terminate()
                except ProcessLookupError:
                    pass
                self.oggfwd = None
            self.ans(serv, author, "Retransmission interrompue.")
        else:
            raise InvalidArgs

    def version(self, serv, author, args):
        """Prints current version"""
        self.ans(serv, author, self.get_version())

    def emprunt(self, serv, author, args):
        """Handles tools borrowings"""
        if len(args) < 3:
            raise InvalidArgs
        this_year = datetime.date.now().year
        tool = args[1]
        until = args[2].split(" /").strip()
        try:
            assert(len(until) > 2)
            day = int(until[0])
            month = int(until[1])
            assert(month > 0 and month < 13)
            if month % 2 == 1:
                assert(day > 0 and day <= 31)
            elif month == 2:
                if((this_year % 4 == 0 and this_year % 100 != 0) or
                   this_year % 400 == 0):
                    assert(day > 0 and day <= 29)
                else:
                    assert(day > 0 and day <= 28)
            else:
                assert(day > 0 and day <= 30)
            hour = int(until[2])
            assert(hour >= 0 and hour < 24)
        except (AssertionError, ValueError):
            raise InvalidArgs
        if len(args) > 3:
            if re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$",
                        args[3]) is not None:
                borrower = args[3]
            else:
                raise InvalidArgs
        else:
            borrower = author
        if month < datetime.date.now().month:
            year = this_year + 1
        else:
            year = this_year
        until = datetime.datetime(year, month, day, hour)
        query = ("INSERT INTO borrowings" +
                 "(id, borrower, tool, from, until, back)" +
                 "VALUES ('', %s, %s, %s, %s, %s)")
        values = (borrower, tool, datetime.datetime.now(), until, 0)
        try:
            self.bdd_cursor.execute("SELECT id, borrower, tool, from, " +
                                    "until, back FROM borrowings " +
                                    "WHERE back=0 AND borrower=%s AND tool=%s",
                                    (borrower, tool))
            if len(self.bdd_cursor) > 0:
                self.ans(serv,
                         author,
                         "Il y a déjà un emprunt en cours, mise à jour.")
                query = ("UPDATE borrowings" +
                         "(id, borrower, tool, from, until, back)" +
                         "SET until=%s " +
                         "WHERE back=0 AND borrower=%s AND tool=%s")
                values = (until, borrower, tool)
            self.bdd_cursor.execute(query, values)
            self.bdd.commit()
        except mysql.connector.errors.Error:
            serv.ans(serv, author, "Impossible d'ajouter l'emprunt.")
            return
        def padding(number):
            if number < 10:
                return "0"+str(number)
            else:
                return str(number)
        self.ans(serv, author,
                 "Emprunt de "+tool+" jusqu'au " +
                 padding(day)+"/"+padding(month)+" à "+padding(hour)+"h noté.")

    def notifs_emprunts(self, serv):
        """Notifications when borrowing is over"""
        now = datetime.datetime.now()
        later_1h = now + datetime.timedelta(hours=1)
        query = ("SELECT borrower, tool, from, until, back FROM borrowings " +
                 "WHERE until BETWEEN %s AND %s AND back=0")
        try:
            self.bdd_cursor.execute(query, (now, later_1h))
        except mysql.connector.errors.Error:
            serv.say(serv,
                     "Impossible de récupérer les notifications d'emprunts.")
            return
        for (borrower, tool, until) in self.bdd_cursor:
            notif = ("Tu as emprunté "+tool+" depuis le " +
                     datetime.strftime("%d/%m/%Y") +
                     " et tu devais le " +
                     "rendre aujourd'hui. L'as-tu rendu ?")
            if re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$",
                        borrower) is not None:
                notif = "Salut,\n\n" + notif
                notif += ("\nPour confirmer le retour, répond à cet e-mail " +
                          "ou connecte-toi sur IRC (#hackens) pour " +
                          "le confirmer directement à Jarvis.")
                msg = MIMEText(notif)
                msg["Subject"] = "Emprunt en hack'ave"
                msg["From"] = config.emails_sender
                msg["to"] = borrower

                s = smtplib.SMTP('localhost')
                s.sendmail(config.emails_sender, [borrower], msg.as_string())
            else:
                serv.privmsg(borrower, notif)
                serv.privmsg(borrower,
                             "Pour confirmer le retour, répond-moi \"oui\".")

    def lien(self, serv, author, args):
        """Handles links managements through Shaarli API"""
        params = {"do": "api", "key": config.shaarli_key}
        if len(args) > 1 and args[1] == "dernier":
            self.ans(serv, author, self.last_added_link)
        elif len(args) > 1 and args[1] == "ignore":
            if not self.has_admin_rights(serv, author):
                return
            if len(args) == 2:
                post = {"url": self.last_added_link, "private": 1}
                r = requests.post(config.shaarli_url,
                                  params=params,
                                  data=post)
                if r.status_code != 200:
                    self.ans(serv, author,
                             "Impossible d'éditer le lien " +
                             self.last_added_link+". "
                             "Status code : "+str(r.status_code))
                    return
            else:
                for arg in args[2:]:
                    if arg.startswith(config.shaarli_url):
                        small_hash = arg.split('?')[-1]
                    else:
                        small_hash = arg
                    params["hash"] = small_hash
                    r = requests.get(config.shaarli_url,
                                     params=params)
                    del(params["hash"])
                    if r.status_code != requests.code.ok:
                        self.ans(serv, author,
                                 "Impossible d'éditer le lien "+arg+". " +
                                 "Status code : "+str(r.status_code))
                        continue
                    post = {"url": r.json['url'], "private": 1}
                    r = requests.post(config.shaarli_url,
                                      params=params,
                                      data=post)
                    if r.status_code != 200:
                        self.ans(serv, author,
                                 "Impossible d'éditer le lien "+arg+". " +
                                 "Status code : "+str(r.status_code))
                        continue
                self.ans(serv, author, "Liens rendus publics.")
        elif len(args) > 1 and args[1] == "supprime":
            if not self.has_admin_rights(serv, author):
                return
            if len(args) == 2:
                params["url"] = self.last_added_link
                r = requests.get(config.shaarli_url,
                                 params=params)
                del(params["url"])
                if r.status_code != requests.code.ok:
                    self.ans(serv, author,
                             "Impossible de supprimer le lien " +
                             arg + ". " +
                             "Status code : "+str(r.status_code))
                    return
                params["key"] = r.json()["key"]
                r = requests.delete(config.shaarli_url,
                                    params=params)
                del(params["key"])
                if r.status_code != 200:
                    self.ans(serv, author,
                             "Impossible de supprimer le lien " +
                             self.last_added_link+". "
                             "Status code : "+str(r.status_code))
                    return
                self.ans(serv, author, "Liens supprimés.")
            else:
                for arg in args[2:]:
                    if arg.startswith(config.shaarli_url):
                        small_hash = arg.split('?')[-1]
                    else:
                        small_hash = arg
                    params["hash"] = small_hash
                    r = requests.get(config.shaarli_url,
                                     params=params)
                    del(params["hash"])
                    if r.status_code != requests.code.ok:
                        self.ans(serv, author,
                                 "Impossible de supprimer le lien " +
                                 arg + ". " +
                                 "Status code : "+str(r.status_code))
                        continue
                    params["key"] = r.json()["key"]
                    r = requests.delete(config.shaarli_url,
                                        params=params)
                    del(params["key"])
                    if r.status_code != 200:
                        self.ans(serv, author,
                                 "Impossible de supprimer le lien " +
                                 arg + ". " +
                                 "Status code : "+str(r.status_code))
                        continue
                self.ans(serv, author, "Liens supprimés.")
        elif len(args) > 2 and args[1] == "affiche":
            if not self.has_admin_rights(serv, author):
                return
            for arg in args[2:]:
                if arg.startswith(config.shaarli_url):
                    small_hash = arg.split('?')[-1]
                else:
                    small_hash = arg
                post = {"hash": small_hash}
                r = requests.post(config.shaarli_url,
                                  params=params,
                                  data=post)
                if r.status_code != requests.code.ok:
                    self.ans(serv, author,
                             "Impossible d'éditer le lien "+arg+". " +
                             "Status code : "+str(r.status_code))
                    continue
                post = {"url": r.json['url'], "private": 0}
                r = requests.post(config.shaarli_url,
                                  params=params,
                                  data=post)
                if r.status_code != 200:
                    self.ans(serv, author,
                             "Impossible d'éditer le lien "+arg+". " +
                             "Status code : "+str(r.status_code))
                    continue
                self.ans(serv, author, "Liens rendus publics.")
        else:
            raise InvalidArgs

    def close(self):
        """Exits nicely"""
        if self.leds is not None:
            try:
                self.leds.terminate()
            except ProcessLookupError:
                pass
            self.leds = None
            self.current_leds = "off"
        if self.streamh is not None:
            try:
                self.streamh.terminate()
            except ProcessLookupError:
                pass
            self.streamh = None
        if self.oggfwd is not None:
            try:
                self.oggfwd.terminate()
            except ProcessLookupError:
                pass
            self.oggfwd = None
        if self.bdd_cursor is not None:
            self.bdd_cursor.close()
        if self.bdd is not None:
            self.bdd.close()
        self.log_flush_all()


if __name__ == '__main__':
    try:
        bot = JarvisBot()
        bot.start()
    except Exception as e:
        bot.close()
        raise e
