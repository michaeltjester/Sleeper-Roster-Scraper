#!/bin/bash

#Delete file if it exists
rm -f '/var/home/mjblue/Documents/Sleeper Py/player_roster_info.csv'

# Install dependencies
pip install -r '/var/home/mjblue/Documents/Sleeper Py/requirements.txt'

python '/var/home/mjblue/Documents/Sleeper Py/Sleeper.py'

flatpak run org.libreoffice.LibreOffice --calc '/var/home/mjblue/Documents/Sleeper Py/player_roster_info.csv'