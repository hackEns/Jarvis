import datetime
from email.mime.text import MIMEText
import re
import smtplib
from ._shared import *


class Emprunt(Rule):
    """Handles tools borrowings"""

    def __init__(self, bot):
        self.bot = bot

    def padding(self, number):
        if number < 10:
            return "0" + str(number)
        else:
            return str(number)

    def notifs(self, serv):
        """Notifications when borrowing is over"""
        now = datetime.datetime.now()
        delta = datetime.timedelta(hours=2)
        query = ("SELECT id, borrower, tool, date_from, until " +
                 "FROM borrowings WHERE until <= %s AND back=false")
        try:
            bdd = self.bot.pgsql_connect(serv)
            assert(bdd is not None)
        except AssertionError:
            return
        bdd_cursor = bdd.cursor()
        bdd_cursor.execute(query,
                           (now + delta,))
        for (id_field, borrower, tool, from_field, until) in bdd_cursor:
            notif = ("Tu as emprunté " + tool + " depuis le " +
                     from_field.strftime("%d/%m/%Y") +
                     " et tu devais le " +
                     "rendre aujourd'hui. L'as-tu rendu ?")
            if re.match("^[a-zA-Z0-9._%-]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6}$",
                        borrower) is not None:
                notif = "Salut,\n\n" + notif
                notif += ("\n\nPour confirmer le retour, répond à cet e-mail" +
                          " ou connecte-toi sur IRC (#hackens) pour" +
                          " le confirmer directement à Jarvis.")
                msg = MIMEText(notif)
                msg["Subject"] = "Emprunt en hack'ave"
                msg["From"] = config.get("emails_sender")
                msg["to"] = borrower

                s = smtplib.SMTP('localhost')
                s.sendmail(config.get("emails_sender"),
                           [borrower],
                           msg.as_bytes())
            else:
                self.bot.privmsg(serv, borrower, notif)
                self.bot.privmsg(serv,
                                 borrower,
                                 "Pour confirmer le retour, répond-moi " +
                                 "\"oui " + str(id_field) + "\" en query.")
        bdd_cursor.close()

    def __call__(self, serv, author, args):
        """Handles tools borrowings"""
        args = [i.lower() for i in args]
        if len(args) < 3:
            raise InvalidArgs
        this_year = datetime.date.today().year
        tool = args[1]
        until = [i.strip() for i in args[2].replace('/', ' ').split(" ")]
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
        if month < datetime.date.today().month:
            year = this_year + 1
        else:
            year = this_year
        until = datetime.datetime(year, month, day, hour)
        query = ("INSERT INTO borrowings" +
                 "(borrower, tool, date_from, until, back)" +
                 "VALUES (%s, %s, %s, %s, false)")
        values = (borrower, tool, datetime.datetime.now(), until)
        try:
            bdd = self.bot.pgsql_connect(serv)
            assert(bdd is not None)
        except AssertionError:
            return
        bdd_cursor = bdd.cursor()
        bdd_cursor.execute("SELECT COUNT(id) FROM borrowings " +
                           "WHERE back=false AND borrower=%s AND tool=%s",
                           (borrower, tool))
        row = bdd_cursor.fetchone()
        if row[0] > 0:
            self.bot.ans(serv,
                         author,
                         "Il y a déjà un emprunt en cours, mise à jour.")
            query = ("UPDATE borrowings" +
                     "(id, borrower, tool, date_from, until, back)" +
                     "SET until=%s " +
                     "WHERE back=false AND borrower=%s AND tool=%s")
            values = (until, borrower, tool)
        bdd_cursor.execute(query, values)
        bdd_cursor.close()

        self.bot.ans(serv, author,
                     "Emprunt de " + tool + " jusqu'au " +
                     self.padding(day) + "/" + self.padding(month) + " à " +
                     self.padding(hour) + "h noté.")

    def close(self):
        pass
