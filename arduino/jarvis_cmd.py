#!/usr/bin/env python3

import config
import os
import sys
import serial
import struct
import subprocess


def initSerial(path):
    os.system("stty -hup -F " + path)
    os.system("stty -hup -F " + path)
    return serial.Serial(path, 115200)


def send(ser, mode, msg):
    ser.readline()
    ser.write(chr(mode).encode("ascii"))
    ser.flush()
    print(ser.readline().decode().strip())
    ser.write(struct.pack("I", msg))
    ser.flush()
    print(ser.readline().decode().strip())


def camera(angle):
    if angle < 0 or angle > 180:
        print("L'angle doit être entre 0 et 180")
        return False

    towrite = int(127 + int(127 * float(angle) / 180))
    try:
        ser = initSerial(config.cam_path)
        send(ser, 1, towrite)
    except (serial.SerialTimeoutException,
            serial.SerialException):
        print("Impossible de régler la caméra.")
        return False


def lumiere(r, v, b):
    msg = [0x80]
    for c in [r, v, b]:
        if c < 0 or c > 255:
            print("La couleur doit être entre 0 et 255")
            return False
        else:
            msg.append(int(c / 2))

    try:
        ser = initSerial(config.lum_path)
        for j in msg:
            ser.write(struct.pack("I", j))
    except (serial.SerialTimeoutException,
            serial.SerialException):
        print("Impossible de régler la LED.")
        return False


def atx(etat):
    try:
        ser = initSerial(config.atx_path)
        send(ser, 2, etat)
    except (serial.SerialTimeoutException,
            serial.SerialException):
        print("Impossible de régler l'ATX.")
        return False


def dis(something):
    try:
        return subprocess.call(["espeak",
                                "-vfrench+m5",
                                "-p 5",
                                "-s 50",
                                "-a 200",
                                something])
    except FileNotFoundError:
        print("Impossible de parler : espeak n'est peut-être pas installé")
        return False


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: %s action ..." % (sys.argv[0], ))
        raise SystemExit

    mode = "camera"
    if sys.argv[1] == mode:
        if len(sys.argv) < 3:
            print("Usage: %s %s angle" % (sys.argv[0], mode))
            raise SystemExit
        else:
            camera(int(sys.argv[2]))
        exit(0)

    mode = "lumiere"
    if sys.argv[1] == mode:
        if len(sys.argv) < 5:
            print("Usage: %s %s rouge vert bleu" % (sys.argv[0], mode))
            raise SystemExit
        else:
            lumiere(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))

        exit(0)

    mode = "dis"
    if sys.argv[1] == mode:
        if len(sys.argv) != 3:
            print("Usage %s %s phrase" % (sys.argv[0], mode))
            raise SystemExit
        else:
            dis(sys.argv[2].strip('"'))
        exit(0)

    mode = "atx"
    if sys.argv[1] == mode:
        if len(sys.argv) < 3 or not sys.argv[2].upper() in ['ON', 'OFF']:
            print("Usage: %s %s ON|OFF" % (sys.argv[0], mode))
            raise SystemExit
        else:
            atx(1 if sys.argv[2].upper() == 'ON' else 0)
        exit(0)

    print("%s: Instruction inconnue : %s" % (sys.argv[0], sys.argv[1]))
    raise SystemExit
