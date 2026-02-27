"""
AI Football Quant Terminal — FastAPI Backend v1.1

v1.1 changes:
  - Full JSON schema: meta/match/probability/market/stats/events/quant/uncertainty/explain/report
  - Admin API for match management
  - Per-match state (delta, rolling Brier, event dedup)
  - Health status: OK / DEGRADED / STALE
  - WebSocket reconnect-friendly (seq numbering)
"""

import asyncio
import time
import random
import math

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import settings
from data.allsports_client import AllSportsClient
from data.sportmonks_client import SportMonksClient
from data.api_client import FootballAPIClient
from data.odds_client import OddsAPIClient
from data.cache import CacheManager
from ws.manager import ConnectionManager
from models.predictor import LivePredictor
from models.quant import QuantEngine
from services.market_engine import MarketEngine
from services.explain_engine import ExplainEngine
from services.uncertainty_engine import UncertaintyEngine
from services.total_goals_engine import TotalGoalsEngine
from store.match_state import MatchStateStore

app = FastAPI(title="Football Quant Terminal API", version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global instances ──────────────────────────────────────────
ws_manager = ConnectionManager()
allsports = AllSportsClient()
sportmonks = SportMonksClient()
football_api = FootballAPIClient()
odds_api = OddsAPIClient()
cache = CacheManager()
quant_engine = QuantEngine()
market_engine = MarketEngine()
explain_engine = ExplainEngine()
uncertainty_engine = UncertaintyEngine()
total_goals_engine = TotalGoalsEngine()
state_store = MatchStateStore()

# Managed matches (admin-controlled)
managed_matches: dict[str, dict] = {}

predictor = None


def get_predictor():
    global predictor
    if predictor is None:
        try:
            predictor = LivePredictor(settings.MODEL_PATH)
        except FileNotFoundError:
            return None
    return predictor


# ══════════════════════════════════════════════════════════════
# ADMIN API — Match Management
# ══════════════════════════════════════════════════════════════

class MatchConfig(BaseModel):
    match_id: str
    league: str = "EPL"
    round: str = ""
    home_name: str = "Home"
    away_name: str = "Away"
    home_short: str = "HOM"
    away_short: str = "AWY"
    home_name_cn: str = ""
    away_name_cn: str = ""
    home_elo: int = 1500
    away_elo: int = 1500
    api_football_id: str = ""        # API-Football fixture ID
    odds_sport: str = "soccer_epl"   # The Odds API sport key
    active: bool = True


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "1.1.0",
        "demo_mode": settings.demo_mode,
        "model_loaded": get_predictor() is not None,
        "active_matches": len([m for m in managed_matches.values() if m.get("active")]),
        "ws_connections": ws_manager.get_connection_count(),
        "timestamp": time.time(),
    }


@app.get("/api/admin/matches")
async def admin_list_matches():
    """List all managed matches."""
    return list(managed_matches.values())


@app.post("/api/admin/matches")
async def admin_add_match(config: MatchConfig):
    """Add or update a managed match."""
    managed_matches[config.match_id] = config.model_dump()
    return {"status": "ok", "match_id": config.match_id}


@app.delete("/api/admin/matches/{match_id}")
async def admin_remove_match(match_id: str):
    """Remove a managed match."""
    managed_matches.pop(match_id, None)
    state_store.remove(match_id)
    return {"status": "ok"}


@app.put("/api/admin/matches/{match_id}/toggle")
async def admin_toggle_match(match_id: str):
    """Toggle match active status."""
    if match_id in managed_matches:
        managed_matches[match_id]["active"] = not managed_matches[match_id]["active"]
        return managed_matches[match_id]
    raise HTTPException(404, "Match not found")


@app.get("/api/matches/live")
async def get_live_matches():
    """List active matches for frontend."""
    active = [m for m in managed_matches.values() if m.get("active")]
    if active:
        return active
    # Fallback: demo
    return [{"match_id": "demo", "league": "EPL", "home_name": "Arsenal",
             "away_name": "Chelsea", "home_short": "ARS", "away_short": "CHE",
             "active": True}]


