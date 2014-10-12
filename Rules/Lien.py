from ._shared import *


class Lien(Rule):
    """Handles links managements through Shaarli API"""

    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.last_added_link = ""

    def edit_link(search, private):
        r = requests.get(self.config.shaarli_url,
                         params=base_params + (search,))
        if r.status_code != requests.codes.ok or r.text == "":
            if private >= 0:
                self.bot.ans(serv, author,
                             "Impossible d'éditer le lien " +
                             search[1] + ". "
                             "Status code : "+str(r.status_code))
            else:
                self.bot.ans(serv, author,
                             "Impossible de supprimer le lien " +
                             search[1] + ". "
                             "Status code : "+str(r.status_code))
            return False
        key = r.json()['linkdate']
        if private >= 0:
            post = {"url": self.last_added_link, "private": private}
            r = requests.post(self.config.shaarli_url,
                              params=base_params + (("key", key),),
                              data=post)
        else:
            r = requests.delete(self.config.shaarli_url,
                                params=base_params + (("key", key),))
        if r.status_code != 200:
            if private >= 0:
                self.bot.ans(serv, author,
                             "Impossible d'éditer le lien " +
                             search[1] + ". "
                             "Status code : "+str(r.status_code))
            else:
                self.bot.ans(serv, author,
                             "Impossible de supprimer le lien " +
                             search[1] + ". "
                             "Status code : "+str(r.status_code))
            return False

    def __call__(self, serv, author, args):
        """Handles links managements through Shaarli API"""
        base_params = (("do", "api"), ("token", self.config.shaarli_token))
        args[1] = args[1].lower()
        if len(args) > 1 and args[1] == "dernier":
            self.bot.ans(serv, author, self.last_added_link)
            return

        if not self.bot.has_admin_rights(serv, author):
            return

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
                if self.edit_link(("url", self.last_added_link),
                             private) is not False:
                    ok = True
            else:
                for arg in args[2:]:
                    if arg.startswith(config.shaarli_url):
                        small_hash = arg.split('?')[-1]
                    else:
                        small_hash = arg
                    if(self.edit_link(("hash", small_hash), private) is not False
                       and ok is False):
                        ok = True
            if ok:
                self.bot.ans(serv, author, msg)
        else:
            raise InvalidArgs

    def on_links(self, serv, author, urls):
        """Stores links in the shaarli"""
        for url in set(urls):
            if url.startswith(self.config.shaarli_url):
                continue
            base_params = (("do", "api"), ("token", self.config.shaarli_token))
            r = requests.get(self.config.shaarli_url,
                             params=base_params + (("url", url),))
            if r.text != "" and len(r.json()) > 0:
                continue
            post = {"url": url,
                    "description": "Posté par "+author+".",
                    "private": 0}
            r = requests.post(self.config.shaarli_url,
                              params=base_params, data=post)
            if r.status_code != 200 and r.status_code != 201:
                self.bot.ans(serv, author,
                             "Impossible d'ajouter le lien à shaarli. " +
                             "Status code : "+str(r.status_code))
            else:
                self.last_added_link = url

    def close(self):
        pass
