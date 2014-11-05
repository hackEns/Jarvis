#!/usr/bin/env python3
import cgi
import datetime
import os
import re
import sys

from bottle import app, run, route, static_file

nb_colors = 37

if len(sys.argv) < 2:
    print("Usage: "+sys.argv[0]+" LOGFILE")
    sys.exit(1)

logfile = sys.argv[1]

msg = re.compile('^(\d\d)/(\d\d)/(\d\d\d\d) (\d\d):(\d\d) <(.*?)> (.*)$',)

script_path = os.path.dirname(os.path.realpath(sys.argv[0]))+'/'


def tuple_of_hue(hue):
    t = hue * 6.0
    if t < 1.0:
        return (1.0, t, 0.0)
    elif t < 2.0:
        return (2.0 - t, 1.0, 0.0)
    elif t < 3.0:
        return (0.0, 1.0, t - 2.0)
    elif t < 4.0:
        return (0.0, 4.0 - t, 1.0)
    elif t < 5.0:
        return (t - 4.0, 0.0, 1.0)
    else:
        return (1.0, 0.0, 6.0 - t)


def color_of_hue(hue):
    c = tuple_of_hue(hue)
    return int(((c[0] * 256 + c[1]) * 256 + c[2]) * 255)


def hex_of_color(c):
    return '#' + hex(c)[2:].zfill(6)


def hash_color(s, offset=0):
    return hex_of_color(color_of_hue(float((sum(s.encode("utf-8")) + offset) % nb_colors) / nb_colors))


colorize_table = {}


def colorize(pseudo):
    if pseudo not in colorize_table:
        c = hash_color(pseudo)
        # vals = list(colorize_table.values())
        colorize_table[pseudo] = c
    return '<span style="color:%s">%s</span>' % (colorize_table[pseudo], pseudo)


def format_time(t):
    short_time = t.strftime('%H:%M')
    long_time = t.strftime('%Y-%m-%d %H:%M')
    return '<div>%s</div><div class="longtime">%s</div>' % (short_time, long_time)


def format_msg(msg):
    msg = cgi.escape(msg)
    msg = re.sub('(https?://[^ ]*)', '<a href="\\1">\\1</a>', msg)
    return msg


def get_log():
    m = []
    with open(logfile, 'r') as f:
        for l in f.readlines():
            m.append(msg.search(l))
        return m


def write_log(logs_matchs):
    write_output = ""
    for m in [i for i in logs_matchs if i is not None]:
        t = datetime.datetime(int(m.group(3)),
                              int(m.group(2)),
                              int(m.group(1)),
                              int(m.group(4)),
                              int(m.group(5)))
        timestamp = t.timestamp()
        write_output += '<tr><td>%s</td><td>&lt;%s&gt;</td><td>%s</td></tr>' % (format_time(t), colorize(m.group(6)), format_msg(m.group(7)))
        write_output += "\n"
    return write_output


@route("/from/<get_from:int>/to/<get_to:int>", name="from_to", template="index")
def from_to(get_from, get_to):
    parsed_log = get_log()
    matching_log = []
    for m in parsed_log:
        t = datetime.datetime(int(m.group(3)),
                              int(m.group(2)),
                              int(m.group(1)),
                              int(m.group(4)),
                              int(m.group(5)))
        if t.timestamp() > get_from and t.timestamp() < get_to:
            matching_log.append(m)
    now = datetime.datetime.fromtimestamp((get_from + get_to) / 2)
    midnight = now.replace(hour=0, minute=0, second=0,
                           microsecond=0).timestamp()
    start_time_yesterday = midnight - 86400
    end_time_yesterday = midnight - 1
    start_time_tomorrow = midnight + 86400
    end_time_tomorrow = midnight + 2*86400 - 1
    return {"log": write_log(matching_log),
            "start_time_yesterday": int(start_time_yesterday),
            "end_time_yesterday": int(end_time_yesterday),
            "start_time_tomorrow": int(start_time_tomorrow),
            "end_time_tomorrow": int(end_time_tomorrow),
            "day": now.strftime("%d/%m/%Y")}


@route("/all", name="all", template="index")
def all():
    parsed_log = get_log()
    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0,
                           microsecond=0).timestamp()
    start_time_yesterday = midnight - 86400
    end_time_yesterday = midnight - 1
    start_time_tomorrow = midnight + 86400
    end_time_tomorrow = midnight + 2*86400 - 1
    return {"log": write_log(parsed_log),
            "start_time_yesterday": int(start_time_yesterday),
            "end_time_yesterday": int(end_time_yesterday),
            "start_time_tomorrow": int(start_time_tomorrow),
            "end_time_tomorrow": int(end_time_tomorrow),
            "day": now.strftime("%d/%m/%Y")}


@route("/", name="index", template="index")
def index():
    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0,
                           microsecond=0).timestamp()
    return from_to(midnight, midnight + 86400 - 1)


@route('/style.css')
def callback():
    return static_file('style.css', root='.')


if __name__ == "__main__":
    run(host="0.0.0.0", port=8081)
