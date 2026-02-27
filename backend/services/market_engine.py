"""
Market Engine — v1.1

Computes market-implied probabilities and AI vs Market edge.
This is the core monetization feature for Pro tier.
"""


class MarketEngine:
    def compute(self, odds: dict | None, ai_prob: dict) -> dict:
        """
        Compute market implied probability and edge.

        odds: {"home": 1.85, "draw": 3.50, "away": 4.20} or None
        ai_prob: {"home": 64.21, "draw": 22.08, "away": 13.71}
        """
        if not odds:
            return {
                "implied_prob": None,
                "edge": None,
                "odds": None,
            }

        oh = odds.get("home", 2.0)
        od = odds.get("draw", 3.5)
        oa = odds.get("away", 3.5)

        # Remove margin (overround)
        raw_h, raw_d, raw_a = 1 / oh, 1 / od, 1 / oa
        total = raw_h + raw_d + raw_a  # typically ~1.06

        implied = {
            "home": round(raw_h / total * 100, 2),
            "draw": round(raw_d / total * 100, 2),
            "away": round(raw_a / total * 100, 2),
        }

        edge = {
            "home": round(ai_prob["home"] - implied["home"], 2),
            "draw": round(ai_prob["draw"] - implied["draw"], 2),
            "away": round(ai_prob["away"] - implied["away"], 2),
        }

        return {
            "implied_prob": implied,
            "edge": edge,
            "odds": {"home": oh, "draw": od, "away": oa},
        }
