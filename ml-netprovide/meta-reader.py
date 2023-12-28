import re
import subprocess
import time
import redis

r = redis.StrictRedis(host='localhost', port=6379, db=0)
album = ""
title = ""

def getMetadata():

    global album
    global title

    # Run the dbus-send command to get metadata
    dbus_command = "dbus-send --print-reply --system --dest=org.gnome.ShairportSync /org/gnome/ShairportSync org.freedesktop.DBus.Properties.Get string:org.gnome.ShairportSync.RemoteControl string:Metadata"
    result = subprocess.run(dbus_command, shell=True, capture_output=True, text=True)

    # Check if the command was successful
    if result.returncode == 0:
        # Extract the D-Bus output
        dbus_output = result.stdout

        # Define regular expression patterns to extract xesam:title and xesam:album values
        title_pattern = re.compile(r'string "xesam:title"\s+variant\s+string "(.*?)"')
        album_pattern = re.compile(r'string "xesam:album"\s+variant\s+string "(.*?)"')

        # Use the patterns to find matches in the D-Bus output
        title_match = title_pattern.search(dbus_output)
        album_match = album_pattern.search(dbus_output)

        # Check if matches are found and extract the values
        title_temp = title_match.group(1) if title_match else None
        album_temp = album_match.group(1) if album_match else None

        if title_temp != title:
            print("Title:", title_temp)
            r.publish('link:ml:transmit:meta:title', title_temp)
            title = title_temp
        
        if album_temp != album:
            print("Album:", album_temp)
            r.publish('link:ml:transmit:meta:album', album_temp)
            album = album_temp    
        
    else:
        print(f"Error running dbus-send: {result.stderr}")

while True:
    getMetadata()
    time.sleep(1)

