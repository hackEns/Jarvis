#!/usr/bin/env python

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
    try:
        while True:
                step = random.random() / (5*3)
                for h in range(100):
                        set_hsv(float(h) / 100, 1, 1)
                        time.sleep(step)
    except KeyboardInterrupt:
        pass
