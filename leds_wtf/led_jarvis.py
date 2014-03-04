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

while True:
	h = 0.66 + (random.random() - 0.5) / 20
	for step in range(10):
		#v = 3 * random.random() / 4 + 0.2
		v = random.random()
		if random.random() > 0.8:
			s = random.random() / 4 + 0.75
		set_hsv(h, 1, v)
		time.sleep(0.01)

#set_color(0, 0, 0)
