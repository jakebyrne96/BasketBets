import math
from nba_api.stats.static import teams
from nba_api.stats.endpoints import teamgamelog
import time

def fetch_team_id(team_name):
    """
    Look up the team ID using nba_api.
    This function searches through all NBA teams and returns the first match.
    """
    all_teams = teams.get_teams()
    team_name_lower = team_name.lower()
    for team in all_teams:
        # We check if the team name (or abbreviation) matches what you entered.
        if team_name_lower in team["full_name"].lower() or team_name_lower == team["abbreviation"].lower():
            return team["id"], team["full_name"]
    raise ValueError(f"Team '{team_name}' not found. Please double-check the name and try again.")

def fetch_recent_games(team_id, num_games=5):
    """
    Retrieves the most recent games for the given team.
    nba_api returns the games sorted in descending order, so we just pick the top few.
    A short sleep is included to be kind to the API (it can be a bit rate-limited).
    """
    time.sleep(0.6)
    gamelog = teamgamelog.TeamGameLog(team_id=team_id)
    data = gamelog.get_dict()["resultSets"][0]
    games = data["rowSet"]
    headers = data["headers"]
    if len(games) < num_games:
        raise ValueError(f"Not enough recent games available for team id {team_id}.")
    return games[:num_games], headers

def compute_team_stats(games, headers):
    """
    Computes average points scored, points allowed, and the point differential.
    The team game log provides:
      - 'PTS': Points scored by the team.
      - 'PLUS_MINUS': Difference between team points and opponent points.
    We calculate opponent points with:
        Opponent Points = Team Points - PLUS_MINUS
    """
    pts_index = headers.index("PTS")
    plus_minus_index = headers.index("PLUS_MINUS")
    
    total_scored = 0
    total_allowed = 0
    for game in games:
        pts = game[pts_index]
        plus_minus = game[plus_minus_index]
        opponent_pts = pts - plus_minus
        total_scored += pts
        total_allowed += opponent_pts

    avg_scored = total_scored / len(games)
    avg_allowed = total_allowed / len(games)
    avg_diff = avg_scored - avg_allowed
    return avg_scored, avg_allowed, avg_diff

def prob_to_moneyline(prob):
    """
    Converts win probability into moneyline odds.
    If the probability is 50% or higher, we return negative odds (favoring the team).
    Otherwise, we return positive odds.
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
        print("There was a problem fetching the recent games:", e)
        return

    team1_stats = compute_team_stats(games1, headers1)
    team2_stats = compute_team_stats(games2, headers2)

    print(f"\n{team1_full} - Avg Points Scored: {team1_stats[0]:.2f}, Allowed: {team1_stats[1]:.2f}, Differential: {team1_stats[2]:.2f}")
    print(f"{team2_full} - Avg Points Scored: {team2_stats[0]:.2f}, Allowed: {team2_stats[1]:.2f}, Differential: {team2_stats[2]:.2f}")

    # We calculate the expected margin as half the difference between the two differentials.
    expected_margin = (team1_stats[2] - team2_stats[2]) / 2
    print(f"\nExpected Margin (a positive value means {team1_full} is favored): {expected_margin:.2f} points")

    if expected_margin > 0:
        handicap_line = f"{team1_full} -{abs(expected_margin):.2f} / {team2_full} +{abs(expected_margin):.2f}"
    elif expected_margin < 0:
        handicap_line = f"{team2_full} -{abs(expected_margin):.2f} / {team1_full} +{abs(expected_margin):.2f}"
    else:
        handicap_line = "Even match"
    print(f"\nHandicap (Point Spread): {handicap_line}")

    # A logistic function estimates win probabilities based on the expected margin.
    scale = 5.0  # You can tweak this factor if needed.
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
