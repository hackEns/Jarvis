#### BEGIN INIT INFO
# Provides: jarvis
# Required-Start:
# Required-Stop:
# Should-Start:
# Should-Stop:
# Default-Start: 1 2 3 4 5
# Default-Stop: 0 6
# Short-Description: Jarvis launcher
#### END INIT INFO

#!/bin/sh

if [[ "$USER" == "jarvis" ]]
then
  gpio export 1 out
  gpio export 7 out

  # On attend que l'internet soit fonctionnel
  until ping -c 4 hackens.org > /dev/null 2>&1; do
    sleep 2
  done

  # Mise en place du tunnel ssh
  autossh -NfL 5432:localhost:5432 hackens@hackens.org

  # On lance jarvis dans un screen
  screen -dmS jarvis
  # Jarvis lui-même
  screen -S jarvis -p 0 -X stuff "~/Jarvis/jarvis.py$(printf \\r)"
else
  su jarvis -c "$0"
fi
