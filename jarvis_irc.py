#!/usr/bin/env python3

import socket
import random
import subprocess
import os
from collections import deque


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


server = "clipper.ens.fr"
channel = "#hackens"
botnick = "jarvis"
password = "***"
debug = True
devnull = subprocess.DEVNULL

joined = False
identified = False

basepath = os.path.dirname(__file__)
history = deque([])

while True:
    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Connecting to : "+server)
    irc.connect((server, 6667))
    irc.send(("USER " + botnick + " " + botnick + " " + botnick +
              " :Jarvis au rapport !\n").encode())
    irc.send(("NICK " + botnick + "\n").encode())

    while True:
        text = irc.recv(2040).decode()

        if text.find("ERROR :Closing Link:") != -1:
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

        t = text.split(botnick+':')
        if text.find('!') != -1:
            nick = text[1:text.index('!')]+": "
        else:
            nick = ''
        ans = ans_nick(nick)
        if len(t) > 1:
            prefix = t[1].strip().upper().startswith
            if prefix('AIDE'):
                ans("Jarvis au rapport ! Usage :")
                say(" jarvis: info")
                say(" jarvis: camera ANGLE, ANGLE entre 0 et 180")
                say(" jarvis: camera ALIAS")
                say(" jarvis: alias ALIAS, ALIAS = camera, more to come")
                say(" jarvis: lumiere R V B, R, V et B entre 0 et 255")
                say(" jarvis: led wtf/jarvis/strobo")
                say(" jarvis: dis \"qqchose\"")
                say(" jarvis: atx on/off")
                say(" jarvis: historique N, N=nombre de lignes, " +
                    "facultatif (défaut = 5)")
                say(" jarvis: citation")
                say(" jarvis: jeu")
            elif prefix('INFO'):
                ans("Quartier général en direct ici : " +
                    "http://ulminfo.fr:8080/hackave.ogg")
            elif prefix('CAMERA'):
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
                        with open(basepath+"/camera.alias", 'r') as fh:
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
            elif prefix('ALIAS'):
                alias = (t[1].strip())[5:].strip()
                try:
                    with open(basepath+"/"+alias+".alias", 'r') as fh:
                        ans("Liste des alias disponibles pour "+alias)
                        for line in fh.readlines():
                            say(line)
                except:
                    ans("Je ne connais pas cet alias : "+alias+".")
            elif prefix('LUMIERE'):
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
            elif prefix('LED'):
                t = (t[1].strip())[3:].strip().upper()
                if t in ["WTF", "JARVIS", "STROBO"]:
                    add_history("led "+t)
                    ret = subprocess.call([basepath +
                                          "/leds_wtf/led_"+t.lower()+".py"],
                                          stdout=devnull)
                    if ret == 0:
                        ans("LED passée en mode "+t+".")
                    else:
                        ans("Je ne peux pas passer la LED en mode "+t+".")
                else:
                    ans("Usage: jarvis: led wtf/jarvis/strobo")
            elif prefix('DIS'):
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
            elif prefix('ATX'):
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
            elif prefix("HISTORIQUE"):
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
            elif prefix("CITATION"):
                try:
                    with open("citations", 'r') as fh:
                        citations = fh.readlines()
                        ans(""+citations[random.randrange(0,
                                                          len(citations))]+"")
                except:
                    ans("Je perds la mémoire…")
            elif prefix("JEU"):
                ans("J'ai perdu le jeu… (poke iXce)" +
                    "hbar, pi, 42, et tout le reste :) (poke cphyc)")
            elif prefix("DISCLAIMER"):
                ans("Jarvis est un bot doté de capacités dépassant à la " +
                    "fois l'entendement et les limites d'irc. Prenez donc " +
                    "garde a toujours rester poli avec lui car bien " +
                    "qu'aucune intention malsaine ne lui a été " +
                    "volontairement inculquée,")
                say("JARVIS IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY " +
                    "KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED " +
                    "TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A " +
                    "PARTICULAR PURPOSE AND NONINFRINGEMENT.")

            elif prefix("LOG"):
                ans("wip...")
            else:
                ans("Je n'ai pas compris…")

        if(debug):
            print("RECEIVED (DEBUG): "+text)