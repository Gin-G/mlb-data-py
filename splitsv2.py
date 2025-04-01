import statsapi
import json

def get_player_splits(player_id, season=None):
    """
    Get player splits (vs LHP/RHP, home/away) using the MLB-StatsAPI module
    
    Parameters:
    - player_id (int): MLB player ID
    - season (int, optional): Season to get stats for (current season if None)
    
    Returns:
    - dict: Dictionary containing the player's splits
    """
    # Create params dictionary
    params = {"personId": player_id}
    if season:
        params["season"] = season
    
    # Get player stats data - we need to use the statsapi.player_stat_data function
    # This is a wrapper around the get() function that's specifically designed for player stats
    player_data = statsapi.player_stat_data(player_id, group="hitting", type="season", seasons=season)
    
    # Now let's get the split stats specifically
    # The key is to use the statsSplits endpoint
    split_types = ["vsRHP", "vsLHP", "homeAway"]
    
    splits_data = {}
    
    for split_type in split_types:
        # Get specific split stats
        split_params = {
            "personId": player_id,
            "stats": "season",
            "gameType": "R",  # Regular season games
            "group": "hitting",
            "splitTeamId": "",
            "sportId": 1,     # MLB
            "split": split_type,
        }
        
        if season:
            split_params["season"] = season
        
        try:
            # Use the 'person_stats' endpoint for split stats
            split_data = statsapi.get("person_stats", split_params)
            splits_data[split_type] = split_data
        except Exception as e:
            print(f"Error getting {split_type} splits: {e}")
    
    return splits_data

# Example usage with pretty printing
def print_player_splits(player_name, season=None):
    """Print splits for a given player"""
    # Find the player's ID
    player_search = statsapi.lookup_player(player_name)
    if not player_search:
        print(f"Player '{player_name}' not found")
        return
    
    player_id = player_search[0]['id']
    print(f"Getting splits for {player_name} (ID: {player_id})")
    
    # Get the splits
    splits = get_player_splits(player_id, season)
    
    # Pretty print the results
    for split_type, data in splits.items():
        print(f"\n{split_type} splits:")
        print(json.dumps(data, indent=2))
        
        # Extract and display the actual stat values if they exist
        if 'stats' in data and len(data['stats']) > 0:
            for stat_group in data['stats']:
                if 'splits' in stat_group and len(stat_group['splits']) > 0:
                    for split in stat_group['splits']:
                        if 'stat' in split:
                            print(f"\n{split.get('split', {}).get('description', 'Unknown')} stats:")
                            stat_values = split['stat']
                            # Print key batting stats
                            for key in ['avg', 'homeRuns', 'rbi', 'obp', 'slg', 'ops']:
                                if key in stat_values:
                                    print(f"  {key}: {stat_values[key]}")

# Run the example with George Springer
if __name__ == "__main__":
    print_player_splits("George Springer", season=2024)