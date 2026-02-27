"""
Goal Window Detection Engine

Detects high-goal-probability windows during live matches.
A "Goal Window" activates when match tempo and scoring rate exceed
league-average thresholds, signalling an elevated probability of
imminent goals.

Activation:  tempo_c >= 1.15 AND lambda_rate > 0.029 goals/min
Deactivation: tempo_c < 1.05 for > 3 consecutive minutes (180 s)
"""

import time


class GoalWindowEngine:
    """Detect and track high-scoring windows in live matches."""

    # Activation thresholds
    TEMPO_ACTIVATE = 1.15       # Tempo_c must reach this to open a window
    TEMPO_DEACTIVATE = 1.05     # Tempo_c must drop below this to start cooldown
    LAMBDA_RATE_AVG = 0.029     # League-average goals per minute (benchmark)

    # Deactivation requires tempo below threshold for this many seconds
    DEACTIVATE_HOLD_SEC = 180   # 3 minutes

    # Confidence formula: clip((tempo_c - 1.0) / 0.7 * 100, 0, 99)
    CONF_BASE = 1.0
    CONF_RANGE = 0.7

    # Duration estimate brackets (minutes of elevated tempo → estimated range)
    DURATION_BRACKETS = [
        (600, "10-15"),   # >10 min elevated → expect 10-15 more
        (420, "8-12"),    # >7 min
        (300, "5-10"),    # >5 min
        (120, "3-8"),     # >2 min
        (0,   "2-5"),     # just started
    ]

    def __init__(self):
        self._active = False
        self._window_start_ts: float = 0.0        # when window opened
        self._tempo_below_since: float = 0.0       # when tempo first dropped below threshold
        self._last_elevated_ts: float = 0.0        # last time tempo was elevated

    @staticmethod
    def _clip(v: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, v))

    def _estimate_duration(self, elapsed_sec: float) -> str:
        """Estimate remaining window duration based on how long it has been active."""
        for threshold_sec, label in self.DURATION_BRACKETS:
            if elapsed_sec >= threshold_sec:
                return label
        return "2-5"

    def compute(self, live_state: dict, lambda_live: float, tempo_c: float) -> dict:
        """
        Evaluate whether a Goal Window is active.

        Args:
            live_state: dict with at least {"minute": int}
            lambda_live: current λ_total_live (expected total goals for the match)
            tempo_c: clipped tempo factor from TotalGoalsEngine

        Returns:
            dict with window status, confidence, duration, and diagnostics.
        """
        now = time.time()
        minute = max(1, live_state.get("minute", 1))
        remaining_min = max(1, 90 - minute)

        # Current scoring rate: remaining expected goals / remaining minutes
        # lambda_live includes goals already scored, so remaining = lambda_live - goals_so_far
        goals_so_far = live_state.get("home_goals", 0) + live_state.get("away_goals", 0)
        lambda_remaining = max(0, lambda_live - goals_so_far)
        lambda_rate = lambda_remaining / remaining_min

        # ── Activation / deactivation logic ──────────────────────
        conditions_met = (tempo_c >= self.TEMPO_ACTIVATE and
                          lambda_rate > self.LAMBDA_RATE_AVG)

        tempo_elevated = tempo_c >= self.TEMPO_DEACTIVATE

        if not self._active:
            # Try to activate
            if conditions_met:
                self._active = True
                self._window_start_ts = now
                self._tempo_below_since = 0.0
                self._last_elevated_ts = now
        else:
            # Window is active — check deactivation
            if tempo_elevated:
                # Tempo is still above deactivation threshold; reset cooldown
                self._tempo_below_since = 0.0
                self._last_elevated_ts = now
            else:
                # Tempo dropped below deactivation threshold
                if self._tempo_below_since == 0.0:
                    self._tempo_below_since = now
                elif now - self._tempo_below_since >= self.DEACTIVATE_HOLD_SEC:
                    # Tempo has been below threshold for >3 minutes → close window
                    self._active = False
                    self._window_start_ts = 0.0
                    self._tempo_below_since = 0.0

        # ── Compute outputs ──────────────────────────────────────
        elapsed_sec = 0
        estimated_duration = ""
        confidence = 0

        if self._active:
            elapsed_sec = int(now - self._window_start_ts)
            estimated_duration = self._estimate_duration(elapsed_sec)
            confidence = int(self._clip(
                (tempo_c - self.CONF_BASE) / self.CONF_RANGE * 100,
                0, 99
            ))

        return {
            "active": self._active,
            "confidence": confidence,
            "estimated_duration_min": estimated_duration,
            "elapsed_sec": elapsed_sec,
            "tempo_c": round(tempo_c, 3),
            "lambda_rate": round(lambda_rate, 4),
        }
