"""
PreMatchEngine -- v1.0
Generates pre-match prediction recommendations using:
  - Elo expected score formula
  - Odds-implied probabilities (when available)
  - Poisson model for O/U prediction
Only active when match status is "upcoming" (minute == 0).
"""

import math


class PreMatchEngine:
    """Computes pre-match prediction recommendations."""

    # Default league average goals per match
    LEAGUE_AVG_GOALS = 2.7

    def compute(self, match_config: dict, odds: dict = None) -> dict:
        """
        Generate pre-match recommendation.

        Args:
            match_config: dict with home_elo, away_elo, league, etc.
            odds: dict with home, draw, away decimal odds (optional)

        Returns:
            dict with recommendation, probabilities, O/U, confidence, key_factors
        """
        home_elo = match_config.get("home_elo", 1500)
        away_elo = match_config.get("away_elo", 1500)

        # ── Elo-based 1X2 probabilities ───────────────────────
        elo_diff = home_elo - away_elo
        e_home = 1 / (1 + 10 ** (-elo_diff / 400))
        # Convert expected score to 1X2 probabilities
        # Home advantage + Elo advantage
        p_home = min(0.85, max(0.10, e_home * 0.85 + 0.075))
        p_away = min(0.85, max(0.10, (1 - e_home) * 0.85 + 0.075))
        p_draw = max(0.10, 1.0 - p_home - p_away)
        # Normalize
        total = p_home + p_draw + p_away
        p_home /= total
        p_draw /= total
        p_away /= total

        # ── Blend with odds-implied probabilities ─────────────
        odds_probs = None
        if odds and odds.get("home") and odds.get("draw") and odds.get("away"):
            oh, od, oa = odds["home"], odds["draw"], odds["away"]
            if oh > 1 and od > 1 and oa > 1:
                raw_h, raw_d, raw_a = 1 / oh, 1 / od, 1 / oa
                vig = raw_h + raw_d + raw_a
                odds_probs = {
                    "home": raw_h / vig,
                    "draw": raw_d / vig,
                    "away": raw_a / vig,
                }
                # Blend: 60% model, 40% market
                p_home = 0.6 * p_home + 0.4 * odds_probs["home"]
                p_draw = 0.6 * p_draw + 0.4 * odds_probs["draw"]
                p_away = 0.6 * p_away + 0.4 * odds_probs["away"]

        probs = {
            "home": round(p_home * 100, 1),
            "draw": round(p_draw * 100, 1),
            "away": round(p_away * 100, 1),
        }

        # ── Recommendation ────────────────────────────────────
        if probs["home"] > probs["away"] and probs["home"] > probs["draw"]:
            rec_1x2 = "HOME"
        elif probs["away"] > probs["home"] and probs["away"] > probs["draw"]:
            rec_1x2 = "AWAY"
        else:
            rec_1x2 = "DRAW"

        # ── O/U prediction (Poisson) ──────────────────────────
        avg_goals = self.LEAGUE_AVG_GOALS
        # Adjust lambda by Elo: stronger teams score more
        elo_factor = 1.0 + (elo_diff / 1000) * 0.15
        lambda_total = avg_goals * elo_factor
        lambda_total = max(1.5, min(4.5, lambda_total))

        ou_line = match_config.get("ou_line", 2.5)
        # Poisson P(total > line) = 1 - P(total <= floor(line))
        p_under = 0.0
        k_max = int(math.floor(ou_line))
        for total_goals in range(k_max + 1):
            # Sum over all (h, a) combinations where h + a = total_goals
            p_combo = 0.0
            lh = lambda_total * 0.55  # slight home bias
            la = lambda_total * 0.45
            for h in range(total_goals + 1):
                a = total_goals - h
                p_h = (lh ** h) * math.exp(-lh) / math.factorial(h)
                p_a = (la ** a) * math.exp(-la) / math.factorial(a)
                p_combo += p_h * p_a
            p_under += p_combo

        p_over = 1.0 - p_under
        rec_ou = "OVER" if p_over > 0.52 else "UNDER"

        # ── Confidence ────────────────────────────────────────
        max_prob = max(probs["home"], probs["draw"], probs["away"])
        elo_gap = abs(elo_diff)
        conf = min(95, max(45, int(max_prob * 0.6 + elo_gap * 0.02 + 30)))
        if odds_probs:
            conf = min(95, conf + 5)  # boost when market data available

        # ── Key factors ───────────────────────────────────────
        factors = []
        if elo_diff > 50:
            factors.append({
                "factor": "elo_advantage",
                "team": "home",
                "value": f"+{elo_diff}",
                "direction": "positive",
            })
        elif elo_diff < -50:
            factors.append({
                "factor": "elo_advantage",
                "team": "away",
                "value": f"+{abs(elo_diff)}",
                "direction": "positive",
            })
        else:
            factors.append({
                "factor": "elo_balanced",
                "team": "neutral",
                "value": f"Δ{abs(elo_diff)}",
                "direction": "neutral",
            })

        factors.append({
            "factor": "expected_goals",
            "team": "neutral",
            "value": f"λ={lambda_total:.2f}",
            "direction": "positive" if lambda_total > 2.7 else "negative",
        })

        if odds_probs:
            factors.append({
                "factor": "market_aligned",
                "team": "neutral",
                "value": "ODDS",
                "direction": "positive",
            })
        else:
            factors.append({
                "factor": "no_market_data",
                "team": "neutral",
                "value": "ELO ONLY",
                "direction": "neutral",
            })

        return {
            "active": True,
            "recommendation_1x2": rec_1x2,
            "probabilities": probs,
            "ou_recommendation": rec_ou,
            "ou_line": ou_line,
            "prob_over": round(p_over * 100, 1),
            "prob_under": round(p_under * 100, 1),
            "lambda_total": round(lambda_total, 2),
            "confidence": conf,
            "key_factors": factors[:3],
            "source": "ELO+MARKET" if odds_probs else "ELO",
        }

    @staticmethod
    def inactive():
        """Return inactive payload for live matches."""
        return {"active": False}
