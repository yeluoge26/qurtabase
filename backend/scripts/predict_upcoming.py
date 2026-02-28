"""
predict_upcoming.py — Pre-match prediction for real upcoming matches

Fetches upcoming fixtures from AllSportsApi, gets odds from The Odds API,
runs the trained model, and outputs formatted predictions.

Run:
  cd backend
  python scripts/predict_upcoming.py
"""

import os
import sys
import asyncio
import json

# Add parent dir
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import settings
from data.allsports_client import AllSportsClient
from data.odds_client import OddsAPIClient
from services.prematch_engine import PreMatchEngine

# Try to load trained model
try:
    from models.predictor import LivePredictor
    predictor = LivePredictor(settings.MODEL_PATH)
    print("[OK] Trained model loaded")
except Exception as e:
    predictor = None
    print(f"[WARN] No trained model: {e}")

allsports = AllSportsClient()
odds_api = OddsAPIClient()
prematch = PreMatchEngine()

# Major league IDs for AllSportsApi
LEAGUES = {
    "EPL": "152",        # English Premier League
    "La Liga": "302",    # Spanish La Liga
    "Bundesliga": "175", # German Bundesliga
    "Serie A": "207",    # Italian Serie A
    "Ligue 1": "168",    # French Ligue 1
    "UCL": "3",          # UEFA Champions League
}

# Default Elo ratings for well-known teams (approximation)
TEAM_ELO = {
    # EPL
    "Manchester City": 1750, "Arsenal": 1720, "Liverpool": 1710,
    "Chelsea": 1620, "Manchester United": 1600, "Tottenham Hotspur": 1600,
    "Newcastle United": 1590, "Aston Villa": 1580, "Brighton": 1560,
    "West Ham United": 1540, "Bournemouth": 1520, "Fulham": 1510,
    "Crystal Palace": 1500, "Brentford": 1500, "Wolverhampton Wanderers": 1490,
    "Nottingham Forest": 1490, "Everton": 1470, "Leicester City": 1460,
    "Ipswich Town": 1430, "Southampton": 1420,
    # La Liga
    "Real Madrid": 1760, "Barcelona": 1750, "Atletico Madrid": 1660,
    "Real Sociedad": 1580, "Athletic Club": 1570, "Real Betis": 1550,
    "Villarreal": 1550, "Sevilla": 1530,
    # Bundesliga
    "Bayern Munich": 1750, "Bayer Leverkusen": 1680, "Borussia Dortmund": 1640,
    "RB Leipzig": 1620, "Stuttgart": 1580, "Eintracht Frankfurt": 1570,
    # Serie A
    "Inter Milan": 1700, "Napoli": 1660, "AC Milan": 1630, "Juventus": 1640,
    "Atalanta": 1620, "Roma": 1580, "Lazio": 1570,
    # Ligue 1
    "Paris Saint-Germain": 1720, "Monaco": 1580, "Marseille": 1560, "Lille": 1550,
}


def get_elo(team_name: str) -> int:
    """Fuzzy match team name to Elo rating."""
    name = team_name.strip()
    if name in TEAM_ELO:
        return TEAM_ELO[name]
    # Fuzzy: check if any key is substring
    for k, v in TEAM_ELO.items():
        if k.lower() in name.lower() or name.lower() in k.lower():
            return v
    return 1500  # default


def format_prediction(fixture: dict, prediction: dict):
    """Pretty-print a match prediction."""
    home = fixture.get("event_home_team", "Home")
    away = fixture.get("event_away_team", "Away")
    date = fixture.get("event_date", "?")
    time_ = fixture.get("event_time", "?")
    league = fixture.get("league_name", "?")

    probs = prediction["probabilities"]
    rec = prediction["recommendation_1x2"]
    ou_rec = prediction["ou_recommendation"]

    print(f"\n{'='*60}")
    print(f"  {league}")
    print(f"  {home} vs {away}")
    print(f"  {date} {time_}")
    print(f"{'='*60}")
    print(f"  1X2 Recommendation:  {rec}")
    print(f"    HOME: {probs['home']:5.1f}%")
    print(f"    DRAW: {probs['draw']:5.1f}%")
    print(f"    AWAY: {probs['away']:5.1f}%")
    print(f"  O/U Recommendation:  {ou_rec} {prediction['ou_line']}")
    print(f"    OVER:  {prediction['prob_over']:5.1f}%")
    print(f"    UNDER: {prediction['prob_under']:5.1f}%")
    print(f"    λ total: {prediction['lambda_total']:.2f}")
    print(f"  Confidence: {prediction['confidence']}%")
    print(f"  Source: {prediction['source']}")
    print(f"  Key Factors:")
    for f in prediction.get("key_factors", []):
        arrow = "▲" if f["direction"] == "positive" else "▼" if f["direction"] == "negative" else "◆"
        print(f"    {arrow} {f['factor'].replace('_', ' ').upper()}: {f['value']}")
    print(f"{'='*60}")


