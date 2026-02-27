"""
Risk Engine — Signal & Model Risk Metrics

Tracks probability stability, signal consistency, and market volatility
to provide a composite risk assessment for the quant terminal.
"""

import math
from collections import deque


class RiskEngine:
    """Compute risk metrics from probability history, edge history, and tempo."""

    HISTORY_SIZE = 10

    def __init__(self):
        self._prob_history: deque[float] = deque(maxlen=self.HISTORY_SIZE)
        self._edge_history: deque[float] = deque(maxlen=self.HISTORY_SIZE)

    def compute(self, ai_prob: dict, edge: float | None, tempo_c: float | None) -> dict:
        """
        Compute risk panel metrics.

        Args:
            ai_prob: {"home": float, "draw": float, "away": float} — model probabilities
            edge: current edge value (can be None)
            tempo_c: tempo coefficient from total goals engine (0.6–1.7 range)

        Returns:
            {
                "model_variance": float,
                "signal_stability": int,
                "market_volatility": str,  # "Low" | "Medium" | "High"
                "drawdown_guard": str,     # "Active" (placeholder)
            }
        """
        # Store snapshots
        home_prob = ai_prob.get("home", 50.0) if ai_prob else 50.0
        self._prob_history.append(home_prob)

        if edge is not None:
            self._edge_history.append(edge)

        # ── 1. Model Variance: stddev of last 10 home prob snapshots ──
        if len(self._prob_history) >= self.HISTORY_SIZE:
            mean = sum(self._prob_history) / len(self._prob_history)
            variance = sum((x - mean) ** 2 for x in self._prob_history) / len(self._prob_history)
            model_variance = round(math.sqrt(variance), 2)
        else:
            model_variance = 0.0

        # ── 2. Signal Stability: 100 - (sign_changes / 10 * 100) ──
        if len(self._edge_history) >= 2:
            sign_changes = 0
            items = list(self._edge_history)
            for i in range(1, len(items)):
                if items[i] * items[i - 1] < 0:  # sign changed
                    sign_changes += 1
            signal_stability = round(100 - (sign_changes / self.HISTORY_SIZE * 100))
            signal_stability = max(0, min(100, signal_stability))
        else:
            signal_stability = 100

        # ── 3. Market Volatility: based on tempo_c ──
        if tempo_c is None:
            market_volatility = "Medium"
        elif tempo_c < 0.9:
            market_volatility = "Low"
        elif tempo_c <= 1.3:
            market_volatility = "Medium"
        else:
            market_volatility = "High"

        # ── 4. Drawdown Guard: placeholder ──
        drawdown_guard = "Active"

        return {
            "model_variance": model_variance,
            "signal_stability": signal_stability,
            "market_volatility": market_volatility,
            "drawdown_guard": drawdown_guard,
        }
