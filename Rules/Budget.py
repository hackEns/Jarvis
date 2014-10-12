import mysql.connector

from ._shared import *


class Budget(Rule):
    """Handles budget"""

    def __init__(self, bot):
        self.bot = bot

    def __call__(self, serv, author, args):
        """Handles budget"""
        if len(args) < 3:
            raise InvalidArgs

        try:
            amount = float(args[2].strip(" €"))
            first_index = 3
        except (KeyError, ValueError):
            try:
                amount = float(args[3].strip(" €"))
                if args[2] == "dépense":
                    amount = -amount
                first_index = 4
            except (KeyError, ValueError):
                raise InvalidArgs

        try:
            comment = args[first_index:]
            if comment[0].startswith("budget="):
                budget = comment[0].replace("budget=", '')
                del(comment[0])
            else:
                budget = ""
            comment = ' '.join(comment)
        except KeyError:
            comment = ""
            budget = ""

        if budget == "":
            # If no budget specified, put it in current year
            now = datetime.datetime.now()
            if now.month >= 9:
                budget = str(year) + " / " + str(year + 1)
            else:
                budget = str(year - 1) + " / " + str(year)

        if args[1] == "ajoute":
            if comment == "":
                raise InvalidArgs

            query = ("INSERT INTO budget(amount, author, date, comment, budget) " +
                     "VALUES(%s, %s, %s, %s, %s)")
            values = (amount, author, datetime.datetime.now(), comment, budget)
            try:
                assert(self.bot.bdd_cursor is not None)
                self.bot.bdd_cursor.execute(query, values)
            except AssertionError:
                self.bot.ans(serv, author,
                             "Impossible d'ajouter la facture, " +
                             "base de données injoignable.")
                return
            except mysql.connector.errors.Error as err:
                self.bot.ans(serv,
                             author,
                             "Impossible d'ajouter la facture. (%s)" % (err,))
                return
            self.bot.ans(serv, author, "Facture ajoutée.")

        elif args[1] == "retire":
            if budget != '':
                query = ("SELECT COUNT(*) as nb FROM budget WHERE amount=%s " +
                         "AND comment LIKE %s AND budget=%s")
                values = (amount, '%'+comment+'%', budget)
            else:
                query = ("SELECT COUNT(*) as nb FROM budget WHERE amount=%s " +
                         "AND comment LIKE %s")
                values = (amount, '%'+comment+'%')
            try:
                assert(self.bot.bdd_cursor is not None)
                self.bot.bdd_cursor.execute(query, values)
                row = self.bot.bdd_cursor.fetchone()
                if row[0] > 1:
                    self.bot.ans(serv, author,
                                 "Requêtes trop ambiguë. Plusieurs entrées " +
                                 "correspondent.")
                    return
                if budget != '':
                    query = ("DELETE FROM budget WHERE amount=%s AND " +
                             "comment LIKE %s AND budget=%s")
                else:
                    query = ("DELETE FROM budget WHERE amount=%s AND " +
                             "comment LIKE %s")
                self.bot.bdd_cursor.execute(query, values)
            except AssertionError:
                self.bot.ans(serv, author,
                             "Impossible de supprimer la facture, " +
                             "base de données injoignable.")
                return
            except mysql.connector.errors.Error as err:
                self.bot.ans(serv,
                             author,
                             "Impossible de supprimer la facture. (%s)" % (err,))
                return
            self.bot.ans(serv, author, "Facture retirée.")
        else:
            raise InvalidArgs

    def close(self):
        pass
