"""
predictor.py — 赛中实时预测引擎
Live Match Prediction Engine

两段式架构:
  1. 赛前: XGBoost 输出初始 P(H/D/A) — 基于赔率/Elo/xG
  2. 赛中: Poisson 动态修正 — 基于当前比分/时间/红牌

这样做的原因:
  - 赛前模型捕捉"实力面"
  - Poisson 修正捕捉"比赛进展"
  - 组合后 > 任何单一方法
"""

import math
import json
import numpy as np
import joblib
from features import build_live_features


class LivePredictor:
    """
    实时比赛预测器
    
    使用方法:
        predictor = LivePredictor("models/model_calibrated.pkl")
        
        result = predictor.predict({
            "minute": 65,
            "home_goals": 1,
            "away_goals": 0,
            "odds_home": 1.85,
            "odds_draw": 3.50,
            "odds_away": 4.20,
            "home_elo": 1650,
            "away_elo": 1580,
            ...
        })
        
        print(result)
        # {
        #   "probability": {"home": 68.5, "draw": 19.2, "away": 12.3},
        #   "confidence": 82,
        #   "quant": {...}
        # }
    """

    def __init__(self, model_path="models/model_calibrated.pkl"):
        self.model = joblib.load(model_path)

        # 加载元数据
        try:
            with open("models/model_meta.json") as f:
                self.meta = json.load(f)
        except FileNotFoundError:
            self.meta = {"class_names": ["Away", "Draw", "Home"]}

        # 平均总进球 (英超约 2.7)
        self.avg_total_goals = 2.7

        # 历史概率追踪 (用于计算 delta)
        self.prev_prob = None

    def predict(self, live_state: dict) -> dict:
        """
        主预测函数
        
        输入: 实时比赛状态
        输出: 完整预测结果 (概率 + 量化指标)
        """
        minute = live_state.get("minute", 0)
        hg = live_state.get("home_goals", 0)
        ag = live_state.get("away_goals", 0)
        h_red = live_state.get("home_red", 0)
        a_red = live_state.get("away_red", 0)

        # ═══ Step 1: 赛前模型概率 ═══
        features = build_live_features(live_state)
        proba = self.model.predict_proba([features])[0]
        # 顺序: [Away=0, Draw=1, Home=2]
        prior_away, prior_draw, prior_home = proba[0], proba[1], proba[2]

        # ═══ Step 2: Poisson 赛中修正 ═══
        if minute > 0:
            p_home, p_draw, p_away = self._poisson_update(
                prior_home, prior_draw, prior_away,
                minute, hg, ag, h_red, a_red
            )
        else:
            p_home, p_draw, p_away = prior_home, prior_draw, prior_away

        # 归一化
        total = p_home + p_draw + p_away
        p_home, p_draw, p_away = p_home / total, p_draw / total, p_away / total

        # 转为百分比
        prob = {
            "home": round(p_home * 100, 2),
            "draw": round(p_draw * 100, 2),
            "away": round(p_away * 100, 2),
        }

        # 计算 delta
        delta = {"home": 0.0, "draw": 0.0, "away": 0.0}
        if self.prev_prob:
            delta["home"] = round(prob["home"] - self.prev_prob["home"], 2)
            delta["draw"] = round(prob["draw"] - self.prev_prob["draw"], 2)
            delta["away"] = round(prob["away"] - self.prev_prob["away"], 2)
        self.prev_prob = prob.copy()

        # ═══ Step 3: 量化指标 ═══
        quant = self._compute_quant(live_state, prob)

        return {
            "probability": prob,
            "delta": delta,
            "confidence": quant["confidence"],
            "quant": quant,
        }

    def _poisson_update(self, prior_h, prior_d, prior_a,
                         minute, hg, ag, h_red, a_red,
                         max_goals=7):
        """
        Poisson 赛中修正
        
        原理:
        1. 用赛前概率估算主/客队进球强度 (λ)
        2. 按已过时间缩放剩余进球强度
        3. 用红牌/xG 修正强度
        4. 枚举所有可能的剩余进球组合
        5. 累加得到最终 P(H/D/A)
        """
        minute = max(1, min(90, minute))
        remain_frac = max(0.02, (90 - minute) / 90)

        # 从先验概率估算主客进球占比
        home_share = 0.5 + 0.2 * (prior_h - prior_a)
        home_share = max(0.25, min(0.75, home_share))

        # 剩余进球期望
        lam_total = self.avg_total_goals * remain_frac
        lam_h = lam_total * home_share
        lam_a = lam_total * (1 - home_share)

        # 红牌修正: 少一人 → 进球能力下降 ~22%
        red_diff = a_red - h_red
        lam_h *= math.exp(0.22 * red_diff)
        lam_a *= math.exp(-0.22 * red_diff)

        # 限制范围
        lam_h = max(0.01, min(4.0, lam_h))
        lam_a = max(0.01, min(4.0, lam_a))

        # 枚举剩余进球
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
        """Poisson 概率质量函数"""
        return math.exp(-lam) * (lam ** k) / math.factorial(k)

    def _compute_quant(self, live_state, prob):
        """
        计算 PRD §4.5 量化指标
        """
        minute = live_state.get("minute", 0)
        hg = live_state.get("home_goals", 0)
        ag = live_state.get("away_goals", 0)
        h_shots = live_state.get("home_shots", 0)
        a_shots = live_state.get("away_shots", 0)
        h_poss = live_state.get("home_possession", 50)
        hxg = live_state.get("home_xg", hg * 0.9 + 0.2)
        axg = live_state.get("away_xg", ag * 0.9 + 0.2)

        # 压力指数: 射门+控球+进攻的综合
        pressure = 50 + (h_shots - a_shots) * 2.5 + (h_poss - 50) * 0.6
        pressure = max(5, min(98, pressure))

        # 攻防势头: 综合考虑射门差+xG差+比分差
        momentum = (h_shots - a_shots) * 1.5 + (hxg - axg) * 8 + (hg - ag) * 5
        momentum = max(-50, min(50, momentum))

        # 波动率: 比赛越到后期，波动越大
        tf = minute / 90
        volatility = 0.3 + tf * 0.5 + abs(hg - ag) * 0.1
        volatility = min(1.5, volatility)

        # 失球风险
        risk = 30 + (1 - tf) * 20 + a_shots * 0.8
        risk = max(5, min(90, risk))

        # 预期进球窗口
        if minute < 80:
            window_start = max(2, int(8 - tf * 5))
            window_end = max(5, int(15 - tf * 8))
            goal_window = f"{window_start}-{window_end}"
        else:
            goal_window = "LOW"

        # 模型置信度
        max_prob = max(prob["home"], prob["draw"], prob["away"])
        confidence = min(98, max(55, int(max_prob * 0.8 + 20)))

        # 模型方差
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


