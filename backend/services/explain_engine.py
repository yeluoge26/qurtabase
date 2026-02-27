"""
Explain Engine — v1.1 (Why Delta)

Identifies top factors driving probability changes.
Builds trust with users by explaining model reasoning.
"""


class ExplainEngine:
    def explain(self, current: dict, previous: dict | None) -> dict:
        """
        Generate explanation for probability delta.

        current: current live_state + quant indicators
        previous: previous live_state snapshot (or None)
        """
        if not previous:
            return {
                "summary": "Initial prediction — no previous data",
                "top_factors": [],
            }

        factors = []

        # Shots on target change
        cur_sot = current.get("home_shots_on_target", 0) - current.get("away_shots_on_target", 0)
        prev_sot = previous.get("home_shots_on_target", 0) - previous.get("away_shots_on_target", 0)
        sot_delta = cur_sot - prev_sot
        if sot_delta != 0:
            factors.append({
                "name": "shots_on_target_delta",
                "impact": round(abs(sot_delta) * 0.45, 2),
                "direction": "up" if sot_delta > 0 else "down",
            })

        # Pressure change
        cur_pressure = current.get("pressure_index", 50)
        prev_pressure = previous.get("pressure_index", 50)
        pressure_delta = cur_pressure - prev_pressure
        if abs(pressure_delta) > 3:
            factors.append({
                "name": "pressure_index_delta",
                "impact": round(abs(pressure_delta) * 0.06, 2),
                "direction": "up" if pressure_delta > 0 else "down",
            })

        # Goal scored
        cur_diff = current.get("home_goals", 0) - current.get("away_goals", 0)
        prev_diff = previous.get("home_goals", 0) - previous.get("away_goals", 0)
        if cur_diff != prev_diff:
            factors.append({
                "name": "goal_scored",
                "impact": round(abs(cur_diff - prev_diff) * 2.5, 2),
                "direction": "up" if cur_diff > prev_diff else "down",
            })

        # Red card
        cur_red = current.get("home_red", 0) + current.get("away_red", 0)
        prev_red = previous.get("home_red", 0) + previous.get("away_red", 0)
        if cur_red != prev_red:
            factors.append({
                "name": "red_card_impact",
                "impact": round(abs(cur_red - prev_red) * 1.8, 2),
                "direction": "up" if current.get("away_red", 0) > previous.get("away_red", 0) else "down",
            })

        # Possession swing
        cur_poss = current.get("home_possession", 50)
        prev_poss = previous.get("home_possession", 50)
        poss_delta = cur_poss - prev_poss
        if abs(poss_delta) > 3:
            factors.append({
                "name": "possession_swing",
                "impact": round(abs(poss_delta) * 0.08, 2),
                "direction": "up" if poss_delta > 0 else "down",
            })

        # xG change
        cur_xg_diff = current.get("home_xg", 0) - current.get("away_xg", 0)
        prev_xg_diff = previous.get("home_xg", 0) - previous.get("away_xg", 0)
        xg_delta = cur_xg_diff - prev_xg_diff
        if abs(xg_delta) > 0.05:
            factors.append({
                "name": "xg_delta_change",
                "impact": round(abs(xg_delta) * 1.5, 2),
                "direction": "up" if xg_delta > 0 else "down",
            })

        # Time decay (always present in 2nd half)
        minute = current.get("minute", 0)
        if minute > 45:
            factors.append({
                "name": "time_decay",
                "impact": round((minute - 45) / 90 * 0.5, 2),
                "direction": "up" if cur_diff > 0 else "down" if cur_diff < 0 else "neutral",
            })

        # Sort by impact, take top 3
        factors.sort(key=lambda f: f["impact"], reverse=True)
        top = factors[:3]

        # Build summary
        if not top:
            summary = "No significant changes detected"
        else:
            parts = []
            for f in top:
                arrow = "↑" if f["direction"] == "up" else "↓" if f["direction"] == "down" else "→"
                name = f["name"].replace("_", " ")
                parts.append(f"{arrow} {name}")
            summary = "ΔHOME driven by: " + " + ".join(parts)

        return {
            "summary": summary,
            "top_factors": top,
        }
