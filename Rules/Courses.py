from ._shared import *


class Courses(Rule):
    """Handles shopping list"""

    def __init__(self, bot):
        self.bot = bot

    def __call__(self, serv, author, args):
        """Handles shopping list"""
        if len(args) < 3:
            if len(args) == 1:
                query = ("SELECT item, author, date FROM shopping WHERE bought=0")
                try:
                    bdd = self.bot.mysql_connect(serv)
                    assert(bdd is not None)
                except AssertionError:
                    return
                bdd_cursor = bdd.cursor()
                bdd_cursor.execute(query)
                serv.privmsg(author, 'Voici la liste de courses (également consultable sur http://hackens.org/jarvis?do=courses)')
                for row in bdd_cursor:
                    serv.privmsg(author, '{0} (ajouté par {1} le {2})'.format(*row))
            else:
                raise InvalidArgs
        try:
            comment = " ".join(args[3:])
        except KeyError:
            comment = ""

        if args[1] == "acheter":
            query = ("SELECT COUNT(*) as nb FROM shopping WHERE item=%s AND " +
                     "comment LIKE %s")
            values = (args[2], '%'+comment+'%')
            try:
                bdd = self.bot.mysql_connect(serv)
                assert(bdd is not None)
            except AssertionError:
                return
            bdd_cursor = bdd.cursor()
            bdd_cursor.execute(query, values)
            row = bdd_cursor.fetchone()
            if row[0] > 0:
                self.bot.ans(serv,
                             author,
                             "Item déjà présent dans la liste de courses")
                return
            query = ("INSERT INTO shopping(item, author, comment, date, " +
                     "bought) VALUES(%s, %s, %s, %s, 0)")
            values = (args[2], author, comment, datetime.datetime.now())
            bdd_cursor.execute(query, values)
            self.bot.ans(serv, author, "Item ajouté à la liste de courses.")
            bdd_cursor.close()
            bdd.close()

        elif args[1] == "annuler":
            query = ("SELECT COUNT(*) as nb FROM shopping WHERE item=%s AND " +
                     "comment LIKE %s")
            values = (args[2], '%'+comment+'%')
            try:
                bdd = self.bot.mysql_connect(serv)
                assert(bdd is not None)
            except AssertionError:
                return
            bdd_cursor = bdd.cursor()
            bdd_cursor.execute(query, values)
            row = bdd_cursor.fetchone()
            if row[0] > 1:
                self.bot.ans(serv, author,
                             "Requêtes trop ambiguë. Plusieurs entrées " +
                             "correspondent.")
                return
            query = ("DELETE FROM shopping WHERE item=%s AND " +
                     "comment LIKE %s")
            bdd_cursor.execute(query, values)
            self.bot.ans(serv, author, "Item supprimé de la liste de courses.")
            bdd_cursor.close()
            bdd.close()

        elif args[1] == "acheté":
            query = ("SELECT COUNT(*) as nb FROM shopping WHERE item=%s AND " +
                     "comment LIKE %s AND bought=0")
            values = (args[2], '%'+comment+'%')
            try:
                bdd = self.bot.mysql_connect(serv)
                assert(bdd is not None)
            except AssertionError:
                return
            bdd_cursor = bdd.cursor()
            bdd_cursor.execute(query, values)
            row = bdd_cursor.fetchone()
            if row[0] > 1:
                self.bot.ans(serv, author,
                             "Requêtes trop ambiguë. Plusieurs entrées " +
                             "correspondent.")
                return
            query = ("UPDATE shopping SET bought=1 WHERE item=%s AND " +
                     "comment LIKE %s AND bought=0")
            bdd_cursor.execute(query, values)
            self.bot.ans(serv, author, "Item marqué comme acheté.")
            bdd_cursor.close()
            bdd.close()

        else:
            raise InvalidArgs

    def close(self):
        pass
