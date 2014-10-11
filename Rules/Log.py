from collections import deque  # Fifo for log cache
from datetime import datetime

from ._shared import *


class Log(Rule):
    """Log interesting (or not) discussion on the chan"""

    def __init__(self, bot, config):
        self.config = config
        self.bot = bot
        self.log_cache = deque("", self.config.log_cache_size)
        self.log_save_buffer = ""
        self.log_save_buffer_count = 0

    def add_cache(self, author, msg):
        """
        Add line to log cache. If cache is full,
        last line is append to save buffer which
        is on its turn flushed to disk if full
        """
        if len(self.log_cache) >= self.config.log_cache_size:
            self.cache_to_buffer()
            if self.log_save_buffer_count > self.config.log_save_buffer_size:
                self.flush_buffer()

        self.log_cache.appendleft((datetime.now().hour,
                                   datetime.now().minute,
                                   author,
                                   msg))

    def cache_to_buffer(self):
        """Pop a line from log cache and append it to save buffer"""
        t = self.log_cache.pop()
        self.log_save_buffer += "%d:%d <%s> %s\n" % t
        self.log_save_buffer_count += 1

    def flush_buffer(self):
        """Flush log save buffer to disk"""
        with open(self.config.log_all_file, 'a') as f:
            f.write(self.log_save_buffer)
            self.log_save_buffer = ""
            self.log_save_buffer_count = 0

    def flush_all(self):
        """Flush the whole cache to the disk"""
        for i in range(len(self.log_cache)):
            self.cache_to_buffer()
        self.flush_buffer()

    def __call__(self, serv, author, args):
        """Handles logging"""
        if len(args) != 4 or args[2] != '...':
            raise InvalidArgs

        tmp = []
        start = args[1]
        end = args[3]
        found_end = False
        found_start = False
        for (h, m, auth, msg) in self.log_cache:
            end_index = msg.rfind(end)
            if not found_end and end_index >= 0:
                msg = msg[:end_index + len(end)]
                found_end = True
            if found_end:
                start_index = msg.find(start)
                if start_index >= 0:
                    msg = msg[start_index:]
                    tmp.append((h, m, auth, msg))
                    found_start = True
                    break
                tmp.append((h, m, auth, msg))

        if found_start:
            with open(self.config.log_file, 'a') as f:
                for i in range(len(tmp)):
                    f.write("%d:%d <%s> %s\n" % tmp.pop())
            self.bot.ans(serv, author, "Loggé !")
        else:
            self.bot.ans(serv, author, "Je n'ai pas trouvé")

    def close(self):
        self.flush_all()
