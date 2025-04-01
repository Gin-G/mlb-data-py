import statsapi

def get_player_splits(player_id, season=None, split_type=None):
    """
    Get a player's split statistics (vs LHP/RHP, home/away, etc.)
    
    Parameters:
    - player_id (int): MLB player ID
    - season (int, optional): Season to get splits for (current season if None)
    - split_type (str, optional): Type of split to return (e.g. 'vsBatter', 'vsLHP', 'vsRHP', 'home', 'away')
                                 If None, returns all available splits
    
    Returns:
    - dict: Player's split statistics
    """
    # Define the params object
    params = {
        "personId": player_id,
        "hydrate": "stats(group=[hitting,pitching],type=[bySplits],sportId=1)"
    }
    
    # Add season parameter if provided
    if season:
        params["season"] = season
    
    # Get the data from the API
    player_data = statsapi.get("person", params)
    
    # Extract splits data
    splits_data = {}
    
    if 'people' in player_data and len(player_data['people']) > 0:
        person = player_data['people'][0]
        if 'stats' in person:
            for stat_group in person['stats']:
                if 'splits' in stat_group:
                    for split in stat_group['splits']:
                        # Check if this is a split we're interested in
                        if split.get('split') and split.get('split').get('description'):
                            split_name = split['split']['description']
                            
                            # If a specific split_type was requested, filter for it
                            if split_type and split_type.lower() not in split_name.lower():
                                continue
                                
                            # Store the split data
                            if split_name not in splits_data:
                                splits_data[split_name] = {}
                            
                            # Add all statistics from this split
                            if 'stat' in split:
                                group_type = stat_group.get('group', {}).get('displayName', 'unknown')
                                if group_type not in splits_data[split_name]:
                                    splits_data[split_name][group_type] = {}
                                
                                for key, value in split['stat'].items():
                                    splits_data[split_name][group_type][key] = value
    
    return splits_data

# Example usage
def print_player_splits_example(player_name, season=None):
    """Print example splits for a given player"""
    # Find the player's ID
    player_search = statsapi.lookup_player(player_name)
    if not player_search:
        print(f"Player '{player_name}' not found")
        return
    
    player_id = player_search[0]['id']
    print(f"Getting splits for {player_name} (ID: {player_id})")
    
    # Get the splits
    splits = get_player_splits(player_id, season)
    
    # Print some example splits
    for split_name, split_data in splits.items():
        if "vs LHP" in split_name or "vs RHP" in split_name or "Home" in split_name or "Away" in split_name:
            print(f"\n{split_name}:")
            for group_name, stats in split_data.items():
                print(f"  {group_name} stats:")
                for key in ['avg', 'homeRuns', 'rbi', 'obp', 'slg', 'ops']:
                    if key in stats:
                        print(f"    {key}: {stats[key]}")

print_player_splits_example('George Springer', season=2025)