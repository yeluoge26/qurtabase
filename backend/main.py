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
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from typing import Optional
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
from services.score_matrix_engine import ScoreMatrixEngine
from services.goal_window_engine import GoalWindowEngine
from services.risk_engine import RiskEngine
from services.post_match_engine import PostMatchEngine
from services.performance_tracker import PerformanceTracker
from services.history_tracker import HistoryTracker
from services.prematch_engine import PreMatchEngine
from services.tts_engine import TTSEngine
try:
    from services.broadcast_engine import BroadcastEngine
except ImportError:
    BroadcastEngine = None
from store.match_state import MatchStateStore
import json as _json
import os as _os

# Load backtest results (if available)
_backtest_path = _os.path.join(_os.path.dirname(__file__), "backtest_results.json")
try:
    with open(_backtest_path) as _f:
        _backtest_data = _json.load(_f)
except (FileNotFoundError, _json.JSONDecodeError):
    _backtest_data = None

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
score_matrix_engine = ScoreMatrixEngine()
goal_window_engine = GoalWindowEngine()
risk_engine = RiskEngine()
post_match_engine = PostMatchEngine()
performance_tracker = PerformanceTracker()
history_tracker = HistoryTracker()
prematch_engine = PreMatchEngine()
_prematch_cache: dict[str, dict] = {}  # match_id → cached pre-match rec

def _get_cached_prematch(match_id: str, config: dict, minute: int) -> dict:
    """Return pre-match rec, caching on first compute so it persists throughout match."""
    if match_id not in _prematch_cache:
        result = prematch_engine.compute(config)
        _prematch_cache[match_id] = result
    return _prematch_cache[match_id]

tts_engine = TTSEngine()
broadcast_engine = BroadcastEngine() if BroadcastEngine else None
state_store = MatchStateStore()

from services.league_predictions import LeaguePredictionService
league_predictions = LeaguePredictionService()

# Managed matches (admin-controlled)
managed_matches: dict[str, dict] = {}

# Track initial predictions per match for auto-recording
_match_predictions: dict[str, dict] = {}
_match_recorded: set = set()  # avoid duplicate recording

predictor = None


def _auto_record_prediction(match_id: str, prob: dict, confidence: float,
                             minute: int, score: list, config: dict,
                             total_goals: dict = None):
    """Auto-record initial prediction & final result for HistoryTracker."""
    # Store initial prediction (first tick, minute <= 2)
    if match_id not in _match_predictions and minute <= 2:
        # Determine predicted 1X2
        if prob["home"] > prob["draw"] and prob["home"] > prob["away"]:
            pred_1x2 = "HOME"
        elif prob["away"] > prob["home"] and prob["away"] > prob["draw"]:
            pred_1x2 = "AWAY"
        else:
            pred_1x2 = "DRAW"

        # Determine predicted O/U
        pred_ou = "OVER"
        ou_line = 2.5
        if total_goals:
            pred_ou = total_goals.get("signal", "OVER")
            if pred_ou not in ("OVER", "UNDER"):
                pred_ou = "OVER" if (total_goals.get("model_prob_over") or 50) > 50 else "UNDER"
            ou_line = total_goals.get("line") or 2.5

        _match_predictions[match_id] = {
            "predicted_1x2": pred_1x2,
            "predicted_ou": pred_ou,
            "ou_line": ou_line,
            "confidence": confidence,
            "predicted_prob": max(prob["home"], prob["draw"], prob["away"]),
            "pre_lambda": total_goals.get("lambda_pre", 0) if total_goals else 0,
            "home": config.get("home_name", "Home"),
            "away": config.get("away_name", "Away"),
            "home_cn": config.get("home_name_cn", ""),
            "away_cn": config.get("away_name_cn", ""),
            "league": config.get("league", ""),
        }

    # Record when match ends (minute >= 90)
    if match_id not in _match_recorded and minute >= 90 and match_id in _match_predictions:
        pred = _match_predictions[match_id]
        h_goals, a_goals = score[0], score[1]
        actual_goals = h_goals + a_goals

        # Determine actual 1X2
        if h_goals > a_goals:
            actual_1x2 = "HOME"
        elif a_goals > h_goals:
            actual_1x2 = "AWAY"
        else:
            actual_1x2 = "DRAW"

        ou_correct = (pred["predicted_ou"] == "OVER" and actual_goals > pred["ou_line"]) or \
                     (pred["predicted_ou"] == "UNDER" and actual_goals < pred["ou_line"])

        # Brier score (simplified: for the predicted outcome)
        p_predicted = pred["predicted_prob"] / 100.0
        brier = round((1 - p_predicted) ** 2, 3)

        history_tracker.record_match({
            "match_id": match_id,
            "league": pred["league"],
            "home": pred["home"],
            "away": pred["away"],
            "home_cn": pred["home_cn"],
            "away_cn": pred["away_cn"],
            "home_short": pred["home"][:3].upper(),
            "away_short": pred["away"][:3].upper(),
            "date": time.strftime("%Y-%m-%d"),
            "predicted_1x2": pred["predicted_1x2"],
            "actual_result": actual_1x2,
            "correct": pred["predicted_1x2"] == actual_1x2,
            "predicted_ou": pred["predicted_ou"],
            "ou_line": pred["ou_line"],
            "actual_goals": actual_goals,
            "ou_correct": ou_correct,
            "confidence": pred["confidence"],
            "predicted_prob": pred["predicted_prob"],
            "pre_lambda": pred["pre_lambda"],
            "brier_score": brier,
        })
        _match_recorded.add(match_id)
        print(f"  [HistoryTracker] Recorded: {pred['home']} vs {pred['away']} | "
              f"Pred: {pred['predicted_1x2']} | Actual: {actual_1x2} | "
              f"{'✓' if pred['predicted_1x2'] == actual_1x2 else '✗'}")


