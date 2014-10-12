import mysql.connector

from ._shared import *


class Courses(Rule):
    """Handles shopping list"""

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config

    def __call__(self, serv, author, args):
        """Handles shopping list"""
        if len(args) < 3:
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
                assert(self.bot.bdd_cursor is not None)
                self.bot.bdd_cursor.execute(query, values)
                row = self.bot.bdd_cursor.fetchone()
                if row[0] > 0:
                    self.bot.ans(serv,
                                 author,
                                 "Item déjà présent dans la liste de courses")
                    return
                query = ("INSERT INTO shopping(item, author, comment, date, " +
                         "bought) VALUES(%s, %s, %s, %s, 0)")
                values = (args[2], author, comment, datetime.datetime.now())
                self.bot.bdd_cursor.execute(query, values)
            except AssertionError:
                self.bot.ans(serv, author,
                             "Impossible d'ajouter l'objet à la " +
                             "liste de courses, base de données injoignable.")
                return
            except mysql.connector.errors.Error as err:
                self.bot.ans(serv,
                             author,
                             "Impossible d'ajouter l'objet à la liste " +
                             "de courses. (%s)" % (err,))
                return
            self.bot.ans(serv, author, "Item ajouté à la liste de courses.")

        elif args[1] == "annuler":
            query = ("SELECT COUNT(*) as nb FROM shopping WHERE item=%s AND " +
                     "comment LIKE %s")
            values = (args[2], '%'+comment+'%')
            try:
                assert(self.bot.bdd_cursor is not None)
                self.bot.bdd_cursor.execute(query, values)
                row = self.bot.bdd_cursor.fetchone()
                if row[0] > 1:
                    self.bot.ans(serv, author,
                                 "Requêtes trop ambiguë. Plusieurs entrées " +
                                 "correspondent.")
                    return
                query = ("DELETE FROM shopping WHERE item=%s AND " +
                         "comment LIKE %s")
                self.bot.bdd_cursor.execute(query, values)
            except AssertionError:
                self.bot.ans(serv, author,
                             "Impossible de supprimer l'item, base de données " +
                             "injoignable.")
                return
            except mysql.connector.errors.Error as err:
                self.bot.ans(serv,
                             author,
                             "Impossible de supprimer l'item. (%s)" % (err,))
                return
            self.bot.ans(serv, author, "Item supprimé de la liste de courses.")

        elif args[1] == "acheté":
            query = ("SELECT COUNT(*) as nb FROM shopping WHERE item=%s AND " +
                     "comment LIKE %s AND bought=0")
            values = (args[2], '%'+comment+'%')
            try:
                assert(self.bot.bdd_cursor is not None)
                self.bot.bdd_cursor.execute(query, values)
                row = self.bot.bdd_cursor.fetchone()
                if row[0] > 1:
                    self.bot.ans(serv, author,
                                 "Requêtes trop ambiguë. Plusieurs entrées " +
                                 "correspondent.")
                    return
                query = ("UPDATE shopping SET bought=1 WHERE item=%s AND " +
                         "comment LIKE %s AND bought=0")
                self.bot.bdd_cursor.execute(query, values)
            except AssertionError:
                self.bot.ans(serv, author,
                             "Impossible de marquer l'item comme acheté, " +
                             "base de données injoignable.")
                return
            except mysql.connector.errors.Error as err:
                self.bot.ans(serv,
                             author,
                             "Impossible de marquer l'item comme " +
                             "acheté. (%s)" % (err,))
                return
            self.bot.ans(serv, author, "Item marqué comme acheté.")

        else:
            raise InvalidArgs

    def close(self):
        pass
