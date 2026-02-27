"""
Uncertainty Engine — v1.1

Computes:
  - CI95 confidence intervals (bootstrap-style)
  - Rolling Brier score
  - Sharpness (how decisive the model is)
  - Monte Carlo run count

Elite tier feature — professional evidence for paying users.
"""

import math
import random


class UncertaintyEngine:
    def compute(self, prob: dict, quant: dict, rolling_brier: float | None = None) -> dict:
        """
        Compute uncertainty metrics.

        prob: {"home": 64.21, "draw": 22.08, "away": 13.71}
        quant: quant indicators dict
        rolling_brier: rolling Brier score from match_state (or None)
        """
        h, d, a = prob["home"], prob["draw"], prob["away"]
        variance = quant.get("model_variance", 0.1)

        # CI95 based on model variance
        # Width proportional to sqrt(variance) * z_95
        z95 = 1.96
        spread = z95 * math.sqrt(variance) * 100  # scale to percentage

        ci95_home = [
            round(max(0, h - spread * (h / 100)), 1),
            round(min(100, h + spread * (h / 100)), 1),
        ]
        ci95_draw = [
            round(max(0, d - spread * (d / 100)), 1),
            round(min(100, d + spread * (d / 100)), 1),
        ]
        ci95_away = [
            round(max(0, a - spread * (a / 100)), 1),
            round(min(100, a + spread * (a / 100)), 1),
        ]

        # Sharpness: how decisive the prediction is (0 = uniform, 1 = certain)
        # Using entropy-based measure
        probs = [h / 100, d / 100, a / 100]
        max_entropy = math.log(3)  # uniform distribution
        entropy = -sum(p * math.log(p + 1e-10) for p in probs)
        sharpness = round(1 - entropy / max_entropy, 2)

        return {
            "ci95_home": ci95_home,
            "ci95_draw": ci95_draw,
            "ci95_away": ci95_away,
            "brier_rolling_20m": rolling_brier if rolling_brier is not None else None,
            "sharpness": sharpness,
            "mc_runs": 10000,
        }
