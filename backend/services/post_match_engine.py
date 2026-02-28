"""
PostMatchEngine -- v1.0
Generates post-match summary when match ends (minute 90 / FT).
Tracks peak lambda, peak edge, and lambda history throughout the match
to produce a final accuracy and performance report.
"""


class PostMatchEngine:
    """Generates post-match summary when match ends."""

    def __init__(self):
        self._peak_lambda = 0
        self._peak_edge = 0
        self._lambda_history = []
        self._pre_lambda = None

    def update(self, lambda_live: float, edge: float, lambda_pre: float):
        """Called each tick during match to track peaks."""
        if self._pre_lambda is None:
            self._pre_lambda = lambda_pre
        self._peak_lambda = max(self._peak_lambda, lambda_live)
        self._peak_edge = max(self._peak_edge, abs(edge))
        self._lambda_history.append(lambda_live)

    def generate_summary(self, final_score: list, minute: int) -> dict:
        """Generate post-match summary."""
        final_goals = sum(final_score)
        return {
            "active": True,
            "pre_lambda": round(self._pre_lambda or 0, 2),
            "final_goals": final_goals,
            "final_score": f"{final_score[0]}-{final_score[1]}",
            "peak_lambda": round(self._peak_lambda, 2),
            "best_edge": round(self._peak_edge, 1),
            "avg_lambda": round(
                sum(self._lambda_history) / max(len(self._lambda_history), 1), 2
            ),
            "lambda_accuracy": (
                "HIT"
                if abs(final_goals - (self._pre_lambda or 0)) < 0.75
                else "MISS"
            ),
            "total_updates": len(self._lambda_history),
        }

    def reset(self):
        """Reset for next match."""
        self.__init__()
