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
import requests
import shlex
import smtplib
import ssl
import subprocess
import sys

from Rules import *
from libjarvis.config import Config
from libjarvis import tools


config = Config()


class JarvisBot(ircbot.SingleServerIRCBot):
    """Main class for the Jarvis bot"""
    def __init__(self):
        if not config.use_ssl:
            ircbot.SingleServerIRCBot.__init__(self, [(config.server,
                                                       config.port)],
                                               config.nick,
                                               config.desc)
        else:
            self.ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
            ircbot.SingleServerIRCBot.__init__(self, [(config.server,
                                                       config.port)],
                                               config.nick,
                                               config.desc,
                                               connect_factory=self.ssl_factory)
        self.error = None
        self.basepath = os.path.dirname(os.path.realpath(__file__))+"/"
        self.leds = None
        self.current_leds = "off"

        try:
            self.bdd = mysql.connector.connect(**config.mysql)
            self.bdd_cursor = self.bdd.cursor()
        except mysql.connector.Error as err:
            if config.debug:
                tools.warning("Debug : " + str(err))
            if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
                self.error = "Accès refusé à la BDD."
            elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.error = "La base MySQL n'existe pas."
            else:
                self.error = err
            self.bdd = None
            self.bdd_cursor = None

        self.log = Log(self, config)
        self.atx = Atx(self, config)
        self.alias = Alias(self, self.basepath)
        self.budget = Budget(self, config)
        self.camera = Camera(self, config)
        self.courses = Courses(self, config)
        self.dis = Dis(self)
        self.disclaimer = Disclaimer(self)
        self.emprunt = Emprunt(self, self.bdd, self.bdd_cursor)
        self.historique = Historique(self, config, self.basepath)
        self.info = Info(self)
        self.jeu = Jeu(self)
        self.lumiere = Lumiere(self, config)
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

        self.nickserved = False
        self.last_added_link = ""

        # Init stream
        self.streamh = None
        self.oggfwd = None

    def add_rule(self, name, action, help_msg=""):
        name = name.lower()
        if name not in self.rules:
            self.rules[name] = {}
        self.rules[name]['action'] = action
        self.rules[name]['help'] = help_msg

    def on_welcome(self, serv, ev):
        """Upon server connection, handles nickserv"""
        serv.privmsg("nickserv", "identify "+config.password)
        serv.join(config.channel)

        self.connection.execute_delayed(random.randrange(3600, 84600),
                                        self.tchou_tchou, (serv,))
        self.connection.execute_every(3600, self.notifs_emprunts, (serv,))
        if self.error is not None:
            self.say(serv, self.error)
        serv.privmsg("nickserv", "identify ")

    def on_privmsg(self, serv, ev):
        """Handles queries"""
        if(ev.source.nick.lower() == 'nickserv' and
           "You are now identified" in ev.arguments[0]):
            self.nickserved = True
        elif(ev.arguments[0].strip().startswith("oui")):
            id = ev.arguments[0].replace("oui", "").strip()
            self.retour_priv(self, ev.source.nick, id)
        elif(config.authorized_queries == [] or
             ev.source.nick in config.authorized_queries):
            self.on_pubmsg(self, serv, ev)

    def on_pubmsg(self, serv, ev):
        """Handles the messages on the chan"""
        author = ev.source.nick
        raw_msg = ev.arguments[0]
        msg = raw_msg.strip()
        urls = re.findall("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                          msg.lower())
        # If found some urls in the message, handles them
        if len(urls) > 0:
            self.on_links(serv, author, urls)
        # If "perdu" or "jeu" or "game" or "42"  in the last message, do Jeu
        if "perdu" in msg or "jeu" in msg or "game" in msg or "42" in msg:
            self.jeu(serv)
        msg = msg.split(':', 1)
        if(msg[0].strip() == self.connection.get_nickname() and
           (config.authorized == [] or author in config.authorized)):
            msg = shlex.split(msg[1])
            msg[0] = msg[0].lower()
            self.historique.add(author, msg[0])
            if msg[0] in self.rules:
                try:
                    self.rules[msg[0]]['action'](serv, author, msg)
                except InvalidArgs:
                    if config.debug:
                        tools.warning("Debug : " + str(msg))
                    self.aide(serv, author, msg)
            else:
                self.ans(serv, author, "Je n'ai pas compris…")
        elif(msg[0].strip().lower() == "aziz" and
             (config.authorized == [] or author in config.authorized)):
            # Easter egg
            msg = shlex.split(msg[1])
            msg[0] = msg[0].lower()
            if msg[0] == "lumiere":
                self.historique.add(author, msg[0])
                try:
                    self.rules[msg[0]]['action'](serv, author, msg)
                except InvalidArgs:
                    if config.debug:
                        tools.warning("Debug : " + str(msg))
                    self.aide(serv, author, msg)
        self.log.add_cache(author, raw_msg)  # Log each line

    def on_links(self, serv, author, urls):
        """Stores links in the shaarli"""
        for url in set(urls):
            if url.startswith(config.shaarli_url):
                continue
            base_params = (("do", "api"), ("token", config.shaarli_token))
            r = requests.get(config.shaarli_url,
                             params=base_params + (("url", url),))
            if r.text != "" and len(r.json()) > 0:
                continue
            post = {"url": url,
                    "description": "Posté par "+author+".",
                    "private": 0}
            r = requests.post(config.shaarli_url,
                              params=base_params, data=post)
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

    def has_admin_rights(self, serv, author):
        """Checks that author is in admin users"""
        if len(config.admins) > 0 and author not in config.admins:
            self.ans(serv, author,
                     "Vous n'avez pas l'autorisation d'accéder à cette " +
                     "commande.")
            return False
        return True

    def aide(self, serv, author, args):
        """Prints help"""
        args = [i.lower() for i in args]
        self.ans(serv, author, config.desc + " Commandes disponibles :")
        if len(args) > 1 and args[0] == "aide":
            if args[1] in self.rules:
                self.say(serv, self.rules[args[1]]['help'])
            else:
                self.say(serv, "Je n'ai pas compris…")
        elif args[0] != "aide" and args[0] in self.rules:
            self.say(serv, self.rules[args[0]]['help'])
        else:
            for rule in sorted(self.rules):
                self.say(serv, self.rules[rule]['help'])

    def moderation(self, serv, author, args):
        """Handles message to moderate listing"""
        if len(config.admins) != 0 and author not in config.admins:
            self.ans(serv, author, "Vous n'avez pas les droits requis.")
            return
        if len(args) > 1:
            liste = args[1].split("@")[0]
            query = ("SELECT id, subject, author, liste FROM moderation " +
                     "WHERE liste=%s AND moderated=0 ORDER BY date DESC")
            values = (liste,)
            message = ("Messages en attente de modération " +
                       "pour la liste " + liste + " :")
        else:
            query = ("SELECT id, subject, author, liste FROM moderation " +
                     "WHERE moderated=0 ORDER BY date DESC")
            values = ()
            message = "Messages en attente de modération :"
        self.bdd_cursor.execute(query, values)
        if self.bdd_cursor.rowcount <= 0:
            self.ans(serv, author, "Aucun message en attente de modération.")
            return
        self.ans(serv, author, message)
        for (ident, subject, author, liste) in self.bdd_cursor:
            self.say(serv, "["+liste+"] : « "+subject+" » par "+author)

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
            assert(self.bdd_cursor is not None)
            self.bdd_cursor.execute(query, values)
        except AssertionError:
            if config.debug:
                tools.warning("Debug : Database disconnected")
            self.ans(serv, author,
                     "Impossible de rendre l'outil, " +
                     "base de données injoignable.")
            return
        except mysql.connector.errors.Error as err:
            if config.debug:
                tools.warning("Debug : " + str(err))
            self.ans(serv,
                     author,
                     "Impossible de rendre l'objet. (%s)" % (err,))
            return
        if self.bdd_cursor.rowcount > 0:
            self.ans(serv, author,
                     "Retour de "+args[1]+" enregistré.")
        else:
            self.ans(serv, author,
                     "Emprunt introuvable.")

    def retour_priv(self, author, id):
        """Handles end of borrowings with private answers to notifications"""
        query = ("UPDATE borrowings SET back=1 WHERE id=%s")
        values = (id,)
        try:
            assert(self.bdd_cursor is not None)
            self.bdd_cursor.execute(query, values)
        except AssertionError:
            if config.debug:
                tools.warning("Debug : Database disconnected")
            self.ans(serv, author,
                     "Impossible de rendre l'outil, " +
                     "base de données injoignable.")
            return
        except mysql.connector.errors.Error as err:
            if config.debug:
                tools.warning("Debug : " + str(err))
            self.ans(serv,
                     author,
                     "Impossible de rendre l'objet. (%s)" % (err,))
            return
        if self.bdd_cursor.rowcount > 0:
            self.privmsg(author,
                         "Retour de "+args[1]+" enregistré.")
        else:
            self.privmsg(author,
                         "Emprunt introuvable.")

    def notifs_emprunts(self, serv):
        """Notifications when borrowing is over"""
        now = datetime.datetime.now()
        delta = datetime.timedelta(hours=2)
        query = ("SELECT id, borrower, tool, date_from, until " +
                 "FROM borrowings WHERE ((until <= %s AND " +
                 "until - date_from <= %s) " + "OR until <= %s) AND back=0")
        try:
            assert(self.bdd_cursor is not None)
            self.bdd_cursor.execute(query,
                                    (now + delta, delta, now))
        except AssertionError:
            if config.debug:
                tools.warning("Debug : Database disconnected")
            self.say(serv,
                     "Impossible de récupérer les notifications d'emprunts.")
            return
        except mysql.connector.errors.Error as err:
            if config.debug:
                tools.warning("Debug : " + str(err))
            self.say(serv,
                     "Impossible de récupérer les notifications d'emprunts.")
            return
        for (id_field, borrower, tool, from_field, until) in self.bdd_cursor:
            notif = ("Tu as emprunté "+tool+" depuis le " +
                     datetime.strftime(from_field, "%d/%m/%Y") +
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
                             "Pour confirmer le retour, répond-moi " +
                             "\"oui " + id_field + "\" en query.")

    def lien(self, serv, author, args):
        """Handles links managements through Shaarli API"""
        base_params = (("do", "api"), ("token", config.shaarli_token))
        args[1] = args[1].lower()
        if len(args) > 1 and args[1] == "dernier":
            self.ans(serv, author, self.last_added_link)
            return

        if not self.has_admin_rights(serv, author):
            return

        def edit_link(search, private):
            r = requests.get(config.shaarli_url,
                             params=base_params + (search,))
            if r.status_code != requests.codes.ok or r.text == "":
                if private >= 0:
                    self.ans(serv, author,
                             "Impossible d'éditer le lien " +
                             search[1] + ". "
                             "Status code : "+str(r.status_code))
                else:
                    self.ans(serv, author,
                             "Impossible de supprimer le lien " +
                             search[1] + ". "
                             "Status code : "+str(r.status_code))
                return False
            key = r.json()['linkdate']
            if private >= 0:
                post = {"url": self.last_added_link, "private": private}
                r = requests.post(config.shaarli_url,
                                  params=base_params + (("key", key),),
                                  data=post)
            else:
                r = requests.delete(config.shaarli_url,
                                    params=base_params + (("key", key),))
            if r.status_code != 200:
                if private >= 0:
                    self.ans(serv, author,
                             "Impossible d'éditer le lien " +
                             search[1] + ". "
                             "Status code : "+str(r.status_code))
                else:
                    self.ans(serv, author,
                             "Impossible de supprimer le lien " +
                             search[1] + ". "
                             "Status code : "+str(r.status_code))
                return False

        if(len(args) > 1 and
           (args[1] in ["cache", "ignore", "affiche", "supprime"])):
            if args[1] == "cache" or args[1] == "ignore":
                msg = "Liens rendus privés."
                private = 1
            elif args[1] == "affiche":
                msg = "Liens rendus publics."
                private = 0
            else:
                msg = "Liens supprimés."
                private = -1
            ok = False
            if len(args) == 2:
                if edit_link(("url", self.last_added_link),
                             private) is not False:
                    ok = True
            else:
                for arg in args[2:]:
                    if arg.startswith(config.shaarli_url):
                        small_hash = arg.split('?')[-1]
                    else:
                        small_hash = arg
                    if(edit_link(("hash", small_hash), private) is not False
                       and ok is False):
                        ok = True
            if ok:
                self.ans(serv, author, msg)
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
        self.log.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
        print("Bye!")
        return not config.debug

if __name__ == '__main__':
    with JarvisBot() as bot:
        bot.start()
