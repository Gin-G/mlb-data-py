import statsapi

def parse_stats_table(data_string):
    lines = data_string.strip().splitlines()
    
    # Get the header line and find the starting positions of each column
    header = lines[0]
    
    # Find the starting positions of each column by looking at the header
    positions = [0]  # Start of 'Rank'
    for i in range(1, len(header)):
        if header[i-1] == ' ' and header[i] != ' ':
            positions.append(i)
    
    # Extract column names
    column_names = []
    for i in range(len(positions)):
        if i < len(positions) - 1:
            column_names.append(header[positions[i]:positions[i+1]].strip())
        else:
            column_names.append(header[positions[i]:].strip())
    
    # Parse the data rows
    result = []
    for line in lines[1:]:  # Skip the header
        if not line.strip():  # Skip empty lines
            continue
            
        row_data = {}
        for i in range(len(positions)):
            if i < len(positions) - 1:
                value = line[positions[i]:positions[i+1]].strip()
            else:
                value = line[positions[i]:].strip()
                
            # Try to convert to correct data type for rank and value
            if column_names[i] == 'Rank':
                try:
                    value = int(value)
                except ValueError:
                    pass  # Keep as string if conversion fails
            elif column_names[i] == 'Value':
                try:
                    value = float(value.replace('.', '0.').strip())
                except ValueError:
                    pass  # Keep as string if conversion fails
                    
            row_data[column_names[i]] = value
            
        result.append(row_data)
    
    return result

def get_player_id_by_name(player_name, season=None, game_type=None):
    """
    Get a player's ID from MLB StatsAPI based on their name.
    
    Parameters:
    - player_name (str): Full name of the player to search for
    - season (int, optional): Season to search in (e.g., 2023)
    - game_type (str, optional): Type of games to consider ('R' for regular season, 
                                'P' for postseason, 'W' for World Series, etc.)
    
    Returns:
    - int: Player ID if found
    - None: If no player is found
    - list: If multiple players match the name
    """
    
    # Create params dictionary based on provided optional arguments
    params = {}
    if season is not None:
        params['season'] = season
    if game_type is not None:
        params['gameType'] = game_type
    
    # If no parameters were provided, use an empty search
    if not params:
        # Search for player by name
        player_search = statsapi.lookup_player(player_name)
        if not player_search:
            return None
        elif len(player_search) == 1:
            return player_search[0]['id']
        else:
            # Return list of players with their IDs if multiple matches
            return [(p['fullName'], p['id']) for p in player_search]
    else:
        # Use the get method with provided parameters
        try:
            people = statsapi.get('sports_players', params)['people']
            matching_players = [p for p in people if p['fullName'].lower() == player_name.lower()]
            
            if not matching_players:
                return None
            elif len(matching_players) == 1:
                return matching_players[0]['id']
            else:
                return [(p['fullName'], p['id']) for p in matching_players]
        except Exception as e:
            print(f"Error searching for player: {e}")
            return None

#print(parse_stats_table(statsapi.league_leaders('battingAverage',statGroup='hitting',limit=25,season='2025')))

personId = get_player_id_by_name('Will Smith')

import json
json_data = json.dumps(statsapi.player_stat_data(personId, group="[hitting]", type="season", sportId=1), indent=2)
print(json_data)