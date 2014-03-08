#!/usr/bin/env python3

import sys
import os
import signal
import subprocess

if len(sys.argv) < 2:
    print("Argument manquant")

print("Déconnexion de jarvis")
os.kill(sys.argv[1], signal.SIGTERM)

print("Mise à jour")
ret = subprocess.call(["git", "pull", "updater"])

if ret == 0:
    print("Mis à jour avec succès !")
else:
    print("Erreur durant la mise à jour")

print("Lancement de jarvis")
subprocess.Popen([os.path.dirname(__file__) + "/jarvis_irc.py"])

sys.exit()
