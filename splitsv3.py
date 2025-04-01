import statsapi
import json
import requests
import pandas as pd

def get_player_complete_splits(player_name, season=2024):
    """
    Get player splits including home/away and vs LHP/RHP
    
    Parameters:
    - player_name (str): Player's name
    - season (int): Season to get stats for
    
    Returns:
    - dict: Dictionary with player's split statistics
    """
    # Find the player ID
    player_search = statsapi.lookup_player(player_name)
    if not player_search:
        print(f"Player '{player_name}' not found")
        return None
    
    player_id = player_search[0]['id']
    print(f"Getting splits for {player_name} (ID: {player_id})")
    
    # Dictionary to store all splits
    all_splits = {
        "player": {
            "name": player_name,
            "id": player_id
        },
        "season": season,
        "splits": {}
    }
    
    # 1. Get home/away splits
    print("\nGetting home/away splits...")
    homeaway_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=homeAndAway&group=hitting&season={season}"
    try:
        response = requests.get(homeaway_url)
        homeaway_data = response.json()
        
        if 'stats' in homeaway_data and len(homeaway_data['stats']) > 0:
            if 'splits' in homeaway_data['stats'][0]:
                splits = homeaway_data['stats'][0]['splits']
                for split in splits:
                    if 'split' in split and 'description' in split['split'] and 'stat' in split:
                        split_name = split['split']['description']
                        all_splits['splits'][split_name] = split['stat']
                        print(f"Found split: {split_name}")
                        print(f"  AVG: {split['stat'].get('avg', 'N/A')}")
                        print(f"  OPS: {split['stat'].get('ops', 'N/A')}")
    except Exception as e:
        print(f"Error getting home/away splits: {e}")
    
    # 2. Get vs RHP splits
    print("\nGetting vs RHP splits...")
    rhp_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=hitting&season={season}&oppPitcherHand=R"
    try:
        response = requests.get(rhp_url)
        rhp_data = response.json()
        
        if 'stats' in rhp_data and len(rhp_data['stats']) > 0:
            if 'splits' in rhp_data['stats'][0]:
                splits = rhp_data['stats'][0]['splits']
                if len(splits) > 0 and 'stat' in splits[0]:
                    all_splits['splits']["vs RHP"] = splits[0]['stat']
                    print(f"Found split: vs RHP")
                    print(f"  AVG: {splits[0]['stat'].get('avg', 'N/A')}")
                    print(f"  OPS: {splits[0]['stat'].get('ops', 'N/A')}")
    except Exception as e:
        print(f"Error getting vs RHP splits: {e}")
    
    # 3. Get vs LHP splits
    print("\nGetting vs LHP splits...")
    lhp_url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=hitting&season={season}&oppPitcherHand=L"
    try:
        response = requests.get(lhp_url)
        lhp_data = response.json()
        
        if 'stats' in lhp_data and len(lhp_data['stats']) > 0:
            if 'splits' in lhp_data['stats'][0]:
                splits = lhp_data['stats'][0]['splits']
                if len(splits) > 0 and 'stat' in splits[0]:
                    all_splits['splits']["vs LHP"] = splits[0]['stat']
                    print(f"Found split: vs LHP")
                    print(f"  AVG: {splits[0]['stat'].get('avg', 'N/A')}")
                    print(f"  OPS: {splits[0]['stat'].get('ops', 'N/A')}")
    except Exception as e:
        print(f"Error getting vs LHP splits: {e}")
    
    # 4. Get Baseball Savant data as a supplementary source
    print("\nGetting Baseball Savant data...")
    savant_url = f"https://baseballsavant.mlb.com/statcast_search/csv?hfPT=&hfAB=&hfGT=R%7C&hfPR=&hfZ=&stadium=&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea={season}%7C&hfSit=&player_type=batter&hfOuts=&opponent=&pitcher_throws=L&batter_stands=&hfSA=&game_date_gt=&game_date_lt=&hfInfield=&team=&position=&hfOutfield=&hfRO=&home_road=&hfFlag=&hfBBT=&metric_1=&hfInn=&min_pitches=0&min_results=0&group_by=name-stats&sort_col=xwoba&player_event_sort=api_p_release_speed&sort_order=desc&min_pas=0&player_id={player_id}"
    
    try:
        response = requests.get(savant_url)
        if response.status_code == 200:
            # Parse CSV data
            data = pd.read_csv(response.content)
            if not data.empty:
                # Store relevant stats
                all_splits['savant_vs_lhp'] = {
                    'ba': data['ba'].values[0] if 'ba' in data.columns else None,
                    'slg': data['slg'].values[0] if 'slg' in data.columns else None,
                    'obp': data['obp'].values[0] if 'obp' in data.columns else None,
                    'woba': data['woba'].values[0] if 'woba' in data.columns else None,
                    'singles': data['singles'].values[0] if 'singles' in data.columns else None,
                    'doubles': data['doubles'].values[0] if 'doubles' in data.columns else None,
                    'triples': data['triples'].values[0] if 'triples' in data.columns else None,
                    'hrs': data['hrs'].values[0] if 'hrs' in data.columns else None,
                }
                print("Found Baseball Savant data vs LHP")
    except Exception as e:
        print(f"Error getting Baseball Savant data vs LHP: {e}")
    
    # Also try vs RHP from Savant
    savant_rhp_url = f"https://baseballsavant.mlb.com/statcast_search/csv?hfPT=&hfAB=&hfGT=R%7C&hfPR=&hfZ=&stadium=&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea={season}%7C&hfSit=&player_type=batter&hfOuts=&opponent=&pitcher_throws=R&batter_stands=&hfSA=&game_date_gt=&game_date_lt=&hfInfield=&team=&position=&hfOutfield=&hfRO=&home_road=&hfFlag=&hfBBT=&metric_1=&hfInn=&min_pitches=0&min_results=0&group_by=name-stats&sort_col=xwoba&player_event_sort=api_p_release_speed&sort_order=desc&min_pas=0&player_id={player_id}"
    
    try:
        response = requests.get(savant_rhp_url)
        if response.status_code == 200:
            # Parse CSV data
            data = pd.read_csv(response.content)
            if not data.empty:
                # Store relevant stats
                all_splits['savant_vs_rhp'] = {
                    'ba': data['ba'].values[0] if 'ba' in data.columns else None,
                    'slg': data['slg'].values[0] if 'slg' in data.columns else None,
                    'obp': data['obp'].values[0] if 'obp' in data.columns else None,
                    'woba': data['woba'].values[0] if 'woba' in data.columns else None,
                    'singles': data['singles'].values[0] if 'singles' in data.columns else None,
                    'doubles': data['doubles'].values[0] if 'doubles' in data.columns else None,
                    'triples': data['triples'].values[0] if 'triples' in data.columns else None,
                    'hrs': data['hrs'].values[0] if 'hrs' in data.columns else None,
                }
                print("Found Baseball Savant data vs RHP")
    except Exception as e:
        print(f"Error getting Baseball Savant data vs RHP: {e}")
    
    # Save all collected splits to a file
    filename = f"{player_name.replace(' ', '_')}_complete_splits.json"
    with open(filename, "w") as f:
        json.dump(all_splits, f, indent=2)
    
    print(f"\nComplete splits data saved to {filename}")
    
    return all_splits

# Run the function
if __name__ == "__main__":
    get_player_complete_splits("Mookie Betts")