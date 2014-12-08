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

exit 0
