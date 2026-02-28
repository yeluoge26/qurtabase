"""
HistoryTracker -- v1.0
Tracks historical prediction accuracy across matches.
Stores past match predictions and outcomes in-memory.
Provides summary statistics for frontend display.
"""

import time


class HistoryTracker:
    """Tracks historical prediction results across matches."""

    def __init__(self):
        self._records: list[dict] = []

    def record_match(self, record: dict) -> None:
        """Add a completed match prediction record."""
        self._records.append(record)

    def get_summary(self) -> dict:
        """Return aggregate prediction history summary."""
        total = len(self._records)
        if total == 0:
            return {
                "total_matches": 0,
                "correct_1x2": 0,
                "accuracy_1x2_pct": 0,
                "correct_ou": 0,
                "accuracy_ou_pct": 0,
                "avg_confidence": 0,
                "avg_brier": 0,
                "streak": 0,
                "by_confidence": {},
                "recent_5": [],
            }

        correct_1x2 = sum(1 for r in self._records if r.get("correct"))
        correct_ou = sum(1 for r in self._records if r.get("ou_correct"))
        avg_conf = round(
            sum(r.get("confidence", 0) for r in self._records) / total, 1
        )
        brier_vals = [r.get("brier_score", 0) for r in self._records if r.get("brier_score") is not None]
        avg_brier = round(sum(brier_vals) / len(brier_vals), 3) if brier_vals else 0

        # Streak: positive = consecutive correct, negative = consecutive wrong
        streak = 0
        for r in reversed(self._records):
            if r.get("correct"):
                if streak < 0:
                    break
                streak += 1
            else:
                if streak > 0:
                    break
                streak -= 1

        # By confidence band
        bands = {"high": [], "medium": [], "low": []}
        for r in self._records:
            c = r.get("confidence", 0)
            if c >= 80:
                bands["high"].append(r)
            elif c >= 65:
                bands["medium"].append(r)
            else:
                bands["low"].append(r)

        by_confidence = {}
        for band, records in bands.items():
            t = len(records)
            c = sum(1 for r in records if r.get("correct"))
            by_confidence[band] = {
                "total": t,
                "correct": c,
                "pct": round(c / t * 100, 1) if t > 0 else 0,
            }

        # Recent 5
        recent_5 = []
        for r in self._records[-5:]:
            home = r.get("home_short", r.get("home", "")[:3].upper())
            away = r.get("away_short", r.get("away", "")[:3].upper())
            recent_5.append({
                "match": f"{home} v {away}",
                "correct": r.get("correct", False),
                "type": "1X2",
            })

        return {
            "total_matches": total,
            "correct_1x2": correct_1x2,
            "accuracy_1x2_pct": round(correct_1x2 / total * 100, 1),
            "correct_ou": correct_ou,
            "accuracy_ou_pct": round(correct_ou / total * 100, 1),
            "avg_confidence": avg_conf,
            "avg_brier": avg_brier,
            "streak": streak,
            "by_confidence": by_confidence,
            "recent_5": recent_5,
        }

    def seed_demo_data(self):
        """Populate with realistic EPL/UCL historical prediction data."""
        matches = [
            # (home, away, home_cn, away_cn, predicted, actual, pred_ou, ou_line, goals, conf, brier)
            ("Arsenal", "Chelsea", "阿森纳", "切尔西", "HOME", "HOME", "OVER", 2.5, 3, 82, 0.145),
            ("Liverpool", "Man City", "利物浦", "曼城", "HOME", "DRAW", "OVER", 2.5, 2, 68, 0.285),
            ("Barcelona", "Real Madrid", "巴塞罗那", "皇家马德里", "HOME", "HOME", "OVER", 2.5, 4, 75, 0.162),
            ("Bayern", "Dortmund", "拜仁慕尼黑", "多特蒙德", "HOME", "HOME", "OVER", 2.5, 5, 88, 0.098),
            ("Man Utd", "Arsenal", "曼联", "阿森纳", "AWAY", "AWAY", "UNDER", 2.5, 1, 72, 0.178),
            ("Tottenham", "Chelsea", "热刺", "切尔西", "HOME", "HOME", "OVER", 2.5, 3, 63, 0.210),
            ("PSG", "Marseille", "巴黎圣日耳曼", "马赛", "HOME", "HOME", "OVER", 2.5, 4, 85, 0.112),
            ("Inter", "AC Milan", "国际米兰", "AC米兰", "HOME", "DRAW", "UNDER", 2.5, 1, 70, 0.245),
            ("Juventus", "Napoli", "尤文图斯", "那不勒斯", "DRAW", "DRAW", "UNDER", 2.5, 2, 58, 0.320),
            ("Man City", "Liverpool", "曼城", "利物浦", "HOME", "HOME", "OVER", 2.5, 3, 78, 0.155),
            ("Chelsea", "Man Utd", "切尔西", "曼联", "HOME", "HOME", "UNDER", 2.5, 2, 66, 0.198),
            ("Real Madrid", "Atletico", "皇家马德里", "马德里竞技", "HOME", "HOME", "UNDER", 2.5, 1, 74, 0.172),
            ("Arsenal", "Tottenham", "阿森纳", "热刺", "HOME", "HOME", "OVER", 2.5, 4, 80, 0.130),
            ("Dortmund", "Leipzig", "多特蒙德", "莱比锡", "HOME", "AWAY", "OVER", 2.5, 3, 62, 0.312),
            ("Newcastle", "Aston Villa", "纽卡斯尔", "阿斯顿维拉", "HOME", "HOME", "UNDER", 2.5, 2, 71, 0.185),
            ("Brighton", "West Ham", "布莱顿", "西汉姆", "HOME", "HOME", "OVER", 2.5, 3, 65, 0.202),
            ("Wolves", "Crystal Palace", "狼队", "水晶宫", "DRAW", "AWAY", "UNDER", 2.5, 1, 55, 0.356),
            ("Bournemouth", "Fulham", "伯恩茅斯", "富勒姆", "HOME", "DRAW", "OVER", 2.5, 2, 60, 0.278),
            ("Everton", "Nottm Forest", "埃弗顿", "诺丁汉森林", "HOME", "HOME", "UNDER", 2.5, 1, 64, 0.215),
            ("Leicester", "Ipswich", "莱斯特城", "伊普斯维奇", "HOME", "HOME", "OVER", 2.5, 4, 76, 0.148),
            ("Liverpool", "Arsenal", "利物浦", "阿森纳", "HOME", "DRAW", "UNDER", 2.5, 2, 73, 0.240),
            ("Man City", "Chelsea", "曼城", "切尔西", "HOME", "HOME", "OVER", 2.5, 3, 84, 0.118),
            ("Bayern", "Leverkusen", "拜仁慕尼黑", "勒沃库森", "HOME", "HOME", "OVER", 2.5, 4, 79, 0.142),
            ("Arsenal", "Man City", "阿森纳", "曼城", "HOME", "HOME", "UNDER", 2.5, 1, 70, 0.190),
            ("Tottenham", "Liverpool", "热刺", "利物浦", "AWAY", "AWAY", "OVER", 2.5, 3, 77, 0.160),
        ]

        for i, (home, away, home_cn, away_cn, pred, actual, pred_ou, ou_line, goals, conf, brier) in enumerate(matches):
            ou_correct = (pred_ou == "OVER" and goals > ou_line) or (pred_ou == "UNDER" and goals < ou_line)
            self._records.append({
                "match_id": f"hist_{i+1}",
                "league": "EPL" if i < 20 else "UCL",
                "home": home,
                "away": away,
                "home_cn": home_cn,
                "away_cn": away_cn,
                "home_short": home[:3].upper(),
                "away_short": away[:3].upper(),
                "date": f"2026-{1 + i // 15:02d}-{1 + (i * 3) % 28:02d}",
                "predicted_1x2": pred,
                "predicted_prob": conf - 5 + (i % 10),
                "actual_result": actual,
                "correct": pred == actual,
                "predicted_ou": pred_ou,
                "ou_line": ou_line,
                "actual_goals": goals,
                "ou_correct": ou_correct,
                "confidence": conf,
                "pre_lambda": round(2.3 + (goals * 0.12) + (i % 5) * 0.08, 2),
                "brier_score": brier,
            })
