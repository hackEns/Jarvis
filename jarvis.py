#!/usr/bin/env python3

"""
This is the code for the jarvis bot on IRC.
"""

import datetime
from email.mime.text import MIMEText
import irc.bot as ircbot
import irc.connection
import mysql.connector
import os
import random
import re
import shlex
import smtplib
import ssl
import subprocess
import random

from Rules import *
from libjarvis.config import Config
from libjarvis import tools


config = Config()


class JarvisBot(ircbot.SingleServerIRCBot):
    """Main class for the Jarvis bot"""
    def __init__(self):
        if not config.get("use_ssl"):
            ircbot.SingleServerIRCBot.__init__(self, [(config.get("server"),
                                                       config.get("port"))],
                                               config.get("nick"),
                                               config.get("desc"))
        else:
            self.ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
            ircbot.SingleServerIRCBot.__init__(self, [(config.get("server"),
                                                       config.get("port"))],
                                               config.get("nick"),
                                               config.get("desc"),
                                               connect_factory=self.ssl_factory)
        self.basepath = os.path.dirname(os.path.realpath(__file__))+"/"
        self.nickserved = False

        self.log = Log(self, config)
        self.aide = Aide(self, config)
        self.atx = Atx(self, config)
        self.alias = Alias(self, self.basepath)
        self.budget = Budget(self)
        self.camera = Camera(self, config)
        self.courses = Courses(self)
        self.dis = Dis(self)
        self.disclaimer = Disclaimer(self)
        self.emprunt = Emprunt(self)
        self.historique = Historique(self, config, self.basepath)
        self.info = Info(self)
        self.jeu = Jeu(self)
        self.lien = Lien(self, config)
        self.lumiere = Lumiere(self, config)
        self.moderation = Moderation(self)
        self.tchou_tchou = Tchou_Tchou(self)
        self.update = Update(self, config)
        self.version = Version(self, config)

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
        self.add_rule("budget",
                      self.budget,
                      help_msg="budget (ajoute|retire) [dépense|crédit] " +
                      "montant [budget=BUDGET] commentaire")
        self.add_rule("camera",
                      self.camera,
                      help_msg="camera ALIAS|ANGLE")
        self.add_rule("courses",
                      self.courses,
                      help_msg="courses (acheter|annuler|acheté) " +
                      "item [commentaire]")
        self.add_rule("dis",
                      self.dis,
                      help_msg="dis \"quelque chose\"")
        self.add_rule("disclaimer",
                      self.disclaimer,
                      help_msg="disclaimer")
        self.add_rule("emprunt",
                      self.emprunt,
                      help_msg="emprunt outil \"jj/mm hh\" [email]")
        self.add_rule("historique",
                      self.historique,
                      help_msg="historique nb_lignes|(début fin)")
        self.add_rule("info",
                      self.info,
                      help_msg="info [atx|camera|leds|stream]")
        self.add_rule("jeu",
                      self.jeu,
                      help_msg="jeu")
        self.add_rule("lien",
                      self.lien,
                      help_msg=("lien (dernier | " +
                                "(supprime|cache|affiche) [id|permalien])"))
        self.add_rule("log",
                      self.log,
                      help_msg="log début ... fin")
        self.add_rule("lumiere",
                      self.lumiere,
                      help_msg="lumiere (R G B)|script")
        self.add_rule("moderation",
                      self.moderation,
                      help_msg="moderation [liste]")
        self.add_rule("retour",
                      self.retour,
                      help_msg="retour outil [email]")
        self.add_rule("stream",
                      self.stream,
                      help_msg="stream on|off")
        self.add_rule("update",
                      self.update,
                      help_msg="update")
        self.add_rule("version",
                      self.version,
                      help_msg="version")

        # Init stream
        self.streamh = None
        self.oggfwd = None

    def add_rule(self, name, action, help_msg=""):
        name = name.lower()
        if name not in self.rules:
            self.rules[name] = {}
        self.rules[name]['action'] = action
        self.rules[name]['help'] = help_msg

    def mysql_connect(self, serv):
        try:
            bdd = mysql.connector.connect(**config.get("mysql"))
            return bdd
        except mysql.connector.Error as err:
            if config.get("debug"):
                tools.warning("Debug : " + str(err))
            if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
                serv.say("Accès refusé à la BDD.")
            elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                serv.say("La base MySQL n'existe pas.")
            return None

    def on_welcome(self, serv, ev):
        """Upon server connection, handles nickserv"""
        serv.privmsg("nickserv", "identify "+config.get("password"))
        serv.join(config.get("channel"))

        self.connection.execute_delayed(random.randrange(3600, 84600),
                                        self.tchou_tchou, (serv,))
        self.connection.execute_every(3600, self.notifs_emprunts, (serv,))
        serv.privmsg("nickserv", "identify ")

    def on_privmsg(self, serv, ev):
        """Handles queries"""
        if(ev.source.nick.lower() == 'nickserv' and
           "You are now identified" in ev.arguments[0]):
            self.nickserved = True
        elif(ev.arguments[0].strip().startswith("oui")):
            id = ev.arguments[0].replace("oui", "").strip()
            self.retour_priv(self, ev.source.nick, id)
        elif(config.get("authorized_queries") == [] or
             (config.get("authorized_queries") is not None and
              ev.source.nick in config.get("authorized_queries"))):
            self.on_pubmsg(self, serv, ev)

    def on_pubmsg(self, serv, ev):
        """Handles the messages on the chan"""
        author = ev.source.nick
        raw_msg = ev.arguments[0]
        msg = raw_msg.strip()
        urls = re.findall("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                          msg)
        # If found some urls in the message, handles them
        if len(urls) > 0:
            self.lien.on_links(serv, author, urls)
        # If "perdu" or "jeu" or "game" or "42"  in the last message, do Jeu
        if ("perdu" in msg or "jeu" in msg or "game" in msg or "42" in msg) and random.randint(0, 10) == 7:
            self.jeu(serv)
        msg = msg.split(':', 1)
        if(msg[0].strip() == self.connection.get_nickname() and
           (config.get("authorized") == [] or author in config.get("authorized"))):
            try:
                msg = shlex.split(msg[1])
            except ValueError:
                self.say(serv, 'Oops.')
                return
            msg[0] = msg[0].lower()
            self.historique.add(author, msg[0])
            if msg[0] in self.rules:
                try:
                    self.rules[msg[0]]['action'](serv, author, msg)
                except InvalidArgs:
                    if config.get("debug"):
                        tools.warning("Debug : " + str(msg))
                    self.aide(serv, author, msg)
            elif msg[0] == "<3" or msg[0] == "♥":
                self.ans(serv, author, "Merci "+author+", moi aussi je t'aime très fort ! #Kikoo")
            else:
                self.ans(serv, author, "Je n'ai pas compris…")
        elif(msg[0].strip().lower() == "aziz" and
             (config.get("authorized") == [] or author in config.get("authorized"))):
            # Easter egg
            try:
                msg = shlex.split(msg[1])
            except ValueError:
                self.say(serv, 'Oops.')
                return
            msg[0] = msg[0].lower()
            if msg[0] == "lumiere":
                self.historique.add(author, msg[0])
                try:
                    self.rules[msg[0]]['action'](serv, author, msg)
                except InvalidArgs:
                    if config.get("debug"):
                        tools.warning("Debug : " + str(msg))
                    self.aide(serv, author, msg)
        self.log.add_cache(author, raw_msg)  # Log each line

    def ans(self, serv, user, message):
        """Answers to specified user"""
        serv.privmsg(config.get("channel"), user+": "+message)

    def say(self, serv, message):
        """Say something on the channel"""
        serv.privmsg(config.get("channel"), message)

    def has_admin_rights(self, serv, author):
        """Checks that author is in admin users"""
        if config.get("admins") is not None and author not in config.get("admins"):
            self.ans(serv, author,
                     "Vous n'avez pas l'autorisation d'accéder à cette " +
                     "commande.")
            return False
        return True

    def stream(self, serv, author, args):
        """Handles stream transmission"""
        args = [i.lower() for i in args]
        if len(args) < 2:
            raise InvalidArgs
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
                    self.oggfwd = subprocess.Popen([config.get("oggfwd_path") +
                                                    "/oggfwd",
                                                    config.get("stream_server"),
                                                    config.get("stream_port"),
                                                    config.get("stream_pass"),
                                                    config.get("stream_mount"),
                                                    "-n "+config.get("stream_name"),
                                                    "-d "+config.get("stream_desc"),
                                                    "-u "+config.get("stream_url"),
                                                    "-g "+config.get("stream_genre")],
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

    def retour(self, serv, author, args):
        """Handles end of borrowings"""
        args = [i.lower() for i in args]
        if len(args) < 2:
            raise InvalidArgs
        if len(args) > 2:
            if re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$",
                        args[2]) is not None:
                borrower = args[2]
            else:
                raise InvalidArgs
        else:
            borrower = author
        query = ("UPDATE borrowings SET back=1 WHERE tool=%s AND borrower=%s")
        values = (args[1], borrower)
        try:
            bdd = self.mysql_connect(serv)
            assert(bdd is not None)
        except AssertionError:
            return
        bdd_cursor = bdd.cursor()
        bdd_cursor.execute(query, values)
        if bdd_cursor.rowcount > 0:
            self.ans(serv, author,
                     "Retour de "+args[1]+" enregistré.")
        else:
            self.ans(serv, author,
                     "Emprunt introuvable.")
        bdd_cursor.close()
        bdd.close()

    def retour_priv(self, author, id):
        """Handles end of borrowings with private answers to notifications"""
        query = ("UPDATE borrowings SET back=1 WHERE id=%s")
        values = (id,)
        try:
            bdd = self.mysql_connect(serv)
            assert(bdd is not None)
        except AssertionError:
            return
        bdd_cursor = bdd.cursor()
        bdd_cursor.execute(query, values)
        if bdd_cursor.rowcount > 0:
            self.privmsg(author,
                         "Retour de "+args[1]+" enregistré.")
        else:
            self.privmsg(author,
                         "Emprunt introuvable.")
        bdd_cursor.close()
        bdd.close()

    def notifs_emprunts(self, serv):
        """Notifications when borrowing is over"""
        now = datetime.datetime.now()
        delta = datetime.timedelta(hours=2)
        query = ("SELECT id, borrower, tool, date_from, until " +
                 "FROM borrowings WHERE ((until <= %s AND " +
                 "until - date_from <= %s) " + "OR until <= %s) AND back=0")
        try:
            bdd = self.mysql_connect(serv)
            assert(bdd is not None)
        except AssertionError:
            return
        bdd_cursor = bdd.cursor()
        bdd_cursor.execute(query,
                           (now + delta, delta, now))
        for (id_field, borrower, tool, from_field, until) in bdd_cursor:
            notif = ("Tu as emprunté "+tool+" depuis le " +
                     datetime.strftime(from_field, "%d/%m/%Y") +
                     " et tu devais le " +
                     "rendre aujourd'hui. L'as-tu rendu ?")
            if re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$",
                        borrower) is not None:
                notif = "Salut,\n\n" + notif
                notif += ("\n\nPour confirmer le retour, répond à cet e-mail " +
                          "ou connecte-toi sur IRC (#hackens) pour " +
                          "le confirmer directement à Jarvis.")
                msg = MIMEText(notif)
                msg["Subject"] = "Emprunt en hack'ave"
                msg["From"] = config.get("emails_sender")
                msg["to"] = borrower

                s = smtplib.SMTP('localhost')
                s.sendmail(config.get("emails_sender"),
                           [borrower],
                           msg.as_string())
            else:
                serv.privmsg(borrower, notif)
                serv.privmsg(borrower,
                             "Pour confirmer le retour, répond-moi " +
                             "\"oui " + id_field + "\" en query.")
        bdd_cursor.close()
        bdd.close()

    def close(self):
        """Exits nicely"""
        # Run close for all the Rules
        for rule in self.rules:
            try:
                self.rules[rule]["action"].close()
            except AttributeError:
                pass
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

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
        print("Bye!")
        return not config.get("debug")

if __name__ == '__main__':
    try:
        with JarvisBot() as bot:
            bot.start()
    except KeyboardInterrupt:
        pass
