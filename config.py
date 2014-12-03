# IRC parameters
server = "irc.ulminfo.fr"
port = 6667
channel = "#yatest"
nick = "Yabot"
desc = "Yabot, pour vous servir."
author = "Élie"
password = ""

# SQL parameters
mysql = {
    "user": "test",
    "password": "",
    "host": "localhost",
    "database": "test",
    "raise_on_warnings": True
}

# Shaarli
shaarli_url = ""
shaarli_token = ""

# Stream parameters
stream_server = ""
stream_port = ""
stream_pass = ""
stream_mount = ""
stream_name = ""
stream_desc = ""
stream_url = ""
stream_genre = ""
oggfwd_path = "/usr/bin"

# Arduino parameters
cam_path = "/dev/ttyACM0"
atx_path = cam_path
lum_path = "/dev/ttyUSB0"

# Access control
authorized = []
admins = ['Elie']

# Log
log_cache_size = 200 # Number of lines that log instruction can access
log_save_buffer_size = 200 # Buffer size to save cache on disk
log_file = "jarvis.log"
log_all_file = "jarvis.all.log"

# Misc
history_length = 1000
history_no_doublons = True
history_lines_to_show = 5
debug = True
