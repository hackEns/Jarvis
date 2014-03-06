#!/usr/bin/env python3

import os
import sys

import pygst
pygst.require("0.10")
import gst
import gobject
import glib
glib.threads_init()

pipeline_string = """v4l2src device=%s ! tee name=videoout ! queue leaky=1 ! \
        videorate ! video/x-raw-yuv,width=640,height=480,fps=24,\
        framerate=(fraction)24/1 ! queue leaky=1 ! textoverlay name=overlay \
        text="Welcome to the hackEns RepRap stream!\nControl center online" \
        shaded-background=true font-desc="Ubuntu Mono 11" deltay=15 ! \
        theoraenc quality=30 ! queue leaky=1 ! oggmux ! fdsink""" % sys.argv[1]


def on_message(bus, message):
    t = message.type
    #print >> sys.stderr,message
    if t == gst.MESSAGE_ERROR:
        err, debug = message.parse_error()
        print >> sys.stderr, "Error: %s" % err, debug
    elif t == gst.MESSAGE_WARNING:
        err, debug = message.parse_warning()
        print >> sys.stderr, "Warning: %s" % err, debug
    elif t == gst.MESSAGE_INFO:
        err, debug = message.parse_info()
        print >> sys.stderr, "Info: %s" % err, debug

pipeline = gst.parse_launch(pipeline_string)
overlay = pipeline.get_by_name("overlay")
pipeline.set_state(gst.STATE_PLAYING)
bus = pipeline.get_bus()
bus.add_signal_watch()
bus.connect("message", on_message)


def reformat_data(src):
    ret = ""
    printer_online = "L'imprimante est connectée" in src
    if printer_online:
        ret += "Imprimante connectée. "
    if "Chargé" in src:
        fname_start = src.find("Chargé") + len("Chargé ")
        fname_end = src.find(" Buse")
        if fname_end == -1:
            ret += "Objet %s chargé. " % src[fname_start:]
        else:
            ret += "Objet %s chargé. " % src[fname_start:fname_end]
    if "Buse" in src:
        temp_start = src.find("Buse")
        temp_end = src.find(" Impression")
        if temp_end == -1:
            ret += "\nTempératures : " + src[temp_start:] + " "
        else:
            ret += "\nTempératures : " + src[temp_start:temp_end] + " "
    if "Impression" in src:
        progress_start = src.find("Impression")
        if progress_start > -1:
            ret += "\n" + (src[progress_start:].replace(" | ETA", "\nETA")
                           .replace(" |  Z", " | Z"))
    return ret


def process_input(source, condition, overlay):
    if condition & glib.IO_IN:
        process_input.buffer += source.read()
        if "\n" in process_input.buffer:
            bits = process_input.buffer.split("\n")
            process_input.buffer = bits[-1]
            data = bits[-2]
            print >> sys.stderr, data
            data = reformat_data(data)
            print >> sys.stderr, data
            if overlay:
                overlay.set_property("text", data)
    if condition & glib.IO_HUP:
        openpipe()
        return False
    return True
process_input.buffer = ""


def openpipe():
    if openpipe.src:
        glib.source_remove(openpipe.src)
    openpipe.f = os.fdopen(os.open(os.path.expanduser("~/reprap_status"),
                                   os.O_RDONLY | os.O_NONBLOCK))
    openpipe.src = glib.io_add_watch(openpipe.f,
                                     glib.IO_IN | glib.IO_HUP | glib.IO_ERR,
                                     process_input,
                                     overlay)
openpipe.f = None
openpipe.src = None

#openpipe()

loop = gobject.MainLoop()
try:
    loop.run()
except KeyboardInterrupt:
    pass

pipeline.set_state(gst.STATE_NULL)
openpipe.f.close()
