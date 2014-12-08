import re
from ._shared import *


class Retour(Rule):
    """Handles tools borrowings"""

    def __init__(self, bot):
        self.bot = bot

    def query_retour(self, serv, author, id):
        """Handles end of borrowings with private answers to notifications"""
        query = ("UPDATE borrowings SET back=true WHERE id=%s")
        values = (id,)
        try:
            bdd = self.bot.pgsql_connect(serv)
            assert(bdd is not None)
        except AssertionError:
            return
        bdd_cursor = bdd.cursor()
        bdd_cursor.execute(query, values)
        if bdd_cursor.rowcount > 0:
            self.bot.privmsg(serv,
                             author,
                             "Retour de " + id + " enregistré.")
        else:
            self.bot.privmsg(serv,
                             author,
                             "Emprunt introuvable.")
        bdd_cursor.close()

    def __call__(self, serv, author, args):
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
        query = ("UPDATE borrowings SET back=true WHERE tool=%s AND borrower=%s")
        values = (args[1], borrower)
        try:
            bdd = self.bot.pgsql_connect(serv)
            assert(bdd is not None)
        except AssertionError:
            return
        bdd_cursor = bdd.cursor()
        bdd_cursor.execute(query, values)
        if bdd_cursor.rowcount > 0:
            self.bot.ans(serv, author,
                         "Retour de " + args[1] + " enregistré.")
        else:
            self.bot.ans(serv, author,
                         "Emprunt introuvable.")
        bdd_cursor.close()

    def close(self):
        pass
