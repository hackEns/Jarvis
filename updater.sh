#!/bin/sh

if [ "$#" -ne 1 ]
then
    echo "Argument manquant"
fi

cd $1

echo "Mise à jour"

if git pull
then
    echo "Mis à jour avec succès !"
else
    echo "Erreur durant la mise à jour"
fi

echo "Lancement de jarvis"
screen -r jarvis -p 0 -X stuff $1"/jarvis.py$(printf \\r)"

exit 0
