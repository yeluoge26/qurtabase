"""
Per-match state manager

Maintains rolling state for each match:
  - Previous probabilities (for delta calculation)
  - Event deduplication
  - Rolling calibration buffer (Brier window)
  - Last update timestamps (for health/staleness)
"""

import time
from collections import deque


class MatchState:
    def __init__(self, match_id: str):
        self.match_id = match_id
        self.last_probability = None
        self.last_update_ts = 0.0
        self.last_stats_ts = 0.0
        self.last_odds_ts = 0.0
        self.seen_event_ids: set = set()
        self.events: list = []
        self.seq = 0
        self.brier_buffer: deque = deque(maxlen=60)  # ~20 min at 2s interval
        self.probability_history: deque = deque(maxlen=300)

    def update_probability(self, prob: dict) -> dict:
        """Update probability and return delta."""
        delta = {"home": 0.0, "draw": 0.0, "away": 0.0}
        if self.last_probability:
            delta["home"] = round(prob["home"] - self.last_probability["home"], 2)
            delta["draw"] = round(prob["draw"] - self.last_probability["draw"], 2)
            delta["away"] = round(prob["away"] - self.last_probability["away"], 2)
        self.last_probability = prob.copy()
        self.probability_history.append({**prob, "ts": time.time()})
        return delta

    def add_event(self, event: dict) -> bool:
        """Add event if not seen before. Returns True if new."""
        eid = event.get("id", f"{event.get('minute', 0)}_{event.get('type', '')}")
        if eid in self.seen_event_ids:
            return False
        self.seen_event_ids.add(eid)
        self.events.append(event)
        # Keep last 20 events
        if len(self.events) > 20:
            self.events = self.events[-20:]
        return True

    def get_recent_events(self, n: int = 5) -> list:
        """Get last N events, newest first."""
        return list(reversed(self.events[-n:]))

    def bump_seq(self) -> int:
        self.seq += 1
        return self.seq

    def get_health(self, stale_threshold: float = 60.0) -> str:
        """Determine data health status."""
        now = time.time()
        if self.last_update_ts == 0:
            return "OK"  # No data yet, assume OK
        age = now - self.last_update_ts
        if age > stale_threshold:
            return "STALE"
        if self.last_odds_ts == 0 or (now - self.last_odds_ts > 120):
            return "DEGRADED"
        return "OK"

    def add_brier_sample(self, predicted: dict, actual_result: str | None):
        """Add a sample to rolling Brier buffer."""
        if actual_result is None:
            return
        # actual_result: "H", "D", "A"
        actual = {"H": [1, 0, 0], "D": [0, 1, 0], "A": [0, 0, 1]}.get(actual_result, [0, 0, 0])
        pred = [predicted.get("home", 0) / 100, predicted.get("draw", 0) / 100, predicted.get("away", 0) / 100]
        brier = sum((p - a) ** 2 for p, a in zip(pred, actual)) / 3
        self.brier_buffer.append(brier)

    def get_rolling_brier(self) -> float | None:
        if not self.brier_buffer:
            return None
        return round(sum(self.brier_buffer) / len(self.brier_buffer), 4)


class MatchStateStore:
    """In-memory store for all match states."""

    def __init__(self):
        self._states: dict[str, MatchState] = {}

    def get(self, match_id: str) -> MatchState:
        if match_id not in self._states:
            self._states[match_id] = MatchState(match_id)
        return self._states[match_id]

    def remove(self, match_id: str):
        self._states.pop(match_id, None)

    def list_active(self) -> list[str]:
        return list(self._states.keys())