# ── Broadcast State ──────────────────────────────────────────
broadcast_state = {
    "text": "",
    "stage": "",
    "priority": "normal",
    "timestamp": 0,
    "speaking": False,
    "cooldown_remaining": 0,
    "speak_until": 0,
}

# ── Signal Control State (per match) ─────────────────────────
# State machine: idle → ready → (confirmed → cooldown) → idle/ready
signal_state: dict[str, dict] = {}

SIGNAL_EDGE_THRESHOLD = 4.0    # Edge % required to move from idle → ready
SIGNAL_LOCK_SEC = 10.0         # Seconds the "confirmed" state stays locked
SIGNAL_COOLDOWN_SEC = 120.0    # Seconds of cooldown after lock expires


def _get_signal_state(match_id: str) -> dict:
    """Return the current signal state for a match, creating if needed."""
    if match_id not in signal_state:
        signal_state[match_id] = {
            "state": "idle",
            "line": 0,
            "model_prob": 0,
            "market_prob": 0,
            "edge": 0.0,
            "confirmed_at": None,
            "cooldown_remaining": 0,
            "rejected_at": None,
        }
    return signal_state[match_id]


def _compute_signal_control(match_id: str, edge: float, line: float,
                             model_prob: float, market_prob: float) -> dict:
    """
    Evaluate the signal control state machine and return the signal_control payload.
    Called on every tick to update state transitions based on time and edge.
    """
    ss = _get_signal_state(match_id)
    now = time.time()

    # Always update latest market data
    ss["line"] = line
    ss["model_prob"] = model_prob
    ss["market_prob"] = market_prob
    ss["edge"] = edge

    current = ss["state"]

    # ── State transitions ──
    if current == "confirmed":
        elapsed = now - (ss["confirmed_at"] or now)
        if elapsed >= SIGNAL_LOCK_SEC:
            # Lock expired → enter cooldown
            ss["state"] = "cooldown"
            ss["cooldown_start"] = now
            current = "cooldown"

    if current == "cooldown":
        cooldown_start = ss.get("cooldown_start", now)
        remaining = SIGNAL_COOLDOWN_SEC - (now - cooldown_start)
        if remaining <= 0:
            # Cooldown expired → re-evaluate based on edge
            ss["state"] = "ready" if abs(edge) >= SIGNAL_EDGE_THRESHOLD else "idle"
            ss["cooldown_remaining"] = 0
            ss["confirmed_at"] = None
            current = ss["state"]
        else:
            ss["cooldown_remaining"] = int(remaining)

    if current == "idle":
        if abs(edge) >= SIGNAL_EDGE_THRESHOLD:
            ss["state"] = "ready"
            current = "ready"

    if current == "ready":
        if abs(edge) < SIGNAL_EDGE_THRESHOLD:
            ss["state"] = "idle"
            current = "idle"

    # Build payload
    return {
        "state": ss["state"],
        "line": round(ss["line"] or 0, 2),
        "model_prob": round(ss["model_prob"] or 0, 1),
        "market_prob": round(ss["market_prob"] or 0, 1),
        "edge": round(ss["edge"] or 0, 1),
        "confirmed_at": ss["confirmed_at"],
        "cooldown_remaining": ss.get("cooldown_remaining", 0),
    }


