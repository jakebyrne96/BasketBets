import requests
import datetime
import math

# Base URL for the balldontlie API
BASE_URL = "https://www.balldontlie.io/api/v1"

def fetch_team_id(team_name):
    """
    Fetches the team ID from the API by matching the provided team name.
    If multiple teams match, returns the first match.
    """
    response = requests.get(f"{BASE_URL}/teams")
    if response.status_code != 200:
        raise Exception("Error fetching teams data from API.")
    teams = response.json()["data"]
    team_name_lower = team_name.lower()
    for team in teams:
        # Match if the provided name is in the full name or the abbreviation
        if team_name_lower in team["full_name"].lower() or team_name_lower == team["abbreviation"].lower():
            return team["id"], team["full_name"]
    raise ValueError(f"Team '{team_name}' not found. Please check the spelling or try a different name.")

def fetch_recent_games(team_id, num_games=5):
    """
    Fetches recent games for the given team ID.
    Returns a list of games sorted by date descending (most recent first).
    """
    # Set the end date as today to avoid future games.
    today = datetime.date.today().isoformat()
    params = {
        "team_ids[]": team_id,
        "end_date": today,
        "per_page": 50  # Get a larger batch so we can filter and sort
    }
    response = requests.get(f"{BASE_URL}/games", params=params)
    if response.status_code != 200:
        raise Exception("Error fetching games data from API.")
    games = response.json()["data"]
    
    # Filter out games that may have future dates (if any)
    past_games = [game for game in games if game["date"][:10] < today]
    # Sort games by date in descending order
    past_games.sort(key=lambda game: game["date"], reverse=True)
    
    # Return the most recent 'num_games' results.
    if len(past_games) < num_games:
        raise ValueError(f"Not enough past games found for team id {team_id}.")
    return past_games[:num_games]

def compute_team_stats(team_id, games):
    """
    Computes average points scored, allowed, and differential for the given team
    based on the list of games. Adjusts based on whether the team was home or away.
    """
    total_scored = 0
    total_allowed = 0
    
    for game in games:
        # Determine if the team was home or away.
        if game["home_team"]["id"] == team_id:
            scored = game["home_team_score"]
            allowed = game["visitor_team_score"]
        else:
            scored = game["visitor_team_score"]
            allowed = game["home_team_score"]
        total_scored += scored
        total_allowed += allowed

    avg_scored = total_scored / len(games)
    avg_allowed = total_allowed / len(games)
    avg_diff = avg_scored - avg_allowed
    return avg_scored, avg_allowed, avg_diff

def prob_to_moneyline(prob):
    """
    Converts a win probability to moneyline odds.
    Probabilities >= 50% produce negative odds (favorites) and those < 50% positive odds.
    """
    if prob >= 0.5:
        odds = -round((prob / (1 - prob)) * 100)
    else:
        odds = round(((1 - prob) / prob) * 100)
    return odds

def main():
    print("NBA Betting Odds Calculator using Recent Game Data")
    
    # Input team names from the user
    team1_input = input("Enter Team 1 name (e.g., 'Lakers' or 'Los Angeles Lakers'): ")
    team2_input = input("Enter Team 2 name (e.g., 'Celtics' or 'Boston Celtics'): ")
    
    try:
        team1_id, team1_full = fetch_team_id(team1_input)
        team2_id, team2_full = fetch_team_id(team2_input)
    except ValueError as e:
        print(e)
        return
    except Exception as ex:
        print("An error occurred while fetching team information:", ex)
        return

    try:
        team1_games = fetch_recent_games(team1_id)
        team2_games = fetch_recent_games(team2_id)
    except Exception as ex:
        print("An error occurred while fetching game data:", ex)
        return

    # Compute statistics for both teams
    team1_stats = compute_team_stats(team1_id, team1_games)
    team2_stats = compute_team_stats(team2_id, team2_games)

    print(f"\n{team1_full} - Avg Points Scored: {team1_stats[0]:.2f}, Allowed: {team1_stats[1]:.2f}, Differential: {team1_stats[2]:.2f}")
    print(f"{team2_full} - Avg Points Scored: {team2_stats[0]:.2f}, Allowed: {team2_stats[1]:.2f}, Differential: {team2_stats[2]:.2f}")

    # Calculate the expected margin between the two teams.
    # This simple model uses half the difference in average point differentials.
    expected_margin = (team1_stats[2] - team2_stats[2]) / 2
    print(f"\nExpected Margin (Positive means {team1_full} favored): {expected_margin:.2f} points")

    # Determine handicap (point spread) line
    if expected_margin > 0:
        handicap_line = f"{team1_full} -{abs(expected_margin):.2f} / {team2_full} +{abs(expected_margin):.2f}"
    elif expected_margin < 0:
        handicap_line = f"{team2_full} -{abs(expected_margin):.2f} / {team1_full} +{abs(expected_margin):.2f}"
    else:
        handicap_line = "Even match"
        
    print(f"\nHandicap (Point Spread): {handicap_line}")

    # Estimate win probabilities using a logistic function.
    # The scale factor adjusts the sensitivity to the point differential.
    scale = 5.0
    win_prob_team1 = 1 / (1 + math.exp(-expected_margin / scale))
    win_prob_team2 = 1 - win_prob_team1

    # Convert probabilities into moneyline odds.
    moneyline_team1 = prob_to_moneyline(win_prob_team1)
    moneyline_team2 = prob_to_moneyline(win_prob_team2)

    print("\nEstimated Win Probabilities:")
    print(f"  {team1_full}: {win_prob_team1 * 100:.2f}%")
    print(f"  {team2_full}: {win_prob_team2 * 100:.2f}%")

    print("\nMoneyline Odds:")
    print(f"  {team1_full}: {moneyline_team1}")
    print(f"  {team2_full}: {moneyline_team2}")

if __name__ == "__main__":
    main()
