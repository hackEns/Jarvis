
Jarvis
======

hackEns multifunction bot to handle most of our internal management.

## Installation

Jarvis can be easily installed on a Raspberry Pi, starting from an up-to-date Raspbian image.

1. Download and put the latest Raspbian image on a SD card.
2. Start the Raspberry Pi. Set it correctly running `sudo raspi-config` (enable camera and so on).
3. Clone Jarvis repo.
4. Run the scripts in `system/` folder to install the requirements.
6. Make sure your user is member of the `gpio` and `video` groups.
7. Jarvis does not automatically export the GPIO pins to prevent it from running as `root`. So you should `gpio export PIN out` for the pins you use (1 and 7 by defautl).
7. Run `jarvis.py` and follow the instructions to start Jarvis.

*Note :* Jarvis requires a MySQL database to be used, and a webserver to serve the web visualisation (repo [Jarvis web](https://github.com/hackEns/Jarvis_web)). As our webserver does not run on the Raspberry Pi, the above scripts do not include the setup for the webserver and the MySQL database. You should install and set them yourself. `system/jarvis.sql` contains all the necessary information to setup the database and tables.

`startup.sh` is a service to use to start Jarvis automatically (Debian).


## Files and folders

* `arduino/`
  * This folder contains some example arduino scripts to use an Arduino and a regular PC instead of the Raspberry Pi GPIO pins. They are just here for demo purpose and are no longer used. Thus, they may be unstable.
* `aziz.py` is our moderation script, to inform us of new emails waiting for moderation. It's basically a Jarvis plugin.
* `data` folder contains the scripts, aliases etc you put into Jarvis.
* `irclog` folder contains the script to convert the Jarvis log as a nice HTML page.
* `jarvis.all.log` (created by Jarvis) is the complete log of the watched channel.
* `jarvis.py` is the main script, which serves the bot.
* `jarvis_cmd.py` is a collection of functions to translate Jarvis actions to GPIO actions etc.
* `Rules` contains a set of scripts for the various Jarvis actions.
* `STL export` contains 3D models for our setup.
* `stream.py` is the script used to handle the cam streaming.
* `system` contains the scripts necessary to setup Jarvis.
* `updater.sh` is a bash script called to update jarvis.