def _compute_broadcast(data, lang="en"):
    """
    Evaluate broadcast triggers from the current tick payload and return
    the broadcast section for the WebSocket payload.
    """
    global broadcast_state

    if not broadcast_engine:
        return {
            "text": "",
            "stage": "",
            "priority": "normal",
            "timestamp": 0,
            "speaking": False,
            "cooldown_remaining": 0,
        }

    now = time.time()

    try:
        match_data = {
            "minute": data.get("match", {}).get("minute", 0),
            "score": data.get("match", {}).get("score", "0-0"),
            "home": data.get("match", {}).get("home", {}).get("name", "Home"),
            "away": data.get("match", {}).get("away", {}).get("name", "Away"),
            "league": data.get("match", {}).get("league", ""),
            "lambda_live": data.get("total_goals", {}).get("lambda_live", 0),
            "lambda_pre": data.get("total_goals", {}).get("lambda_pre", 0),
            "lambda_rem": data.get("total_goals", {}).get("lambda_remaining", 0),
            "edge": data.get("total_goals", {}).get("edge", 0),
            "tempo": data.get("total_goals", {}).get("tempo_index", 50),
            "signal_state": data.get("signal_control", {}).get("state", "idle"),
            "line": data.get("total_goals", {}).get("line", 2.5),
            "model_prob": data.get("total_goals", {}).get("final_prob_over", 0),
            "events": data.get("events", []),
        }

        triggers = broadcast_engine.evaluate_triggers(match_data, lang)

        if triggers:
            top = triggers[0]
            priority = top.get("priority", "normal")
            if broadcast_engine.can_broadcast(priority):
                broadcast_state["text"] = top.get("text", "")
                broadcast_state["stage"] = top.get("stage", "")
                broadcast_state["priority"] = priority
                broadcast_state["timestamp"] = now
                broadcast_state["speaking"] = True
                broadcast_state["speak_until"] = now + 8
                broadcast_engine.record_broadcast()

        broadcast_state["cooldown_remaining"] = getattr(
            broadcast_engine, "cooldown_remaining", 0
        )

        if now > broadcast_state.get("speak_until", 0):
            broadcast_state["speaking"] = False

    except Exception:
        pass

    return {
        "text": broadcast_state.get("text", ""),
        "stage": broadcast_state.get("stage", ""),
        "priority": broadcast_state.get("priority", "normal"),
        "timestamp": broadcast_state.get("timestamp", 0),
        "speaking": broadcast_state.get("speaking", False),
        "cooldown_remaining": broadcast_state.get("cooldown_remaining", 0),
    }


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
    kickoff: str = ""                # Kickoff time (ISO 8601 or HH:MM)
    status: str = ""                 # Match status: upcoming/live/finished/HT
    live_enabled: bool = False       # Whether live streaming is enabled


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "2.3.0",
        "demo_mode": settings.demo_mode,
        "model_loaded": get_predictor() is not None,
        "active_matches": len([m for m in managed_matches.values() if m.get("active")]),
        "live_matches": len([m for m in managed_matches.values() if m.get("live_enabled")]),
        "ws_connections": ws_manager.get_connection_count(),
        "live_source": settings.live_source,
        "has_odds": settings.has_odds,
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


@app.put("/api/admin/matches/{match_id}/live")
async def admin_toggle_live(match_id: str):
    """Toggle live streaming for a match."""
    if match_id in managed_matches:
        managed_matches[match_id]["live_enabled"] = not managed_matches[match_id].get("live_enabled", False)
        return managed_matches[match_id]
    raise HTTPException(404, "Match not found")


@app.get("/api/matches/live")
async def get_live_matches():
    """List active matches for frontend.
    Priority: managed active → API live → API latest finished → demo fallback
    """
    # 1) Managed active matches (admin-imported, excluding demo)
    active = [m for m in managed_matches.values()
              if m.get("active") and m.get("match_id") != "demo"]
    if active:
        return active

    # 2) Auto-discover from live API
    if settings.ALLSPORTS_API_KEY:
        try:
            live_list = await allsports.fetch_live_matches()
            if live_list:
                out = []
                for lm in live_list[:5]:
                    mid = lm["id"]
                    out.append({
                        "match_id": mid,
                        "league": lm.get("league", ""),
                        "home_name": lm.get("home", "Home"),
                        "away_name": lm.get("away", "Away"),
                        "home_short": lm.get("home", "HOM")[:3].upper(),
                        "away_short": lm.get("away", "AWY")[:3].upper(),
                        "score": lm.get("score", "0 - 0"),
                        "minute": lm.get("minute", 0),
                        "status": lm.get("status", ""),
                        "active": True,
                        "mode": "live",
                    })
                return out
        except Exception:
            pass

        # 3) No live matches — fetch latest finished
        try:
            latest = await allsports.fetch_latest_finished()
            if latest:
                return [{
                    "match_id": latest["id"],
                    "league": latest.get("league", ""),
                    "home_name": latest.get("home", "Home"),
                    "away_name": latest.get("away", "Away"),
                    "home_short": latest.get("home", "HOM")[:3].upper(),
                    "away_short": latest.get("away", "AWY")[:3].upper(),
                    "score": latest.get("score", "0-0"),
                    "minute": latest.get("minute", 90),
                    "status": latest.get("status", "Finished"),
                    "date": latest.get("date", ""),
                    "active": True,
                    "mode": "finished",
                }]
        except Exception:
            pass

    # 4) No matches available
    return []


