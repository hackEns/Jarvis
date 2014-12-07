#!/usr/bin/env python3

"""
This files provides a config management as a JSON file under ~/.config/jarvis/
folder.

See below for the default config options.
"""

import errno
import json
import os
import sys

from libjarvis import tools


def make_sure_path_exists(path):
    try:
        os.makedirs(path)
        return False
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise
        else:
            return True


class Config():
    def __init__(self, base_config_path="~/.config/jarvis/"):
        self.VERSION = "0.2"
        self.config_path = os.path.expanduser(base_config_path)
        self.config = {}
        self.load()

    def as_dict(self):
        return self.config

    def get(self, param):
        return self.config.get(param, False)

    def set(self, param, value):
        self.config[param] = value

    def initialize(self):
        # IRC parameters
        self.set("server", "")
        self.set("port", 6667)
        self.set("use_ssl", False)
        self.set("channel", "")
        self.set("nick", "Jarvis")
        self.set("desc", "Jarvis, au rapport !")
        # Nickserv pasword
        self.set("password", "")
        # Author of this bot, shown in version
        self.set("author", "hackEns")
        # pgsql params
        self.set("pgsql", {"user": "",
                           "password": "",
                           "host": "",
                           "database": ""})
        # Shaarli params
        self.set("shaarli_url", "")
        self.set("shaarli_token", "")
        # Stream parameters
        self.set("stream_server", "")
        self.set("stream_port", "")
        self.set("stream_pass", "")
        self.set("stream_mount", "")
        self.set("stream_name", "")
        self.set("stream_desc", "")
        self.set("stream_url", "")
        self.set("stream_genre", "")
        self.set("oggfwd_path", "")
        # Pins, uses BCM numbering
        self.set("pin1_cam", 18)  # To control the camera servo, PWM
        self.set("pin2_cam", 18)  # To control the second camera servo, PWM
        self.set("pin_atx", 4)  # To control the ATX status via green wire
        self.set("pin_atx_status", 17)  # 5V, to get ATX status
        # RX/TX path in the filesystem to communicate with LED
        self.set("pin_led", "")
        # Access control
        self.set("authorized", [])  # Restrict access to some users
        # Restrict queries access, list of nicks
        self.set("authorized_queries", None)
        # Declare admins, list of nicks
        self.set("admins", None)
        # Log
        self.set("log_cache_size", 200)
        self.set("log_save_buffer_size", 200)
        self.set("log_file", "data/jarvis.log")
        self.set("log_all_file", "data/jarvis.all.log")
        # Misc
        self.set("history_length", 1000)
        self.set("history_no_doublons", True)
        self.set("history_lines_to_show", 5)
        self.set("emails_sender", "user@example.org")
        self.set("debug", False)
        self.set("version", self.VERSION)
        # Imap for the moderation emails
        self.set("imap_server", "")
        self.set("imap_user", "")
        self.set("imap_password", "")
        self.save()

    def load(self):
        try:
            folder_exists = make_sure_path_exists(self.config_path)
            if(folder_exists and
               os.path.isfile(self.config_path + "config.json")):
                initialized = True
            else:
                initialized = False
        except OSError:
            tools.warning("Unable to create ~/.config folder.")
            sys.exit(1)
        if not initialized:
            self.initialize()
            tools.warning("Config initialized to its default values. " +
                          "Edit " + self.config_path + "config.json prior to "
                          "running jarvis again.")
            sys.exit()
        else:
            try:
                with open(self.config_path + "config.json", 'r') as fh:
                    self.config = json.load(fh)
            except (ValueError, IOError):
                tools.warning("Config file could not be read.")
                sys.exit(1)
        if self.get("version") != self.VERSION:
            self.set("version", self.VERSION)
            self.save()
            tools.warning("Updated Jarvis version to " + self.VERSION)

    def save(self):
        try:
            with open(self.config_path + "config.json", 'w') as fh:
                fh.write(json.dumps(self.config,
                                    sort_keys=True,
                                    indent=4,
                                    separators=(',', ': ')))
        except IOError:
            tools.warning("Could not write config file.")
            sys.exit(1)
