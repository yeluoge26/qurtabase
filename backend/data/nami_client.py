"""
纳米数据 (Nami Data) Football Client

Base URL: https://open.sportnanoapi.com/api/v5/football/
Auth: user + secret query parameters
Docs: https://www.nami.com/zh/docs

API response: {"code": 0, "results": [...] or {...}}
  code 0 = success

Endpoints used:
  match/schedule/diary — full schedule by date (yyyymmdd), 10min poll
  match/live           — real-time stats/events for last 120min, 2s poll
  recent/match/list    — incremental match changes, 1min poll

Rate limit: 1000 requests/minute per IP
"""

import aiohttp
import time as _time
from datetime import datetime, timedelta
from config import settings


class NamiClient:
    BASE = "https://open.sportnanoapi.com/api/v5/football"

    def __init__(self):
        self.user = settings.NAMI_USER
        self.secret = settings.NAMI_SECRET
        # Cache for team/competition name lookups
        self._team_cache: dict[int, str] = {}
        self._comp_cache: dict[int, str] = {}

    @property
    def available(self) -> bool:
        return bool(self.user and self.secret)

    def _params(self, **extra) -> dict:
        p = {"user": self.user, "secret": self.secret}
        p.update(extra)
        return p

    async def _get(self, path: str, **kwargs) -> list | dict:
        """Core GET request. Returns results (list or dict)."""
        if not self.available:
            return []
        url = f"{self.BASE}/{path}"
        try:
            async with aiohttp.ClientSession() as session:
                params = self._params(**kwargs)
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    data = await resp.json()
                    if data.get("code") != 0:
                        return []
                    return data.get("results", [])
        except Exception:
            return []

    # ── Status mapping ────────────────────────────────────────
    # Nami status_id: 1=未开始 2=上半场 3=中场 4=下半场 5=加时
    # 6=加时(弃用) 7=点球 8=完场 9=推迟 10=中断 11=腰斩
    # 12=取消 13=待定 14=延迟

    STATUS_MAP = {
        1: "Not Started", 2: "1H", 3: "HT", 4: "2H",
        5: "ET", 6: "ET", 7: "Pen", 8: "FT",
        9: "Postponed", 10: "Int", 11: "Abandoned",
        12: "Cancelled", 13: "TBD", 14: "Delayed",
    }

    # Nami stats type mapping
    STAT_TYPE_MAP = {
        1: "corners", 2: "yellow_cards", 3: "red_cards",
        5: "shots_on_target", 6: "shots_off_target",
        7: "attacks", 8: "dangerous_attacks", 9: "possession",
        10: "shots_blocked",
    }

    LIVE_STATUSES = {2, 3, 4, 5, 6, 7}
    FINISHED_STATUSES = {8}
    NOT_STARTED = {1, 13, 14}

    # ── Public API ────────────────────────────────────────────

    async def fetch_live_matches(self) -> list:
        """Fetch all currently live matches.
        Uses schedule/diary for team names + match/live for real-time scores."""
        matches = []

        # 1) Always load schedule first (for team/competition name lookups)
        today = datetime.now().strftime("%Y%m%d")
        sched = await self._get("match/schedule/diary", date=today)
        if isinstance(sched, dict):
            self._update_caches(sched)

        # Build match lookup from schedule (id → match dict)
        sched_by_id: dict[int, dict] = {}
        if isinstance(sched, dict):
            for m in sched.get("match", []):
                sched_by_id[m.get("id", 0)] = m

        # 2) match/live — real-time scores + stats
        live_results = await self._get("match/live")
        live_ids: set[int] = set()

        if isinstance(live_results, list) and live_results:
            for m in live_results:
                mid = m.get("id", 0)
                score_arr = m.get("score", [])
                if not score_arr or len(score_arr) < 4:
                    continue
                status_id = score_arr[1] if len(score_arr) > 1 else 0
                if status_id not in self.LIVE_STATUSES:
                    continue

                live_ids.add(mid)
                home_scores = score_arr[2] if len(score_arr) > 2 else [0]
                away_scores = score_arr[3] if len(score_arr) > 3 else [0]
                kick_time = score_arr[4] if len(score_arr) > 4 else 0
                h_goals = home_scores[0] if home_scores else 0
                a_goals = away_scores[0] if away_scores else 0

                # Get team/league names from schedule lookup
                sm = sched_by_id.get(mid, {})
                home_id = sm.get("home_team_id", 0)
                away_id = sm.get("away_team_id", 0)
                comp_id = sm.get("competition_id", 0)

                matches.append({
                    "id": str(mid),
                    "league": self._comp_cache.get(comp_id, str(comp_id)),
                    "league_key": str(comp_id),
                    "home": self._team_cache.get(home_id, str(home_id)),
                    "away": self._team_cache.get(away_id, str(away_id)),
                    "home_id": str(home_id),
                    "away_id": str(away_id),
                    "score": f"{h_goals} - {a_goals}",
                    "minute": self._calc_minute_from_kick(status_id, kick_time),
                    "status": self.STATUS_MAP.get(status_id, str(status_id)),
                })

        # 3) Add any live matches from schedule not in match/live
        if isinstance(sched, dict):
            for m in sched.get("match", []):
                mid = m.get("id", 0)
                if mid in live_ids:
                    continue
                status_id = m.get("status_id", 0)
                if status_id not in self.LIVE_STATUSES:
                    continue
                home_scores = m.get("home_scores", [0, 0, 0, 0, -1, 0, 0])
                away_scores = m.get("away_scores", [0, 0, 0, 0, -1, 0, 0])
                h_goals = home_scores[0] if home_scores else 0
                a_goals = away_scores[0] if away_scores else 0
                home_id = m.get("home_team_id", 0)
                away_id = m.get("away_team_id", 0)
                comp_id = m.get("competition_id", 0)
                matches.append({
                    "id": str(mid),
                    "league": self._comp_cache.get(comp_id, str(comp_id)),
                    "league_key": str(comp_id),
                    "home": self._team_cache.get(home_id, str(home_id)),
                    "away": self._team_cache.get(away_id, str(away_id)),
                    "home_id": str(home_id),
                    "away_id": str(away_id),
                    "score": f"{h_goals} - {a_goals}",
                    "minute": self._calc_minute_from_match(m),
                    "status": self.STATUS_MAP.get(status_id, str(status_id)),
                })

        return matches

    async def fetch_match(self, match_id: str) -> dict:
        """Fetch full match data including real-time stats and events."""
        m_data = None
        live_data = None

        # 1) Get real-time stats from match/live
        results = await self._get("match/live")
        if isinstance(results, list):
            for item in results:
                if str(item.get("id", "")) == str(match_id):
                    live_data = item
                    break

        # 2) Get match basic info from schedule (for team names etc)
        today = datetime.now().strftime("%Y%m%d")
        sched = await self._get("match/schedule/diary", date=today)
        if isinstance(sched, dict):
            self._update_caches(sched)
            for item in sched.get("match", []):
                if str(item.get("id", "")) == str(match_id):
                    m_data = item
                    break

        # 3) If not found in today, try yesterday
        if not m_data:
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
            sched = await self._get("match/schedule/diary", date=yesterday)
            if isinstance(sched, dict):
                self._update_caches(sched)
                for item in sched.get("match", []):
                    if str(item.get("id", "")) == str(match_id):
                        m_data = item
                        break

        if not m_data and not live_data:
            raise ValueError(f"Match {match_id} not found")

        # Merge data: schedule for team info, live for stats/events
        m = m_data or {}
        home_id = m.get("home_team_id", 0)
        away_id = m.get("away_team_id", 0)
        comp_id = m.get("competition_id", 0)

        # Get scores from live_data or schedule
        if live_data and live_data.get("score"):
            score_arr = live_data["score"]
            status_id = score_arr[1] if len(score_arr) > 1 else m.get("status_id", 0)
            home_scores = score_arr[2] if len(score_arr) > 2 else m.get("home_scores", [0])
            away_scores = score_arr[3] if len(score_arr) > 3 else m.get("away_scores", [0])
            kick_time = score_arr[4] if len(score_arr) > 4 else 0
        else:
            status_id = m.get("status_id", 0)
            home_scores = m.get("home_scores", [0, 0, 0, 0, -1, 0, 0])
            away_scores = m.get("away_scores", [0, 0, 0, 0, -1, 0, 0])
            kick_time = 0

        h_goals = home_scores[0] if home_scores else 0
        a_goals = away_scores[0] if away_scores else 0

        # Calculate minute
        if kick_time and status_id in self.LIVE_STATUSES:
            minute = self._calc_minute_from_kick(status_id, kick_time)
        else:
            minute = self._calc_minute_from_match(m) if m else 0

        home_name = self._team_cache.get(home_id, str(home_id))
        away_name = self._team_cache.get(away_id, str(away_id))
        league_name = self._comp_cache.get(comp_id, str(comp_id))

        # Parse stats from live data
        stats = self._parse_live_stats(live_data.get("stats", []) if live_data else [])
        # Supplement from scores array (red/yellow/corners)
        self._supplement_stats_from_scores(stats, home_scores, away_scores)

        # Parse events from live data
        events = self._parse_live_incidents(live_data.get("incidents", []) if live_data else [])

        # Round info
        round_info = m.get("round", {})
        round_str = str(round_info.get("round_num", "")) if isinstance(round_info, dict) else ""

        return {
            "match": {
                "league": league_name,
                "round": round_str,
                "minute": minute,
                "half": "H1" if minute <= 45 else "H2",
                "home_goals": h_goals,
                "away_goals": a_goals,
                "home_short": home_name[:3].upper(),
                "away_short": away_name[:3].upper(),
                "home_name": home_name,
                "away_name": away_name,
            },
            "stats": stats,
            "events": events,
            "minute": minute,
            "home_goals": h_goals,
            "away_goals": a_goals,
        }

    async def fetch_odds(self, match_id: str) -> dict | None:
        """Fetch pre-match 1X2 odds (requires index data package)."""
        results = await self._get("odds/history", id=match_id)
        if not results:
            return None
        try:
            odds_data = results[0] if isinstance(results, list) else results
            companies = odds_data if isinstance(odds_data, list) else odds_data.get("odds", [])
            if isinstance(companies, list) and companies:
                for company in companies:
                    odds_list = company.get("odds", []) if isinstance(company, dict) else []
                    if odds_list:
                        latest = odds_list[-1] if odds_list else {}
                        home_win = latest.get("home_win") or latest.get("home") or latest.get("h")
                        draw = latest.get("draw") or latest.get("d")
                        away_win = latest.get("away_win") or latest.get("away") or latest.get("a")
                        if home_win and draw and away_win:
                            return {
                                "home": float(home_win),
                                "draw": float(draw),
                                "away": float(away_win),
                            }
            return None
        except (ValueError, TypeError, IndexError, KeyError):
            return None

    async def fetch_trend(self, match_id: str) -> dict | None:
        """Fetch per-minute trend detail for a match.
        GET match/trend/detail?id={match_id}
        Actual response: {count, per, data: [[momentum_values...], ...], incidents: [...]}
        data: array of halves, each half is array of momentum values per minute
          positive = home dominant, negative = away dominant
        incidents: [{type, time, position}]
          type: 1=goal, 2=corner, 3=yellow, 4=red, 5=sub, 7=pen, 8=OG
        """
        results = await self._get("match/trend/detail", id=match_id)
        if not results:
            return None
        if isinstance(results, list):
            results = results[0] if results else {}

        trend = results if isinstance(results, dict) else {}

        # Parse momentum data: flatten halves into per-minute timeline
        half_data = trend.get("data", [])
        per = trend.get("per", 45)
        momentum = []
        minute_offset = 0
        for half_idx, half in enumerate(half_data):
            if not isinstance(half, list):
                continue
            for i, val in enumerate(half):
                minute = minute_offset + i + 1
                momentum.append({
                    "minute": minute,
                    "value": val,  # positive=home, negative=away
                })
            minute_offset += per

        # Parse incidents from trend
        trend_incidents = trend.get("incidents", [])
        incidents = []
        for inc in trend_incidents:
            if not isinstance(inc, dict):
                continue
            incidents.append({
                "type": inc.get("type", 0),
                "time": int(inc.get("time", 0) or 0),
                "position": inc.get("position", 0),
            })

        return {
            "momentum": momentum,
            "incidents": incidents,
        }

    # Position string mapping: Nami uses "G"/"D"/"M"/"F"
    POS_STR_MAP = {"G": "GK", "D": "DF", "M": "MF", "F": "FW"}

    async def fetch_lineup(self, match_id: str) -> dict | None:
        """Fetch lineup details for a match.
        GET match/lineup/detail?id={match_id}
        Actual response: {confirmed, home_formation, away_formation,
          home_coach_id, away_coach_id, home_color, away_color,
          home: [players...], away: [players...]}
        Player: {id, team_id, first, captain, name, logo, shirt_number,
          position ("G"/"D"/"M"/"F"), x, y, rating}
        """
        results = await self._get("match/lineup/detail", id=match_id)
        if not results:
            return None
        if isinstance(results, list):
            results = results[0] if results else {}

        lineup = results if isinstance(results, dict) else {}

        home_formation = lineup.get("home_formation", "")
        away_formation = lineup.get("away_formation", "")
        confirmed = lineup.get("confirmed", 0)
        home_lineup = lineup.get("home", [])
        away_lineup = lineup.get("away", [])

        def parse_players(player_list):
            players = []
            if not isinstance(player_list, list):
                return players
            for p in player_list:
                if not isinstance(p, dict):
                    continue
                pos_str = p.get("position", "")
                players.append({
                    "id": p.get("id", 0),
                    "name": p.get("name", ""),
                    "shirt_number": p.get("shirt_number", 0),
                    "position": self.POS_STR_MAP.get(pos_str, pos_str),
                    "first": p.get("first", 0),  # 1=starting, 0=bench
                    "x": p.get("x", 0),
                    "y": p.get("y", 0),
                    "rating": p.get("rating", "0.0"),
                    "is_captain": p.get("captain", 0) == 1,
                    "incidents": self._parse_player_incidents(p.get("incidents", [])),
                })
            return players

        return {
            "home_formation": home_formation,
            "away_formation": away_formation,
            "confirmed": confirmed == 1,
            "home": parse_players(home_lineup),
            "away": parse_players(away_lineup),
        }

    def _parse_player_incidents(self, incidents: list) -> list:
        """Parse player-level incidents (goals, cards, subs)."""
        result = []
        if not isinstance(incidents, list):
            return result
        for inc in incidents:
            if not isinstance(inc, dict):
                continue
            result.append({
                "type": inc.get("type", 0),
                "time": inc.get("time", 0),
            })
        return result

    async def fetch_h2h(self, home_team_id: str, away_team_id: str) -> dict:
        return {"h2h": [], "home_results": [], "away_results": []}

    async def fetch_fixtures_by_date(self, date_from: str, date_to: str,
                                     league_id: str = None) -> list:
        """Fetch fixtures for a date range. Returns AllSportsApi-compatible format."""
        all_fixtures = []

        start = datetime.strptime(date_from, "%Y-%m-%d")
        end = datetime.strptime(date_to, "%Y-%m-%d")
        day = start
        while day <= end:
            date_str = day.strftime("%Y%m%d")  # yyyymmdd format
            results = await self._get("match/schedule/diary", date=date_str)
            if isinstance(results, dict):
                self._update_caches(results)
                for m in results.get("match", []):
                    comp_id = str(m.get("competition_id", ""))
                    if league_id and comp_id != league_id:
                        continue
                    all_fixtures.append(self._to_allsports_format(m))
            day += timedelta(days=1)

        return all_fixtures

    async def fetch_latest_finished(self, league_ids: list = None) -> dict | None:
        """Fetch the most recently finished match."""
        today = datetime.now().strftime("%Y%m%d")
        results = await self._get("match/schedule/diary", date=today)
        if isinstance(results, dict):
            self._update_caches(results)
            matches = results.get("match", [])
        else:
            matches = []

        finished = [m for m in matches if m.get("status_id") in self.FINISHED_STATUSES]
        if league_ids:
            filtered = [m for m in finished
                        if str(m.get("competition_id", "")) in league_ids]
            if filtered:
                finished = filtered
        if finished:
            return self._to_summary(finished[-1])

        # Try yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        results = await self._get("match/schedule/diary", date=yesterday)
        if isinstance(results, dict):
            self._update_caches(results)
            matches = results.get("match", [])
            finished = [m for m in matches if m.get("status_id") in self.FINISHED_STATUSES]
            if league_ids:
                filtered = [m for m in finished
                            if str(m.get("competition_id", "")) in league_ids]
                if filtered:
                    finished = filtered
            if finished:
                return self._to_summary(finished[-1])

        return None

    # ── Cache helpers ─────────────────────────────────────────

    def _update_caches(self, results: dict):
        """Update team/competition name caches from schedule response."""
        for comp in results.get("competition", []):
            cid = comp.get("id", 0)
            name = comp.get("name", "")
            if cid and name:
                self._comp_cache[cid] = name
        for team in results.get("team", []):
            tid = team.get("id", 0)
            name = team.get("name", "")
            if tid and name:
                self._team_cache[tid] = name

    # ── Format converters ─────────────────────────────────────

    def _to_allsports_format(self, m: dict) -> dict:
        """Convert Nami match to AllSportsApi-compatible fixture format.
        home_scores: [score, half_score, red, yellow, corner, et_score, pen_score]"""
        home_scores = m.get("home_scores", [0, 0, 0, 0, -1, 0, 0])
        away_scores = m.get("away_scores", [0, 0, 0, 0, -1, 0, 0])
        h_goals = home_scores[0] if len(home_scores) > 0 else 0
        a_goals = away_scores[0] if len(away_scores) > 0 else 0
        status_id = m.get("status_id", 0)

        home_id = m.get("home_team_id", 0)
        away_id = m.get("away_team_id", 0)
        comp_id = m.get("competition_id", 0)

        status_str = self.STATUS_MAP.get(status_id, "")
        if status_id == 1:
            status_str = ""

        match_time = m.get("match_time", 0)
        date_str = ""
        time_str = ""
        if match_time:
            try:
                dt = datetime.fromtimestamp(match_time)
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%H:%M")
            except (ValueError, OSError):
                pass

        round_info = m.get("round", {})
        round_str = str(round_info.get("round_num", "")) if isinstance(round_info, dict) else ""

        return {
            "event_key": str(m.get("id", "")),
            "league_name": self._comp_cache.get(comp_id, str(comp_id)),
            "league_key": str(comp_id),
            "event_home_team": self._team_cache.get(home_id, str(home_id)),
            "event_away_team": self._team_cache.get(away_id, str(away_id)),
            "home_team_key": str(home_id),
            "away_team_key": str(away_id),
            "event_final_result": f"{h_goals} - {a_goals}",
            "event_status": status_str,
            "event_date": date_str,
            "event_time": time_str,
            "league_round": round_str,
            "country_name": "",
        }

    def _to_summary(self, m: dict) -> dict:
        """Convert Nami match to summary dict."""
        f = self._to_allsports_format(m)
        score = f["event_final_result"]
        parts = score.replace(" ", "").split("-")
        h_goals = int(parts[0]) if parts[0].isdigit() else 0
        a_goals = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        return {
            "id": f["event_key"],
            "league": f["league_name"],
            "league_key": f["league_key"],
            "round": f["league_round"],
            "home": f["event_home_team"],
            "away": f["event_away_team"],
            "home_id": f["home_team_key"],
            "away_id": f["away_team_key"],
            "score": score,
            "home_goals": h_goals,
            "away_goals": a_goals,
            "minute": 90,
            "status": "Finished",
            "date": f["event_date"],
            "time": f["event_time"],
            "country": f["country_name"],
        }

    # ── Parsers ───────────────────────────────────────────────

    def _calc_minute_from_kick(self, status_id: int, kick_time: int) -> int:
        """Calculate minute using kick-off timestamp.
        1H: (now - kick_time) / 60 + 1
        2H: (now - kick_time) / 60 + 45 + 1"""
        if not kick_time:
            return 0
        if status_id == 3:  # HT
            return 45
        if status_id in self.FINISHED_STATUSES:
            return 90
        if status_id not in self.LIVE_STATUSES:
            return 0

        elapsed = (_time.time() - kick_time) / 60
        if status_id == 2:  # 1H
            return max(1, min(int(elapsed) + 1, 45))
        elif status_id == 4:  # 2H
            return max(46, min(int(elapsed) + 46, 90))
        elif status_id in (5, 6):  # ET
            return max(91, min(int(elapsed) + 91, 120))
        return max(1, int(elapsed) + 1)

    def _calc_minute_from_match(self, m: dict) -> int:
        """Calculate minute from match data when no kick_time available."""
        status_id = m.get("status_id", 0)
        if status_id == 3:
            return 45
        if status_id in self.FINISHED_STATUSES:
            return 90
        if status_id not in self.LIVE_STATUSES:
            return 0
        # Estimate from match_time
        match_time = m.get("match_time", 0)
        if match_time and status_id in self.LIVE_STATUSES:
            elapsed = (_time.time() - match_time) / 60
            if status_id == 2:
                return max(1, min(int(elapsed), 45))
            elif status_id == 4:
                return max(46, min(45 + int(elapsed - 60), 90))
            return max(1, int(elapsed))
        return 0

    def _parse_live_stats(self, stats_data: list) -> dict:
        """Parse match/live stats array into standard format.
        Each stat: {type: int, home: int, away: int}
        Confirmed type mapping from live API:
          2=黄牌  3=红牌  4=点球
          8=危险进攻  21=射门  22=射正  23=射偏
          24=角球  25=控球率  37=进攻
        """
        result = self._empty_stats()
        if not stats_data or not isinstance(stats_data, list):
            return result

        for s in stats_data:
            if not isinstance(s, dict):
                continue
            stype = s.get("type", 0)
            home_val = s.get("home", 0) or 0
            away_val = s.get("away", 0) or 0

            if stype == 2:
                result["yellow_cards"] = [home_val, away_val]
            elif stype == 3:
                result["red_cards"] = [home_val, away_val]
            elif stype == 8:
                result["dangerous_attacks"] = [home_val, away_val]
            elif stype == 21:
                result["shots"] = [home_val, away_val]
            elif stype == 22:
                result["shots_on_target"] = [home_val, away_val]
            elif stype == 23:
                result["shots_off_target"] = [home_val, away_val]
            elif stype == 24:
                result["corners"] = [home_val, away_val]
            elif stype == 25:
                result["possession"] = [home_val or 50, away_val or 50]
            elif stype == 37:
                result["attacks"] = [home_val, away_val]

        # Calculate total shots if not set
        if result["shots"] == [0, 0] and (result["shots_on_target"] != [0, 0] or result["shots_off_target"] != [0, 0]):
            result["shots"] = [
                result["shots_on_target"][0] + result["shots_off_target"][0],
                result["shots_on_target"][1] + result["shots_off_target"][1],
            ]

        # Estimate xG
        if result["shots_on_target"][0] > 0 or result["shots_on_target"][1] > 0:
            result["xg"] = self._estimate_xg(result)

        return result

    def _supplement_stats_from_scores(self, stats: dict, home_scores: list, away_scores: list):
        """Fill in stats from scores array if not already set.
        scores: [score, half_score, red, yellow, corner, et_score, pen_score]"""
        if len(home_scores) >= 5 and len(away_scores) >= 5:
            if stats["red_cards"] == [0, 0]:
                hr = home_scores[2] if len(home_scores) > 2 else 0
                ar = away_scores[2] if len(away_scores) > 2 else 0
                if hr or ar:
                    stats["red_cards"] = [hr, ar]
            if stats["yellow_cards"] == [0, 0]:
                hy = home_scores[3] if len(home_scores) > 3 else 0
                ay = away_scores[3] if len(away_scores) > 3 else 0
                if hy or ay:
                    stats["yellow_cards"] = [hy, ay]
            if stats["corners"] == [0, 0]:
                hc = home_scores[4] if len(home_scores) > 4 else -1
                ac = away_scores[4] if len(away_scores) > 4 else -1
                if hc >= 0 and ac >= 0:
                    stats["corners"] = [hc, ac]

    def _parse_live_incidents(self, incidents: list) -> list:
        """Parse match/live incidents into unified events list.
        Each incident: {type, position, time, player_name, ...}
        type mapping from Nami docs:
          1=进球 2=角球 3=黄牌 4=红牌 5=换人 7=点球 8=乌龙球
          9=助攻 11=两黄变红 15=VAR 16=点球未进
          21=中场 22=伤停补时 23=结束 24=加时结束 25=点球大战结束
        """
        events = []
        if not incidents or not isinstance(incidents, list):
            return events

        for inc in incidents:
            if not isinstance(inc, dict):
                continue
            try:
                minute = int(inc.get("time", 0) or 0)
                inc_type = inc.get("type", 0)
                position = inc.get("position", 0)
                team = "HOME" if position == 1 else "AWAY"
                player = inc.get("player_name", "") or ""

                if inc_type in (1, 7, 8):  # goal, penalty, own goal
                    label = "GOAL"
                    if inc_type == 7:
                        label = "GOAL (PEN)"
                    elif inc_type == 8:
                        label = "GOAL (OG)"
                    events.append({
                        "id": f"g{minute}{team[0]}",
                        "minute": minute,
                        "type": "GOAL",
                        "team": team,
                        "text": f"{label} — {player}" if player else label,
                    })
                elif inc_type == 16:  # penalty missed
                    events.append({
                        "id": f"pm{minute}{team[0]}",
                        "minute": minute,
                        "type": "PENALTY_MISS",
                        "team": team,
                        "text": f"PEN MISS — {player}" if player else "PEN MISS",
                    })
                elif inc_type in (3, 11):  # yellow, second yellow
                    events.append({
                        "id": f"c{minute}{team[0]}",
                        "minute": minute,
                        "type": "YELLOW",
                        "team": team,
                        "text": f"YELLOW — {player}" if player else "YELLOW",
                    })
                elif inc_type == 4:  # red
                    events.append({
                        "id": f"c{minute}{team[0]}",
                        "minute": minute,
                        "type": "RED",
                        "team": team,
                        "text": f"RED — {player}" if player else "RED",
                    })
                elif inc_type == 5:  # substitution
                    events.append({
                        "id": f"s{minute}{team[0]}",
                        "minute": minute,
                        "type": "SUB",
                        "team": team,
                        "text": f"SUB — {player}" if player else "SUB",
                    })
                elif inc_type == 15:  # VAR
                    var_reason = inc.get("var_reason", 0)
                    var_result = inc.get("var_result", 0)
                    events.append({
                        "id": f"v{minute}",
                        "minute": minute,
                        "type": "VAR",
                        "team": team,
                        "text": f"VAR — Review",
                    })
            except Exception:
                continue

        return sorted(events, key=lambda x: x["minute"], reverse=True)

    @staticmethod
    def _estimate_xg(stats: dict) -> list:
        sot = stats.get("shots_on_target", [0, 0])
        da = stats.get("dangerous_attacks", [0, 0])
        shots = stats.get("shots", [0, 0])
        xg = [0.0, 0.0]
        for i in range(2):
            base = sot[i] * 0.10
            if shots[i] > 0 and da[i] > 0:
                quality = min(1.5, 0.8 + (da[i] / max(shots[i] * 5, 1)) * 0.7)
                base *= quality
            xg[i] = round(base, 2)
        return xg

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