@app.get("/api/predictions/leagues")
async def get_league_predictions():
    """Return per-league predictions + backtest stats for dashboard."""
    predictions = league_predictions.predictions
    by_league = _backtest_data.get("by_league", {}) if _backtest_data else {}

    league_list = []
    for league_name, pred in predictions.items():
        backtest = by_league.get(league_name, {})
        league_list.append({
            **pred,
            "backtest_accuracy": backtest.get("accuracy", 0),
            "backtest_total": backtest.get("total", 0),
            "backtest_correct": backtest.get("correct", 0),
        })

    league_list.sort(key=lambda x: x.get("backtest_accuracy", 0), reverse=True)

    return {
        "leagues": league_list,
        "model_stats": _backtest_data,
        "last_refresh": league_predictions.last_refresh,
        "league_count": len(league_list),
    }


@app.get("/api/admin/fixtures")
async def admin_fetch_fixtures(date_from: str = "", date_to: str = "",
                                league_id: str = ""):
    """
    Fetch upcoming/today's fixtures from live data sources.
    Returns match list with kickoff times for admin to import.
    """
    from datetime import datetime, timedelta

    today = datetime.now().strftime("%Y-%m-%d")
    if not date_from:
        date_from = today
    if not date_to:
        date_to = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")

    fixtures = []

    # Source 1: AllSportsApi fixtures
    if settings.ALLSPORTS_API_KEY:
        try:
            raw = await allsports.fetch_fixtures_by_date(date_from, date_to,
                                                          league_id or None)
            for ev in raw:
                status = ev.get("event_status", "")
                fixtures.append({
                    "source": "allsports",
                    "match_id": str(ev.get("event_key", "")),
                    "league": ev.get("league_name", ""),
                    "league_key": str(ev.get("league_key", "")),
                    "home_name": ev.get("event_home_team", ""),
                    "away_name": ev.get("event_away_team", ""),
                    "home_id": str(ev.get("home_team_key", "")),
                    "away_id": str(ev.get("away_team_key", "")),
                    "kickoff": ev.get("event_date", "") + "T" + ev.get("event_time", "00:00"),
                    "status": _parse_fixture_status(status),
                    "score": ev.get("event_final_result", ""),
                    "round": ev.get("league_round", ""),
                    "country": ev.get("country_name", ""),
                })
        except Exception as e:
            print(f"AllSports fixtures error: {e}")

    # Source 2: AllSportsApi live matches (currently in-play)
    if settings.ALLSPORTS_API_KEY and not fixtures:
        try:
            live = await allsports.fetch_live_matches()
            for m in live:
                fixtures.append({
                    "source": "allsports-live",
                    "match_id": m["id"],
                    "league": m.get("league", ""),
                    "home_name": m.get("home", ""),
                    "away_name": m.get("away", ""),
                    "kickoff": "",
                    "status": "live",
                    "score": m.get("score", ""),
                    "round": "",
                    "minute": m.get("minute", 0),
                })
        except Exception:
            pass

    # Source 3: The Odds API — upcoming matches with odds
    if settings.has_odds:
        try:
            # Fetch from multiple sport keys
            sport_keys = [
                "soccer_epl", "soccer_spain_la_liga", "soccer_germany_bundesliga",
                "soccer_italy_serie_a", "soccer_france_ligue_one",
                "soccer_uefa_champs_league", "soccer_fifa_world_cup",
            ]
            for sport in sport_keys:
                odds_data = await odds_api.fetch_all_odds(sport)
                if not odds_data:
                    continue
                for match in odds_data:
                    mid = match.get("id", "")
                    # Check if already in fixtures
                    existing_ids = {f["match_id"] for f in fixtures}
                    if mid in existing_ids:
                        continue
                    fixtures.append({
                        "source": "odds-api",
                        "match_id": mid,
                        "league": _sport_key_to_league(sport),
                        "home_name": match.get("home_team", ""),
                        "away_name": match.get("away_team", ""),
                        "kickoff": match.get("commence_time", ""),
                        "status": "upcoming",
                        "odds_sport": sport,
                        "odds_home": match.get("home", 0),
                        "odds_draw": match.get("draw", 0),
                        "odds_away": match.get("away", 0),
                    })
        except Exception as e:
            print(f"Odds API fixtures error: {e}")

    # Sort by kickoff time
    fixtures.sort(key=lambda x: x.get("kickoff", ""))

    return {
        "fixtures": fixtures,
        "count": len(fixtures),
        "date_range": {"from": date_from, "to": date_to},
        "sources": {
            "allsports": bool(settings.ALLSPORTS_API_KEY),
            "odds_api": settings.has_odds,
        },
    }


@app.post("/api/admin/import-fixture")
async def admin_import_fixture(data: dict):
    """
    Import a fixture from the fixtures list into managed matches.
    Auto-populates match config from the fixture data.
    """
    match_id = data.get("match_id", "")
    if not match_id:
        raise HTTPException(400, "match_id required")

    home = data.get("home_name", "Home")
    away = data.get("away_name", "Away")

    config = {
        "match_id": match_id,
        "league": data.get("league", ""),
        "round": data.get("round", ""),
        "home_name": home,
        "away_name": away,
        "home_short": home[:3].upper() if home else "HOM",
        "away_short": away[:3].upper() if away else "AWY",
        "home_name_cn": data.get("home_name_cn", ""),
        "away_name_cn": data.get("away_name_cn", ""),
        "home_elo": data.get("home_elo", 1500),
        "away_elo": data.get("away_elo", 1500),
        "api_football_id": data.get("api_football_id", match_id),
        "odds_sport": data.get("odds_sport", "soccer_epl"),
        "active": True,
        "kickoff": data.get("kickoff", ""),
        "status": data.get("status", "upcoming"),
        "live_enabled": False,
    }

    managed_matches[match_id] = config
    return {"status": "ok", "match_id": match_id, "config": config}


