import statsapi
import json

def simple_get_example(player_name, season=2024):
    """
    Simple example to explore available MLB API data for player splits
    """
    # Find the player ID
    player_search = statsapi.lookup_player(player_name)
    if not player_search:
        print(f"Player '{player_name}' not found")
        return
    
    player_id = player_search[0]['id']
    print(f"Found player: {player_name} (ID: {player_id})")
    
    # Try a variety of different endpoints and parameters to explore split data
    endpoints = [
        # Example 1: Basic person stats with hydration for split stats
        {
            "endpoint": "person",
            "params": {
                "personId": player_id,
                "hydrate": f"stats(group=hitting,type=vsLHP,season={season})"
            },
            "description": "Stats vs Left-handed pitchers"
        },
        
        # Example 2: Try another split type
        {
            "endpoint": "person",
            "params": {
                "personId": player_id,
                "hydrate": f"stats(group=hitting,type=vsRHP,season={season})"
            },
            "description": "Stats vs Right-handed pitchers"
        },
        
        # Example 3: Try home/away splits
        {
            "endpoint": "person",
            "params": {
                "personId": player_id,
                "hydrate": f"stats(group=hitting,type=homeAway,season={season})"
            },
            "description": "Home/Away splits"
        },
        
        # Example 4: Try using statSplits endpoint directly
        {
            "endpoint": "person_stats",
            "params": {
                "personId": player_id,
                "stats": "statSplits",
                "sportId": 1,
                "group": "hitting",
                "season": season
            },
            "description": "General stat splits endpoint"
        },
        
        # Example 5: Try with sitCodes parameter
        {
            "endpoint": "person_stats",
            "params": {
                "personId": player_id,
                "stats": "season",
                "sportId": 1,
                "group": "hitting",
                "season": season,
                "sitCodes": "h,a,vl,vr"  # home, away, vs lefty, vs righty
            },
            "description": "Using sitCodes parameter"
        }
    ]
    
    # Try each endpoint and print the raw results
    for example in endpoints:
        try:
            print(f"\n\n=== {example['description']} ===")
            print(f"Endpoint: {example['endpoint']}")
            print(f"Params: {example['params']}")
            
            result = statsapi.get(example['endpoint'], example['params'])
            
            # Print the raw result to see the structure
            print("\nResult structure:")
            print(json.dumps(result, indent=2)[:1000] + "...\n(truncated)")
            
            # Try to extract splits if they exist
            if 'people' in result and len(result['people']) > 0:
                if 'stats' in result['people'][0]:
                    print("\nFound these split types:")
                    for stats in result['people'][0]['stats']:
                        if 'type' in stats:
                            print(f"- {stats['type'].get('displayName', 'Unknown')}")
                        
                        if 'splits' in stats and len(stats['splits']) > 0:
                            print(f"  Found {len(stats['splits'])} splits")
                            
                            # Print the first split for reference
                            first_split = stats['splits'][0]
                            if 'split' in first_split:
                                print(f"  First split: {first_split['split'].get('description', 'Unknown')}")
                            
                            if 'stat' in first_split:
                                print("  Example stat keys:")
                                for key in list(first_split['stat'].keys())[:10]:  # First 10 keys
                                    print(f"  - {key}: {first_split['stat'][key]}")
        
        except Exception as e:
            print(f"Error with {example['description']}: {e}")
    
    # Also try to get available stat types from meta endpoint
    try:
        print("\n\n=== Available Stat Types ===")
        stat_types = statsapi.meta('statTypes')
        print(json.dumps(stat_types, indent=2))
    except Exception as e:
        print(f"Error getting stat types: {e}")

# Run the example
if __name__ == "__main__":
    simple_get_example("George Springer")