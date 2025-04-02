from io import StringIO
import pandas as pd
import requests
import statsapi
import json
import os
from datetime import datetime

def get_player_id(player_name):
    """
    Get the player ID from MLB StatsAPI based on the player's name.
    
    Parameters:
    - player_name (str): Full name of the player to search for
    
    Returns:
    - int: Player ID if found, None otherwise
    """
    player_search = statsapi.lookup_player(player_name)
    if not player_search:
        print(f"Player '{player_name}' not found")
        return None
    
    player_id = player_search[0]['id']
    print(f"Found player: {player_name} (ID: {player_id})")
    
    return player_id

def get_baseball_savant_data(player_id, season, parameter_name, parameter_value):
    """
    Generic function to get data from Baseball Savant with specified parameters
    
    Parameters:
    - player_id (int): MLB player ID
    - season (int): Season year
    - parameter_name (str): Name of the parameter to set (e.g., 'pitcher_throws', 'home_road')
    - parameter_value (str): Value for the parameter (e.g., 'R', 'L', 'Home', 'Road')
    
    Returns:
    - dict: Formatted stats or None if error
    """
    try:
        print(f"\nGetting {parameter_name}={parameter_value} data for {season}...")
        
        # Build the URL with the appropriate parameter
        params = {}
        if parameter_name == 'pitcher_throws':
            params['pitcher_throws'] = parameter_value
            split_name = f"vs {parameter_value}HP"
        elif parameter_name == 'home_road':
            params['home_road'] = parameter_value
            split_name = parameter_value if parameter_value == 'Home' else 'Away'
        
        # Format the URL
        param_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        savant_url = f"https://baseballsavant.mlb.com/statcast_search/csv?hfPT=&hfAB=&hfGT=R%7C&hfPR=&hfZ=&stadium=&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea={season}%7C&hfSit=&player_type=batter&hfOuts=&opponent=&{param_string}&batter_stands=&hfSA=&game_date_gt=&game_date_lt=&hfInfield=&team=&position=&hfOutfield=&hfRO=&hfFlag=&hfBBT=&metric_1=&hfInn=&min_pitches=0&min_results=0&group_by=name-stats&sort_col=xwoba&player_event_sort=api_p_release_speed&sort_order=desc&min_pas=0&player_id={player_id}"
        
        response = requests.get(savant_url)
        
        if response.status_code == 200:
            data = pd.read_csv(StringIO(response.text))
            if not data.empty:
                # Check if required columns exist
                required_columns = ['ba', 'slg', 'obp', 'hrs', 'singles', 'doubles', 'triples', 'so', 'bb', 'abs', 'pa']
                missing_columns = [col for col in required_columns if col not in data.columns]
                
                if missing_columns:
                    print(f"Warning: Missing columns in {split_name} data: {missing_columns}")
                    print(f"Available columns: {list(data.columns)}")
                    return None
                else:
                    # Map to more standard keys
                    stats = {
                        'avg': str(data['ba'].values[0]),
                        'slg': str(data['slg'].values[0]),
                        'obp': str(data['obp'].values[0]),
                        'ops': str(float(data['obp'].values[0]) + float(data['slg'].values[0])),  # Calculate OPS
                        'homeRuns': int(data['hrs'].values[0]),
                        'singles': int(data['singles'].values[0]),
                        'doubles': int(data['doubles'].values[0]),
                        'triples': int(data['triples'].values[0]),
                        'strikeOuts': int(data['so'].values[0]),
                        'baseOnBalls': int(data['bb'].values[0]),
                        'atBats': int(data['abs'].values[0]),
                        'plateAppearances': int(data['pa'].values[0]),
                        'lastUpdated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    print(f"Found {split_name} data")
                    print(f"  AVG: {stats['avg']}")
                    print(f"  OPS: {stats['ops']}")
                    print(f"  HR: {stats['homeRuns']}")
                    
                    return stats
            else:
                print(f"No data found for {split_name}")
                return None
        else:
            print(f"Error: Status code {response.status_code}")
            return None
    except Exception as e:
        print(f"Error getting {parameter_name}={parameter_value} data: {e}")
        return None

def get_combined_split_data(player_id, season, params):
    """
    Get player data with multiple combined split parameters
    
    Parameters:
    - player_id (int): MLB player ID
    - season (int): Season year
    - params (dict): Dictionary of parameters to apply (e.g., {'home_road': 'Home', 'pitcher_throws': 'L', 'pitch_type': 'FF'})
    
    Returns:
    - dict: Performance data for the combined splits
    """
    # Build a description of the split combination
    split_descriptions = []
    if 'home_road' in params:
        split_descriptions.append(params['home_road'])
    if 'pitcher_throws' in params:
        split_descriptions.append(f"vs {params['pitcher_throws']}HP")
    if 'pitch_type' in params:
        pitch_types = {
            "FF": "Fastball (4-seam)",
            "SI": "Sinker (2-Seam)",
            "FC": "Cutter",
            "CH": "Changeup",
            "FS": "Split-finger",
            "FO": "Forkball",
            "SC": "Screwball",
            "CU": "Curveball",
            "KC": "Knuckle Curve",
            "CS": "Slow Curve",
            "SL": "Slider",
            "ST": "Sweeper",
            "SV": "Slurve",
            "KN": "Knuckleball",
            "EP": "Eephus",
            "FA": "Other",
            "IN": "Intentional Ball",
            "PO": "Pitchout"
        }
        pitch_name = pitch_types.get(params['pitch_type'], params['pitch_type'])
        split_descriptions.append(f"on {pitch_name}")
    
    split_name = " ".join(split_descriptions)
    print(f"\nGetting combined split data: {split_name} in {season}...")
    
    # Build URL parameters
    url_params = []
    
    # Add pitch type parameter if provided
    if 'pitch_type' in params:
        url_params.append(f"hfPT={params['pitch_type']}%7C")
    else:
        url_params.append("hfPT=")
    
    # Add other parameters
    for param_name, param_value in params.items():
        if param_name == 'pitch_type':
            continue  # Already handled above
        elif param_name == 'home_road':
            url_params.append(f"home_road={param_value}")
        elif param_name == 'pitcher_throws':
            url_params.append(f"pitcher_throws={param_value}")
    
    # Format the URL
    param_string = '&'.join(url_params)
    savant_url = f"https://baseballsavant.mlb.com/statcast_search/csv?{param_string}&hfAB=&hfGT=R%7C&hfPR=&hfZ=&stadium=&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea={season}%7C&hfSit=&player_type=batter&hfOuts=&opponent=&batter_stands=&hfSA=&game_date_gt=&game_date_lt=&hfInfield=&team=&position=&hfOutfield=&hfRO=&hfFlag=&hfBBT=&metric_1=&hfInn=&min_pitches=0&min_results=0&group_by=name-stats&sort_col=xwoba&player_event_sort=api_p_release_speed&sort_order=desc&min_pas=0&player_id={player_id}"
    
    try:
        response = requests.get(savant_url)
        
        if response.status_code == 200:
            data = pd.read_csv(StringIO(response.text))
            if not data.empty:
                # Check if we have meaningful data (some at-bats)
                if 'abs' in data.columns and data['abs'].values[0] > 0:
                    stats = {
                        'split_name': split_name,
                        'params': params.copy(),
                        'avg': str(data['ba'].values[0]) if 'ba' in data.columns else 'N/A',
                        'slg': str(data['slg'].values[0]) if 'slg' in data.columns else 'N/A',
                        'obp': str(data['obp'].values[0]) if 'obp' in data.columns else 'N/A',
                        'ops': str(float(data['obp'].values[0]) + float(data['slg'].values[0])) if 'obp' in data.columns and 'slg' in data.columns else 'N/A',
                        'homeRuns': int(data['hrs'].values[0]) if 'hrs' in data.columns else 0,
                        'hits': int(data['hits'].values[0]) if 'hits' in data.columns else 0,
                        'atBats': int(data['abs'].values[0]) if 'abs' in data.columns else 0,
                        'plateAppearances': int(data['pa'].values[0]) if 'pa' in data.columns else 0,
                        'strikeOuts': int(data['so'].values[0]) if 'so' in data.columns else 0,
                        'baseOnBalls': int(data['bb'].values[0]) if 'bb' in data.columns else 0,
                        'lastUpdated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Additional metrics if available
                    if 'whiffs' in data.columns and 'swings' in data.columns:
                        stats['whiffs'] = int(data['whiffs'].values[0])
                        stats['swings'] = int(data['swings'].values[0])
                        if data['swings'].values[0] > 0:
                            stats['whiff_rate'] = str(round(data['whiffs'].values[0] / data['swings'].values[0], 3))
                    
                    print(f"Found data for {split_name}")
                    print(f"  AVG: {stats['avg']}")
                    print(f"  OPS: {stats['ops']}")
                    print(f"  AB: {stats['atBats']}")
                    
                    return stats
                else:
                    print(f"No meaningful at-bats found for {split_name}")
                    return None
            else:
                print(f"No data found for {split_name}")
                return None
        else:
            print(f"Error: Status code {response.status_code}")
            return None
    except Exception as e:
        print(f"Error getting combined split data: {e}")
        return None

def get_pitch_type_data(player_id, season):
    """
    Get data for individual pitch types
    
    Parameters:
    - player_id (int): MLB player ID
    - season (int): Season year
    
    Returns:
    - dict: Data for each pitch type
    """
    pitch_types = {
        # Fastball group
        "FF": "Fastball (4-seam)",
        "SI": "Sinker (2-Seam)",
        "FC": "Cutter",
        # Offspeed group
        "CH": "Changeup",
        "FS": "Split-finger",
        "FO": "Forkball",
        "SC": "Screwball",
        # Breaking group
        "CU": "Curveball",
        "KC": "Knuckle Curve",
        "CS": "Slow Curve",
        "SL": "Slider",
        "ST": "Sweeper",
        "SV": "Slurve",
        "KN": "Knuckleball",
        # Other group
        "EP": "Eephus",
        "FA": "Other",
        "IN": "Intentional Ball",
        "PO": "Pitchout"
    }
    
    pitch_groups = {
        "Fastball": ["FF", "SI", "FC"],
        "Breaking": ["CU", "KC", "CS", "SL", "ST", "SV", "KN"],
        "Offspeed": ["CH", "FS", "FO", "SC"],
        "Other": ["EP", "FA", "IN", "PO"]
    }
    
    # Initialize pitch data
    pitch_data = {}
    
    # Get data for each pitch type
    print("\nGetting pitch type data...")
    for pitch_code, pitch_name in pitch_types.items():
        data = get_combined_split_data(player_id, season, {'pitch_type': pitch_code})
        if data and data.get('atBats', 0) >= 5:  # Only include if enough data
            pitch_data[pitch_code] = data
    
    # Get data for pitch groups
    print("\nGetting pitch group data...")
    for group_name, group_pitches in pitch_groups.items():
        # Build list of pitch codes for the URL
        pitch_code_list = '%7C'.join([p for p in group_pitches if p in pitch_types])
        if pitch_code_list:
            pitch_code_param = f"{pitch_code_list}%7C"
            
            # Get data for this group
            group_data = get_combined_split_data(player_id, season, {'pitch_type': group_name})
            if group_data and group_data.get('atBats', 0) >= 10:  # Higher threshold for groups
                pitch_data[f"GROUP_{group_name}"] = group_data
    
    return pitch_data

def get_detailed_pitch_splits(player_id, season):
    """
    Get detailed pitch type data split by pitcher handedness and location
    
    Parameters:
    - player_id (int): MLB player ID
    - season (int): Season year
    
    Returns:
    - dict: Detailed pitch split data
    """
    pitch_types = [
        # Fastball group
        "FF", "SI", "FC",
        # Offspeed group
        "CH", "FS", "FO", "SC",
        # Breaking group
        "CU", "KC", "CS", "SL", "ST", "SV", "KN",
        # Other group (skip less common ones)
        "EP"
    ]
    
    pitcher_hands = ["L", "R"]
    locations = ["Home", "Road"]
    
    # Initialize the data structure
    detailed_splits = {
        "player_id": player_id,
        "season": season,
        "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "splits": {}
    }
    
    # Get data for each pitch type by handedness and location
    for pitch in pitch_types:
        # Get data for this pitch type overall
        pitch_data = get_combined_split_data(player_id, season, {'pitch_type': pitch})
        if pitch_data and pitch_data.get('atBats', 0) >= 5:  # Only if we have enough data
            split_key = f"pitch_{pitch}"
            detailed_splits["splits"][split_key] = pitch_data
            
            # Get data by pitcher handedness
            for hand in pitcher_hands:
                hand_data = get_combined_split_data(player_id, season, {'pitch_type': pitch, 'pitcher_throws': hand})
                if hand_data and hand_data.get('atBats', 0) >= 5:
                    split_key = f"pitch_{pitch}_hand_{hand}"
                    detailed_splits["splits"][split_key] = hand_data
                    
                    # Get data by location and handedness
                    for location in locations:
                        loc_data = get_combined_split_data(player_id, season, {
                            'pitch_type': pitch, 
                            'pitcher_throws': hand,
                            'home_road': location
                        })
                        if loc_data and loc_data.get('atBats', 0) >= 5:
                            split_key = f"pitch_{pitch}_hand_{hand}_loc_{location}"
                            detailed_splits["splits"][split_key] = loc_data
    
    # Get data for pitch groups
    pitch_groups = {
        "Fastball": ["FF", "SI", "FC"],
        "Breaking": ["CU", "KC", "CS", "SL", "ST", "SV", "KN"],
        "Offspeed": ["CH", "FS", "FO", "SC"]
    }
    
    # For each pitch group, also get by handedness and location
    for group_name, group_pitches in pitch_groups.items():
        for hand in pitcher_hands:
            hand_data = []
            for pitch in group_pitches:
                # Look for existing data for this pitch and hand
                split_key = f"pitch_{pitch}_hand_{hand}"
                if split_key in detailed_splits["splits"]:
                    hand_data.append(detailed_splits["splits"][split_key])
            
            # Summarize the group data
            if hand_data:
                # Simple average of AVG, OPS, etc.
                avg_sum = sum(float(d['avg']) for d in hand_data if d['avg'] != 'N/A')
                ops_sum = sum(float(d['ops']) for d in hand_data if d['ops'] != 'N/A')
                ab_sum = sum(d['atBats'] for d in hand_data)
                hr_sum = sum(d['homeRuns'] for d in hand_data)
                
                if len(hand_data) > 0 and ab_sum > 0:
                    group_key = f"group_{group_name}_hand_{hand}"
                    detailed_splits["splits"][group_key] = {
                        'split_name': f"{group_name} pitches vs {hand}HP",
                        'avg': str(round(avg_sum / len(hand_data), 3)),
                        'ops': str(round(ops_sum / len(hand_data), 3)),
                        'atBats': ab_sum,
                        'homeRuns': hr_sum,
                        'lastUpdated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
    
    return detailed_splits

def generate_performance_summary(player_name, player_id, season, all_data):
    """
    Generate a high-level summary of a player's performance across different contexts
    
    Parameters:
    - player_name (str): Player's name
    - player_id (int): Player's ID
    - season (int): Season year
    - all_data (dict): All collected data
    
    Returns:
    - dict: Summary of player's performance
    """
    # Initialize summary structure
    summary = {
        "player": {
            "name": player_name,
            "id": player_id
        },
        "season": season,
        "basic_splits": {},
        "pitch_type_summary": {},
        "handedness_summary": {},
        "location_summary": {},
        "notable_splits": []
    }
    
    # Extract basic splits
    if "basic_splits" in all_data:
        basic_splits = all_data["basic_splits"]
        
        # Overall stats
        if "overall" in basic_splits:
            summary["basic_splits"]["overall"] = {
                "avg": basic_splits["overall"].get("avg", "N/A"),
                "ops": basic_splits["overall"].get("ops", "N/A"),
                "hr": basic_splits["overall"].get("homeRuns", 0),
                "ab": basic_splits["overall"].get("atBats", 0)
            }
        
        # vs LHP/RHP
        for hand in ["vs LHP", "vs RHP"]:
            if hand in basic_splits:
                summary["basic_splits"][hand] = {
                    "avg": basic_splits[hand].get("avg", "N/A"),
                    "ops": basic_splits[hand].get("ops", "N/A"),
                    "hr": basic_splits[hand].get("homeRuns", 0),
                    "ab": basic_splits[hand].get("atBats", 0)
                }
        
        # Home/Away
        for loc in ["Home", "Away"]:
            if loc in basic_splits:
                summary["basic_splits"][loc] = {
                    "avg": basic_splits[loc].get("avg", "N/A"),
                    "ops": basic_splits[loc].get("ops", "N/A"),
                    "hr": basic_splits[loc].get("homeRuns", 0),
                    "ab": basic_splits[loc].get("atBats", 0)
                }
    
    # Extract pitch type summary
    if "pitch_data" in all_data:
        pitch_data = all_data["pitch_data"]
        
        # Summarize by pitch type
        for pitch_code, data in pitch_data.items():
            if not pitch_code.startswith("GROUP_") and data.get("atBats", 0) >= 10:
                summary["pitch_type_summary"][pitch_code] = {
                    "name": data.get("split_name", pitch_code),
                    "avg": data.get("avg", "N/A"),
                    "ops": data.get("ops", "N/A"),
                    "hr": data.get("homeRuns", 0),
                    "ab": data.get("atBats", 0)
                }
        
        # Summarize by pitch group
        for pitch_code, data in pitch_data.items():
            if pitch_code.startswith("GROUP_") and data.get("atBats", 0) >= 10:
                group_name = pitch_code.replace("GROUP_", "")
                summary["pitch_type_summary"][group_name] = {
                    "name": data.get("split_name", group_name),
                    "avg": data.get("avg", "N/A"),
                    "ops": data.get("ops", "N/A"),
                    "hr": data.get("homeRuns", 0),
                    "ab": data.get("atBats", 0)
                }
    
    # Extract detailed split insights if available
    if "detailed_splits" in all_data and "splits" in all_data["detailed_splits"]:
        detailed_splits = all_data["detailed_splits"]["splits"]
        
        # Find notable splits (high performance)
        notable_splits = []
        
        for key, data in detailed_splits.items():
            # Only include splits with enough data
            if data.get("atBats", 0) >= 10 and data.get("avg", "N/A") != "N/A":
                if not key.startswith("group_"):  # Skip group summaries
                    notable_splits.append({
                        "name": data.get("split_name", key),
                        "avg": data.get("avg", "N/A"),
                        "ops": data.get("ops", "N/A"),
                        "hr": data.get("homeRuns", 0),
                        "ab": data.get("atBats", 0)
                    })
        
        # Sort by batting average (descending)
        notable_splits.sort(key=lambda x: float(x["avg"]) if x["avg"] != "N/A" else 0, reverse=True)
        
        # Take top 5 notable splits
        summary["notable_splits"] = notable_splits[:5]
    
    return summary

def print_performance_summary(summary):
    """
    Print the player performance summary in a readable format
    
    Parameters:
    - summary (dict): Player performance summary
    """
    player_name = summary["player"]["name"]
    season = summary["season"]
    
    print("\n" + "="*80)
    print(f"PERFORMANCE SUMMARY: {player_name} - {season} SEASON")
    print("="*80)
    
    # Print basic splits
    print("\nBASIC SPLITS:")
    print("-" * 60)
    
    if "overall" in summary["basic_splits"]:
        overall = summary["basic_splits"]["overall"]
        print(f"OVERALL:      AVG: {overall['avg']}  OPS: {overall['ops']}  HR: {overall['hr']}  AB: {overall['ab']}")
    
    print("\nSPLIT TYPE      AVG      OPS       HR      AB")
    print("-" * 60)
    
    if "vs LHP" in summary["basic_splits"]:
        lhp = summary["basic_splits"]["vs LHP"]
        print(f"vs LHP:       {lhp['avg']}    {lhp['ops']}    {lhp['hr']:2d}     {lhp['ab']}")
    
    if "vs RHP" in summary["basic_splits"]:
        rhp = summary["basic_splits"]["vs RHP"]
        print(f"vs RHP:       {rhp['avg']}    {rhp['ops']}    {rhp['hr']:2d}     {rhp['ab']}")
    
    if "Home" in summary["basic_splits"]:
        home = summary["basic_splits"]["Home"]
        print(f"Home:         {home['avg']}    {home['ops']}    {home['hr']:2d}     {home['ab']}")
    
    if "Away" in summary["basic_splits"]:
        away = summary["basic_splits"]["Away"]
        print(f"Away:         {away['avg']}    {away['ops']}    {away['hr']:2d}     {away['ab']}")
    
    # Print pitch type summary if available
    if summary["pitch_type_summary"]:
        print("\nPITCH TYPE PERFORMANCE:")
        print("-" * 60)
        print("PITCH TYPE     AVG      OPS       HR      AB")
        print("-" * 60)
        
        # Group by pitch categories
        categories = {
            "Fastball": [],
            "Breaking": [],
            "Offspeed": [],
            "Other": []
        }
        
        # First print the group summaries
        for group in ["Fastball", "Breaking", "Offspeed"]:
            if group in summary["pitch_type_summary"]:
                data = summary["pitch_type_summary"][group]
                print(f"{group:<14} {data['avg']}    {data['ops']}    {data['hr']:2d}     {data['ab']}")
                
        print("-" * 60)
        
        # Then print individual pitch types, sorted by group
        pitch_groups = {
            "Fastball": ["FF", "SI", "FC"],
            "Breaking": ["CU", "KC", "CS", "SL", "ST", "SV", "KN"],
            "Offspeed": ["CH", "FS", "FO", "SC"],
            "Other": ["EP", "FA", "IN", "PO"]
        }
        
        pitch_names = {
            "FF": "4-seam FB",
            "SI": "Sinker",
            "FC": "Cutter",
            "CH": "Changeup",
            "FS": "Splitter",
            "FO": "Forkball",
            "SC": "Screwball",
            "CU": "Curveball",
            "KC": "Knuckle Curve",
            "CS": "Slow Curve",
            "SL": "Slider",
            "ST": "Sweeper",
            "SV": "Slurve",
            "KN": "Knuckleball",
            "EP": "Eephus",
            "FA": "Other FB",
            "IN": "Int. Ball",
            "PO": "Pitchout"
        }
        
        for group, pitches in pitch_groups.items():
            printed_header = False
            
            for pitch in pitches:
                if pitch in summary["pitch_type_summary"]:
                    if not printed_header:
                        print(f"\n{group} Pitches:")
                        printed_header = True
                    
                    data = summary["pitch_type_summary"][pitch]
                    pitch_display = pitch_names.get(pitch, pitch)
                    print(f"  {pitch_display:<12} {data['avg']}    {data['ops']}    {data['hr']:2d}     {data['ab']}")
    
    # Print notable splits if available
    if summary["notable_splits"]:
        print("\nNOTABLE PERFORMANCE SPLITS:")
        print("-" * 80)
        print("CONTEXT                                 AVG      OPS       HR      AB")
        print("-" * 80)
        
        for i, split in enumerate(summary["notable_splits"]):
            print(f"{i+1}. {split['name']:<35} {split['avg']}    {split['ops']}    {split['hr']:2d}     {split['ab']}")
    
    print("\n" + "="*80)
    print("SUMMARY OF STRENGTHS AND WEAKNESSES:")
    
    # Analyze strengths and weaknesses
    # Pitcher handedness
    if "vs LHP" in summary["basic_splits"] and "vs RHP" in summary["basic_splits"]:
        lhp_avg = float(summary["basic_splits"]["vs LHP"]["avg"])
        rhp_avg = float(summary["basic_splits"]["vs RHP"]["avg"])
        
        if abs(lhp_avg - rhp_avg) >= 0.050:  # Significant difference
            if lhp_avg > rhp_avg:
                print(f"- Strong vs LHP: {lhp_avg:.3f} AVG vs LHP compared to {rhp_avg:.3f} vs RHP")
            else:
                print(f"- Strong vs RHP: {rhp_avg:.3f} AVG vs RHP compared to {lhp_avg:.3f} vs LHP")
    
    # Home/Away
    if "Home" in summary["basic_splits"] and "Away" in summary["basic_splits"]:
        home_avg = float(summary["basic_splits"]["Home"]["avg"])
        away_avg = float(summary["basic_splits"]["Away"]["avg"])
        
        if abs(home_avg - away_avg) >= 0.050:  # Significant difference
            if home_avg > away_avg:
                print(f"- Home field advantage: {home_avg:.3f} AVG at home compared to {away_avg:.3f} away")
            else:
                print(f"- Performs better on the road: {away_avg:.3f} AVG away compared to {home_avg:.3f} at home")
    
    # Pitch type strengths
    if summary["pitch_type_summary"]:
        # Get individual pitch types with enough at-bats
        valid_pitches = {}
        for pitch, data in summary["pitch_type_summary"].items():
            if pitch not in ["Fastball", "Breaking", "Offspeed"] and data["ab"] >= 20:
                valid_pitches[pitch] = float(data["avg"])
        
        # Find best and worst pitch types
        if valid_pitches:
            best_pitch = max(valid_pitches.items(), key=lambda x: x[1])
            worst_pitch = min(valid_pitches.items(), key=lambda x: x[1])
            
            pitch_names = {
                "FF": "4-seam Fastball",
                "SI": "Sinker",
                "FC": "Cutter",
                "CH": "Changeup",
                "FS": "Splitter",
                "CU": "Curveball",
                "SL": "Slider",
                "ST": "Sweeper"
            }
            
            best_name = pitch_names.get(best_pitch[0], best_pitch[0])
            worst_name = pitch_names.get(worst_pitch[0], worst_pitch[0])
            
            print(f"- Best against {best_name}: {best_pitch[1]:.3f} AVG")
            print(f"- Worst against {worst_name}: {worst_pitch[1]:.3f} AVG")
    
    print("="*80)

def save_player_detailed_data(player_name, player_id, season, all_data):
    """
    Save all player data to files
    
    Parameters:
    - player_name (str): Player's name
    - player_id (int): Player's ID
    - season (int): Season year
    - all_data (dict): All collected data
    """
    # Create directory structure if needed
    data_dirs = ["splits", "pitch_data", "detailed_splits", "summaries"]
    for dir_name in data_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
    
    # Save basic splits
    if "basic_splits" in all_data:
        filename = f"splits/{player_name.replace(' ', '_')}_{season}_splits.json"
        try:
            with open(filename, 'w') as f:
                json.dump(all_data["basic_splits"], f, indent=2)
            print(f"Saved basic splits to {filename}")
        except Exception as e:
            print(f"Error saving basic splits: {e}")
    
    # Save pitch data
    if "pitch_data" in all_data:
        filename = f"pitch_data/{player_name.replace(' ', '_')}_{season}_pitch_types.json"
        try:
            with open(filename, 'w') as f:
                json.dump(all_data["pitch_data"], f, indent=2)
            print(f"Saved pitch data to {filename}")
        except Exception as e:
            print(f"Error saving pitch data: {e}")
    
    # Save detailed splits
    if "detailed_splits" in all_data:
        filename = f"detailed_splits/{player_name.replace(' ', '_')}_{season}_detailed.json"
        try:
            with open(filename, 'w') as f:
                json.dump(all_data["detailed_splits"], f, indent=2)
            print(f"Saved detailed splits to {filename}")
        except Exception as e:
            print(f"Error saving detailed splits: {e}")
    
    # Save summary
    if "summary" in all_data:
        filename = f"summaries/{player_name.replace(' ', '_')}_{season}_summary.json"
        try:
            with open(filename, 'w') as f:
                json.dump(all_data["summary"], f, indent=2)
            print(f"Saved summary to {filename}")
        except Exception as e:
            print(f"Error saving summary: {e}")
    
    # Update career files
    update_career_files(player_name, player_id, season, all_data)

def update_career_files(player_name, player_id, season, all_data):
    """
    Update career files with new season data
    
    Parameters:
    - player_name (str): Player's name
    - player_id (int): Player's ID
    - season (int): Season year
    - all_data (dict): All collected data
    """
    # Update career basic splits
    if "basic_splits" in all_data:
        career_filename = f"splits/{player_name.replace(' ', '_')}_career.json"
        career_data = {}
        
        if os.path.exists(career_filename):
            try:
                with open(career_filename, 'r') as f:
                    career_data = json.load(f)
                print(f"Loaded existing career data from {career_filename}")
            except Exception as e:
                print(f"Error loading career data: {e}")
        
        # Initialize career data if needed
        if "player" not in career_data:
            career_data["player"] = {
                "name": player_name,
                "id": player_id
            }
        
        if "seasons" not in career_data:
            career_data["seasons"] = {}
        
        # Update this season's data
        career_data["seasons"][str(season)] = all_data["basic_splits"]
        career_data["lastUpdated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save updated career data
        try:
            with open(career_filename, 'w') as f:
                json.dump(career_data, f, indent=2)
            print(f"Updated career data in {career_filename}")
        except Exception as e:
            print(f"Error saving career data: {e}")
    
    # Update all players file
    all_players_filename = "all_players_career.json"
    all_players_data = {}
    
    if os.path.exists(all_players_filename):
        try:
            with open(all_players_filename, 'r') as f:
                all_players_data = json.load(f)
            print(f"Loaded existing all-players data from {all_players_filename}")
        except Exception as e:
            print(f"Error loading all-players data: {e}")
    
    # Initialize player if needed
    if player_name not in all_players_data:
        all_players_data[player_name] = {
            "player": {
                "name": player_name,
                "id": player_id
            },
            "seasons": {}
        }
    
    # Update player data with this season
    if "summary" in all_data:
        all_players_data[player_name]["seasons"][str(season)] = all_data["summary"]
        all_players_data[player_name]["lastUpdated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save updated all-players file
    try:
        with open(all_players_filename, 'w') as f:
            json.dump(all_players_data, f, indent=2)
        print(f"Updated all-players data in {all_players_filename}")
    except Exception as e:
        print(f"Error saving all-players data: {e}")

def get_complete_player_data(player_name, season=2024):
    """
    Get complete player data including basic splits, pitch types, and detailed splits
    
    Parameters:
    - player_name (str): Player's name
    - season (int): Season year
    
    Returns:
    - dict: All player data
    """
    player_id = get_player_id(player_name)
    if not player_id:
        return None
    
    # Get all data
    all_data = {}
    
    # 1. Get basic splits (LHP/RHP, Home/Away)
    print("\nGetting basic splits...")
    basic_splits = {}
    
    # Get overall stats
    overall_stats = get_baseball_savant_data(player_id, season, 'overall', 'total')
    if overall_stats:
        basic_splits["overall"] = overall_stats
    
    # Get pitcher handedness splits
    for hand in ['R', 'L']:
        stats = get_baseball_savant_data(player_id, season, 'pitcher_throws', hand)
        if stats:
            basic_splits[f'vs {hand}HP'] = stats
    
    # Get home/away splits
    for location in [('Home', 'Home'), ('Road', 'Away')]:
        savant_param, split_name = location
        stats = get_baseball_savant_data(player_id, season, 'home_road', savant_param)
        if stats:
            basic_splits[split_name] = stats
    
    all_data["basic_splits"] = basic_splits
    
    # 2. Get pitch type data
    print("\nGetting pitch type data...")
    pitch_data = get_pitch_type_data(player_id, season)
    all_data["pitch_data"] = pitch_data
    
    # 3. Get detailed pitch splits
    print("\nGetting detailed pitch splits...")
    detailed_splits = get_detailed_pitch_splits(player_id, season)
    all_data["detailed_splits"] = detailed_splits
    
    # 4. Generate summary
    print("\nGenerating performance summary...")
    summary = generate_performance_summary(player_name, player_id, season, all_data)
    all_data["summary"] = summary
    
    # Print summary
    print_performance_summary(summary)
    
    # Save all data
    save_player_detailed_data(player_name, player_id, season, all_data)
    
    return all_data