#!/usr/bin/env python
# -*- coding: utf8 -*-

import random
import time
import os
import sys
import colorsys
import serial

os.system("stty -hup -F /dev/ttyUSB0")

try:
	ser = serial.Serial("/dev/ttyUSB0", 115200)
except:
	sys.exit("Erreur à l'ouverture du port série.")

def set_rgb(r, g, b):
	global ser
	for j in [0x80, int(int(r)/2), int(int(g)/2), int(int(b)/2)]:
		ser.write(chr(j))

def set_hsv(h, s, v):
	r, g, b = colorsys.hsv_to_rgb(h, s, v)
	r = int(255 * r)
	g = int(255 * g)
	b = int(255 * b)
	set_rgb(r, g, b)

if __name__ == "__main__":
    fixed_color = tuple(sys.argv[3:6]) if len(sys.argv) > 3 else None
    rate = float(sys.argv[2]) if len(sys.argv) > 2 else None

    while True:
        if rate is None:
            step = random.random() * 0.01
        else:
            step = rate
        h = random.random()
        white = random.random() < 0.1
        s = 0 if white else 1
        for flashes in range(1):
            if fixed_color:
                set_rgb(*fixed_color)
            else:
                set_hsv(h, s, 1)
            time.sleep(step)
            set_hsv(h, 0, 0)
            time.sleep(step)
