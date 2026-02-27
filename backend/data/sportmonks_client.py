"""
SportMonks Football API Client (v3)

Fetches live match data from SportMonks.
Base URL: https://api.sportmonks.com/v3/football
Auth: api_token query parameter
"""

import aiohttp
from config import settings


class SportMonksClient:
    BASE = "https://api.sportmonks.com/v3/football"

    def __init__(self):
        self.api_key = settings.SPORTMONKS_API_KEY

    def _params(self, **extra) -> dict:
        p = {"api_token": self.api_key}
        p.update(extra)
        return p

    async def fetch_live_matches(self) -> list:
        """Fetch all currently live (in-play) fixtures."""
        if not self.api_key:
            return []

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE}/livescores/inplay"
                params = self._params(include="scores;participants;statistics.type;events")
                async with session.get(url, params=params) as resp:
                    data = await resp.json()

                results = []
                for fix in data.get("data", []):
                    participants = fix.get("participants", [])
                    home = next((p for p in participants if p.get("meta", {}).get("location") == "home"), {})
                    away = next((p for p in participants if p.get("meta", {}).get("location") == "away"), {})

                    scores = fix.get("scores", [])
                    h_goals, a_goals = self._extract_score(scores)

                    results.append({
                        "id": str(fix["id"]),
                        "league": fix.get("league", {}).get("name", ""),
                        "home": home.get("name", "Home"),
                        "away": away.get("name", "Away"),
                        "home_id": home.get("id"),
                        "away_id": away.get("id"),
                        "score": f"{h_goals}-{a_goals}",
                        "minute": fix.get("minute", 0) or 0,
                        "state_id": fix.get("state_id"),
                    })
                return results
        except Exception:
            return []

    async def fetch_match(self, fixture_id: str) -> dict:
        """Fetch full match data for a specific fixture."""
        if not self.api_key:
            raise ValueError("No SportMonks API key configured")

        async with aiohttp.ClientSession() as session:
            url = f"{self.BASE}/fixtures/{fixture_id}"
            params = self._params(include="scores;participants;statistics.type;events")
            async with session.get(url, params=params) as resp:
                data = await resp.json()

            fix = data.get("data")
            if not fix:
                raise ValueError(f"Fixture {fixture_id} not found or no access")

            participants = fix.get("participants", [])
            home = next((p for p in participants if p.get("meta", {}).get("location") == "home"), {})
            away = next((p for p in participants if p.get("meta", {}).get("location") == "away"), {})

            scores = fix.get("scores", [])
            h_goals, a_goals = self._extract_score(scores)

            stats = self._parse_stats(fix.get("statistics", []), home.get("id"), away.get("id"))
            events = self._parse_events(fix.get("events", []))

            minute = fix.get("minute", 0) or 0

            return {
                "match": {
                    "league": "",
                    "round": "",
                    "minute": minute,
                    "half": "H1" if minute <= 45 else "H2",
                    "home_goals": h_goals,
                    "away_goals": a_goals,
                    "home_short": home.get("short_code", home.get("name", "HOM")[:3].upper()),
                    "away_short": away.get("short_code", away.get("name", "AWY")[:3].upper()),
                    "home_name": home.get("name", "Home"),
                    "away_name": away.get("name", "Away"),
                },
                "stats": stats,
                "events": events,
                "minute": minute,
                "home_goals": h_goals,
                "away_goals": a_goals,
            }

    def _extract_score(self, scores: list) -> tuple:
        """Extract current score from SportMonks scores array."""
        h, a = 0, 0
        # scores are broken into periods; use the "current" or highest period
        for s in scores:
            desc = s.get("description", "")
            participant = s.get("score", {}).get("participant", "")
            goals = s.get("score", {}).get("goals", 0) or 0
            if desc == "CURRENT":
                if participant == "home":
                    h = goals
                elif participant == "away":
                    a = goals
        # Fallback: sum up period scores
        if h == 0 and a == 0:
            for s in scores:
                desc = s.get("description", "")
                if desc in ("1ST_HALF", "2ND_HALF"):
                    participant = s.get("score", {}).get("participant", "")
                    goals = s.get("score", {}).get("goals", 0) or 0
                    if participant == "home":
                        h += goals
                    elif participant == "away":
                        a += goals
        return h, a

    def _parse_stats(self, statistics: list, home_id: int | None, away_id: int | None) -> dict:
        """Parse SportMonks statistics into our flat format."""
        result = self._empty_stats()
        if not statistics:
            return result

        # SportMonks stats: each item has type.code and participant_id
        home_stats = {}
        away_stats = {}
        for s in statistics:
            pid = s.get("participant_id")
            type_info = s.get("type", {})
            code = type_info.get("code", "") if isinstance(type_info, dict) else ""
            value = s.get("data", {}).get("value", 0) if isinstance(s.get("data"), dict) else 0
            if pid == home_id:
                home_stats[code] = value
            elif pid == away_id:
                away_stats[code] = value

        def g(d, key, default=0):
            v = d.get(key, default)
            if v is None:
                return default
            if isinstance(v, str):
                return int(v.replace("%", "")) if v.replace("%", "").isdigit() else default
            return v

        result["shots"] = [g(home_stats, "shots-total"), g(away_stats, "shots-total")]
        result["shots_on_target"] = [g(home_stats, "shots-on-target"), g(away_stats, "shots-on-target")]
        result["possession"] = [g(home_stats, "ball-possession", 50), g(away_stats, "ball-possession", 50)]
        result["corners"] = [g(home_stats, "corners"), g(away_stats, "corners")]
        result["fouls"] = [g(home_stats, "fouls"), g(away_stats, "fouls")]
        result["yellow_cards"] = [g(home_stats, "yellowcards"), g(away_stats, "yellowcards")]
        result["red_cards"] = [g(home_stats, "redcards"), g(away_stats, "redcards")]
        result["offsides"] = [g(home_stats, "offsides"), g(away_stats, "offsides")]
        result["saves"] = [g(home_stats, "saves"), g(away_stats, "saves")]
        result["dangerous_attacks"] = [g(home_stats, "dangerous-attacks"), g(away_stats, "dangerous-attacks")]
        result["attacks"] = [g(home_stats, "attacks"), g(away_stats, "attacks")]
        result["pass_accuracy"] = [g(home_stats, "passes-accuracy", 80), g(away_stats, "passes-accuracy", 80)]

        # xG may not be available on all plans
        result["xg"] = [
            float(home_stats.get("expected-goals", 0) or 0),
            float(away_stats.get("expected-goals", 0) or 0),
        ]

        return result

    def _parse_events(self, events: list) -> list:
        """Parse SportMonks events into our format."""
        result = []
        # SportMonks event type_id mapping
        TYPE_MAP = {
            14: "GOAL", 15: "GOAL", 16: "GOAL",  # goal, own-goal, penalty-goal
            17: "PENALTY",  # missed penalty
            19: "YELLOW",
            20: "RED",
            18: "SUB",
            24: "VAR",
        }
        for ev in events:
            type_id = ev.get("type_id", 0)
            ev_type = TYPE_MAP.get(type_id, "OTHER")
            if ev_type == "OTHER":
                continue
            minute = ev.get("minute", 0) or 0
            player = ev.get("player_name", "")
            result.append({
                "id": str(ev.get("id", "")),
                "minute": minute,
                "type": ev_type,
                "team": "HOME" if ev.get("section") == "home" else "AWAY",
                "text": f"{ev_type} — {player}" if player else ev_type,
            })
        return sorted(result, key=lambda x: x["minute"], reverse=True)

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
            "yellow_cards": [0, 0],
            "red_cards": [0, 0],
            "attacks": [0, 0],
            "saves": [0, 0],
            "offsides": [0, 0],
        }
