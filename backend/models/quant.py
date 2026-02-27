"""
Quant Engine — Fallback quantitative indicators
Used when the ML model is not loaded.
"""


class QuantEngine:
    def compute(self, live_state: dict, prob: dict) -> dict:
        """Compute quant indicators without ML model."""
        minute = live_state.get("minute", 0)
        hg = live_state.get("home_goals", 0)
        ag = live_state.get("away_goals", 0)
        h_shots = live_state.get("home_shots", 0)
        a_shots = live_state.get("away_shots", 0)
        h_poss = live_state.get("home_possession", 50)
        hxg = live_state.get("home_xg", hg * 0.9 + 0.2)
        axg = live_state.get("away_xg", ag * 0.9 + 0.2)

        tf = minute / 90 if minute > 0 else 0

        pressure = 50 + (h_shots - a_shots) * 2.5 + (h_poss - 50) * 0.6
        pressure = max(5, min(98, pressure))

        momentum = (h_shots - a_shots) * 1.5 + (hxg - axg) * 8 + (hg - ag) * 5
        momentum = max(-50, min(50, momentum))

        volatility = 0.3 + tf * 0.5 + abs(hg - ag) * 0.1
        volatility = min(1.5, volatility)

        risk = 30 + (1 - tf) * 20 + a_shots * 0.8
        risk = max(5, min(90, risk))

        if minute < 80:
            ws = max(2, int(8 - tf * 5))
            we = max(5, int(15 - tf * 8))
            goal_window = f"{ws}-{we}"
        else:
            goal_window = "LOW"

        max_prob = max(prob.get("home", 50), prob.get("draw", 25), prob.get("away", 25))
        confidence = min(98, max(55, int(max_prob * 0.8 + 20)))

        probs = [prob.get("home", 50) / 100, prob.get("draw", 25) / 100, prob.get("away", 25) / 100]
        variance = round(sum(p * (1 - p) for p in probs) / 3, 4)

        return {
            "pressure_index": round(pressure),
            "momentum": round(momentum),
            "volatility": round(volatility, 2),
            "risk_concede": round(risk),
            "goal_window": goal_window,
            "confidence": confidence,
            "model_variance": variance,
            "xg_delta": round(hxg - axg, 2),
            "conf_interval": min(99, max(80, int(confidence * 1.05))),
        }
