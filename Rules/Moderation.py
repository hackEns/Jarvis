from ._shared import *


class Moderation(Rule):
    """Handles message to moderate listing"""

    def __init__(self, bot):
        self.bot = bot

    def __call__(self, serv, author, args):
        """Handles message to moderate listing"""
        if not self.bot.has_admin_rights(serv, author):
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
        try:
            bdd = self.bot.mysql_connect(serv)
            assert(bdd is not None)
        except AssertionError:
            return

        bdd_cursor = bdd.cursor()
        bdd_cursor.execute(query, values)
        if bdd_cursor.rowcount <= 0:
            self.ans(serv,
                     author,
                     "Aucun message en attente de modération.")
            return
        self.ans(serv, author, message)
        for (ident, subject, author, liste) in bdd_cursor:
            self.say(serv, "["+liste+"] : « "+subject+" » par "+author)
        bdd_cursor.close()
        bdd.close()

    def close(self):
        pass
