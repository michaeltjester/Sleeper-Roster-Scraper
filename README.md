# Sleeper-Roster-Scraper
Simple Python tool to scrape multiple rosters for an owner id and check player statuses across the rosters.  

Sleeper.py is the python script that will scrape rosters across multiple leagues. 

Changes you will have to make:
  1. Update the Owner ID where applicable
  2. Update the league urls
  3. update the desired filepaths

There is also a bash script version which will accomplish the same named Sleeper Roster Scraper Bash Version.

I've also included a bash launcher which will:
  1. Delete the existing csv file if it exists. (this path will need to be updated.)
  2. Verify and download the python dependencies.
  3. Launch the python script.
  4. Launch the csv file in Libreoffice. (your command for libreoffice and/or excel will likely differ)

For references on the Sleeper API visit https://docs.sleeper.com/