def _parse_fixture_status(status: str) -> str:
    """Parse AllSportsApi status into simplified status."""
    if not status:
        return "upcoming"
    s = status.strip()
    if s.isdigit() or s == "Half Time":
        return "live"
    if s in ("Finished", "After Pen.", "After ET"):
        return "finished"
    if s in ("Postponed", "Cancelled", "Suspended"):
        return "cancelled"
    return "upcoming"


def _sport_key_to_league(sport_key: str) -> str:
    """Map The Odds API sport key to league name."""
    return {
        "soccer_epl": "EPL",
        "soccer_spain_la_liga": "La Liga",
        "soccer_germany_bundesliga": "Bundesliga",
        "soccer_italy_serie_a": "Serie A",
        "soccer_france_ligue_one": "Ligue 1",
        "soccer_uefa_champs_league": "UCL",
        "soccer_fifa_world_cup": "FIFA World Cup",
        "soccer_uefa_europa_league": "UEL",
    }.get(sport_key, sport_key)


# ══════════════════════════════════════════════════════════════
# SIGNAL CONTROL — REST API
# ══════════════════════════════════════════════════════════════

class SignalAction(BaseModel):
    match_id: str = "demo"
    action: str  # "confirm" | "reject"


@app.post("/api/signal/confirm")
async def signal_confirm(body: SignalAction):
    """Confirm or reject the current signal."""
    ss = _get_signal_state(body.match_id)
    if body.action == "confirm":
        if ss["state"] != "ready":
            raise HTTPException(400, f"Cannot confirm signal in state '{ss['state']}'. Must be 'ready'.")
        ss["state"] = "confirmed"
        ss["confirmed_at"] = time.time()
        ss["cooldown_remaining"] = 0
        # Trigger Stage 5 SIGNAL_CONFIRM broadcast
        try:
            if broadcast_engine:
                sc_text = broadcast_engine.get_template(
                    "SIGNAL_CONFIRM", "en",
                    line=ss.get("line", 2.5),
                    edge=ss.get("edge", 0),
                    model_prob=ss.get("model_prob", 0),
                )
                if sc_text:
                    broadcast_state["text"] = sc_text
                    broadcast_state["stage"] = "SIGNAL_CONFIRM"
                    broadcast_state["priority"] = "high"
                    broadcast_state["timestamp"] = time.time()
                    broadcast_state["speaking"] = True
                    broadcast_state["speak_until"] = time.time() + 8
                    broadcast_engine.record_broadcast()
        except Exception:
            pass
    elif body.action == "reject":
        if ss["state"] not in ("ready", "pending"):
            raise HTTPException(400, f"Cannot reject signal in state '{ss['state']}'.")
        ss["state"] = "idle"
        ss["rejected_at"] = time.time()
        ss["confirmed_at"] = None
    else:
        raise HTTPException(400, f"Invalid action '{body.action}'. Must be 'confirm' or 'reject'.")

    return {"status": "ok", "signal_state": ss}


@app.get("/api/signal/state")
async def signal_get_state(match_id: str = "demo"):
    """Return current signal state for a match."""
    ss = _get_signal_state(match_id)
    return {
        "status": "ok",
        "signal_state": {
            "state": ss["state"],
            "line": ss["line"],
            "model_prob": ss["model_prob"],
            "market_prob": ss["market_prob"],
            "edge": ss["edge"],
            "confirmed_at": ss["confirmed_at"],
            "cooldown_remaining": ss.get("cooldown_remaining", 0),
        },
    }


# ══════════════════════════════════════════════════════════════
# PERFORMANCE TRACKER — REST API
# ══════════════════════════════════════════════════════════════

@app.get("/api/performance")
async def get_performance():
    """Return session performance summary."""
    return performance_tracker.get_summary()


# ══════════════════════════════════════════════════════════════
# TTS — Text-to-Speech Announcement
# ══════════════════════════════════════════════════════════════

class AnnounceRequest(BaseModel):
    text: str
    lang: str = "en"
    template_key: Optional[str] = None  # reserved for future broadcast templates


