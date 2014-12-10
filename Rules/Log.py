from collections import deque  # Fifo for log cache
from datetime import datetime
import re

from ._shared import *


class LogIterator:
    def __init__(self, logfilename, cache=[]):
        self.cache = iter(cache)
        self.logline_parser = re.compile(r'^(?P<day>\d*)/(?P<month>\d*)/(?P<year>\d*) (?P<hour>\d*):(?P<minute>\d*) <(?P<author>.+?)> (?P<message>.*)$')
        logfile = []
        with open(logfilename, 'r') as f:
            for l in f.readlines()[::-1]:
                m = self.logline_parser.match(l)
                if m is not None:
                    d = m.groupdict()
                    logfile.append((int(d['day']), int(d['month']), int(d['year']), int(d['hour']), int(d['minute']), d['author'], d['message']))
        self.logfile = iter(logfile)
                

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return next(self.cache)
        except StopIteration:
            return next(self.logfile)
                



class Log(Rule):
    """Log interesting (or not) discussion on the chan"""

    def __init__(self, bot, config):
        self.config = config
        self.bot = bot
        self.log_cache = deque(maxlen=self.config.get("log_cache_size"))
        self.log_save_buffer = ""
        self.log_save_buffer_count = 0

    def add_cache(self, author, msg):
        """
        Add line to log cache. If cache is full,
        last line is append to save buffer which
        is on its turn flushed to disk if full
        """
        if len(self.log_cache) >= self.config.get("log_cache_size"):
            self.cache_to_buffer()
            save_buffer_size = self.config.get("log_save_buffer_size")
            if self.log_save_buffer_count > save_buffer_size:
                self.flush_buffer()

        self.log_cache.appendleft((datetime.now().day,
                                   datetime.now().month,
                                   datetime.now().year,
                                   datetime.now().hour,
                                   datetime.now().minute,
                                   author,
                                   msg))

    def cache_to_buffer(self):
        """Pop a line from log cache and append it to save buffer"""
        t = self.log_cache.pop()
        self.log_save_buffer += "%02d/%02d/%04d %02d:%02d <%s> %s\n" % t
        self.log_save_buffer_count += 1

    def flush_buffer(self):
        """Flush log save buffer to disk"""
        with open(self.config.get("log_all_file"), 'a') as f:
            f.write(self.log_save_buffer)
            self.log_save_buffer = ""
            self.log_save_buffer_count = 0

    def flush_all(self):
        """Flush the whole cache to the disk"""
        for i in range(len(self.log_cache)):
            self.cache_to_buffer()
        self.flush_buffer()

    def load_logfile(self, logfile):
        """Load cache object from file"""
        messages = []
        line_parser = re.compile(r'^(?P<day>\d*)/(?P<month>\d*)/(?P<year>\d*) (?P<hour>\d*):(?P<minute>\d*) <(?P<author>.+?)> (?P<message>.*)$')
        with open(logfile, 'r') as f:
            for line in f:
                m = line_parser.match(line)
                if m is not None:
                    d = m.groupdict()
                    messages.append((int(d['day']), int(d['month']), int(d['year']), int(d['hour']), int(d['minute']), d['author'], d['message']))
        return messages

    def __call__(self, serv, author, args):
        """Handles logging"""
        if len(args) < 4 or re.match('\\.\\.+', args[2]) is None:
            raise InvalidArgs

        tmp = []
        start = args[1]
        end = args[3]
        found_end = False
        found = False

        messages = LogIterator(self.config.get("log_all_file"), self.log_cache)

        for (d, mth, y, h, m, auth, msg) in messages:
            # Ignore messages that ping the bot
            if msg[:len(self.config.get("nick"))] == self.config.get("nick"):
                if found_end:
                    tmp.append((h, m, auth, msg))
                continue

            if not found_end:
                # Search end sentence
                if end in msg:
                    found_end = True

            if found_end:
                # Accumulate messages
                tmp.append((h, m, auth, msg))

                # Search start sentence
                if start in msg:
                    found = True
                    break


        if found:
            for i in range(len(tmp)):
                data = tmp.pop()
                quote.push(data)
                if end in data[3]: # Stop at first occurrence of end sentence
                    break

            # Write quote body
            body = ""
            for line in quote:
                body += "%d:%d <%s> %s\n" % line

            tags = [a[1:] for a in args[4:] if a[0] == "#"]
            tags.append("Logs")
            loglist = " ".join(tags)

            # Save to Shaarli
            base_params = (("do", "api"),
                           ("token", self.config.get("shaarli_token")))
            post = {"url": "",
                    "description": body,
                    "private": 1,
                    "tags": loglist}
            r = requests.post(self.config.get("shaarli_url"),
                              params=base_params, data=post)
            if r.status_code != 200 and r.status_code != 201:
                self.bot.ans(serv, author,
                             "Impossible d'ajouter le log à shaarli. " +
                             "Status code : " + str(r.status_code))


            self.bot.ans(serv, author, "Loggé !")
        else:
            self.bot.ans(serv, author, "Je n'ai pas trouvé")

    def close(self):
        self.flush_all()
