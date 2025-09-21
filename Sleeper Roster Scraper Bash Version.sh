#!/bin/bash

#Delete file if it exists
rm -f '/var/home/mjblue/player_roster_info.csv'

# Define the URLs
url1="https://api.sleeper.app/v1/league/1258502970421563392/rosters"
url2="https://api.sleeper.app/v1/league/1252826095145713664/rosters"
url3="https://api.sleeper.app/v1/players/nfl"

# Define the owner ID
OWNER_ID="470333759997079552"

# Output CSV file
OUTPUT_FILE="player_roster_info.csv"

echo "Fetching roster data from both leagues..."

# Get player IDs from both leagues for the specific owner
LEAGUE1_PLAYERS=$(curl -s "$url1" | jq -r --arg owner "$OWNER_ID" '.[] | select(.owner_id == $owner) | .players[]?' 2>/dev/null)
LEAGUE2_PLAYERS=$(curl -s "$url2" | jq -r --arg owner "$OWNER_ID" '.[] | select(.owner_id == $owner) | .players[]?' 2>/dev/null)

# Concatenate and deduplicate player IDs
ALL_PLAYERS=$(echo -e "$LEAGUE1_PLAYERS\n$LEAGUE2_PLAYERS" | grep -v '^$' | sort -u)

# Check if we found any players
if [ -z "$ALL_PLAYERS" ]; then
    echo "No players found for owner ID: $OWNER_ID"
    exit 1
fi

echo "Found $(echo "$ALL_PLAYERS" | wc -l) unique players"
echo "Fetching NFL player data..."

# Fetch the NFL players data once
PLAYERS_DATA=$(curl -s "$url3")

# Create CSV header
echo "player_id,search_full_name,injury_body_part,injury_status,team,age,position,practice_description,years_exp,fantasy_positions,yahoo_id,rotoworld_id,stats_id" > "$OUTPUT_FILE"

echo "Processing player data and writing to CSV..."

# Process each player ID
while IFS= read -r player_id; do
    # Skip team defense entries (like "GB", "KC", etc.)
    if [[ ! "$player_id" =~ ^[0-9]+$ ]]; then
        echo "Skipping non-numeric player ID: $player_id"
        continue
    fi
    
    # Extract player information using jq
    PLAYER_INFO=$(echo "$PLAYERS_DATA" | jq -r --arg id "$player_id" '
        .[$id] as $player |
        if $player then
            [
                $id,
                ($player.search_full_name // ""),
				($player.team // ""),
                ($player.injury_body_part // ""),
                ($player.injury_status // ""),
                ($player.age // ""),
                ($player.position // ""),
                ($player.practice_description // ""),
                ($player.years_exp // ""),
                (if $player.fantasy_positions then ($player.fantasy_positions | join(";")) else "" end),
                ($player.yahoo_id // ""),
                ($player.rotoworld_id // ""),
                ($player.stats_id // "")
            ] | @csv
        else
            [$id, "", "", "", "", "", "", "", "", "", "", ""] | @csv
        end
    ')
    
    # Append to CSV file
    echo "$PLAYER_INFO" >> "$OUTPUT_FILE"
    
done <<< "$ALL_PLAYERS"

echo "Data written to: $OUTPUT_FILE"
echo "Total records: $(tail -n +2 "$OUTPUT_FILE" | wc -l)"

# Display first few rows for verification
echo ""
echo "First 5 rows of output:"
head -n 6 "$OUTPUT_FILE" | column -t -s ','

flatpak run org.libreoffice.LibreOffice --calc '/var/home/mjblue/player_roster_info.csv'