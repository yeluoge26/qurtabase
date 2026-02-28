"""
LeaguePredictionService — v1.0
Fetches the latest/next fixture for each major league, runs PreMatchEngine,
and caches results in memory. Refreshed on startup + every 30 minutes.
"""

import time
from datetime import datetime, timedelta

from data.allsports_client import AllSportsClient
from data.odds_client import OddsAPIClient
from services.prematch_engine import PreMatchEngine
from config import settings


# 5 major leagues (AllSportsApi league IDs + Odds API sport keys)
LEAGUES = {
    "EPL":        {"id": "152", "odds_key": "soccer_epl"},
    "La Liga":    {"id": "302", "odds_key": "soccer_spain_la_liga"},
    "Bundesliga": {"id": "175", "odds_key": "soccer_germany_bundesliga"},
    "Serie A":    {"id": "207", "odds_key": "soccer_italy_serie_a"},
    "Ligue 1":    {"id": "168", "odds_key": "soccer_france_ligue_one"},
}

# Default Elo ratings for well-known teams
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
    "Villarreal": 1550, "Sevilla": 1530, "Girona": 1520,
    # Bundesliga
    "Bayern Munich": 1750, "Bayer Leverkusen": 1680, "Borussia Dortmund": 1640,
    "RB Leipzig": 1620, "Stuttgart": 1580, "Eintracht Frankfurt": 1570,
    "Freiburg": 1540, "Wolfsburg": 1520,
    # Serie A
    "Inter Milan": 1700, "Napoli": 1660, "AC Milan": 1630, "Juventus": 1640,
    "Atalanta": 1620, "Roma": 1580, "Lazio": 1570, "Fiorentina": 1550,
    # Ligue 1
    "Paris Saint-Germain": 1720, "Monaco": 1580, "Marseille": 1560,
    "Lille": 1550, "Lyon": 1540, "Nice": 1520, "Lens": 1510,
}


def get_elo(team_name: str) -> int:
    """Fuzzy match team name to Elo rating."""
    name = team_name.strip()
    if name in TEAM_ELO:
        return TEAM_ELO[name]
    for k, v in TEAM_ELO.items():
        if k.lower() in name.lower() or name.lower() in k.lower():
            return v
    return 1500


def _find_odds(home_name: str, odds_events: list) -> dict | None:
    """Find matching odds from batch OddsAPI data."""
    if not odds_events:
        return None
    for ev in odds_events:
        if (home_name.lower() in ev.get("home_team", "").lower() or
                ev.get("home_team", "").lower() in home_name.lower()):
            bms = ev.get("bookmakers", [])
            if not bms:
                continue
            for mkt in bms[0].get("markets", []):
                if mkt["key"] == "h2h":
                    odds = {}
                    for o in mkt["outcomes"]:
                        if o["name"] == ev["home_team"]:
                            odds["home"] = o["price"]
                        elif o["name"] == ev["away_team"]:
                            odds["away"] = o["price"]
                        else:
                            odds["draw"] = o["price"]
                    if odds:
                        return odds
    return None


class LeaguePredictionService:
    def __init__(self):
        self.allsports = AllSportsClient()
        self.odds_api = OddsAPIClient()
        self.prematch = PreMatchEngine()
        self._cache: dict[str, dict] = {}
        self._last_refresh: float = 0
        self._refreshing = False

    @property
    def predictions(self) -> dict:
        return self._cache

    @property
    def last_refresh(self) -> float:
        return self._last_refresh

    def _pick_fixture(self, fixtures: list) -> tuple:
        """Pick best fixture from a list: upcoming first, then recent finished.
        Returns (fixture_dict, status_label) or (None, None)."""
        if not fixtures:
            return None, None
        upcoming = [f for f in fixtures
                    if f.get("event_status", "") in ("", "NS", "Not Started")]
        if upcoming:
            return upcoming[0], "upcoming"
        finished = [f for f in fixtures
                    if f.get("event_status", "") in ("Finished", "After Pen.", "After ET")]
        if finished:
            return finished[-1], "recent"
        return fixtures[-1], "recent"

    def _fixture_to_prediction(self, fixture: dict, league_name: str,
                                league_id: str, status_label: str,
                                odds_events: list = None) -> dict:
        """Run PreMatchEngine on a fixture and return prediction dict."""
        home = fixture.get("event_home_team", "Home")
        away = fixture.get("event_away_team", "Away")
        home_elo = get_elo(home)
        away_elo = get_elo(away)
        match_odds = _find_odds(home, odds_events) if odds_events else None

        config = {"home_elo": home_elo, "away_elo": away_elo, "league": league_name}
        prediction = self.prematch.compute(config, match_odds)

        return {
            "league": league_name,
            "league_id": league_id,
            "home": home,
            "away": away,
            "date": fixture.get("event_date", ""),
            "time": fixture.get("event_time", ""),
            "round": fixture.get("league_round", ""),
            "match_status": status_label,
            "score": fixture.get("event_final_result", ""),
            "country": fixture.get("country_name", ""),
            **prediction,
        }

    async def refresh(self):
        """Fetch latest fixture per league, run predictions, update cache."""
        if self._refreshing:
            return
        self._refreshing = True
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            end = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

            # Batch-fetch odds for configured leagues
            all_odds: dict[str, list] = {}
            if settings.has_odds:
                for league_name, meta in LEAGUES.items():
                    try:
                        batch = await self.odds_api.fetch_all_odds(meta["odds_key"])
                        if batch:
                            all_odds[league_name] = batch
                    except Exception:
                        pass

            results = {}

            # 1) Try configured major leagues first
            for league_name, meta in LEAGUES.items():
                try:
                    fixtures = await self.allsports.fetch_fixtures_by_date(
                        today, end, meta["id"]
                    )
                    fixture, status = self._pick_fixture(fixtures)

                    if not fixture:
                        fixtures = await self.allsports.fetch_fixtures_by_date(
                            yesterday, today, meta["id"]
                        )
                        fixture, status = self._pick_fixture(fixtures)

                    if fixture:
                        results[league_name] = self._fixture_to_prediction(
                            fixture, league_name, meta["id"], status,
                            all_odds.get(league_name)
                        )
                except Exception as e:
                    print(f"  [LeaguePredictions] {league_name} error: {e}")

            # 2) Auto-discover: if configured leagues returned nothing,
            #    fetch all available fixtures (works on free/limited API plans)
            if not results:
                try:
                    all_fixtures = await self.allsports.fetch_fixtures_by_date(today, end)
                    if not all_fixtures:
                        all_fixtures = await self.allsports.fetch_fixtures_by_date(yesterday, today)

                    if all_fixtures:
                        # Group by league
                        by_league: dict[str, list] = {}
                        for f in all_fixtures:
                            ln = f.get("league_name", "Unknown")
                            if ln not in by_league:
                                by_league[ln] = []
                            by_league[ln].append(f)

                        for ln, league_fixtures in by_league.items():
                            fixture, status = self._pick_fixture(league_fixtures)
                            if fixture:
                                lid = str(fixture.get("league_key", ""))
                                results[ln] = self._fixture_to_prediction(
                                    fixture, ln, lid, status
                                )
                except Exception as e:
                    print(f"  [LeaguePredictions] auto-discover error: {e}")

            self._cache = results
            self._last_refresh = time.time()
            print(f"  [LeaguePredictions] Refreshed {len(results)} leagues at {datetime.now().strftime('%H:%M:%S')}")
        finally:
            self._refreshing = False
