#!/usr/bin/sh

until ping -c 4 hackens.org > /dev/null 2>&1; do
    sleep 2
done

screen -dmS jarvis && screen -S jarvis -p 0 -X stuff "~/Jarvis/jarvis_irc.py$(printf \\r)"
