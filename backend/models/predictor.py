"""
Live Match Prediction Engine

Two-stage architecture:
  1. Pre-match: XGBoost outputs initial P(H/D/A) based on odds/Elo/xG
  2. In-match: Poisson dynamic correction based on score/time/red cards
"""

import math
import json
import joblib


class LivePredictor:
    def __init__(self, model_path: str = "models/trained/model_calibrated.pkl"):
        self.model = joblib.load(model_path)

        # Load metadata
        meta_path = model_path.replace(".pkl", "").rsplit("/", 1)[0] + "/model_meta.json"
        try:
            with open(meta_path) as f:
                self.meta = json.load(f)
        except FileNotFoundError:
            self.meta = {"class_names": ["Away", "Draw", "Home"]}

        self.avg_total_goals = 2.7
        self.prev_prob = None

    def predict(self, live_state: dict) -> dict:
        """
        Main prediction function.

        Input: live match state dict
        Output: full prediction result (probability + quant indicators)
        """
        minute = live_state.get("minute", 0)
        hg = live_state.get("home_goals", 0)
        ag = live_state.get("away_goals", 0)
        h_red = live_state.get("home_red", 0)
        a_red = live_state.get("away_red", 0)

        # Step 1: Pre-match model probability
        features = self._build_features(live_state)
        proba = self.model.predict_proba([features])[0]
        # Order: [Away=0, Draw=1, Home=2]
        prior_away, prior_draw, prior_home = proba[0], proba[1], proba[2]

        # Step 2: Poisson in-match correction
        if minute > 0:
            p_home, p_draw, p_away = self._poisson_update(
                prior_home, prior_draw, prior_away,
                minute, hg, ag, h_red, a_red
            )
        else:
            p_home, p_draw, p_away = prior_home, prior_draw, prior_away

        # Normalize
        total = p_home + p_draw + p_away
        p_home, p_draw, p_away = p_home / total, p_draw / total, p_away / total

        prob = {
            "home": round(p_home * 100, 2),
            "draw": round(p_draw * 100, 2),
            "away": round(p_away * 100, 2),
        }

        # Delta
        delta = {"home": 0.0, "draw": 0.0, "away": 0.0}
        if self.prev_prob:
            delta["home"] = round(prob["home"] - self.prev_prob["home"], 2)
            delta["draw"] = round(prob["draw"] - self.prev_prob["draw"], 2)
            delta["away"] = round(prob["away"] - self.prev_prob["away"], 2)
        self.prev_prob = prob.copy()

        # Quant indicators
        quant = self._compute_quant(live_state, prob)

        return {
            "probability": prob,
            "delta": delta,
            "confidence": quant["confidence"],
            "quant": quant,
        }

    def _build_features(self, live_state: dict) -> list:
        """Build feature vector for model inference."""
        def odds_to_probs(h, d, a):
            ph, pd_, pa = 1 / h, 1 / d, 1 / a
            t = ph + pd_ + pa
            return ph / t, pd_ / t, pa / t

        oh = live_state.get("odds_home", 2.0)
        od = live_state.get("odds_draw", 3.5)
        oa = live_state.get("odds_away", 3.5)
        ph, pd_, pa = odds_to_probs(oh, od, oa)

        he = live_state.get("home_elo", 1500)
        ae = live_state.get("away_elo", 1500)

        hg = live_state.get("home_goals", 0)
        ag = live_state.get("away_goals", 0)
        hxg = live_state.get("home_xg", hg * 0.9)
        axg = live_state.get("away_xg", ag * 0.9)

        return [
            ph, pd_, pa, ph - pa,       # odds features
            he - ae, (he - ae) / 400,    # elo features
            he / 2000, ae / 2000,
            1.0,                          # is_home
            hxg - axg, hxg + axg,        # xG features
            hxg, axg,
        ]

    def _poisson_update(self, prior_h, prior_d, prior_a,
                         minute, hg, ag, h_red, a_red, max_goals=7):
        """Poisson in-match correction."""
        minute = max(1, min(90, minute))
        remain_frac = max(0.02, (90 - minute) / 90)

        home_share = 0.5 + 0.2 * (prior_h - prior_a)
        home_share = max(0.25, min(0.75, home_share))

        lam_total = self.avg_total_goals * remain_frac
        lam_h = lam_total * home_share
        lam_a = lam_total * (1 - home_share)

        # Red card correction
        red_diff = a_red - h_red
        lam_h *= math.exp(0.22 * red_diff)
        lam_a *= math.exp(-0.22 * red_diff)

        lam_h = max(0.01, min(4.0, lam_h))
        lam_a = max(0.01, min(4.0, lam_a))

        p_home, p_draw, p_away = 0.0, 0.0, 0.0
        for i in range(max_goals + 1):
            pi = self._poisson_pmf(i, lam_h)
            for j in range(max_goals + 1):
                pj = self._poisson_pmf(j, lam_a)
                w = pi * pj
                final_h = hg + i
                final_a = ag + j
                if final_h > final_a:
                    p_home += w
                elif final_h == final_a:
                    p_draw += w
                else:
                    p_away += w

        return p_home, p_draw, p_away

    @staticmethod
    def _poisson_pmf(k, lam):
        return math.exp(-lam) * (lam ** k) / math.factorial(k)

    def _compute_quant(self, live_state, prob):
        """Compute quant indicators."""
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

        max_prob = max(prob["home"], prob["draw"], prob["away"])
        confidence = min(98, max(55, int(max_prob * 0.8 + 20)))

        probs = [prob["home"] / 100, prob["draw"] / 100, prob["away"] / 100]
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
