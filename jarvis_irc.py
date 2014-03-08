#!/usr/bin/env python3

import os
import random
import socket
import subprocess
import time
from collections import deque
from config import *


def add_history(string):
    global history

    history.append(string)
    while len(history) > 1000:
        history.popleft()
    return


def say(msg):
    irc.send(("PRIVMSG %s :%s\r\n" % (channel, msg)).encode())


def ans_nick(nick):
    return lambda msg: say("%s%s" % (nick, msg))


def main():
    global irc, server, channel, botnick, password
    global joined, identified, history
    global debug, basepath, oggfwd_path
    global stream_cave, oggfwd, leds
    global stream_server, stream_port, stream_pass, stream_mount, stream_name
    global stream_desc, stream_url, stream_genre

    devnull = subprocess.DEVNULL

    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Connecting to : "+server)
    irc.settimeout(250)
    irc.connect((server, 6667))
    irc.send(("USER " + botnick + " " + botnick + " " + botnick +
              " :Jarvis au rapport !\n").encode())
    irc.send(("NICK " + botnick + "\n").encode())

    while True:
        try:
            text = irc.recv(2040).decode()
        except Exception as e:
            err = e.args[0]
            if err == 'timed out':
                joined = False
                identified = False
                irc.close()
                time.sleep(1)
                break
            else:
                print(e)
                sys.exit(1)

        if text.find("ERROR :Closing Link:") != -1:
            joined = False
            identified = False
            irc.close()
            break

        if(text.find('MODE ' + botnick) != -1 and
           not joined and not identified):
            print("Identifying with NickServ")
            irc.send(("PRIVMSG NICKSERV " +
                      ":IDENTIFY %s\r\n" % (password)).encode())
            print("Joining " + channel)
            irc.send(("JOIN " + channel + "\n").encode())

        if text.find('End of /NAMES list') != -1:
            joined = True
            print(channel+" joined")

        if(text.find(':NickServ') != -1
           and text.find("NOTICE "+botnick+" :You are now identified") != -1):
            identified = True
            print("Successfully identified")

        if text.find('PING') != -1:
            irc.send(('PONG ' + text.split()[1] + '\r\n').encode())
            if debug:
                print("PING received, PONG sent")

        if text.find('PRIVMSG '+botnick) != -1:
            continue

        t = text.split("PRIVMSG " + channel + ":" + botnick + ':')
        if text.find('!') != -1:
            nick = text[1:text.index('!')]+": "
        else:
            nick = ''
        ans = ans_nick(nick)
        if len(t) > 1:
            prefix = (t[1].strip() + " ").upper().startswith
            if prefix('AIDE'):
                ans("Jarvis au rapport ! Commandes disponibles :")
                say(" jarvis: info")
                say(" jarvis: camera ANGLE, ANGLE entre 0 et 180")
                say(" jarvis: camera ALIAS")
                say(" jarvis: alias ALIAS, ALIAS = camera, more to come")
                say(" jarvis: lumiere R V B, R, V et B entre 0 et 255")
                say(" jarvis: led off/wtf/jarvis/strobo/…")
                say(" jarvis: dis \"qqchose\"")
                say(" jarvis: atx on/off")
                say(" jarvis: historique N, N=nombre de lignes, " +
                    "facultatif (défaut = 5)")
                say(" jarvis: citation")
                say(" jarvis: jeu")
                say(" jarvis: stream on/off")
                say(" jarvis: update")
            elif prefix('INFO '):
                ans("Quartier général en direct ici : " +
                    "http://ulminfo.fr:8080/hackave.ogg")
            elif prefix('CAMERA '):
                angle = (t[1].strip())[6:].strip()
                try:
                    angle_int = int(angle)
                    if angle_int < 0 or angle_int > 180:
                        raise ValueError
                    add_history("camera "+str(angle_int))
                    ret = subprocess.call([basepath+"/jarvis",
                                          "camera",
                                          str(angle_int)],
                                          stdout=devnull)
                    if ret == 0:
                        ans("Caméra réglée à %d°." % (angle_int,))
                    else:
                        ans("Je n'arrive pas à régler la caméra.")
                except ValueError:
                    try:
                        if angle == "":
                            raise ValueError
                        with open(basepath+"/data/camera.alias", 'r') as fh:
                            alias = fh.readlines()
                            for line in [i for i in alias if
                                         i.startswith(angle.upper)]:
                                angle_int = int((line.split(":"))[1].strip())
                                add_history("camera "+angle)
                                ret = subprocess.call([basepath+"/jarvis",
                                                       "camera",
                                                       str(angle_int)],
                                                      stdout=devnull)
                                if ret == 0:
                                    ans("Caméra réglée à %d°." % (angle_int,))
                                else:
                                    ans("Je n'arrive pas à régler la caméra.")
                    except:
                        ans("Usage : jarvis: camera ANGLE, " +
                            "ANGLE entre 0 et 180")
                        ans("Usage : jarvis: camera ALIAS")
            elif prefix('ALIAS '):
                alias = (t[1].strip())[5:].strip()
                try:
                    with open(basepath+"/"+alias+".alias", 'r') as fh:
                        ans("Liste des alias disponibles pour "+alias)
                        for line in fh.readlines():
                            say(line)
                except:
                    ans("Je ne connais pas cet alias : "+alias+".")
            elif prefix('LUMIERE '):
                t = (t[1].strip())[7:].split(" ")
                try:
                    if len(t) <= 3:
                        raise ValueError
                    R = int(t[1].strip())
                    V = int(t[2].strip())
                    B = int(t[3].strip())

                    if(R > 255 or R < 0 or
                       V > 255 or V < 0 or
                       B > 255 or B < 0):
                        raise ValueError
                    if leds is not None:
                        leds.terminate()
                    add_history("lumiere "+str(R)+" "+str(V)+" "+str(B))
                    ret = subprocess.call([basepath+"/jarvis",
                                          "lumiere",
                                          str(R), str(V), str(B)],
                                          stdout=devnull)
                    if ret == 0:
                        ans("Lumière réglée à (R,V,B) = " +
                            "(%d,%d,%d)." % (R, V, B))
                    else:
                        ans("Je n'arrive pas à régler la lumière.")
                except ValueError:
                    ans("Usage : jarvis: lumiere R V B, " +
                        "R, V et B entre 0 et 255")
            elif prefix('LED '):
                t = (t[1].strip())[3:].strip().upper()
                if t.startswith("OFF"):
                    add_history("led off")
                    if leds is not None:
                        leds.terminate()
                    subprocess.call([basepath+"/jarvis",
                                     "lumiere",
                                     str(R), str(V), str(B)],
                                    stdout=devnull)
                    ans("LEDs éteintes.")
                    continue

                scripts = [f.upper() for f in os.listdir('leds_wtf/') if
                           os.path.isfile(os.path.join('leds_wtf', f))]

                if t in scripts:
                    add_history("led "+t)
                    if leds is not None:
                        leds.terminate()
                    leds = subprocess.Popen([basepath +
                                             "/leds_wtf/led_"+t.lower()+".py"],
                                            stdout=devnull)
                    if leds is not None:
                        ans("LED passée en mode "+t+".")
                    else:
                        ans("Je ne peux pas passer la LED en mode "+t+".")
                else:
                    ans("Usage: jarvis: led wtf/jarvis/strobo")
            elif prefix('DIS '):
                t = t[1].strip()
                qqchose = t[3:].split("\"")
                if len(qqchose) > 2:
                    qqchose = qqchose[1].strip("\"")
                    add_history("dis "+qqchose)
                    ret = subprocess.call([basepath+"/jarvis", "dis", qqchose],
                                          stdout=devnull)
                    if ret == 0:
                        ans(""+qqchose+"")
                    else:
                        ans("Je n'arrive plus à parler…")
                else:
                    ans("Usage :  jarvis: dis \"qqchose\"")
            elif prefix('ATX '):
                t = t[1].strip()
                if t[3:].strip().upper().startswith("ON"):
                    add_history("atx on")
                    ret = subprocess.call([basepath+"/jarvis", "atx", "on"],
                                          stdout=devnull)
                    if ret == 0:
                        ans("ATX allumée.")
                    else:
                        ans("L'ATX est devenue incontrôlable !")
                elif t[3:].strip().upper().startswith("OFF"):
                    add_history("atx off")
                    ret = subprocess.call([basepath+"/jarvis", "atx", "off"],
                                          stdout=devnull)
                    if ret == 0:
                        ans("ATX éteinte.")
                    else:
                        ans("L'ATX est devenue incontrôlable !")
                else:
                    ans("Usage : jarvis: atx on/off")
            elif prefix("HISTORIQUE "):
                N = 5
                if not t[1].strip().upper().endswith("HISTORIQUE"):
                    try:
                        N = int((t[1].strip())[10:].strip())
                    except ValueError:
                        ans("Usage : jarvis: historique N, N=nombre de " +
                            "lignes, facultatif (défaut = 5)")
                        continue
                add_history("historique " + str(N))

                ans("Affichage des " + str(N) + " dernières lignes " +
                    "d'historique.")
                if len(history) < N+1:
                    ans("Il n'y a que " + str(len(history) - 1) + " lignes " +
                        "dans l'historique. Je les affiche maintenant :")
                for line in list(history)[-N-1:-1]:
                    say(line)
            elif prefix("CITATION "):
                try:
                    with open("data/citations", 'r') as fh:
                        citations = fh.readlines()
                        ans(""+citations[random.randrange(0,
                                                          len(citations))]+"")
                except:
                    ans("Je perds la mémoire…")
            elif prefix("JEU "):
                ans("J'ai perdu le jeu… (poke iXce)" +
                    "hbar, pi, 42, et tout le reste :) (poke cphyc)")
            elif prefix("DISCLAIMER "):
                ans("Jarvis est un bot doté de capacités dépassant à la " +
                    "fois l'entendement et les limites d'irc. Prenez donc " +
                    "garde a toujours rester poli avec lui car bien " +
                    "qu'aucune intention malsaine ne lui a été " +
                    "volontairement inculquée,")
                say("JARVIS IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY " +
                    "KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED " +
                    "TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A " +
                    "PARTICULAR PURPOSE AND NONINFRINGEMENT.")
            elif prefix("STREAM "):
                t = t[1].strip()
                if t[6:].strip().upper().startswith("ON"):
                    add_history("stream on")
                    if oggfwd is not None and stream_cave is not None:
                        ans("La retransmission est déjà opérationnelle.")
                        continue
                    if stream_cave is None:
                        stream_cave = subprocess.Popen([basepath +
                                                        "/stream_cave.py",
                                                        "/dev/video0"],
                                                       stdout=subprocess.PIPE)
                    if oggfwd is None:
                        oggfwd = subprocess.Popen([oggfwd_path + "/oggfwd",
                                                   stream_server,
                                                   stream_port,
                                                   stream_pass,
                                                   stream_mount,
                                                   "-n " + stream_name,
                                                   "-d " + stream_desc,
                                                   "-u " + stream_url,
                                                   "-g " + stream_genre],
                                                  stdin=stream_cave.stdout)
                    ans("Retransmission opérationnelle !")
                elif t[6:].strip().upper().startswith("OFF"):
                    add_history("stream off")
                    if stream_cave is not None:
                        stream_cave.terminate()
                        stream_cave = None
                    if oggfwd is not None:
                        oggfwd.terminate()
                        oggfwd = None
                    ans("Retransmission interrompue.")
                else:
                    ans("Usage : jarvis: stream on/off")
            elif prefix("LOG "):
                ans("wip…")
            elif prefix("UPDATE"):
                add_history("update")
                subprocess.Popen([basepath + "/updater.py", os.getpid()])
                ans("I will now update myself.")
                raise SystemExit
            else:
                ans("Je n'ai pas compris…")

        if(debug):
            print("RECEIVED (DEBUG): "+text)

basepath = os.path.dirname(__file__)
irc = None
stream_cave = subprocess.Popen([basepath + "/stream_cave.py",
                                "/dev/video0"],
                               stdout=subprocess.PIPE)
oggfwd = subprocess.Popen([oggfwd_path + "/oggfwd",
                           stream_server,
                           stream_port,
                           stream_pass,
                           stream_mount,
                           "-n " + stream_name,
                           "-d " + stream_desc,
                           "-u " + stream_url,
                           "-g " + stream_genre],
                          stdin=stream_cave.stdout)
print("Retransmission opérationnelle !")
leds = None

debug = True

joined = False
identified = False

history = deque([])

try:
    while True:
        main()
except:
    if irc is not None:
        irc.close()
    if stream_cave is not None:
        stream_cave.terminate()
    if oggfwd is not None:
        oggfwd.terminate()
    if leds is not None:
        leds.terminate()
    print("Jarvis est triste de devoir vous quitter…")
