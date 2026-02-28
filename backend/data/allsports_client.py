"""
AllSportsApi Football Client

Base URL: https://apiv2.allsportsapi.com/football/
Auth: APIkey query parameter
Docs: https://allsportsapi.com/soccer-football-api-documentation

Free plan: 2 random leagues, 260 calls/hour, no odds
European plan ($74/mo): 42 leagues + UCL/UEL, 2000 calls/hour
World Wide ($111/mo): 800+ leagues, includes odds
Ultimate ($149/mo): 800+ leagues, live odds, WebSocket, 100k calls/hour
"""

import aiohttp
from config import settings


class AllSportsClient:
    BASE = "https://apiv2.allsportsapi.com/football"

    def __init__(self):
        self.api_key = settings.ALLSPORTS_API_KEY

    def _params(self, met: str, **extra) -> dict:
        p = {"met": met, "APIkey": self.api_key}
        p.update(extra)
        return p

    async def _get(self, met: str, **kwargs) -> list | dict:
        if not self.api_key:
            return []
        try:
            async with aiohttp.ClientSession() as session:
                params = self._params(met, **kwargs)
                async with session.get(self.BASE, params=params) as resp:
                    data = await resp.json()
                    if data.get("success") != 1:
                        return []
                    return data.get("result", [])
        except Exception:
            return []

    # ── Public API ──────────────────────────────────────────

    async def fetch_live_matches(self) -> list:
        """Fetch all currently live matches."""
        results = await self._get("Livescore")
        if not isinstance(results, list):
            return []

        matches = []
        for ev in results:
            status = ev.get("event_status", "")
            if not status or status in ("Finished", "After Pen.", "Cancelled", "Postponed", ""):
                continue
            matches.append({
                "id": str(ev.get("event_key", "")),
                "league": ev.get("league_name", ""),
                "league_key": ev.get("league_key"),
                "home": ev.get("event_home_team", "Home"),
                "away": ev.get("event_away_team", "Away"),
                "home_id": ev.get("home_team_key"),
                "away_id": ev.get("away_team_key"),
                "score": ev.get("event_final_result", "0 - 0"),
                "minute": self._parse_minute(status),
                "status": status,
            })
        return matches

    async def fetch_match(self, match_id: str) -> dict:
        """Fetch full match data for a specific fixture."""
        results = await self._get("Livescore", matchId=match_id)
        if not results:
            # Fallback: try Fixtures endpoint
            results = await self._get(
                "Fixtures", matchId=match_id,
                **{"from": "2026-01-01", "to": "2026-12-31"}
            )
        if not results or not isinstance(results, list):
            raise ValueError(f"Match {match_id} not found")

        ev = results[0]
        stats = self._parse_stats(ev.get("statistics", []))
        events = self._parse_events(ev)
        status = ev.get("event_status", "")
        minute = self._parse_minute(status)

        score = ev.get("event_final_result", "0 - 0")
        parts = score.replace(" ", "").split("-")
        h_goals = int(parts[0]) if parts[0].isdigit() else 0
        a_goals = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0

        return {
            "match": {
                "league": ev.get("league_name", ""),
                "round": ev.get("league_round", ""),
                "minute": minute,
                "half": "H1" if minute <= 45 else "H2",
                "home_goals": h_goals,
                "away_goals": a_goals,
                "home_short": ev.get("event_home_team", "HOM")[:3].upper(),
                "away_short": ev.get("event_away_team", "AWY")[:3].upper(),
                "home_name": ev.get("event_home_team", "Home"),
                "away_name": ev.get("event_away_team", "Away"),
            },
            "stats": stats,
            "events": events,
            "minute": minute,
            "home_goals": h_goals,
            "away_goals": a_goals,
        }

    async def fetch_odds(self, match_id: str) -> dict | None:
        """Fetch pre-match odds (requires World Wide plan+)."""
        results = await self._get("Odds", matchId=match_id)
        if not results or not isinstance(results, dict):
            return None

        # AllSportsApi odds format: {"odd_1": "1.85", "odd_x": "3.50", "odd_2": "4.20", ...}
        try:
            return {
                "home": float(results.get("odd_1", 0)),
                "draw": float(results.get("odd_x", 0)),
                "away": float(results.get("odd_2", 0)),
            }
        except (ValueError, TypeError):
            return None

    async def fetch_h2h(self, home_team_id: str, away_team_id: str) -> dict:
        """Fetch head-to-head record."""
        results = await self._get(
            "H2H", firstTeamId=home_team_id, secondTeamId=away_team_id
        )
        if not results or not isinstance(results, dict):
            return {"h2h": [], "home_results": [], "away_results": []}

        return {
            "h2h": results.get("H2H", [])[:10],
            "home_results": results.get("firstTeamResults", [])[:5],
            "away_results": results.get("secondTeamResults", [])[:5],
        }

    async def fetch_fixtures_by_date(self, date_from: str, date_to: str,
                                     league_id: str = None) -> list:
        """Fetch fixtures for a date range."""
        kwargs = {"from": date_from, "to": date_to}
        if league_id:
            kwargs["leagueId"] = league_id
        results = await self._get("Fixtures", **kwargs)
        if not isinstance(results, list):
            return []
        return results

    async def fetch_latest_finished(self, league_ids: list = None) -> dict | None:
        """Fetch the most recently finished match.
        Tries livescore first (for just-finished), then today's fixtures."""
        from datetime import datetime, timedelta

        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # 1) Check livescore for just-finished matches
        results = await self._get("Livescore")
        if isinstance(results, list):
            finished = [ev for ev in results
                        if ev.get("event_status", "") in ("Finished", "After Pen.", "After ET")]
            if league_ids:
                filtered = [ev for ev in finished
                            if str(ev.get("league_key", "")) in league_ids]
                if filtered:
                    finished = filtered
            if finished:
                # Return the last one (most recent)
                ev = finished[-1]
                return self._ev_to_summary(ev)

        # 2) Fallback: yesterday + today fixtures, find finished
        for date_range in [(today, today), (yesterday, today)]:
            results = await self._get("Fixtures", **{"from": date_range[0], "to": date_range[1]})
            if isinstance(results, list):
                finished = [ev for ev in results
                            if ev.get("event_status", "") in ("Finished", "After Pen.", "After ET")]
                if league_ids:
                    filtered = [ev for ev in finished
                                if str(ev.get("league_key", "")) in league_ids]
                    if filtered:
                        finished = filtered
                if finished:
                    ev = finished[-1]
                    return self._ev_to_summary(ev)

        return None

    def _ev_to_summary(self, ev: dict) -> dict:
        """Convert an AllSportsApi event to a summary dict."""
        status = ev.get("event_status", "")
        score = ev.get("event_final_result", "0 - 0")
        parts = score.replace(" ", "").split("-")
        h_goals = int(parts[0]) if parts[0].isdigit() else 0
        a_goals = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        return {
            "id": str(ev.get("event_key", "")),
            "league": ev.get("league_name", ""),
            "league_key": str(ev.get("league_key", "")),
            "round": ev.get("league_round", ""),
            "home": ev.get("event_home_team", "Home"),
            "away": ev.get("event_away_team", "Away"),
            "home_id": ev.get("home_team_key"),
            "away_id": ev.get("away_team_key"),
            "score": score,
            "home_goals": h_goals,
            "away_goals": a_goals,
            "minute": self._parse_minute(status),
            "status": status,
            "date": ev.get("event_date", ""),
            "time": ev.get("event_time", ""),
            "country": ev.get("country_name", ""),
        }

    # ── Parsers ─────────────────────────────────────────────

    def _parse_minute(self, status: str) -> int:
        """Parse minute from event_status (e.g. '45', '67', 'Half Time', 'Finished')."""
        if not status:
            return 0
        s = status.strip()
        if s.isdigit():
            return int(s)
        if s == "Half Time":
            return 45
        if s in ("Finished", "After Pen.", "After ET"):
            return 90
        # Try to extract number from status like "45+2"
        for c in s:
            if not c.isdigit() and c != "+":
                return 0
        try:
            return int(s.split("+")[0])
        except (ValueError, IndexError):
            return 0

    def _parse_stats(self, statistics: list) -> dict:
        """Parse AllSportsApi statistics array into our format."""
        result = self._empty_stats()
        if not statistics:
            return result

        # AllSportsApi stats format:
        # [{"type": "Ball Possession", "home": "55%", "away": "45%"}, ...]
        stat_map = {}
        for s in statistics:
            stat_type = s.get("type", "")
            stat_map[stat_type] = s

        def g(stat_type: str, side: str, default=0):
            s = stat_map.get(stat_type, {})
            v = s.get(side, default)
            if v is None:
                return default
            if isinstance(v, str):
                v = v.strip().replace("%", "")
                return int(v) if v.isdigit() else default
            return int(v)

        result["shots"] = [g("Shots Total", "home"), g("Shots Total", "away")]
        result["shots_on_target"] = [g("Shots On Target", "home"), g("Shots On Target", "away")]
        result["shots_off_target"] = [g("Shots Off Target", "home"), g("Shots Off Target", "away")]
        result["possession"] = [g("Ball Possession", "home", 50), g("Ball Possession", "away", 50)]
        result["corners"] = [g("Corners", "home"), g("Corners", "away")]
        result["fouls"] = [g("Fouls", "home"), g("Fouls", "away")]
        result["yellow_cards"] = [g("Yellow Cards", "home"), g("Yellow Cards", "away")]
        result["red_cards"] = [g("Red Cards", "home"), g("Red Cards", "away")]
        result["offsides"] = [g("Offsides", "home"), g("Offsides", "away")]
        result["saves"] = [g("Goalkeeper Saves", "home"), g("Goalkeeper Saves", "away")]
        result["dangerous_attacks"] = [g("Attacks", "home"), g("Attacks", "away")]
        result["pass_accuracy"] = [g("Passes Accurate", "home", 80), g("Passes Accurate", "away", 80)]

        return result

    def _parse_events(self, ev: dict) -> list:
        """Parse goalscorers + cards + substitutes into unified events list.
        Robust against varying API data formats across leagues."""
        events = []

        # Goals
        for g in ev.get("goalscorers", []) or []:
            try:
                if not isinstance(g, dict):
                    continue
                minute = self._parse_event_minute(g.get("time", ""))
                scorer = g.get("home_scorer", "") or g.get("away_scorer", "")
                team = "HOME" if g.get("home_scorer") else "AWAY"
                events.append({
                    "id": f"g{minute}{team[0]}",
                    "minute": minute,
                    "type": "GOAL",
                    "team": team,
                    "text": f"GOAL — {scorer}" if scorer else "GOAL",
                })
            except Exception:
                continue

        # Cards
        for c in ev.get("cards", []) or []:
            try:
                if not isinstance(c, dict):
                    continue
                minute = self._parse_event_minute(c.get("time", ""))
                card_type = c.get("card", "yellow card")
                player = c.get("home_fault", "") or c.get("away_fault", "")
                team = "HOME" if c.get("home_fault") else "AWAY"
                ev_type = "RED" if "red" in str(card_type).lower() else "YELLOW"
                events.append({
                    "id": f"c{minute}{team[0]}",
                    "minute": minute,
                    "type": ev_type,
                    "team": team,
                    "text": f"{ev_type} — {player}" if player else ev_type,
                })
            except Exception:
                continue

        # Substitutions
        for s in ev.get("substitutes", []) or []:
            try:
                if not isinstance(s, dict):
                    continue
                minute = self._parse_event_minute(s.get("time", ""))
                sub_in = ""
                for key in ("home_scorer", "away_scorer"):
                    val = s.get(key)
                    if isinstance(val, dict):
                        sub_in = val.get("in", "")
                    elif isinstance(val, str) and val:
                        sub_in = val
                    if sub_in:
                        break
                team = "HOME" if s.get("home_scorer") else "AWAY"
                events.append({
                    "id": f"s{minute}{team[0]}",
                    "minute": minute,
                    "type": "SUB",
                    "team": team,
                    "text": f"SUB — {sub_in}" if sub_in else "SUB",
                })
            except Exception:
                continue

        # VAR decisions
        for v in ev.get("vars", []) or []:
            try:
                if not isinstance(v, dict):
                    continue
                minute = self._parse_event_minute(v.get("time", ""))
                events.append({
                    "id": f"v{minute}",
                    "minute": minute,
                    "type": "VAR",
                    "team": "HOME" if v.get("home_team") else "AWAY",
                    "text": f"VAR — {v.get('info', 'Review')}",
                })
            except Exception:
                continue

        return sorted(events, key=lambda x: x["minute"], reverse=True)

    def _parse_event_minute(self, time_str: str) -> int:
        """Parse event time string like '45+2' or '67' into integer minute."""
        if not time_str:
            return 0
        try:
            return int(str(time_str).split("+")[0].strip().replace("'", ""))
        except (ValueError, IndexError):
            return 0

    @staticmethod
    def _empty_stats() -> dict:
        return {
            "shots": [0, 0],
            "shots_on_target": [0, 0],
            "shots_off_target": [0, 0],
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
