#!/usr/bin/env python3

import requests
import csv
import json
import pandas as pd
from typing import List, Dict, Set, Optional
import sys
import argparse
from datetime import datetime

class SleeperRosterAnalyzer:
    def __init__(self, owner_id: str, output_file: str = "/var/home/mjblue/Documents/Sleeper Py/player_roster_info.csv"):
        self.owner_id = owner_id
        self.output_file = output_file
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Python-Sleeper-Analyzer/1.0'})
        
        # CSV field names
        self.fieldnames = [
            'player_id', 'search_full_name', 'injury_body_part', 'injury_status',
            'age', 'position', 'practice_description', 'years_exp',
            'fantasy_positions', 'yahoo_id', 'rotoworld_id', 'stats_id', 'team'
        ]
    
    def fetch_json(self, url: str) -> Dict:
        """Fetch JSON data from a URL with error handling."""
        try:
            print(f"Fetching data from: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from {url}: {e}")
            sys.exit(1)
    
    def get_player_ids_from_roster(self, roster_data: List[Dict]) -> tuple:
        """Extract player IDs and roster info for the owner."""
        all_players = []
        starters = []
        roster_info = {}
        
        for roster in roster_data:
            if roster.get('owner_id') == self.owner_id:
                players = roster.get('players', [])
                starter_list = roster.get('starters', [])
                
                # Filter out team defenses (non-numeric IDs)
                numeric_players = [p for p in players if str(p).isdigit()]
                numeric_starters = [p for p in starter_list if str(p).isdigit()]
                
                all_players.extend(numeric_players)
                starters.extend(numeric_starters)
                
                # Store roster metadata
                roster_info = {
                    'roster_id': roster.get('roster_id'),
                    'league_id': roster.get('league_id'),
                    'wins': roster.get('settings', {}).get('wins', 0),
                    'losses': roster.get('settings', {}).get('losses', 0),
                    'fpts': roster.get('settings', {}).get('fpts', 0)
                }
                
                break
        
        return all_players, starters, roster_info
    
    def get_player_info(self, player_data: Dict, player_id: str, is_starter: bool = False) -> Dict:
        """Extract specific player information fields."""
        player = player_data.get(str(player_id), {})
        
        # Handle fantasy_positions array
        fantasy_positions = player.get('fantasy_positions', [])
        fantasy_positions_str = ';'.join(fantasy_positions) if fantasy_positions else ''
        
        return {
            'player_id': player_id,
            'search_full_name': player.get('search_full_name', ''),
            'injury_body_part': player.get('injury_body_part') or '',
            'injury_status': player.get('injury_status') or '',
            'age': player.get('age') or '',
            'position': player.get('position', ''),
            'practice_description': player.get('practice_description') or '',
            'years_exp': player.get('years_exp') or '',
            'fantasy_positions': fantasy_positions_str,
            'yahoo_id': player.get('yahoo_id') or '',
            'rotoworld_id': player.get('rotoworld_id') or '',
            'stats_id': player.get('stats_id') or '',
            'team': player.get('team') or 'FA',
            'is_starter': is_starter
        }
    
    def analyze_rosters(self, league_urls: List[str]):
        """Main method to analyze rosters from multiple leagues."""
        print(f"Analyzing rosters for owner ID: {self.owner_id}")
        
        all_player_ids = set()
        all_starters = set()
        roster_summaries = []
        
        # Process each league
        for i, url in enumerate(league_urls, 1):
            print(f"\nProcessing League {i}...")
            roster_data = self.fetch_json(url)
            
            players, starters, roster_info = self.get_player_ids_from_roster(roster_data)
            
            if players:
                all_player_ids.update(players)
                all_starters.update(starters)
                roster_summaries.append(roster_info)
                print(f"  Found {len(players)} players ({len(starters)} starters)")
            else:
                print(f"  No roster found for owner in this league")
        
        if not all_player_ids:
            print(f"No players found for owner ID: {self.owner_id}")
            return
        
        print(f"\nTotal unique players across all leagues: {len(all_player_ids)}")
        print("Fetching NFL player data...")
        
        # Fetch NFL player data
        players_data = self.fetch_json("https://api.sleeper.app/v1/players/nfl")
        
        # Process and write data
        self.write_player_data(all_player_ids, all_starters, players_data)
        self.print_summary(roster_summaries)
    
    def write_player_data(self, player_ids: Set[str], starters: Set[str], players_data: Dict):
        """Write player data to CSV file."""
        print("Writing player data to CSV...")
        
        with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
            # Add is_starter to fieldnames
            fieldnames_with_starter = self.fieldnames + ['is_starter']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames_with_starter)
            writer.writeheader()
            
            # Sort players by starter status first, then by player_id
            sorted_players = sorted(player_ids, key=lambda x: (x not in starters, int(x)))
            
            for player_id in sorted_players:
                is_starter = player_id in starters
                player_info = self.get_player_info(players_data, player_id, is_starter)
                writer.writerow(player_info)
        
        print(f"Data written to: {self.output_file}")
    
    def print_summary(self, roster_summaries: List[Dict]):
        """Print summary information."""
        print(f"\n{'='*50}")
        print("ROSTER SUMMARY")
        print(f"{'='*50}")
        
        for i, roster in enumerate(roster_summaries, 1):
            print(f"League {i} - ID: {roster['league_id']}")
            print(f"  Roster ID: {roster['roster_id']}")
            print(f"  Record: {roster['wins']}-{roster['losses']}")
            print(f"  Fantasy Points: {roster['fpts']}")
            print()
        
        # Display sample of CSV
        print("Sample player data:")
        try:
            df = pd.read_csv(self.output_file)
            print(df.head()[['player_id', 'search_full_name', 'position', 'team', 'is_starter']].to_string(index=False))
        except ImportError:
            print("Install pandas for better formatted output: pip install pandas")
            with open(self.output_file, 'r') as f:
                for i, line in enumerate(f):
                    if i < 6:
                        print(line.strip())
                    else:
                        break

def main():
    parser = argparse.ArgumentParser(description='Analyze Sleeper fantasy football rosters')
    parser.add_argument('--owner-id', default="470333759997079552", 
                       help='Owner ID to analyze (default: 470333759997079552)')
    parser.add_argument('--output', default="/var/home/mjblue/Documents/Sleeper Py/player_roster_info.csv",
                       help='Output CSV filename (default: player_roster_info.csv)')
    
    args = parser.parse_args()
    
    # Define league URLs
    league_urls = [
        "https://api.sleeper.app/v1/league/1258502970421563392/rosters",
        "https://api.sleeper.app/v1/league/1252826095145713664/rosters"
    ]
    
    # Create analyzer and run
    analyzer = SleeperRosterAnalyzer(args.owner_id, args.output)
    analyzer.analyze_rosters(league_urls)

if __name__ == "__main__":
    main()