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

su jarvis

gpio export 1 out
gpio export 7 out

until ping -c 4 hackens.org > /dev/null 2>&1; do
    sleep 2
done

if ! nc -z localhost 3306; then
  # Open SSH tunnel for MySQL
  ssh -NfL 3306:localhost:3306 hackens@hackens.org &
fi

screen -dmS jarvis && screen -S jarvis -p 0 -X stuff "~/Jarvis/jarvis.py$(printf \\r)"