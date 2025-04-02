from stats import get_complete_player_data

# Example usage
if __name__ == "__main__":
    print("MLB Player Performance Analysis Tool")
    print("=" * 60)
    print("This tool collects and analyzes player performance data across different contexts")
    print("including pitcher handedness, location, and pitch types.")
    print("=" * 60)
    
    player_name = input("\nEnter player name: ")
    season = int(input("Enter season year (default 2024): ") or "2024")
    
    # Get all data and generate summary
    get_complete_player_data(player_name, season)