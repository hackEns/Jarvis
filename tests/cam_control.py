#!/usr/bin/env python
# -*- coding: utf8 -*-

import os
import sys
import serial

path = "/dev/ttyACM1"

angle = int(sys.argv[1])
if angle < 0 or angle > 180:
    print "Angle invalide"
    raise SystemExit

os.system("stty -hup -F "+path)

try:
    ser = serial.Serial(path, 115200)
except:
    sys.exit("Erreur à l'ouverture du port série.")

towrite = chr(127+int(127*float(angle)/180))
ser.readline()
ser.write(towrite)
ser.flush()
print ser.readline().strip()