# ══════════════════════════════════════════════════════════════
# DEMO SIMULATOR (v1.1 full schema)
# ══════════════════════════════════════════════════════════════

class DemoSimulator:
    def __init__(self):
        self.minute = 0
        self.score = [0, 0]
        self.hxg = 0.0
        self.axg = 0.0
        self.events = []
        self.prev_state = None

    def tick(self, match_state, real_odds=None):
        """real_odds: optional {"home":1.85,"draw":3.5,"away":4.2} from The Odds API."""
        self.minute = min(self.minute + 1, 90)
        m = max(1, self.minute)
        cl = lambda v, lo, hi: max(lo, min(hi, v))
        diff = self.score[0] - self.score[1]
        tf = m / 90

        # Goals (generate events)
        new_events = []
        if self.minute > 1:
            if random.random() < 0.014:
                self.score[0] += 1
                new_events.append({"id": f"e{m}h", "minute": m, "type": "GOAL",
                                   "team": "HOME", "text": f"GOAL — ARS {self.score[0]}-{self.score[1]}"})
            if random.random() < 0.011:
                self.score[1] += 1
                new_events.append({"id": f"e{m}a", "minute": m, "type": "GOAL",
                                   "team": "AWAY", "text": f"GOAL — CHE {self.score[0]}-{self.score[1]}"})
            if random.random() < 0.02:
                team = "HOME" if random.random() > 0.5 else "AWAY"
                new_events.append({"id": f"y{m}", "minute": m, "type": "YELLOW",
                                   "team": team, "text": f"YELLOW — {'ARS' if team == 'HOME' else 'CHE'}"})

        for ev in new_events:
            match_state.add_event(ev)

        # Probability
        pH = cl(50 + diff * 13 + diff * tf * 14 + (random.random() - 0.5) * 2.5, 4, 94)
        pA = cl(24 - diff * 11 + (random.random() - 0.5) * 2, 3, 65)
        pD = cl(100 - pH - pA, 3, 55)
        total = pH + pD + pA
        prob = {
            "home": round(pH / total * 100, 2),
            "draw": round(pD / total * 100, 2),
            "away": round(pA / total * 100, 2),
        }
        confidence = cl(round(75 + random.random() * 18), 60, 98)

        # Delta from match_state
        delta = match_state.update_probability(prob)
        match_state.last_update_ts = time.time()
        match_state.last_odds_ts = time.time()
        seq = match_state.bump_seq()

        # xG
        self.hxg = cl(self.hxg + random.random() * 0.065, 0, 5)
        self.axg = cl(self.axg + random.random() * 0.05, 0, 5)

        # Stats
        stats = {
            "shots": [m // 7 + 2 + random.randint(0, 1), m // 9 + 1 + random.randint(0, 1)],
            "shots_on_target": [m // 14 + 1, m // 18 + 1],
            "shots_off_target": [0, 0],
            "xg": [round(self.hxg, 2), round(self.axg, 2)],
            "dangerous_attacks": [int(m * 0.55) + random.randint(0, 2), int(m * 0.4) + random.randint(0, 2)],
            "corners": [m // 14 + random.randint(0, 1), m // 18 + random.randint(0, 1)],
            "possession": [cl(round(53 + diff * 3 + (random.random() - 0.5) * 6), 35, 70), 0],
            "pass_accuracy": [cl(round(85 + (random.random() - 0.5) * 8), 72, 95),
                              cl(round(81 + (random.random() - 0.5) * 8), 70, 93)],
            "fouls": [m // 10 + 1, m // 9 + 1],
            "yellow_cards": [m // 35, m // 30],
            "red_cards": [0, 0],
            "offsides": [m // 25, m // 22],
            "saves": [m // 20, m // 15 + 1],
        }
        stats["shots_off_target"] = [stats["shots"][0] - stats["shots_on_target"][0],
                                     stats["shots"][1] - stats["shots_on_target"][1]]
        stats["possession"][1] = 100 - stats["possession"][0]

        # Quant
        quant = {
            "pressure_index": cl(round(50 + diff * 12 + (random.random() - 0.5) * 10), 10, 98),
            "momentum_score": cl(round(diff * 14 + (random.random() - 0.5) * 8), -50, 50),
            "volatility_index": cl(round((0.5 + tf * 0.4 + random.random() * 0.3) * 100) / 100, 0.1, 1.5),
            "risk_of_concede": cl(round(25 + (1 - tf) * 15 + random.random() * 15), 5, 85),
            "expected_goal_window_min": [max(2, int(8 - tf * 5)), max(5, int(15 - tf * 8))] if m < 80 else None,
            "model_variance": cl(round((0.08 + random.random() * 0.12) * 1000) / 1000, 0.01, 0.3),
            "xg_delta": round(self.hxg - self.axg, 2),
        }

        # Market — use real odds if available, else simulate
        if real_odds:
            odds_used = real_odds
            odds_source = "the-odds-api"
        else:
            odds_used = {"home": round(1.5 + random.random(), 2),
                         "draw": round(3.2 + random.random(), 2),
                         "away": round(3.8 + random.random() * 2, 2)}
            odds_source = "demo-simulator"
        market = market_engine.compute(odds_used, prob)

        # Explain
        cur_state = {
            "minute": m, "home_goals": self.score[0], "away_goals": self.score[1],
            "home_shots_on_target": stats["shots_on_target"][0],
            "away_shots_on_target": stats["shots_on_target"][1],
            "pressure_index": quant["pressure_index"],
            "home_possession": stats["possession"][0],
            "home_xg": self.hxg, "away_xg": self.axg,
            "home_red": 0, "away_red": 0,
        }
        explain = explain_engine.explain(cur_state, self.prev_state)
        self.prev_state = cur_state.copy()

        # Uncertainty
        uncertainty = uncertainty_engine.compute(prob, quant, match_state.get_rolling_brier())

        # Report
        report = {
            "half_time_ready": self.minute == 45,
            "full_time_ready": self.minute == 90,
            "snapshot_url": None,
        }

        # Total Goals O/U — build live_state for total_goals_engine
        tg_live_state = {
            "minute": m,
            "home_goals": self.score[0],
            "away_goals": self.score[1],
            "home_xg": self.hxg,
            "away_xg": self.axg,
            "home_shots_on_target": stats["shots_on_target"][0],
            "away_shots_on_target": stats["shots_on_target"][1],
            "home_dangerous_attacks": stats["dangerous_attacks"][0],
            "away_dangerous_attacks": stats["dangerous_attacks"][1],
            "home_red": stats["red_cards"][0],
            "away_red": stats["red_cards"][1],
        }

        # Simulated O/U odds in demo mode (over_odds ~1.80-2.10, under ~1.80-2.10)
        if real_odds and real_odds.get("totals"):
            demo_odds_ou = real_odds["totals"]
        else:
            demo_odds_ou = {
                "line": 2.5,
                "over_odds": round(1.80 + random.random() * 0.30, 2),
                "under_odds": round(1.80 + random.random() * 0.30, 2),
            }

        total_goals = total_goals_engine.compute(tg_live_state, demo_odds_ou, time.time())

        # ═══ v1.1 Full Payload ═══
        return {
            "meta": {
                "match_id": "demo",
                "source": {"live": "demo-simulator", "odds": odds_source},
                "last_update_ts": time.time(),
                "data_delay_sec": 0,
                "health": "OK",
                "seq": seq,
            },
            "match": {
                "league": "EPL", "round": "R28",
                "minute": self.minute,
                "half": "H1" if self.minute <= 45 else "H2",
                "score": f"{self.score[0]}-{self.score[1]}",
                "home": {"code": "ARS", "name": "Arsenal", "name_cn": "阿森纳"},
                "away": {"code": "CHE", "name": "Chelsea", "name_cn": "切尔西"},
            },
            "probability": {
                **prob,
                "delta_home": delta["home"],
                "delta_draw": delta["draw"],
                "delta_away": delta["away"],
                "model_confidence": confidence,
            },
            "market": market,
            "stats": stats,
            "events": match_state.get_recent_events(5),
            "quant": quant,
            "uncertainty": uncertainty,
            "explain": explain,
            "report": report,
            "total_goals": total_goals,
        }


# ══════════════════════════════════════════════════════════════
# WEBSOCKET
# ══════════════════════════════════════════════════════════════

@app.websocket("/ws/{match_id}")
async def websocket_endpoint(ws: WebSocket, match_id: str):
    await ws_manager.connect(ws, match_id)
    ms = state_store.get(match_id)
    try:
        if match_id == "demo" or settings.demo_mode:
            sim = DemoSimulator()
            # Fetch real odds once at start, refresh periodically
            config = managed_matches.get(match_id, {})
            real_odds = None
            odds_tick = 0
            while True:
                # Refresh real odds every 30 ticks (~60s at 2s interval)
                if settings.has_odds and odds_tick % 30 == 0:
                    try:
                        real_odds = await odds_api.fetch_odds(
                            match_id, config.get("odds_sport", "soccer_epl"))
                    except Exception:
                        pass
                odds_tick += 1
                payload = sim.tick(ms, real_odds=real_odds)
                await ws.send_json(payload)
                await asyncio.sleep(settings.WS_PUSH_INTERVAL)
        else:
            # Live mode — priority: AllSportsApi → SportMonks → API-Football
            pred = get_predictor()
            config = managed_matches.get(match_id, {})
            api_id = config.get("api_football_id", match_id)
            live_source_name = settings.live_source
            prev_live_state = None

            while True:
                try:
                    # Fetch live data from best available source
                    if settings.ALLSPORTS_API_KEY:
                        live = await allsports.fetch_match(api_id)
                    elif settings.SPORTMONKS_API_KEY:
                        live = await sportmonks.fetch_match(api_id)
                    else:
                        live = await football_api.fetch_match(api_id)
                    odds_data = await odds_api.fetch_odds(
                        match_id, config.get("odds_sport", "soccer_epl"))

                    live_state = {
                        "minute": live.get("minute", 0),
                        "home_goals": live.get("home_goals", 0),
                        "away_goals": live.get("away_goals", 0),
                        "home_shots": live.get("stats", {}).get("shots", [0, 0])[0],
                        "away_shots": live.get("stats", {}).get("shots", [0, 0])[1],
                        "home_shots_on_target": live.get("stats", {}).get("shots_on_target", [0, 0])[0],
                        "away_shots_on_target": live.get("stats", {}).get("shots_on_target", [0, 0])[1],
                        "home_possession": live.get("stats", {}).get("possession", [50, 50])[0],
                        "home_xg": live.get("stats", {}).get("xg", [0, 0])[0],
                        "away_xg": live.get("stats", {}).get("xg", [0, 0])[1],
                        "home_dangerous_attacks": live.get("stats", {}).get("dangerous_attacks", [0, 0])[0],
                        "away_dangerous_attacks": live.get("stats", {}).get("dangerous_attacks", [0, 0])[1],
                        "home_red": live.get("stats", {}).get("red_cards", [0, 0])[0],
                        "away_red": live.get("stats", {}).get("red_cards", [0, 0])[1],
                        "home_elo": config.get("home_elo", 1500),
                        "away_elo": config.get("away_elo", 1500),
                    }

                    if odds_data:
                        live_state["odds_home"] = odds_data.get("home", 2.0)
                        live_state["odds_draw"] = odds_data.get("draw", 3.5)
                        live_state["odds_away"] = odds_data.get("away", 3.5)
                        ms.last_odds_ts = time.time()

                    # Predict
                    if pred:
                        result = pred.predict(live_state)
                        prob = result["probability"]
                        quant_data = result["quant"]
                    else:
                        oh = live_state.get("odds_home", 2.0)
                        od = live_state.get("odds_draw", 3.5)
                        oa = live_state.get("odds_away", 3.5)
                        t = 1 / oh + 1 / od + 1 / oa
                        prob = {
                            "home": round(100 / oh / t, 2),
                            "draw": round(100 / od / t, 2),
                            "away": round(100 / oa / t, 2),
                        }
                        quant_data = quant_engine.compute(live_state, prob)

                    ms.last_update_ts = time.time()
                    delta = ms.update_probability(prob)
                    seq = ms.bump_seq()

                    # Market
                    market = market_engine.compute(odds_data, prob)

                    # Explain
                    explain = explain_engine.explain(live_state, prev_live_state)
                    prev_live_state = live_state.copy()

                    # Uncertainty
                    uncertainty = uncertainty_engine.compute(prob, quant_data, ms.get_rolling_brier())

                    # Match info from config
                    match_info = {
                        "league": config.get("league", live.get("match", {}).get("league", "?")),
                        "round": config.get("round", ""),
                        "minute": live_state["minute"],
                        "half": "H1" if live_state["minute"] <= 45 else "H2",
                        "score": f"{live_state['home_goals']}-{live_state['away_goals']}",
                        "home": {
                            "code": config.get("home_short", "HOM"),
                            "name": config.get("home_name", "Home"),
                            "name_cn": config.get("home_name_cn", ""),
                        },
                        "away": {
                            "code": config.get("away_short", "AWY"),
                            "name": config.get("away_name", "Away"),
                            "name_cn": config.get("away_name_cn", ""),
                        },
                    }

                    minute = live_state["minute"]
                    report = {
                        "half_time_ready": minute == 45,
                        "full_time_ready": minute == 90,
                        "snapshot_url": None,
                    }

                    # Total Goals O/U
                    odds_ou = odds_data.get("totals") if odds_data else None
                    total_goals = total_goals_engine.compute(live_state, odds_ou, time.time())

                    payload = {
                        "meta": {
                            "match_id": match_id,
                            "source": {"live": live_source_name.lower(), "odds": "the-odds-api" if odds_data else "none"},
                            "last_update_ts": ms.last_update_ts,
                            "data_delay_sec": settings.API_FETCH_INTERVAL,
                            "health": ms.get_health(),
                            "seq": seq,
                        },
                        "match": match_info,
                        "probability": {
                            **prob,
                            "delta_home": delta["home"],
                            "delta_draw": delta["draw"],
                            "delta_away": delta["away"],
                            "model_confidence": quant_data.get("confidence", 75),
                        },
                        "market": market,
                        "stats": live.get("stats", {}),
                        "events": ms.get_recent_events(5),
                        "quant": quant_data,
                        "uncertainty": uncertainty,
                        "explain": explain,
                        "report": report,
                        "total_goals": total_goals,
                    }

                    await ws.send_json(payload)

                except Exception as e:
                    await ws.send_json({
                        "meta": {"health": "DEGRADED", "error": str(e), "seq": ms.bump_seq()},
                    })

                await asyncio.sleep(settings.WS_PUSH_INTERVAL)

    except WebSocketDisconnect:
        ws_manager.disconnect(ws, match_id)


# ── Startup ───────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    # Auto-register demo match
    managed_matches["demo"] = {
        "match_id": "demo", "league": "EPL", "round": "R28",
        "home_name": "Arsenal", "away_name": "Chelsea",
        "home_short": "ARS", "away_short": "CHE",
        "home_name_cn": "阿森纳", "away_name_cn": "切尔西",
        "home_elo": 1650, "away_elo": 1580,
        "api_football_id": "", "odds_sport": "soccer_epl",
        "active": True,
    }
    print("=" * 50)
    print("  AI Football Quant Terminal v1.1 — Backend")
    print(f"  Mode: {'DEMO' if settings.demo_mode else 'LIVE'}")
    print(f"  Live source: {settings.live_source}")
    print(f"  Odds: {'The Odds API' if settings.has_odds else 'None'}")
    print(f"  Model: {'Loaded' if get_predictor() else 'Not found (fallback)'}")
    print("=" * 50)


# ── Mount admin static files (after all routes) ─────────────
import os
_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/admin", StaticFiles(directory=_static_dir, html=True), name="admin")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
