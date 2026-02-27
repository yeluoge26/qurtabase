"""
Odds API Client

Fetches real-time betting odds from The Odds API.
Supports multiple bookmakers and markets.
"""

import aiohttp
from config import settings


class OddsAPIClient:
    def __init__(self):
        self.base_url = settings.ODDS_API_BASE
        self.api_key = settings.ODDS_API_KEY

    async def fetch_odds(self, match_id: str = None, sport: str = "soccer_epl") -> dict | None:
        """
        Fetch odds for a specific sport/league (h2h + totals).

        Returns odds dict: {
            "home": 1.85, "draw": 3.50, "away": 4.20,
            "totals": {"line": 2.5, "over_odds": 1.85, "under_odds": 2.05}
        }
        """
        if not self.api_key:
            return None

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sports/{sport}/odds"
                params = {
                    "apiKey": self.api_key,
                    "regions": "eu",
                    "markets": "h2h,totals",
                    "oddsFormat": "decimal",
                }
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()

                if not data:
                    return None

                # Find the match or return the first available
                for event in data:
                    bookmakers = event.get("bookmakers", [])
                    if not bookmakers:
                        continue

                    # Use first bookmaker
                    bm = bookmakers[0]
                    markets = bm.get("markets", [])
                    odds = {}
                    for market in markets:
                        if market["key"] == "h2h":
                            outcomes = market["outcomes"]
                            for o in outcomes:
                                if o["name"] == event["home_team"]:
                                    odds["home"] = o["price"]
                                elif o["name"] == event["away_team"]:
                                    odds["away"] = o["price"]
                                else:
                                    odds["draw"] = o["price"]
                        elif market["key"] == "totals":
                            outcomes = market["outcomes"]
                            totals = {}
                            for o in outcomes:
                                if o["name"] == "Over":
                                    totals["over_odds"] = o["price"]
                                    totals["line"] = o.get("point", 2.5)
                                elif o["name"] == "Under":
                                    totals["under_odds"] = o["price"]
                            if totals.get("over_odds") and totals.get("under_odds"):
                                odds["totals"] = totals
                    if odds:
                        return odds

                return None

        except Exception:
            return None

    async def fetch_all_odds(self, sport: str = "soccer_epl") -> list:
        """Fetch odds for all upcoming matches in a league."""
        if not self.api_key:
            return []

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sports/{sport}/odds"
                params = {
                    "apiKey": self.api_key,
                    "regions": "eu",
                    "markets": "h2h",
                    "oddsFormat": "decimal",
                }
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        return []
                    return await resp.json()
        except Exception:
            return []