async def main():
    print("\n" + "=" * 60)
    print("  AI Football Quant Terminal — Pre-Match Predictions")
    print("=" * 60)

    if not settings.ALLSPORTS_API_KEY:
        print("\n[ERROR] ALLSPORTS_API_KEY not configured. Set it in .env")
        return

    # Fetch upcoming fixtures (next 3 days)
    from datetime import datetime, timedelta
    today = datetime.now().strftime("%Y-%m-%d")
    end = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

    print(f"\n[1/3] Fetching fixtures {today} to {end}...")

    all_fixtures = []
    for league_name, league_id in LEAGUES.items():
        try:
            fixtures = await allsports.fetch_fixtures_by_date(today, end, league_id)
            if fixtures:
                print(f"  {league_name}: {len(fixtures)} fixtures")
                all_fixtures.extend(fixtures)
        except Exception as e:
            print(f"  {league_name}: error - {e}")

    if not all_fixtures:
        print("\n[WARN] No upcoming fixtures found. Trying without league filter...")
        try:
            all_fixtures = await allsports.fetch_fixtures_by_date(today, end)
            print(f"  Found {len(all_fixtures)} fixtures (all leagues)")
        except Exception as e:
            print(f"  Error: {e}")

    if not all_fixtures:
        print("\n[ERROR] No fixtures available. Check API key or date range.")
        return

    # Filter for not-started matches
    upcoming = [f for f in all_fixtures
                if f.get("event_status", "") in ("", "NS", "Not Started", "Cancelled", "Postponed")]
    # Include all if none match the filter
    if not upcoming:
        upcoming = all_fixtures[:20]

    print(f"\n[2/3] Found {len(upcoming)} upcoming matches")

    # Fetch odds
    print(f"\n[3/3] Fetching odds and running predictions...")

    odds_data = None
    if settings.has_odds:
        for sport_key in ["soccer_epl", "soccer_spain_la_liga", "soccer_germany_bundesliga",
                          "soccer_italy_serie_a", "soccer_france_ligue_one",
                          "soccer_uefa_champs_league"]:
            try:
                batch = await odds_api.fetch_all_odds(sport_key)
                if batch:
                    if odds_data is None:
                        odds_data = []
                    odds_data.extend(batch)
            except Exception:
                pass
        if odds_data:
            print(f"  Fetched odds for {len(odds_data)} events")

    # Run predictions (show up to 10)
    predictions = []
    for fix in upcoming[:10]:
        home = fix.get("event_home_team", "Home")
        away = fix.get("event_away_team", "Away")
        home_elo = get_elo(home)
        away_elo = get_elo(away)

        # Try to find matching odds
        match_odds = None
        if odds_data:
            for od in odds_data:
                if (home.lower() in od.get("home_team", "").lower() or
                    od.get("home_team", "").lower() in home.lower()):
                    bms = od.get("bookmakers", [])
                    if bms:
                        for mkt in bms[0].get("markets", []):
                            if mkt["key"] == "h2h":
                                outcomes = mkt["outcomes"]
                                match_odds = {}
                                for o in outcomes:
                                    if o["name"] == od["home_team"]:
                                        match_odds["home"] = o["price"]
                                    elif o["name"] == od["away_team"]:
                                        match_odds["away"] = o["price"]
                                    else:
                                        match_odds["draw"] = o["price"]
                    break

        config = {
            "home_elo": home_elo,
            "away_elo": away_elo,
            "league": fix.get("league_name", ""),
        }

        prediction = prematch.compute(config, match_odds)
        format_prediction(fix, prediction)
        predictions.append({"fixture": fix, "prediction": prediction})

    # Save to JSON
    output_path = os.path.join(os.path.dirname(__file__), "..", "predictions_upcoming.json")
    save_data = []
    for p in predictions:
        save_data.append({
            "home": p["fixture"].get("event_home_team"),
            "away": p["fixture"].get("event_away_team"),
            "date": p["fixture"].get("event_date"),
            "time": p["fixture"].get("event_time"),
            "league": p["fixture"].get("league_name"),
            **p["prediction"],
        })
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] Predictions saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
