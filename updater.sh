#!/bin/sh

if [ "$#" -ne 1 ]
then
    echo "Argument manquant"
fi

cd $1

echo "Mise à jour"

if git pull updater
then
    echo "Mis à jour avec succès !"
else
    echo "Erreur durant la mise à jour"
fi

echo "Lancement de jarvis"
screen -S jarvis -p 0 -X stuff $1"/jarvis_bot.py$(printf \\r)"

exit 0
