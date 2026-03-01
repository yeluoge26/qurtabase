"""
纳米数据 (Nami Data) Football Client

Base URL: https://open.sportnanoapi.com/api/v5/football/
Auth: user + secret query parameters
Docs: https://www.nami.com/zh/docs

API response: {"code": 0, "results": [...]}
  code 0 = success, 404 = not found, 9999 = unknown error

Rate limit: 1000 requests/minute per IP
Polling recommendation: 20s for match changes, 10min for full schedule
"""

import aiohttp
from datetime import datetime
from config import settings


class NamiClient:
    BASE = "https://open.sportnanoapi.com/api/v5/football"

    def __init__(self):
        self.user = settings.NAMI_USER
        self.secret = settings.NAMI_SECRET

    @property
    def available(self) -> bool:
        return bool(self.user and self.secret)

    def _params(self, **extra) -> dict:
        p = {"user": self.user, "secret": self.secret}
        p.update(extra)
        return p

    async def _get(self, path: str, **kwargs) -> list | dict:
        """Core GET request. Returns results array or dict."""
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
        1: "Not Started",
        2: "1H",
        3: "HT",
        4: "2H",
        5: "ET",
        6: "ET",
        7: "Pen",
        8: "FT",
        9: "Postponed",
        10: "Int",
        11: "Abandoned",
        12: "Cancelled",
        13: "TBD",
        14: "Delayed",
    }

    LIVE_STATUSES = {2, 3, 4, 5, 6, 7}   # match is in progress
    FINISHED_STATUSES = {8}                 # match completed
    NOT_STARTED = {1, 13, 14}

    # ── Public API ────────────────────────────────────────────

    async def fetch_live_matches(self) -> list:
        """Fetch all currently live matches (today's schedule, filtered to in-progress)."""
        today = datetime.now().strftime("%Y-%m-%d")
        results = await self._get("match/diary", date=today)
        if not isinstance(results, list):
            return []

        matches = []
        for m in results:
            status_id = m.get("status_id", 0)
            if status_id not in self.LIVE_STATUSES:
                continue

            home_scores = m.get("home_scores", [0, 0, 0, 0, 0, 0, 0])
            away_scores = m.get("away_scores", [0, 0, 0, 0, 0, 0, 0])
            # scores array: [total, h1, h2, et1, et2, pen, ?]
            h_goals = home_scores[0] if home_scores else 0
            a_goals = away_scores[0] if away_scores else 0

            home_info = m.get("home_team_info", {}) or {}
            away_info = m.get("away_team_info", {}) or {}
            competition = m.get("competition_info", {}) or {}

            matches.append({
                "id": str(m.get("id", "")),
                "league": competition.get("name_zh", "") or competition.get("name_en", ""),
                "league_key": str(m.get("competition_id", "")),
                "home": home_info.get("name_zh", "") or home_info.get("name_en", "Home"),
                "away": away_info.get("name_zh", "") or away_info.get("name_en", "Away"),
                "home_id": str(m.get("home_team_id", "")),
                "away_id": str(m.get("away_team_id", "")),
                "score": f"{h_goals} - {a_goals}",
                "minute": self._calc_minute(m),
                "status": self.STATUS_MAP.get(status_id, str(status_id)),
            })
        return matches

    async def fetch_match(self, match_id: str) -> dict:
        """Fetch full match data for a specific fixture."""
        # Try match detail endpoint
        results = await self._get("match/detail/advanced", id=match_id)
        if not results:
            # Fallback: try basic match detail
            results = await self._get("match/detail", id=match_id)
        if not results:
            raise ValueError(f"Match {match_id} not found")

        m = results[0] if isinstance(results, list) else results

        home_scores = m.get("home_scores", [0, 0, 0, 0, 0, 0, 0])
        away_scores = m.get("away_scores", [0, 0, 0, 0, 0, 0, 0])
        h_goals = home_scores[0] if home_scores else 0
        a_goals = away_scores[0] if away_scores else 0
        minute = self._calc_minute(m)

        home_info = m.get("home_team_info", {}) or {}
        away_info = m.get("away_team_info", {}) or {}
        competition = m.get("competition_info", {}) or {}
        home_name = home_info.get("name_zh", "") or home_info.get("name_en", "Home")
        away_name = away_info.get("name_zh", "") or away_info.get("name_en", "Away")

        stats = self._parse_stats(m.get("stats", []))
        events = self._parse_events(m.get("incidents", []), home_name, away_name)

        return {
            "match": {
                "league": competition.get("name_zh", "") or competition.get("name_en", ""),
                "round": str(m.get("round", {}).get("round", "")) if isinstance(m.get("round"), dict) else str(m.get("round", "")),
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
        """Fetch pre-match 1X2 odds."""
        results = await self._get("odds/history", id=match_id)
        if not results:
            return None

        try:
            # Nami odds format varies; try to extract 1X2
            odds_data = results[0] if isinstance(results, list) else results

            # Try standard format: company odds list
            companies = odds_data if isinstance(odds_data, list) else odds_data.get("odds", [])
            if isinstance(companies, list) and companies:
                for company in companies:
                    odds_list = company.get("odds", []) if isinstance(company, dict) else []
                    if odds_list:
                        # First odds entry is usually initial, last is current
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

    async def fetch_h2h(self, home_team_id: str, away_team_id: str) -> dict:
        """Fetch head-to-head record (not directly available, return empty)."""
        return {"h2h": [], "home_results": [], "away_results": []}

    async def fetch_fixtures_by_date(self, date_from: str, date_to: str,
                                     league_id: str = None) -> list:
        """Fetch fixtures for a date range. Returns AllSportsApi-compatible format."""
        all_fixtures = []

        # Nami uses per-day diary endpoint
        from datetime import datetime as dt, timedelta
        start = dt.strptime(date_from, "%Y-%m-%d")
        end = dt.strptime(date_to, "%Y-%m-%d")
        day = start
        while day <= end:
            date_str = day.strftime("%Y-%m-%d")
            results = await self._get("match/diary", date=date_str)
            if isinstance(results, list):
                for m in results:
                    comp_id = str(m.get("competition_id", ""))
                    if league_id and comp_id != league_id:
                        continue
                    all_fixtures.append(self._to_allsports_format(m))
            day += timedelta(days=1)

        return all_fixtures

    async def fetch_latest_finished(self, league_ids: list = None) -> dict | None:
        """Fetch the most recently finished match."""
        today = datetime.now().strftime("%Y-%m-%d")
        results = await self._get("match/diary", date=today)
        if not isinstance(results, list):
            return None

        finished = [m for m in results
                    if m.get("status_id") in self.FINISHED_STATUSES]
        if league_ids:
            filtered = [m for m in finished
                        if str(m.get("competition_id", "")) in league_ids]
            if filtered:
                finished = filtered
        if finished:
            return self._to_summary(finished[-1])

        # Try yesterday
        from datetime import timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        results = await self._get("match/diary", date=yesterday)
        if isinstance(results, list):
            finished = [m for m in results
                        if m.get("status_id") in self.FINISHED_STATUSES]
            if league_ids:
                filtered = [m for m in finished
                            if str(m.get("competition_id", "")) in league_ids]
                if filtered:
                    finished = filtered
            if finished:
                return self._to_summary(finished[-1])

        return None

    async def fetch_competitions(self) -> list:
        """Fetch all available football competitions/leagues."""
        return await self._get("competition/list")

    # ── Format converters ─────────────────────────────────────

    def _to_allsports_format(self, m: dict) -> dict:
        """Convert Nami match to AllSportsApi-compatible fixture format.
        This lets existing code (league_predictions.py) work unchanged."""
        home_scores = m.get("home_scores", [0])
        away_scores = m.get("away_scores", [0])
        h_goals = home_scores[0] if home_scores else 0
        a_goals = away_scores[0] if away_scores else 0
        status_id = m.get("status_id", 0)

        home_info = m.get("home_team_info", {}) or {}
        away_info = m.get("away_team_info", {}) or {}
        competition = m.get("competition_info", {}) or {}
        country = m.get("country_info", {}) or {}

        status_str = self.STATUS_MAP.get(status_id, "")
        if status_id == 1:
            status_str = ""  # AllSports uses empty string for not started

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

        return {
            "event_key": str(m.get("id", "")),
            "league_name": competition.get("name_zh", "") or competition.get("name_en", ""),
            "league_key": str(m.get("competition_id", "")),
            "event_home_team": home_info.get("name_zh", "") or home_info.get("name_en", "Home"),
            "event_away_team": away_info.get("name_zh", "") or away_info.get("name_en", "Away"),
            "home_team_key": str(m.get("home_team_id", "")),
            "away_team_key": str(m.get("away_team_id", "")),
            "event_final_result": f"{h_goals} - {a_goals}",
            "event_status": status_str,
            "event_date": date_str,
            "event_time": time_str,
            "league_round": str(m.get("round", {}).get("round", "")) if isinstance(m.get("round"), dict) else "",
            "country_name": country.get("name_zh", "") or country.get("name_en", ""),
        }

    def _to_summary(self, m: dict) -> dict:
        """Convert Nami match to summary dict (same as AllSportsClient._ev_to_summary)."""
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

    def _calc_minute(self, m: dict) -> int:
        """Calculate current match minute from Nami data."""
        status_id = m.get("status_id", 0)
        if status_id == 3:  # HT
            return 45
        if status_id in self.FINISHED_STATUSES:
            return 90
        if status_id not in self.LIVE_STATUSES:
            return 0

        # Try to get minute from time_running or match_time
        minute = m.get("time_running", 0)
        if minute:
            try:
                return int(str(minute).split(":")[0])
            except (ValueError, IndexError):
                pass

        # Estimate from match_time timestamp
        match_time = m.get("match_time", 0)
        if match_time and status_id in self.LIVE_STATUSES:
            import time as _time
            elapsed = (_time.time() - match_time) / 60
            if status_id == 2:  # 1H
                return min(int(elapsed), 45)
            elif status_id == 4:  # 2H
                return min(45 + int(elapsed - 60), 90)  # ~15 min HT break
            return int(elapsed)
        return 0

    def _parse_stats(self, stats_data: list | dict) -> dict:
        """Parse Nami technical statistics into standard format."""
        result = self._empty_stats()
        if not stats_data:
            return result

        # Nami stats format: list of {type, home, away} or dict with stat keys
        if isinstance(stats_data, list):
            stat_map = {}
            for s in stats_data:
                if isinstance(s, dict):
                    stype = s.get("type", "")
                    stat_map[stype] = s
        elif isinstance(stats_data, dict):
            stat_map = stats_data
        else:
            return result

        def g(keys: list, side: str, default=0):
            """Get stat value trying multiple key names."""
            for k in keys:
                s = stat_map.get(k, {})
                if isinstance(s, dict):
                    v = s.get(side, default)
                elif k in stat_map:
                    return default
                else:
                    continue
                if v is None:
                    continue
                if isinstance(v, str):
                    v = v.strip().replace("%", "")
                    return int(v) if v.isdigit() else default
                return int(v)
            return default

        result["shots"] = [g(["shots", "Shots Total", "射门"], "home"),
                           g(["shots", "Shots Total", "射门"], "away")]
        result["shots_on_target"] = [g(["shots_on_target", "Shots On Target", "射正"], "home"),
                                     g(["shots_on_target", "Shots On Target", "射正"], "away")]
        result["shots_off_target"] = [g(["shots_off_target", "Shots Off Target", "射偏"], "home"),
                                      g(["shots_off_target", "Shots Off Target", "射偏"], "away")]
        result["possession"] = [g(["possession", "Ball Possession", "控球率"], "home", 50),
                                g(["possession", "Ball Possession", "控球率"], "away", 50)]
        result["corners"] = [g(["corners", "Corners", "角球"], "home"),
                             g(["corners", "Corners", "角球"], "away")]
        result["fouls"] = [g(["fouls", "Fouls", "犯规"], "home"),
                           g(["fouls", "Fouls", "犯规"], "away")]
        result["yellow_cards"] = [g(["yellow_cards", "Yellow Cards", "黄牌"], "home"),
                                  g(["yellow_cards", "Yellow Cards", "黄牌"], "away")]
        result["red_cards"] = [g(["red_cards", "Red Cards", "红牌"], "home"),
                               g(["red_cards", "Red Cards", "红牌"], "away")]
        result["offsides"] = [g(["offsides", "Offsides", "越位"], "home"),
                              g(["offsides", "Offsides", "越位"], "away")]
        result["saves"] = [g(["saves", "Goalkeeper Saves", "扑救"], "home"),
                           g(["saves", "Goalkeeper Saves", "扑救"], "away")]
        result["dangerous_attacks"] = [g(["dangerous_attacks", "Attacks", "进攻", "危险进攻"], "home"),
                                       g(["dangerous_attacks", "Attacks", "进攻", "危险进攻"], "away")]
        result["pass_accuracy"] = [g(["pass_accuracy", "Passes Accurate", "传球成功率"], "home", 80),
                                   g(["pass_accuracy", "Passes Accurate", "传球成功率"], "away", 80)]

        if result["xg"] == [0, 0] and (result["shots_on_target"][0] > 0 or result["shots_on_target"][1] > 0):
            result["xg"] = self._estimate_xg(result)

        return result

    def _parse_events(self, incidents: list, home_name: str = "", away_name: str = "") -> list:
        """Parse Nami incidents into unified events list."""
        events = []
        if not incidents or not isinstance(incidents, list):
            return events

        for inc in incidents:
            if not isinstance(inc, dict):
                continue
            try:
                minute = int(inc.get("time", 0) or 0)
                inc_type = inc.get("type", 0)
                # position: 1=home, 2=away
                position = inc.get("position", 1)
                team = "HOME" if position == 1 else "AWAY"
                player = inc.get("player_name", "") or ""

                # type mapping: 1=进球, 2=角球, 3=黄牌, 4=红牌, 5=换人, 7=点球, 8=乌龙球, 9=助攻, 11=两黄变红
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
                    sub_in = inc.get("in_player_name", "") or player
                    events.append({
                        "id": f"s{minute}{team[0]}",
                        "minute": minute,
                        "type": "SUB",
                        "team": team,
                        "text": f"SUB — {sub_in}" if sub_in else "SUB",
                    })
            except Exception:
                continue

        return sorted(events, key=lambda x: x["minute"], reverse=True)

    @staticmethod
    def _estimate_xg(stats: dict) -> list:
        """Estimate xG from shots-on-target."""
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