@app.post("/api/announce")
async def announce(body: AnnounceRequest):
    """Generate TTS audio from text and return as MP3."""
    audio = await tts_engine.speak(body.text, lang=body.lang)
    if audio is None:
        raise HTTPException(500, "TTS generation failed — check server logs for details")
    return Response(content=audio, media_type="audio/mpeg")


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
        # Line movement tracking
        self._prev_line = 2.5
        self._prev_over_odds = 1.90

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

        # Goal Window detection
        goal_window = goal_window_engine.compute(
            tg_live_state,
            total_goals["lambda_live"],
            total_goals["tempo_raw"],
        )

        # ── Line Movement ──
        current_line = demo_odds_ou.get("line", 2.5)
        current_over_odds = demo_odds_ou.get("over_odds", 1.90)
        current_under_odds = demo_odds_ou.get("under_odds", 1.90)

        if current_line < self._prev_line:
            lm_direction = "UNDER"
        elif current_line > self._prev_line:
            lm_direction = "OVER"
        else:
            lm_direction = "NEUTRAL"

        if current_over_odds < self._prev_over_odds - 0.01:
            lm_pressure = "OVER"
        elif current_over_odds > self._prev_over_odds + 0.01:
            lm_pressure = "UNDER"
        else:
            lm_pressure = "NEUTRAL"

        line_movement = {
            "current_line": current_line,
            "previous_line": self._prev_line,
            "over_odds": current_over_odds,
            "over_odds_prev": self._prev_over_odds,
            "under_odds": current_under_odds,
            "direction": lm_direction,
            "pressure": lm_pressure,
        }

        self._prev_line = current_line
        self._prev_over_odds = current_over_odds

        # ── Risk Engine ──
        risk = risk_engine.compute(
            ai_prob=prob,
            edge=total_goals.get("edge"),
            tempo_c=total_goals.get("tempo_raw"),
        )

        # ── Signal Control ──
        sc = _compute_signal_control(
            "demo",
            edge=total_goals.get("edge", 0),
            line=total_goals.get("line", 2.5),
            model_prob=total_goals.get("model_prob_over", 0),
            market_prob=total_goals.get("market_prob_over", 0),
        )

        # ── Post-Match Engine ──
        post_match_engine.update(
            lambda_live=total_goals.get("lambda_live", 0),
            edge=total_goals.get("edge", 0),
            lambda_pre=total_goals.get("lambda_pre", 0),
        )

        if self.minute >= 90:
            post_match = post_match_engine.generate_summary(self.score, self.minute)
        else:
            post_match = {"active": False}

        # ── Score Matrix ──
        try:
            home_share = prob["home"] / max(prob["home"] + prob["away"], 1)
            away_share = 1.0 - home_share
            sm_lambda_home = total_goals["lambda_live"] * home_share
            sm_lambda_away = total_goals["lambda_live"] * away_share
            score_matrix = score_matrix_engine.compute(sm_lambda_home, sm_lambda_away)
        except Exception:
            score_matrix = None

        # ═══ v1.1 Full Payload ═══
        payload = {
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
            "score_matrix": score_matrix,
            "goal_window": goal_window,
            "line_movement": line_movement,
            "risk": risk,
            "signal_control": sc,
            "performance": performance_tracker.get_summary(),
            "post_match": post_match,
            "prediction_history": history_tracker.get_summary(),
            "pre_match_rec": _get_cached_prematch("managed", {
                "home_elo": 1650, "away_elo": 1580, "league": "EPL",
            }, self.minute),
            "model_stats": _backtest_data,
        }

        # ── Auto-record prediction result ──
        _auto_record_prediction(
            "demo", prob, confidence, self.minute, self.score,
            {"home_name": "Arsenal", "away_name": "Chelsea",
             "home_name_cn": "阿森纳", "away_name_cn": "切尔西", "league": "EPL"},
            total_goals,
        )

        # ── Broadcast (computed after full payload is built) ──
        try:
            payload["broadcast"] = _compute_broadcast(payload, lang="en")
            # Post-match broadcast: override with Stage 10 summary when full time
            if self.minute >= 90 and report.get("full_time_ready") and broadcast_engine:
                try:
                    pm_text = broadcast_engine.get_template(
                        "POST_MATCH", "en",
                        home=payload["match"]["home"]["name"],
                        away=payload["match"]["away"]["name"],
                        score=payload["match"]["score"],
                        summary=post_match,
                    )
                    if pm_text and broadcast_engine.can_broadcast("critical"):
                        broadcast_state["text"] = pm_text
                        broadcast_state["stage"] = "POST_MATCH"
                        broadcast_state["priority"] = "critical"
                        broadcast_state["timestamp"] = time.time()
                        broadcast_state["speaking"] = True
                        broadcast_state["speak_until"] = time.time() + 8
                        broadcast_engine.record_broadcast()
                        payload["broadcast"] = {
                            "text": pm_text, "stage": "POST_MATCH", "priority": "critical",
                            "timestamp": broadcast_state["timestamp"],
                            "speaking": True, "cooldown_remaining": 0,
                        }
                except Exception:
                    pass
        except Exception:
            payload["broadcast"] = {"text": "", "stage": "", "priority": "normal",
                                     "timestamp": 0, "speaking": False, "cooldown_remaining": 0}

        return payload


# ══════════════════════════════════════════════════════════════
# WEBSOCKET
# ══════════════════════════════════════════════════════════════

