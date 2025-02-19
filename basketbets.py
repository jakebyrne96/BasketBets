import math
import time
from nba_api.stats.static import teams
from nba_api.stats.endpoints import teamgamelog, boxscoretraditionalv2

def fetch_team_id(team_name):
    """
    Looks up the team using nba_api.
    Returns a tuple (team_id, full_team_name) for the first matching team.
    """
    all_teams = teams.get_teams()
    team_name_lower = team_name.lower()
    for team in all_teams:
        # We check if your input is found in the full name or matches the abbreviation.
        if team_name_lower in team["full_name"].lower() or team_name_lower == team["abbreviation"].lower():
            return team["id"], team["full_name"]
    raise ValueError(f"Team '{team_name}' not found. Please double-check the name and try again.")

def fetch_recent_games(team_id, num_games=5):
    """
    Uses nba_api's TeamGameLog to get recent games for a team.
    Returns a tuple (games, headers) where games is a list of game log rows
    and headers is a list of column names.
    A short sleep is added to help with rate limiting.
    """
    time.sleep(0.6)  # be nice to the API
    gamelog = teamgamelog.TeamGameLog(team_id=team_id)
    data = gamelog.get_dict()["resultSets"][0]
    games = data["rowSet"]
    headers = data["headers"]
    if len(games) < num_games:
        raise ValueError(f"Not enough recent games available for team id {team_id}.")
    return games[:num_games], headers

def get_opponent_points(game_id, team_id):
    """
    Retrieves the opponent's points for a given game.
    It calls the box score endpoint and looks through the team stats.
    """
    time.sleep(0.6)  # avoid rate limits
    boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
    result_set = boxscore.get_dict()["resultSets"][1]  # team stats are usually here
    headers = result_set["headers"]
    rows = result_set["rowSet"]
    team_id_index = headers.index("TEAM_ID")
    pts_index = headers.index("PTS")
    # Look through the rows and return the points for the team that is NOT ours.
    for row in rows:
        if row[team_id_index] != team_id:
            return row[pts_index]
    raise ValueError(f"Opponent points not found for game {game_id}.")

def compute_team_stats(team_id, games, headers):
    """
    Computes average points scored, allowed, and differential for a team.
    Instead of relying on the PLUS_MINUS field, we use the team's points from the game log
    and fetch the opponent's points using the box score endpoint.
    """
    pts_index = headers.index("PTS")
    # Try to find the game id field with a fallback in case the header name is different.
    try:
        game_id_index = headers.index("GAME_ID")
    except ValueError:
        try:
            game_id_index = headers.index("Game_ID")
        except ValueError:
            raise ValueError(f"'GAME_ID' field not found in headers: {headers}")
    
    total_scored = 0
    total_allowed = 0
    for game in games:
        team_pts = game[pts_index]
        game_id = game[game_id_index]
        opponent_pts = get_opponent_points(game_id, team_id)
        total_scored += team_pts
        total_allowed += opponent_pts

    avg_scored = total_scored / len(games)
    avg_allowed = total_allowed / len(games)
    avg_diff = avg_scored - avg_allowed
    return avg_scored, avg_allowed, avg_diff

def prob_to_moneyline(prob):
    """
    Converts win probability to moneyline odds.
    Probabilities ≥ 50% yield negative odds (favorites), while below 50% yield positive odds.
    """
    if prob >= 0.5:
        return -round((prob / (1 - prob)) * 100)
    else:
        return round(((1 - prob) / prob) * 100)

def main():
    print("NBA Betting Odds Calculator using nba_api")
    
    team1_input = input("Enter Team 1 name (e.g., 'Lakers' or 'Los Angeles Lakers'): ").strip()
    team2_input = input("Enter Team 2 name (e.g., 'Celtics' or 'Boston Celtics'): ").strip()
    
    try:
        team1_id, team1_full = fetch_team_id(team1_input)
        team2_id, team2_full = fetch_team_id(team2_input)
    except Exception as e:
        print("There was an issue finding team information:", e)
        return

    try:
        games1, headers1 = fetch_recent_games(team1_id)
        games2, headers2 = fetch_recent_games(team2_id)
    except Exception as e:
        print("There was a problem fetching recent games:", e)
        return

    team1_stats = compute_team_stats(team1_id, games1, headers1)
    team2_stats = compute_team_stats(team2_id, games2, headers2)

    print(f"\n{team1_full} - Avg Points Scored: {team1_stats[0]:.2f}, Allowed: {team1_stats[1]:.2f}, Differential: {team1_stats[2]:.2f}")
    print(f"{team2_full} - Avg Points Scored: {team2_stats[0]:.2f}, Allowed: {team2_stats[1]:.2f}, Differential: {team2_stats[2]:.2f}")

    # Calculate expected margin as half the difference of the teams' differentials.
    expected_margin = (team1_stats[2] - team2_stats[2]) / 2
    print(f"\nExpected Margin (a positive value means {team1_full} is favored): {expected_margin:.2f} points")

    if expected_margin > 0:
        handicap_line = f"{team1_full} -{abs(expected_margin):.2f} / {team2_full} +{abs(expected_margin):.2f}"
    elif expected_margin < 0:
        handicap_line = f"{team2_full} -{abs(expected_margin):.2f} / {team1_full} +{abs(expected_margin):.2f}"
    else:
        handicap_line = "Even match"
    print(f"\nHandicap (Point Spread): {handicap_line}")

    # Estimate win probabilities using a logistic function.
    scale = 5.0  # You can tweak this parameter if needed.
    win_prob_team1 = 1 / (1 + math.exp(-expected_margin / scale))
    win_prob_team2 = 1 - win_prob_team1

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
