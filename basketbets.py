import math

def get_team_data(team):
    """
    Prompts the user to enter the points scored and points allowed for a team's last 5 games.
    Returns a list of tuples: (points_scored, points_allowed)
    """
    print(f"\nEnter data for {team}'s last 5 games:")
    games = []
    for i in range(5):
        while True:
            try:
                scored = float(input(f"  Game {i+1} - Points scored by {team}: "))
                allowed = float(input(f"  Game {i+1} - Points allowed by {team}: "))
                games.append((scored, allowed))
                break
            except ValueError:
                print("Invalid input. Please enter numeric values.")
    return games

def compute_stats(games):
    """
    Computes average points scored, points allowed, and point differential from a list of games.
    """
    total_scored = sum(game[0] for game in games)
    total_allowed = sum(game[1] for game in games)
    avg_scored = total_scored / len(games)
    avg_allowed = total_allowed / len(games)
    avg_diff = avg_scored - avg_allowed
    return avg_scored, avg_allowed, avg_diff

def prob_to_moneyline(prob):
    """
    Converts a win probability to moneyline odds.
    For probabilities above 50%, returns a negative moneyline (favorite),
    and for underdogs (below 50%) a positive moneyline.
    """
    if prob >= 0.5:
        odds = -round((prob / (1 - prob)) * 100)
    else:
        odds = round(((1 - prob) / prob) * 100)
    return odds

def main():
    print("Basketball Betting Odds Calculator")
    
    # Input team names
    team1 = input("Enter Team 1 name: ")
    team2 = input("Enter Team 2 name: ")

    # Retrieve data for each team
    team1_games = get_team_data(team1)
    team2_games = get_team_data(team2)

    # Compute average stats for each team
    team1_stats = compute_stats(team1_games)
    team2_stats = compute_stats(team2_games)

    print(f"\n{team1} - Avg Points Scored: {team1_stats[0]:.2f}, Allowed: {team1_stats[1]:.2f}, Differential: {team1_stats[2]:.2f}")
    print(f"{team2} - Avg Points Scored: {team2_stats[0]:.2f}, Allowed: {team2_stats[1]:.2f}, Differential: {team2_stats[2]:.2f}")

    # Calculate the expected margin between the two teams.
    # This is a simple method: the difference in point differentials scaled down.
    expected_margin = (team1_stats[2] - team2_stats[2]) / 2
    print(f"\nExpected Margin (Team1 - Team2): {expected_margin:.2f} points")

    # Set the handicap (point spread) based on the expected margin.
    if expected_margin > 0:
        handicap_line = f"{team1} -{abs(expected_margin):.2f} / {team2} +{abs(expected_margin):.2f}"
    elif expected_margin < 0:
        handicap_line = f"{team2} -{abs(expected_margin):.2f} / {team1} +{abs(expected_margin):.2f}"
    else:
        handicap_line = "Even match"

    print(f"\nHandicap (Point Spread): {handicap_line}")

    # Estimate win probability using a logistic function.
    # The scale factor adjusts how sensitive the probability is to the expected margin.
    scale = 5.0
    win_prob_team1 = 1 / (1 + math.exp(-expected_margin / scale))
    win_prob_team2 = 1 - win_prob_team1

    # Convert win probabilities to moneyline odds.
    moneyline_team1 = prob_to_moneyline(win_prob_team1)
    moneyline_team2 = prob_to_moneyline(win_prob_team2)

    print("\nEstimated Win Probabilities:")
    print(f"  {team1}: {win_prob_team1 * 100:.2f}%")
    print(f"  {team2}: {win_prob_team2 * 100:.2f}%")

    print("\nMoneyline Odds:")
    print(f"  {team1}: {moneyline_team1}")
    print(f"  {team2}: {moneyline_team2}")

if __name__ == "__main__":
    main()
