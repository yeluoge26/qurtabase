"""
Score Matrix Engine — Poisson-based correct score probabilities.

Computes a 7x7 probability matrix (0-5 goals + 6+ bucket for each team)
using independent Poisson distributions. Provides top-3 most likely scores
and 1X2 outcome probabilities derived from the matrix cells.
"""
import math


class ScoreMatrixEngine:
    MAX_GOALS = 6  # 0-5 for each team, plus 6+ bucket

    def compute(self, lambda_home: float, lambda_away: float) -> dict:
        """
        Compute correct score probability matrix using independent Poisson.

        Args:
            lambda_home: Expected goals for home team
            lambda_away: Expected goals for away team

        Returns:
            dict with:
              - matrix: 7x7 list of lists (home 0-6 x away 0-6), each cell = probability
              - top3: list of top 3 most likely scores [{"score": "1-1", "prob": 0.12}, ...]
              - home_win_prob: sum of home win cells
              - draw_prob: sum of draw cells
              - away_win_prob: sum of away win cells
        """
        try:
            matrix = []
            flat = []

            for h in range(self.MAX_GOALS + 1):
                row = []
                for a in range(self.MAX_GOALS + 1):
                    p_h = self._poisson_pmf(h, lambda_home)
                    p_a = self._poisson_pmf(a, lambda_away)
                    prob = p_h * p_a
                    row.append(round(prob * 100, 2))  # percentage
                    flat.append({"score": f"{h}-{a}", "prob": prob, "h": h, "a": a})
                matrix.append(row)

            # Sort for top 3
            flat.sort(key=lambda x: x["prob"], reverse=True)
            top3 = [{"score": f["score"], "prob": round(f["prob"] * 100, 2)} for f in flat[:3]]

            # Win/Draw/Lose probabilities
            home_win = sum(f["prob"] for f in flat if f["h"] > f["a"])
            draw = sum(f["prob"] for f in flat if f["h"] == f["a"])
            away_win = sum(f["prob"] for f in flat if f["h"] < f["a"])

            return {
                "matrix": matrix,
                "top3": top3,
                "home_win_prob": round(home_win, 4),
                "draw_prob": round(draw, 4),
                "away_win_prob": round(away_win, 4),
                "home_lambda": round(lambda_home, 3),
                "away_lambda": round(lambda_away, 3),
            }
        except Exception:
            # Fallback: empty matrix
            empty_row = [0.0] * (self.MAX_GOALS + 1)
            return {
                "matrix": [empty_row[:] for _ in range(self.MAX_GOALS + 1)],
                "top3": [],
                "home_win_prob": 0.0,
                "draw_prob": 0.0,
                "away_win_prob": 0.0,
                "home_lambda": round(lambda_home, 3),
                "away_lambda": round(lambda_away, 3),
            }

    def _poisson_pmf(self, k: int, lam: float) -> float:
        """Poisson probability mass function."""
        if k < 0 or lam <= 0:
            return 0.0
        # For k = MAX_GOALS, use 1 - CDF(MAX_GOALS-1) to capture 6+
        if k == self.MAX_GOALS:
            return 1.0 - sum(self._poisson_pmf(i, lam) for i in range(self.MAX_GOALS))
        return math.exp(-lam) * (lam ** k) / math.factorial(k)
