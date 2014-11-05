#!/usr/bin/env python3
import cgi
import datetime
import os
import re
import sys
import time

nb_colors = 37

if len(sys.argv) < 3:
    print("Usage: "+sys.argv[0]+" LOGFILE OUTPUT")
    sys.exit(1)

logfile = sys.argv[1]
output = sys.argv[2]

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


if __name__ == "__main__":
    write_output = ""
    with open(script_path+'begin.php', 'r') as begin:
        write_output = begin.read()+"\n"

    with open(logfile, 'r') as f:
        for l in f:
            m = msg.search(l)
            if m is not None:
                t = datetime.datetime(int(m.group(3)),
                                      int(m.group(2)),
                                      int(m.group(1)),
                                      int(m.group(4)),
                                      int(m.group(5)))
                timestamp = time.mktime(t.timetuple())
                write_output += '<?php if (%d < $max_time && %d >= $min_time) { ?>' % (timestamp, timestamp)
                write_output += "\n"
                write_output += '<tr><td>%s</td><td>&lt;%s&gt;</td><td>%s</td></tr>' % (format_time(t), colorize(m.group(6)), format_msg(m.group(7)))
                write_output += "\n"
                write_output += '<?php } ?>\n'

    with open(script_path+'end.php', 'r') as end:
        write_output += end.read()+"\n"

    with open(output, 'w') as fh:
        fh.write(write_output)
