"""
features.py — 特征工程
Feature Engineering for Football Match Prediction

这是模型准确度的关键。好的特征 > 好的算法。

特征分为 4 类：
  1. 赔率隐含概率 (最强特征 - 市场共识)
  2. Elo 实力差
  3. 比赛统计 (射门/角球/控球等)
  4. 衍生特征 (xG差/攻防效率)
"""

import pandas as pd
import numpy as np


def odds_to_probs(h_odds, d_odds, a_odds):
    """
    赔率 → 隐含概率 (去除水位归一化)
    
    这是最强的单一特征。博彩公司赔率本质上是
    成千上万分析师 + 大量资金博弈后的市场共识概率。
    """
    ph = 1.0 / h_odds
    pd_ = 1.0 / d_odds
    pa = 1.0 / a_odds
    total = ph + pd_ + pa  # > 1.0 因为水位
    return ph / total, pd_ / total, pa / total


def build_prematch_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    赛前特征 — 用于赛前模型训练
    
    输入: 原始比赛数据 DataFrame
    输出: 特征 DataFrame
    """
    feats = pd.DataFrame(index=df.index)

    # ═══ 1. 赔率隐含概率 (最强特征) ═══
    if {"B365H", "B365D", "B365A"}.issubset(df.columns):
        probs = df.apply(
            lambda r: odds_to_probs(r["B365H"], r["B365D"], r["B365A"]),
            axis=1
        )
        feats["odds_home_prob"] = [p[0] for p in probs]
        feats["odds_draw_prob"] = [p[1] for p in probs]
        feats["odds_away_prob"] = [p[2] for p in probs]
        
        # 赔率差值
        feats["odds_home_minus_away"] = feats["odds_home_prob"] - feats["odds_away_prob"]

    # ═══ 2. Elo 实力 ═══
    if {"HomeElo", "AwayElo"}.issubset(df.columns):
        feats["elo_diff"] = df["HomeElo"] - df["AwayElo"]
        feats["elo_diff_norm"] = feats["elo_diff"] / 400  # 归一化
        feats["home_elo_norm"] = df["HomeElo"] / 2000
        feats["away_elo_norm"] = df["AwayElo"] / 2000

    # ═══ 3. 主场优势 ═══
    feats["is_home"] = 1.0  # 恒为1 (数据已按主客排列)

    # ═══ 4. xG (如果有) ═══
    if {"Home_xG", "Away_xG"}.issubset(df.columns):
        feats["xg_diff"] = df["Home_xG"] - df["Away_xG"]
        feats["xg_total"] = df["Home_xG"] + df["Away_xG"]
        feats["home_xg"] = df["Home_xG"]
        feats["away_xg"] = df["Away_xG"]

    return feats


def build_live_features(live_state: dict) -> list:
    """
    赛中特征 — 用于实时推理
    
    输入: 实时比赛状态 dict
    输出: 特征向量 list
    
    live_state 结构:
    {
        "minute": 65,
        "home_goals": 1,
        "away_goals": 0,
        "home_shots": 12,
        "away_shots": 7,
        "home_shots_on_target": 5,
        "away_shots_on_target": 3,
        "home_corners": 6,
        "away_corners": 3,
        "home_possession": 58,
        "home_xg": 1.23,  # 可选
        "away_xg": 0.78,  # 可选
        "home_elo": 1650,  # 可选
        "away_elo": 1580,  # 可选
        "odds_home": 1.85, # 可选 (赛前赔率)
        "odds_draw": 3.50,
        "odds_away": 4.20,
    }
    """
    m = live_state.get("minute", 0)
    hg = live_state.get("home_goals", 0)
    ag = live_state.get("away_goals", 0)

    features = []

    # 赔率隐含概率
    oh = live_state.get("odds_home", 2.0)
    od = live_state.get("odds_draw", 3.5)
    oa = live_state.get("odds_away", 3.5)
    ph, pd_, pa = odds_to_probs(oh, od, oa)
    features.extend([ph, pd_, pa, ph - pa])

    # Elo
    he = live_state.get("home_elo", 1500)
    ae = live_state.get("away_elo", 1500)
    features.extend([
        he - ae,           # elo_diff (raw)
        (he - ae) / 400,   # elo_diff_norm
        he / 2000,         # home_elo_norm
        ae / 2000,         # away_elo_norm
    ])

    # 主场
    features.append(1.0)

    # xG
    hxg = live_state.get("home_xg", hg * 0.9)
    axg = live_state.get("away_xg", ag * 0.9)
    features.extend([hxg - axg, hxg + axg, hxg, axg])

    return features


def build_labels(df: pd.DataFrame) -> np.ndarray:
    """
    构建标签: H→2, D→1, A→0
    """
    return df["FTR"].map({"H": 2, "D": 1, "A": 0}).values