def demo():
    """演示实时预测"""
    print("=" * 50)
    print("  实时预测演示 Demo")
    print("=" * 50)

    predictor = LivePredictor("models/model_calibrated.pkl")

    # 模拟比赛进程
    scenarios = [
        {"minute": 0,  "home_goals": 0, "away_goals": 0,
         "desc": "开场"},
        {"minute": 25, "home_goals": 0, "away_goals": 0,
         "home_shots": 5, "away_shots": 3,
         "desc": "25分钟 0-0"},
        {"minute": 30, "home_goals": 1, "away_goals": 0,
         "home_shots": 7, "away_shots": 3,
         "desc": "30分钟 主队进球! 1-0"},
        {"minute": 60, "home_goals": 1, "away_goals": 0,
         "home_shots": 11, "away_shots": 6,
         "desc": "60分钟 1-0"},
        {"minute": 65, "home_goals": 1, "away_goals": 1,
         "home_shots": 12, "away_shots": 8,
         "desc": "65分钟 客队扳平! 1-1"},
        {"minute": 80, "home_goals": 2, "away_goals": 1,
         "home_shots": 15, "away_shots": 9,
         "desc": "80分钟 主队再进! 2-1"},
        {"minute": 88, "home_goals": 2, "away_goals": 1,
         "home_shots": 16, "away_shots": 10,
         "home_red": 0, "away_red": 1,
         "desc": "88分钟 客队红牌! 2-1"},
    ]

    for s in scenarios:
        # 添加赔率和Elo (赛前数据)
        s.update({
            "odds_home": 1.85, "odds_draw": 3.50, "odds_away": 4.20,
            "home_elo": 1650, "away_elo": 1580,
            "home_possession": 55,
            "home_xg": s.get("home_goals", 0) * 0.85 + 0.3,
            "away_xg": s.get("away_goals", 0) * 0.85 + 0.2,
        })

        result = predictor.predict(s)
        p = result["probability"]
        d = result["delta"]
        q = result["quant"]

        print(f"\n  ⏱ {s['desc']}")
        print(f"  ┌──────────────────────────────────────────┐")
        print(f"  │ HOME WIN   {p['home']:6.2f}%   Δ {'+' if d['home']>=0 else ''}{d['home']:.2f}%  │")
        print(f"  │ DRAW       {p['draw']:6.2f}%   Δ {'+' if d['draw']>=0 else ''}{d['draw']:.2f}%  │")
        print(f"  │ AWAY WIN   {p['away']:6.2f}%   Δ {'+' if d['away']>=0 else ''}{d['away']:.2f}%  │")
        print(f"  ├──────────────────────────────────────────┤")
        print(f"  │ CONFIDENCE     {result['confidence']}%                   │")
        print(f"  │ PRESSURE       {q['pressure_index']}                     │")
        print(f"  │ MOMENTUM       {'+' if q['momentum']>=0 else ''}{q['momentum']}                   │")
        print(f"  │ VOLATILITY     {q['volatility']}                  │")
        print(f"  │ RISK CONCEDE   {q['risk_concede']}%                   │")
        print(f"  │ GOAL WINDOW    {q['goal_window']} min               │")
        print(f"  └──────────────────────────────────────────┘")


if __name__ == "__main__":
    demo()
