import datetime
import re
import mysql
from ._shared import *


class Emprunt(Rule):
    """Handles tools borrowings"""

    def __init__(self, bot):
        self.bot = bot

    def padding(number):
        if number < 10:
            return "0"+str(number)
        else:
            return str(number)

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
                 "(borrower, tool, `date_from`, until, back)" +
                 "VALUES (%s, %s, %s, %s, %s)")
        values = (borrower, tool, datetime.datetime.now(), until, 0)
        try:
            bdd = self.bot.mysql_connect(serv)
            assert(bdd is not None)
        except AssertionError:
            return
        bdd_cursor = bdd.cursor()
        bdd_cursor.execute("SELECT COUNT(id) FROM borrowings " +
                           "WHERE back=0 AND borrower=%s AND tool=%s",
                           (borrower, tool))
        row = bdd_cursor.fetchone()
        if row[0] > 0:
            self.bot.ans(serv,
                         author,
                         "Il y a déjà un emprunt en cours, mise à jour.")
            query = ("UPDATE borrowings" +
                     "(id, borrower, tool, `date_from`, until, back)" +
                     "SET until=%s " +
                     "WHERE back=0 AND borrower=%s AND tool=%s")
            values = (until, borrower, tool)
        bdd_cursor.execute(query, values)
        bdd_cursor.close()
        bdd.close()

        self.bot.ans(serv, author,
                     "Emprunt de "+tool+" jusqu'au " +
                     self.padding(day) + "/" + self.padding(month) + " à " +
                     self.padding(hour) + "h noté.")

    def close(self):
        pass
