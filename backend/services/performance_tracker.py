"""
PerformanceTracker -- v1.0
Tracks signal performance for the current session.
Records confirmed signals, matches results, and provides summary stats.
"""

import time
from typing import Optional


class PerformanceTracker:
    """Tracks signal performance for the current session."""

    def __init__(self):
        self._signals: list[dict] = []
        self._next_id = 1

    def record_signal(
        self,
        signal_type: str,
        line: float,
        edge: float,
        model_prob: float,
        market_prob: float,
        minute: int,
    ) -> int:
        """Record a confirmed signal. Returns the signal id."""
        record = {
            "id": self._next_id,
            "minute": minute,
            "type": signal_type,       # "OVER" | "UNDER"
            "line": line,
            "edge": round(edge, 1),
            "model_prob": round(model_prob, 1),
            "market_prob": round(market_prob, 1),
            "result": "pending",       # "win" | "loss" | "pending"
            "timestamp": time.time(),
        }
        self._signals.append(record)
        sid = self._next_id
        self._next_id += 1
        return sid

    def record_result(self, signal_id: int, actual_goals: int):
        """
        Record the result when match ends (or a line is settled).
        Compares actual total goals against the signal line & type.
        """
        for sig in self._signals:
            if sig["id"] == signal_id and sig["result"] == "pending":
                line = sig["line"]
                stype = sig["type"]
                if stype == "OVER":
                    sig["result"] = "win" if actual_goals > line else "loss"
                elif stype == "UNDER":
                    sig["result"] = "win" if actual_goals < line else "loss"
                else:
                    # For exact-line pushes, mark as loss (conservative)
                    sig["result"] = "loss"
                break

    def get_summary(self) -> dict:
        """Return today's performance summary."""
        total = len(self._signals)
        wins = sum(1 for s in self._signals if s["result"] == "win")
        losses = sum(1 for s in self._signals if s["result"] == "loss")
        pending = sum(1 for s in self._signals if s["result"] == "pending")

        edges = [s["edge"] for s in self._signals if s["edge"] is not None]
        best_edge = max(edges) if edges else 0.0
        avg_edge = round(sum(edges) / len(edges), 1) if edges else 0.0

        # Simplified ROI: wins contribute +edge%, losses contribute -100/odds (~-edge%)
        # For demo purposes, use a simplified formula
        if wins + losses > 0:
            roi_pct = round(
                (sum(s["edge"] for s in self._signals if s["result"] == "win")
                 - sum(abs(s["edge"]) * 0.5 for s in self._signals if s["result"] == "loss"))
                / max(1, wins + losses),
                1,
            )
        else:
            roi_pct = 0.0

        return {
            "total_signals": total,
            "wins": wins,
            "losses": losses,
            "pending": pending,
            "roi_pct": roi_pct,
            "best_edge": round(best_edge, 1),
            "avg_edge": avg_edge,
            "signals": [
                {
                    "id": s["id"],
                    "minute": s["minute"],
                    "type": s["type"],
                    "line": s["line"],
                    "edge": s["edge"],
                    "model_prob": s["model_prob"],
                    "result": s["result"],
                    "timestamp": s["timestamp"],
                }
                for s in self._signals[-10:]   # last 10 signals
            ],
        }

    def seed_demo_data(self):
        """Populate with mock performance data for demo mode."""
        now = time.time()

        demo_signals = [
            {"type": "OVER",  "line": 2.25, "edge": 7.0, "model_prob": 61, "market_prob": 54, "minute": 34, "result": "win"},
            {"type": "OVER",  "line": 2.5,  "edge": 5.2, "model_prob": 58, "market_prob": 53, "minute": 52, "result": "loss"},
            {"type": "OVER",  "line": 2.25, "edge": 9.2, "model_prob": 64, "market_prob": 55, "minute": 71, "result": "pending"},
        ]

        for i, ds in enumerate(demo_signals):
            record = {
                "id": self._next_id,
                "minute": ds["minute"],
                "type": ds["type"],
                "line": ds["line"],
                "edge": ds["edge"],
                "model_prob": ds["model_prob"],
                "market_prob": ds["market_prob"],
                "result": ds["result"],
                "timestamp": now - (len(demo_signals) - i) * 600,
            }
            self._signals.append(record)
            self._next_id += 1