@app.websocket("/ws/{match_id}")
async def websocket_endpoint(ws: WebSocket, match_id: str):
    await ws_manager.connect(ws, match_id)
    ms = state_store.get(match_id)
    try:
        # Only use demo simulator when explicitly requesting "demo"
        if match_id == "demo":
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
            live_prev_line = 2.5
            live_prev_over_odds = 1.90
            _config_populated = bool(config)
            _match_finished = False

            while True:
                try:
                    # Fetch live data from best available source
                    if settings.ALLSPORTS_API_KEY:
                        live = await allsports.fetch_match(api_id)
                    elif settings.SPORTMONKS_API_KEY:
                        live = await sportmonks.fetch_match(api_id)
                    else:
                        live = await football_api.fetch_match(api_id)

                    # Auto-populate config from API response if not managed
                    if not _config_populated:
                        mi = live.get("match", {})
                        config = {
                            "match_id": match_id,
                            "league": mi.get("league", ""),
                            "round": mi.get("round", ""),
                            "home_name": mi.get("home_name", "Home"),
                            "away_name": mi.get("away_name", "Away"),
                            "home_short": mi.get("home_short", "HOM"),
                            "away_short": mi.get("away_short", "AWY"),
                            "home_name_cn": "",
                            "away_name_cn": "",
                            "home_elo": 1500,
                            "away_elo": 1500,
                            "odds_sport": "soccer_epl",
                        }
                        _config_populated = True

                    # Fetch odds (may be None for non-matched IDs)
                    try:
                        odds_data = await odds_api.fetch_odds(
                            match_id, config.get("odds_sport", "soccer_epl"))
                    except Exception:
                        odds_data = None

                    _match_finished = live.get("minute", 0) >= 90
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

                    # Predict (model may fail on feature mismatch — fallback to odds)
                    pred_ok = False
                    if pred:
                        try:
                            result = pred.predict(live_state)
                            prob = result["probability"]
                            quant_data = result["quant"]
                            pred_ok = True
                        except Exception:
                            pass
                    if not pred_ok:
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

                    # Goal Window detection
                    goal_window = goal_window_engine.compute(
                        live_state,
                        total_goals["lambda_live"],
                        total_goals["tempo_raw"],
                    )

                    # Line Movement (live mode)
                    lm_odds_ou = odds_data.get("totals") if odds_data else {}
                    lm_current_line = lm_odds_ou.get("line", 2.5) if lm_odds_ou else 2.5
                    lm_current_over = lm_odds_ou.get("over_odds", 1.90) if lm_odds_ou else 1.90
                    lm_current_under = lm_odds_ou.get("under_odds", 1.90) if lm_odds_ou else 1.90

                    if lm_current_line < live_prev_line:
                        lm_dir = "UNDER"
                    elif lm_current_line > live_prev_line:
                        lm_dir = "OVER"
                    else:
                        lm_dir = "NEUTRAL"

                    if lm_current_over < live_prev_over_odds - 0.01:
                        lm_pres = "OVER"
                    elif lm_current_over > live_prev_over_odds + 0.01:
                        lm_pres = "UNDER"
                    else:
                        lm_pres = "NEUTRAL"

                    line_movement = {
                        "current_line": lm_current_line,
                        "previous_line": live_prev_line,
                        "over_odds": lm_current_over,
                        "over_odds_prev": live_prev_over_odds,
                        "under_odds": lm_current_under,
                        "direction": lm_dir,
                        "pressure": lm_pres,
                    }

                    live_prev_line = lm_current_line
                    live_prev_over_odds = lm_current_over

                    # Risk Engine (live mode)
                    risk = risk_engine.compute(
                        ai_prob=prob,
                        edge=total_goals.get("edge"),
                        tempo_c=total_goals.get("tempo_raw"),
                    )

                    # Post-Match Engine (live mode)
                    post_match_engine.update(
                        lambda_live=total_goals.get("lambda_live", 0),
                        edge=total_goals.get("edge", 0),
                        lambda_pre=total_goals.get("lambda_pre", 0),
                    )

                    if minute >= 90:
                        post_match = post_match_engine.generate_summary(
                            [live_state["home_goals"], live_state["away_goals"]], minute
                        )
                    else:
                        post_match = {"active": False}

                    # ── Score Matrix (live mode) ──
                    try:
                        _home_share = prob["home"] / max(prob["home"] + prob["away"], 1)
                        _away_share = 1.0 - _home_share
                        _sm_lh = total_goals["lambda_live"] * _home_share
                        _sm_la = total_goals["lambda_live"] * _away_share
                        live_score_matrix = score_matrix_engine.compute(_sm_lh, _sm_la)
                    except Exception:
                        live_score_matrix = None

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
                        "score_matrix": live_score_matrix,
                        "goal_window": goal_window,
                        "line_movement": line_movement,
                        "risk": risk,
                        "signal_control": _compute_signal_control(
                            match_id,
                            edge=total_goals.get("edge") or 0,
                            line=total_goals.get("line") or 2.5,
                            model_prob=total_goals.get("model_prob_over") or 0,
                            market_prob=total_goals.get("market_prob_over") or 0,
                        ),
                        "performance": performance_tracker.get_summary(),
                        "post_match": post_match,
                        "prediction_history": history_tracker.get_summary(),
                        "pre_match_rec": _get_cached_prematch(match_id, config, minute),
                        "model_stats": _backtest_data,
                    }

                    # ── Auto-record prediction result (live mode) ──
                    _auto_record_prediction(
                        match_id, prob, quant_data.get("confidence", 75),
                        minute, [live_state["home_goals"], live_state["away_goals"]],
                        config, total_goals,
                    )

                    # ── Broadcast (live mode) ──
                    try:
                        payload["broadcast"] = _compute_broadcast(payload, lang="en")
                        # Post-match broadcast: override with Stage 10 summary when full time
                        if minute >= 90 and report.get("full_time_ready") and broadcast_engine:
                            try:
                                pm_text = broadcast_engine.get_template(
                                    "POST_MATCH", "en",
                                    home=match_info["home"]["name"],
                                    away=match_info["away"]["name"],
                                    score=match_info["score"],
                                    summary=post_match,
                                )
                                if pm_text and broadcast_engine.can_broadcast("critical"):
                                    broadcast_state["text"] = pm_text
                                    broadcast_state["stage"] = "POST_MATCH"
                                    broadcast_state["priority"] = "critical"
                                    broadcast_state["timestamp"] = time.time()
                                    broadcast_state["speaking"] = True
                                    broadcast_state["speak_until"] = time.time() + 8
                                    broadcast_engine.record_broadcast()
                                    payload["broadcast"] = {
                                        "text": pm_text, "stage": "POST_MATCH", "priority": "critical",
                                        "timestamp": broadcast_state["timestamp"],
                                        "speaking": True, "cooldown_remaining": 0,
                                    }
                            except Exception:
                                pass
                    except Exception:
                        payload["broadcast"] = {"text": "", "stage": "", "priority": "normal",
                                                 "timestamp": 0, "speaking": False, "cooldown_remaining": 0}

                    await ws.send_json(payload)

                except ValueError as e:
                    # Match not found — send structured WAITING payload
                    home_name = config.get("home_name", "Home")
                    away_name = config.get("away_name", "Away")
                    await ws.send_json({
                        "meta": {"match_id": match_id, "source": "waiting",
                                 "health": "WAITING", "error": str(e),
                                 "last_update_ts": 0, "seq": ms.bump_seq()},
                        "match": {"league": config.get("league", ""),
                                  "round": config.get("round", ""),
                                  "minute": 0, "half": "PRE",
                                  "home_goals": 0, "away_goals": 0,
                                  "home_short": home_name[:3].upper(),
                                  "away_short": away_name[:3].upper(),
                                  "home_name": home_name,
                                  "away_name": away_name},
                    })
                except Exception as e:
                    # Temporary API error — send DEGRADED with match context
                    await ws.send_json({
                        "meta": {"match_id": match_id, "source": "error",
                                 "health": "DEGRADED", "error": str(e),
                                 "last_update_ts": 0, "seq": ms.bump_seq()},
                        "match": {"league": config.get("league", ""),
                                  "round": config.get("round", ""),
                                  "minute": 0, "half": "PRE",
                                  "home_goals": 0, "away_goals": 0,
                                  "home_short": config.get("home_short", "HOM"),
                                  "away_short": config.get("away_short", "AWY"),
                                  "home_name": config.get("home_name", "Home"),
                                  "away_name": config.get("away_name", "Away")},
                    })

                # Slower polling for finished matches (10s vs 2s)
                await asyncio.sleep(10 if _match_finished else settings.WS_PUSH_INTERVAL)

    except WebSocketDisconnect:
        ws_manager.disconnect(ws, match_id)


# ── Startup ───────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    print("=" * 50)
    print("  AI Football Quant Terminal v2.5 — Backend")
    print(f"  Mode: {'DEMO' if settings.demo_mode else 'LIVE'}")
    print(f"  Live source: {settings.live_source}")
    print(f"  Odds: {'The Odds API' if settings.has_odds else 'None'}")
    print(f"  Model: {'Loaded' if get_predictor() else 'Not found (fallback)'}")
    print("=" * 50)

    # Start league prediction refresh loop
    asyncio.create_task(_league_prediction_loop())


async def _league_prediction_loop():
    """Refresh league predictions on startup, then every 30 minutes."""
    while True:
        try:
            await league_predictions.refresh()
        except Exception as e:
            print(f"[LeaguePredictions] Error: {e}")
        await asyncio.sleep(1800)


# ── Mount admin static files (after all routes) ─────────────
import os
_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/admin", StaticFiles(directory=_static_dir, html=True), name="admin")

# ── Mount frontend dist (React SPA) ──────────────────────────
_frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.isdir(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
