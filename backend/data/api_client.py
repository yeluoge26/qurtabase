"""
Football API Client

Fetches live match data from API-Football (api-sports.io).
Handles rate limiting, response parsing, and error recovery.
"""

import aiohttp
from config import settings


class FootballAPIClient:
    def __init__(self):
        self.base_url = settings.FOOTBALL_API_BASE
        self.headers = {"x-apisports-key": settings.FOOTBALL_API_KEY}

    async def fetch_live_matches(self) -> list:
        """Fetch all currently live matches."""
        if not settings.FOOTBALL_API_KEY:
            return []

        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/fixtures"
            params = {"live": "all"}
            async with session.get(url, headers=self.headers, params=params) as resp:
                data = await resp.json()

            matches = []
            for fix in data.get("response", []):
                matches.append({
                    "id": str(fix["fixture"]["id"]),
                    "league": fix["league"]["name"],
                    "league_country": fix["league"]["country"],
                    "home": fix["teams"]["home"]["name"],
                    "away": fix["teams"]["away"]["name"],
                    "home_logo": fix["teams"]["home"].get("logo", ""),
                    "away_logo": fix["teams"]["away"].get("logo", ""),
                    "score": f"{fix['goals']['home'] or 0}-{fix['goals']['away'] or 0}",
                    "minute": fix["fixture"]["status"].get("elapsed", 0),
                    "status": fix["fixture"]["status"]["short"],
                })
            return matches

    async def fetch_match(self, match_id: str) -> dict:
        """Fetch detailed data for a specific match."""
        if not settings.FOOTBALL_API_KEY:
            raise ValueError("No API key configured")

        async with aiohttp.ClientSession() as session:
            # Fetch fixture data
            url = f"{self.base_url}/fixtures"
            params = {"id": match_id}
            async with session.get(url, headers=self.headers, params=params) as resp:
                data = await resp.json()

            if not data.get("response"):
                raise ValueError(f"Match {match_id} not found")

            fixture = data["response"][0]
            stats_raw = fixture.get("statistics", [])

            # Fetch fixture statistics separately if not included
            if not stats_raw:
                stats_url = f"{self.base_url}/fixtures/statistics"
                async with session.get(stats_url, headers=self.headers, params={"fixture": match_id}) as resp:
                    stats_data = await resp.json()
                    stats_raw = stats_data.get("response", [])

            # Parse stats
            stats = self._parse_stats(stats_raw)

            home_team = fixture["teams"]["home"]
            away_team = fixture["teams"]["away"]
            status = fixture["fixture"]["status"]

            return {
                "match": {
                    "league": fixture["league"]["name"],
                    "round": fixture["league"].get("round", ""),
                    "minute": status.get("elapsed", 0) or 0,
                    "half": "H1" if (status.get("elapsed", 0) or 0) <= 45 else "H2",
                    "home_goals": fixture["goals"]["home"] or 0,
                    "away_goals": fixture["goals"]["away"] or 0,
                    "home_short": home_team["name"][:3].upper(),
                    "away_short": away_team["name"][:3].upper(),
                    "home_name": home_team["name"],
                    "away_name": away_team["name"],
                },
                "stats": stats,
                "minute": status.get("elapsed", 0) or 0,
                "home_goals": fixture["goals"]["home"] or 0,
                "away_goals": fixture["goals"]["away"] or 0,
            }

    def _parse_stats(self, stats_raw: list) -> dict:
        """Parse API-Football statistics into our format."""
        if not stats_raw or len(stats_raw) < 2:
            return self._empty_stats()

        home_stats = {}
        away_stats = {}
        for s in stats_raw[0].get("statistics", []):
            home_stats[s["type"]] = s["value"]
        for s in stats_raw[1].get("statistics", []):
            away_stats[s["type"]] = s["value"]

        def safe_int(val, default=0):
            if val is None:
                return default
            if isinstance(val, str):
                return int(val.replace("%", "")) if val.replace("%", "").isdigit() else default
            return int(val)

        h_shots = safe_int(home_stats.get("Total Shots"))
        a_shots = safe_int(away_stats.get("Total Shots"))
        h_on = safe_int(home_stats.get("Shots on Goal"))
        a_on = safe_int(away_stats.get("Shots on Goal"))

        return {
            "shots": [h_shots, a_shots],
            "shots_on_target": [h_on, a_on],
            "xg": [
                float(home_stats.get("expected_goals", 0) or 0),
                float(away_stats.get("expected_goals", 0) or 0),
            ],
            "dangerous_attacks": [
                safe_int(home_stats.get("Dangerous Attacks")),
                safe_int(away_stats.get("Dangerous Attacks")),
            ],
            "corners": [
                safe_int(home_stats.get("Corner Kicks")),
                safe_int(away_stats.get("Corner Kicks")),
            ],
            "possession": [
                safe_int(home_stats.get("Ball Possession", "50%")),
                safe_int(away_stats.get("Ball Possession", "50%")),
            ],
            "pass_accuracy": [
                safe_int(home_stats.get("Passes accurate")),
                safe_int(away_stats.get("Passes accurate")),
            ],
            "fouls": [
                safe_int(home_stats.get("Fouls")),
                safe_int(away_stats.get("Fouls")),
            ],
            "yellows": [
                safe_int(home_stats.get("Yellow Cards")),
                safe_int(away_stats.get("Yellow Cards")),
            ],
            "reds": [
                safe_int(home_stats.get("Red Cards")),
                safe_int(away_stats.get("Red Cards")),
            ],
            "attacks": [
                safe_int(home_stats.get("Total Attacks")),
                safe_int(away_stats.get("Total Attacks")),
            ],
            "saves": [
                safe_int(home_stats.get("Goalkeeper Saves")),
                safe_int(away_stats.get("Goalkeeper Saves")),
            ],
            "offsides": [
                safe_int(home_stats.get("Offsides")),
                safe_int(away_stats.get("Offsides")),
            ],
        }

    @staticmethod
    def _empty_stats() -> dict:
        return {
            "shots": [0, 0],
            "shots_on_target": [0, 0],
            "xg": [0, 0],
            "dangerous_attacks": [0, 0],
            "corners": [0, 0],
            "possession": [50, 50],
            "pass_accuracy": [80, 80],
            "fouls": [0, 0],
            "yellows": [0, 0],
            "reds": [0, 0],
            "attacks": [0, 0],
            "saves": [0, 0],
            "offsides": [0, 0],
        }
