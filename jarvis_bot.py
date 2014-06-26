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

from Rules import *


class JarvisBot(ircbot.SingleServerIRCBot):
    def __init__(self):
        ircbot.SingleServerIRCBot.__init__(self, [(config.server,
                                                   config.port)],
                                           config.nick,
                                           config.desc)
        self.version_nb = "0.2"
        self.error = None
        self.basepath = os.path.dirname(os.path.realpath(__file__))+"/"
        self.leds = None
        self.current_leds = "off"

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

        self.log = Log(self, config)
        self.atx = Atx(self, config, jarvis_cmd)
        self.alias = Alias(self, config, self.basepath)
        self.camera = Camera(self, config, jarvis_cmd)
        self.dis = Dis(self, config, jarvis_cmd)
        self.disclaimer = Disclaimer(self, config)
        self.emprunt = Emprunt(self, config, self.bdd, self.bdd_cursor)
        self.historique = Historique(self, config, self.basepath)
        self.info = Info(self, config)

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
                      help_msg="budget (ajoute|retire) [dépense|crédit] "+
                      "montant [budget=BUDGET] commentaire")
        self.add_rule("camera",
                      self.camera,
                      help_msg="camera ALIAS|ANGLE")
        self.add_rule("courses",
                      self.courses,
                      help_msg="courses (acheter|annuler|acheté) item [comment]")
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
                                "(supprime|cache|affiche) [id|permalien] | "))
        self.add_rule("log",
                      self.log,
                      help_msg="log debut ... fin")
        self.add_rule("lumiere",
                      self.lumiere,
                      help_msg="lumiere (R G B)|script")
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
        """Upon server connection"""
        serv.privmsg("nickserv", "identify "+config.password)
        serv.join(config.channel)

        self.connection.execute_delayed(random.randrange(3600, 604800),
                                        self.tchou_tchou, (serv,))
        self.connection.execute_every(3600, self.notifs_emprunts, (serv,))
        if self.error is not None:
            self.say(serv, self.error)

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
        """Handles the queries on the chan"""
        author = ev.source.nick
        raw_msg = ev.arguments[0]
        msg = raw_msg.strip()
        urls = re.findall("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",
                          msg.lower())
        if len(urls) > 0:
            self.on_links(serv, author, urls)
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
                    self.aide(serv, author, msg)
            else:
                self.ans(serv, author, "Je n'ai pas compris…")
        self.log.add_cache(author, raw_msg)  # Log each line

    def on_links(self, serv, author, urls):
        """Stores links in the shaarli"""
        for url in set(urls):
            if url.startswith(config.shaarli_url):
                continue
            base_params = (("do", "api"), ("token", config.shaarli_key))
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

    def get_version(self):
        """Returns the bot version"""
        return (config.nick + "Bot version " +
                self.version_nb + " by " + config.author)

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
            self.say(serv, self.rules[args[1]]['help'])
        elif args[0] != "aide" and args[0] in self.rules:
            self.say(serv, self.rules[args[0]]['help'])
        else:
            for rule in sorted(self.rules):
                self.say(serv, self.rules[rule]['help'])

    def budget(self, serv, author, args):
        """Handles budget"""
        try:
            amount = float(args[2].strip(" €"))
        except (KeyError, ValueError):
            try:
                amount = float(args[3].strip(" €"))
                if args[2] == "dépense":
                    amount = -amount
            except (KeyError, ValueError):
                raise InvalidArgs
        try:
            comment = args[3:]
            if comment[0].startswith("budget="):
                budget = comment[0].replace("budget=", '')
                del(comment[0])
            else:
                budget = ""
            comment = ' '.join(comment)
        except KeyError:
            comment = ""
            budget = ""
        if args[1] == "ajoute":
            if comment == "":
                raise InvalidArgs
            query = ("INSERT INTO budget(id, amount, author, date, comment, budget) " +
                    "VALUES('', %s, %s, %s, %s, %s)")
            values = (amount, author, datetime.datetime.now(), comment, budget)
            try:
                assert(self.bdd_cursor is not None)
                self.bdd_cursor.execute(query, values)
                self.bdd.commit()
            except AssertionError:
                self.ans(serv, author,
                        "Impossible d'ajouter la facture, base de données " +
                        "injoignable.")
                return
            except mysql.connector.errors.Error as err:
                self.ans(serv,
                        author,
                        "Impossible d'ajouter la facture. (%s)" % (err,))
                return
        elif args[1] == "retire":
            if budget != '':
                query = ("SELECT COUNT(*) as nb FROM budget WHERE amount=%s AND "+
                         "comment LIKE '%%s%' AND budget=%s")
                values = (amount, comment, budget)
            else:
                query = ("SELECT COUNT(*) as nb FROM budget WHERE amount=%s AND "+
                         "comment LIKE '%%s%'")
                values = (amount, comment)
            try:
                assert(self.bdd_cursor is not None)
                self.bdd_cursor.execute(query, values)
                row = self.bdd_cursor.fetchone()
                if row[0] > 1:
                    self.ans(serv, author,
                             "Requêtes trop ambiguë. Plusieurs entrées " +
                             "correspondent.")
                    return
                if budget != '':
                    query = ("DELETE FROM budget WHERE amount=%s AND "+
                             "comment LIKE '%%s%' AND budget=%s")
                else:
                    query = ("DELETE FROM budget WHERE amount=%s AND "+
                             "comment LIKE '%%s%'")
                self.bdd_cursor.execute(query, values)
                self.bdd.commit()
            except AssertionError:
                self.ans(serv, author,
                        "Impossible de supprimer la facture, base de données " +
                        "injoignable.")
                return
            except mysql.connector.errors.Error as err:
                self.ans(serv,
                        author,
                        "Impossible de supprimer la facture. (%s)" % (err,))
                return
        else:
            raise InvalidArgs

    def courses(self, serv, author, args):
        """Handles shopping list"""
        if len(args) < 3:
            raise InvalidArgs
        try:
            comment = args[3:]
        except KeyError:
            comment = ""
        if args[1] == "acheter":
            if comment == "":
                raise InvalidArgs
            query = ("INSERT INTO shopping(id, item, author, comment, date, " +
                     "bought) VALUES('', %s, %s, %s, %s, 0)")
            values = (args[2], author, comment, datetime.datetime.now())
            try:
                assert(self.bdd_cursor is not None)
                self.bdd_cursor.execute(query, values)
                self.bdd.commit()
            except AssertionError:
                self.ans(serv, author,
                        "Impossible d'ajouter l'objet à la liste de courses, " +
                        "base de données injoignable.")
                return
            except mysql.connector.errors.Error as err:
                self.ans(serv,
                        author,
                        "Impossible d'ajouter l'objet à la liste de courses. (%s)" % (err,))
                return
        elif args[1] == "annuler":
            query = ("SELECT COUNT(*) as nb FROM shopping WHERE item=%s AND "+
                     "comment LIKE '%%s%'")
            values = (args[2], comment)
            try:
                assert(self.bdd_cursor is not None)
                self.bdd_cursor.execute(query, values)
                row = self.bdd_cursor.fetchone()
                if row[0] > 1:
                    self.ans(serv, author,
                             "Requêtes trop ambiguë. Plusieurs entrées " +
                             "correspondent.")
                    return
                query = ("DELETE FROM shopping WHERE item=%s AND "+
                         "comment LIKE '%%s%'")
                self.bdd_cursor.execute(query, values)
                self.bdd.commit()
            except AssertionError:
                self.ans(serv, author,
                        "Impossible de supprimer l'item, base de données " +
                        "injoignable.")
                return
            except mysql.connector.errors.Error as err:
                self.ans(serv,
                         author,
                         "Impossible de supprimer l'item. (%s)" % (err,))
                return
        elif args[1] == "acheté":
            query = ("SELECT COUNT(*) as nb FROM shopping WHERE item=%s AND "+
                     "comment LIKE '%%s%' AND bought=0")
            values = (args[2], comment)
            try:
                assert(self.bdd_cursor is not None)
                self.bdd_cursor.execute(query, values)
                row = self.bdd_cursor.fetchone()
                if row[0] > 1:
                    self.ans(serv, author,
                             "Requêtes trop ambiguë. Plusieurs entrées " +
                             "correspondent.")
                    return
                query = ("UPDATE shopping SET bought=1 WHERE item=%s AND "+
                         "comment LIKE '%%s%' AND bought=0")
                self.bdd_cursor.execute(query, values)
                self.bdd.commit()
            except AssertionError:
                self.ans(serv, author,
                         "Impossible de marquer l'item comme acheté, " +
                         "base de données injoignable.")
                return
            except mysql.connector.errors.Error as err:
                self.ans(serv,
                        author,
                        "Impossible de marquer l'item comme acheté. (%s)" % (err,))
                return
        else:
            raise InvalidArgs

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
                self.leds = subprocess.Popen(['python', script],
                                             stdout=subprocess.DEVNULL)
                self.current_leds = args[1]
        else:
            raise InvalidArgs

    def jeu(self, serv, author, args):
        """Handles game"""
        self.ans(serv, author, "J'ai perdu le jeu…")

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
        args = [i.lower() for i in args]
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

    def retour(self, serv, author, args):
        """Handles end of borrowings"""
        args = [i.lower() for i in args]
        if len(args) < 2:
            raise InvalidArgs
        if len(args) > 3:
            if re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$",
                        args[3]) is not None:
                borrower = args[3]
            else:
                raise InvalidArgs
        else:
            borrower = author
        query = ("UPDATE borrowings SET back=1 WHERE tool=%s AND borrower=%s")
        values = (args[1], borrower)
        self.bdd_cursor.execute(query, values)
        self.bdd.commit()
        if cursor.rowcount > 0:
            self.ans(serv, author,
                     "Emprunt de "+args[1]+" enregistré.")
        else:
            self.ans(serv, author,
                     "Emprunt introuvable.")

    def retour_priv(self, author, id):
        """Handles end of borrowings with private answers to notifications"""
        query = ("UPDATE borrowings SET back=1 WHERE id=%s")
        values = (id,)
        self.bdd_cursor.execute(query, values)
        self.bdd.commit()
        if cursor.rowcount > 0:
            self.privmsg(author,
                         "Emprunt de "+args[1]+" enregistré.")
        else:
            self.privmsg(author,
                         "Emprunt introuvable.")

    def notifs_emprunts(self, serv):
        """Notifications when borrowing is over"""
        now = datetime.datetime.now()
        delta = datetime.timedelta(hours=2)
        query = ("SELECT id, borrower, tool, date_from, until FROM borrowings " +
                 "WHERE ((until <= %s AND until - date_from <= %s) " +
                 "OR until <= %s) AND back=0")
        try:
            assert(self.bdd_cursor is not None)
            self.bdd_cursor.execute(query,
                                    (now + delta, delta, now))
        except (AssertionError, mysql.connector.errors.Error):
            serv.say(serv,
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
        base_params = (("do", "api"), ("token", config.shaarli_key))
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

        if len(args) > 1 and (args[1] in ["cache", "ignore", "affiche", "supprime"]):
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
